
\## Nodes Included



\### 1. VACE Inpaint Keyframe Insert

Insert keyframe images at specific frame positions in your video sequence. Perfect for replacing frames with inpainted or edited versions while maintaining the original frame count.



\### 2. Mask Range Doctor

Edit mask sequences by setting specific frames or frame ranges to white (1.0) or black (0.0). Fine-tune your VACE preprocessing masks with simple range syntax.



---



\## Installation



\### Method 1: Via ComfyUI Manager (Coming Soon)

Search for "VACE Nodes" in ComfyUI Manager and click Install.



\### Method 2: Manual Installation



1\. Navigate to your ComfyUI custom\_nodes folder:

&nbsp;  ```bash

&nbsp;  cd ComfyUI/custom\_nodes/

&nbsp;  ```



2\. Clone this repository:

&nbsp;  ```bash

&nbsp;  git clone https://github.com/YOUR\_USERNAME/VACE-Nodes.git

&nbsp;  ```



3\. Restart ComfyUI



4\. Both nodes will appear under: `Vace/VFX/`



---



\## Node 1: VACE Inpaint Keyframe Insert



\### What Does It Do?

Replaces specific frames in a video sequence with keyframe images at exact positions. Perfect for VACE preprocessing where you need to insert inpainted frames at specific positions.



\### Features

\- ✅ Replace frames at exact positions (0-indexed)

\- ✅ Maintains original video frame count

\- ✅ Automatic black mask generation at keyframe positions

\- ✅ Supports up to 5 keyframes per node

\- ✅ Strict validation with helpful error messages

\- ✅ Resolution matching enforcement



\### Usage



\*\*Basic Example:\*\*

```

\[Load Video] → images → \[VACE Inpaint Keyframe Insert] → images → \[Save Video]

&nbsp;                        ↑                                ↓

\[Load Image] → keyframe\_1                              masks → \[Preview]

&nbsp;                        ↑

&nbsp;        "10,20,30" → keyframe\_positions

```



\*\*Example:\*\*

```

Original Video: \[F1, F2, F3, F4, F5, F6, F7, F8]  (8 frames)

Keyframes: \[K1, K2]

Positions: "3,7"



Result: \[F1, F2, F3, K1, F5, F6, F7, K2]  (still 8 frames)

```



\### Parameters



\*\*Required:\*\*

\- `images` - Input video frames (IMAGE)

\- `keyframe\_positions` - Comma-separated positions (STRING, e.g., "3,7,12")



\*\*Optional:\*\*

\- `masks` - Input masks (auto-generated if not provided)

\- `keyframe\_1` to `keyframe\_5` - Keyframe images to insert

\- `keyframe\_mask\_value` - Mask value at replaced positions (default: 0.0)



\*\*Outputs:\*\*

\- `images` - Modified video frames

\- `masks` - Modified masks (black at keyframe positions)



\### Error Handling

\- ❌ Position out of range

\- ❌ Duplicate positions

\- ❌ Keyframe count mismatch

\- ❌ Resolution mismatch

\- ❌ Invalid position format



---



\## Node 2: Mask Range Doctor



\### What Does It Do?

Edits mask sequences by setting specific frames or frame ranges to white (1.0) or black (0.0). Essential for VACE workflows where you need precise control over which frames are masked.



\### Features

\- ✅ Simple range syntax: `"3,5,10-15,20"`

\- ✅ Both endpoints inclusive: `"10-15"` = 6 frames

\- ✅ Strict overlap validation

\- ✅ Preserves mask dimensions

\- ✅ Optional ranges (leave empty to skip)

\- ✅ Clear error messages



\### Usage



\*\*Basic Example:\*\*

```

\[Load Video] → masks → \[Mask Range Doctor] → masks → \[Preview]

&nbsp;                      ↑                  ↑

&nbsp;      "0-10,50-60" → white\_range    "30-40" → black\_range

```



\*\*Range Syntax:\*\*

\- Individual frames: `"3,5,20"`

\- Ranges (inclusive): `"10-15"` → frames 10,11,12,13,14,15

\- Mixed: `"3,5,10-15,20,25-30"`

\- Empty: `""` → skip this operation



\### Parameters



\*\*Required:\*\*

\- `masks` - Input mask sequence (MASK)



\*\*Optional:\*\*

\- `white\_range` - Frames to set white/1.0 (STRING, default: "")

\- `black\_range` - Frames to set black/0.0 (STRING, default: "")



\*\*Outputs:\*\*

\- `masks` - Modified mask sequence



\### Error Handling

\- ❌ Overlapping white/black ranges

\- ❌ Frame out of range

\- ❌ Invalid range format (e.g., "30-10")

\- ❌ Invalid number format



---



\## Complete Workflow Example



\*\*VACE Preprocessing Pipeline:\*\*

