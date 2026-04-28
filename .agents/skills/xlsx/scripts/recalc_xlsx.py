#!/usr/bin/env python3
"""Recalculate an .xlsx workbook with LibreOffice or Microsoft Excel when available."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_libreoffice() -> str | None:
    for command in ("libreoffice", "soffice"):
        path = shutil.which(command)
        if path:
            return path
    mac_path = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    if mac_path.exists():
        return str(mac_path)
    return None


def excel_is_available() -> bool:
    return sys.platform == "darwin" and Path("/Applications/Microsoft Excel.app").exists()


def run_libreoffice(input_path: Path, output_path: Path, timeout: int) -> None:
    executable = find_libreoffice()
    if not executable:
        raise RuntimeError("LibreOffice was not found on PATH or in /Applications.")

    with tempfile.TemporaryDirectory(prefix="xlsx-recalc-lo-") as temp_dir:
        temp = Path(temp_dir)
        user_profile = temp / "profile"
        out_dir = temp / "out"
        out_dir.mkdir()
        command = [
            executable,
            f"-env:UserInstallation=file://{user_profile}",
            "--headless",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(out_dir),
            str(input_path),
        ]
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(
                "LibreOffice recalculation failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        converted = out_dir / input_path.name
        if not converted.exists():
            candidates = sorted(out_dir.glob("*.xlsx"))
            if not candidates:
                raise RuntimeError("LibreOffice did not produce an .xlsx output file.")
            converted = candidates[0]
        shutil.copyfile(converted, output_path)


def applescript_quote(value: Path) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def run_excel(input_path: Path, output_path: Path, timeout: int) -> None:
    if not excel_is_available():
        raise RuntimeError("Microsoft Excel automation is available only on macOS with Microsoft Excel installed.")

    # Work on a copy so a failed automation pass never corrupts the input workbook.
    if input_path.resolve() != output_path.resolve():
        shutil.copyfile(input_path, output_path)

    script = f'''
set workbookPath to "{applescript_quote(output_path)}"
tell application "Microsoft Excel"
    set display alerts to false
    open POSIX file workbookPath
    set wb to active workbook
    calculate full rebuild
    save wb
    close wb saving no
end tell
'''
    result = subprocess.run(["osascript", "-e", script], text=True, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            "Microsoft Excel recalculation failed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def choose_backends(requested: str) -> list[str]:
    if requested == "auto":
        return ["libreoffice", "excel"]
    return [requested]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input .xlsx workbook.")
    parser.add_argument("--output", type=Path, help="Output workbook path. Defaults to <input>.recalculated.xlsx.")
    parser.add_argument("--in-place", action="store_true", help="Replace the input workbook after successful recalculation.")
    parser.add_argument("--backend", choices=("auto", "libreoffice", "excel"), default="auto")
    parser.add_argument("--timeout", type=int, default=120, help="Backend timeout in seconds.")
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        raise SystemExit(f"Input workbook does not exist: {input_path}")
    if input_path.suffix.lower() != ".xlsx":
        raise SystemExit("This script expects an .xlsx workbook.")
    if args.in_place and args.output:
        raise SystemExit("Use either --output or --in-place, not both.")

    final_output = (
        input_path
        if args.in_place
        else (args.output.resolve() if args.output else input_path.with_name(f"{input_path.stem}.recalculated.xlsx"))
    )

    with tempfile.TemporaryDirectory(prefix="xlsx-recalc-safe-") as temp_dir:
        temp_output = Path(temp_dir) / final_output.name
        errors: list[str] = []
        for backend in choose_backends(args.backend):
            try:
                if backend == "libreoffice":
                    run_libreoffice(input_path, temp_output, args.timeout)
                elif backend == "excel":
                    run_excel(input_path, temp_output, args.timeout)
                else:
                    raise RuntimeError(f"Unsupported backend: {backend}")
                final_output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(temp_output, final_output)
                print(f"Recalculated workbook written to {final_output} using {backend}.")
                return 0
            except Exception as exc:  # noqa: BLE001 - report all backend failures cleanly.
                errors.append(f"{backend}: {exc}")

    print("Unable to recalculate workbook with available backends.", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    print("Install LibreOffice, use Microsoft Excel on macOS, or state that cached formula values may be stale.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
