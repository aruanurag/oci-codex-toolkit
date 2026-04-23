#!/usr/bin/env python3
"""Resolve workload components to OCI PowerPoint library entries with explicit fallbacks."""

from __future__ import annotations

import argparse
import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from build_powerpoint_catalog import build_catalog, default_paths, normalize, tokenize

COMMON_ALIASES = {
    "adb": "Database - Oracle Autonomous Database",
    "autonomous db": "Database - Oracle Autonomous Database",
    "autonomous database": "Database - Oracle Autonomous Database",
    "adw": "Database - Oracle Autonomous Data Warehouse",
    "autonomous data warehouse": "Database - Oracle Autonomous Data Warehouse",
    "atp": "Database - Oracle Autonomous Transaction Processing ATP",
    "autonomous transaction processing": "Database - Oracle Autonomous Transaction Processing ATP",
    "apigw": "Developer Services - API Gateway",
    "api gateway": "Developer Services - API Gateway",
    "api service": "Developer Services - API Service",
    "ocir": "Developer Services - OCI Container Registry",
    "container registry": "Developer Services - OCI Container Registry",
    "oke": "Developer Services - OCI Container Engine for Kubernetes",
    "container engine for kubernetes": "Developer Services - OCI Container Engine for Kubernetes",
    "kubernetes": "Developer Services - OCI Container Engine for Kubernetes",
    "k8s": "Developer Services - OCI Container Engine for Kubernetes",
    "service mesh": "Developer Services - Service Mesh",
    "functions": "Compute - OCI Functions",
    "function": "Compute - OCI Functions",
    "vm": "Compute - Virtual Machine",
    "virtual machine": "Compute - Virtual Machine",
    "flex vm": "Compute - Flex VM",
    "burstable vm": "Compute - Burstable VM",
    "object storage": "Storage - OCI Object Storage",
    "bucket": "Storage - OCI Object Storage Buckets",
    "buckets": "Storage - OCI Object Storage Buckets",
    "block storage": "Storage - Block Storage",
    "file storage": "Storage - File Storage",
    "mount target": "Storage - File Storage Mount Target",
    "vcn": "Physical - Grouping - VCN",
    "lb": "Networking - Load Balancer",
    "load balancer": "Networking - Load Balancer",
    "flexible load balancer": "Networking - Flexible Load Balancer",
    "dns": "Networking - DNS",
    "cpe": "Networking - Customer Premises Equipment",
    "customer premises equipment": "Networking - Customer Premises Equipment",
    "drg": "Networking - DRG",
    "service gateway": "Networking - Service Gateway",
    "internet gateway": "Networking - Internet Gateway",
    "nat gateway": "Networking - NAT Gateway",
    "local peering gateway": "Networking - Local Peering Gateway",
    "route table": "Networking - Route Table",
    "route table and security list": "Networking - Route Table and Security List",
    "route table with security list": "Networking - Route Table and Security List",
    "postgres": "Database - OCI Database with PostgreSQL",
    "postgresql": "Database - OCI Database with PostgreSQL",
    "ords": "Database - Oracle REST Data Services",
    "database migration service": "Database - Oracle Database Migration Service",
    "db migration service": "Database - Oracle Database Migration Service",
    "oci migrate": "Database - OCI Migrate Autonomous Database",
    "heatwave": "Database - MySQL HeatWave",
    "lakehouse": "Database - Data Lakehouse",
    "data lake": "Database - Data Lake",
    "waf": "Identity and Security - WAF",
    "iam": "Identity and Security - IAM",
    "identity and access management": "Identity and Security - IAM",
    "vault": "Identity and Security - Vault",
    "key vault": "Identity and Security - Key Vault",
    "bastion": "Identity and Security - Bastion",
    "nsg": "Identity and Security - NSG",
    "security list": "Identity and Security - Security Lists",
    "security lists": "Identity and Security - Security Lists",
    "ddos": "Identity and Security - DDoS Protection",
    "cloud guard": "Identity and Security - Cloud Guard",
    "data safe": "Database - Data Safe",
    "opensearch": "Database - OpenSearch",
    "goldengate": "Database - GoldenGate",
    "genai": "Analytics and AI - OCI Generative AI",
    "generative ai": "Analytics and AI - OCI Generative AI",
    "language": "Analytics and AI - OCI Language",
    "speech": "Analytics and AI - OCI Speech",
    "vision": "Analytics and AI - OCI Vision",
    "document understanding": "Analytics and AI - Document Understanding",
    "forecasting": "Analytics and AI - Forecasting",
    "queue": "Observability and Management - OCI Queue",
    "oci queue": "Observability and Management - OCI Queue",
    "message queue": "Observability and Management - OCI Queue",
    "workflow": "Observability and Management - Workflow",
    "nosql": "Database - NoSQL Database",
    "redis": "Database - NoSQL Database",
    "cache": "Database - NoSQL Database",
    "streaming": "Analytics and AI - OCI Streaming",
}

