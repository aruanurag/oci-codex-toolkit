#!/usr/bin/env python3
"""Build a reusable PowerPoint reference-layout catalog from the Oracle OCI toolkit deck."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from build_powerpoint_catalog import default_paths as icon_default_paths
from build_powerpoint_catalog import normalize, tokenize

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"p": P_NS, "a": A_NS, "r": R_NS}

REFERENCE_SLIDE_HINTS: dict[int, dict[str, Any]] = {
    24: {
        "title": "Logical Landscape Blank Canvas",
        "page_type": "logical",
        "orientation": "landscape",
        "tags": ["blank", "canvas", "internet", "logical", "oci-region", "on-premises", "third-party"],
        "traits": ["baseline", "canvas", "logical", "location-groups"],
        "layout_notes": "Best starting point for a clean landscape logical slide with OCI Region, Internet, On-Premises, and 3rd Party Cloud boundaries.",
    },
    25: {
        "title": "Logical Portrait Blank Canvas",
        "page_type": "logical",
        "orientation": "portrait",
        "tags": ["blank", "canvas", "logical", "portrait"],
        "traits": ["baseline", "canvas", "logical", "portrait"],
        "layout_notes": "Use when the request explicitly needs portrait orientation or a tall logical flow.",
    },
    27: {
        "title": "Physical Landscape Blank Canvas",
        "page_type": "physical",
        "orientation": "landscape",
        "tags": ["availability-domain", "blank", "canvas", "fault-domain", "oci-region", "physical", "vcn"],
        "traits": ["baseline", "canvas", "network", "physical"],
        "layout_notes": "Best general physical baseline when you need a fresh OCI Region and VCN layout without inheriting extra sample complexity.",
    },
    28: {
        "title": "Physical Single-Region Network Sample",
        "page_type": "physical",
        "orientation": "landscape",
        "tags": ["availability-domain", "database", "fault-domain", "network", "sample", "single-region", "vcn"],
        "traits": ["network", "physical", "sample"],
        "layout_notes": "Useful for single-region physical diagrams that need ADs, subnets, routing, and databases but not OKE.",
    },
    29: {
        "title": "Physical Dual-AD Compute and Database Sample",
        "page_type": "physical",
        "orientation": "landscape",
        "tags": ["bastion", "compute", "database", "dual-ad", "ha", "on-premises", "sample", "subnet"],
        "traits": ["compute", "ha", "network", "physical", "sample"],
        "layout_notes": "Good baseline for HA compute/database layouts with multiple availability domains and public/private subnet separation.",
    },
    30: {
        "title": "Physical Portrait HA Sample",
        "page_type": "physical",
        "orientation": "portrait",
        "tags": ["database", "dual-ad", "ha", "portrait", "sample"],
        "traits": ["ha", "physical", "portrait", "sample"],
        "layout_notes": "Use only when the user explicitly wants portrait physical output.",
    },
    31: {
        "title": "Physical Mixed-Boundary Reference Sample",
        "page_type": "physical",
        "orientation": "landscape",
        "tags": ["annotations", "internet", "lb", "mixed-boundary", "object-storage", "on-premises", "third-party"],
        "traits": ["layout-reference", "network", "physical", "sample"],
        "layout_notes": "Helpful when the slide must show OCI together with Internet, On-Premises, or 3rd Party boundaries in one view.",
    },
    32: {
        "title": "Physical OKE Multi-Tier Reference Sample",
        "page_type": "physical",
        "orientation": "landscape",
        "tags": ["application-tier", "data-tier", "edge-tier", "kubernetes", "lb", "multi-ad", "oke", "three-tier", "vcn"],
        "traits": ["application-platform", "network", "oke", "physical", "sample"],
        "layout_notes": "Preferred starting point for OKE, multi-tier, and modern app diagrams with clear public/private subnet separation.",
    },
}

NOISE_FRAGMENTS = {
    "copyright",
    "landscape sample",
    "portrait sample",
    "landscape blank template",
    "portrait blank template",
    "tip",
}


def default_paths() -> tuple[Path, Path, Path]:
    pptx_path, _, _ = icon_default_paths()
    skill_dir = Path(__file__).resolve().parents[1]
    json_path = skill_dir / "references" / "powerpoint-reference-catalog.json"
    md_path = skill_dir / "references" / "powerpoint-reference-catalog.md"
    return pptx_path, json_path, md_path


def extract_slide_texts(slide_root: ET.Element) -> list[str]:
    values: list[str] = []
    for text_node in slide_root.findall(".//a:t", NS):
        text = " ".join(html.unescape(text_node.text or "").replace("\xa0", " ").split())
        if not text:
            continue
        normalized = normalize(text)
        if not normalized or normalized.isdigit():
            continue
        if any(fragment in normalized for fragment in NOISE_FRAGMENTS):
            continue
        values.append(text)
    return values


def load_slide_roots(pptx_path: Path) -> dict[int, ET.Element]:
    with zipfile.ZipFile(pptx_path) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        relationships = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relationships}
        slide_roots: dict[int, ET.Element] = {}
        slide_list = presentation.find("./p:sldIdLst", NS)
        if slide_list is None:
            raise ValueError("PowerPoint presentation is missing the slide list.")
        for slide_number, slide_id in enumerate(slide_list, start=1):
            if slide_number not in REFERENCE_SLIDE_HINTS:
                continue
            rel_id = slide_id.attrib[f"{{{R_NS}}}id"]
            target = "ppt/" + rel_map[rel_id].lstrip("../")
            slide_roots[slide_number] = ET.fromstring(archive.read(target))
    return slide_roots


def build_catalog(pptx_path: Path) -> list[dict[str, Any]]:
    slide_roots = load_slide_roots(pptx_path)
    entries: list[dict[str, Any]] = []

    for slide_number, hint in sorted(REFERENCE_SLIDE_HINTS.items()):
        slide_root = slide_roots[slide_number]
        texts = extract_slide_texts(slide_root)
        sample_labels = texts[:16]
        joined_text = " ".join(sample_labels)
        entries.append(
            {
                "title": hint["title"],
                "slide_number": slide_number,
                "page_type": hint["page_type"],
                "orientation": hint["orientation"],
                "tags": sorted(hint["tags"]),
                "traits": sorted(hint["traits"]),
                "layout_notes": hint["layout_notes"],
                "sample_labels": sample_labels,
                "normalized_title": normalize(hint["title"]),
                "tokens": sorted(set(tokenize(hint["title"]) + tokenize(joined_text))),
                "source": f"{pptx_path.name}:slide{slide_number}",
            }
        )

    return entries


def write_json(path: Path, catalog: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2) + "\n")


def write_markdown(path: Path, catalog: list[dict[str, Any]]) -> None:
    lines = [
        "# PowerPoint Reference Catalog",
        "",
        "These Oracle PowerPoint slides are the preferred layout baselines when the skill can reuse a close starting point instead of arranging a slide from scratch.",
        "",
        f"Total references: {len(catalog)}",
        "",
    ]

    for entry in catalog:
        lines.append(f"## Slide {entry['slide_number']} - {entry['title']}")
        lines.append("")
        lines.append(f"- Page type: `{entry['page_type']}`")
        lines.append(f"- Orientation: `{entry['orientation']}`")
        lines.append(f"- Tags: `{', '.join(entry['tags'])}`")
        lines.append(f"- Traits: `{', '.join(entry['traits'])}`")
        lines.append(f"- Layout notes: {entry['layout_notes']}")
        if entry["sample_labels"]:
            lines.append(f"- Sample labels: `{', '.join(entry['sample_labels'][:10])}`")
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

    print(f"Wrote {len(catalog)} PowerPoint reference entries.")
    print(f"JSON: {args.json_out}")
    print(f"Markdown: {args.md_out}")


if __name__ == "__main__":
    main()
