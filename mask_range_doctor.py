"""
Mask Range Doctor Node for ComfyUI

Edits mask sequences by setting specific frames or frame ranges to white (1.0) or black (0.0).
Perfect for fine-tuning VACE preprocessing masks after keyframe insertion.

Developer: Ryan Game
Email: ryangamevfx@gmail.com
Category: Vace/VFX
"""

import torch
from typing import Optional, List, Set


class MaskRangeDoctor:
    """
    Edits mask sequences by setting specific frames or ranges to white or black.
    
    Key Features:
    - Range syntax: "3,5,10-15,20" (commas for individual, dashes for ranges)
    - Both endpoints inclusive: "10-15" includes frames 10,11,12,13,14,15
    - Strict validation: Errors on overlapping ranges or out-of-bounds frames
    - Preserves mask dimensions
    - Empty ranges allowed (skip white or black processing)
    
    Example:
        Input: 120 frames
        White Range: "3,5,10-15"  → Frames 3,5,10,11,12,13,14,15 set to white (1.0)
        Black Range: "20,25-30"   → Frames 20,25,26,27,28,29,30 set to black (0.0)
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "masks": ("MASK",),  # [B, H, W]
            },
            "optional": {
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
    
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("masks",)
    FUNCTION = "edit_mask_ranges"
    CATEGORY = "Vace/VFX"
    
    def edit_mask_ranges(
        self,
        masks: torch.Tensor,
        white_range: str = "",
        black_range: str = ""
    ) -> tuple:
        """
        Edit mask values at specified frame ranges.
        
        Args:
            masks: Input mask sequence [B, H, W]
            white_range: Frames to set white (e.g., "3,5,10-15")
            black_range: Frames to set black (e.g., "20,25-30")
            
        Returns:
            Tuple containing modified masks
            
        Raises:
            ValueError: On validation failures (overlaps, out-of-range, invalid format)
        """
        
        # Get mask dimensions
        total_frames = masks.shape[0]
        
        # Step 1: Parse range strings
        white_frames = self._parse_range_string(white_range, total_frames, "white_range")
        black_frames = self._parse_range_string(black_range, total_frames, "black_range")
        
        # Step 2: Check for overlapping frames (strict error)
        self._check_overlaps(white_frames, black_frames)
        
        # Step 3: Clone masks to avoid modifying input
        output_masks = masks.clone()
        
        # Step 4: Apply white masks
        for frame_idx in white_frames:
            output_masks[frame_idx] = torch.ones_like(
                output_masks[frame_idx],
                dtype=torch.float32
            )
        
        # Step 5: Apply black masks
        for frame_idx in black_frames:
            output_masks[frame_idx] = torch.zeros_like(
                output_masks[frame_idx],
                dtype=torch.float32
            )
        
        return (output_masks,)
    
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
            total_frames: Total number of frames in mask sequence
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
                            f"Mask has {total_frames} frames (valid range: 0-{total_frames - 1})"
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
                            f"Mask has {total_frames} frames (valid range: 0-{total_frames - 1})"
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
    
    def _check_overlaps(self, white_frames: List[int], black_frames: List[int]) -> None:
        """
        Check for overlapping frames between white and black ranges.
        
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
    "MaskRangeDoctor": MaskRangeDoctor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskRangeDoctor": "Mask Range Doctor"
}