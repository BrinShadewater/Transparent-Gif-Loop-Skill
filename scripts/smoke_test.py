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


def main() -> int:
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
