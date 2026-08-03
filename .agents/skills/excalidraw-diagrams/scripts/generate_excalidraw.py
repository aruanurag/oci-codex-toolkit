#!/usr/bin/env python3
"""Generate a small, editable Excalidraw scene from a node-and-edge JSON spec."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_STROKE = "#1f2937"
DEFAULT_FILL = "#eff6ff"
GROUP_FILL = "#f8fafc"
ACCENT = "#2563eb"


def stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16) % 2_000_000_000


def clean_id(value: str, suffix: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-") or "element"
    return f"{normalized}-{suffix}"


def measure_text(value: str, font_size: int = 20) -> tuple[float, float]:
    lines = value.splitlines() or [""]
    return max(1, max(len(line) for line in lines)) * font_size * 0.58, max(1, len(lines)) * font_size * 1.3


def base_element(element_id: str, element_type: str, x: float, y: float, width: float, height: float) -> dict[str, Any]:
    seed = stable_int(element_id)
    return {
        "id": element_id,
        "type": element_type,
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(width, 2),
        "height": round(height, 2),
        "angle": 0,
        "strokeColor": DEFAULT_STROKE,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": None,
        "roundness": None,
        "seed": seed,
        "version": 1,
        "versionNonce": stable_int(f"{element_id}:nonce"),
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }


def text_element(element_id: str, value: str, x: float, y: float, *, container_id: str | None = None, font_size: int = 20, color: str = DEFAULT_STROKE, align: str = "center") -> dict[str, Any]:
    width, height = measure_text(value, font_size)
    item = base_element(element_id, "text", x, y, width, height)
    item.update({
        "strokeColor": color,
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "roughness": 0,
        "fontSize": font_size,
        "fontFamily": 2,
        "text": value,
        "originalText": value,
        "textAlign": align,
        "verticalAlign": "middle",
        "containerId": container_id,
        "autoResize": True,
        "lineHeight": 1.25,
    })
    return item


def color(value: Any, fallback: str) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def read_json(source: str) -> dict[str, Any]:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("The spec must be a JSON object.")
    return parsed


def validate_spec(spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    nodes = spec.get("nodes")
    edges = spec.get("edges", [])
    direction = spec.get("direction", "LR")
    if direction not in {"LR", "TB"}:
        raise ValueError("direction must be LR or TB")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("nodes must be a non-empty list")
    if not isinstance(edges, list):
        raise ValueError("edges must be a list")
    ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"].strip():
            raise ValueError("every node needs a non-empty string id")
        if not isinstance(node.get("label"), str) or not node["label"].strip():
            raise ValueError(f"node {node['id']!r} needs a non-empty label")
        if node["id"] in ids:
            raise ValueError(f"duplicate node id: {node['id']}")
        ids.add(node["id"])
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("from") not in ids or edge.get("to") not in ids:
            raise ValueError("each edge must refer to existing node ids with from and to")
    return nodes, edges, direction


def node_positions(nodes: list[dict[str, Any]], direction: str) -> dict[str, tuple[float, float, float, float]]:
    locations: dict[str, tuple[float, float, float, float]] = {}
    for position, node in enumerate(nodes):
        label = node["label"]
        label_width, label_height = measure_text(label)
        width = max(180, min(280, label_width + 48))
        height = max(72, label_height + 34)
        x, y = (100 + position * 350, 150) if direction == "LR" else (180, 120 + position * 180)
        locations[node["id"]] = (x, y, width, height)
    return locations


def group_definitions(spec: dict[str, Any], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    defined: dict[str, dict[str, Any]] = {}
    raw_groups = spec.get("groups", [])
    if raw_groups is not None and not isinstance(raw_groups, list):
        raise ValueError("groups must be a list")
    for raw in raw_groups or []:
        if not isinstance(raw, dict) or not isinstance(raw.get("label"), str) or not raw["label"].strip():
            raise ValueError("every group needs a non-empty label")
        key = raw.get("id", raw["label"])
        defined[str(key)] = {**raw, "_key": str(key), "nodes": list(raw.get("nodes", []))}
    for node in nodes:
        group = node.get("group")
        if isinstance(group, str) and group.strip():
            entry = defined.setdefault(group, {"_key": group, "label": group, "nodes": []})
            if node["id"] not in entry["nodes"]:
                entry["nodes"].append(node["id"])
    return [group for group in defined.values() if group["nodes"]]


def make_scene(spec: dict[str, Any]) -> dict[str, Any]:
    nodes, edges, direction = validate_spec(spec)
    positions = node_positions(nodes, direction)
    elements: list[dict[str, Any]] = []
    title = spec.get("title")
    if isinstance(title, str) and title.strip():
        elements.append(text_element("diagram-title", title.strip(), 100, 45, font_size=28, align="left"))

    for group in group_definitions(spec, nodes):
        members = [positions[node_id] for node_id in group["nodes"] if node_id in positions]
        if not members:
            continue
        left = min(item[0] for item in members) - 32
        top = min(item[1] for item in members) - 52
        right = max(item[0] + item[2] for item in members) + 32
        bottom = max(item[1] + item[3] for item in members) + 32
        group_id = clean_id(group["_key"], "group")
        box = base_element(group_id, "rectangle", left, top, right - left, bottom - top)
        box.update({
            "strokeColor": color(group.get("color"), "#94a3b8"),
            "backgroundColor": color(group.get("fill"), GROUP_FILL),
            "strokeStyle": "dashed",
            "roundness": {"type": 3},
            "customData": {"role": "group"},
        })
        label = text_element(clean_id(group["_key"], "group-label"), group["label"], left + 16, top + 12, font_size=16, color="#475569", align="left")
        elements.extend([box, label])

    shape_ids: dict[str, str] = {}
    for node in nodes:
        x, y, width, height = positions[node["id"]]
        shape_id = clean_id(node["id"], "node")
        label_id = clean_id(node["id"], "label")
        shape_ids[node["id"]] = shape_id
        shape = base_element(shape_id, "rectangle", x, y, width, height)
        shape.update({
            "strokeColor": color(node.get("color"), ACCENT),
            "backgroundColor": color(node.get("fill"), DEFAULT_FILL),
            "roundness": {"type": 3},
            "boundElements": [{"id": label_id, "type": "text"}],
        })
        label_width, label_height = measure_text(node["label"])
        label = text_element(label_id, node["label"], x + (width - label_width) / 2, y + (height - label_height) / 2, container_id=shape_id)
        elements.extend([shape, label])

    for index, edge in enumerate(edges):
        source = positions[edge["from"]]
        target = positions[edge["to"]]
        source_id, target_id = shape_ids[edge["from"]], shape_ids[edge["to"]]
        if direction == "LR":
            start_x, start_y = source[0] + source[2], source[1] + source[3] / 2
            end_x, end_y = target[0], target[1] + target[3] / 2
        else:
            start_x, start_y = source[0] + source[2] / 2, source[1] + source[3]
            end_x, end_y = target[0] + target[2] / 2, target[1]
        arrow_id = clean_id(f"{edge['from']}-{edge['to']}-{index}", "edge")
        arrow = base_element(arrow_id, "arrow", start_x, start_y, end_x - start_x, end_y - start_y)
        arrow.update({
            "strokeColor": color(edge.get("color"), DEFAULT_STROKE),
            "backgroundColor": "transparent",
            "lastCommittedPoint": None,
            "startBinding": {"elementId": source_id, "focus": 0, "gap": 1},
            "endBinding": {"elementId": target_id, "focus": 0, "gap": 1},
            "startArrowhead": None,
            "endArrowhead": "arrow",
            "points": [[0, 0], [round(end_x - start_x, 2), round(end_y - start_y, 2)]],
            "elbowed": False,
        })
        elements.append(arrow)
        for shape_id in (source_id, target_id):
            shape = next(item for item in elements if item["id"] == shape_id)
            shape["boundElements"].append({"id": arrow_id, "type": "arrow"})
        if isinstance(edge.get("label"), str) and edge["label"].strip():
            label = edge["label"].strip()
            label_width, _ = measure_text(label, 15)
            midpoint_x, midpoint_y = (start_x + end_x) / 2, (start_y + end_y) / 2
            label_x = midpoint_x - label_width / 2
            label_y = midpoint_y - 28 if direction == "LR" else midpoint_y - 10
            elements.append(text_element(clean_id(arrow_id, "label"), label, label_x, label_y, font_size=15, color="#374151"))

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "codex-excalidraw-diagrams",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": {},
    }


def scene_bounds(scene: dict[str, Any]) -> tuple[float, float, float, float]:
    visible = [item for item in scene.get("elements", []) if not item.get("isDeleted")]
    if not visible:
        return 0, 0, 800, 600
    left = min(float(item.get("x", 0)) for item in visible)
    top = min(float(item.get("y", 0)) for item in visible)
    right = max(float(item.get("x", 0)) + abs(float(item.get("width", 0))) for item in visible)
    bottom = max(float(item.get("y", 0)) + abs(float(item.get("height", 0))) for item in visible)
    return left - 40, top - 40, max(200, right - left + 80), max(160, bottom - top + 80)


def scene_to_svg(scene: dict[str, Any]) -> str:
    left, top, width, height = scene_bounds(scene)
    rendered: list[str] = []
    for item in scene.get("elements", []):
        if item.get("isDeleted"):
            continue
        item_type = item.get("type")
        x, y = float(item.get("x", 0)), float(item.get("y", 0))
        item_width, item_height = float(item.get("width", 0)), float(item.get("height", 0))
        stroke = html.escape(str(item.get("strokeColor", DEFAULT_STROKE)))
        fill = html.escape(str(item.get("backgroundColor", "transparent")))
        opacity = max(0, min(100, int(item.get("opacity", 100)))) / 100
        if item_type in {"rectangle", "ellipse", "diamond"}:
            dash = ' stroke-dasharray="8 6"' if item.get("strokeStyle") == "dashed" else ""
            if item_type == "ellipse":
                rendered.append(f'<ellipse cx="{x + item_width / 2}" cy="{y + item_height / 2}" rx="{abs(item_width) / 2}" ry="{abs(item_height) / 2}" fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"{dash}/>')
            elif item_type == "diamond":
                points = f"{x + item_width / 2},{y} {x + item_width},{y + item_height / 2} {x + item_width / 2},{y + item_height} {x},{y + item_height / 2}"
                rendered.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"{dash}/>')
            else:
                radius = 10 if item.get("roundness") else 0
                rendered.append(f'<rect x="{x}" y="{y}" width="{abs(item_width)}" height="{abs(item_height)}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2" opacity="{opacity}"{dash}/>')
        elif item_type in {"arrow", "line"}:
            points = item.get("points") or [[0, 0], [item_width, item_height]]
            absolute = " ".join(f"{x + float(point[0])},{y + float(point[1])}" for point in points if isinstance(point, list) and len(point) >= 2)
            marker = ' marker-end="url(#arrowhead)"' if item_type == "arrow" and item.get("endArrowhead") else ""
            rendered.append(f'<polyline points="{absolute}" fill="none" stroke="{stroke}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"{marker}/>')
        elif item_type == "text":
            size = int(item.get("fontSize", 20))
            lines = str(item.get("text", "")).splitlines() or [""]
            line_height = size * 1.25
            for line_number, line in enumerate(lines):
                rendered.append(f'<text x="{x}" y="{y + size + line_number * line_height}" fill="{stroke}" font-family="Arial, sans-serif" font-size="{size}" text-anchor="start">{html.escape(line)}</text>')
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left} {top} {width} {height}" width="{width:.0f}" height="{height:.0f}" role="img" aria-label="Excalidraw diagram preview">',
        '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><path d="M0,0 L10,3.5 L0,7 z" fill="#1f2937"/></marker></defs>',
        f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="#ffffff"/>',
        *rendered,
        '</svg>',
    ])


def write_preview(scene: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(scene_to_svg(scene), encoding="utf-8")


def default_preview_path(output: Path) -> Path:
    return output.with_name(f"{output.stem}-preview.svg")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="JSON spec path, or - to read JSON from stdin")
    parser.add_argument("output", type=Path, help="destination .excalidraw file")
    parser.add_argument("--preview", nargs="?", const="AUTO", metavar="SVG", help="also write an SVG preview; omit SVG to use output-preview.svg")
    args = parser.parse_args()
    try:
        scene = make_scene(read_json(args.spec))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
        result: dict[str, Any] = {"excalidraw": str(args.output.resolve()), "element_count": len(scene["elements"])}
        if args.preview is not None:
            preview = default_preview_path(args.output) if args.preview == "AUTO" else Path(args.preview)
            write_preview(scene, preview)
            result["preview_svg"] = str(preview.resolve())
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
