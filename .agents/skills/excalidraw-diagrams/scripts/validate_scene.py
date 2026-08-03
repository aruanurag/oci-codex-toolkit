#!/usr/bin/env python3
"""Check an Excalidraw scene for structural and readability problems."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def problem(items: list[dict[str, str]], level: str, message: str, element_id: str | None = None) -> None:
    item = {"level": level, "message": message}
    if element_id:
        item["element_id"] = element_id
    items.append(item)


def validate(scene: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(scene, dict):
        problem(issues, "error", "scene must be a JSON object")
        return issues
    if scene.get("type") != "excalidraw":
        problem(issues, "error", "top-level type must be excalidraw")
    elements = scene.get("elements")
    if not isinstance(elements, list):
        problem(issues, "error", "top-level elements must be a list")
        return issues
    ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for element in elements:
        if not isinstance(element, dict):
            problem(issues, "error", "every element must be an object")
            continue
        element_id = element.get("id")
        if not isinstance(element_id, str) or not element_id:
            problem(issues, "error", "element is missing a non-empty id")
            continue
        if element_id in ids:
            problem(issues, "error", "duplicate element id", element_id)
        ids.add(element_id)
        by_id[element_id] = element
        if not isinstance(element.get("type"), str):
            problem(issues, "error", "element is missing a type", element_id)
        for dimension in ("x", "y", "width", "height"):
            if not isinstance(element.get(dimension), (int, float)):
                problem(issues, "error", f"{dimension} must be numeric", element_id)
        if element.get("type") in {"rectangle", "ellipse", "diamond"} and (abs(element.get("width", 0)) < 8 or abs(element.get("height", 0)) < 8):
            problem(issues, "warning", "shape is too small to be readable", element_id)
        if element.get("type") == "text":
            text = element.get("text")
            if not isinstance(text, str) or not text.strip():
                problem(issues, "warning", "text element is empty", element_id)
            elif len(text) > 90:
                problem(issues, "warning", "text is long; use a note or supporting content instead", element_id)
        if element.get("type") == "arrow":
            points = element.get("points")
            if not isinstance(points, list) or len(points) < 2:
                problem(issues, "error", "arrow needs at least two points", element_id)
    for element_id, element in by_id.items():
        if element.get("type") == "text":
            container = element.get("containerId")
            if container is not None and container not in by_id:
                problem(issues, "warning", "containerId does not reference a scene element", element_id)
        if element.get("type") == "arrow":
            for binding_name in ("startBinding", "endBinding"):
                binding = element.get(binding_name)
                if binding is not None and (not isinstance(binding, dict) or binding.get("elementId") not in by_id):
                    problem(issues, "warning", f"{binding_name} does not reference a scene element", element_id)
    if not elements:
        problem(issues, "warning", "scene has no elements")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()
    try:
        scene = json.loads(args.scene.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "issues": [{"level": "error", "message": str(exc)}]}, indent=2))
        return 1
    issues = validate(scene)
    errors = [item for item in issues if item["level"] == "error"]
    warnings = [item for item in issues if item["level"] == "warning"]
    print(json.dumps({"ok": not errors and (not args.strict or not warnings), "element_count": len(scene.get("elements", [])) if isinstance(scene, dict) else 0, "issues": issues}, indent=2))
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
