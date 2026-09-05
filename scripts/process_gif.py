#!/usr/bin/env python
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageOps, ImageSequence
except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency message
    raise SystemExit("Pillow is required. Install it with: python -m pip install Pillow") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a matte-black GIF into a transparent WebP animation or still."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("src", type=Path, help="Source GIF path")
    common.add_argument("out", type=Path, help="Output WebP path")
    common.add_argument("--size", type=int, default=220, help="Maximum output dimension in pixels")
    common.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Near-black alpha threshold. Lower values preserve more dark detail.",
    )
    common.add_argument(
        "--loop-start",
        type=int,
        default=None,
        help="Optional inclusive first frame index for trimming to a cleaner cycle.",
    )
    common.add_argument(
        "--loop-end",
        type=int,
        default=None,
        help="Optional inclusive last frame index for trimming to a cleaner cycle.",
    )

    animated = subparsers.add_parser("animated", parents=[common], help="Create an animated transparent WebP")
    animated.add_argument(
        "--speed-scale",
        type=float,
        default=1.12,
        help="Playback scale. Greater than 1 slows playback, less than 1 speeds it up.",
    )
    animated.add_argument(
        "--midpoint-frames",
        type=int,
        default=1,
        help="Number of interpolated frames inserted between adjacent source frames.",
    )
    animated.add_argument(
        "--bridge-frames",
        type=int,
        default=8,
        help="Number of eased bridge frames appended from the last frame back to the first.",
    )
    animated.add_argument(
        "--bridge-duration",
        type=int,
        default=38,
        help="Duration in milliseconds for each bridge frame.",
    )
    animated.add_argument(
        "--quality",
        type=int,
        default=80,
        help="Animated WebP quality from 0-100.",
    )
    animated.add_argument(
        "--method",
        type=int,
        default=4,
        help="Animated WebP encoding effort from 0-6 (libwebp's own default is 4; 0 is fastest and largest).",
    )

    still = subparsers.add_parser("still", parents=[common], help="Extract a single transparent WebP still")
    still.add_argument(
        "--still-frame",
        type=int,
        default=0,
        help="Frame index inside the selected range to export for still mode.",
    )

    return parser.parse_args()


def matte_to_alpha(frame: Image.Image, size: int, threshold: int) -> Image.Image:
    """Knock out the black matte, keeping any transparency the source already had."""
    rgba = frame.convert("RGBA")
    rgba.thumbnail((size, size), Image.Resampling.LANCZOS)
    existing = rgba.getchannel("A")
    gray = ImageOps.grayscale(rgba.convert("RGB"))
    matte = gray.point(lambda px: 0 if px <= threshold else 255, "L")
    # Both masks are 0/255, so multiply is an AND: transparent stays transparent,
    # matte-black becomes transparent, everything else keeps its source alpha.
    rgba.putalpha(ImageChops.multiply(existing, matte))
    return rgba


def load_frames(
    src: Path,
    size: int,
    threshold: int,
    loop_start: int | None,
    loop_end: int | None,
) -> tuple[list[Image.Image], list[int]]:
    image = Image.open(src)
    selected_frames: list[Image.Image] = []
    selected_durations: list[int] = []

    if loop_start is not None and loop_start < 0:
        raise ValueError("--loop-start must be 0 or greater.")
    if loop_end is not None and loop_end < 0:
        raise ValueError("--loop-end must be 0 or greater.")
    if loop_start is not None and loop_end is not None and loop_start > loop_end:
        raise ValueError("--loop-start cannot be greater than --loop-end.")

    for index, frame in enumerate(ImageSequence.Iterator(image)):
        if loop_start is not None and index < loop_start:
            continue
        if loop_end is not None and index > loop_end:
            continue

        processed = matte_to_alpha(frame, size=size, threshold=threshold)
        selected_frames.append(processed)
        selected_durations.append(frame.info.get("duration", 40))

    if not selected_frames:
        raise ValueError("No frames matched the selected range.")

    return selected_frames, selected_durations


def build_animation(
    frames: list[Image.Image],
    durations: list[int],
    speed_scale: float,
    midpoint_frames: int,
    bridge_frames: int,
    bridge_duration: int,
):
    output_frames: list[Image.Image] = []
    output_durations: list[int] = []

    intended_total = 0
    for index, frame in enumerate(frames):
        is_last = index == len(frames) - 1
        next_frame = frames[(index + 1) % len(frames)]
        scaled_duration = max(20, int(round(durations[index] * speed_scale)))
        intended_total += scaled_duration

        # With a bridge, the seam is the bridge's job: interpolating the last frame
        # toward frame 0 here and then bridging from the last frame again made the
        # loop walk halfway home and jump back.
        if midpoint_frames <= 0 or (is_last and bridge_frames > 0):
            output_frames.append(frame)
            output_durations.append(scaled_duration)
            continue

        # The source frame keeps ~58% of its time; the midpoints share the rest. The
        # 18 ms floor is a decoder sanity limit, and when it binds the base frame gives
        # the time up, so a frame's total only grows when both floors bind.
        base_share = int(round(scaled_duration * 0.58))
        midpoint_share = max(18, int(round((scaled_duration - base_share) / midpoint_frames)))
        base_share = max(18, scaled_duration - midpoint_frames * midpoint_share)

        output_frames.append(frame)
        output_durations.append(base_share)

        for step in range(1, midpoint_frames + 1):
            blend_amount = step / (midpoint_frames + 1)
            midpoint = Image.blend(frame, next_frame, blend_amount)
            output_frames.append(midpoint)
            output_durations.append(midpoint_share)

    stretched = sum(output_durations) - intended_total
    if stretched > 0:
        print(
            f"note: the 18 ms per-frame floor stretched playback by {stretched} ms "
            f"({stretched / intended_total:.0%}); use fewer --midpoint-frames or a larger --speed-scale.",
            file=sys.stderr,
        )

    last = frames[-1]
    first = frames[0]
    for step in range(1, bridge_frames + 1):
        t = step / (bridge_frames + 1)
        eased = 0.5 - 0.5 * math.cos(math.pi * t)
        bridge = Image.blend(last, first, eased)
        output_frames.append(bridge)
        output_durations.append(max(18, bridge_duration))

    return output_frames, output_durations


def save_animation(
    out: Path,
    frames: list[Image.Image],
    durations: list[int],
    quality: int,
    method: int,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=quality,
        method=method,
    )


def save_still(out: Path, frame: Image.Image, quality: int = 100, method: int = 6) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.save(out, quality=quality, method=method)


def main() -> int:
    args = parse_args()

    if not args.src.exists():
        raise SystemExit(f"Source file does not exist: {args.src}")

    frames, durations = load_frames(
        src=args.src,
        size=args.size,
        threshold=args.threshold,
        loop_start=args.loop_start,
        loop_end=args.loop_end,
    )

    if args.mode == "still":
        still_index = max(0, min(args.still_frame, len(frames) - 1))
        save_still(args.out, frames[still_index])
        print(f"Saved transparent still to {args.out}")
        return 0

    animated_frames, animated_durations = build_animation(
        frames=frames,
        durations=durations,
        speed_scale=args.speed_scale,
        midpoint_frames=args.midpoint_frames,
        bridge_frames=args.bridge_frames,
        bridge_duration=args.bridge_duration,
    )
    save_animation(
        args.out,
        animated_frames,
        animated_durations,
        quality=args.quality,
        method=args.method,
    )
    print(
        f"Saved transparent animation to {args.out} "
        f"({len(animated_frames)} frames, avg {sum(animated_durations) / len(animated_durations):.2f}ms)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
