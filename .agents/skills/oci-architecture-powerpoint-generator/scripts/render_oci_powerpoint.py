#!/usr/bin/env python3
"""Render OCI architecture JSON specs into finalized PowerPoint files."""

from __future__ import annotations

import argparse
import copy
import html
import json
import math
import re
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from build_powerpoint_catalog import default_paths
from resolve_oci_powerpoint_icon import load_catalog, resolve_icon

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
A16_NS = "http://schemas.microsoft.com/office/drawing/2014/main"
ASVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
ADEC_NS = "http://schemas.microsoft.com/office/drawing/2017/decorative"

ET.register_namespace("a", A_NS)
ET.register_namespace("p", P_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("mc", MC_NS)
ET.register_namespace("p14", P14_NS)
ET.register_namespace("a14", A14_NS)
ET.register_namespace("a16", A16_NS)
ET.register_namespace("asvg", ASVG_NS)
ET.register_namespace("adec", ADEC_NS)
ET.register_namespace("", REL_NS)

NS = {"a": A_NS, "p": P_NS, "r": R_NS}

SLIDE_CX = 12_192_000
SLIDE_CY = 6_858_000
EMU_PER_PT = 12_700
DEFAULT_PAGE_WIDTH = 1_600
DEFAULT_PAGE_HEIGHT = 900
DEFAULT_ICON_BOX = 108

COLOR_BARK = "312D2A"
COLOR_NEUTRAL1 = "F5F4F2"
COLOR_NEUTRAL2 = "DFDCD8"
COLOR_NEUTRAL3 = "9E9892"
COLOR_AIR = "FCFBFA"
CONNECTOR_CLEARANCE = 22.0
EDGE_LABEL_HEIGHT = 20.0
EDGE_LABEL_VERTICAL_GAP = 4.0
TOP_LANE_LABEL_GAP = 2.0
BOUNDARY_TOLERANCE = 1.5
PAGE_MARGIN_LEFT = 40.0
PAGE_MARGIN_RIGHT = 40.0
PAGE_MARGIN_TOP = 48.0
PAGE_MARGIN_BOTTOM = 52.0
MAX_CONNECTOR_BENDS = 2
MIN_GROUPING_INSET = 8.0
SIBLING_OVERLAP_TOLERANCE = 2.0
UNRELATED_OVERLAP_TOLERANCE = 2.0
TEXT_FIT_SHRINK_THRESHOLD = 0.98
TEXT_FIT_ERROR_THRESHOLD = 0.90
TEXT_FIT_CHAR_WIDTH = 0.40
TEXT_FIT_UPPERCASE_WIDTH = 0.50
TEXT_FIT_DIGIT_WIDTH = 0.46
TEXT_FIT_WIDE_WIDTH = 0.66
TEXT_FIT_NARROW_WIDTH = 0.16
TEXT_FIT_SPACE_WIDTH = 0.24
REQUIRED_CLARIFICATION_TOPICS = (
    "availability",
    "database",
    "subnet_scope",
    "icon_resolution",
)
ALLOWED_CLARIFICATION_GATE_STATUSES = {"satisfied", "waived"}
ALLOWED_DECISION_RESOLUTION_SOURCES = {
    "user_answer",
    "thread_context",
    "recommendation_accepted",
    "assumed",
    "not_applicable",
}
BLANK_SLIDE_LAYOUT_NAME = "slideLayout16.xml"
BLANK_SLIDE_LAYOUT_PATH = f"ppt/slideLayouts/{BLANK_SLIDE_LAYOUT_NAME}"

STYLE_KV_RE = re.compile(r"([A-Za-z][A-Za-z0-9]*)=([^;]+)")
TAG_RE = re.compile(r"<[^>]+>")


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def qn(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def parse_style(style: str | None) -> dict[str, str]:
    if not style:
        return {}
    return {key: value for key, value in STYLE_KV_RE.findall(style)}


def drawio_html_to_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = TAG_RE.sub("", text)
    return "\n".join(part.strip() for part in text.splitlines()).strip()


def strip_non_placeholder_tags(value: str | None) -> str:
    return drawio_html_to_text(value)


def require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def validate_clarification_gate(spec: dict[str, Any]) -> None:
    gate = spec.get("clarification_gate")
    if not isinstance(gate, dict):
        raise ValueError("Spec must include a top-level clarification_gate object before rendering.")

    status = require_non_empty_string(gate.get("status"), "clarification_gate.status").lower()
    if status not in ALLOWED_CLARIFICATION_GATE_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_CLARIFICATION_GATE_STATUSES))
        raise ValueError(f"clarification_gate.status must be one of: {allowed}.")

    require_non_empty_string(gate.get("notes"), "clarification_gate.notes")

    if status == "waived":
        require_non_empty_string(gate.get("waiver_reason"), "clarification_gate.waiver_reason")
        return

    decisions = gate.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise ValueError("clarification_gate.decisions must be a non-empty list when status is 'satisfied'.")

    seen_topics: set[str] = set()
    for index, decision in enumerate(decisions, start=1):
        if not isinstance(decision, dict):
            raise ValueError(f"clarification_gate.decisions[{index}] must be an object.")

        prefix = f"clarification_gate.decisions[{index}]"
        topic = require_non_empty_string(decision.get("topic"), f"{prefix}.topic").lower()
        if topic in seen_topics:
            raise ValueError(f"{prefix}.topic duplicates '{topic}'. Each clarification topic must appear only once.")
        seen_topics.add(topic)

        require_non_empty_string(decision.get("question"), f"{prefix}.question")
        require_non_empty_string(decision.get("recommended_option"), f"{prefix}.recommended_option")
        require_non_empty_string(decision.get("selected_option"), f"{prefix}.selected_option")
        resolution_source = require_non_empty_string(decision.get("resolution_source"), f"{prefix}.resolution_source").lower()
        if resolution_source not in ALLOWED_DECISION_RESOLUTION_SOURCES:
            allowed = ", ".join(sorted(ALLOWED_DECISION_RESOLUTION_SOURCES))
            raise ValueError(f"{prefix}.resolution_source must be one of: {allowed}.")
        require_non_empty_string(decision.get("rationale"), f"{prefix}.rationale")

    missing_topics = [topic for topic in REQUIRED_CLARIFICATION_TOPICS if topic not in seen_topics]
    if missing_topics:
        joined = ", ".join(missing_topics)
        raise ValueError(
            "clarification_gate.decisions is missing required topics: "
            f"{joined}. Record the selected and recommended options before rendering."
        )


def build_empty_tx_body(
    shape: ET.Element,
    *,
    anchor: str = "ctr",
    wrap: str | None = None,
    zero_margins: bool = False,
    auto_fit: bool = False,
) -> ET.Element:
    tx_body = shape.find("./p:txBody", NS)
    if tx_body is None:
        tx_body = ET.SubElement(shape, qn(P_NS, "txBody"))
    tx_body.clear()
    body_pr_attrib = {"rtlCol": "0", "anchor": anchor}
    if wrap is not None:
        body_pr_attrib["wrap"] = wrap
    if zero_margins:
        body_pr_attrib.update({"lIns": "0", "rIns": "0", "tIns": "0", "bIns": "0"})
    body_pr = ET.SubElement(tx_body, qn(A_NS, "bodyPr"), body_pr_attrib)
    if auto_fit:
        # PowerPoint cards and labels in this renderer use fixed geometry. Use
        # normal auto-fit so the text shrinks to stay inside the box instead of
        # requesting shape growth, which can still render as visible overflow.
        ET.SubElement(body_pr, qn(A_NS, "normAutofit"))
    ET.SubElement(tx_body, qn(A_NS, "lstStyle"))
    return tx_body


def ensure_tx_body(shape: ET.Element) -> ET.Element:
    """Ensure placeholder shapes still carry a valid empty text body."""
    tx_body = build_empty_tx_body(shape)
    ET.SubElement(tx_body, qn(A_NS, "p"))
    return tx_body


def normalize_text_bodies(root: ET.Element) -> None:
    """PowerPoint expects each text body to include at least one paragraph node."""
    for tx_body in root.findall(".//p:txBody", NS):
        if tx_body.find("./a:p", NS) is None:
            ET.SubElement(tx_body, qn(A_NS, "p"))


def clone_text_template(shape: ET.Element) -> tuple[ET.Element | None, ET.Element | None, ET.Element | None, ET.Element | None]:
    tx_body = shape.find("./p:txBody", NS)
    if tx_body is None:
        return None, None, None, None

    body_pr = tx_body.find("./a:bodyPr", NS)
    lst_style = tx_body.find("./a:lstStyle", NS)
    paragraph = tx_body.find("./a:p", NS)
    paragraph_pr = paragraph.find("./a:pPr", NS) if paragraph is not None else None
    run_pr = paragraph.find(".//a:rPr", NS) if paragraph is not None else None
    if run_pr is None and paragraph is not None:
        run_pr = paragraph.find("./a:endParaRPr", NS)

    return (
        copy.deepcopy(body_pr) if body_pr is not None else None,
        copy.deepcopy(lst_style) if lst_style is not None else None,
        copy.deepcopy(paragraph_pr) if paragraph_pr is not None else None,
        copy.deepcopy(run_pr) if run_pr is not None else None,
    )


def build_text_paragraph(
    parent: ET.Element,
    text: str,
    *,
    font_size_pt: int,
    bold: bool,
    align: str = "ctr",
    paragraph_template: ET.Element | None = None,
    run_template: ET.Element | None = None,
) -> None:
    paragraph = ET.SubElement(parent, qn(A_NS, "p"))
    if paragraph_template is not None:
        paragraph.append(copy.deepcopy(paragraph_template))
    else:
        ET.SubElement(paragraph, qn(A_NS, "pPr"), {"algn": align})
    run = ET.SubElement(paragraph, qn(A_NS, "r"))
    if run_template is not None:
        rpr = copy.deepcopy(run_template)
        rpr.tag = qn(A_NS, "rPr")
        rpr.attrib["sz"] = str(font_size_pt * 100)
        if bold:
            rpr.attrib["b"] = "1"
        run.append(rpr)
    else:
        rpr_attrs = {"lang": "en-US", "sz": str(font_size_pt * 100)}
        if bold:
            rpr_attrs["b"] = "1"
        rpr = ET.SubElement(run, qn(A_NS, "rPr"), rpr_attrs)
        solid_fill = ET.SubElement(rpr, qn(A_NS, "solidFill"))
        ET.SubElement(solid_fill, qn(A_NS, "srgbClr"), {"val": COLOR_BARK})
        ET.SubElement(rpr, qn(A_NS, "latin"), {"typeface": "Arial"})
    text_node = ET.SubElement(run, qn(A_NS, "t"))
    text_node.text = text
    if run_template is not None:
        end_rpr = copy.deepcopy(run_template)
        end_rpr.tag = qn(A_NS, "endParaRPr")
        end_rpr.attrib["sz"] = str(font_size_pt * 100)
        paragraph.append(end_rpr)
    else:
        end_rpr = ET.SubElement(paragraph, qn(A_NS, "endParaRPr"), {"lang": "en-US", "sz": str(font_size_pt * 100)})
        solid_fill = ET.SubElement(end_rpr, qn(A_NS, "solidFill"))
        ET.SubElement(solid_fill, qn(A_NS, "srgbClr"), {"val": COLOR_BARK})
        ET.SubElement(end_rpr, qn(A_NS, "latin"), {"typeface": "Arial"})


def set_text(
    shape: ET.Element,
    text: str,
    *,
    font_size_pt: int = 10,
    bold: bool = False,
    align: str = "ctr",
    preserve: bool = False,
    anchor: str = "ctr",
    wrap: str | None = None,
    zero_margins: bool = False,
    auto_fit: bool = False,
) -> None:
    body_pr_template = None
    lst_style_template = None
    paragraph_template = None
    run_template = None
    if preserve:
        body_pr_template, lst_style_template, paragraph_template, run_template = clone_text_template(shape)

    tx_body = build_empty_tx_body(
        shape,
        anchor=anchor,
        wrap=wrap,
        zero_margins=zero_margins,
        auto_fit=auto_fit,
    )
    if body_pr_template is not None:
        tx_body[0] = body_pr_template
    if lst_style_template is not None:
        if len(tx_body) >= 2:
            tx_body[1] = lst_style_template
        else:
            tx_body.append(lst_style_template)
    for line in text.split("\n") or [""]:
        build_text_paragraph(
            tx_body,
            line or " ",
            font_size_pt=font_size_pt,
            bold=bold,
            align=align,
            paragraph_template=paragraph_template,
            run_template=run_template,
        )


def find_text_shapes(element: ET.Element) -> list[ET.Element]:
    shapes = []
    if local_name(element) == "sp":
        values = [(node.text or "").strip() for node in element.findall(".//a:t", NS)]
        if any(values):
            shapes.append(element)
    for shape in element.findall(".//p:sp", NS):
        values = [(node.text or "").strip() for node in shape.findall(".//a:t", NS)]
        if any(values):
            if shape is element:
                continue
            shapes.append(shape)
    return shapes


