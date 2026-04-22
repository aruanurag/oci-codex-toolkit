#!/usr/bin/env python3
"""Tests for bundled OCI reference architecture selection."""

from __future__ import annotations

import unittest

from select_reference_architecture import build_reference_catalog, rank_references, select_reference_bundle


class ReferenceSelectorTests(unittest.TestCase):
    def test_reference_catalog_includes_imported_drawio_files(self) -> None:
        catalog = build_reference_catalog()
        paths = {reference.path.name for reference in catalog}

        self.assertGreaterEqual(len(catalog), 14)
        self.assertIn("hub-spoke-oci.drawio", paths)
        self.assertIn("multi-tenant-app-oci.drawio", paths)
        self.assertIn("secure-web-applications-oci-api-gateway-open-id-architecture.drawio", paths)

    def test_api_gateway_openid_query_prefers_secure_web_reference(self) -> None:
        matches = rank_references("secure web app with API Gateway and OpenID Connect OAuth")
        self.assertEqual(
            matches[0]["path"].split("/")[-1],
            "secure-web-applications-oci-api-gateway-open-id-architecture.drawio",
        )

    def test_architecture_query_prefers_architecture_page_over_data_flow_page(self) -> None:
        matches = rank_references("API Gateway OpenID Connect architecture for a secure web application")
        self.assertEqual(
            matches[0]["path"].split("/")[-1],
            "secure-web-applications-oci-api-gateway-open-id-architecture.drawio",
        )
        self.assertEqual(matches[0]["view_kind"], "architecture")

    def test_hub_spoke_query_prefers_hub_spoke_reference(self) -> None:
        matches = rank_references("hub and spoke VCN with LPG peering and DRG connectivity")
        self.assertEqual(matches[0]["path"].split("/")[-1], "hub-spoke-oci.drawio")

    def test_multi_tenant_query_prefers_multi_tenant_reference(self) -> None:
        matches = rank_references("multi tenant OCI SaaS platform with isolated tenants")
        self.assertEqual(matches[0]["path"].split("/")[-1], "multi-tenant-app-oci.drawio")

    def test_oke_dr_bundle_prefers_oke_primary_with_dr_support(self) -> None:
        bundle = select_reference_bundle("OKE SaaS platform with disaster recovery and public private subnets")
        self.assertIsNotNone(bundle["primary"])
        self.assertEqual(bundle["primary"]["path"].split("/")[-1], "oke-architecture-diagram.drawio")

        supporting = {item["path"].split("/")[-1] for item in bundle["supplemental"]}
        self.assertIn("cloudany-migration-dr-logical-arch.drawio", supporting)


if __name__ == "__main__":
    unittest.main()
