#!/usr/bin/env python3
"""Flag common visual crowding and collision problems in an Excalidraw scene."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SHAPE_TYPES = {"rectangle", "ellipse", "diamond"}
MIN_GAP = 10.0


def issue(items: list[dict[str, Any]], kind: str, first: str, second: str, message: str) -> None:
    items.append({"level": "warning", "kind": kind, "elements": [first, second], "message": message})


def bounds(element: dict[str, Any]) -> tuple[float, float, float, float] | None:
    try:
        x, y = float(element["x"]), float(element["y"])
        width, height = float(element["width"]), float(element["height"])
    except (KeyError, TypeError, ValueError):
        return None
    return (min(x, x + width), min(y, y + height), max(x, x + width), max(y, y + height))


def intersection(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float]:
    return (max(0.0, min(a[2], b[2]) - max(a[0], b[0])), max(0.0, min(a[3], b[3]) - max(a[1], b[1])))


def gap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float]:
    return (max(0.0, max(a[0], b[0]) - min(a[2], b[2])), max(0.0, max(a[1], b[1]) - min(a[3], b[3])))


def point_inside(point: tuple[float, float], box: tuple[float, float, float, float]) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    first = orientation(a, b, c)
    second = orientation(a, b, d)
    third = orientation(c, d, a)
    fourth = orientation(c, d, b)
    return first * second <= 0 and third * fourth <= 0


def segment_hits_box(start: tuple[float, float], end: tuple[float, float], box: tuple[float, float, float, float]) -> bool:
    if point_inside(start, box) or point_inside(end, box):
        return True
    corners = [(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
    return any(segments_intersect(start, end, corners[index], corners[(index + 1) % 4]) for index in range(4))


def is_group(element: dict[str, Any]) -> bool:
    return element.get("customData", {}).get("role") == "group"


def is_bound_pair(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return first.get("containerId") == second.get("id") or second.get("containerId") == first.get("id")


def review(scene: dict[str, Any]) -> list[dict[str, Any]]:
    elements = [element for element in scene.get("elements", []) if isinstance(element, dict) and not element.get("isDeleted")]
    candidates = [element for element in elements if element.get("type") in SHAPE_TYPES | {"text"} and not is_group(element) and bounds(element)]
    findings: list[dict[str, Any]] = []

    for index, first in enumerate(candidates):
        first_box = bounds(first)
        if first_box is None:
            continue
        for second in candidates[index + 1 :]:
            if is_bound_pair(first, second):
                continue
            second_box = bounds(second)
            if second_box is None:
                continue
            overlap_width, overlap_height = intersection(first_box, second_box)
            if overlap_width and overlap_height:
                smallest_area = min((first_box[2] - first_box[0]) * (first_box[3] - first_box[1]), (second_box[2] - second_box[0]) * (second_box[3] - second_box[1]))
                overlap_area = overlap_width * overlap_height
                if smallest_area and overlap_area / smallest_area >= 0.05:
                    issue(findings, "overlap", first["id"], second["id"], "peer elements overlap; separate them or intentionally bind the label to its container")
                continue
            horizontal_gap, vertical_gap = gap(first_box, second_box)
            if (horizontal_gap < MIN_GAP and overlap_height > 0) or (vertical_gap < MIN_GAP and overlap_width > 0):
                issue(findings, "crowding", first["id"], second["id"], "peer elements are tightly packed; add whitespace for scanability")

    shapes = [element for element in elements if element.get("type") in SHAPE_TYPES and not is_group(element) and bounds(element)]
    for arrow in (element for element in elements if element.get("type") == "arrow"):
        points = arrow.get("points")
        if not isinstance(points, list) or len(points) < 2:
            continue
        try:
            origin = (float(arrow["x"]), float(arrow["y"]))
            path = [(origin[0] + float(point[0]), origin[1] + float(point[1])) for point in points]
        except (KeyError, TypeError, ValueError, IndexError):
            continue
        bound_ids = {binding.get("elementId") for binding in (arrow.get("startBinding"), arrow.get("endBinding")) if isinstance(binding, dict)}
        for shape in shapes:
            if shape.get("id") in bound_ids:
                continue
            shape_box = bounds(shape)
            if shape_box and any(segment_hits_box(start, end, shape_box) for start, end in zip(path, path[1:])):
                issue(findings, "arrow_collision", arrow["id"], shape["id"], "arrow runs through an unrelated node; reroute it around the node")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("--strict", action="store_true", help="return non-zero when review findings exist")
    args = parser.parse_args()
    try:
        scene = json.loads(args.scene.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "findings": [{"level": "error", "message": str(exc)}]}, indent=2))
        return 1
    if not isinstance(scene, dict):
        print(json.dumps({"ok": False, "findings": [{"level": "error", "message": "scene must be a JSON object"}]}, indent=2))
        return 1
    findings = review(scene)
    print(json.dumps({"ok": not findings, "finding_count": len(findings), "findings": findings}, indent=2))
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
