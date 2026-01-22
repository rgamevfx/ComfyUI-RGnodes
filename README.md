
# VFX and video utility nodes. Avoiding opening other apps/clearing other caches. 

---

<img width="1307" height="621" alt="Screenshot 2026-01-21 201006" src="https://github.com/user-attachments/assets/cd0d7c4f-e1bc-415c-ac7d-652f271cf835" />

---


### 🎞️ VACE Inpaint Keyframe Insert

 Insert inpainted frames into an image sequence, and clear the mask on that frame.
 Chain multiple nodes to add >5

  [Make sure inputs are same size]



### 🎞️ Mask Range Doctor

  Turn mask sequences on or off with white (1.0) or black (0.0). Simple comma , and dash - range syntax to define range


### 🎞️ VACE Video Splice

 Splice two video sequences together by overlaying sequence2 at a specified frame offset, fills empty frames with grey for VACE. Preserves uncovered frames and fills gaps with grey frames and white masks. (Mostly for transitions) 
---



### Installation


### Manual Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/rgamevfx/ComfyUI-RGnodes.git
```






Special thanks to:

\- https://github.com/TrentHunter82/TrentNodes

\- https://github.com/drozbay/ComfyUI-WanVaceAdvanced

\- Claude Free Tier