```

\[Load Video] (100 frames)

&nbsp;   ↓

&nbsp;   images → \[VACE Inpaint Keyframe Insert]

&nbsp;            ↑ keyframe\_1 (inpainted frame)

&nbsp;            ↑ keyframe\_2 (inpainted frame)  

&nbsp;            ↑ keyframe\_3 (inpainted frame)

&nbsp;            ↑ keyframe\_positions: "10,30,50"

&nbsp;            ↓

&nbsp;            images → \[Save Video]

&nbsp;            ↓

&nbsp;            masks → \[Mask Range Doctor]

&nbsp;                    ↑ white\_range: "10,30,50"      (preserve keyframes)

&nbsp;                    ↑ black\_range: "5,15,25,35,45,55"  (interpolate surroundings)

&nbsp;                    ↓

&nbsp;                    masks → \[Preview/Save Masks]

```



\*\*This workflow:\*\*

1\. Inserts 3 inpainted keyframes at positions 10, 30, 50

2\. Sets those keyframe positions to white masks (preserve)

3\. Sets surrounding frames to black masks (allow interpolation)

4\. Perfect setup for VACE video generation



---



\## Use Cases



\### Keyframe Inpainting

```

1\. Remove objects from specific frames (inpainting)

2\. Insert inpainted frames with VACE Inpaint Keyframe Insert

3\. Fine-tune masks with Mask Range Doctor

4\. Process with VACE

```



\### Selective Masking

```

1\. Load video mask sequence

2\. Use Mask Range Doctor to override specific sections

3\. White = keep original, Black = allow changes

```



\### Transition Control

```

1\. Insert keyframes at transition points

2\. Set keyframes to white (preserve)

3\. Set transition frames to black (smooth interpolation)

```



---



\## Tips \& Best Practices



\### For VACE Inpaint Keyframe Insert:

1\. \*\*Match resolution\*\*: Ensure keyframes match video resolution exactly

2\. \*\*0-indexed\*\*: First frame is 0, not 1

3\. \*\*Test positions\*\*: Start with one keyframe, then add more

4\. \*\*Chain nodes\*\*: Need more than 5 keyframes? Chain multiple nodes



\### For Mask Range Doctor:

1\. \*\*Plan ranges\*\*: Sketch out your white/black ranges before applying

2\. \*\*Avoid overlaps\*\*: Check that ranges don't conflict

3\. \*\*Use ranges\*\*: `"10-20"` is cleaner than listing 11 individual frames

4\. \*\*Preview often\*\*: Use Preview Image to verify your mask edits



\### For Both:

1\. \*\*Chain together\*\*: Keyframe Insert → Mask Doctor = complete control

2\. \*\*Save intermediates\*\*: Preview/save masks between steps

3\. \*\*Start simple\*\*: Test with small ranges/few keyframes first

4\. \*\*Read errors\*\*: Error messages are detailed and helpful



---



\## Requirements



\- ComfyUI (latest version recommended)

\- Python 3.10+

\- PyTorch (included with ComfyUI)



---



\## Examples Gallery



\### Example 1: Remove Object from 3 Frames

```

Frames 10, 30, 50 have unwanted object

→ Inpaint those frames externally

→ Insert with keyframe\_positions: "10,30,50"

→ Set white\_range: "10,30,50" (keep inpainted frames)

→ Set black\_range: "" (interpolate everything else)

```



\### Example 2: Transition Smoothing

```

Abrupt cuts at frames 25, 75

→ Create transition frames

→ Insert at positions: "24,25,26,74,75,76"

→ Set white\_range: "25,75" (preserve key transitions)

→ Set black\_range: "24,26,74,76" (smooth surroundings)

```



\### Example 3: Stylization Control

```

Want to keep original style on certain frames

→ Insert style-preserved frames at: "0,20,40,60,80,100"

→ Set white\_range: "0,20,40,60,80,100"

→ Let VACE interpolate between them

```



---



\## Troubleshooting



\### Nodes Don't Appear

\- Restart ComfyUI completely

\- Check console for Python errors

\- Verify all files are in the correct folder



\### "Position out of range" Error

\- Remember: 0-indexed (first frame = 0)

\- 100-frame video → valid range is 0-99



\### "Overlapping frames" Error

\- Check that white\_range and black\_range don't share frames

\- Example: white: "10-20", black: "15-25" → frames 15-20 overlap ❌



\### Resolution Mismatch

\- Use Image Scale node to resize keyframes before insertion

\- All keyframes must match video resolution exactly



---



\## License



MIT License - See LICENSE file for details



---



\## Support



Please only email me to hire me =]



---



\## Roadmap



Road H\*\*\* map



---



\## Contributing



Contributions welcome! Please:

1\. Fork the repository

2\. Create a feature branch

3\. Test thoroughly

4\. Submit a pull request



---



\## Changelog



\### Version 1.0.0 (Initial Release)

\*\*VACE Inpaint Keyframe Insert:\*\*

\- Basic keyframe insertion at exact positions

\- Support for up to 5 keyframes

\- Automatic mask generation

\- Strict validation



\*\*Mask Range Doctor:\*\*

\- Range syntax support

\- Overlap validation

\- White/black mask editing

\- Dimension preservation



---



\## Attribution



Special thanks to:

\- https://github.com/TrentHunter82/TrentNodes

\- https://github.com/drozbay/ComfyUI-WanVaceAdvanced

\- Claude Free Tier





