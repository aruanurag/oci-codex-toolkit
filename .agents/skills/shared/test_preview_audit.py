#!/usr/bin/env python3
"""Focused tests for OCI preview visual review gates."""

from __future__ import annotations

import unittest

import preview_audit as audit


def grouping(element_id: str, title: str, bbox: dict[str, float], parent: str | None = None, label: str | None = None) -> dict:
    return {
        "id": element_id,
        "parent": parent,
        "kind": "library",
        "role": "grouping",
        "resolution": {"resolution": "alias", "icon_title": title},
        "label": label,
        "bbox": bbox,
    }


def icon(element_id: str, title: str, bbox: dict[str, float], parent: str | None = None, **extra: object) -> dict:
    return {
        "id": element_id,
        "parent": parent,
        "kind": "library",
        "role": "icon",
        "resolution": {"resolution": "direct", "icon_title": title},
        "bbox": bbox,
        **extra,
    }


class PreviewAuditVisualGateTests(unittest.TestCase):
    def issue_types(self, elements: list[dict], edges: list[dict]) -> set[str]:
        return {issue["type"] for issue in audit.audit_architecture_visual_gates(elements, edges)}

    def test_clean_ingress_gateway_and_data_tier_pass(self) -> None:
        elements = [
            grouping("vcn", "Physical - Grouping - VCN", {"x": 100, "y": 100, "w": 600, "h": 400}),
            grouping("ad1", "Physical - Grouping - Availability Domain", {"x": 160, "y": 250, "w": 180, "h": 120}, parent="vcn"),
            grouping("public-subnet", "Physical - Grouping - Subnet", {"x": 120, "y": 140, "w": 560, "h": 90}, parent="vcn", label="Public Subnet"),
            grouping("data-subnet", "Physical - Grouping - Subnet", {"x": 120, "y": 380, "w": 560, "h": 90}, parent="vcn", label="Private Data Subnet"),
            icon("waf", "Identity and Security - WAF", {"x": 10, "y": 40, "w": 80, "h": 80}, hide_internal_label=True),
            icon("igw", "Networking - Internet Gateway", {"x": 370, "y": 60, "w": 60, "h": 80}, hide_internal_label=True),
            icon("lb", "Networking - Flexible Load Balancer", {"x": 350, "y": 145, "w": 80, "h": 80}, parent="public-subnet", hide_internal_label=True),
            icon("adb", "Database - Autonomous DB", {"x": 350, "y": 385, "w": 80, "h": 80}, parent="data-subnet"),
        ]
        edges = [
            {"id": "waf-to-igw", "source": "waf", "target": "igw", "points": [(90, 80), (400, 100)]},
            {"id": "igw-to-lb", "source": "igw", "target": "lb", "points": [(400, 140), (390, 145)]},
        ]

        self.assertEqual(self.issue_types(elements, edges), set())

    def test_detects_customer_presentation_regressions(self) -> None:
        elements = [
            grouping("vcn", "Physical - Grouping - VCN", {"x": 100, "y": 100, "w": 600, "h": 400}),
            icon("waf", "Identity and Security - WAF", {"x": 10, "y": 40, "w": 80, "h": 80}),
            icon("igw", "Networking - Internet Gateway", {"x": 250, "y": 250, "w": 60, "h": 80}),
            icon("lb", "Networking - Flexible Load Balancer", {"x": 300, "y": 140, "w": 80, "h": 80}, parent="vcn"),
            grouping("ad1", "Physical - Grouping - Availability Domain", {"x": 120, "y": 220, "w": 300, "h": 200}, parent="vcn"),
            grouping("data-subnet", "Physical - Grouping - Subnet", {"x": 110, "y": 260, "w": 560, "h": 120}, parent="vcn", label="Private Data Subnet"),
            icon("adb", "Database - Autonomous DB", {"x": 250, "y": 300, "w": 80, "h": 80}, parent="data-subnet"),
            {"id": "ops", "kind": "shape", "role": "placeholder", "label": "Security and Operations", "bbox": {"x": 620, "y": 120, "w": 140, "h": 160}},
            {"id": "lb-label", "kind": "text", "role": "text", "text": "Flexible Load Balancer", "bbox": {"x": 385, "y": 150, "w": 130, "h": 24}},
        ]
        edges = [{"id": "waf-to-lb", "source": "waf", "target": "lb", "points": [(90, 80), (300, 180)]}]

        self.assertTrue(
            {
                "duplicate-native-and-custom-label",
                "gateway-not-on-vcn-boundary",
                "internet-gateway-decorative",
                "public-ingress-bypasses-internet-gateway",
                "regional-data-tier-inside-ad-lane",
                "support-panel-overlaps-network-boundary",
            }.issubset(self.issue_types(elements, edges))
        )

    def test_detects_connector_boundary_lanes_and_wrapped_gateway_labels(self) -> None:
        elements = [
            grouping("vcn", "Physical - Grouping - VCN", {"x": 100, "y": 100, "w": 600, "h": 400}),
            grouping("subnet", "Physical - Grouping - Subnet", {"x": 120, "y": 200, "w": 560, "h": 120}, parent="vcn"),
            {"id": "gw-label", "kind": "text", "role": "text", "text": "Internet\nGateway\nLabel", "bbox": {"x": 80, "y": 80, "w": 60, "h": 60}},
        ]
        edges = [{"id": "border-flow", "source": "a", "target": "b", "points": [(130, 200), (660, 200)]}]

        self.assertTrue(
            {"connector-on-container-boundary", "gateway-label-overwrapped"}.issubset(self.issue_types(elements, edges))
        )


if __name__ == "__main__":
    unittest.main()
