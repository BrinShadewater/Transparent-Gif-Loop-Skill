#!/usr/bin/env python3
"""Offline smoke tests for transparent GIF conversion."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent


def make_source_gif(path: Path) -> None:
    frames = []
    for offset, color in [(3, (255, 0, 0)), (8, (0, 160, 255))]:
        frame = Image.new("RGB", (24, 24), (0, 0, 0))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((offset, 6, offset + 8, 16), fill=color)
        frames.append(frame)

    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=[40, 40],
        loop=0,
    )


def run_process(*args: str) -> None:
    subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "process_gif.py"), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def assert_webp(path: Path) -> None:
    assert path.exists(), f"missing output: {path}"
    with Image.open(path) as image:
        assert image.format == "WEBP"
        assert image.width <= 16
        assert image.height <= 16


def make_transparent_gif(path: Path) -> None:
    """A GIF whose transparent pixels map to WHITE, the case luminance alone gets wrong."""
    frame = Image.new("RGBA", (24, 24), (255, 255, 255, 255))
    for x in range(8):
        for y in range(8):
            frame.putpixel((x, y), (255, 255, 255, 0))
    frame.save(path, save_all=True, append_images=[frame], duration=[40, 40], loop=0, disposal=2)


def unit_checks() -> None:
    sys.path.insert(0, str(SCRIPT_DIR))
    import process_gif  # noqa: E402

    # Timing: with generous frames the midpoints must not stretch the loop.
    frames = [Image.new("RGBA", (24, 24), (c, c, c, 255)) for c in (40, 120, 200)]
    out_frames, out_durations = process_gif.build_animation(
        frames, [100, 100, 100], speed_scale=1.0, midpoint_frames=2, bridge_frames=0, bridge_duration=40
    )
    assert sum(out_durations) == 300, f"midpoints stretched 300 ms to {sum(out_durations)} ms"
    assert len(out_frames) == 9, len(out_frames)

    # Seam: with a bridge, the last frame gets no midpoints toward frame 0 (no double walk).
    out_frames, _ = process_gif.build_animation(
        frames, [100, 100, 100], speed_scale=1.0, midpoint_frames=1, bridge_frames=2, bridge_duration=40
    )
    assert len(out_frames) == 3 + 2 + 2, f"expected f0 m f1 m f2 + 2 bridge frames, got {len(out_frames)}"

    # Alpha: source transparency survives the matte pass even when it maps to white.
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "transparent.gif"
        make_transparent_gif(src)
        loaded, _ = process_gif.load_frames(src, size=24, threshold=10, loop_start=None, loop_end=None)
    corner = loaded[0].getpixel((2, 2))
    body = loaded[0].getpixel((20, 20))
    assert corner[3] == 0, f"transparent source pixel came back opaque: {corner}"
    assert body[3] == 255, f"opaque white pixel lost its alpha: {body}"


def main() -> int:
    unit_checks()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / "source.gif"
        still = tmp_dir / "still.webp"
        animated = tmp_dir / "animated.webp"

        make_source_gif(source)

        run_process("still", str(source), str(still), "--size", "16", "--threshold", "10")
        assert_webp(still)

        run_process(
            "animated",
            str(source),
            str(animated),
            "--size",
            "16",
            "--threshold",
            "10",
            "--midpoint-frames",
            "0",
            "--bridge-frames",
            "0",
        )
        assert_webp(animated)

    print("transparent-gif-loop smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
