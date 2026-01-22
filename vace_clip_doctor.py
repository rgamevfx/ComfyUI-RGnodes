"""
VACE Clip Doctor Node for ComfyUI

Edits both image and mask sequences by setting specific frames or frame ranges to:
- Images: Grey (RGB 127,127,127)
- Masks: White (1.0) or Black (0.0)

Perfect for fine-tuning VACE preprocessing after keyframe insertion.

Developer: Ryan Game
Email: ryangamevfx@gmail.com
Category: Vace/VFX
"""

import torch
from typing import Optional, List, Set


class VACEClipDoctor:
    """
    Edits image and mask sequences by setting specific frames or ranges.
    
    Key Features:
    - Range syntax: "3,5,10-15,20" (commas for individual, dashes for ranges)
    - Both endpoints inclusive: "10-15" includes frames 10,11,12,13,14,15
    - Strict validation: Errors on overlapping ranges or out-of-bounds frames
    - Preserves image and mask dimensions
    - Empty ranges allowed (skip processing)
    
    Example:
        Input: 6 frames
        Grey Range: "2,6"      → Frames 2,6 set to grey (127,127,127)
        White Range: "2,5-6"   → Frames 2,5,6 set to white (1.0)
        Black Range: "1"       → Frame 1 set to black (0.0)
        
        Output Images: [a1, grey, a3, a4, a5, grey]
        Output Masks:  [black, white, m3, m4, white, white]
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # [B, H, W, C]
                "masks": ("MASK",),    # [B, H, W]
            },
            "optional": {
                "grey_range": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "e.g., 2,5,10-15"
                }),
                "white_range": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "e.g., 3,5,10-15,20"
                }),
                "black_range": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "e.g., 25,30-40,50"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")
    FUNCTION = "edit_sequences"
    CATEGORY = "Vace/VFX"
    
    def edit_sequences(
        self,
        images: torch.Tensor,
        masks: torch.Tensor,
        grey_range: str = "",
        white_range: str = "",
        black_range: str = ""
    ) -> tuple:
        """
        Edit image and mask values at specified frame ranges.
        
        Args:
            images: Input image sequence [B, H, W, C]
            masks: Input mask sequence [B, H, W]
            grey_range: Frames to set grey in images (e.g., "2,5,10-15")
            white_range: Frames to set white in masks (e.g., "3,5,10-15")
            black_range: Frames to set black in masks (e.g., "20,25-30")
            
        Returns:
            Tuple containing (modified_images, modified_masks)
            
        Raises:
            ValueError: On validation failures (overlaps, out-of-range, invalid format, mismatched counts)
        """
        
        # Validate image and mask counts match
        if images.shape[0] != masks.shape[0]:
            raise ValueError(
                f"Image and mask frame counts must match. "
                f"Got {images.shape[0]} images and {masks.shape[0]} masks."
            )
        
        # Get sequence length
        total_frames = images.shape[0]
        
        # Step 1: Parse range strings
        grey_frames = self._parse_range_string(grey_range, total_frames, "grey_range")
        white_frames = self._parse_range_string(white_range, total_frames, "white_range")
        black_frames = self._parse_range_string(black_range, total_frames, "black_range")
        
        # Step 2: Check for overlapping frames in mask ranges (strict error)
        self._check_mask_overlaps(white_frames, black_frames)
        
        # Step 3: Clone sequences to avoid modifying input
        output_images = images.clone()
        output_masks = masks.clone()
        
        # Step 4: Apply grey frames to images
        for frame_idx in grey_frames:
            # Create grey frame: RGB (127, 127, 127) normalized to [0, 1]
            grey_value = 127.0 / 255.0
            output_images[frame_idx] = torch.full_like(
                output_images[frame_idx],
                grey_value,
                dtype=torch.float32
            )
        
        # Step 5: Apply white masks
        for frame_idx in white_frames:
            output_masks[frame_idx] = torch.ones_like(
                output_masks[frame_idx],
                dtype=torch.float32
            )
        
        # Step 6: Apply black masks
        for frame_idx in black_frames:
            output_masks[frame_idx] = torch.zeros_like(
                output_masks[frame_idx],
                dtype=torch.float32
            )
        
        return (output_images, output_masks)
    
    def _parse_range_string(
        self,
        range_string: str,
        total_frames: int,
        param_name: str
    ) -> List[int]:
        """
        Parse range string into list of frame indices.
        
        Supports:
        - Individual frames: "3,5,20"
        - Ranges (inclusive): "10-15" → [10,11,12,13,14,15]
        - Mixed: "3,5,10-15,20"
        
        Args:
            range_string: Range specification string
            total_frames: Total number of frames in sequence
            param_name: Parameter name for error messages
            
        Returns:
            Sorted list of unique frame indices
            
        Raises:
            ValueError: If range format is invalid or frames are out of bounds
        """
        # Handle empty string
        range_string = range_string.strip()
        if not range_string:
            return []  # Empty range = no frames to process
        
        frames = []
        parts = range_string.split(',')
        
        for part in parts:
            part = part.strip()
            
            if not part:
                continue  # Skip empty parts from trailing commas
            
            try:
                if '-' in part:
                    # Range format: "10-15"
                    range_parts = part.split('-')
                    
                    if len(range_parts) != 2:
                        raise ValueError(
                            f"Invalid range format in {param_name}: '{part}'. "
                            f"Use format 'start-end' (e.g., '10-15')"
                        )
                    
                    start_str, end_str = range_parts
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    
                    # Validate range
                    if start > end:
                        raise ValueError(
                            f"Invalid range in {param_name}: '{part}'. "
                            f"Start frame ({start}) must be ≤ end frame ({end})"
                        )
                    
                    # Validate bounds
                    if start < 0:
                        raise ValueError(
                            f"Frame {start} in {param_name} is negative. "
                            f"Use 0-indexed frames (0 to {total_frames - 1})"
                        )
                    
                    if end >= total_frames:
                        raise ValueError(
                            f"Frame {end} in {param_name} is out of range. "
                            f"Sequence has {total_frames} frames (valid range: 0-{total_frames - 1})"
                        )
                    
                    # Add all frames in range (inclusive)
                    frames.extend(range(start, end + 1))
                    
                else:
                    # Single frame: "3"
                    frame = int(part)
                    
                    # Validate bounds
                    if frame < 0:
                        raise ValueError(
                            f"Frame {frame} in {param_name} is negative. "
                            f"Use 0-indexed frames (0 to {total_frames - 1})"
                        )
                    
                    if frame >= total_frames:
                        raise ValueError(
                            f"Frame {frame} in {param_name} is out of range. "
                            f"Sequence has {total_frames} frames (valid range: 0-{total_frames - 1})"
                        )
                    
                    frames.append(frame)
                    
            except ValueError as e:
                # Re-raise validation errors
                if "in " + param_name in str(e):
                    raise
                # Wrap parsing errors
                raise ValueError(
                    f"Invalid format in {param_name}: '{part}'. "
                    f"Frame indices must be integers. Error: {e}"
                )
        
        # Remove duplicates and sort
        return sorted(set(frames))
    
    def _check_mask_overlaps(self, white_frames: List[int], black_frames: List[int]) -> None:
        """
        Check for overlapping frames between white and black mask ranges.
        
        Args:
            white_frames: List of frames to set white
            black_frames: List of frames to set black
            
        Raises:
            ValueError: If any frames appear in both ranges
        """
        # Convert to sets for efficient intersection
        white_set = set(white_frames)
        black_set = set(black_frames)
        
        # Find overlapping frames
        overlaps = white_set & black_set
        
        if overlaps:
            # Sort for consistent error message
            overlap_list = sorted(overlaps)
            
            # Format overlap list for display
            if len(overlap_list) <= 10:
                overlap_str = ", ".join(map(str, overlap_list))
            else:
                # Show first 10 and count
                first_ten = ", ".join(map(str, overlap_list[:10]))
                overlap_str = f"{first_ten}... ({len(overlap_list)} total)"
            
            raise ValueError(
                f"Overlapping frames detected between white_range and black_range: [{overlap_str}]. "
                f"Each frame can only be assigned to white OR black, not both. "
                f"Please adjust your ranges to remove overlaps."
            )


# ComfyUI Node Registration
NODE_CLASS_MAPPINGS = {
    "VACEClipDoctor": VACEClipDoctor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VACEClipDoctor": "VACE Clip Doctor"
}
