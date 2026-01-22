"""
VACE Nodes - ComfyUI Custom Nodes

A collection of nodes for VACE (Video Art Composition Engine) workflows.

Developer: Ryan Game
Email: ryangamevfx@gmail.com
Category: Vace/VFX

Nodes:
- VACE Inpaint Keyframe Insert: Insert keyframes at specific positions
- Mask Range Doctor: Edit mask ranges with white/black values
"""

from .vace_inpaint_keyframe_insert import NODE_CLASS_MAPPINGS as KEYFRAME_MAPPINGS
from .vace_inpaint_keyframe_insert import NODE_DISPLAY_NAME_MAPPINGS as KEYFRAME_DISPLAY

from .mask_range_doctor import NODE_CLASS_MAPPINGS as MASK_MAPPINGS
from .mask_range_doctor import NODE_DISPLAY_NAME_MAPPINGS as MASK_DISPLAY

# Merge the mappings from both nodes
NODE_CLASS_MAPPINGS = {
    **KEYFRAME_MAPPINGS,
    **MASK_MAPPINGS
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **KEYFRAME_DISPLAY,
    **MASK_DISPLAY
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']