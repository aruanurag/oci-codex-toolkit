#!/usr/bin/env python3
"""Render smoke test for the OCI PowerPoint skill."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import zipfile

from render_oci_powerpoint import render_presentation
from build_powerpoint_catalog import default_paths


def build_clarification_gate(
    *,
    availability: str = "Single-region deployment decisions are either not in scope for this test or intentionally simplified.",
    database: str = "No database choice is required for this guardrail test.",
    subnet_scope: str = "Regional subnet scope is assumed unless a test explicitly says otherwise.",
    icon_resolution: str = "Use a direct OCI icon first, then the closest honest official fallback, then a clearly labeled placeholder.",
) -> dict[str, object]:
    return {
        "status": "satisfied",
        "notes": "Renderer test fixture clarification gate.",
        "decisions": [
            {
                "topic": "availability",
                "question": "Should this test represent HA, DR, or neither?",
                "recommended_option": "Keep the topology as simple as possible unless the specific test requires HA or DR semantics.",
                "selected_option": availability,
                "resolution_source": "not_applicable",
                "rationale": "This fixture exists to exercise renderer behavior, not workload architecture discovery.",
            },
            {
                "topic": "database",
                "question": "Which database type should appear in this test?",
                "recommended_option": "If no database behavior is under test, record that no database choice is in scope.",
                "selected_option": database,
                "resolution_source": "not_applicable",
                "rationale": "The database decision is documented explicitly so the clarification gate stays complete.",
            },
            {
                "topic": "subnet_scope",
                "question": "Should subnet framing be regional or AD-specific?",
                "recommended_option": "Use regional subnet scope unless the test explicitly requires AD-specific subnet framing.",
                "selected_option": subnet_scope,
                "resolution_source": "recommendation_accepted",
                "rationale": "Regional subnets are the default OCI assumption for these renderer fixtures.",
            },
            {
                "topic": "icon_resolution",
                "question": "If a direct icon is missing, what should this test use?",
                "recommended_option": "Use a direct OCI icon first, then the closest honest fallback, then a clearly labeled placeholder.",
                "selected_option": icon_resolution,
                "resolution_source": "recommendation_accepted",
                "rationale": "The renderer should always have an explicit icon-resolution rule recorded before rendering.",
            },
        ],
    }


def main() -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    spec_path = skill_dir / "assets" / "examples" / "specs" / "simple-three-tier-oci-adb.json"
    spec = json.loads(spec_path.read_text())
    missing_gate_spec = {
        "title": "Missing Clarification Gate",
        "pages": [
            {
                "name": "Physical - Missing Clarification Gate",
                "page_type": "physical",
                "width": 800,
                "height": 450,
                "elements": [],
            }
        ],
    }
    placeholder_spec = {
        "title": "Placeholder Shape Transparency",
        "clarification_gate": build_clarification_gate(),
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
    clean_spec = {
        "title": "Clean Render Baseline",
        "clarification_gate": build_clarification_gate(),
        "pages": [
            {
                "name": "Physical - Clean Render Baseline",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "elements": [
                    {
                        "id": "left",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 140,
                        "y": 190,
                        "w": 120,
                        "h": 70,
                        "label": "Ingress",
                        "style": "fillColor=#FFFFFF;strokeColor=#312D2A;"
                    },
                    {
                        "id": "right",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 420,
                        "y": 190,
                        "w": 120,
                        "h": 70,
                        "label": "App",
                        "style": "fillColor=#FFFFFF;strokeColor=#312D2A;"
                    },
                    {
                        "type": "edge",
                        "source": "left",
                        "target": "right",
                        "source_anchor": "right",
                        "target_anchor": "left"
                    }
                ]
            }
        ]
    }
    guardrail_spec = {
        "title": "Layout Guardrails",
        "clarification_gate": build_clarification_gate(),
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
    unrelated_overlap_spec = {
        "title": "Unrelated Overlap Guardrail",
        "clarification_gate": build_clarification_gate(),
        "pages": [
            {
                "name": "Physical - Unrelated Overlap Guardrail",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "elements": [
                    {
                        "id": "left",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 120,
                        "y": 170,
                        "w": 140,
                        "h": 80,
                        "label": "",
                        "style": "fillColor=none;strokeColor=#312D2A;"
                    },
                    {
                        "id": "right",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 220,
                        "y": 190,
                        "w": 140,
                        "h": 80,
                        "label": "",
                        "style": "fillColor=none;strokeColor=#312D2A;"
                    }
                ]
            }
        ]
    }
    icon_guardrail_spec = {
        "title": "Icon Resolution Guardrail",
        "clarification_gate": build_clarification_gate(
            icon_resolution="This test intentionally requests a missing direct icon so the renderer can flag the issue."
        ),
        "pages": [
            {
                "name": "Physical - Icon Resolution Guardrail",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "elements": [
                    {
                        "id": "missing-icon",
                        "query": "compute instance",
                        "x": 160,
                        "y": 150,
                        "w": 120,
                        "h": 90
                    }
                ]
            }
        ]
    }
    semantic_spec = {
        "title": "Semantic Connectors and Text Autofit",
        "clarification_gate": build_clarification_gate(),
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
    overflow_spec = {
        "title": "Text Overflow Guardrail",
        "clarification_gate": build_clarification_gate(),
        "pages": [
            {
                "name": "Physical - Text Overflow Guardrail",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "elements": [
                    {
                        "id": "tiny-card",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 120,
                        "y": 130,
                        "w": 88,
                        "h": 28,
                        "label": "This label is still far too long for this impossible card",
                        "style": "fillColor=#FFFFFF;strokeColor=#312D2A;fontSize=18;fontStyle=1;"
                    },
                    {
                        "id": "tiny-copy",
                        "type": "text",
                        "x": 320,
                        "y": 128,
                        "w": 84,
                        "h": 24,
                        "text": "This body copy is intentionally impossible to fit cleanly.",
                        "style": "align=left;fontSize=17;fontStyle=0;"
                    }
                ]
            }
        ]
    }
    notes_spec = {
        "title": "Presenter Notes Support",
        "clarification_gate": build_clarification_gate(),
        "pages": [
            {
                "name": "Physical - Presenter Notes",
                "page_type": "physical",
                "width": 900,
                "height": 500,
                "presenter_notes": [
                    "Lead with the customer implication instead of adding a visible takeaway strip.",
                    "Use the card as proof and keep the spoken recommendation in notes.",
                ],
                "elements": [
                    {
                        "id": "message",
                        "type": "shape",
                        "shape": "rounded-rectangle",
                        "x": 180,
                        "y": 160,
                        "w": 220,
                        "h": 90,
                        "label": "Proof card",
                        "style": "fillColor=#FFFFFF;strokeColor=#312D2A;"
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
        clean_output_path = tmp / "clean.pptx"
        clean_report_path = tmp / "clean.report.json"
        clean_quality_path = tmp / "clean.quality.json"
        guardrail_output_path = tmp / "guardrail.pptx"
        guardrail_report_path = tmp / "guardrail.report.json"
        guardrail_quality_path = tmp / "guardrail.quality.json"
        unrelated_overlap_output_path = tmp / "unrelated-overlap.pptx"
        unrelated_overlap_report_path = tmp / "unrelated-overlap.report.json"
        unrelated_overlap_quality_path = tmp / "unrelated-overlap.quality.json"
        icon_guardrail_output_path = tmp / "icon-guardrail.pptx"
        icon_guardrail_report_path = tmp / "icon-guardrail.report.json"
        icon_guardrail_quality_path = tmp / "icon-guardrail.quality.json"
        semantic_output_path = tmp / "semantic.pptx"
        semantic_report_path = tmp / "semantic.report.json"
        semantic_quality_path = tmp / "semantic.quality.json"
        overflow_output_path = tmp / "overflow.pptx"
        overflow_report_path = tmp / "overflow.report.json"
        overflow_quality_path = tmp / "overflow.quality.json"
        notes_output_path = tmp / "notes.pptx"
        notes_report_path = tmp / "notes.report.json"
        notes_quality_path = tmp / "notes.quality.json"

        try:
            render_presentation(
                missing_gate_spec,
                template_pptx=template_pptx,
                output_path=tmp / "missing-gate.pptx",
                report_out=tmp / "missing-gate.report.json",
                quality_out=tmp / "missing-gate.quality.json",
                fail_on_quality=False,
            )
        except ValueError as exc:
            assert "clarification_gate" in str(exc), exc
        else:
            raise AssertionError("Expected render_presentation to reject specs without a clarification_gate.")

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
        report = json.loads(report_path.read_text())
        first_edge = report["pages"][0]["edges"][0]
        assert first_edge["bend_count"] == 0, first_edge
        assert first_edge["straight_route_available"] is True, first_edge

        with zipfile.ZipFile(output_path) as archive:
            slide_xml = archive.read("ppt/slides/slide1.xml").decode("utf-8")
            slide_rels_xml = archive.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
            blank_layout_xml = archive.read("ppt/slideLayouts/slideLayout16.xml").decode("utf-8")
            slide_master_xml = archive.read("ppt/slideMasters/slideMaster2.xml").decode("utf-8")
            notes_slides = [name for name in archive.namelist() if name.startswith("ppt/notesSlides/")]
        assert "<a:tailEnd" in slide_xml, slide_xml
        assert "<a:headEnd" not in slide_xml, slide_xml
        assert 'wrap="none"' in slide_xml, slide_xml
        assert "<p:cNvSpPr id=" not in slide_xml, slide_xml
        assert "<p:cNvGrpSpPr id=" not in slide_xml, slide_xml
        assert 'Target="../slideLayouts/slideLayout16.xml"' in slide_rels_xml, slide_rels_xml
        assert 'xmlns:p14=' in blank_layout_xml, blank_layout_xml
        assert 'Requires="p14"' in blank_layout_xml, blank_layout_xml
        assert "<p:pic" not in blank_layout_xml, blank_layout_xml
        assert "<p:sp>" not in blank_layout_xml, blank_layout_xml
        assert "Copyright" not in blank_layout_xml, blank_layout_xml
        assert "Confidential" not in blank_layout_xml, blank_layout_xml
        assert "Confidential" not in slide_master_xml, slide_master_xml
        assert "Copyright" not in slide_master_xml, slide_master_xml
        assert not notes_slides, notes_slides

        render_presentation(
            clean_spec,
            template_pptx=template_pptx,
            output_path=clean_output_path,
            report_out=clean_report_path,
            quality_out=clean_quality_path,
            fail_on_quality=False,
        )

        clean_quality = json.loads(clean_quality_path.read_text())
        assert clean_quality["pages"][0]["issue_count"] == 0, clean_quality

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
            unrelated_overlap_spec,
            template_pptx=template_pptx,
            output_path=unrelated_overlap_output_path,
            report_out=unrelated_overlap_report_path,
            quality_out=unrelated_overlap_quality_path,
            fail_on_quality=False,
        )

        unrelated_overlap_quality = json.loads(unrelated_overlap_quality_path.read_text())
        unrelated_overlap_issue_types = {issue["type"] for issue in unrelated_overlap_quality["pages"][0]["issues"]}
        assert "element-overlap" in unrelated_overlap_issue_types, unrelated_overlap_quality

        render_presentation(
            icon_guardrail_spec,
            template_pptx=template_pptx,
            output_path=icon_guardrail_output_path,
            report_out=icon_guardrail_report_path,
            quality_out=icon_guardrail_quality_path,
            fail_on_quality=False,
        )

        icon_guardrail_quality = json.loads(icon_guardrail_quality_path.read_text())
        icon_guardrail_issue_types = {issue["type"] for issue in icon_guardrail_quality["pages"][0]["issues"]}
        assert "icon-missing" in icon_guardrail_issue_types, icon_guardrail_quality

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
        assert "normAutofit" in semantic_slide_xml, semantic_slide_xml
        assert "spAutoFit" not in semantic_slide_xml, semantic_slide_xml
        assert 'anchor="t"' in semantic_slide_xml, semantic_slide_xml
        semantic_quality = json.loads(semantic_quality_path.read_text())
        semantic_issue_types = {issue["type"] for issue in semantic_quality["pages"][0]["issues"]}
        assert "connector-elbows" in semantic_issue_types, semantic_quality

        render_presentation(
            overflow_spec,
            template_pptx=template_pptx,
            output_path=overflow_output_path,
            report_out=overflow_report_path,
            quality_out=overflow_quality_path,
            fail_on_quality=False,
        )

        overflow_quality = json.loads(overflow_quality_path.read_text())
        overflow_issue_types = {issue["type"] for issue in overflow_quality["pages"][0]["issues"]}
        assert "text-overflow" in overflow_issue_types, overflow_quality

        try:
            render_presentation(
                overflow_spec,
                template_pptx=template_pptx,
                output_path=tmp / "overflow-fail.pptx",
                report_out=tmp / "overflow-fail.report.json",
                quality_out=tmp / "overflow-fail.quality.json",
                fail_on_quality=False,
                fail_on_text_overflow=True,
            )
        except SystemExit as exc:
            assert "Text overflow review found" in str(exc), exc
        else:
            raise AssertionError("Expected render_presentation to fail the hard text-overflow gate.")

        render_presentation(
            notes_spec,
            template_pptx=template_pptx,
            output_path=notes_output_path,
            report_out=notes_report_path,
            quality_out=notes_quality_path,
            fail_on_quality=False,
        )

        with zipfile.ZipFile(notes_output_path) as archive:
            notes_slide_xml = archive.read("ppt/notesSlides/notesSlide1.xml").decode("utf-8")
            notes_slide_rels_xml = archive.read("ppt/notesSlides/_rels/notesSlide1.xml.rels").decode("utf-8")
            notes_slide_rel_xml = archive.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
        assert "customer implication" in notes_slide_xml, notes_slide_xml
        assert "spoken recommendation in notes" in notes_slide_xml, notes_slide_xml
        assert 'Target="../slides/slide1.xml"' in notes_slide_rels_xml, notes_slide_rels_xml
        assert 'relationships/notesSlide' in notes_slide_rel_xml, notes_slide_rel_xml

    print("PowerPoint render tests passed.")


if __name__ == "__main__":
    main()
