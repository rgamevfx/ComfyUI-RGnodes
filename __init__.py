"""
VACE Nodes - ComfyUI Custom Nodes Collection

A collection of nodes for VACE (Video Art Composition Engine) workflows.

Developer: Ryan Game
Email: ryangamevfx@gmail.com
Category: Vace/VFX

Nodes Included:
- VACE Inpaint Keyframe Insert: Insert keyframes at specific frame positions
- Mask Range Doctor: Edit mask ranges by setting frames to white/black values
- VACE Clip Doctor: Edit image and mask sequences with grey/white/black frame control
- VACE Video Splice: Splice two video sequences with frame offset control
"""

from .vace_inpaint_keyframe_insert import NODE_CLASS_MAPPINGS as KEYFRAME_MAPPINGS
from .vace_inpaint_keyframe_insert import NODE_DISPLAY_NAME_MAPPINGS as KEYFRAME_DISPLAY

from .mask_range_doctor import NODE_CLASS_MAPPINGS as MASK_MAPPINGS
from .mask_range_doctor import NODE_DISPLAY_NAME_MAPPINGS as MASK_DISPLAY

from .vace_clip_doctor import NODE_CLASS_MAPPINGS as CLIP_MAPPINGS
from .vace_clip_doctor import NODE_DISPLAY_NAME_MAPPINGS as CLIP_DISPLAY

from .vace_video_splice import NODE_CLASS_MAPPINGS as SPLICE_MAPPINGS
from .vace_video_splice import NODE_DISPLAY_NAME_MAPPINGS as SPLICE_DISPLAY

# Merge the mappings from all nodes
NODE_CLASS_MAPPINGS = {
    **KEYFRAME_MAPPINGS,
    **MASK_MAPPINGS,
    **CLIP_MAPPINGS,
    **SPLICE_MAPPINGS
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **KEYFRAME_DISPLAY,
    **MASK_DISPLAY,
    **CLIP_DISPLAY,
    **SPLICE_DISPLAY
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