def get_shape_offset(shape: ET.Element) -> tuple[int, int]:
    xfrm = shape.find("./p:spPr/a:xfrm", NS)
    if xfrm is None:
        return (0, 0)
    off = xfrm.find("./a:off", NS)
    if off is None:
        return (0, 0)
    return (int(off.attrib.get("x", "0")), int(off.attrib.get("y", "0")))


def override_element_text(element: ET.Element, text: str | None = None, *, hide: bool = False) -> None:
    target_shapes = find_text_shapes(element)
    if not target_shapes:
        return
    target_shapes.sort(key=lambda shape: get_shape_offset(shape)[1])
    if hide:
        for shape in target_shapes:
            set_text(shape, " ", font_size_pt=9, bold=False, preserve=True)
        return
    if text is None:
        return
    chosen = target_shapes[-1]
    set_text(chosen, text, font_size_pt=9, bold=True, preserve=True)
    for extra in target_shapes[:-1]:
        set_text(extra, " ", font_size_pt=9, bold=False, preserve=True)


def set_element_frame(element: ET.Element, x: int, y: int, w: int, h: int) -> None:
    if local_name(element) == "grpSp":
        xfrm = element.find("./p:grpSpPr/a:xfrm", NS)
    else:
        xfrm = element.find("./p:spPr/a:xfrm", NS)
    if xfrm is None:
        return
    off = xfrm.find("./a:off", NS)
    ext = xfrm.find("./a:ext", NS)
    if off is None or ext is None:
        return
    off.attrib["x"] = str(int(x))
    off.attrib["y"] = str(int(y))
    ext.attrib["cx"] = str(int(max(w, 1)))
    ext.attrib["cy"] = str(int(max(h, 1)))


def element_frame(element: ET.Element) -> tuple[int, int, int, int] | None:
    if local_name(element) == "grpSp":
        xfrm = element.find("./p:grpSpPr/a:xfrm", NS)
    else:
        xfrm = element.find("./p:spPr/a:xfrm", NS)
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


def has_non_empty_text(element: ET.Element) -> bool:
    return any((node.text or "").strip() for node in element.findall(".//a:t", NS))


def group_visual_children(group: ET.Element) -> list[ET.Element]:
    return [
        child
        for child in list(group)
        if local_name(child) not in {"nvGrpSpPr", "grpSpPr"}
    ]


def union_element_frames(elements: list[ET.Element]) -> tuple[int, int, int, int] | None:
    frames = [frame for frame in (element_frame(element) for element in elements) if frame is not None]
    if not frames:
        return None
    min_x = min(frame[0] for frame in frames)
    min_y = min(frame[1] for frame in frames)
    max_x = max(frame[0] + frame[2] for frame in frames)
    max_y = max(frame[1] + frame[3] for frame in frames)
    return (min_x, min_y, max(max_x - min_x, 1), max(max_y - min_y, 1))


def crop_group_to_visual_children(group: ET.Element) -> bool:
    if local_name(group) != "grpSp":
        return False

    drawable_children = group_visual_children(group)
    text_children = [child for child in drawable_children if has_non_empty_text(child)]
    visual_children = [child for child in drawable_children if child not in text_children]
    if not text_children or not visual_children:
        return False

    for child in text_children:
        group.remove(child)

    bbox = union_element_frames(visual_children)
    if bbox is None:
        return False

    xfrm = group.find("./p:grpSpPr/a:xfrm", NS)
    if xfrm is None:
        return False
    off = xfrm.find("./a:off", NS)
    ext = xfrm.find("./a:ext", NS)
    ch_off = xfrm.find("./a:chOff", NS)
    ch_ext = xfrm.find("./a:chExt", NS)
    if off is None or ext is None or ch_off is None or ch_ext is None:
        return False

    x, y, w, h = bbox
    off.attrib["x"] = str(x)
    off.attrib["y"] = str(y)
    ext.attrib["cx"] = str(w)
    ext.attrib["cy"] = str(h)
    ch_off.attrib["x"] = str(x)
    ch_off.attrib["y"] = str(y)
    ch_ext.attrib["cx"] = str(w)
    ch_ext.attrib["cy"] = str(h)
    return True


def shift_element_coordinates(element: ET.Element, delta_x: int, delta_y: int) -> None:
    if local_name(element) == "grpSp":
        xfrm = element.find("./p:grpSpPr/a:xfrm", NS)
    else:
        xfrm = element.find("./p:spPr/a:xfrm", NS)
    if xfrm is None:
        return

    off = xfrm.find("./a:off", NS)
    if off is not None:
        off.attrib["x"] = str(int(off.attrib.get("x", "0")) + delta_x)
        off.attrib["y"] = str(int(off.attrib.get("y", "0")) + delta_y)

    ch_off = xfrm.find("./a:chOff", NS)
    if ch_off is not None:
        ch_off.attrib["x"] = str(int(ch_off.attrib.get("x", "0")) + delta_x)
        ch_off.attrib["y"] = str(int(ch_off.attrib.get("y", "0")) + delta_y)


def normalize_group_coordinate_space(group: ET.Element) -> bool:
    if local_name(group) != "grpSp":
        return False

    xfrm = group.find("./p:grpSpPr/a:xfrm", NS)
    if xfrm is None:
        return False
    ch_off = xfrm.find("./a:chOff", NS)
    ch_ext = xfrm.find("./a:chExt", NS)
    if ch_off is None or ch_ext is None:
        return False

    shift_x = -int(ch_off.attrib.get("x", "0"))
    shift_y = -int(ch_off.attrib.get("y", "0"))

    normalized = False
    if shift_x != 0 or shift_y != 0:
        for child in group_visual_children(group):
            shift_element_coordinates(child, shift_x, shift_y)
            for descendant in child.iter():
                if descendant is child:
                    continue
                shift_element_coordinates(descendant, shift_x, shift_y)
        ch_off.attrib["x"] = "0"
        ch_off.attrib["y"] = "0"
        normalized = True

    for child in group_visual_children(group):
        if local_name(child) == "grpSp":
            normalized = normalize_group_coordinate_space(child) or normalized

    return normalized


def slide_sp_tree(slide_root: ET.Element) -> ET.Element:
    sp_tree = slide_root.find(f".//{{{P_NS}}}spTree")
    if sp_tree is None:
        raise ValueError("Slide is missing spTree")
    return sp_tree


def resolve_catalog_path(sp_tree: ET.Element, path: list[int]) -> ET.Element:
    element = sp_tree
    for index in path:
        element = list(element)[index]
    return element


class AssetLibrary:
    def __init__(self, pptx_path: Path, catalog: list[dict[str, Any]]) -> None:
        self.pptx_path = pptx_path
        self.catalog = catalog
        self.catalog_by_title = {entry["title"]: entry for entry in catalog}
        self.slide_roots: dict[int, ET.Element] = {}
        self.slide_relationships: dict[int, dict[str, ET.Element]] = {}
        with zipfile.ZipFile(pptx_path) as archive:
            for slide_number in {entry["slide_number"] for entry in catalog}:
                self.slide_roots[slide_number] = ET.fromstring(
                    archive.read(f"ppt/slides/slide{slide_number}.xml")
                )
                rel_name = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
                slide_rels: dict[str, ET.Element] = {}
                if rel_name in archive.namelist():
                    rel_root = ET.fromstring(archive.read(rel_name))
                    for rel in rel_root:
                        rel_id = rel.attrib.get("Id")
                        if rel_id:
                            slide_rels[rel_id] = rel
                self.slide_relationships[slide_number] = slide_rels

    def clone(self, title: str) -> ET.Element:
        return self.clone_with_relationships(title)[0]

    def clone_with_relationships(self, title: str) -> tuple[ET.Element, dict[str, ET.Element]]:
        entry = self.catalog_by_title[title]
        sp_tree = slide_sp_tree(self.slide_roots[entry["slide_number"]])
        original = resolve_catalog_path(sp_tree, entry["element_path"])
        return copy.deepcopy(original), self.slide_relationships.get(entry["slide_number"], {})


class IdAllocator:
    def __init__(self) -> None:
        self.next_id = 1_500

    def assign(self, element: ET.Element) -> None:
        for node in element.iter():
            tag = local_name(node)
            if tag == "cNvPr":
                node.attrib["id"] = str(self.next_id)
                if "name" in node.attrib and not node.attrib["name"]:
                    node.attrib["name"] = f"Generated {self.next_id}"
                self.next_id += 1


def to_emu(value: float, scale: float) -> int:
    return int(round(value * scale))


def bbox_anchor_point(bbox: dict[str, float], anchor: str | None) -> tuple[float, float]:
    x = bbox["x"]
    y = bbox["y"]
    w = bbox["w"]
    h = bbox["h"]
    if anchor == "left":
        return (x, y + (h / 2))
    if anchor == "right":
        return (x + w, y + (h / 2))
    if anchor == "top":
        return (x + (w / 2), y)
    if anchor == "bottom":
        return (x + (w / 2), y + h)
    return (x + (w / 2), y + (h / 2))


def overlap_axis_range(
    start_a: float,
    end_a: float,
    start_b: float,
    end_b: float,
    *,
    tolerance: float = 0.1,
) -> tuple[float, float] | None:
    low = max(start_a, start_b)
    high = min(end_a, end_b)
    if low <= high + tolerance:
        return (low, high)
    return None


