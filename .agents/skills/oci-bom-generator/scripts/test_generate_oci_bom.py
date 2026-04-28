#!/usr/bin/env python3
from __future__ import annotations

import csv
import os
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from unittest import mock
from decimal import Decimal
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("generate_oci_bom.py")
spec = importlib.util.spec_from_file_location("generate_oci_bom", SCRIPT_PATH)
assert spec and spec.loader
generate_oci_bom = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = generate_oci_bom
spec.loader.exec_module(generate_oci_bom)


REPO_ROOT = Path(__file__).resolve().parents[4]
OKE_SPEC = REPO_ROOT / "output" / "single-region-oke-production-ready.json"
OKE_REPORT = REPO_ROOT / "output" / "single-region-oke-production-ready.report.json"


def minimal_feed(unit_price: str = "0.03") -> dict:
    return {
        "lastUpdated": "2026-04-28T00:00:00Z",
        "items": [
            {
                "partNumber": "B97384",
                "displayName": "Compute - Standard - E5 - OCPU",
                "metricName": "OCPU Per Hour",
                "serviceCategory": "Compute",
                "currencyCodeLocalizations": [
                    {"currencyCode": "USD", "prices": [{"model": "PAY_AS_YOU_GO", "value": float(unit_price)}]}
                ],
            }
        ],
    }


