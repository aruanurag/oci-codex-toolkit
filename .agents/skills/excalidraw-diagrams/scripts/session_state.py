#!/usr/bin/env python3
"""Persist one local Excalidraw handoff for an incremental revision workflow."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def state_dir(value: str | None) -> Path:
    return Path(value or os.environ.get("CODEX_EXCALIDRAW_STATE_DIR", Path.home() / ".codex" / "excalidraw-diagrams"))


def copy_if_present(source: str | None, destination: Path) -> str | None:
    if not source:
        return None
    candidate = Path(source)
    if not candidate.is_file():
        raise ValueError(f"not a readable file: {candidate}")
    shutil.copy2(candidate, destination)
    return str(destination.resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", help="state directory; defaults to CODEX_EXCALIDRAW_STATE_DIR or ~/.codex/excalidraw-diagrams")
    commands = parser.add_subparsers(dest="command", required=True)
    save = commands.add_parser("save", help="save a local revision record")
    save.add_argument("--scene", required=True)
    save.add_argument("--preview")
    save.add_argument("--spec")
    save.add_argument("--request")
    commands.add_parser("show", help="show the latest local revision record")
    args = parser.parse_args()
    root = state_dir(args.state_dir)
    metadata_path = root / "latest.json"
    try:
        if args.command == "show":
            if not metadata_path.is_file():
                print(json.dumps({"exists": False}, indent=2))
                return 0
            record = json.loads(metadata_path.read_text(encoding="utf-8"))
            record["exists"] = True
            print(json.dumps(record, indent=2))
            return 0
        root.mkdir(parents=True, exist_ok=True)
        record = {
            "scene": copy_if_present(args.scene, root / "latest.excalidraw"),
            "preview": copy_if_present(args.preview, root / "latest-preview.svg"),
            "spec": copy_if_present(args.spec, root / "latest-spec.json"),
            "request": args.request,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        metadata_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        record["exists"] = True
        print(json.dumps(record, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