PLACEHOLDER_SHAPES = {
    "app": "rounded-rectangle",
    "data": "cylinder",
    "network": "hexagon",
    "external": "cloud",
    "user": "ellipse",
}

PAGE_OVERRIDES = {
    "physical": {
        "region": "Physical - Grouping - OCI Region",
        "oci region": "Physical - Grouping - OCI Region",
        "availability domain": "Physical - Grouping - Availability Domain",
        "fault domain": "Physical - Grouping - Fault Domain",
        "vcn": "Physical - Grouping - VCN",
        "subnet": "Physical - Grouping - Subnet",
        "oracle services network": "Physical - Grouping - Oracle Services Network",
        "on premises": "Physical - Location - On-Premises",
        "on-premises": "Physical - Location - On-Premises",
        "internet": "Physical - Location - Internet",
        "3rd party cloud": "Physical - Location - 3rd Party Cloud",
        "third party cloud": "Physical - Location - 3rd Party Cloud",
        "metro area": "Physical - Grouping - Metro Area or Realm",
        "metro area or realm": "Physical - Grouping - Metro Area or Realm",
    }
}

CATEGORY_HINTS = {
    "compute": {"compute", "vm", "machine", "gpu", "instance", "function", "functions", "autoscaling"},
    "storage": {"storage", "object", "bucket", "file", "block", "backup", "restore", "volume"},
    "networking": {
        "network",
        "vcn",
        "subnet",
        "gateway",
        "load",
        "balancer",
        "drg",
        "dns",
        "cdn",
        "cpe",
        "peering",
        "route",
        "security",
        "igw",
        "nat",
        "osn",
        "internet",
    },
    "database": {
        "database",
        "db",
        "warehouse",
        "adw",
        "atp",
        "adb",
        "postgres",
        "postgresql",
        "nosql",
        "opensearch",
        "goldengate",
        "heatwave",
        "lakehouse",
        "redis",
        "cache",
    },
    "analytics and ai": {
        "analytics",
        "ai",
        "streaming",
        "vision",
        "speech",
        "language",
        "document",
        "forecasting",
        "generative",
    },
    "developer services": {"oke", "kubernetes", "container", "registry", "mesh", "api", "notifications", "devops"},
    "identity and security": {
        "iam",
        "security",
        "vault",
        "bastion",
        "nsg",
        "ddos",
        "certificate",
        "threat",
        "cloud",
        "guard",
        "firewall",
        "waf",
    },
    "observability and management": {"logging", "monitoring", "audit", "events", "queue", "workflow"},
}

EXTERNAL_TOKENS = {"external", "third", "3rd", "saas", "vendor", "partner", "non", "oci"}
ONPREM_TOKENS = {"onprem", "on", "prem", "datacenter", "legacy"}
USER_TOKENS = {"user", "users", "browser", "client", "operator", "developer", "admin"}


def load_catalog(catalog_path: Path | None = None) -> list[dict[str, Any]]:
    default_pptx, default_json, _ = default_paths()
    catalog_path = catalog_path or default_json

    if catalog_path.exists():
        return json.loads(catalog_path.read_text())

    return build_catalog(default_pptx)


