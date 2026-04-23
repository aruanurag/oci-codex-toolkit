#!/usr/bin/env python3
"""Smoke tests for the PowerPoint reference catalog and selector."""

from __future__ import annotations

from build_powerpoint_reference_catalog import build_catalog, default_paths
from select_reference_architecture import rank_references


def main() -> None:
    pptx_path, _, _ = default_paths()
    catalog = build_catalog(pptx_path)

    assert any(entry["slide_number"] == 32 for entry in catalog), catalog
    assert any(entry["slide_number"] == 27 for entry in catalog), catalog

    ranked = rank_references("HA OKE app with load balancer and autonomous database")
    assert ranked, ranked
    assert ranked[0]["slide_number"] == 32, ranked[:3]

    print("PowerPoint reference catalog tests passed.")


if __name__ == "__main__":
    main()