def clamp_to_range(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def aligned_connector_endpoints(
    source_bbox: dict[str, float],
    target_bbox: dict[str, float],
    source_anchor: str | None,
    target_anchor: str | None,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    if source_anchor in {"left", "right"} and target_anchor in {"left", "right"}:
        overlap = overlap_axis_range(
            source_bbox["y"],
            source_bbox["y"] + source_bbox["h"],
            target_bbox["y"],
            target_bbox["y"] + target_bbox["h"],
        )
        if overlap:
            source_center_y = source_bbox["y"] + (source_bbox["h"] / 2)
            target_center_y = target_bbox["y"] + (target_bbox["h"] / 2)
            shared_y = clamp_to_range((source_center_y + target_center_y) / 2, overlap[0], overlap[1])
            source_x = source_bbox["x"] if source_anchor == "left" else source_bbox["x"] + source_bbox["w"]
            target_x = target_bbox["x"] if target_anchor == "left" else target_bbox["x"] + target_bbox["w"]
            return ((source_x, shared_y), (target_x, shared_y))

    if source_anchor in {"top", "bottom"} and target_anchor in {"top", "bottom"}:
        overlap = overlap_axis_range(
            source_bbox["x"],
            source_bbox["x"] + source_bbox["w"],
            target_bbox["x"],
            target_bbox["x"] + target_bbox["w"],
        )
        if overlap:
            source_center_x = source_bbox["x"] + (source_bbox["w"] / 2)
            target_center_x = target_bbox["x"] + (target_bbox["w"] / 2)
            shared_x = clamp_to_range((source_center_x + target_center_x) / 2, overlap[0], overlap[1])
            source_y = source_bbox["y"] if source_anchor == "top" else source_bbox["y"] + source_bbox["h"]
            target_y = target_bbox["y"] if target_anchor == "top" else target_bbox["y"] + target_bbox["h"]
            return ((shared_x, source_y), (shared_x, target_y))

    return None


def resolve_connector_endpoints(
    source_bbox: dict[str, float],
    target_bbox: dict[str, float],
    source_anchor: str | None,
    target_anchor: str | None,
) -> tuple[tuple[float, float], tuple[float, float], bool]:
    aligned = aligned_connector_endpoints(source_bbox, target_bbox, source_anchor, target_anchor)
    if aligned is not None:
        return aligned[0], aligned[1], True
    return (
        bbox_anchor_point(source_bbox, source_anchor),
        bbox_anchor_point(target_bbox, target_anchor),
        False,
    )


def aligned_offset(span: float, size: float, align: str | None) -> float:
    if align == "start":
        return 0.0
    if align == "end":
        return max(span - size, 0.0)
    return max((span - size) / 2, 0.0)


def place_on_boundary(
    boundary_bbox: dict[str, float],
    *,
    side: str,
    width: float,
    height: float,
    axis_offset: float | None = None,
    align: str | None = "center",
    align_to_bbox: dict[str, float] | None = None,
) -> tuple[float, float]:
    if side not in {"left", "right", "top", "bottom"}:
        raise ValueError(f"Unsupported boundary side '{side}'.")

    if side in {"left", "right"}:
        if axis_offset is not None:
            y = boundary_bbox["y"] + axis_offset
        elif align_to_bbox is not None:
            y = (align_to_bbox["y"] + (align_to_bbox["h"] / 2)) - (height / 2)
        else:
            y = boundary_bbox["y"] + aligned_offset(boundary_bbox["h"], height, align)
        x = boundary_bbox["x"] - (width / 2) if side == "left" else boundary_bbox["x"] + boundary_bbox["w"] - (width / 2)
        return (x, y)

    if axis_offset is not None:
        x = boundary_bbox["x"] + axis_offset
    elif align_to_bbox is not None:
        x = (align_to_bbox["x"] + (align_to_bbox["w"] / 2)) - (width / 2)
    else:
        x = boundary_bbox["x"] + aligned_offset(boundary_bbox["w"], width, align)
    y = boundary_bbox["y"] - (height / 2) if side == "top" else boundary_bbox["y"] + boundary_bbox["h"] - (height / 2)
    return (x, y)


def point_offset_from_anchor(
    point: tuple[float, float],
    anchor: str | None,
    distance: float,
) -> tuple[float, float]:
    x, y = point
    if anchor == "left":
        return (x - distance, y)
    if anchor == "right":
        return (x + distance, y)
    if anchor == "top":
        return (x, y - distance)
    if anchor == "bottom":
        return (x, y + distance)
    return point


def manhattan_points(
    start: tuple[float, float],
    end: tuple[float, float],
    source_anchor: str | None,
    target_anchor: str | None,
) -> list[tuple[float, float]]:
    sx, sy = start
    tx, ty = end
    if math.isclose(sx, tx) or math.isclose(sy, ty):
        return [start, end]
    if source_anchor in {"left", "right"} or target_anchor in {"left", "right"}:
        mid_x = (sx + tx) / 2
        return [start, (mid_x, sy), (mid_x, ty), end]
    mid_y = (sy + ty) / 2
    return [start, (sx, mid_y), (tx, mid_y), end]


def orthogonalize_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not points:
        return []
    orthogonal = [points[0]]
    for current in points[1:]:
        previous = orthogonal[-1]
        if math.isclose(previous[0], current[0]) or math.isclose(previous[1], current[1]):
            orthogonal.append(current)
            continue
        elbow = (current[0], previous[1])
        if not (math.isclose(elbow[0], previous[0]) and math.isclose(elbow[1], previous[1])):
            orthogonal.append(elbow)
        orthogonal.append(current)
    return orthogonal


def same_point(a: tuple[float, float], b: tuple[float, float], tolerance: float = 0.1) -> bool:
    return math.isclose(a[0], b[0], abs_tol=tolerance) and math.isclose(a[1], b[1], abs_tol=tolerance)


def simplify_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    cleaned: list[tuple[float, float]] = []
    for point in points:
        if cleaned and same_point(cleaned[-1], point):
            continue
        cleaned.append(point)

    index = 1
    while index < len(cleaned) - 1:
        previous = cleaned[index - 1]
        current = cleaned[index]
        following = cleaned[index + 1]
        if (
            math.isclose(previous[0], current[0], abs_tol=0.1)
            and math.isclose(current[0], following[0], abs_tol=0.1)
        ) or (
            math.isclose(previous[1], current[1], abs_tol=0.1)
            and math.isclose(current[1], following[1], abs_tol=0.1)
        ):
            cleaned.pop(index)
            continue
        index += 1

    return cleaned


def build_connector_points(
    start: tuple[float, float],
    end: tuple[float, float],
    source_anchor: str | None,
    target_anchor: str | None,
    waypoints: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    source_exit = point_offset_from_anchor(start, source_anchor, CONNECTOR_CLEARANCE) if source_anchor else start
    target_entry = point_offset_from_anchor(end, target_anchor, CONNECTOR_CLEARANCE) if target_anchor else end

    points = [start]
    if source_anchor:
        points.append(source_exit)

    if waypoints:
        points.extend(waypoints)
    else:
        auto_points = manhattan_points(source_exit, target_entry, source_anchor, target_anchor)
        points.extend(auto_points[1:-1])

    if target_anchor:
        points.append(target_entry)
    points.append(end)
    return simplify_points(orthogonalize_points(points))


def count_connector_bends(points: list[tuple[float, float]]) -> int:
    return max(len(points) - 2, 0)


def clamp_within_page_margins(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    page_width: float,
    page_height: float,
) -> tuple[float, float]:
    min_x = PAGE_MARGIN_LEFT
    min_y = PAGE_MARGIN_TOP
    max_x = page_width - PAGE_MARGIN_RIGHT - width
    max_y = page_height - PAGE_MARGIN_BOTTOM - height

    if max_x >= min_x:
        x = min(max(x, min_x), max_x)
    else:
        x = max(max_x, 0.0)

    if max_y >= min_y:
        y = min(max(y, min_y), max_y)
    else:
        y = max(max_y, 0.0)

    return x, y


def should_apply_page_margins(
    item: dict[str, Any],
    resolution: dict[str, Any] | None,
    width: float,
    height: float,
) -> bool:
    if item.get("parent") or item.get("boundary_parent"):
        return False
    if item.get("type") == "text":
        return False
    if resolution and str(resolution.get("icon_title", "")).startswith("Physical - "):
        return True
    if resolution and str(resolution.get("category", "")) == "Physical":
        return True
    return width >= 140.0 or height >= 100.0


def estimate_label_width(text: str, icon_width: float) -> float:
    lines = text.splitlines() or [text]
    longest = max((len(line.strip()) for line in lines), default=0)
    return max(72.0, min(max(icon_width * 1.35, 0.0), max(96.0, (longest * 7.0) + 18.0)))


def estimate_label_height(text: str, font_size_pt: int) -> float:
    line_count = max(len(text.splitlines()), 1)
    return max(20.0, (line_count * (font_size_pt + 3)) + 6.0)


def text_units_per_point(page_width: float) -> float:
    return page_width / 960.0


def text_width_weight(ch: str) -> float:
    if ch in " \t":
        return TEXT_FIT_SPACE_WIDTH
    if ch in "ilI.,;:!|/'`":
        return TEXT_FIT_NARROW_WIDTH
    if ch in "mwMW@#%&QO":
        return TEXT_FIT_WIDE_WIDTH
    if ch.isupper():
        return TEXT_FIT_UPPERCASE_WIDTH
    if ch.isdigit():
        return TEXT_FIT_DIGIT_WIDTH
    return TEXT_FIT_CHAR_WIDTH


def estimate_text_width(text: str, font_size_pt: float, *, page_width: float) -> float:
    font_units = font_size_pt * text_units_per_point(page_width)
    return sum(text_width_weight(ch) for ch in text) * font_units


def wrap_text_line(text: str, available_width: float, font_size_pt: float, *, page_width: float) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return [" "]

    words = stripped.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if current and estimate_text_width(trial, font_size_pt, page_width=page_width) > available_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current or not lines:
        lines.append(current or " ")
    return lines


def estimate_text_fit(
    item: dict[str, Any],
    *,
    page_width: float,
) -> dict[str, Any] | None:
    text = str(item.get("text_content", "") or "").strip()
    if not text:
        return None

    font_size_pt = float(item.get("font_size_pt", 11))
    bold = bool(item.get("bold"))
    zero_margins = bool(item.get("zero_margins"))
    wrap_enabled = bool(item.get("wrap_enabled", True))
    bbox = item["bbox"]

    font_units = font_size_pt * text_units_per_point(page_width)
    pad_x = 0.0 if zero_margins else max(3.0, font_units * 0.18)
    pad_y = 0.0 if zero_margins else max(2.0, font_units * 0.10)
    available_width = max(1.0, bbox["w"] - (pad_x * 2))
    available_height = max(1.0, bbox["h"] - (pad_y * 2))

    rendered_lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        rendered_lines.extend(
            wrap_text_line(paragraph, available_width, font_size_pt, page_width=page_width)
            if wrap_enabled
            else [paragraph or " "]
        )

    if not rendered_lines:
        rendered_lines = [" "]

    width_needed = max(estimate_text_width(line, font_size_pt, page_width=page_width) for line in rendered_lines)
    if len(rendered_lines) == 1:
        height_needed = font_units * (0.62 if not bold else 0.66)
    else:
        height_needed = len(rendered_lines) * font_units * (0.72 if not bold else 0.76)

    width_scale = available_width / max(width_needed, 1.0)
    height_scale = available_height / max(height_needed, 1.0)
    return {
        "rendered_lines": rendered_lines,
        "required_scale": min(width_scale, height_scale),
        "available_width": available_width,
        "available_height": available_height,
        "width_needed": width_needed,
        "height_needed": height_needed,
    }


def shrink_font_size_to_fit(
    text: str,
    *,
    font_size_pt: int,
    bold: bool,
    bbox: dict[str, float],
    wrap_enabled: bool,
    zero_margins: bool,
    auto_fit: bool,
    page_width: float,
    min_font_size_pt: int = 8,
) -> int:
    if not text.strip():
        return font_size_pt
    if not auto_fit:
        return font_size_pt

    adjusted = max(int(font_size_pt), min_font_size_pt)
    probe = {
        "text_content": text,
        "font_size_pt": adjusted,
        "bold": bold,
        "bbox": bbox,
        "wrap_enabled": wrap_enabled,
        "zero_margins": zero_margins,
    }
    fit = estimate_text_fit(probe, page_width=page_width)
    while adjusted > min_font_size_pt and fit and fit["required_scale"] < TEXT_FIT_SHRINK_THRESHOLD:
        adjusted -= 1
        probe["font_size_pt"] = adjusted
        fit = estimate_text_fit(probe, page_width=page_width)
    return adjusted


def clamp_within_bounds(
    x: float,
    y: float,
    width: float,
    height: float,
    bounds: dict[str, float],
    *,
    padding: float = 0.0,
) -> tuple[float, float]:
    min_x = bounds["x"] + padding
    min_y = bounds["y"] + padding
    max_x = bounds["x"] + bounds["w"] - padding - width
    max_y = bounds["y"] + bounds["h"] - padding - height

    if max_x >= min_x:
        x = min(max(x, min_x), max_x)
    if max_y >= min_y:
        y = min(max(y, min_y), max_y)
    return x, y


def overflow_distance(frame: dict[str, float], bounds: dict[str, float]) -> float:
    left = max(bounds["x"] - frame["x"], 0.0)
    top = max(bounds["y"] - frame["y"], 0.0)
    right = max((frame["x"] + frame["w"]) - (bounds["x"] + bounds["w"]), 0.0)
    bottom = max((frame["y"] + frame["h"]) - (bounds["y"] + bounds["h"]), 0.0)
    return left + top + right + bottom


def external_label_frame_for_side(
    icon_bbox: dict[str, float],
    *,
    side: str,
    width: float,
    height: float,
    offset: float,
) -> dict[str, float]:
    if side == "top":
        return {
            "x": icon_bbox["x"] + ((icon_bbox["w"] - width) / 2),
            "y": icon_bbox["y"] - offset - height,
            "w": width,
            "h": height,
        }
    if side == "left":
        return {
            "x": icon_bbox["x"] - offset - width,
            "y": icon_bbox["y"] + ((icon_bbox["h"] - height) / 2),
            "w": width,
            "h": height,
        }
    if side == "right":
        return {
            "x": icon_bbox["x"] + icon_bbox["w"] + offset,
            "y": icon_bbox["y"] + ((icon_bbox["h"] - height) / 2),
            "w": width,
            "h": height,
        }
    return {
        "x": icon_bbox["x"] + ((icon_bbox["w"] - width) / 2),
        "y": icon_bbox["y"] + icon_bbox["h"] + offset,
        "w": width,
        "h": height,
    }


def choose_external_label_frame(
    item: dict[str, Any],
    icon_bbox: dict[str, float],
    *,
    text: str,
    parent_bbox: dict[str, float] | None,
    page_width: float,
    page_height: float,
    avoid_segments: list[tuple[tuple[float, float], tuple[float, float]]] | None = None,
) -> dict[str, float]:
    font_size = int(item.get("external_label_font_size", 10))
    width = float(item.get("external_label_width", estimate_label_width(text, icon_bbox["w"])))
    height = float(item.get("external_label_height", estimate_label_height(text, font_size)))
    offset = float(item.get("external_label_offset", 6))
    preferred_side = str(item.get("external_label_side", "")).strip().lower()

    side_order = ["bottom", "top", "right", "left"]
    boundary_side = str(item.get("boundary_side", "")).strip().lower()
    if boundary_side == "right":
        side_order = ["bottom", "top", "left", "right"]
    elif boundary_side == "left":
        side_order = ["bottom", "top", "right", "left"]
    if preferred_side:
        side_order = [preferred_side] + [side for side in side_order if side != preferred_side]

    page_bounds = {"x": 0.0, "y": 0.0, "w": page_width, "h": page_height}
    best_frame = external_label_frame_for_side(icon_bbox, side=side_order[0], width=width, height=height, offset=offset)
    best_score = float("-inf")

    for side in side_order:
        frame = external_label_frame_for_side(icon_bbox, side=side, width=width, height=height, offset=offset)
        page_overflow = overflow_distance(frame, page_bounds)
        parent_overflow = overflow_distance(frame, parent_bbox) if parent_bbox is not None else 0.0
        icon_overlap = bboxes_overlap(frame, icon_bbox, tolerance=0.5)
        connector_overlap = bool(avoid_segments) and frame_overlaps_segments(frame, avoid_segments)
        score = 0.0
        if page_overflow == 0.0:
            score += 2.0
        if parent_bbox is None or parent_overflow == 0.0:
            score += 3.0
        if side == preferred_side and preferred_side:
            score += 0.35
        if icon_overlap:
            score -= 6.0
        if connector_overlap:
            score -= 7.0
        score -= (page_overflow + parent_overflow) / 100.0
        if score > best_score:
            best_score = score
            best_frame = frame

    x, y = clamp_within_page_margins(
        best_frame["x"],
        best_frame["y"],
        best_frame["w"],
        best_frame["h"],
        page_width=page_width,
        page_height=page_height,
    )
    if parent_bbox is not None:
        x, y = clamp_within_bounds(x, y, best_frame["w"], best_frame["h"], parent_bbox, padding=2.0)
    return {"x": x, "y": y, "w": best_frame["w"], "h": best_frame["h"]}


def frame_overlaps_segments(
    frame: dict[str, float],
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    *,
    padding: float = 2.0,
) -> bool:
    padded_frame = {
        "x": frame["x"] - padding,
        "y": frame["y"] - padding,
        "w": frame["w"] + (padding * 2),
        "h": frame["h"] + (padding * 2),
    }
    for start, end in segments:
        if segment_intersects_bbox(start, end, padded_frame):
            return True
    return False


def polyline_bbox(points_emu: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    xs = [point[0] for point in points_emu]
    ys = [point[1] for point in points_emu]
    x = min(xs)
    y = min(ys)
    w = max(max(xs) - x, 1)
    h = max(max(ys) - y, 1)
    return x, y, w, h


def create_polyline_shape(
    allocator: IdAllocator,
    points_emu: list[tuple[int, int]],
    *,
    color: str = COLOR_BARK,
    width_pt: float = 1.0,
    end_arrow: bool = True,
    dashed: bool = False,
) -> ET.Element:
    x, y, w, h = polyline_bbox(points_emu)
    rel_points = [(px - x, py - y) for px, py in points_emu]

    shape = ET.Element(qn(P_NS, "sp"))
    nv_sp_pr = ET.SubElement(shape, qn(P_NS, "nvSpPr"))
    ET.SubElement(nv_sp_pr, qn(P_NS, "cNvPr"), {"id": "0", "name": "Generated Connector"})
    ET.SubElement(nv_sp_pr, qn(P_NS, "cNvSpPr"))
    ET.SubElement(nv_sp_pr, qn(P_NS, "nvPr"))

    sp_pr = ET.SubElement(shape, qn(P_NS, "spPr"))
    xfrm = ET.SubElement(sp_pr, qn(A_NS, "xfrm"))
    ET.SubElement(xfrm, qn(A_NS, "off"), {"x": str(x), "y": str(y)})
    ET.SubElement(xfrm, qn(A_NS, "ext"), {"cx": str(w), "cy": str(h)})

    geom = ET.SubElement(sp_pr, qn(A_NS, "custGeom"))
    ET.SubElement(geom, qn(A_NS, "avLst"))
    ET.SubElement(geom, qn(A_NS, "gdLst"))
    ET.SubElement(geom, qn(A_NS, "ahLst"))
    ET.SubElement(geom, qn(A_NS, "cxnLst"))
    ET.SubElement(geom, qn(A_NS, "rect"), {"l": "l", "t": "t", "r": "r", "b": "b"})
    path_lst = ET.SubElement(geom, qn(A_NS, "pathLst"))
    path = ET.SubElement(path_lst, qn(A_NS, "path"), {"w": str(w), "h": str(h)})
    for index, (px, py) in enumerate(rel_points):
        tag = "moveTo" if index == 0 else "lnTo"
        point_container = ET.SubElement(path, qn(A_NS, tag))
        ET.SubElement(point_container, qn(A_NS, "pt"), {"x": str(px), "y": str(py)})

    ET.SubElement(sp_pr, qn(A_NS, "noFill"))
    line = ET.SubElement(sp_pr, qn(A_NS, "ln"), {"w": str(int(width_pt * EMU_PER_PT)), "cap": "flat"})
    fill = ET.SubElement(line, qn(A_NS, "solidFill"))
    ET.SubElement(fill, qn(A_NS, "srgbClr"), {"val": color})
    if dashed:
        ET.SubElement(line, qn(A_NS, "prstDash"), {"val": "sysDot"})
    ET.SubElement(line, qn(A_NS, "miter"), {"lim": "800000"})
    if end_arrow:
        ET.SubElement(line, qn(A_NS, "tailEnd"), {"type": "arrow", "w": "med", "len": "sm"})
    tx_body = ET.SubElement(shape, qn(P_NS, "txBody"))
    ET.SubElement(tx_body, qn(A_NS, "bodyPr"), {"rtlCol": "0"})
    ET.SubElement(tx_body, qn(A_NS, "lstStyle"))
    ET.SubElement(tx_body, qn(A_NS, "p"))

    allocator.assign(shape)
    return shape


def create_textbox(
    allocator: IdAllocator,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    text: str,
    font_size_pt: int = 10,
    bold: bool = False,
    align: str = "ctr",
    fill: str | None = None,
    stroke: str | None = None,
    wrap: str | None = None,
    zero_margins: bool = False,
    auto_fit: bool = False,
    anchor: str = "ctr",
) -> ET.Element:
    shape = ET.Element(qn(P_NS, "sp"))
    nv_sp_pr = ET.SubElement(shape, qn(P_NS, "nvSpPr"))
    ET.SubElement(nv_sp_pr, qn(P_NS, "cNvPr"), {"id": "0", "name": "Generated Text"})
    ET.SubElement(nv_sp_pr, qn(P_NS, "cNvSpPr"), {"txBox": "1"})
    ET.SubElement(nv_sp_pr, qn(P_NS, "nvPr"))

    sp_pr = ET.SubElement(shape, qn(P_NS, "spPr"))
    xfrm = ET.SubElement(sp_pr, qn(A_NS, "xfrm"))
    ET.SubElement(xfrm, qn(A_NS, "off"), {"x": str(x), "y": str(y)})
    ET.SubElement(xfrm, qn(A_NS, "ext"), {"cx": str(w), "cy": str(h)})
    prst_geom = ET.SubElement(sp_pr, qn(A_NS, "prstGeom"), {"prst": "rect"})
    ET.SubElement(prst_geom, qn(A_NS, "avLst"))
    if fill:
        fill_node = ET.SubElement(sp_pr, qn(A_NS, "solidFill"))
        ET.SubElement(fill_node, qn(A_NS, "srgbClr"), {"val": fill})
    else:
        ET.SubElement(sp_pr, qn(A_NS, "noFill"))
    if stroke:
        line = ET.SubElement(sp_pr, qn(A_NS, "ln"), {"w": str(EMU_PER_PT)})
        fill_node = ET.SubElement(line, qn(A_NS, "solidFill"))
        ET.SubElement(fill_node, qn(A_NS, "srgbClr"), {"val": stroke})
    else:
        line = ET.SubElement(sp_pr, qn(A_NS, "ln"), {"w": "0"})
        ET.SubElement(line, qn(A_NS, "noFill"))

    set_text(
        shape,
        text,
        font_size_pt=font_size_pt,
        bold=bold,
        align=align,
        anchor=anchor,
        wrap=wrap,
        zero_margins=zero_margins,
        auto_fit=auto_fit,
    )
    allocator.assign(shape)
    return shape


SHAPE_PRESETS = {
    "rounded-rectangle": "roundRect",
    "ellipse": "ellipse",
    "hexagon": "hexagon",
    "cloud": "cloud",
    "cylinder": "can",
}


def create_placeholder_shape(
    allocator: IdAllocator,
    *,
    shape_name: str,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str = "",
    style: dict[str, str] | None = None,
) -> ET.Element:
    style = style or {}
    preset = SHAPE_PRESETS.get(shape_name, "rect")
    fill_token = (style.get("fillColor") or "").strip().lower()
    stroke_token = (style.get("strokeColor") or "").strip().lower()
    fill_color = (style.get("fillColor") or "").replace("#", "") or COLOR_AIR
    stroke_color = (style.get("strokeColor") or "").replace("#", "") or COLOR_NEUTRAL3
    dashed = style.get("dashed") == "1"
    stroke_width = float(style.get("strokeWidth", "1"))
    font_size = int(float(style.get("fontSize", "11")))
    bold = style.get("fontStyle") == "1"

    shape = ET.Element(qn(P_NS, "sp"))
    nv_sp_pr = ET.SubElement(shape, qn(P_NS, "nvSpPr"))
    ET.SubElement(nv_sp_pr, qn(P_NS, "cNvPr"), {"id": "0", "name": "Generated Shape"})
    ET.SubElement(nv_sp_pr, qn(P_NS, "cNvSpPr"))
    ET.SubElement(nv_sp_pr, qn(P_NS, "nvPr"))

    sp_pr = ET.SubElement(shape, qn(P_NS, "spPr"))
    xfrm = ET.SubElement(sp_pr, qn(A_NS, "xfrm"))
    ET.SubElement(xfrm, qn(A_NS, "off"), {"x": str(x), "y": str(y)})
    ET.SubElement(xfrm, qn(A_NS, "ext"), {"cx": str(w), "cy": str(h)})
    prst_geom = ET.SubElement(sp_pr, qn(A_NS, "prstGeom"), {"prst": preset})
    ET.SubElement(prst_geom, qn(A_NS, "avLst"))
    if fill_token == "none":
        ET.SubElement(sp_pr, qn(A_NS, "noFill"))
    else:
        fill = ET.SubElement(sp_pr, qn(A_NS, "solidFill"))
        ET.SubElement(fill, qn(A_NS, "srgbClr"), {"val": fill_color})
    line = ET.SubElement(sp_pr, qn(A_NS, "ln"), {"w": str(int(stroke_width * EMU_PER_PT))})
    if stroke_token == "none":
        ET.SubElement(line, qn(A_NS, "noFill"))
    else:
        line_fill = ET.SubElement(line, qn(A_NS, "solidFill"))
        ET.SubElement(line_fill, qn(A_NS, "srgbClr"), {"val": stroke_color})
    if dashed:
        ET.SubElement(line, qn(A_NS, "prstDash"), {"val": "sysDot"})
    ET.SubElement(line, qn(A_NS, "miter"), {"lim": "800000"})
    if label:
        set_text(shape, label, font_size_pt=font_size, bold=bold, auto_fit=True)
    else:
        ensure_tx_body(shape)
    allocator.assign(shape)
    return shape


def make_slide_root() -> ET.Element:
    slide = ET.Element(qn(P_NS, "sld"))
    c_sld = ET.SubElement(slide, qn(P_NS, "cSld"))
    sp_tree = ET.SubElement(c_sld, qn(P_NS, "spTree"))

    nv_grp = ET.SubElement(sp_tree, qn(P_NS, "nvGrpSpPr"))
    ET.SubElement(nv_grp, qn(P_NS, "cNvPr"), {"id": "1", "name": ""})
    ET.SubElement(nv_grp, qn(P_NS, "cNvGrpSpPr"))
    ET.SubElement(nv_grp, qn(P_NS, "nvPr"))

    grp_sp_pr = ET.SubElement(sp_tree, qn(P_NS, "grpSpPr"))
    xfrm = ET.SubElement(grp_sp_pr, qn(A_NS, "xfrm"))
    ET.SubElement(xfrm, qn(A_NS, "off"), {"x": "0", "y": "0"})
    ET.SubElement(xfrm, qn(A_NS, "ext"), {"cx": "0", "cy": "0"})
    ET.SubElement(xfrm, qn(A_NS, "chOff"), {"x": "0", "y": "0"})
    ET.SubElement(xfrm, qn(A_NS, "chExt"), {"cx": "0", "cy": "0"})

    clr = ET.SubElement(slide, qn(P_NS, "clrMapOvr"))
    ET.SubElement(clr, qn(A_NS, "masterClrMapping"))
    return slide


def serialize_xml(element: ET.Element) -> bytes:
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def fit_dimensions(
    raw: dict[str, Any],
    resolution: dict[str, Any] | None,
    catalog_entry: dict[str, Any] | None,
    native_bbox_emu: dict[str, int] | None = None,
) -> tuple[float, float]:
    width = raw.get("w")
    height = raw.get("h")
    if width is not None and height is not None:
        return float(width), float(height)

    if native_bbox_emu is not None:
        bbox = native_bbox_emu
        aspect = bbox["w"] / max(bbox["h"], 1)
    elif catalog_entry:
        bbox = catalog_entry["bbox_emu"]
        aspect = bbox["w"] / max(bbox["h"], 1)
    else:
        bbox = None
        aspect = 1.0

    if width is None and height is None:
        if catalog_entry and catalog_entry["category"].startswith("Physical - Grouping"):
            assert bbox is not None
            return float(max(bbox["w"] // 6000, 100)), float(
                max(bbox["h"] // 6000, 70)
            )
        width = DEFAULT_ICON_BOX
        height = DEFAULT_ICON_BOX / max(aspect, 0.1)
        return width, height

    if width is None:
        return float(height * aspect), float(height)
    return float(width), float(width / max(aspect, 0.1))


def build_slide_relationships(extra_relationships: list[ET.Element] | None = None) -> bytes:
    return build_slide_relationships_for_page(
        extra_relationships,
        slide_number=1,
        include_presenter_notes=False,
    )


def build_slide_relationships_for_page(
    extra_relationships: list[ET.Element] | None = None,
    *,
    slide_number: int,
    include_presenter_notes: bool,
) -> bytes:
    root = ET.Element(qn(REL_NS, "Relationships"))
    ET.SubElement(
        root,
        qn(REL_NS, "Relationship"),
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
            "Target": f"../slideLayouts/{BLANK_SLIDE_LAYOUT_NAME}",
        },
    )
    if include_presenter_notes:
        ET.SubElement(
            root,
            qn(REL_NS, "Relationship"),
            {
                "Id": "rId2",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
                "Target": f"../notesSlides/notesSlide{slide_number}.xml",
            },
        )
    for rel in extra_relationships or []:
        root.append(copy.deepcopy(rel))
    return serialize_xml(root)


def normalize_presenter_notes(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        text = raw.strip()
        return text or None
    if isinstance(raw, list):
        lines = [str(item).strip() for item in raw if str(item).strip()]
        if not lines:
            return None
        return "\n".join(lines)
    text = str(raw).strip()
    return text or None


def find_placeholder_shape(root: ET.Element, placeholder_type: str) -> ET.Element | None:
    for shape in root.findall(".//p:sp", NS):
        placeholder = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
        if placeholder is not None and placeholder.attrib.get("type") == placeholder_type:
            return shape
    return None


def update_notes_slide_xml(template_xml: bytes, *, notes_text: str, slide_number: int) -> bytes:
    root = ET.fromstring(template_xml)
    body_shape = find_placeholder_shape(root, "body")
    if body_shape is None:
        raise ValueError("Notes slide template is missing a body placeholder.")
    set_text(
        body_shape,
        notes_text,
        font_size_pt=12,
        bold=False,
        align="l",
        preserve=True,
        anchor="t",
    )

    slide_number_shape = find_placeholder_shape(root, "sldNum")
    if slide_number_shape is not None:
        text_node = slide_number_shape.find(".//a:t", NS)
        if text_node is not None:
            text_node.text = str(slide_number)

    normalize_text_bodies(root)
    return serialize_xml(root)


def update_notes_slide_rels(template_xml: bytes, *, slide_number: int) -> bytes:
    root = ET.fromstring(template_xml)
    for rel in root.findall("./rel:Relationship", {"rel": REL_NS}):
        if rel.attrib.get("Type", "").endswith("/slide"):
            rel.attrib["Target"] = f"../slides/slide{slide_number}.xml"
    return serialize_xml(root)


def first_matching_part(contents: dict[str, bytes], preferred_name: str, prefix: str) -> bytes:
    if preferred_name in contents:
        return contents[preferred_name]
    candidates = sorted(name for name in contents if name.startswith(prefix))
    if not candidates:
        raise ValueError(f"Template is missing required part prefix '{prefix}'.")
    return contents[candidates[0]]


def remap_element_relationships(
    element: ET.Element,
    source_relationships: dict[str, ET.Element],
    *,
    next_rel_id: int,
) -> tuple[list[ET.Element], int]:
    rel_map: dict[str, str] = {}
    remapped_relationships: list[ET.Element] = []
    supported_relation_keys = {"id", "embed", "link"}

    for node in element.iter():
        for attr_name, attr_value in list(node.attrib.items()):
            if not attr_name.startswith(f"{{{R_NS}}}"):
                continue
            if attr_name.rsplit("}", 1)[-1] not in supported_relation_keys:
                continue
            source_rel = source_relationships.get(attr_value)
            if source_rel is None:
                continue
            if attr_value not in rel_map:
                rel_map[attr_value] = f"rId{next_rel_id}"
                next_rel_id += 1
                rel_clone = copy.deepcopy(source_rel)
                rel_clone.attrib["Id"] = rel_map[attr_value]
                remapped_relationships.append(rel_clone)
            node.attrib[attr_name] = rel_map[attr_value]

    return remapped_relationships, next_rel_id


def update_presentation_xml(contents: dict[str, bytes], slide_count: int) -> bytes:
    root = ET.fromstring(contents["ppt/presentation.xml"])
    slide_id_list = root.find("./p:sldIdLst", NS)
    if slide_id_list is None:
        raise ValueError("presentation.xml missing slide list")
    slide_id_list.clear()
    for index in range(slide_count):
        ET.SubElement(
            slide_id_list,
            qn(P_NS, "sldId"),
            {
                "id": str(256 + index),
                qn(R_NS, "id"): f"rId{3 + index}",
            },
        )

    ext_lst = root.find("./p:extLst", NS)
    if ext_lst is not None:
        root.remove(ext_lst)

    return serialize_xml(root)


def update_presentation_rels(contents: dict[str, bytes], slide_count: int) -> bytes:
    root = ET.fromstring(contents["ppt/_rels/presentation.xml.rels"])
    slide_rels = [
        rel
        for rel in list(root)
        if rel.attrib.get("Type", "").endswith("/slide")
    ]
    for rel in slide_rels:
        root.remove(rel)

    insert_index = 0
    for index in range(slide_count):
        rel = ET.Element(
            qn(REL_NS, "Relationship"),
            {
                "Id": f"rId{3 + index}",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
                "Target": f"slides/slide{index + 1}.xml",
            },
        )
        root.insert(insert_index, rel)
        insert_index += 1
    return serialize_xml(root)


def update_content_types(contents: dict[str, bytes], slide_count: int, *, include_presenter_notes: bool) -> bytes:
    root = ET.fromstring(contents["[Content_Types].xml"])
    for override in list(root):
        if override.attrib.get("PartName", "").startswith("/ppt/slides/slide"):
            root.remove(override)
        if override.attrib.get("PartName", "").startswith("/ppt/notesSlides/notesSlide"):
            root.remove(override)

    for index in range(slide_count):
        ET.SubElement(
            root,
            qn(CT_NS, "Override"),
            {
                "PartName": f"/ppt/slides/slide{index + 1}.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.presentationml.slide+xml",
            },
        )
        if include_presenter_notes:
            ET.SubElement(
                root,
                qn(CT_NS, "Override"),
                {
                    "PartName": f"/ppt/notesSlides/notesSlide{index + 1}.xml",
                    "ContentType": "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
                },
            )
    return serialize_xml(root)


def prune_unused_parts(contents: dict[str, bytes], slide_count: int, *, include_presenter_notes: bool) -> None:
    note_prefixes = (
        "ppt/notesSlides/notesSlide",
        "ppt/notesSlides/_rels/notesSlide",
    )
    for name in list(contents):
        if not name.startswith(note_prefixes):
            continue
        if not include_presenter_notes:
            del contents[name]
            continue
        match = re.search(r"notesSlide(\d+)\.xml(?:\.rels)?$", name)
        if not match:
            continue
        if int(match.group(1)) > slide_count:
            del contents[name]

    prefixes = (
        "ppt/slides/slide",
        "ppt/slides/_rels/slide",
    )
    for name in list(contents):
        if not name.startswith(prefixes):
            continue
        match = re.search(r"slide(\d+)\.xml(?:\.rels)?$", name)
        if not match:
            continue
        number_text = match.group(1)
        if number_text is None:
            continue
        if int(number_text) > slide_count:
            del contents[name]


def strip_confidential_markings(contents: dict[str, bytes]) -> None:
    phrases = {
        "Copyright © 2022, Oracle and/or its affiliates",
        "Confidential: Internal/Restricted/Highly Restricted",
        "Confidential - Oracle Restricted Employees Only",
        "Confidential - Oracle Restricted Employees Only ",
        "Oracle Restricted Employees Only",
        "Confidential",
    }
    xml_targets = [
        name
        for name in contents
        if name.startswith("ppt/slideMasters/") or name.startswith("ppt/slideLayouts/")
    ]

    for name in xml_targets:
        root = ET.fromstring(contents[name])
        changed = False
        for text_node in root.findall(".//a:t", NS):
            text = text_node.text or ""
            if any(phrase in text for phrase in phrases):
                text_node.text = " "
                changed = True
        if changed:
            contents[name] = serialize_xml(root)


def sanitize_blank_slide_layout(contents: dict[str, bytes]) -> None:
    layout_name = BLANK_SLIDE_LAYOUT_PATH
    if layout_name not in contents:
        return

    root = ET.fromstring(contents[layout_name])
    sp_tree = root.find("./p:cSld/p:spTree", NS)
    if sp_tree is None:
        return

    for child in list(sp_tree):
        if local_name(child) in {"nvGrpSpPr", "grpSpPr"}:
            continue
        sp_tree.remove(child)

    contents[layout_name] = serialize_xml(root)


def compute_segment_center(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    best_segment = None
    best_length = -1.0
    for start, end in zip(points, points[1:]):
        if not math.isclose(start[1], end[1]):
            continue
        length = abs(end[0] - start[0])
        if length > best_length:
            best_length = length
            best_segment = (start, end)
    if best_segment is None:
        return None
    (sx, sy), (tx, _) = best_segment
    return ((sx + tx) / 2, sy)


def point_on_boundary(point: tuple[float, float], bbox: dict[str, float], tolerance: float = BOUNDARY_TOLERANCE) -> bool:
    x, y = point
    left = math.isclose(x, bbox["x"], abs_tol=tolerance)
    right = math.isclose(x, bbox["x"] + bbox["w"], abs_tol=tolerance)
    top = math.isclose(y, bbox["y"], abs_tol=tolerance)
    bottom = math.isclose(y, bbox["y"] + bbox["h"], abs_tol=tolerance)
    inside_x = bbox["x"] - tolerance <= x <= bbox["x"] + bbox["w"] + tolerance
    inside_y = bbox["y"] - tolerance <= y <= bbox["y"] + bbox["h"] + tolerance
    return (inside_x and (top or bottom)) or (inside_y and (left or right))


def center_on_boundary(
    child_bbox: dict[str, float],
    boundary_bbox: dict[str, float],
    side: str,
    tolerance: float = BOUNDARY_TOLERANCE,
) -> bool:
    cx = child_bbox["x"] + (child_bbox["w"] / 2)
    cy = child_bbox["y"] + (child_bbox["h"] / 2)
    if side == "left":
        return math.isclose(cx, boundary_bbox["x"], abs_tol=tolerance)
    if side == "right":
        return math.isclose(cx, boundary_bbox["x"] + boundary_bbox["w"], abs_tol=tolerance)
    if side == "top":
        return math.isclose(cy, boundary_bbox["y"], abs_tol=tolerance)
    if side == "bottom":
        return math.isclose(cy, boundary_bbox["y"] + boundary_bbox["h"], abs_tol=tolerance)
    return False


def segment_intersects_bbox(
    start: tuple[float, float],
    end: tuple[float, float],
    bbox: dict[str, float],
) -> bool:
    sx, sy = start
    ex, ey = end
    if math.isclose(sx, ex):
        if not (bbox["x"] < sx < bbox["x"] + bbox["w"]):
            return False
        low, high = sorted((sy, ey))
        return low < bbox["y"] + bbox["h"] and high > bbox["y"]
    if math.isclose(sy, ey):
        if not (bbox["y"] < sy < bbox["y"] + bbox["h"]):
            return False
        low, high = sorted((sx, ex))
        return low < bbox["x"] + bbox["w"] and high > bbox["x"]
    return True


def overlap_length(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    low = max(min(a_start, a_end), min(b_start, b_end))
    high = min(max(a_start, a_end), max(b_start, b_end))
    return max(high - low, 0.0)


def is_grouping_item(item: dict[str, Any]) -> bool:
    resolution = item.get("resolution") or {}
    icon_title = str(resolution.get("icon_title", ""))
    return icon_title.startswith("Physical - Grouping -")


def grouping_insets(child_bbox: dict[str, float], parent_bbox: dict[str, float]) -> tuple[float, float, float, float]:
    left = child_bbox["x"] - parent_bbox["x"]
    top = child_bbox["y"] - parent_bbox["y"]
    right = (parent_bbox["x"] + parent_bbox["w"]) - (child_bbox["x"] + child_bbox["w"])
    bottom = (parent_bbox["y"] + parent_bbox["h"]) - (child_bbox["y"] + child_bbox["h"])
    return (left, top, right, bottom)


def bboxes_overlap(a: dict[str, float], b: dict[str, float], tolerance: float = 0.0) -> bool:
    overlap_x = overlap_length(a["x"], a["x"] + a["w"], b["x"], b["x"] + b["w"])
    overlap_y = overlap_length(a["y"], a["y"] + a["h"], b["y"], b["y"] + b["h"])
    return overlap_x > tolerance and overlap_y > tolerance


def segment_rides_bbox_edge(
    start: tuple[float, float],
    end: tuple[float, float],
    bbox: dict[str, float],
    tolerance: float = 2.0,
    minimum_overlap: float = 12.0,
) -> bool:
    sx, sy = start
    ex, ey = end
    if math.isclose(sy, ey, abs_tol=tolerance):
        overlap = overlap_length(sx, ex, bbox["x"], bbox["x"] + bbox["w"])
        if overlap < minimum_overlap:
            return False
        return math.isclose(sy, bbox["y"], abs_tol=tolerance) or math.isclose(
            sy, bbox["y"] + bbox["h"], abs_tol=tolerance
        )
    if math.isclose(sx, ex, abs_tol=tolerance):
        overlap = overlap_length(sy, ey, bbox["y"], bbox["y"] + bbox["h"])
        if overlap < minimum_overlap:
            return False
        return math.isclose(sx, bbox["x"], abs_tol=tolerance) or math.isclose(
            sx, bbox["x"] + bbox["w"], abs_tol=tolerance
        )
    return False


def ancestor_chain(element_id: str, placed_by_id: dict[str, dict[str, Any]]) -> set[str]:
    ancestors: set[str] = set()
    current = placed_by_id.get(element_id)
    while current and current.get("parent"):
        parent_id = current["parent"]
        ancestors.add(parent_id)
        current = placed_by_id.get(parent_id)
    return ancestors


def has_expected_spatial_overlap(
    left: dict[str, Any],
    right: dict[str, Any],
    placed_by_id: dict[str, dict[str, Any]],
) -> bool:
    left_id = left.get("id")
    right_id = right.get("id")
    if not left_id or not right_id:
        return False
    left_ancestors = ancestor_chain(left_id, placed_by_id)
    right_ancestors = ancestor_chain(right_id, placed_by_id)
    if left_id in right_ancestors or right_id in left_ancestors:
        return True
    if left.get("boundary_parent") == right_id or right.get("boundary_parent") == left_id:
        return True
    left_boundary_parent = left.get("boundary_parent")
    right_boundary_parent = right.get("boundary_parent")
    if left_boundary_parent and (left_boundary_parent == right_id or left_boundary_parent in right_ancestors):
        return True
    if right_boundary_parent and (right_boundary_parent == left_id or right_boundary_parent in left_ancestors):
        return True
    return False


def route_context(
    placed_elements: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    placed_by_id = {item["id"]: item for item in placed_elements if item.get("id")}
    container_ids = {item.get("parent") for item in placed_elements if item.get("parent")}
    visible_boxes = [
        item
        for item in placed_elements
        if item["kind"] not in {"text", "hidden-anchor"} and item["visible"] and not item.get("qa_ignore")
    ]
    container_boxes = [
        item
        for item in visible_boxes
        if item.get("id") in container_ids
        or str(item.get("category", "")).startswith("Physical - Grouping")
        or str(item.get("category", "")).startswith("Physical - Location")
    ]
    return placed_by_id, visible_boxes, container_boxes


def external_label_bounds_parent(
    parent_id: str | None,
    element_index: dict[str, dict[str, Any]],
) -> str | None:
    if not parent_id:
        return None
    parent = element_index.get(parent_id)
    if parent is None:
        return None
    if parent.get("kind") == "shape" and parent.get("parent"):
        return str(parent["parent"])
    return parent_id


def external_label_bounds_bbox(
    parent_id: str | None,
    element_index: dict[str, dict[str, Any]],
) -> dict[str, float] | None:
    bounds_parent_id = external_label_bounds_parent(parent_id, element_index)
    if not bounds_parent_id:
        return None
    bounds_parent = element_index.get(bounds_parent_id)
    if bounds_parent is None:
        return None
    return bounds_parent["bbox"]


def evaluate_connector_route(
    points: list[tuple[float, float]],
    *,
    source: str,
    target: str,
    placed_elements: list[dict[str, Any]],
    element_index: dict[str, dict[str, Any]],
) -> dict[str, int]:
    placed_by_id, visible_boxes, container_boxes = route_context(placed_elements)
    ignored_boxes = ancestor_chain(source, placed_by_id) | ancestor_chain(target, placed_by_id)
    border_rides = 0
    overlaps = 0

    for start, end in zip(points, points[1:]):
        for box in container_boxes:
            if box.get("id") in ignored_boxes or box.get("id") in {source, target}:
                continue
            if segment_rides_bbox_edge(start, end, box["bbox"]):
                border_rides += 1
                break
        for box in visible_boxes:
            if box.get("id") in ignored_boxes:
                continue
            if str(box.get("category", "")).startswith("Physical - Grouping"):
                continue
            if str(box.get("category", "")).startswith("Physical - Location"):
                continue
            if box.get("id") in {source, target}:
                continue
            if segment_intersects_bbox(start, end, box["bbox"]):
                overlaps += 1
                break

    bends = count_connector_bends(points)
    score = (bends * 12) + (border_rides * 8) + (overlaps * 12)
    return {
        "bends": bends,
        "border_rides": border_rides,
        "overlaps": overlaps,
        "score": score,
    }


def choose_connector_route(
    explicit_points: list[tuple[float, float]],
    auto_points: list[tuple[float, float]],
    *,
    source: str,
    target: str,
    placed_elements: list[dict[str, Any]],
    element_index: dict[str, dict[str, Any]],
) -> tuple[list[tuple[float, float]], dict[str, int], dict[str, int], str]:
    explicit_eval = evaluate_connector_route(
        explicit_points,
        source=source,
        target=target,
        placed_elements=placed_elements,
        element_index=element_index,
    )
    auto_eval = evaluate_connector_route(
        auto_points,
        source=source,
        target=target,
        placed_elements=placed_elements,
        element_index=element_index,
    )

    prefers_auto = False
    if auto_eval["score"] < explicit_eval["score"]:
        prefers_auto = True
    elif auto_eval["score"] == explicit_eval["score"] and auto_eval["bends"] < explicit_eval["bends"]:
        prefers_auto = True

    if prefers_auto:
        return auto_points, auto_eval, explicit_eval, "auto"
    return explicit_points, explicit_eval, auto_eval, "explicit"


def should_review_page_margin(item: dict[str, Any], page_width: float, page_height: float) -> bool:
    if item.get("parent") or not item.get("visible"):
        return False
    if item.get("qa_ignore"):
        return False
    if item["kind"] in {"text", "hidden-anchor"}:
        return False
    bbox = item["bbox"]
    if bbox["w"] >= page_width * 0.35 or bbox["h"] >= page_height * 0.18:
        return True
    return str(item.get("category", "")).startswith("Physical")


def validate_geometry(
    page: dict[str, Any],
    placed_elements: list[dict[str, Any]],
    element_index: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page_width = float(page.get("width", DEFAULT_PAGE_WIDTH))
    page_height = float(page.get("height", DEFAULT_PAGE_HEIGHT))
    placed_by_id, visible_boxes, container_boxes = route_context(placed_elements)

    for item in placed_elements:
        resolution = item.get("resolution") or {}
        resolution_type = str(resolution.get("resolution", ""))
        item_id = item.get("id") or "element"
        query = resolution.get("query") or item_id
        if resolution_type == "placeholder":
            issues.append(
                {
                    "severity": "error",
                    "type": "icon-missing",
                    "message": f"{query} does not have a direct official icon in the deck and is using a placeholder.",
                }
            )
        elif resolution_type == "closest":
            issues.append(
                {
                    "severity": "warning",
                    "type": "icon-fallback",
                    "message": f"{query} is using the closest available official icon instead of a direct match.",
                }
            )

    for item in placed_elements:
        parent_id = item.get("parent")
        if not parent_id or parent_id not in placed_by_id:
            if should_review_page_margin(item, page_width, page_height):
                bbox = item["bbox"]
                if bbox["y"] < PAGE_MARGIN_TOP - 0.5:
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "page-margin",
                            "message": f"{item['id']} is too close to the slide header area.",
                        }
                    )
                if bbox["y"] + bbox["h"] > page_height - PAGE_MARGIN_BOTTOM + 0.5:
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "page-margin",
                            "message": f"{item['id']} is too close to the slide footer area.",
                        }
                    )
                if bbox["x"] < PAGE_MARGIN_LEFT - 0.5:
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "page-margin",
                            "message": f"{item['id']} is too close to the left slide edge.",
                        }
                    )
                if bbox["x"] + bbox["w"] > page_width - PAGE_MARGIN_RIGHT + 0.5:
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "page-margin",
                            "message": f"{item['id']} is too close to the right slide edge.",
                        }
                    )
            boundary_parent_id = item.get("boundary_parent")
            boundary_side = item.get("boundary_side")
            if boundary_parent_id and boundary_side:
                boundary_parent = placed_by_id.get(boundary_parent_id)
                if boundary_parent is None:
                    issues.append(
                        {
                            "severity": "error",
                            "type": "boundary-placement",
                            "message": f"{item['id']} references missing boundary parent {boundary_parent_id}.",
                        }
                    )
                elif not center_on_boundary(item["bbox"], boundary_parent["bbox"], boundary_side):
                    issues.append(
                        {
                            "severity": "error",
                            "type": "boundary-placement",
                            "message": f"{item['id']} is not centered on the {boundary_side} boundary of {boundary_parent_id}.",
                        }
                    )
            if item.get("visible") and not item.get("qa_ignore"):
                text_fit = estimate_text_fit(item, page_width=page_width)
                if text_fit and text_fit["required_scale"] < TEXT_FIT_ERROR_THRESHOLD:
                    scale_pct = max(text_fit["required_scale"], 0.0) * 100.0
                    issues.append(
                        {
                            "severity": "error",
                            "type": "text-overflow",
                            "message": (
                                f"{item['id']} is overstuffed for its box and would need roughly "
                                f"{scale_pct:.0f}% text scale to fit cleanly."
                            ),
                        }
                    )
            continue

        parent = placed_by_id[parent_id]
        child_bbox = item["bbox"]
        parent_bbox = parent["bbox"]
        if (
            child_bbox["x"] < parent_bbox["x"]
            or child_bbox["y"] < parent_bbox["y"]
            or child_bbox["x"] + child_bbox["w"] > parent_bbox["x"] + parent_bbox["w"]
            or child_bbox["y"] + child_bbox["h"] > parent_bbox["y"] + parent_bbox["h"]
        ):
            issues.append(
                {
                    "severity": "error",
                    "type": "containment",
                    "message": f"{item['id']} spills outside parent {parent_id}.",
                }
            )
        if is_grouping_item(item) and is_grouping_item(parent) and not item.get("boundary_parent"):
            if min(grouping_insets(child_bbox, parent_bbox)) < MIN_GROUPING_INSET:
                issues.append(
                    {
                        "severity": "warning",
                        "type": "grouping-inset",
                        "message": f"{item['id']} sits too close to the border of {parent_id}.",
                    }
                )
        boundary_parent_id = item.get("boundary_parent")
        boundary_side = item.get("boundary_side")
        if boundary_parent_id and boundary_side:
            boundary_parent = placed_by_id.get(boundary_parent_id)
            if boundary_parent is None:
                issues.append(
                    {
                        "severity": "error",
                        "type": "boundary-placement",
                        "message": f"{item['id']} references missing boundary parent {boundary_parent_id}.",
                    }
                )
            elif not center_on_boundary(item["bbox"], boundary_parent["bbox"], boundary_side):
                issues.append(
                    {
                        "severity": "error",
                        "type": "boundary-placement",
                        "message": f"{item['id']} is not centered on the {boundary_side} boundary of {boundary_parent_id}.",
                    }
                )

        if item.get("visible") and not item.get("qa_ignore"):
            text_fit = estimate_text_fit(item, page_width=page_width)
            if text_fit and text_fit["required_scale"] < TEXT_FIT_ERROR_THRESHOLD:
                scale_pct = max(text_fit["required_scale"], 0.0) * 100.0
                issues.append(
                    {
                        "severity": "error",
                        "type": "text-overflow",
                        "message": (
                            f"{item['id']} is overstuffed for its box and would need roughly "
                            f"{scale_pct:.0f}% text scale to fit cleanly."
                        ),
                    }
                )

    siblings_by_parent: dict[str, list[dict[str, Any]]] = {}
    for item in placed_elements:
        parent_id = item.get("parent")
        if not parent_id or not item.get("visible"):
            continue
        if item.get("qa_ignore"):
            continue
        if item["kind"] in {"text", "hidden-anchor"}:
            continue
        if item.get("boundary_parent"):
            continue
        siblings_by_parent.setdefault(parent_id, []).append(item)

    for parent_id, siblings in siblings_by_parent.items():
        for index, left in enumerate(siblings):
            left_id = left.get("id")
            if not left_id:
                continue
            for right in siblings[index + 1 :]:
                right_id = right.get("id")
                if not right_id:
                    continue
                if bboxes_overlap(left["bbox"], right["bbox"], tolerance=SIBLING_OVERLAP_TOLERANCE):
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "sibling-overlap",
                            "message": f"{left_id} overlaps {right_id} inside {parent_id}.",
                        }
                    )

    for index, left in enumerate(visible_boxes):
        left_id = left.get("id")
        if not left_id:
            continue
        for right in visible_boxes[index + 1 :]:
            right_id = right.get("id")
            if not right_id:
                continue
            if has_expected_spatial_overlap(left, right, placed_by_id):
                continue
            if is_grouping_item(left) and is_grouping_item(right):
                continue
            if bboxes_overlap(left["bbox"], right["bbox"], tolerance=UNRELATED_OVERLAP_TOLERANCE):
                issues.append(
                    {
                        "severity": "warning",
                        "type": "element-overlap",
                        "message": f"{left_id} overlaps unrelated element {right_id}.",
                    }
                )

    for edge in edges:
        points = edge["points"]
        if len(points) < 2:
            issues.append({"severity": "error", "type": "connector", "message": f"{edge['id']} has too few points."})
            continue

        source_bbox = element_index[edge["source"]]["bbox"]
        target_bbox = element_index[edge["target"]]["bbox"]
        ignored_boxes = ancestor_chain(edge["source"], placed_by_id) | ancestor_chain(edge["target"], placed_by_id)

        if not point_on_boundary(points[0], source_bbox):
            issues.append(
                {"severity": "error", "type": "connector", "message": f"{edge['id']} does not attach to source boundary."}
            )
        if not point_on_boundary(points[-1], target_bbox):
            issues.append(
                {"severity": "error", "type": "connector", "message": f"{edge['id']} does not attach to target boundary."}
            )
        if edge.get("bend_count", 0) > MAX_CONNECTOR_BENDS:
            issues.append(
                {
                    "severity": "warning",
                    "type": "connector-bends",
                    "message": f"{edge['id']} uses too many turns ({edge['bend_count']}).",
                }
            )
        elif edge.get("bend_count", 0) > 0:
            issues.append(
                {
                    "severity": "warning",
                    "type": "connector-elbows",
                    "message": f"{edge['id']} uses elbows ({edge['bend_count']} bend(s)).",
                }
            )
        auto_bends = edge.get("auto_bend_count")
        if auto_bends is not None and edge.get("bend_count", 0) > auto_bends:
            issues.append(
                {
                    "severity": "warning",
                    "type": "connector-bends",
                    "message": f"{edge['id']} is more complex than the automatic orthogonal route.",
                }
            )
        if edge.get("straight_route_available") and edge.get("bend_count", 0) > 0:
            issues.append(
                {
                    "severity": "warning",
                    "type": "connector-straightness",
                    "message": f"{edge['id']} could be rendered as a straight connector.",
                }
            )

        for start, end in zip(points, points[1:]):
            if not (math.isclose(start[0], end[0]) or math.isclose(start[1], end[1])):
                issues.append(
                    {"severity": "error", "type": "connector", "message": f"{edge['id']} contains a diagonal segment."}
                )
            for box in container_boxes:
                if segment_rides_bbox_edge(start, end, box["bbox"]):
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "connector-border-overlap",
                            "message": f"{edge['id']} rides along the border of {box['id']}.",
                        }
                    )
                    break
            for box in visible_boxes:
                if box["id"] in ignored_boxes:
                    continue
                if str(box.get("category", "")).startswith("Physical - Grouping"):
                    continue
                if str(box.get("category", "")).startswith("Physical - Location"):
                    continue
                if box["id"] in {edge["source"], edge["target"]}:
                    continue
                if segment_intersects_bbox(start, end, box["bbox"]):
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "connector-overlap",
                            "message": f"{edge['id']} crosses {box['id']}.",
                        }
                    )
                    break

    return issues


