# Transparent Gif Loop 🎞️

Takes an animated GIF with a matte-black background and gives you back a clean, transparent, properly-looping WebP.

Built for the specific and very common problem of a spinning 3D render, sticker, or reaction GIF that was exported onto black, snaps visibly at the loop seam, and plays about 40% too fast for comfort.

> **Private working copy** — source behind the `transparent-gif-loop` skill.

## ⚙️ Requirements

- Python 3
- Pillow (`python -m pip install Pillow`)

## 🚀 Quick Start

Transparent animated WebP:

```shell
python scripts/process_gif.py animated input.gif output.webp --size 220 --threshold 10
```

Transparent still frame:

```shell
python scripts/process_gif.py still input.gif output.webp --still-frame 0 --size 275 --threshold 10
```

## 🔧 What It Actually Does

- Removes near-black matte pixels using an alpha threshold
- Resizes frames for web delivery
- Retimes playback with a speed scale
- Interpolates midpoint frames between adjacent frames for smoother motion
- Adds an **eased last-to-first bridge** so the loop seam stops snapping
- Optionally trims to a cleaner internal frame range

## 🎛️ Flags Worth Knowing

| Flag | Effect |
|---|---|
| `--threshold` | Lower values preserve more dark detail (raise it if the matte lingers) |
| `--size` | Maximum output dimension in pixels |
| `--speed-scale` | `>1` slows playback, `<1` speeds it up |
| `--midpoint-frames` | Interpolated frames between every adjacent pair |
| `--bridge-frames` | Extra eased frames added **only** at the loop seam |
| `--bridge-duration` | Milliseconds per seam frame |
| `--loop-start` / `--loop-end` | Inclusive frame range for trimming to a clean cycle |
| `--still-frame` | Frame index to use in `still` mode |

## 🧭 Workflow

1. Run `animated` mode with the defaults first. Often that's enough.
2. If the seam still snaps, raise `--bridge-frames` and `--bridge-duration`.
3. If the source has dead frames or repeated poses, trim to a cleaner cycle with `--loop-start` / `--loop-end`.
4. If it's *still* ugly — stop tuning. That is a source-asset problem, not a bridge problem. Ask for a better export or fall back to a still cutout.

## ⚠️ Honest Limitations

This can hide a bad seam. It cannot invent a mathematically perfect loop out of source frames that never return to the same pose. Step 4 above exists because overfitting the bridge to a hopeless source wastes more time than re-exporting does.

Animated WebP is almost always a better web target than GIF once the cleanup is done.

## 🗺️ Project Map

```text
SKILL.md                Skill definition and workflow
scripts/process_gif.py  The whole tool — animated and still modes
agents/openai.yaml      Agent-facing config
```

## 🔗 Related

- **[webp-me-daddy](https://github.com/BrinShadewater/Webp-Me-Daddy-Skill)** — the still-image site pipeline. It calls this script for its `animate` command, so for website assets start there instead.
