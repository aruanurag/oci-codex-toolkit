#!/usr/bin/env python3
"""Render a local SVG preview for an Excalidraw scene."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from generate_excalidraw import write_preview


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path, help="source .excalidraw file")
    parser.add_argument("output", type=Path, help="destination SVG preview")
    args = parser.parse_args()
    try:
        parsed = json.loads(args.scene.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict) or not isinstance(parsed.get("elements"), list):
            raise ValueError("scene must contain an elements list")
        write_preview(parsed, args.output)
        print(json.dumps({"preview_svg": str(args.output.resolve()), "element_count": len(parsed["elements"])}, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
