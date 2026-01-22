"""
VACE Inpaint Keyframe Insert Node for ComfyUI

Replaces specific frames in a video sequence with keyframe images at specified positions.
Maintains original frame count and generates corresponding masks.

Developer: Ryan Game
Email: ryangamevfx@gmail.com
Category: Vace/VFX
"""

import torch
import numpy as np
from typing import Optional, Tuple, List


class VACEInpaintKeyframeInsert:
    """
    Replaces frames in a video sequence with keyframes at specified positions.
    
    Key Features:
    - Replacement model: Original frame count maintained
    - 0-indexed position specification
    - Automatic black mask generation at keyframe positions
    - Strict validation with clear error messages
    - Supports up to 5 keyframes per node
    
    Example:
        Original: [F1, F2, F3, F4, F5, F6, F7, F8]
        Keyframes: [K1, K2] at positions "3,7"
        Result: [F1, F2, F3, K1, F5, F6, F7, K2]
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # [B, H, W, C]
                "keyframe_positions": ("STRING", {
                    "default": "0",
                    "multiline": False
                }),
            },
            "optional": {
                "masks": ("MASK",),  # [B, H, W]
                "keyframe_1": ("IMAGE",),
                "keyframe_2": ("IMAGE",),
                "keyframe_3": ("IMAGE",),
                "keyframe_4": ("IMAGE",),
                "keyframe_5": ("IMAGE",),
                "keyframe_mask_value": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")
    FUNCTION = "replace_keyframes"
    CATEGORY = "Vace/VFX"
    
    def replace_keyframes(
        self,
        images: torch.Tensor,
        keyframe_positions: str,
        masks: Optional[torch.Tensor] = None,
        keyframe_1: Optional[torch.Tensor] = None,
        keyframe_2: Optional[torch.Tensor] = None,
        keyframe_3: Optional[torch.Tensor] = None,
        keyframe_4: Optional[torch.Tensor] = None,
        keyframe_5: Optional[torch.Tensor] = None,
        keyframe_mask_value: float = 0.0
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Replace frames at specified positions with keyframes.
        
        Args:
            images: Input video frames [B, H, W, C]
            keyframe_positions: Comma-separated 0-indexed positions (e.g., "3,7,12")
            masks: Optional input masks [B, H, W]
            keyframe_1-5: Optional keyframe images to insert
            keyframe_mask_value: Mask value for replaced frames (default: 0.0 = black)
            
        Returns:
            Tuple of (modified_images, modified_masks)
            
        Raises:
            ValueError: On validation failures
        """
        
        # Step 1: Parse positions
        positions = self._parse_positions(keyframe_positions, len(images))
        
        # Step 2: Collect provided keyframes
        keyframes = self._collect_keyframes([
            keyframe_1, keyframe_2, keyframe_3, keyframe_4, keyframe_5
        ])
        
        # Step 3: Validate inputs
        self._validate_inputs(images, keyframes, positions, masks)
        
        # Step 4: Clone tensors to avoid modifying inputs
        output_images = images.clone()
        
        # Step 5: Handle masks - create white masks if none provided
        if masks is not None:
            output_masks = masks.clone()
        else:
            # Create white (1.0) masks matching image dimensions
            batch_size, height, width, _ = images.shape
            output_masks = torch.ones(batch_size, height, width, 
                                     dtype=torch.float32, device=images.device)
        
        # Step 6: Replace frames and set masks at specified positions
        for idx, position in enumerate(positions):
            # Replace frame
            output_images[position] = keyframes[idx]
            
            # Set mask value at this position
            output_masks[position] = torch.full_like(
                output_masks[position],
                keyframe_mask_value,
                dtype=torch.float32
            )
        
        return (output_images, output_masks)
    
    def _parse_positions(self, position_string: str, video_length: int) -> List[int]:
        """
        Parse position string into list of integers.
        
        Args:
            position_string: Comma-separated positions (e.g., "3,7,12")
            video_length: Total number of frames in video
            
        Returns:
            Sorted list of unique positions
            
        Raises:
            ValueError: If positions are invalid
        """
        # Remove whitespace and split by comma
        position_string = position_string.strip()
        
        if not position_string:
            raise ValueError(
                "Empty position string provided. "
                "Specify at least one position (e.g., '0' or '3,7,12')"
            )
        
        try:
            # Parse each position
            positions = []
            for pos_str in position_string.split(','):
                pos_str = pos_str.strip()
                if not pos_str:
                    continue  # Skip empty strings from trailing commas
                
                # Convert to integer
                pos = int(pos_str)
                positions.append(pos)
            
            if not positions:
                raise ValueError("No valid positions found in string")
            
        except ValueError as e:
            raise ValueError(
                f"Invalid position format: '{position_string}'. "
                f"Use comma-separated integers (e.g., '3,7,12'). Error: {e}"
            )
        
        # Validate positions
        for pos in positions:
            if pos < 0:
                raise ValueError(
                    f"Negative position not allowed: {pos}. "
                    f"Use 0-indexed positions (0 to {video_length - 1})"
                )
            
            if pos >= video_length:
                raise ValueError(
                    f"Position {pos} is out of range. "
                    f"Video has {video_length} frames (valid range: 0-{video_length - 1})"
                )
        
        # Check for duplicates
        if len(positions) != len(set(positions)):
            duplicates = [p for p in positions if positions.count(p) > 1]
            unique_duplicates = sorted(set(duplicates))
            raise ValueError(
                f"Duplicate positions found: {unique_duplicates}. "
                f"Each position must be unique."
            )
        
        # Return sorted positions for predictable replacement order
        return sorted(positions)
    
    def _collect_keyframes(self, keyframe_list: List[Optional[torch.Tensor]]) -> List[torch.Tensor]:
        """
        Collect non-None keyframes from optional inputs.
        
        Args:
            keyframe_list: List of optional keyframe tensors
            
        Returns:
            List of provided keyframes (non-None values)
            
        Raises:
            ValueError: If no keyframes provided or too many keyframes
        """
        keyframes = [kf for kf in keyframe_list if kf is not None]
        
        if not keyframes:
            raise ValueError(
                "No keyframes provided. "
                "Connect at least one keyframe image (keyframe_1, keyframe_2, etc.)"
            )
        
        if len(keyframes) > 5:
            raise ValueError(
                f"Too many keyframes ({len(keyframes)}). "
                f"Maximum is 5 keyframes per node. "
                f"Use multiple VACE Keyframe Replacer nodes for more keyframes."
            )
        
        return keyframes
    
    def _validate_inputs(
        self,
        images: torch.Tensor,
        keyframes: List[torch.Tensor],
        positions: List[int],
        masks: Optional[torch.Tensor]
    ) -> None:
        """
        Validate all inputs with strict error checking.
        
        Args:
            images: Input video frames
            keyframes: List of keyframe images
            positions: List of replacement positions
            masks: Optional input masks
            
        Raises:
            ValueError: If validation fails
        """
        # Validate keyframe count matches position count
        if len(keyframes) != len(positions):
            raise ValueError(
                f"Keyframe count ({len(keyframes)}) does not match "
                f"position count ({len(positions)}). "
                f"Provide exactly one keyframe per position."
            )
        
        # Get video dimensions
        video_batch, video_height, video_width, video_channels = images.shape
        
        # Validate each keyframe resolution and channels
        for idx, keyframe in enumerate(keyframes):
            kf_batch, kf_height, kf_width, kf_channels = keyframe.shape
            
            # Each keyframe should be a single image (batch size 1)
            if kf_batch != 1:
                raise ValueError(
                    f"Keyframe {idx + 1} has batch size {kf_batch}. "
                    f"Each keyframe must be a single image (batch size 1). "
                    f"Use VHS Video Combine or similar to extract single frames."
                )
            
            # Check resolution match
            if kf_height != video_height or kf_width != video_width:
                raise ValueError(
                    f"Keyframe {idx + 1} resolution ({kf_width}x{kf_height}) "
                    f"does not match video resolution ({video_width}x{video_height}). "
                    f"All keyframes must match video resolution exactly. "
                    f"Use Image Scale or similar to resize keyframes."
                )
            
            # Check channel count match
            if kf_channels != video_channels:
                raise ValueError(
                    f"Keyframe {idx + 1} has {kf_channels} channels but "
                    f"video has {video_channels} channels. "
                    f"Channel count must match (RGB=3, RGBA=4)."
                )
        
        # Validate masks if provided
        if masks is not None:
            mask_batch, mask_height, mask_width = masks.shape
            
            if mask_batch != video_batch:
                raise ValueError(
                    f"Mask batch size ({mask_batch}) does not match "
                    f"video batch size ({video_batch}). "
                    f"Provide one mask per video frame."
                )
            
            if mask_height != video_height or mask_width != video_width:
                raise ValueError(
                    f"Mask resolution ({mask_width}x{mask_height}) "
                    f"does not match video resolution ({video_width}x{video_height}). "
                    f"Masks must have same dimensions as video frames."
                )


# ComfyUI Node Registration
NODE_CLASS_MAPPINGS = {
    "VACEInpaintKeyframeInsert": VACEInpaintKeyframeInsert
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VACEInpaintKeyframeInsert": "VACE Inpaint Keyframe Insert"
}