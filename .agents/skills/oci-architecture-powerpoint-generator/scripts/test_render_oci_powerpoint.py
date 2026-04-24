#!/usr/bin/env python3
"""Render smoke test for the OCI PowerPoint skill."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import zipfile

from render_oci_powerpoint import render_presentation
from build_powerpoint_catalog import default_paths


def main() -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    spec_path = skill_dir / "assets" / "examples" / "specs" / "simple-three-tier-oci-adb.json"
    spec = json.loads(spec_path.read_text())
    placeholder_spec = {
        "title": "Placeholder Shape Transparency",
        "pages": [
            {
                "name": "Physical - Placeholder Shape Transparency",
                "page_type": "physical",
                "width": 800,
                "height": 450,
                "elements": [
                    {
                        "id": "outline-box",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 150,
                        "y": 100,
                        "w": 220,
                        "h": 120,
                        "label": "",
                        "style": "fillColor=none;strokeColor=#312D2A;dashed=1;strokeWidth=2;"
                    }
                ]
            }
        ]
    }
    guardrail_spec = {
        "title": "Layout Guardrails",
        "pages": [
            {
                "name": "Physical - Layout Guardrails",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "elements": [
                    {
                        "id": "region",
                        "query": "region",
                        "x": 80,
                        "y": 70,
                        "w": 420,
                        "h": 320,
                        "value": "<b>OCI Region</b>"
                    },
                    {
                        "id": "vcn",
                        "query": "VCN",
                        "parent": "region",
                        "x": 35,
                        "y": 60,
                        "w": 320,
                        "h": 220,
                        "value": "<b>Guardrail VCN</b><br/>10.0.0.0/16"
                    },
                    {
                        "id": "subnet",
                        "query": "subnet",
                        "parent": "vcn",
                        "x": 0,
                        "y": 40,
                        "w": 260,
                        "h": 90,
                        "value": "<b>Flush Subnet</b><br/>10.0.1.0/24"
                    },
                    {
                        "id": "box-a",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "parent": "subnet",
                        "x": 30,
                        "y": 20,
                        "w": 90,
                        "h": 48,
                        "label": "",
                        "style": "fillColor=none;strokeColor=#312D2A;"
                    },
                    {
                        "id": "box-b",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "parent": "subnet",
                        "x": 75,
                        "y": 28,
                        "w": 90,
                        "h": 48,
                        "label": "",
                        "style": "fillColor=none;strokeColor=#312D2A;"
                    }
                ]
            }
        ]
    }
    semantic_spec = {
        "title": "Semantic Connectors and Text Autofit",
        "pages": [
            {
                "name": "Physical - Semantic Connectors",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "elements": [
                    {
                        "id": "left",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 90,
                        "y": 200,
                        "w": 80,
                        "h": 50,
                        "label": "A"
                    },
                    {
                        "id": "right",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 320,
                        "y": 200,
                        "w": 80,
                        "h": 50,
                        "label": "B"
                    },
                    {
                        "type": "text",
                        "x": 520,
                        "y": 110,
                        "w": 58,
                        "h": 16,
                        "text": "Publisher",
                        "style": "align=left;fontSize=11;fontStyle=1;"
                    },
                    {
                        "type": "edge",
                        "source": "left",
                        "target": "right",
                        "source_anchor": "right",
                        "target_anchor": "left",
                        "semantic": "publish"
                    },
                    {
                        "type": "edge",
                        "source": "right",
                        "target": "left",
                        "source_anchor": "bottom",
                        "target_anchor": "bottom",
                        "waypoints": [[360, 300], [130, 300]],
                        "semantic": "consume"
                    }
                ]
            }
        ]
    }
    template_pptx, _, _ = default_paths()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        output_path = tmp / "sample.pptx"
        report_path = tmp / "sample.report.json"
        quality_path = tmp / "sample.quality.json"
        placeholder_output_path = tmp / "placeholder.pptx"
        placeholder_report_path = tmp / "placeholder.report.json"
        placeholder_quality_path = tmp / "placeholder.quality.json"
        guardrail_output_path = tmp / "guardrail.pptx"
        guardrail_report_path = tmp / "guardrail.report.json"
        guardrail_quality_path = tmp / "guardrail.quality.json"
        semantic_output_path = tmp / "semantic.pptx"
        semantic_report_path = tmp / "semantic.report.json"
        semantic_quality_path = tmp / "semantic.quality.json"

        render_presentation(
            spec,
            template_pptx=template_pptx,
            output_path=output_path,
            report_out=report_path,
            quality_out=quality_path,
            fail_on_quality=False,
        )

        assert output_path.exists()
        quality = json.loads(quality_path.read_text())
        assert quality["pages"]
        assert quality["pages"][0]["issue_count"] == 0, quality
        report = json.loads(report_path.read_text())
        first_edge = report["pages"][0]["edges"][0]
        assert first_edge["bend_count"] == 0, first_edge
        assert first_edge["straight_route_available"] is True, first_edge

        with zipfile.ZipFile(output_path) as archive:
            slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<a:tailEnd" in slide_xml, slide_xml
        assert "<a:headEnd" not in slide_xml, slide_xml
        assert 'wrap="none"' in slide_xml, slide_xml
        assert "<p:cNvSpPr id=" not in slide_xml, slide_xml
        assert "<p:cNvGrpSpPr id=" not in slide_xml, slide_xml

        render_presentation(
            placeholder_spec,
            template_pptx=template_pptx,
            output_path=placeholder_output_path,
            report_out=placeholder_report_path,
            quality_out=placeholder_quality_path,
            fail_on_quality=False,
        )

        with zipfile.ZipFile(placeholder_output_path) as archive:
            placeholder_slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "<a:noFill" in placeholder_slide_xml, placeholder_slide_xml
        assert 'val="none"' not in placeholder_slide_xml, placeholder_slide_xml

        render_presentation(
            guardrail_spec,
            template_pptx=template_pptx,
            output_path=guardrail_output_path,
            report_out=guardrail_report_path,
            quality_out=guardrail_quality_path,
            fail_on_quality=False,
        )

        guardrail_quality = json.loads(guardrail_quality_path.read_text())
        guardrail_issue_types = {issue["type"] for issue in guardrail_quality["pages"][0]["issues"]}
        assert "grouping-inset" in guardrail_issue_types, guardrail_quality
        assert "sibling-overlap" in guardrail_issue_types, guardrail_quality

        render_presentation(
            semantic_spec,
            template_pptx=template_pptx,
            output_path=semantic_output_path,
            report_out=semantic_report_path,
            quality_out=semantic_quality_path,
            fail_on_quality=False,
        )

        with zipfile.ZipFile(semantic_output_path) as archive:
            semantic_slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
        assert semantic_slide_xml.count('<a:prstDash val="sysDot"') == 1, semantic_slide_xml
        assert 'wrap="none"' in semantic_slide_xml, semantic_slide_xml
        assert "spAutoFit" in semantic_slide_xml, semantic_slide_xml

    print("PowerPoint render tests passed.")


if __name__ == "__main__":
    main()