def build_indexes(catalog: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    title_index: dict[str, dict[str, Any]] = {}
    variant_index: dict[str, dict[str, Any]] = {}

    for entry in catalog:
        title_index[entry["title"]] = entry
        variants = {
            entry["normalized_title"],
            entry["normalized_name"],
            *entry.get("acronyms", []),
        }
        for variant in variants:
            if variant and variant not in variant_index:
                variant_index[variant] = entry

    return title_index, variant_index


def infer_category_hint(query_tokens: set[str]) -> str | None:
    for category, hints in CATEGORY_HINTS.items():
        if query_tokens & hints:
            return category
    return None


def infer_placeholder_shape(
    query_tokens: set[str],
    category_hint: str | None = None,
    closest_entry: dict[str, Any] | None = None,
) -> str:
    normalized_category = category_hint
    if not normalized_category and closest_entry:
        normalized_category = normalize(str(closest_entry.get("category", "")))

    if query_tokens & USER_TOKENS:
        return PLACEHOLDER_SHAPES["user"]
    if normalized_category in {"networking", "identity and security"}:
        return PLACEHOLDER_SHAPES["network"]
    if normalized_category in {"database", "storage"}:
        return PLACEHOLDER_SHAPES["data"]
    if query_tokens & EXTERNAL_TOKENS:
        return PLACEHOLDER_SHAPES["external"]
    return PLACEHOLDER_SHAPES["app"]


def score_candidate(query_norm: str, query_tokens: set[str], entry: dict[str, Any], category_hint: str | None) -> float:
    title_tokens = set(entry.get("tokens", []))
    overlap = len(query_tokens & title_tokens) / max(len(query_tokens), 1)
    containment = 1.0 if query_norm in entry["normalized_title"] or entry["normalized_name"] in query_norm else 0.0
    sequence = SequenceMatcher(None, query_norm, entry["normalized_name"]).ratio()
    category_bonus = 0.12 if category_hint and normalize(entry["category"]) == category_hint else 0.0
    source_bonus = 0.05 if entry["source"].startswith("oracle-oci-architecture-toolkit") else 0.0
    return min(1.0, (0.42 * overlap) + (0.38 * sequence) + (0.10 * containment) + category_bonus + source_bonus)


def resolve_icon(query: str, page: str = "physical", catalog_path: Path | None = None) -> dict[str, Any]:
    catalog = load_catalog(catalog_path)
    title_index, variant_index = build_indexes(catalog)

    query_norm = normalize(query)
    query_tokens = set(tokenize(query))
    category_hint = infer_category_hint(query_tokens)

    page_override_title = PAGE_OVERRIDES.get(page, {}).get(query_norm)
    if page_override_title and page_override_title in title_index:
        entry = title_index[page_override_title]
        return {
            "query": query,
            "page": page,
            "resolution": "alias",
            "icon_title": entry["title"],
            "category": entry["category"],
            "source": entry["source"],
            "confidence": 1.0,
            "reason": f"Mapped the query to the page-specific Oracle PowerPoint grouping for {page} diagrams.",
        }

    alias_target = COMMON_ALIASES.get(query_norm)
    if alias_target and alias_target in title_index:
        entry = title_index[alias_target]
        return {
            "query": query,
            "page": page,
            "resolution": "alias",
            "icon_title": entry["title"],
            "category": entry["category"],
            "source": entry["source"],
            "confidence": 1.0,
            "reason": f"Mapped the query through a trusted alias: {query_norm}.",
        }

    direct_match = variant_index.get(query_norm)
    if direct_match:
        return {
            "query": query,
            "page": page,
            "resolution": "direct",
            "icon_title": direct_match["title"],
            "category": direct_match["category"],
            "source": direct_match["source"],
            "confidence": 1.0,
            "reason": "Matched the query directly to an official PowerPoint icon title, name, or acronym.",
        }

    scored = [(score_candidate(query_norm, query_tokens, entry, category_hint), entry) for entry in catalog]
    best_score, best_entry = max(scored, key=lambda item: item[0])

    if best_score >= 0.74:
        return {
            "query": query,
            "page": page,
            "resolution": "closest",
            "icon_title": best_entry["title"],
            "category": best_entry["category"],
            "source": best_entry["source"],
            "confidence": round(best_score, 3),
            "reason": "No direct icon match was found. This is the closest official PowerPoint icon with acceptable similarity.",
        }

    placeholder_shape = infer_placeholder_shape(
        query_tokens,
        category_hint=category_hint,
        closest_entry=best_entry if best_score >= 0.45 else None,
    )
    closest_official_icon = best_entry["title"] if best_score >= 0.45 else None
    return {
        "query": query,
        "page": page,
        "resolution": "placeholder",
        "icon_title": None,
        "category": None,
        "source": None,
        "confidence": round(best_score, 3),
        "placeholder_shape": placeholder_shape,
        "closest_official_icon": closest_official_icon,
        "reason": (
            "No direct PowerPoint OCI icon was found. Use the closest honest placeholder shape and document the gap."
        ),
    }


def search_catalog(term: str, catalog_path: Path | None = None) -> list[dict[str, Any]]:
    catalog = load_catalog(catalog_path)
    needle = normalize(term)
    matches = [
        entry
        for entry in catalog
        if needle in entry["normalized_title"] or needle in entry["normalized_name"]
    ]
    return sorted(matches, key=lambda entry: (entry["category"], entry["name"], entry["title"]))


def main() -> None:
    _, default_json, _ = default_paths()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", default=[], help="Component name to resolve. Repeat as needed.")
    parser.add_argument("--page", choices=["physical"], default="physical", help="Diagram page type.")
    parser.add_argument("--catalog", type=Path, default=default_json, help="Path to icon-catalog.json")
    parser.add_argument("--search", help="Browse the catalog instead of resolving a component.")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format.")
    args = parser.parse_args()

    if args.search:
        payload: Any = search_catalog(args.search, args.catalog)
    else:
        if not args.query:
            parser.error("Provide at least one --query or use --search.")
        payload = [resolve_icon(query, page=args.page, catalog_path=args.catalog) for query in args.query]

    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return

    if args.search:
        for entry in payload:
            print(f"{entry['title']} [{entry['source']}]")
        return

    for result in payload:
        print(f"Query: {result['query']}")
        print(f"Resolution: {result['resolution']}")
        if result["icon_title"]:
            print(f"Icon: {result['icon_title']}")
        if result.get("placeholder_shape"):
            print(f"Placeholder: {result['placeholder_shape']}")
        print(f"Reason: {result['reason']}")
        print()


if __name__ == "__main__":
    main()
