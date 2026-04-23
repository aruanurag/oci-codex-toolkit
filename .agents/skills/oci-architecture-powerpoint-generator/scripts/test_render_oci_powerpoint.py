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
    template_pptx, _, _ = default_paths()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        output_path = tmp / "sample.pptx"
        report_path = tmp / "sample.report.json"
        quality_path = tmp / "sample.quality.json"

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

    print("PowerPoint render tests passed.")


if __name__ == "__main__":
    main()
