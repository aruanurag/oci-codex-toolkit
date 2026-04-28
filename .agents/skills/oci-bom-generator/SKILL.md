---
name: oci-bom-generator
description: Generate OCI bill-of-materials and cost-estimator inputs from OCI architecture specs, diagram reports, service lists, or prompts. Use when Codex needs OCI pricing, BOM CSV/Markdown/JSON deliverables, Oracle Cost Estimator validation, or customer-facing OCI estimate assumptions.
---

# OCI BOM Generator

## Core Rules

- Prefer deterministic local BOM generation from Oracle's public Cost Estimator products API before using the browser UI.
- Treat generated costs as list-price estimates, not quotes. Always disclose exclusions: taxes, support, discounts, private pricing, data transfer, backup retention, and committed-use discounts unless explicitly modeled.
- Use architecture JSON/report artifacts as the best source when available. Treat raw `.drawio` and `.pptx` parsing as best-effort unless a source spec or report exists.
- Never silently invent sizing. Use documented defaults only when needed and record each one in the assumptions output.
- Run the assumption confirmation gate before fetching prices for any customer-facing BOM. Do not price defaulted sizing until the user confirms or edits the assumptions.
- Browser automation against Oracle Cost Estimator is optional and gated. Confirm before importing files, adding nontrivial customer architecture details, saving, exporting, or submitting anything on oracle.com.
- If pricing lookup fails, disclose whether the result used bundled fallback pricing and which SKUs were affected.
- Cache Oracle pricing feed responses for 48 hours by default in `.cache/oci-bom-generator/products-<currency>.json`. Use `--no-cache` only when a fresh live pull is explicitly required, `--pricing-cache` for a pinned feed, or `--offline` for bundled fallback pricing.

## Workflow

1. Identify the source type:
   - architecture JSON/report artifact
   - explicit OCI service list
   - freeform prompt
2. Extract assumptions without pricing:
   ```bash
   python3 .agents/skills/oci-bom-generator/scripts/generate_oci_bom.py --input output/single-region-oke-production-ready.json --currency USD --output-dir output --assumptions-only
   ```
3. Present the assumptions to the user before fetching prices:
   - service/component interpretation
   - region/currency and hours/month
   - instance counts, shapes, OCPU, memory, storage, bandwidth, request volume, and database sizing
   - unpriced or usage-dependent items such as VCN, subnets, route tables, NAT, egress, logging, and backups
4. Wait for the user to confirm or edit the assumptions. If they edit values, update the generated `*-assumptions.json` or create a small assumptions JSON with the corrected keys.
5. Generate the local BOM using the confirmed assumptions file. Excel is always produced as the primary deliverable:
   ```bash
   python3 .agents/skills/oci-bom-generator/scripts/generate_oci_bom.py --input output/single-region-oke-production-ready.json --currency USD --output-dir output --assumptions-file output/single-region-oke-production-ready-bom-assumptions.json
   ```
6. Review the generated JSON warnings and review gates before presenting totals.
7. If the user asks for Oracle Cost Estimator validation, read `references/oracle-cost-estimator.md` and perform the browser flow with explicit confirmation before transmitting data.
8. Validate the generated workbook with the sibling `$xlsx` skill's `inspect_xlsx.py` script before delivery.

## Output Contract

The default generator writes four files with the same stem:

- `*.xlsx`: primary customer-facing Excel BOM with summary, assumptions, priced lines, warnings, review gates, formulas, filters, and frozen headers
- `*.md`: readable summary, assumptions, warnings, and line items
- `*.csv`: spreadsheet-friendly flat BOM rows and totals
- `*.json`: source metadata, assumptions, detected services, line items, totals, warnings, and review gates

The pre-pricing assumption gate writes:

- `*-assumptions.json`: detected services, inferred/default assumptions, and confirmation instructions. This file is safe to produce before any price lookup.

## Pricing Cache

- Automatic cache: `.cache/oci-bom-generator/products-USD.json` by default.
- TTL: 48 hours by default via `--cache-ttl-hours 48`.
- Override cache directory with `--cache-dir` or `OCI_BOM_PRICE_CACHE_DIR`.
- Force a live pull and skip cache read/write with `--no-cache`.
- Use a pinned downloaded feed with `--pricing-cache path/to/products.json`; this bypasses the automatic cache.
- Use `--offline` to avoid network and use bundled fallback pricing for known USD SKUs.
- Always record `metadata.pricing_source.type` from the JSON output before presenting totals.

## Excel Validation

- Treat the `.xlsx` as the primary deliverable for every BOM.
- Validate with:
  ```bash
  python3 .agents/skills/xlsx/scripts/inspect_xlsx.py output/name.xlsx --output /tmp/name-xlsx-inspection.json
  ```
- Confirm the workbook has `Summary`, `Assumptions`, `Priced BOM`, `Warnings`, and `Review Gates`.
- Confirm formulas have cached values before delivery. If recalculation tools are unavailable, the generator writes cached values alongside formulas.

## Review Gates

Read `references/bom-review-gates.md` when checking quality. At minimum verify:

- source parsed and at least one priced line item exists
- every priced line has a SKU, quantity, unit price, and monthly total
- every default sizing assumption is explicit
- assumptions were confirmed by the user before pricing, or the output clearly warns that pricing used unconfirmed defaults
- zero-cost/free-tier assumptions are explicit
- unpriced detected services are disclosed
- CSV, Markdown, and JSON totals agree
- Oracle Cost Estimator variance is recorded when browser validation is requested

## Resources

- `scripts/generate_oci_bom.py`: main BOM generator CLI.
- `scripts/test_generate_oci_bom.py`: deterministic regression tests.
- `references/bom-review-gates.md`: manual and automated BOM review checklist.
- `references/oracle-cost-estimator.md`: gated browser validation workflow.
