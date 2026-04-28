#!/usr/bin/env python3
"""Inspect an .xlsx workbook without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import posixpath
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "officeRel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL_ID = f"{{{NS['officeRel']}}}id"


def read_xml(package: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        with package.open(name) as handle:
            return ET.parse(handle).getroot()
    except KeyError:
        return None


def rels_for(package: zipfile.ZipFile, source: str) -> dict[str, dict[str, str]]:
    directory = posixpath.dirname(source)
    filename = posixpath.basename(source)
    rels_path = posixpath.join(directory, "_rels", f"{filename}.rels")
    root = read_xml(package, rels_path)
    if root is None:
        return {}
    result: dict[str, dict[str, str]] = {}
    for rel in root.findall("rel:Relationship", NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if not rel_id:
            continue
        if rel.attrib.get("TargetMode") == "External":
            normalized_target = target
        elif target.startswith("/"):
            normalized_target = target.lstrip("/")
        else:
            normalized_target = posixpath.normpath(posixpath.join(directory, target))
        result[rel_id] = {
            "type": rel.attrib.get("Type", ""),
            "target": normalized_target,
            "target_mode": rel.attrib.get("TargetMode", "Internal"),
        }
    return result


def text_of(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    return "".join(element.itertext())


def count_items(root: ET.Element, path: str) -> int:
    return len(root.findall(path, NS))


def sheet_inspection(
    package: zipfile.ZipFile,
    path: str,
    include_formula_samples: bool,
    max_formula_samples: int,
) -> dict[str, Any]:
    root = read_xml(package, path)
    if root is None:
        return {"path": path, "error": "worksheet XML not found"}

    dimension = root.find("main:dimension", NS)
    stats: dict[str, Any] = {
        "path": path,
        "dimension": dimension.attrib.get("ref") if dimension is not None else None,
        "cell_count": 0,
        "formula_count": 0,
        "formulas_with_cached_values": 0,
        "merged_cell_count": count_items(root, "main:mergeCells/main:mergeCell"),
        "table_count": count_items(root, "main:tableParts/main:tablePart"),
        "drawing_count": count_items(root, "main:drawing"),
        "comment_part_count": 0,
        "hyperlink_count": count_items(root, "main:hyperlinks/main:hyperlink"),
        "data_validation_count": count_items(root, "main:dataValidations/main:dataValidation"),
        "conditional_formatting_count": count_items(root, "main:conditionalFormatting"),
        "has_autofilter": root.find("main:autoFilter", NS) is not None,
        "freeze_panes": [],
    }

    for rel in rels_for(package, path).values():
        if rel.get("type", "").endswith("/comments"):
            stats["comment_part_count"] += 1

    formula_samples: list[dict[str, str | None]] = []
    for cell in root.findall(".//main:c", NS):
        stats["cell_count"] += 1
        formula = cell.find("main:f", NS)
        if formula is None:
            continue
        stats["formula_count"] += 1
        if cell.find("main:v", NS) is not None:
            stats["formulas_with_cached_values"] += 1
        if include_formula_samples and len(formula_samples) < max_formula_samples:
            formula_samples.append(
                {
                    "cell": cell.attrib.get("r"),
                    "type": formula.attrib.get("t"),
                    "formula": text_of(formula),
                }
            )
    if formula_samples:
        stats["formula_samples"] = formula_samples

    for pane in root.findall("main:sheetViews/main:sheetView/main:pane", NS):
        stats["freeze_panes"].append(
            {
                "top_left_cell": pane.attrib.get("topLeftCell"),
                "x_split": pane.attrib.get("xSplit"),
                "y_split": pane.attrib.get("ySplit"),
                "state": pane.attrib.get("state"),
            }
        )

    return stats


def inspect_workbook(path: Path, include_formula_samples: bool = True, max_formula_samples: int = 20) -> dict[str, Any]:
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        workbook_path = "xl/workbook.xml"
        workbook = read_xml(package, workbook_path)
        if workbook is None:
            raise ValueError(f"{path} does not contain xl/workbook.xml")
        workbook_rels = rels_for(package, workbook_path)

        calc_pr = workbook.find("main:calcPr", NS)
        workbook_pr = workbook.find("main:workbookPr", NS)
        sheets: list[dict[str, Any]] = []
        totals = {
            "sheet_count": 0,
            "hidden_sheet_count": 0,
            "cell_count": 0,
            "formula_count": 0,
            "formulas_with_cached_values": 0,
            "merged_cell_count": 0,
            "table_count": 0,
            "drawing_count": 0,
            "comment_part_count": 0,
        }

        for sheet in workbook.findall("main:sheets/main:sheet", NS):
            rel_id = sheet.attrib.get(REL_ID)
            rel = workbook_rels.get(rel_id or "", {})
            sheet_path = rel.get("target")
            state = sheet.attrib.get("state", "visible")
            sheet_info: dict[str, Any] = {
                "name": sheet.attrib.get("name"),
                "sheet_id": sheet.attrib.get("sheetId"),
                "state": state,
                "relationship_id": rel_id,
                "path": sheet_path,
            }
            if sheet_path:
                sheet_info.update(sheet_inspection(package, sheet_path, include_formula_samples, max_formula_samples))
            sheets.append(sheet_info)

            totals["sheet_count"] += 1
            if state != "visible":
                totals["hidden_sheet_count"] += 1
            for key in (
                "cell_count",
                "formula_count",
                "formulas_with_cached_values",
                "merged_cell_count",
                "table_count",
                "drawing_count",
                "comment_part_count",
            ):
                totals[key] += int(sheet_info.get(key, 0) or 0)

        defined_names = []
        for defined_name in workbook.findall("main:definedNames/main:definedName", NS):
            defined_names.append(
                {
                    "name": defined_name.attrib.get("name"),
                    "local_sheet_id": defined_name.attrib.get("localSheetId"),
                    "hidden": defined_name.attrib.get("hidden"),
                    "refers_to": text_of(defined_name),
                }
            )

        external_links = [
            {
                "relationship_id": external_ref.attrib.get(REL_ID),
                "target": workbook_rels.get(external_ref.attrib.get(REL_ID, ""), {}).get("target"),
            }
            for external_ref in workbook.findall("main:externalReferences/main:externalReference", NS)
        ]

        return {
            "file": str(path),
            "package": {
                "file_count": len(names),
                "has_vba_project": "xl/vbaProject.bin" in names,
                "has_shared_strings": "xl/sharedStrings.xml" in names,
                "has_styles": "xl/styles.xml" in names,
            },
            "calculation": {
                "calc_mode": calc_pr.attrib.get("calcMode") if calc_pr is not None else None,
                "full_calc_on_load": calc_pr.attrib.get("fullCalcOnLoad") if calc_pr is not None else None,
                "force_full_calc": calc_pr.attrib.get("forceFullCalc") if calc_pr is not None else None,
                "calc_id": calc_pr.attrib.get("calcId") if calc_pr is not None else None,
                "date1904": workbook_pr.attrib.get("date1904") if workbook_pr is not None else None,
            },
            "totals": totals,
            "sheets": sheets,
            "defined_names": defined_names,
            "external_links": external_links,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="Path to an .xlsx workbook.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    parser.add_argument("--no-formula-samples", action="store_true", help="Omit formula samples from the report.")
    parser.add_argument("--max-formula-samples", type=int, default=20, help="Maximum formula samples per sheet.")
    args = parser.parse_args()

    report = inspect_workbook(
        args.workbook.resolve(),
        include_formula_samples=not args.no_formula_samples,
        max_formula_samples=max(args.max_formula_samples, 0),
    )
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
