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
        
        # Step 1: Validate input
        self._validate_offset(frame_offset)
        self._validate_resolution(imagesequence1, imagesequence2)
        
        # Step 2: Get dimensions and device
        seq1_count, height, width, channels = imagesequence1.shape
        seq2_count = imagesequence2.shape[0]
        device = imagesequence1.device  # Ensure we stay on the correct hardware
        
        # Step 3: Calculate total output length
        total_frames = max(seq1_count, frame_offset + seq2_count)
        
        # Step 4: Build image timeline
        output_images = self._build_image_timeline(
            imagesequence1, imagesequence2, 
            frame_offset, total_frames,
            height, width, channels, device
        )
        
        # Step 5: Build mask timeline
        output_masks = self._build_mask_timeline(
            mask1, mask2,
            seq1_count, seq2_count,
            frame_offset, total_frames,
            height, width, device
        )
        
        return (output_images, output_masks, total_frames)
    
    def _validate_offset(self, offset: int) -> None:
        if offset < 0:
            raise ValueError(f"frame_offset must be >= 0, got {offset}")
        if offset > 2000:
            raise ValueError(f"frame_offset ({offset}) exceeds maximum of 2000.")
    
    def _validate_resolution(self, seq1: torch.Tensor, seq2: torch.Tensor) -> None:
        seq1_h, seq1_w, seq1_c = seq1.shape[1:]
        seq2_h, seq2_w, seq2_c = seq2.shape[1:]
        
        if (seq1_h, seq1_w) != (seq2_h, seq2_w):
            raise ValueError(
                f"Resolution mismatch: {seq1_w}x{seq1_h} vs {seq2_w}x{seq2_h}. "
                f"Resize sequences before splicing."
            )
        if seq1_c != seq2_c:
            raise ValueError(f"Channel mismatch: {seq1_c} vs {seq2_c}.")
    
    def _build_image_timeline(
        self,
        seq1: torch.Tensor,
        seq2: torch.Tensor,
        offset: int,
        total_frames: int,
        height: int,
        width: int,
        channels: int,
        device: torch.device
    ) -> torch.Tensor:
        
        seq1_count = len(seq1)
        seq2_count = len(seq2)
        
        # 1. Start with Seq1. If output is longer, pad with Grey.
        if total_frames > seq1_count:
            grey_count = total_frames - seq1_count
            grey_value = 127.0 / 255.0
            grey_frames = torch.full(
                (grey_count, height, width, channels),
                grey_value,
                dtype=torch.float32,
                device=device
            )
            base_timeline = torch.cat([seq1, grey_frames], dim=0)
        else:
            base_timeline = seq1.clone()
        
        # 2. Overlay Seq2
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
        width: int,
        device: torch.device
    ) -> torch.Tensor:
        """
        Builds mask timeline using 'White Canvas' strategy.
        1. Initialize everything as White (1.0/Gap).
        2. Paint Black (0.0/Content) or specific masks where video exists.
        """
        
        # 1. Initialize Canvas: Default to WHITE (1.0) for gaps
        timeline = torch.ones(
            (total_frames, height, width), 
            dtype=torch.float32, 
            device=device
        )
        
        # 2. Apply Seq 1 Mask (or Black if None)
        # This covers indices [0 : seq1_count]
        if mask1 is not None:
            self._validate_mask(mask1, seq1_count, height, width, "mask1", "imagesequence1")
            timeline[0:seq1_count] = mask1.to(device)
        else:
            # Video content exists here -> set mask to Black (0.0)
            timeline[0:seq1_count] = 0.0
            
        # 3. Overlay Seq 2 Mask (or Black if None)
        # This overwrites indices [offset : offset + seq2_count]
        end_position = offset + seq2_count
        if mask2 is not None:
            self._validate_mask(mask2, seq2_count, height, width, "mask2", "imagesequence2")
            timeline[offset:end_position] = mask2.to(device)
        else:
            # Video content exists here -> set mask to Black (0.0)
            timeline[offset:end_position] = 0.0
            
        return timeline
    
    def _validate_mask(
        self,
        mask: torch.Tensor,
        expected_count: int,
        height: int,
        width: int,
        mask_name: str,
        seq_name: str
    ) -> None:
        mask_count, mask_h, mask_w = mask.shape
        if mask_count != expected_count:
            raise ValueError(f"{mask_name} count {mask_count} != {seq_name} count {expected_count}")
        if (mask_h, mask_w) != (height, width):
            raise ValueError(f"{mask_name} res {mask_w}x{mask_h} != {seq_name} res {width}x{height}")


# ComfyUI Node Registration
NODE_CLASS_MAPPINGS = {
    "VACEVideoSplice": VACEVideoSplice
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VACEVideoSplice": "VACE Video Splice"
}