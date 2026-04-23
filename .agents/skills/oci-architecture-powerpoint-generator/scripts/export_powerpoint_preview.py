#!/usr/bin/env python3
"""Export a PowerPoint deck to a preview image using PowerPoint and Quick Look."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Input .pptx path")
    parser.add_argument("--pdf-out", type=Path, help="Intermediate PDF path")
    parser.add_argument("--image-out", type=Path, help="Final preview image path")
    parser.add_argument("--size", type=int, default=2400, help="Quick Look preview size")
    args = parser.parse_args()

    input_path = args.input.resolve()
    pdf_out = (args.pdf_out or Path("/tmp") / f"{input_path.stem}.pdf").resolve()
    image_out = (args.image_out or Path("/tmp") / f"{input_path.stem}.png").resolve()

    run(
        [
            "osascript",
            "-e",
            'tell application "Microsoft PowerPoint"',
            "-e",
            "activate",
            "-e",
            f'open "{input_path}"',
            "-e",
            "delay 1",
            "-e",
            f'save active presentation in POSIX file "{pdf_out}" as save as PDF',
            "-e",
            "close active presentation saving no",
            "-e",
            "end tell",
        ]
    )

    run(["qlmanage", "-t", "-s", str(args.size), "-o", str(pdf_out.parent), str(pdf_out)])
    generated_png = pdf_out.parent / f"{pdf_out.name}.png"
    if not generated_png.exists():
        raise SystemExit(f"Quick Look did not produce the expected thumbnail: {generated_png}")

    image_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(generated_png, image_out)

    print(f"PDF: {pdf_out}")
    print(f"Preview: {image_out}")


if __name__ == "__main__":
    main()
