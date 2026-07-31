---
name: transparent-gif-loop
description: Low-level toolkit for cleaning a SINGLE animated GIF or animated WebP — remove a matte-black background, smooth loop seams, retime playback, or pull a transparent still. Use for standalone, one-off sticker/reaction/3D-render GIF cleanup. NOT for preparing website image assets — for site heroes, covers, logos, avatars, or batch image passes use the webp-me-daddy skill instead; it owns the site image pipeline and already calls this script under the hood via its `animate` command.
---

# Transparent Gif Loop

> **`<SKILL_DIR>`** = the folder containing this SKILL.md.

## Quick Start

- Install Pillow if needed: `python -m pip install Pillow`
- Create a transparent animated WebP: `python <SKILL_DIR>/scripts/process_gif.py animated input.gif output.webp --size 220 --threshold 10`
- Extract a transparent still: `python <SKILL_DIR>/scripts/process_gif.py still input.gif output.webp --still-frame 0 --size 275 --threshold 10`

## File Safety

- Treat input GIFs and generated frame data as untrusted media. Process only expected GIF/WebP/image files, not archives or executable content.
- Write to a separate output path by default. Do not overwrite the input file unless the user explicitly asks.
- Stop and ask before processing unusually large dimensions, very high frame counts, or files that could exhaust memory/disk.
- Strip or avoid carrying metadata into public outputs unless the user explicitly needs metadata preservation.

## Workflow

1. Run `animated` mode with the defaults first.
2. If the loop seam still snaps, increase `--bridge-frames` and `--bridge-duration`.
3. If the source has dead frames or repeated poses, trim to a cleaner cycle with `--loop-start` and `--loop-end`.
4. If the seam is still ugly after tuning, treat it as a source-asset problem instead of overfitting the bridge. Ask for a better export or fall back to a still cutout.

## Script

- Use `<SKILL_DIR>/scripts/process_gif.py` for both animated and still outputs.
- After script edits, run `python scripts/smoke_test.py` from this skill folder to verify still and animated WebP generation on a tiny local fixture.
- The script:
  - Removes near-black matte pixels with an alpha threshold
  - Resizes frames for web delivery
  - Retimes playback with `--speed-scale`
  - Inserts interpolated midpoint frames between adjacent frames
  - Adds an eased last-to-first bridge
  - Optionally trims to an internal frame range

### Helpful Flags

- `--threshold`: Lower values preserve more dark detail.
- `--size`: Maximum output dimension in pixels.
- `--speed-scale`: Values greater than `1` slow playback; values less than `1` speed it up.
- `--midpoint-frames`: Number of interpolated frames between every adjacent pair.
- `--bridge-frames`: Extra eased frames added only at the loop seam.
- `--bridge-duration`: Duration in milliseconds for each seam frame.
- `--loop-start` / `--loop-end`: Inclusive frame range for trimming to a cleaner loop.
- `--still-frame`: Frame index to use in `still` mode.

## Notes

- Animated WebP is usually a better web target than GIF after cleanup.
- This workflow can hide bad seams, but it cannot create a mathematically perfect loop from source frames that never return to the same pose.