class GenerateOciBomTest(unittest.TestCase):
    def test_generates_oke_bom_from_architecture_spec(self) -> None:
        bom = generate_oci_bom.generate_bom(
            str(OKE_SPEC),
            currency="USD",
            pricing_cache=None,
            offline=True,
            estimator_browser=False,
        )

        services = {line["service"] for line in bom["line_items"]}
        self.assertIn("OCI Kubernetes Engine", services)
        self.assertIn("Compute", services)
        self.assertIn("Block Volume", services)
        self.assertIn("Flexible Load Balancer", services)
        self.assertIn("WAF", services)
        self.assertIn("DNS", services)
        self.assertIn("Autonomous Database", services)
        self.assertEqual(bom["estimated_monthly_total"], "975.8844")
        self.assertEqual(bom["review_status"]["status"], "passed_with_warnings")

    def test_service_list_records_defaults_and_browser_gate(self) -> None:
        bom = generate_oci_bom.generate_bom(
            "OKE with public Load Balancer, WAF, DNS, Autonomous Database, Logging and Monitoring",
            currency="USD",
            pricing_cache=None,
            offline=True,
            estimator_browser=True,
        )

        self.assertEqual(bom["assumptions"]["worker_count"]["source"], "default")
        self.assertEqual(bom["assumptions"]["worker_ocpus"]["value"], "4")
        self.assertEqual(bom["metadata"]["assumption_confirmation"]["status"], "not_confirmed")
        self.assertIn("assumptions_not_confirmed", {warning["code"] for warning in bom["warnings"]})
        self.assertEqual(bom["browser_validation"]["status"], "pending_user_confirmation")
        browser_gate = [
            gate
            for gate in bom["review_status"]["gates"]
            if gate["name"] == "oracle_estimator_browser_validation"
        ][0]
        self.assertEqual(browser_gate["status"], "pending_user_confirmation")

    def test_report_json_list_is_supported(self) -> None:
        bom = generate_oci_bom.generate_bom(
            str(OKE_REPORT),
            currency="USD",
            pricing_cache=None,
            offline=True,
            estimator_browser=False,
        )

        self.assertIn("oke", bom["detected_services"])
        self.assertTrue(bom["line_items"])

    def test_assumptions_preview_does_not_fetch_prices(self) -> None:
        preview = generate_oci_bom.build_assumptions_preview(str(OKE_SPEC), currency="USD")

        self.assertFalse(preview["metadata"]["pricing_fetch_performed"])
        self.assertTrue(preview["metadata"]["confirmation_required"])
        self.assertIn("worker_ocpus", preview["confirmation_prompt"]["defaulted_assumptions"])
        self.assertNotIn("line_items", preview)

    def test_confirmed_assumptions_file_overrides_before_pricing(self) -> None:
        preview = generate_oci_bom.build_assumptions_preview(str(OKE_SPEC), currency="USD")
        preview["assumptions"]["worker_count"]["value"] = "3"
        preview["assumptions"]["worker_count"]["source"] = "user_override"
        preview["assumptions"]["worker_count"]["note"] = "Confirmed higher worker count for test."

        with tempfile.TemporaryDirectory() as tmp:
            assumptions_path = Path(tmp) / "confirmed-assumptions.json"
            assumptions_path.write_text(json.dumps(preview), encoding="utf-8")
            bom = generate_oci_bom.generate_bom(
                str(OKE_SPEC),
                currency="USD",
                pricing_cache=None,
                offline=True,
                estimator_browser=False,
                assumptions_file=str(assumptions_path),
            )

        self.assertEqual(bom["metadata"]["assumption_confirmation"]["status"], "confirmed_from_file")
        self.assertEqual(bom["assumptions"]["worker_count"]["value"], "3")
        self.assertNotIn("assumptions_not_confirmed", {warning["code"] for warning in bom["warnings"]})
        self.assertEqual(bom["estimated_monthly_total"], "1117.0304")

    def test_non_usd_fallback_fails_closed(self) -> None:
        bom = generate_oci_bom.generate_bom(
            "OKE with Autonomous Database",
            currency="EUR",
            pricing_cache=None,
            offline=True,
            estimator_browser=False,
        )

        self.assertFalse(bom["review_status"]["passed"])
        self.assertIn("fallback_currency_unsupported", {warning["code"] for warning in bom["warnings"]})

    def test_auto_cache_hit_skips_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            cache_path = cache_dir / "products-USD.json"
            cache_path.write_text(json.dumps(minimal_feed()), encoding="utf-8")

            with mock.patch.object(generate_oci_bom, "fetch_pricing_feed", side_effect=AssertionError("should not fetch")):
                products, metadata = generate_oci_bom.load_pricing(
                    "USD",
                    pricing_cache=None,
                    offline=False,
                    warnings=[],
                    cache_dir=str(cache_dir),
                    cache_ttl_hours=48,
                )

        self.assertIn("B97384", products)
        self.assertEqual(metadata["type"], "oracle_cost_estimator_products_api_cache_hit")
        self.assertEqual(metadata["cache_ttl_hours"], 48)

    def test_stale_auto_cache_refreshes_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            cache_path = cache_dir / "products-USD.json"
            cache_path.write_text(json.dumps(minimal_feed("0.01")), encoding="utf-8")
            old_time = 0
            os.utime(cache_path, (old_time, old_time))

            with mock.patch.object(
                generate_oci_bom,
                "fetch_pricing_feed",
                return_value=(minimal_feed("0.04"), "https://example.invalid/products?currencyCode=USD"),
            ):
                products, metadata = generate_oci_bom.load_pricing(
                    "USD",
                    pricing_cache=None,
                    offline=False,
                    warnings=[],
                    cache_dir=str(cache_dir),
                    cache_ttl_hours=48,
                )

            refreshed = json.loads(cache_path.read_text())

        self.assertEqual(metadata["type"], "oracle_cost_estimator_products_api")
        self.assertEqual(metadata["cache_ttl_hours"], 48)
        self.assertEqual(str(products["B97384"].list_unit_price), "0.04")
        self.assertEqual(refreshed["items"][0]["currencyCodeLocalizations"][0]["prices"][0]["value"], 0.04)

    def test_outputs_are_written_and_totals_are_consistent(self) -> None:
        bom = generate_oci_bom.generate_bom(
            str(OKE_SPEC),
            currency="USD",
            pricing_cache=None,
            offline=True,
            estimator_browser=False,
        )
        line_total = sum(Decimal(line["monthly_cost"]) for line in bom["line_items"])
        self.assertEqual(f"{line_total:.4f}", bom["estimated_monthly_total"])

        with tempfile.TemporaryDirectory() as tmp:
            outputs = generate_oci_bom.write_outputs(bom, tmp, "test-oci-bom")
            self.assertTrue(Path(outputs["excel"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(zipfile.is_zipfile(outputs["excel"]))
            with zipfile.ZipFile(outputs["excel"]) as workbook:
                names = set(workbook.namelist())
                self.assertIn("xl/workbook.xml", names)
                self.assertIn("xl/worksheets/sheet1.xml", names)
                self.assertIn("xl/worksheets/sheet5.xml", names)

            with open(outputs["json"], "r", encoding="utf-8") as handle:
                roundtrip = json.load(handle)
            self.assertEqual(roundtrip["estimated_monthly_total"], bom["estimated_monthly_total"])

            with open(outputs["csv"], "r", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[-1]["Extended Monthly"], bom["estimated_monthly_total"])


if __name__ == "__main__":
    unittest.main()
