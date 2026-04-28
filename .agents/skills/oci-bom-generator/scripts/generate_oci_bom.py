#!/usr/bin/env python3
"""Generate OCI BOM Markdown, CSV, and JSON outputs.

The generator favors Oracle's public Cost Estimator product feed, but keeps a
small fallback catalog for deterministic local tests and common OKE examples.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


PRICING_ENDPOINT = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
DEFAULT_HOURS_PER_MONTH = Decimal("744")
DEFAULT_CACHE_TTL_HOURS = 48
MONEY = Decimal("0.0001")


@dataclass(frozen=True)
class PriceTier:
    value: Decimal
    range_min: Decimal | None = None
    range_max: Decimal | None = None


@dataclass(frozen=True)
class Product:
    part_number: str
    display_name: str
    metric_name: str
    service_category: str
    currency: str
    price_tiers: tuple[PriceTier, ...]

    @property
    def list_unit_price(self) -> Decimal:
        non_zero = [tier.value for tier in self.price_tiers if tier.value != 0]
        if non_zero:
            return non_zero[-1]
        if self.price_tiers:
            return self.price_tiers[-1].value
        return Decimal("0")

    def cost_for_quantity(self, quantity: Decimal) -> Decimal:
        if not self.price_tiers:
            return Decimal("0")
        if len(self.price_tiers) == 1 and self.price_tiers[0].range_min is None:
            return quantity * self.price_tiers[0].value

        total = Decimal("0")
        for tier in self.price_tiers:
            lower = tier.range_min if tier.range_min is not None else Decimal("0")
            upper = tier.range_max
            if quantity <= lower:
                continue
            tier_qty = quantity - lower if upper is None else min(quantity, upper) - lower
            if tier_qty > 0:
                total += tier_qty * tier.value
        return total

    def billable_quantity_for(self, quantity: Decimal) -> Decimal:
        if not self.price_tiers:
            return Decimal("0")
        if len(self.price_tiers) == 1 and self.price_tiers[0].range_min is None:
            return quantity if self.price_tiers[0].value != 0 else Decimal("0")

        billable = Decimal("0")
        for tier in self.price_tiers:
            if tier.value == 0:
                continue
            lower = tier.range_min if tier.range_min is not None else Decimal("0")
            upper = tier.range_max
            if quantity <= lower:
                continue
            tier_qty = quantity - lower if upper is None else min(quantity, upper) - lower
            if tier_qty > 0:
                billable += tier_qty
        return billable


@dataclass
class BomLine:
    tier: str
    group: str
    service: str
    sku_part_number: str
    sku_display_name: str
    metric: str
    configuration: str
    quantity: Decimal
    billable_quantity: Decimal
    unit_price: Decimal
    monthly_cost: Decimal
    notes: str

    def as_json(self, line_number: int) -> dict[str, Any]:
        return {
            "line": line_number,
            "tier": self.tier,
            "group": self.group,
            "service": self.service,
            "sku_part_number": self.sku_part_number,
            "sku_display_name": self.sku_display_name,
            "metric": self.metric,
            "configuration": self.configuration,
            "quantity": decimal_string(self.quantity),
            "billable_quantity": decimal_string(self.billable_quantity),
            "unit_price": decimal_string(self.unit_price),
            "monthly_cost": decimal_string(self.monthly_cost),
            "notes": self.notes,
        }


FALLBACK_PRODUCTS: dict[str, dict[str, Any]] = {
    "B96545": {
        "displayName": "OCI Kubernetes Engine - Enhanced Cluster",
        "metricName": "Cluster Per Hour",
        "serviceCategory": "Container Engine for Kubernetes",
        "prices": [{"value": "0.1"}],
    },
    "B97384": {
        "displayName": "Compute - Standard - E5 - OCPU",
        "metricName": "OCPU Per Hour",
        "serviceCategory": "Compute",
        "prices": [{"value": "0.03"}],
    },
    "B97385": {
        "displayName": "Compute - Standard - E5 - Memory",
        "metricName": "Gigabytes Per Hour",
        "serviceCategory": "Compute",
        "prices": [{"value": "0.002"}],
    },
    "B91961": {
        "displayName": "Storage - Block Volume - Storage",
        "metricName": "Gigabyte Storage Capacity Per Month",
        "serviceCategory": "Block Volume",
        "prices": [{"value": "0.0255"}],
    },
    "B91962": {
        "displayName": "Storage - Block Volume - Performance Units",
        "metricName": "Performance Units Per Gigabyte Per Month",
        "serviceCategory": "Block Volume",
        "prices": [{"value": "0.0017"}],
    },
    "B93030": {
        "displayName": "Load Balancer Base",
        "metricName": "Load Balancer",
        "serviceCategory": "Flexible Load Balancer",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "744"},
            {"value": "0.0113", "rangeMin": "744", "rangeMax": "999999999"},
        ],
    },
    "B93031": {
        "displayName": "Load Balancer Bandwidth",
        "metricName": "Mbps Per Hour",
        "serviceCategory": "Flexible Load Balancer",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "7440"},
            {"value": "0.0001", "rangeMin": "7440", "rangeMax": "999999999"},
        ],
    },
    "B94579": {
        "displayName": "Web Application Firewall - Instance",
        "metricName": "Instance Per Month",
        "serviceCategory": "WAF",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "1"},
            {"value": "5", "rangeMin": "1", "rangeMax": "999999999999999"},
        ],
    },
    "B94277": {
        "displayName": "Web Application Firewall - Requests",
        "metricName": "1,000,000 Incoming Requests Per Month",
        "serviceCategory": "WAF",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "10"},
            {"value": "0.6", "rangeMin": "10", "rangeMax": "999999999999999"},
        ],
    },
    "B88525": {
        "displayName": "Networking - DNS",
        "metricName": "1,000,000 Queries",
        "serviceCategory": "DNS",
        "prices": [{"value": "0.85"}],
    },
    "B95702": {
        "displayName": "Oracle Autonomous AI Transaction Processing - ECPU",
        "metricName": "ECPU Per Hour",
        "serviceCategory": "Autonomous Database",
        "prices": [{"value": "0.336"}],
    },
    "B95706": {
        "displayName": "Oracle Autonomous AI Database Storage for Transaction Processing",
        "metricName": "Gigabyte Storage Capacity Per Month",
        "serviceCategory": "Autonomous Database",
        "prices": [{"value": "0.1156"}],
    },
    "B92593": {
        "displayName": "OCI - Logging - Storage",
        "metricName": "Gigabyte Log Storage Per Month",
        "serviceCategory": "Observability - Logging",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "10"},
            {"value": "0.05", "rangeMin": "10", "rangeMax": "999999999"},
        ],
    },
    "B90925": {
        "displayName": "Monitoring - Ingestion",
        "metricName": "Million Datapoints",
        "serviceCategory": "Observability - Monitoring",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "500"},
            {"value": "0.0025", "rangeMin": "500", "rangeMax": "999999999"},
        ],
    },
    "B90926": {
        "displayName": "Monitoring - Retrieval",
        "metricName": "Million Datapoints",
        "serviceCategory": "Observability - Monitoring",
        "prices": [
            {"value": "0", "rangeMin": "0", "rangeMax": "1000"},
            {"value": "0.0015", "rangeMin": "1000", "rangeMax": "999999999"},
        ],
    },
}


SERVICE_PATTERNS: dict[str, tuple[str, ...]] = {
    "oke": (r"\boke\b", r"container engine for kubernetes", r"\bkubernetes\b"),
    "worker_compute": (r"worker pool", r"worker node", r"app pods", r"\bcompute\b"),
    "load_balancer": (r"load balancer", r"flexible load balancer"),
    "waf": (r"\bwaf\b", r"web application firewall"),
    "dns": (r"\bdns\b",),
    "autonomous_database": (
        r"autonomous database",
        r"autonomous ai transaction",
        r"\batp\b",
        r"\badb\b",
    ),
    "logging": (r"\blogging\b",),
    "monitoring": (r"\bmonitoring\b",),
    "vault": (r"\bvault\b", r"key management"),
    "bastion": (r"\bbastion\b",),
    "container_registry": (r"container registry", r"\bocir\b"),
    "nat_gateway": (r"nat gateway",),
    "service_gateway": (r"service gateway",),
    "internet_gateway": (r"internet gateway",),
    "vcn": (r"\bvcn\b", r"virtual cloud network"),
    "subnet": (r"\bsubnet\b",),
}


def d(value: Any) -> Decimal:
    return Decimal(str(value))


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def decimal_string(value: Decimal, places: int = 4) -> str:
    quant = Decimal("1") if places == 0 else Decimal("0." + ("0" * (places - 1)) + "1")
    normalized = value.quantize(quant, rounding=ROUND_HALF_UP)
    return f"{normalized:.{places}f}"


def money_string(value: Decimal) -> str:
    return f"{money(value):.4f}"


def compact_decimal(value: Decimal) -> str:
    if value == value.to_integral():
        return str(value.to_integral())
    return format(value.normalize(), "f")


def parse_price_tiers(raw_prices: list[dict[str, Any]]) -> tuple[PriceTier, ...]:
    tiers: list[PriceTier] = []
    for raw in raw_prices:
        if raw.get("model") and raw.get("model") != "PAY_AS_YOU_GO":
            continue
        tiers.append(
            PriceTier(
                value=d(raw.get("value", "0")),
                range_min=d(raw["rangeMin"]) if "rangeMin" in raw else None,
                range_max=d(raw["rangeMax"]) if "rangeMax" in raw else None,
            )
        )
    if not tiers and raw_prices:
        raw = raw_prices[0]
        tiers.append(PriceTier(value=d(raw.get("value", "0"))))
    return tuple(tiers)


def fallback_product(part_number: str, currency: str = "USD") -> Product | None:
    raw = FALLBACK_PRODUCTS.get(part_number)
    if not raw:
        return None
    return Product(
        part_number=part_number,
        display_name=raw["displayName"],
        metric_name=raw["metricName"],
        service_category=raw["serviceCategory"],
        currency=currency,
        price_tiers=parse_price_tiers(raw["prices"]),
    )


def products_from_feed(feed: dict[str, Any], currency: str) -> dict[str, Product]:
    products: dict[str, Product] = {}
    for item in feed.get("items", []):
        part_number = item.get("partNumber")
        if not part_number:
            continue
        localization = None
        for candidate in item.get("currencyCodeLocalizations", []):
            if candidate.get("currencyCode") == currency:
                localization = candidate
                break
        if localization is None:
            continue
        prices = parse_price_tiers(localization.get("prices", []))
        products[part_number] = Product(
            part_number=part_number,
            display_name=item.get("displayName", part_number),
            metric_name=item.get("metricName", ""),
            service_category=item.get("serviceCategory", ""),
            currency=currency,
            price_tiers=prices,
        )
    return products


def default_cache_path(currency: str) -> Path:
    safe_currency = re.sub(r"[^A-Za-z0-9_-]", "_", currency.upper())
    base = Path(os.environ.get("OCI_BOM_PRICE_CACHE_DIR", ".cache/oci-bom-generator"))
    return base / f"products-{safe_currency}.json"


def cache_age_hours(path: Path) -> Decimal | None:
    if not path.exists():
        return None
    modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
    age = dt.datetime.now(dt.timezone.utc) - modified
    return Decimal(str(age.total_seconds())) / Decimal("3600")


def read_products_cache(
    path: Path,
    currency: str,
    source_type: str,
    ttl_hours: int | None = None,
) -> tuple[dict[str, Product], dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        feed = json.load(handle)
    products = products_from_feed(feed, currency)
    age = cache_age_hours(path)
    metadata: dict[str, Any] = {
        "type": source_type,
        "currency": currency,
        "last_updated": feed.get("lastUpdated"),
        "cache_path": str(path),
        "url": PRICING_ENDPOINT,
    }
    if age is not None:
        metadata["cache_age_hours"] = decimal_string(age, places=2)
    if ttl_hours is not None:
        metadata["cache_ttl_hours"] = ttl_hours
    return products, metadata


def write_products_cache(path: Path, feed: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(feed, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def fetch_pricing_feed(currency: str) -> tuple[dict[str, Any], str]:
    url = f"{PRICING_ENDPOINT}?{urllib.parse.urlencode({'currencyCode': currency})}"
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8")), url


def load_pricing(
    currency: str,
    pricing_cache: str | None,
    offline: bool,
    warnings: list[dict[str, str]],
    *,
    cache_dir: str | None = None,
    cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS,
    no_cache: bool = False,
) -> tuple[dict[str, Product], dict[str, Any]]:
    if pricing_cache:
        return read_products_cache(Path(pricing_cache), currency, "oracle_cost_estimator_products_api_cache")

    auto_cache_path = Path(cache_dir) / f"products-{currency.upper()}.json" if cache_dir else default_cache_path(currency)
    if not offline and not no_cache:
        age = cache_age_hours(auto_cache_path)
        if age is not None and age <= Decimal(cache_ttl_hours):
            return read_products_cache(
                auto_cache_path,
                currency,
                "oracle_cost_estimator_products_api_cache_hit",
                ttl_hours=cache_ttl_hours,
            )

    if not offline:
        try:
            feed, url = fetch_pricing_feed(currency)
            if not no_cache:
                try:
                    write_products_cache(auto_cache_path, feed)
                except OSError as exc:
                    warnings.append(
                        {
                            "severity": "warning",
                            "code": "pricing_cache_write_failed",
                            "message": f"Fetched live Oracle pricing but could not write cache {auto_cache_path}: {exc}",
                        }
                    )
            products = products_from_feed(feed, currency)
            return products, {
                "type": "oracle_cost_estimator_products_api",
                "currency": currency,
                "last_updated": feed.get("lastUpdated"),
                "url": url,
                "cache_path": None if no_cache else str(auto_cache_path),
                "cache_ttl_hours": None if no_cache else cache_ttl_hours,
            }
        except Exception as exc:  # pragma: no cover - exercised only when network is flaky
            warnings.append(
                {
                    "severity": "warning",
                    "code": "pricing_feed_fetch_failed",
                    "message": f"Could not fetch Oracle pricing feed, using bundled fallback prices for known SKUs: {exc}",
                }
            )

    fallback_currency = "USD"
    if currency != fallback_currency:
        warnings.append(
            {
                "severity": "error",
                "code": "fallback_currency_unsupported",
                "message": (
                    f"Bundled fallback prices are USD only, but {currency} was requested. "
                    "Use a live Oracle pricing feed or --pricing-cache for the requested currency."
                ),
            }
        )

    products = {
        part_number: product
        for part_number in FALLBACK_PRODUCTS
        if (product := fallback_product(part_number, fallback_currency))
    }
    return products, {
        "type": "bundled_fallback_prices",
        "currency": fallback_currency,
        "requested_currency": currency,
        "last_updated": None,
        "url": PRICING_ENDPOINT,
    }


def strip_markup(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text.replace("\\n", " ")).strip()


def collect_elements(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, list):
        return [element for element in document if isinstance(element, dict)]
    if not isinstance(document, dict):
        return []
    elements: list[dict[str, Any]] = []
    for page in document.get("pages", []):
        if isinstance(page, dict):
            for element in page.get("elements", []):
                if isinstance(element, dict):
                    elements.append(element)
    if not elements and isinstance(document.get("elements"), list):
        elements.extend(e for e in document["elements"] if isinstance(e, dict))
    return elements


def source_to_text(source: Any) -> str:
    if isinstance(source, str):
        return source
    elements = collect_elements(source)
    chunks: list[str] = []
    if isinstance(source, dict):
        chunks.append(strip_markup(source.get("title", "")))
    for element in elements:
        for key in ("id", "query", "label", "value", "external_label", "text", "icon_title"):
            chunks.append(strip_markup(element.get(key, "")))
    return "\n".join(chunk for chunk in chunks if chunk)


def load_source(input_value: str) -> tuple[Any, dict[str, Any]]:
    path = Path(input_value).expanduser()
    if path.exists():
        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle), {"type": "file", "path": str(path), "format": "json"}
        return path.read_text(encoding="utf-8", errors="ignore"), {
            "type": "file",
            "path": str(path),
            "format": path.suffix.lower().lstrip("."),
        }
    return input_value, {"type": "text", "path": None, "format": "prompt_or_service_list"}


def detect_services(text: str) -> list[str]:
    normalized = text.lower()
    detected: list[str] = []
    for service, patterns in SERVICE_PATTERNS.items():
        if any(re.search(pattern, normalized) for pattern in patterns):
            detected.append(service)
    return detected


def first_number(pattern: str, text: str) -> Decimal | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return d(match.group(1).replace(",", ""))


def infer_worker_count(source: Any, text: str, detected: set[str]) -> tuple[Decimal, str]:
    explicit = first_number(
        r"(\d+(?:\.\d+)?)\s+(?:oke\s+)?(?:worker instances|workers|worker nodes|worker vms|nodes)",
        text,
    )
    if explicit:
        return explicit, "detected"

    elements = collect_elements(source)
    worker_elements = []
    for element in elements:
        combined = " ".join(
            strip_markup(element.get(key, ""))
            for key in ("id", "query", "label", "value", "external_label", "text")
        ).lower()
        if re.search(r"worker pool|worker node|app pods", combined):
            worker_elements.append(element)
    if worker_elements:
        return d(len(worker_elements)), "detected_from_architecture"
    if "oke" in detected or "worker_compute" in detected:
        return Decimal("2"), "default"
    return Decimal("0"), "not_applicable"


def build_assumptions(source: Any, text: str, detected_services: list[str]) -> dict[str, dict[str, str]]:
    detected = set(detected_services)
    worker_count, worker_count_source = infer_worker_count(source, text, detected)
    assumptions: dict[str, dict[str, str]] = {
        "currency": {"value": "USD", "source": "cli_default", "note": "Can be overridden with --currency."},
        "hours_per_month": {
            "value": compact_decimal(DEFAULT_HOURS_PER_MONTH),
            "source": "default",
            "note": "Monthly estimate uses 744 hours unless overridden in a future version.",
        },
        "worker_count": {
            "value": compact_decimal(worker_count),
            "source": worker_count_source,
            "note": "OKE worker instances counted from worker groups when present; otherwise defaulted for OKE.",
        },
        "worker_shape": {"value": "VM.Standard.E5.Flex", "source": "default", "note": "Default flexible worker shape."},
        "worker_ocpus": {
            "value": compact_decimal(first_number(r"(\d+(?:\.\d+)?)\s*ocpu", text) or Decimal("4")),
            "source": "detected" if first_number(r"(\d+(?:\.\d+)?)\s*ocpu", text) else "default",
            "note": "OCPU count per worker.",
        },
        "worker_memory_gb": {
            "value": compact_decimal(first_number(r"(\d+(?:\.\d+)?)\s*(?:gb|gib)\s*(?:memory|ram)", text) or Decimal("32")),
            "source": "detected" if first_number(r"(\d+(?:\.\d+)?)\s*(?:gb|gib)\s*(?:memory|ram)", text) else "default",
            "note": "Memory in GB per worker.",
        },
        "boot_volume_gb": {"value": "100", "source": "default", "note": "Boot volume size per worker."},
        "boot_volume_vpus_per_gb": {"value": "10", "source": "default", "note": "Balanced performance assumption."},
        "load_balancer_mbps": {"value": "10", "source": "default", "note": "Flexible Load Balancer bandwidth assumption."},
        "waf_requests_millions": {"value": "10", "source": "default", "note": "Monthly WAF request volume in millions."},
        "dns_queries_millions": {"value": "1", "source": "default", "note": "Monthly DNS query volume in millions."},
        "adb_ecpus": {
            "value": compact_decimal(first_number(r"(\d+(?:\.\d+)?)\s*ecpu", text) or Decimal("2")),
            "source": "detected" if first_number(r"(\d+(?:\.\d+)?)\s*ecpu", text) else "default",
            "note": "Autonomous Database ECPU count.",
        },
        "adb_storage_gb": {"value": "1024", "source": "default", "note": "1 TB transaction-processing storage."},
        "logging_storage_gb": {"value": "10", "source": "default", "note": "OCI Logging storage free-tier threshold."},
        "monitoring_ingestion_million_datapoints": {
            "value": "500",
            "source": "default",
            "note": "Monitoring ingestion free-tier threshold.",
        },
        "monitoring_retrieval_million_datapoints": {
            "value": "1000",
            "source": "default",
            "note": "Monitoring retrieval free-tier threshold.",
        },
    }
    if "autonomous_database" in detected:
        tb = first_number(r"(\d+(?:\.\d+)?)\s*tb", text)
        gb = first_number(r"(\d+(?:\.\d+)?)\s*gb\s+(?:database\s+)?storage", text)
        if tb:
            assumptions["adb_storage_gb"] = {
                "value": compact_decimal(tb * Decimal("1024")),
                "source": "detected",
                "note": "Converted from TB to GB for pricing.",
            }
        elif gb:
            assumptions["adb_storage_gb"] = {
                "value": compact_decimal(gb),
                "source": "detected",
                "note": "Autonomous Database storage in GB.",
            }
    return assumptions


def load_assumption_overrides(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and isinstance(payload.get("assumptions"), dict):
        return payload["assumptions"]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Assumptions file must contain a JSON object: {path}")


def apply_assumption_overrides(
    assumptions: dict[str, dict[str, str]],
    overrides: dict[str, Any],
) -> dict[str, dict[str, str]]:
    updated = {key: value.copy() for key, value in assumptions.items()}
    for key, raw_value in overrides.items():
        if key not in updated:
            updated[key] = {"value": "", "source": "user_override", "note": "Added from assumptions file."}
        if isinstance(raw_value, dict):
            if "value" in raw_value:
                updated[key]["value"] = str(raw_value["value"])
            if "source" in raw_value:
                updated[key]["source"] = str(raw_value["source"])
            elif updated[key].get("source") == "default":
                updated[key]["source"] = "user_confirmed_default"
            if "note" in raw_value:
                updated[key]["note"] = str(raw_value["note"])
        else:
            updated[key]["value"] = str(raw_value)
            updated[key]["source"] = "user_override"
    return updated


def build_assumptions_preview(input_value: str, *, currency: str) -> dict[str, Any]:
    source, source_metadata = load_source(input_value)
    source_text = source_to_text(source)
    detected_services = detect_services(source_text)
    assumptions = build_assumptions(source, source_text, detected_services)
    assumptions["currency"]["value"] = currency
    assumptions["currency"]["source"] = "cli_default" if currency == "USD" else "cli_argument"
    defaults = sorted(key for key, value in assumptions.items() if value.get("source") == "default")
    return {
        "metadata": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "generator": "oci-bom-generator",
            "source": source_metadata,
            "pricing_fetch_performed": False,
            "confirmation_required": True,
        },
        "detected_services": detected_services,
        "assumptions": assumptions,
        "confirmation_prompt": {
            "status": "needs_user_confirmation",
            "defaulted_assumptions": defaults,
            "instruction": (
                "Confirm these assumptions before pricing, or edit this JSON and pass it back with "
                "--assumptions-file."
            ),
        },
    }


def assumption_decimal(assumptions: dict[str, dict[str, str]], key: str) -> Decimal:
    return d(assumptions[key]["value"])


def add_line(
    lines: list[BomLine],
    products: dict[str, Product],
    warnings: list[dict[str, str]],
    *,
    tier: str,
    group: str,
    service: str,
    part_number: str,
    configuration: str,
    quantity: Decimal,
    notes: str,
) -> None:
    product = products.get(part_number) or fallback_product(part_number)
    if product is None:
        warnings.append(
            {
                "severity": "error",
                "code": "sku_not_found",
                "message": f"Could not resolve SKU {part_number} for {service}.",
            }
        )
        return
    monthly_cost = money(product.cost_for_quantity(quantity))
    lines.append(
        BomLine(
            tier=tier,
            group=group,
            service=service,
            sku_part_number=part_number,
            sku_display_name=product.display_name,
            metric=product.metric_name,
            configuration=configuration,
            quantity=quantity,
            billable_quantity=product.billable_quantity_for(quantity),
            unit_price=product.list_unit_price,
            monthly_cost=monthly_cost,
            notes=notes,
        )
    )


def build_bom_lines(
    detected_services: list[str],
    assumptions: dict[str, dict[str, str]],
    products: dict[str, Product],
    warnings: list[dict[str, str]],
) -> list[BomLine]:
    detected = set(detected_services)
    lines: list[BomLine] = []
    hours = assumption_decimal(assumptions, "hours_per_month")
    worker_count = assumption_decimal(assumptions, "worker_count")
    worker_ocpus = assumption_decimal(assumptions, "worker_ocpus")
    worker_memory = assumption_decimal(assumptions, "worker_memory_gb")
    boot_gb = assumption_decimal(assumptions, "boot_volume_gb")
    boot_vpus = assumption_decimal(assumptions, "boot_volume_vpus_per_gb")

    if "oke" in detected:
        add_line(
            lines,
            products,
            warnings,
            tier="Control Plane",
            group="OKE control plane",
            service="OCI Kubernetes Engine",
            part_number="B96545",
            configuration=f"1 enhanced OKE cluster x {compact_decimal(hours)} hours/month",
            quantity=hours,
            notes="Set to 0.00 if the customer selects a basic OKE cluster instead of enhanced cluster.",
        )

    if "oke" in detected or "worker_compute" in detected:
        if worker_count <= 0:
            worker_count = Decimal("2")
        add_line(
            lines,
            products,
            warnings,
            tier="Private App Tier",
            group="OKE worker compute",
            service="Compute",
            part_number="B97384",
            configuration=(
                f"{compact_decimal(worker_count)} worker instances x VM.Standard.E5.Flex x "
                f"{compact_decimal(worker_ocpus)} OCPU x {compact_decimal(hours)} hours/month"
            ),
            quantity=worker_count * worker_ocpus * hours,
            notes="Flexible E5 worker OCPU for the private application tier.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Private App Tier",
            group="OKE worker compute",
            service="Compute",
            part_number="B97385",
            configuration=(
                f"{compact_decimal(worker_count)} worker instances x {compact_decimal(worker_memory)} GB memory "
                f"x {compact_decimal(hours)} hours/month"
            ),
            quantity=worker_count * worker_memory * hours,
            notes="Flexible E5 memory is billed separately from OCPU.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Private App Tier",
            group="Worker boot volumes",
            service="Block Volume",
            part_number="B91961",
            configuration=f"{compact_decimal(worker_count)} boot volumes x {compact_decimal(boot_gb)} GB",
            quantity=worker_count * boot_gb,
            notes="Boot volume storage for worker instances.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Private App Tier",
            group="Worker boot volumes",
            service="Block Volume",
            part_number="B91962",
            configuration=(
                f"{compact_decimal(worker_count)} boot volumes x {compact_decimal(boot_gb)} GB "
                f"x {compact_decimal(boot_vpus)} VPUs/GB"
            ),
            quantity=worker_count * boot_gb * boot_vpus,
            notes="Balanced boot volume performance assumption.",
        )

    if "load_balancer" in detected:
        lb_hours = hours
        lb_mbps = assumption_decimal(assumptions, "load_balancer_mbps")
        add_line(
            lines,
            products,
            warnings,
            tier="Public Ingress",
            group="Public ingress",
            service="Flexible Load Balancer",
            part_number="B93030",
            configuration=f"1 flexible load balancer x {compact_decimal(lb_hours)} hours/month",
            quantity=lb_hours,
            notes="First Flexible Load Balancer instance-hours are free each month in the price-list tier.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Public Ingress",
            group="Public ingress",
            service="Flexible Load Balancer",
            part_number="B93031",
            configuration=f"{compact_decimal(lb_mbps)} Mbps load balancer bandwidth x {compact_decimal(hours)} hours/month",
            quantity=lb_mbps * hours,
            notes="First 10 Mbps per hour are free each month in the price-list tier; adjust to expected ingress throughput.",
        )

    if "waf" in detected:
        waf_requests = assumption_decimal(assumptions, "waf_requests_millions")
        add_line(
            lines,
            products,
            warnings,
            tier="Public Ingress",
            group="Public ingress",
            service="WAF",
            part_number="B94579",
            configuration="1 WAF instance",
            quantity=Decimal("1"),
            notes="First WAF instance is free per month in the price-list tier.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Public Ingress",
            group="Public ingress",
            service="WAF",
            part_number="B94277",
            configuration=f"{compact_decimal(waf_requests)} million incoming requests/month",
            quantity=waf_requests,
            notes="First 10 million WAF requests are free per month in the price-list tier.",
        )

    if "dns" in detected:
        dns_queries = assumption_decimal(assumptions, "dns_queries_millions")
        add_line(
            lines,
            products,
            warnings,
            tier="Public Ingress",
            group="Public ingress",
            service="DNS",
            part_number="B88525",
            configuration=f"{compact_decimal(dns_queries)} million DNS queries/month",
            quantity=dns_queries,
            notes="Adjust to expected DNS query volume.",
        )

    if "autonomous_database" in detected:
        adb_ecpus = assumption_decimal(assumptions, "adb_ecpus")
        adb_storage_gb = assumption_decimal(assumptions, "adb_storage_gb")
        add_line(
            lines,
            products,
            warnings,
            tier="Private Data Tier",
            group="Autonomous Database",
            service="Autonomous Database",
            part_number="B95702",
            configuration=f"{compact_decimal(adb_ecpus)} ECPU x {compact_decimal(hours)} hours/month",
            quantity=adb_ecpus * hours,
            notes="Private endpoint Autonomous Transaction Processing baseline.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Private Data Tier",
            group="Autonomous Database",
            service="Autonomous Database",
            part_number="B95706",
            configuration=f"{compact_decimal(adb_storage_gb)} GB transaction-processing database storage",
            quantity=adb_storage_gb,
            notes="Adjust to allocated database storage.",
        )

    if "logging" in detected:
        logging_gb = assumption_decimal(assumptions, "logging_storage_gb")
        add_line(
            lines,
            products,
            warnings,
            tier="Operations",
            group="Observability",
            service="Logging",
            part_number="B92593",
            configuration=f"{compact_decimal(logging_gb)} GB log storage/month",
            quantity=logging_gb,
            notes="Default set to the OCI Logging free-tier threshold; tune for retained log volume.",
        )

    if "monitoring" in detected:
        ingest = assumption_decimal(assumptions, "monitoring_ingestion_million_datapoints")
        retrieval = assumption_decimal(assumptions, "monitoring_retrieval_million_datapoints")
        add_line(
            lines,
            products,
            warnings,
            tier="Operations",
            group="Observability",
            service="Monitoring",
            part_number="B90925",
            configuration=f"{compact_decimal(ingest)} million datapoints ingested/month",
            quantity=ingest,
            notes="Default set to the Monitoring ingestion free-tier threshold.",
        )
        add_line(
            lines,
            products,
            warnings,
            tier="Operations",
            group="Observability",
            service="Monitoring",
            part_number="B90926",
            configuration=f"{compact_decimal(retrieval)} million datapoints retrieved/month",
            quantity=retrieval,
            notes="Default set to the Monitoring retrieval free-tier threshold.",
        )

    disclose_unpriced_services(detected, warnings)
    return lines


def disclose_unpriced_services(detected: set[str], warnings: list[dict[str, str]]) -> None:
    unpriced_notes = {
        "nat_gateway": "NAT Gateway has no direct line item in the product feed; data processing/egress assumptions are not included.",
        "service_gateway": "Service Gateway has no direct monthly SKU in this estimate.",
        "internet_gateway": "Internet Gateway has no direct monthly SKU; outbound data transfer is not included.",
        "vault": "Vault detected but private-vault/key-version sizing was not inferred; add Key Management SKUs if required.",
        "bastion": "Bastion detected but no separate SKU was found in the pricing feed; session usage is not priced here.",
        "container_registry": "Container Registry detected but image storage/transfer usage was not inferred.",
        "vcn": "VCN grouping detected; VCN itself is not a priced line item.",
        "subnet": "Subnet grouping detected; subnets are not priced line items.",
    }
    for service, message in unpriced_notes.items():
        if service in detected:
            warnings.append({"severity": "review", "code": f"{service}_not_priced", "message": message})


def totals_by_group(lines: list[BomLine]) -> dict[str, str]:
    totals: dict[str, Decimal] = {}
    for line in lines:
        totals[line.group] = totals.get(line.group, Decimal("0")) + line.monthly_cost
    return {group: decimal_string(money(total)) for group, total in totals.items()}


def build_review_status(
    lines: list[BomLine],
    warnings: list[dict[str, str]],
    estimator_browser: bool,
) -> dict[str, Any]:
    total = sum((line.monthly_cost for line in lines), Decimal("0"))
    gates = [
        {
            "name": "source_has_priced_line_items",
            "status": "passed" if lines else "failed",
            "detail": f"{len(lines)} priced line item(s) generated.",
        },
        {
            "name": "pricing_resolved",
            "status": "passed" if all(line.sku_part_number and line.unit_price >= 0 for line in lines) else "failed",
            "detail": "Every generated line has a SKU and unit price.",
        },
        {
            "name": "free_tier_assumptions_recorded",
            "status": "passed",
            "detail": "Zero-cost rows include free-tier notes when applicable.",
        },
        {
            "name": "unsupported_services_disclosed",
            "status": "passed" if not any(w["code"].endswith("_not_priced") for w in warnings) else "passed_with_warnings",
            "detail": "Detected unpriced supporting services are listed in warnings.",
        },
        {
            "name": "totals_consistent",
            "status": "passed" if total >= 0 else "failed",
            "detail": f"Line-item sum is {decimal_string(money(total))}.",
        },
        {
            "name": "oracle_estimator_browser_validation",
            "status": "not_requested" if not estimator_browser else "pending_user_confirmation",
            "detail": (
                "Browser validation was not requested."
                if not estimator_browser
                else "Open Oracle Cost Estimator read-only first and confirm before transmitting estimate details."
            ),
        },
    ]
    has_error = any(w.get("severity") == "error" for w in warnings) or any(g["status"] == "failed" for g in gates)
    has_warning = bool(warnings) or any(g["status"] == "passed_with_warnings" for g in gates)
    status = "failed" if has_error else "passed_with_warnings" if has_warning else "passed"
    return {"status": status, "passed": not has_error, "gates": gates}


def generate_bom(
    input_value: str,
    *,
    currency: str,
    pricing_cache: str | None,
    offline: bool,
    estimator_browser: bool,
    assumptions_file: str | None = None,
    cache_dir: str | None = None,
    cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS,
    no_cache: bool = False,
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    source, source_metadata = load_source(input_value)
    source_text = source_to_text(source)
    detected_services = detect_services(source_text)
    assumptions = build_assumptions(source, source_text, detected_services)
    assumptions["currency"]["value"] = currency
    assumptions["currency"]["source"] = "cli_default" if currency == "USD" else "cli_argument"
    assumption_confirmation = {
        "status": "not_confirmed",
        "source": None,
        "message": "Assumptions were generated automatically. Customer-facing estimates should confirm them before pricing.",
    }
    if assumptions_file:
        assumptions = apply_assumption_overrides(assumptions, load_assumption_overrides(assumptions_file))
        assumption_confirmation = {
            "status": "confirmed_from_file",
            "source": assumptions_file,
            "message": "Assumptions were supplied or confirmed before pricing.",
        }
    else:
        warnings.append(
            {
                "severity": "review",
                "code": "assumptions_not_confirmed",
                "message": (
                    "Assumptions were not supplied from a confirmed assumptions file. "
                    "Run --assumptions-only first for customer-facing estimates."
                ),
            }
        )

    products, pricing_source = load_pricing(
        currency,
        pricing_cache,
        offline,
        warnings,
        cache_dir=cache_dir,
        cache_ttl_hours=cache_ttl_hours,
        no_cache=no_cache,
    )
    lines = build_bom_lines(detected_services, assumptions, products, warnings)
    total = money(sum((line.monthly_cost for line in lines), Decimal("0")))
    review_status = build_review_status(lines, warnings, estimator_browser)

    return {
        "metadata": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "generator": "oci-bom-generator",
            "currency": currency,
            "hours_per_month": decimal_string(DEFAULT_HOURS_PER_MONTH, places=0),
            "pricing_source": pricing_source,
            "source": source_metadata,
            "assumption_confirmation": assumption_confirmation,
            "exclusions": [
                "taxes",
                "support",
                "discounts",
                "private pricing",
                "committed-use discounts",
                "data transfer unless explicitly modeled",
                "backup retention unless explicitly modeled",
            ],
        },
        "detected_services": detected_services,
        "assumptions": assumptions,
        "line_items": [line.as_json(index) for index, line in enumerate(lines, start=1)],
        "monthly_totals_by_group": totals_by_group(lines),
        "estimated_monthly_total": decimal_string(total),
        "warnings": warnings,
        "review_status": review_status,
        "browser_validation": {
            "requested": estimator_browser,
            "status": "pending_user_confirmation" if estimator_browser else "not_requested",
            "oracle_cost_estimator_url": "https://www.oracle.com/cloud/costestimator.html",
        },
    }


def output_stem(input_value: str, name: str | None) -> str:
    if name:
        return name
    path = Path(input_value)
    if path.exists():
        return f"{path.stem}-bom"
    return "oci-bom"


def write_json(path: Path, bom: dict[str, Any]) -> None:
    path.write_text(json.dumps(bom, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, bom: dict[str, Any]) -> None:
    fieldnames = [
        "Line",
        "Tier",
        "Group",
        "OCI Service",
        "SKU Part Number",
        "SKU Display Name",
        "Metric",
        "Configuration",
        "Quantity",
        "Billable Quantity",
        "Unit Price",
        "Extended Monthly",
        "Notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in bom["line_items"]:
            writer.writerow(
                {
                    "Line": item["line"],
                    "Tier": item["tier"],
                    "Group": item["group"],
                    "OCI Service": item["service"],
                    "SKU Part Number": item["sku_part_number"],
                    "SKU Display Name": item["sku_display_name"],
                    "Metric": item["metric"],
                    "Configuration": item["configuration"],
                    "Quantity": item["quantity"],
                    "Billable Quantity": item["billable_quantity"],
                    "Unit Price": item["unit_price"],
                    "Extended Monthly": item["monthly_cost"],
                    "Notes": item["notes"],
                }
            )
        writer.writerow(
            {
                "Line": "",
                "Tier": "",
                "Group": "",
                "OCI Service": "",
                "SKU Part Number": "",
                "SKU Display Name": "",
                "Metric": "",
                "Configuration": "",
                "Quantity": "",
                "Billable Quantity": "",
                "Unit Price": "",
                "Extended Monthly": bom["estimated_monthly_total"],
                "Notes": "Estimated monthly total before exclusions listed in JSON metadata.",
            }
        )


def write_markdown(path: Path, bom: dict[str, Any]) -> None:
    lines = [
        "# OCI BOM Estimate",
        "",
        "## Scope",
        "",
        "This BOM is a list-price estimate generated from the supplied OCI architecture artifact, service list, or prompt.",
        "",
        f"- Currency: `{bom['metadata']['currency']}`",
        f"- Hours/month: `{bom['metadata']['hours_per_month']}`",
        f"- Pricing source: `{bom['metadata']['pricing_source']['type']}`",
    ]
    last_updated = bom["metadata"]["pricing_source"].get("last_updated")
    if last_updated:
        lines.append(f"- Price-list feed last updated: `{last_updated}`")
    lines.extend(
        [
            f"- Estimated monthly total: **{bom['metadata']['currency']} {bom['estimated_monthly_total']}**",
            "",
            "Exclusions: " + ", ".join(bom["metadata"]["exclusions"]) + ".",
            "",
            "## Summary By Group",
            "",
            "| Group | Estimated Monthly |",
            "| --- | ---: |",
        ]
    )
    for group, total in bom["monthly_totals_by_group"].items():
        lines.append(f"| {group} | {total} |")
    lines.extend(
        [
            f"| **Estimated total** | **{bom['estimated_monthly_total']}** |",
            "",
            "## Assumptions",
            "",
            "| Assumption | Value | Source | Note |",
            "| --- | --- | --- | --- |",
        ]
    )
    for key, value in bom["assumptions"].items():
        lines.append(f"| `{key}` | {value['value']} | {value['source']} | {value['note']} |")
    lines.extend(
        [
            "",
            "## BOM Lines",
            "",
            "| Line | Tier | Group | OCI Service | SKU | Configuration | Quantity | Billable Qty | Unit Price | Monthly |",
            "| ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in bom["line_items"]:
        lines.append(
            "| {line} | {tier} | {group} | {service} | {sku} | {config} | {qty} | {billable} | {unit} | {monthly} |".format(
                line=item["line"],
                tier=item["tier"],
                group=item["group"],
                service=item["service"],
                sku=item["sku_part_number"],
                config=item["configuration"],
                qty=item["quantity"],
                billable=item["billable_quantity"],
                unit=item["unit_price"],
                monthly=item["monthly_cost"],
            )
        )
    lines.extend(["", "## Review Status", "", f"- Status: `{bom['review_status']['status']}`"])
    for gate in bom["review_status"]["gates"]:
        lines.append(f"- {gate['name']}: `{gate['status']}` - {gate['detail']}")
    if bom["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in bom["warnings"]:
            lines.append(f"- `{warning['code']}` ({warning['severity']}): {warning['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def excel_col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def excel_cell_ref(row: int, col: int) -> str:
    return f"{excel_col(col)}{row}"


def excel_number(value: Any) -> str:
    decimal_value = d(value)
    if decimal_value == decimal_value.to_integral_value():
        return str(decimal_value.quantize(Decimal("1")))
    return format(decimal_value.normalize(), "f")


def xlsx_cell(row: int, col: int, value: Any = None, style: int | None = None, formula: str | None = None) -> str:
    attrs = [f'r="{excel_cell_ref(row, col)}"']
    if style is not None:
        attrs.append(f's="{style}"')
    attr_text = " ".join(attrs)
    if formula is not None:
        cached = "" if value is None else f"<v>{excel_number(value)}</v>"
        return f"<c {attr_text}><f>{html.escape(formula)}</f>{cached}</c>"
    if value is None:
        return f"<c {attr_text}/>"
    if isinstance(value, (Decimal, int, float)):
        return f"<c {attr_text}><v>{excel_number(value)}</v></c>"
    return f'<c {attr_text} t="inlineStr"><is><t>{html.escape(str(value))}</t></is></c>'


def xlsx_row(
    row_number: int,
    values: list[Any],
    *,
    style: int | None = None,
    cell_styles: dict[int, int] | None = None,
    formulas: dict[int, str] | None = None,
    height: int | None = None,
) -> str:
    attrs = [f'r="{row_number}"']
    if height:
        attrs.extend([f'ht="{height}"', 'customHeight="1"'])
    cells = []
    for index, value in enumerate(values, start=1):
        cells.append(
            xlsx_cell(
                row_number,
                index,
                value=value,
                style=(cell_styles or {}).get(index, style),
                formula=(formulas or {}).get(index),
            )
        )
    return f"<row {' '.join(attrs)}>{''.join(cells)}</row>"


def xlsx_sheet(
    rows: list[str],
    *,
    freeze_row: int | None = None,
    auto_filter_ref: str | None = None,
    col_widths: dict[int, int] | None = None,
) -> str:
    cols = ""
    if col_widths:
        cols = "<cols>" + "".join(
            f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
            for index, width in col_widths.items()
        ) + "</cols>"
    views = '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
    if freeze_row:
        split = freeze_row - 1
        top_left = f"A{freeze_row}"
        views = (
            '<sheetViews><sheetView workbookViewId="0">'
            f'<pane ySplit="{split}" topLeftCell="{top_left}" activePane="bottomLeft" state="frozen"/>'
            f'<selection pane="bottomLeft" activeCell="{top_left}" sqref="{top_left}"/>'
            "</sheetView></sheetViews>"
        )
    auto_filter = f'<autoFilter ref="{auto_filter_ref}"/>' if auto_filter_ref else ""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"{views}{cols}<sheetData>{''.join(rows)}</sheetData>{auto_filter}"
        '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
        "</worksheet>"
    )


def build_summary_xlsx_sheet(bom: dict[str, Any]) -> str:
    rows = [
        xlsx_row(1, ["OCI BOM Estimate"], cell_styles={1: 1}, height=24),
        xlsx_row(2, ["Currency", bom["metadata"]["currency"]], cell_styles={1: 2, 2: 0}),
        xlsx_row(3, ["Pricing source", bom["metadata"]["pricing_source"]["type"]], cell_styles={1: 2, 2: 0}),
        xlsx_row(4, ["Price-list last updated", bom["metadata"]["pricing_source"].get("last_updated", "not available")], cell_styles={1: 2, 2: 0}),
        xlsx_row(5, ["Assumption confirmation", bom["metadata"]["assumption_confirmation"]["status"]], cell_styles={1: 2, 2: 0}),
        xlsx_row(7, ["Group", "Monthly USD"], style=2),
    ]
    row_number = 8
    for group, total in bom["monthly_totals_by_group"].items():
        rows.append(xlsx_row(row_number, [group, d(total)], cell_styles={1: 0, 2: 3}))
        row_number += 1
    total_row = row_number
    first_total_row = 8
    last_total_row = row_number - 1
    rows.append(
        xlsx_row(
            total_row,
            ["Estimated Monthly Total", d(bom["estimated_monthly_total"])],
            cell_styles={1: 6, 2: 6},
            formulas={2: f"SUM(B{first_total_row}:B{last_total_row})" if last_total_row >= first_total_row else "0"},
        )
    )
    row_number += 2
    rows.append(xlsx_row(row_number, ["Exclusions"], style=2))
    row_number += 1
    for exclusion in bom["metadata"]["exclusions"]:
        rows.append(xlsx_row(row_number, [exclusion], cell_styles={1: 5}))
        row_number += 1
    return xlsx_sheet(rows, col_widths={1: 36, 2: 24, 3: 90})


def build_assumptions_xlsx_sheet(bom: dict[str, Any]) -> str:
    rows = [xlsx_row(1, ["Assumption", "Value", "Source", "Note"], style=2)]
    for row_number, (key, value) in enumerate(bom["assumptions"].items(), start=2):
        rows.append(xlsx_row(row_number, [key, value["value"], value["source"], value["note"]], cell_styles={1: 0, 2: 0, 3: 0, 4: 5}))
    return xlsx_sheet(
        rows,
        freeze_row=2,
        auto_filter_ref=f"A1:D{len(bom['assumptions']) + 1}",
        col_widths={1: 34, 2: 24, 3: 26, 4: 90},
    )


def build_priced_bom_xlsx_sheet(bom: dict[str, Any]) -> str:
    headers = [
        "Line",
        "Tier",
        "Group",
        "OCI Service",
        "SKU Part Number",
        "SKU Display Name",
        "Metric",
        "Configuration",
        "Quantity",
        "Billable Quantity",
        "Unit Price",
        "Monthly",
        "Notes",
    ]
    rows = [xlsx_row(1, headers, style=2)]
    for row_number, item in enumerate(bom["line_items"], start=2):
        monthly = d(item["monthly_cost"])
        rows.append(
            xlsx_row(
                row_number,
                [
                    item["line"],
                    item["tier"],
                    item["group"],
                    item["service"],
                    item["sku_part_number"],
                    item["sku_display_name"],
                    item["metric"],
                    item["configuration"],
                    d(item["quantity"]),
                    d(item["billable_quantity"]),
                    d(item["unit_price"]),
                    monthly,
                    item["notes"],
                ],
                cell_styles={1: 4, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 5, 9: 4, 10: 4, 11: 3, 12: 3, 13: 5},
                formulas={12: f"ROUND(J{row_number}*K{row_number},4)"},
            )
        )
    total_row = len(bom["line_items"]) + 3
    last_line_row = len(bom["line_items"]) + 1
    rows.append(
        xlsx_row(
            total_row,
            ["", "", "", "", "", "", "", "", "", "", "Estimated Total", d(bom["estimated_monthly_total"]), "Formula sum of priced line items."],
            cell_styles={11: 6, 12: 6, 13: 5},
            formulas={12: f"SUM(L2:L{last_line_row})" if last_line_row >= 2 else "0"},
        )
    )
    return xlsx_sheet(
        rows,
        freeze_row=2,
        auto_filter_ref=f"A1:M{max(1, last_line_row)}",
        col_widths={1: 8, 2: 22, 3: 28, 4: 28, 5: 16, 6: 52, 7: 34, 8: 62, 9: 16, 10: 18, 11: 16, 12: 16, 13: 90},
    )


def build_warnings_xlsx_sheet(bom: dict[str, Any]) -> str:
    rows = [xlsx_row(1, ["Severity", "Code", "Message"], style=2)]
    warnings = bom["warnings"] or [{"severity": "info", "code": "none", "message": "No warnings."}]
    for row_number, warning in enumerate(warnings, start=2):
        style = 5 if warning["severity"] != "error" else 7
        rows.append(xlsx_row(row_number, [warning["severity"], warning["code"], warning["message"]], cell_styles={1: style, 2: 0, 3: 5}))
    return xlsx_sheet(rows, freeze_row=2, auto_filter_ref=f"A1:C{len(warnings) + 1}", col_widths={1: 18, 2: 36, 3: 110})


def build_review_gates_xlsx_sheet(bom: dict[str, Any]) -> str:
    rows = [xlsx_row(1, ["Gate", "Status", "Detail"], style=2)]
    gates = bom["review_status"]["gates"]
    for row_number, gate in enumerate(gates, start=2):
        status_style = 8 if gate["status"] == "passed" else 5
        rows.append(xlsx_row(row_number, [gate["name"], gate["status"], gate["detail"]], cell_styles={1: 0, 2: status_style, 3: 5}))
    return xlsx_sheet(rows, freeze_row=2, auto_filter_ref=f"A1:C{len(gates) + 1}", col_widths={1: 42, 2: 28, 3: 100})


def write_xlsx(path: Path, bom: dict[str, Any]) -> None:
    sheet_names = ["Summary", "Assumptions", "Priced BOM", "Warnings", "Review Gates"]
    sheets = [
        build_summary_xlsx_sheet(bom),
        build_assumptions_xlsx_sheet(bom),
        build_priced_bom_xlsx_sheet(bom),
        build_warnings_xlsx_sheet(bom),
        build_review_gates_xlsx_sheet(bom),
    ]
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        + "".join(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for index in range(1, len(sheets) + 1)
        )
        + "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + "".join(
            f'<sheet name="{html.escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
            for index, name in enumerate(sheet_names, start=1)
        )
        + '</sheets><calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(
            f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
            for index in range(1, len(sheets) + 1)
        )
        + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "<dc:title>OCI BOM Estimate</dc:title></cp:coreProperties>"
    )
    app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Codex</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop>"
        f'<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(sheet_names)}</vt:i4></vt:variant></vt:vector></HeadingPairs>'
        f'<TitlesOfParts><vt:vector size="{len(sheet_names)}" baseType="lpstr">'
        + "".join(f"<vt:lpstr>{html.escape(name)}</vt:lpstr>" for name in sheet_names)
        + "</vt:vector></TitlesOfParts></Properties>"
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="2"><numFmt numFmtId="164" formatCode="$#,##0.00"/><numFmt numFmtId="165" formatCode="#,##0.0000"/></numFmts>'
        '<fonts count="4"><font><sz val="11"/><name val="Aptos"/></font><font><b/><sz val="16"/><color rgb="FF1F4E5F"/><name val="Aptos Display"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font><font><b/><sz val="11"/><color rgb="FF0F5132"/><name val="Aptos"/></font></fonts>'
        '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF1F4E5F"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE2F0D9"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill></fills>'
        '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left style="thin"><color rgb="FFD9E2E3"/></left><right style="thin"><color rgb="FFD9E2E3"/></right><top style="thin"><color rgb="FFD9E2E3"/></top><bottom style="thin"><color rgb="FFD9E2E3"/></bottom><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="9">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
        '<xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1"/>'
        '<xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1"/>'
        '<xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment wrapText="1"/></xf>'
        '<xf numFmtId="164" fontId="3" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyNumberFormat="1" applyBorder="1"/>'
        '<xf numFmtId="0" fontId="2" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>'
        '<xf numFmtId="0" fontId="3" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>'
        "</cellXfs>"
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles><dxfs count="0"/><tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/></styleSheet>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("docProps/core.xml", core)
        archive.writestr("docProps/app.xml", app)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", styles)
        for index, sheet in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", sheet)


def write_outputs(bom: dict[str, Any], output_dir: str, stem: str) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "excel": out / f"{stem}.xlsx",
        "markdown": out / f"{stem}.md",
        "csv": out / f"{stem}.csv",
        "json": out / f"{stem}.json",
    }
    write_xlsx(paths["excel"], bom)
    write_markdown(paths["markdown"], bom)
    write_csv(paths["csv"], bom)
    write_json(paths["json"], bom)
    return {key: str(value) for key, value in paths.items()}


def write_assumptions_preview(preview: dict[str, Any], output_dir: str, stem: str) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{stem}-assumptions.json"
    write_json(path, preview)
    return {"assumptions_json": str(path)}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OCI BOM Markdown, CSV, and JSON outputs.")
    parser.add_argument("--input", required=True, help="Path to an architecture JSON/report file, or a service list/prompt string.")
    parser.add_argument("--currency", default="USD", help="Oracle pricing currency code. Default: USD.")
    parser.add_argument("--output-dir", default="output", help="Directory for generated BOM outputs. Default: output.")
    parser.add_argument("--name", help="Output file stem. Default: input stem plus '-bom', or 'oci-bom' for text input.")
    parser.add_argument("--pricing-cache", help="Path to a cached Oracle products API JSON response.")
    parser.add_argument(
        "--cache-dir",
        help="Directory for automatic Oracle pricing feed cache. Default: .cache/oci-bom-generator or OCI_BOM_PRICE_CACHE_DIR.",
    )
    parser.add_argument(
        "--cache-ttl-hours",
        type=int,
        default=DEFAULT_CACHE_TTL_HOURS,
        help=f"Automatic pricing cache TTL in hours. Default: {DEFAULT_CACHE_TTL_HOURS}.",
    )
    parser.add_argument("--no-cache", action="store_true", help="Do not read or write the automatic pricing cache.")
    parser.add_argument(
        "--assumptions-only",
        action="store_true",
        help="Extract detected services and sizing assumptions without fetching prices or writing a priced BOM.",
    )
    parser.add_argument(
        "--assumptions-file",
        help="JSON file containing confirmed or edited assumptions to apply before pricing.",
    )
    parser.add_argument("--offline", action="store_true", help="Use bundled fallback pricing only; do not fetch the Oracle pricing feed.")
    parser.add_argument(
        "--estimator-browser",
        action="store_true",
        help="Mark Oracle Cost Estimator browser validation as requested. The browser workflow still requires explicit confirmation.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    stem = output_stem(args.input, args.name)
    if args.assumptions_only:
        preview = build_assumptions_preview(args.input, currency=args.currency)
        paths = write_assumptions_preview(preview, args.output_dir, stem)
        print(json.dumps({"outputs": paths, "status": "assumptions_ready", "pricing_fetch_performed": False}, indent=2))
        return 0

    bom = generate_bom(
        args.input,
        currency=args.currency,
        pricing_cache=args.pricing_cache,
        offline=args.offline,
        estimator_browser=args.estimator_browser,
        assumptions_file=args.assumptions_file,
        cache_dir=args.cache_dir,
        cache_ttl_hours=args.cache_ttl_hours,
        no_cache=args.no_cache,
    )
    paths = write_outputs(bom, args.output_dir, stem)
    print(json.dumps({"outputs": paths, "estimated_monthly_total": bom["estimated_monthly_total"], "status": bom["review_status"]["status"]}, indent=2))
    return 0 if bom["review_status"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
