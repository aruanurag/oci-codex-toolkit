#!/usr/bin/env python3
"""Basic resolver checks for the OCI PowerPoint skill."""

from __future__ import annotations

from resolve_oci_powerpoint_icon import resolve_icon


def main() -> None:
    queue = resolve_icon("queue")
    assert queue["icon_title"] == "Observability and Management - OCI Queue"
    assert queue["resolution"] == "alias"

    oke = resolve_icon("oke")
    assert oke["icon_title"] == "Developer Services - OCI Container Engine for Kubernetes"

    adb = resolve_icon("adb")
    assert adb["icon_title"] == "Database - Oracle Autonomous Database"

    region = resolve_icon("region")
    assert region["icon_title"] == "Physical - Grouping - OCI Region"

    unknown = resolve_icon("nonexistent bespoke appliance")
    assert unknown["resolution"] == "placeholder"
    assert unknown["placeholder_shape"]

    print("PowerPoint icon resolver tests passed.")


if __name__ == "__main__":
    main()