def render_slide(
    page: dict[str, Any],
    *,
    asset_library: AssetLibrary,
    catalog_by_title: dict[str, dict[str, Any]],
    slide_number: int,
    include_presenter_notes: bool,
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    slide_root = make_slide_root()
    sp_tree = slide_sp_tree(slide_root)
    allocator = IdAllocator()

    page_width = float(page.get("width", DEFAULT_PAGE_WIDTH))
    page_height = float(page.get("height", DEFAULT_PAGE_HEIGHT))
    scale_x = SLIDE_CX / page_width
    scale_y = SLIDE_CY / page_height

    placed_elements: list[dict[str, Any]] = []
    element_index: dict[str, dict[str, Any]] = {}
    renderables: list[tuple[dict[str, Any], ET.Element | None]] = []
    external_label_renderables: list[dict[str, Any]] = []
    slide_extra_relationships: list[ET.Element] = []
    next_slide_rel_id = 3 if include_presenter_notes else 2

    for raw in page.get("elements", []):
        item = dict(raw)
        parent_id = item.get("parent")
        parent = element_index.get(parent_id)
        raw_x = float(item.get("x", 0))
        raw_y = float(item.get("y", 0))

        resolution = None
        catalog_entry = None
        kind = item.get("type", "library")
        visible = True
        render_element: ET.Element | None = None
        render_element_relationships: dict[str, ET.Element] | None = None
        native_bbox_emu = None
        separate_external_label_text: str | None = None
        internal_label_hidden = False
        text_content = ""
        font_size_pt = 11
        bold = False
        wrap_enabled = True
        zero_margins = False
        auto_fit = False

        if item.get("query") or item.get("icon_title"):
            query = item.get("icon_title") or item.get("query")
            resolution = resolve_icon(str(query), page=page.get("page_type", "physical"))
            if resolution["resolution"] == "placeholder":
                kind = "shape"
                item["shape"] = item.get("shape") or resolution["placeholder_shape"]
            else:
                catalog_entry = catalog_by_title[resolution["icon_title"]]
                external_label_text = drawio_html_to_text(item["external_label"]) if item.get("external_label") else None
                external_label_side = str(item.get("external_label_side", "")).strip().lower()
                separate_external_label_requested = bool(external_label_text) and (
                    bool(item.get("hide_internal_label"))
                    or bool(item.get("force_external_label"))
                    or external_label_side in {"top", "bottom", "left", "right"}
                )
                if separate_external_label_requested:
                    separate_external_label_text = external_label_text
                internal_label_hidden = bool(item.get("hide_internal_label")) or (
                    bool(separate_external_label_text) and not bool(item.get("preserve_internal_label"))
                )
                if internal_label_hidden:
                    render_element, render_element_relationships = asset_library.clone_with_relationships(
                        catalog_entry["title"]
                    )
                    if crop_group_to_visual_children(render_element):
                        cropped_frame = element_frame(render_element)
                        if cropped_frame is not None:
                            native_bbox_emu = {
                                "x": cropped_frame[0],
                                "y": cropped_frame[1],
                                "w": cropped_frame[2],
                                "h": cropped_frame[3],
                            }
                    normalize_group_coordinate_space(render_element)

        width, height = fit_dimensions(item, resolution, catalog_entry, native_bbox_emu=native_bbox_emu)
        boundary_parent_id = item.get("boundary_parent")
        boundary_side = item.get("boundary_side")
        if boundary_parent_id:
            boundary_parent = element_index.get(boundary_parent_id)
            if boundary_parent is None:
                raise ValueError(f"{item.get('id', 'element')} references unknown boundary parent '{boundary_parent_id}'.")
            boundary_side = boundary_side or "right"
            align_to_id = item.get("boundary_align_to")
            align_to_bbox = element_index[align_to_id]["bbox"] if align_to_id else None
            axis_offset = None
            if boundary_side in {"left", "right"} and "y" in item:
                axis_offset = raw_y
            elif boundary_side in {"top", "bottom"} and "x" in item:
                axis_offset = raw_x
            abs_x, abs_y = place_on_boundary(
                boundary_parent["bbox"],
                side=boundary_side,
                width=width,
                height=height,
                axis_offset=axis_offset,
                align=item.get("boundary_align", "center"),
                align_to_bbox=align_to_bbox,
            )
        else:
            abs_x = raw_x + (parent["bbox"]["x"] if parent else 0.0)
            abs_y = raw_y + (parent["bbox"]["y"] if parent else 0.0)
            if should_apply_page_margins(item, resolution, width, height):
                abs_x, abs_y = clamp_within_page_margins(
                    abs_x,
                    abs_y,
                    width,
                    height,
                    page_width=page_width,
                    page_height=page_height,
                )
        bbox = {"x": abs_x, "y": abs_y, "w": width, "h": height}

        if kind == "text":
            style = parse_style(item.get("style"))
            align = {"left": "l", "center": "ctr", "right": "r"}.get(style.get("align", "center"), "ctr")
            font_size_pt = int(float(style.get("fontSize", "11")))
            bold = style.get("fontStyle") == "1"
            text_value = item.get("text", "")
            text_content = text_value
            single_line_text = "\n" not in text_value
            wrap_enabled = not single_line_text
            zero_margins = single_line_text
            auto_fit = True
            font_size_pt = shrink_font_size_to_fit(
                text_value,
                font_size_pt=font_size_pt,
                bold=bold,
                bbox=bbox,
                wrap_enabled=wrap_enabled,
                zero_margins=zero_margins,
                auto_fit=auto_fit,
                page_width=page_width,
            )
            render_element = create_textbox(
                allocator,
                x=to_emu(abs_x, scale_x),
                y=to_emu(abs_y, scale_y),
                w=to_emu(width, scale_x),
                h=to_emu(height, scale_y),
                text=text_value,
                font_size_pt=font_size_pt,
                bold=bold,
                align=align,
                wrap="none" if single_line_text else None,
                zero_margins=zero_margins,
                auto_fit=auto_fit,
                anchor="t",
            )
            kind = "text"
        elif kind == "shape":
            style = parse_style(item.get("style"))
            font_size_pt = int(float(style.get("fontSize", "11")))
            bold = style.get("fontStyle") == "1"
            text_content = strip_non_placeholder_tags(item.get("label"))
            wrap_enabled = True
            zero_margins = False
            auto_fit = bool(text_content)
            if text_content:
                font_size_pt = shrink_font_size_to_fit(
                    text_content,
                    font_size_pt=font_size_pt,
                    bold=bold,
                    bbox=bbox,
                    wrap_enabled=wrap_enabled,
                    zero_margins=zero_margins,
                    auto_fit=auto_fit,
                    page_width=page_width,
                )
                style["fontSize"] = str(font_size_pt)
            hidden = item.get("id", "").endswith("-anchor") or (
                style.get("fillColor") == "none" and style.get("strokeColor") == "none"
            )
            if hidden:
                visible = False
                kind = "hidden-anchor"
            else:
                render_element = create_placeholder_shape(
                    allocator,
                    shape_name=item.get("shape", "rounded-rectangle"),
                    x=to_emu(abs_x, scale_x),
                    y=to_emu(abs_y, scale_y),
                    w=to_emu(width, scale_x),
                    h=to_emu(height, scale_y),
                    label=strip_non_placeholder_tags(item.get("label")),
                    style=style,
                )
        elif catalog_entry:
            if render_element is None:
                render_element, render_element_relationships = asset_library.clone_with_relationships(
                    catalog_entry["title"]
                )
                normalize_group_coordinate_space(render_element)
            set_element_frame(
                render_element,
                to_emu(abs_x, scale_x),
                to_emu(abs_y, scale_y),
                to_emu(width, scale_x),
                to_emu(height, scale_y),
            )
            label_override = None
            if item.get("value"):
                label_override = drawio_html_to_text(item["value"])
            elif item.get("label"):
                label_override = drawio_html_to_text(item["label"])
            elif item.get("external_label") and not separate_external_label_text:
                label_override = drawio_html_to_text(item["external_label"])
            if label_override is not None:
                override_element_text(render_element, label_override)
            elif internal_label_hidden and not native_bbox_emu:
                override_element_text(render_element, None, hide=True)
            if render_element_relationships:
                extra_relationships, next_slide_rel_id = remap_element_relationships(
                    render_element,
                    render_element_relationships,
                    next_rel_id=next_slide_rel_id,
                )
                slide_extra_relationships.extend(extra_relationships)
            allocator.assign(render_element)

        record = {
            "id": item.get("id"),
            "parent": parent_id,
            "bbox": bbox,
            "kind": kind,
            "visible": visible,
            "qa_ignore": bool(item.get("qa_ignore")),
            "resolution": resolution,
            "category": resolution.get("category") if resolution else None,
            "boundary_parent": boundary_parent_id,
            "boundary_side": boundary_side,
            "text_content": text_content,
            "font_size_pt": font_size_pt,
            "bold": bold,
            "wrap_enabled": wrap_enabled,
            "zero_margins": zero_margins,
            "auto_fit": auto_fit,
        }
        placed_elements.append(record)
        if record["id"]:
            element_index[record["id"]] = record
        renderables.append((record, render_element))

        if separate_external_label_text and visible:
            label_parent_id = external_label_bounds_parent(parent_id, element_index)
            label_parent_bbox = external_label_bounds_bbox(parent_id, element_index)
            label_bbox = choose_external_label_frame(
                item,
                bbox,
                text=separate_external_label_text,
                parent_bbox=label_parent_bbox,
                page_width=page_width,
                page_height=page_height,
            )
            label_font_size = int(item.get("external_label_font_size", 10))
            label_align = {"left": "l", "center": "ctr", "right": "r"}.get(
                str(item.get("external_label_align", "center")).strip().lower(),
                "ctr",
            )
            label_wrap_enabled = "\n" in separate_external_label_text
            label_font_size = shrink_font_size_to_fit(
                separate_external_label_text,
                font_size_pt=label_font_size,
                bold=bool(item.get("external_label_bold", True)),
                bbox=label_bbox,
                wrap_enabled=label_wrap_enabled,
                zero_margins=not bool(item.get("external_label_box", True)),
                auto_fit=True,
                page_width=page_width,
            )
            if bool(item.get("external_label_box", True)):
                external_label_shape = create_placeholder_shape(
                    allocator,
                    shape_name=str(item.get("external_label_shape", "rounded-rectangle")),
                    x=to_emu(label_bbox["x"], scale_x),
                    y=to_emu(label_bbox["y"], scale_y),
                    w=to_emu(label_bbox["w"], scale_x),
                    h=to_emu(label_bbox["h"], scale_y),
                    label=separate_external_label_text,
                    style={
                        "fillColor": str(item.get("external_label_fill", "#F5F4F2")),
                        "strokeColor": str(item.get("external_label_stroke", "#9E9892")),
                        "fontSize": str(label_font_size),
                        "fontStyle": "1" if bool(item.get("external_label_bold", True)) else "0",
                    },
                )
            else:
                external_label_shape = create_textbox(
                    allocator,
                    x=to_emu(label_bbox["x"], scale_x),
                    y=to_emu(label_bbox["y"], scale_y),
                    w=to_emu(label_bbox["w"], scale_x),
                    h=to_emu(label_bbox["h"], scale_y),
                    text=separate_external_label_text,
                    font_size_pt=label_font_size,
                    bold=bool(item.get("external_label_bold", True)),
                    align=label_align,
                    wrap="none" if not label_wrap_enabled else None,
                    zero_margins=True,
                    auto_fit=True,
                )
            label_id = f"{record['id']}__external_label" if record.get("id") else None
            label_record = {
                "id": label_id,
                "parent": label_parent_id,
                "bbox": label_bbox,
                "kind": "text",
                "visible": True,
                "qa_ignore": bool(item.get("qa_ignore")),
                "resolution": None,
                "category": None,
                "boundary_parent": None,
                "boundary_side": None,
                "text_content": separate_external_label_text,
                "font_size_pt": label_font_size,
                "bold": bool(item.get("external_label_bold", True)),
                "wrap_enabled": label_wrap_enabled,
                "zero_margins": not bool(item.get("external_label_box", True)),
                "auto_fit": True,
            }
            placed_elements.append(label_record)
            if label_id:
                element_index[label_id] = label_record
            external_label_renderables.append(
                {
                    "record": label_record,
                    "element": external_label_shape,
                    "item": item,
                    "text": separate_external_label_text,
                    "icon_bbox": bbox,
                    "parent_bbox": label_parent_bbox,
                }
            )

    for record, render_element in renderables:
        if render_element is None or not record["visible"]:
            continue
        sp_tree.append(render_element)

    edge_reports: list[dict[str, Any]] = []
    edge_label_elements: list[ET.Element] = []
    for raw in page.get("elements", []):
        if raw.get("type") != "edge":
            continue
        source = raw["source"]
        target = raw["target"]
        source_bbox = element_index[source]["bbox"]
        target_bbox = element_index[target]["bbox"]
        source_anchor = raw.get("source_anchor")
        target_anchor = raw.get("target_anchor")
        start, end, straight_route_available = resolve_connector_endpoints(
            source_bbox,
            target_bbox,
            source_anchor,
            target_anchor,
        )
        waypoints = [
            (float(point[0]), float(point[1])) if isinstance(point, list) else (float(point["x"]), float(point["y"]))
            for point in raw.get("waypoints", [])
        ]
        explicit_points = build_connector_points(start, end, source_anchor, target_anchor, waypoints)
        auto_points = build_connector_points(start, end, source_anchor, target_anchor, [])
        points = explicit_points
        explicit_eval = evaluate_connector_route(
            explicit_points,
            source=source,
            target=target,
            placed_elements=placed_elements,
            element_index=element_index,
        )
        auto_eval = explicit_eval
        route_mode = "explicit" if waypoints else "auto"
        if waypoints:
            points, explicit_eval, auto_eval, route_mode = choose_connector_route(
                explicit_points,
                auto_points,
                source=source,
                target=target,
                placed_elements=placed_elements,
                element_index=element_index,
            )
        points_emu = [(to_emu(px, scale_x), to_emu(py, scale_y)) for px, py in points]
        style = parse_style(raw.get("style"))
        end_arrow = style.get("endArrow", "arrow") != "none"
        semantic = str(raw.get("semantic", "")).strip().lower()
        semantic_dashed = semantic in {"publish", "fanout", "enqueue", "async", "event", "emit"}
        dashed = style.get("dashed") == "1" if "dashed" in style else semantic_dashed
        connector = create_polyline_shape(
            allocator,
            points_emu,
            end_arrow=end_arrow,
            dashed=dashed,
        )
        sp_tree.append(connector)

        label_text = drawio_html_to_text(raw.get("label")) if raw.get("label") else ""
        if label_text:
            center = compute_segment_center(points)
            if center:
                label_width = max(72.0, min(150.0, (len(label_text) * 8.5) + 22.0))
                if center[1] < 260.0:
                    label_y = center[1] + TOP_LANE_LABEL_GAP
                else:
                    label_y = center[1] - EDGE_LABEL_VERTICAL_GAP - EDGE_LABEL_HEIGHT
                if label_y + EDGE_LABEL_HEIGHT > page_height:
                    label_y = max(center[1] - EDGE_LABEL_VERTICAL_GAP - EDGE_LABEL_HEIGHT, 0.0)
                edge_label_elements.append(
                    create_textbox(
                        allocator,
                        x=to_emu(center[0] - (label_width / 2), scale_x),
                        y=to_emu(label_y, scale_y),
                        w=to_emu(label_width, scale_x),
                        h=to_emu(EDGE_LABEL_HEIGHT, scale_y),
                        text=label_text,
                        font_size_pt=8,
                        bold=False,
                        wrap="none",
                        zero_margins=True,
                        auto_fit=True,
                    )
                )

        edge_reports.append(
            {
                "id": f"edge-{len(edge_reports) + 1}",
                "source": source,
                "target": target,
                "points": points,
                "bend_count": count_connector_bends(points),
                "auto_bend_count": count_connector_bends(auto_points),
                "route_mode": route_mode,
                "route_score": explicit_eval["score"],
                "straight_route_available": straight_route_available,
                "semantic": semantic,
            }
        )

    connector_segments = [
        (start, end)
        for edge in edge_reports
        for start, end in zip(edge["points"], edge["points"][1:])
    ]
    for label_entry in external_label_renderables:
        label_record = label_entry["record"]
        label_element = label_entry["element"]
        if label_record["visible"] and frame_overlaps_segments(label_record["bbox"], connector_segments):
            adjusted_bbox = choose_external_label_frame(
                label_entry["item"],
                label_entry["icon_bbox"],
                text=label_entry["text"],
                parent_bbox=label_entry["parent_bbox"],
                page_width=page_width,
                page_height=page_height,
                avoid_segments=connector_segments,
            )
            label_record["bbox"] = adjusted_bbox
            set_element_frame(
                label_element,
                to_emu(adjusted_bbox["x"], scale_x),
                to_emu(adjusted_bbox["y"], scale_y),
                to_emu(adjusted_bbox["w"], scale_x),
                to_emu(adjusted_bbox["h"], scale_y),
            )
        if label_record["visible"]:
            sp_tree.append(label_element)

    for label_element in edge_label_elements:
        sp_tree.append(label_element)

    normalize_text_bodies(slide_root)
    issues = validate_geometry(page, placed_elements, element_index, edge_reports)
    report = {
        "page": page.get("name", "Slide"),
        "elements": placed_elements,
        "edges": edge_reports,
    }
    quality = {
        "page": page.get("name", "Slide"),
        "issue_count": len(issues),
        "issues": issues,
    }
    return (
        serialize_xml(slide_root),
        build_slide_relationships_for_page(
            slide_extra_relationships,
            slide_number=slide_number,
            include_presenter_notes=include_presenter_notes,
        ),
        report,
        quality,
    )


def load_spec(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def render_presentation(
    spec: dict[str, Any],
    *,
    template_pptx: Path,
    output_path: Path,
    report_out: Path | None,
    quality_out: Path | None,
    fail_on_quality: bool,
    fail_on_text_overflow: bool = False,
) -> None:
    validate_clarification_gate(spec)
    catalog = load_catalog()
    catalog_by_title = {entry["title"]: entry for entry in catalog}
    asset_library = AssetLibrary(template_pptx, catalog)

    pages = spec.get("pages") or []
    if not pages:
        raise ValueError("Spec must contain at least one page")
    include_presenter_notes = any(
        normalize_presenter_notes(page.get("presenter_notes") or page.get("speaker_notes"))
        is not None
        for page in pages
    )

    with zipfile.ZipFile(template_pptx) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}

    slide_reports = []
    slide_qualities = []
    for index, page in enumerate(pages, start=1):
        slide_xml, slide_relationships, report, quality = render_slide(
            page,
            asset_library=asset_library,
            catalog_by_title=catalog_by_title,
            slide_number=index,
            include_presenter_notes=include_presenter_notes,
        )
        contents[f"ppt/slides/slide{index}.xml"] = slide_xml
        contents[f"ppt/slides/_rels/slide{index}.xml.rels"] = slide_relationships
        slide_reports.append(report)
        slide_qualities.append(quality)

    if include_presenter_notes:
        for index, page in enumerate(pages, start=1):
            notes_text = normalize_presenter_notes(
                page.get("presenter_notes") or page.get("speaker_notes")
            ) or ""
            notes_name = f"ppt/notesSlides/notesSlide{index}.xml"
            notes_rels_name = f"ppt/notesSlides/_rels/notesSlide{index}.xml.rels"
            contents[notes_name] = update_notes_slide_xml(
                first_matching_part(contents, notes_name, "ppt/notesSlides/notesSlide"),
                notes_text=notes_text,
                slide_number=index,
            )
            contents[notes_rels_name] = update_notes_slide_rels(
                first_matching_part(
                    contents,
                    notes_rels_name,
                    "ppt/notesSlides/_rels/notesSlide",
                ),
                slide_number=index,
            )

    prune_unused_parts(contents, len(pages), include_presenter_notes=include_presenter_notes)
    contents["ppt/presentation.xml"] = update_presentation_xml(contents, len(pages))
    contents["ppt/_rels/presentation.xml.rels"] = update_presentation_rels(contents, len(pages))
    contents["[Content_Types].xml"] = update_content_types(
        contents,
        len(pages),
        include_presenter_notes=include_presenter_notes,
    )
    sanitize_blank_slide_layout(contents)
    strip_confidential_markings(contents)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr(name, data)

    if report_out:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(
            json.dumps(
                {
                    "title": spec.get("title"),
                    "clarification_gate": spec.get("clarification_gate"),
                    "pages": slide_reports,
                },
                indent=2,
            )
            + "\n"
        )

    if quality_out:
        quality_out.parent.mkdir(parents=True, exist_ok=True)
        quality_out.write_text(json.dumps({"title": spec.get("title"), "pages": slide_qualities}, indent=2) + "\n")

    total_issues = sum(page_quality["issue_count"] for page_quality in slide_qualities)
    total_text_overflow_issues = sum(
        1
        for page_quality in slide_qualities
        for issue in page_quality["issues"]
        if issue.get("type") == "text-overflow"
    )
    if fail_on_quality and total_issues:
        raise SystemExit(f"Quality review found {total_issues} issue(s).")
    if fail_on_text_overflow and total_text_overflow_issues:
        raise SystemExit(f"Text overflow review found {total_text_overflow_issues} blocking issue(s).")


def main() -> None:
    template_pptx, _, _ = default_paths()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True, help="Renderable OCI PPT JSON spec")
    parser.add_argument("--output", type=Path, required=True, help="Output .pptx path")
    parser.add_argument("--report-out", type=Path, help="Optional report JSON path")
    parser.add_argument("--quality-out", type=Path, help="Optional quality JSON path")
    parser.add_argument("--fail-on-quality", action="store_true", help="Exit non-zero if geometry issues are found")
    parser.add_argument(
        "--fail-on-text-overflow",
        action="store_true",
        help="Exit non-zero if any blocking text-overflow issues are found",
    )
    parser.add_argument("--template", type=Path, default=template_pptx, help="Oracle PowerPoint toolkit path")
    args = parser.parse_args()

    spec = load_spec(args.spec)
    render_presentation(
        spec,
        template_pptx=args.template,
        output_path=args.output,
        report_out=args.report_out,
        quality_out=args.quality_out,
        fail_on_quality=args.fail_on_quality,
        fail_on_text_overflow=args.fail_on_text_overflow,
    )


if __name__ == "__main__":
    main()
