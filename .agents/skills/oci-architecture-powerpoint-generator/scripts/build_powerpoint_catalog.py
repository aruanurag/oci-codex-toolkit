#!/usr/bin/env python3
"""Build a reusable OCI PowerPoint catalog from the bundled Oracle PPT toolkit."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)?\b")

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"p": P_NS, "a": A_NS}

SLIDE_CATEGORY_OVERRIDES = {
    34: "Compute",
    35: "Storage",
    36: "Networking",
    37: "Database",
    38: "Analytics and AI",
    39: "Developer Services",
    40: "Identity and Security",
    41: "Observability and Management",
    42: "Hybrid",
    43: "Migration",
    44: "Governance and Administration",
    45: "Marketplace",
    46: "Applications",
    47: "Other Oracle Services",
}

PHYSICAL_GROUPINGS = [
    {"slide": 27, "path": [4], "title": "Physical - Grouping - OCI Region"},
    {"slide": 27, "path": [5], "title": "Physical - Location - On-Premises"},
    {"slide": 27, "path": [6], "title": "Physical - Location - Internet"},
    {"slide": 27, "path": [7], "title": "Physical - Location - 3rd Party Cloud"},
    {"slide": 27, "path": [8], "title": "Physical - Grouping - Availability Domain"},
    {"slide": 27, "path": [9], "title": "Physical - Grouping - Fault Domain"},
    {"slide": 27, "path": [12], "title": "Physical - Grouping - VCN"},
    {"slide": 27, "path": [13], "title": "Physical - Grouping - Subnet"},
    {"slide": 19, "path": [17], "title": "Physical - Grouping - Oracle Services Network"},
    {"slide": 19, "path": [16], "title": "Physical - Grouping - Optional"},
    {"slide": 19, "path": [23], "title": "Physical - Grouping - Metro Area or Realm"},
]

TEXT_ONLY_EXCLUSIONS = {
    "copyright 2022 oracle and or its affiliates",
    "copyright 2022 oracle and or its affiliates.",
    "copyright 2022 oracle and or its affiliates |",
    "copyright 2022 oracle and or its affiliates  |",
    "landscape blank template",
    "portrait blank template",
    "connectors",
    "sample connectors",
    "usage examples",
    "logical",
    "physical",
    "icons",
}


def normalize(text: str) -> str:
    text = html.unescape(text).replace("\xa0", " ")
    text = text.lower().strip()
    text = NORMALIZE_RE.sub(" ", text)
    return " ".join(text.split())


def tokenize(text: str) -> list[str]:
    return [token for token in normalize(text).split() if token]


def extract_acronyms(text: str) -> list[str]:
    return sorted({match.group(0).lower() for match in ACRONYM_RE.finditer(text)})


def default_paths() -> tuple[Path, Path, Path]:
    skill_dir = Path(__file__).resolve().parents[1]
    pptx_path = skill_dir / "assets" / "powerpoint" / "oracle-oci-architecture-toolkit-v24.1.pptx"
    json_path = skill_dir / "references" / "icon-catalog.json"
    md_path = skill_dir / "references" / "icon-catalog.md"
    return pptx_path, json_path, md_path


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def slide_path(slide_number: int) -> str:
    return f"ppt/slides/slide{slide_number}.xml"


def parse_presentation(pptx_path: Path) -> dict[int, ET.Element]:
    slides: dict[int, ET.Element] = {}
    with zipfile.ZipFile(pptx_path) as archive:
        for slide_number in set(SLIDE_CATEGORY_OVERRIDES) | {item["slide"] for item in PHYSICAL_GROUPINGS}:
            slides[slide_number] = ET.fromstring(archive.read(slide_path(slide_number)))
    return slides


def get_sp_tree(slide_root: ET.Element) -> ET.Element:
    sp_tree = slide_root.find(f".//{{{P_NS}}}spTree")
    if sp_tree is None:
        raise ValueError("Slide is missing spTree")
    return sp_tree


def extract_text_from_shape(shape: ET.Element) -> str:
    values: list[str] = []
    for text_node in shape.findall(".//a:t", NS):
        value = (text_node.text or "").strip()
        if value:
            values.append(value)
    return " ".join(values)


def get_transform(element: ET.Element) -> tuple[int, int, int, int] | None:
    xfrm = element.find("./p:grpSpPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = element.find("./p:spPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = element.find("./p:pic/p:spPr/a:xfrm", NS)
    if xfrm is None:
        return None
    off = xfrm.find("./a:off", NS)
    ext = xfrm.find("./a:ext", NS)
    if off is None or ext is None:
        return None
    return (
        int(off.attrib.get("x", "0")),
        int(off.attrib.get("y", "0")),
        int(ext.attrib.get("cx", "0")),
        int(ext.attrib.get("cy", "0")),
    )


def clean_title(text: str) -> str:
    parts = []
    for chunk in re.split(r"\s{2,}|\n", text):
        chunk = " ".join(chunk.split())
        if chunk:
            parts.append(chunk)
    return " ".join(parts)


def add_entry(
    catalog: dict[str, dict[str, Any]],
    *,
    title: str,
    slide_number: int,
    path: list[int],
    kind: str,
    bbox: tuple[int, int, int, int] | None,
    source: str,
) -> None:
    title = clean_title(title)
    if not title:
        return

    normalized = normalize(title)
    if normalized in TEXT_ONLY_EXCLUSIONS:
        return

    if title in catalog:
        return

    if " - " in title:
        category, name = title.split(" - ", 1)
    else:
        category, name = "Uncategorized", title

    catalog[title] = {
        "title": title,
        "category": category,
        "name": name,
        "normalized_title": normalize(title),
        "normalized_name": normalize(name),
        "tokens": tokenize(name),
        "acronyms": extract_acronyms(title),
        "slide_number": slide_number,
        "element_path": path,
        "kind": kind,
        "bbox_emu": {
            "x": bbox[0] if bbox else 0,
            "y": bbox[1] if bbox else 0,
            "w": bbox[2] if bbox else 0,
            "h": bbox[3] if bbox else 0,
        },
        "source": source,
    }


def resolve_path(root: ET.Element, path: list[int]) -> ET.Element:
    element = root
    for index in path:
        children = list(element)
        element = children[index]
    return element


def child_groups_with_text(element: ET.Element) -> list[tuple[int, ET.Element, str]]:
    matches: list[tuple[int, ET.Element, str]] = []
    for index, child in enumerate(list(element)):
        if local_name(child) != "grpSp":
            continue
        text = clean_title(extract_text_from_shape(child))
        if text:
            matches.append((index, child, text))
    return matches


def has_graphic_only_immediate_children(element: ET.Element) -> bool:
    for child in list(element):
        tag = local_name(child)
        if tag not in {"grpSp", "sp", "pic"}:
            continue
        if clean_title(extract_text_from_shape(child)):
            continue
        if get_transform(child):
            return True
    return False


def collect_icon_groups(
    catalog: dict[str, dict[str, Any]],
    slide_root: ET.Element,
    *,
    slide_number: int,
    category: str,
    path_prefix: list[int] | None = None,
) -> None:
    path_prefix = path_prefix or []
    sp_tree = get_sp_tree(slide_root)
    container = resolve_path(sp_tree, path_prefix) if path_prefix else sp_tree

    for index, child in enumerate(list(container)):
        if local_name(child) != "grpSp":
            continue
        current_path = [*path_prefix, index]
        child_groups = child_groups_with_text(child)
        if child_groups and not has_graphic_only_immediate_children(child):
            collect_icon_groups(
                catalog,
                slide_root,
                slide_number=slide_number,
                category=category,
                path_prefix=current_path,
            )
            continue
        text = clean_title(extract_text_from_shape(child))
        if not text:
            continue
        add_entry(
            catalog,
            title=f"{category} - {text}",
            slide_number=slide_number,
            path=current_path,
            kind="grpSp",
            bbox=get_transform(child),
            source=f"oracle-oci-architecture-toolkit-v24.1.pptx:slide{slide_number}",
        )


def collect_physical_groupings(
    catalog: dict[str, dict[str, Any]],
    slides: dict[int, ET.Element],
) -> None:
    for item in PHYSICAL_GROUPINGS:
        slide_root = slides[item["slide"]]
        sp_tree = get_sp_tree(slide_root)
        element = resolve_path(sp_tree, item["path"])
        add_entry(
            catalog,
            title=item["title"],
            slide_number=item["slide"],
            path=item["path"],
            kind=local_name(element),
            bbox=get_transform(element),
            source=f"oracle-oci-architecture-toolkit-v24.1.pptx:slide{item['slide']}",
        )


def build_catalog(pptx_path: Path) -> list[dict[str, Any]]:
    slides = parse_presentation(pptx_path)
    catalog: dict[str, dict[str, Any]] = {}

    for slide_number, category in SLIDE_CATEGORY_OVERRIDES.items():
        collect_icon_groups(catalog, slides[slide_number], slide_number=slide_number, category=category)

    collect_physical_groupings(catalog, slides)

    return sorted(catalog.values(), key=lambda entry: (entry["category"], entry["name"], entry["title"]))


def write_json(path: Path, catalog: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2) + "\n")


def write_markdown(path: Path, catalog: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in catalog:
        grouped[entry["category"]].append(entry)

    lines = [
        "# OCI PowerPoint Catalog",
        "",
        "This catalog is built from the bundled Oracle PowerPoint toolkit and records reusable icon and grouping snippets by slide path.",
        "",
        f"Total entries: {len(catalog)}",
        "",
    ]

    for category in sorted(grouped):
        lines.append(f"## {category}")
        lines.append("")
        for entry in grouped[category]:
            lines.append(
                f"- {entry['title']} (`slide {entry['slide_number']}`, path `{entry['element_path']}`)"
            )
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> None:
    default_pptx, default_json, default_md = default_paths()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pptx", type=Path, default=default_pptx, help="Oracle PowerPoint toolkit path")
    parser.add_argument("--json-out", type=Path, default=default_json, help="JSON catalog output path")
    parser.add_argument("--md-out", type=Path, default=default_md, help="Markdown catalog output path")
    args = parser.parse_args()

    catalog = build_catalog(args.pptx)
    write_json(args.json_out, catalog)
    write_markdown(args.md_out, catalog)

    print(f"Wrote {len(catalog)} PowerPoint catalog entries.")
    print(f"JSON: {args.json_out}")
    print(f"Markdown: {args.md_out}")


if __name__ == "__main__":
    main()
