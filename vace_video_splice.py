"""
VACE Video Splice Node for ComfyUI

Splices two video sequences together by overlaying sequence2 at a specified frame offset.
Preserves uncovered frames from sequence1 and fills gaps with grey frames.

Developer: Ryan Game
Email: ryangamevfx@gmail.com
Category: Vace/VFX
"""

import torch
from typing import Optional, Tuple


class VACEVideoSplice:
    """
    Splice two video sequences together with frame offset control.
    
    Key Features:
    - Overlay behavior: seq2 overlays onto timeline starting at frame_offset
    - Preserves uncovered frames from seq1
    - Fills gaps with grey frames (RGB 127,127,127) and white masks (1.0)
    - Optional mask support with auto-generation
    - Offset range: 0 to 2000
    
    Example:
        seq1: 5 frames [A1, A2, A3, A4, A5]
        seq2: 4 frames [B1, B2, B3, B4]
        offset: 3
        
        Result: [A1, A2, A3, B1, B2, B3, B4]  (7 frames)
        - Positions 0-2: A1, A2, A3 (preserved)
        - Positions 3-6: B1, B2, B3, B4 (overlay seq2)
        - A4, A5 are replaced by B1, B2
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "imagesequence1": ("IMAGE",),  # [B, H, W, C]
                "imagesequence2": ("IMAGE",),  # [B, H, W, C]
                "frame_offset": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2000,
                    "step": 1,
                    "display": "number"
                }),
            },
            "optional": {
                "mask1": ("MASK",),  # [B, H, W]
                "mask2": ("MASK",),  # [B, H, W]
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "INT")
    RETURN_NAMES = ("images", "masks", "frame_count")
    FUNCTION = "splice_video"
    CATEGORY = "Vace/VFX"
    
    def splice_video(
        self,
        imagesequence1: torch.Tensor,
        imagesequence2: torch.Tensor,
        frame_offset: int,
        mask1: Optional[torch.Tensor] = None,
        mask2: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, int]:
        """
        Splice two video sequences together.
        
        Args:
            imagesequence1: First video sequence [B, H, W, C]
            imagesequence2: Second video sequence to overlay [B, H, W, C]
            frame_offset: Position to start overlaying seq2 (0-2000)
            mask1: Optional masks for sequence1 [B, H, W]
            mask2: Optional masks for sequence2 [B, H, W]
            
        Returns:
            Tuple of (spliced_images, spliced_masks, frame_count)
            
        Raises:
            ValueError: On validation failures
        """
        
        # Step 1: Validate offset
        self._validate_offset(frame_offset)
        
        # Step 2: Get dimensions and validate
        seq1_count, height, width, channels = imagesequence1.shape
        seq2_count = imagesequence2.shape[0]
        
        self._validate_resolution(imagesequence1, imagesequence2)
        
        # Step 3: Calculate total output length
        total_frames = max(seq1_count, frame_offset + seq2_count)
        
        # Step 4: Build image timeline
        output_images = self._build_image_timeline(
            imagesequence1, imagesequence2, 
            frame_offset, total_frames,
            height, width, channels
        )
        
        # Step 5: Build mask timeline
        output_masks = self._build_mask_timeline(
            mask1, mask2,
            seq1_count, seq2_count,
            frame_offset, total_frames,
            height, width
        )
        
        return (output_images, output_masks, total_frames)
    
    def _validate_offset(self, offset: int) -> None:
        """
        Validate frame offset is within acceptable range.
        
        Args:
            offset: Frame offset value
            
        Raises:
            ValueError: If offset is out of range
        """
        if offset < 0:
            raise ValueError(
                f"frame_offset must be >= 0, got {offset}"
            )
        
        if offset > 2000:
            raise ValueError(
                f"frame_offset ({offset}) exceeds maximum of 2000. "
                f"This limit prevents excessive memory usage from grey frame generation."
            )
    
    def _validate_resolution(
        self,
        seq1: torch.Tensor,
        seq2: torch.Tensor
    ) -> None:
        """
        Validate that both sequences have matching dimensions.
        
        Args:
            seq1: First sequence
            seq2: Second sequence
            
        Raises:
            ValueError: If dimensions don't match
        """
        seq1_h, seq1_w, seq1_c = seq1.shape[1:]
        seq2_h, seq2_w, seq2_c = seq2.shape[1:]
        
        if (seq1_h, seq1_w) != (seq2_h, seq2_w):
            raise ValueError(
                f"Resolution mismatch: imagesequence1 is {seq1_w}x{seq1_h} "
                f"but imagesequence2 is {seq2_w}x{seq2_h}. "
                f"Use Image Scale to resize sequences before splicing."
            )
        
        if seq1_c != seq2_c:
            raise ValueError(
                f"Channel mismatch: imagesequence1 has {seq1_c} channels "
                f"but imagesequence2 has {seq2_c} channels."
            )
    
    def _build_image_timeline(
        self,
        seq1: torch.Tensor,
        seq2: torch.Tensor,
        offset: int,
        total_frames: int,
        height: int,
        width: int,
        channels: int
    ) -> torch.Tensor:
        """
        Build the spliced image timeline.
        
        Strategy:
        1. Create base timeline from seq1 + grey fill if needed
        2. Overlay seq2 at offset position
        
        Args:
            seq1: First image sequence
            seq2: Second image sequence
            offset: Starting position for seq2
            total_frames: Total output length
            height, width, channels: Frame dimensions
            
        Returns:
            Spliced image tensor [total_frames, H, W, C]
        """
        seq1_count = len(seq1)
        seq2_count = len(seq2)
        
        # Build base timeline
        if total_frames > seq1_count:
            # Need to extend with grey frames
            grey_count = total_frames - seq1_count
            grey_frames = self._create_grey_frames(
                grey_count, height, width, channels, seq1.device
            )
            base_timeline = torch.cat([seq1, grey_frames], dim=0)
        else:
            # seq1 is long enough, clone to avoid modifying input
            base_timeline = seq1.clone()
        
        # Overlay seq2 at offset position
        end_position = offset + seq2_count
        base_timeline[offset:end_position] = seq2
        
        return base_timeline
    
    def _build_mask_timeline(
        self,
        mask1: Optional[torch.Tensor],
        mask2: Optional[torch.Tensor],
        seq1_count: int,
        seq2_count: int,
        offset: int,
        total_frames: int,
        height: int,
        width: int
    ) -> torch.Tensor:
        """
        Build the spliced mask timeline.
        
        Handles auto-generation of masks when not provided.
        Gap frames get white (1.0) masks.
        
        Args:
            mask1: Optional masks for seq1
            mask2: Optional masks for seq2
            seq1_count: Frame count of seq1
            seq2_count: Frame count of seq2
            offset: Starting position for seq2
            total_frames: Total output length
            height, width: Mask dimensions
            
        Returns:
            Spliced mask tensor [total_frames, H, W]
        """
        # Get device from mask1 if available, otherwise will be determined later
        device = mask1.device if mask1 is not None else None
        
        # Auto-generate masks if not provided
        if mask1 is None:
            device = mask2.device if mask2 is not None else torch.device('cpu')
            mask1 = torch.ones(seq1_count, height, width, 
                              dtype=torch.float32, device=device)
        else:
            # Validate mask1
            self._validate_mask(mask1, seq1_count, height, width, "mask1", "imagesequence1")
            device = mask1.device
        
        if mask2 is None:
            mask2 = torch.ones(seq2_count, height, width,
                              dtype=torch.float32, device=device)
        else:
            # Validate mask2
            self._validate_mask(mask2, seq2_count, height, width, "mask2", "imagesequence2")
        
        # Build base mask timeline (same logic as images)
        if total_frames > seq1_count:
            # Gap needs WHITE masks (1.0)
            grey_count = total_frames - seq1_count
            white_masks = torch.ones(grey_count, height, width,
                                    dtype=torch.float32, device=device)
            base_mask_timeline = torch.cat([mask1, white_masks], dim=0)
        else:
            base_mask_timeline = mask1.clone()
        
        # Overlay mask2 at offset position
        end_position = offset + seq2_count
        base_mask_timeline[offset:end_position] = mask2
        
        return base_mask_timeline
    
    def _validate_mask(
        self,
        mask: torch.Tensor,
        expected_count: int,
        height: int,
        width: int,
        mask_name: str,
        seq_name: str
    ) -> None:
        """
        Validate mask dimensions match the corresponding sequence.
        
        Args:
            mask: Mask tensor to validate
            expected_count: Expected frame count
            height, width: Expected dimensions
            mask_name: Name of mask parameter for error messages
            seq_name: Name of sequence parameter for error messages
            
        Raises:
            ValueError: If dimensions don't match
        """
        mask_count, mask_h, mask_w = mask.shape
        
        if mask_count != expected_count:
            raise ValueError(
                f"{mask_name} frame count ({mask_count}) doesn't match "
                f"{seq_name} frame count ({expected_count})"
            )
        
        if (mask_h, mask_w) != (height, width):
            raise ValueError(
                f"{mask_name} resolution ({mask_w}x{mask_h}) doesn't match "
                f"{seq_name} resolution ({width}x{height})"
            )
    
    def _create_grey_frames(
        self,
        count: int,
        height: int,
        width: int,
        channels: int,
        device: torch.device
    ) -> torch.Tensor:
        """
        Create grey frames for timeline gaps.
        
        Grey value: RGB(127, 127, 127) = 0.498 normalized
        
        Args:
            count: Number of grey frames to create
            height, width, channels: Frame dimensions
            device: Torch device for tensor
            
        Returns:
            Grey frame tensor [count, H, W, C]
        """
        grey_value = 127.0 / 255.0  # ~0.498 normalized
        
        grey_frames = torch.full(
            (count, height, width, channels),
            grey_value,
            dtype=torch.float32,
            device=device
        )
        
        return grey_frames


# ComfyUI Node Registration
NODE_CLASS_MAPPINGS = {
    "VACEVideoSplice": VACEVideoSplice
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VACEVideoSplice": "VACE Video Splice"
}