# OCI BOM Review Gates

Use these gates before delivering a customer-facing BOM.

## Required Gates

- **Source coverage**: Confirm the input source was parsed and the detected services match the architecture or prompt.
- **Line-item integrity**: Every priced row must include service, SKU part number, display name, metric, quantity, unit price, and extended monthly cost.
- **Assumption visibility**: Record hours/month, instance counts, shapes, OCPU, memory, storage, request volume, bandwidth, and database sizing when used.
- **Assumption confirmation**: For customer-facing estimates, confirm or edit assumptions with the user before fetching prices. If pricing used unconfirmed defaults, disclose that as a review warning.
- **Free-tier visibility**: Zero-cost rows must explain the free tier or reason for no charge.
- **Unsupported services**: Disclose detected services that are not priced because they are free, usage-dependent, or require more sizing.
- **Totals consistency**: JSON total must equal the sum of line items; CSV and Markdown totals must match the JSON total.
- **Estimator variance**: If Oracle Cost Estimator browser validation is requested, record whether validation passed, was skipped, or produced a variance that needs review.

## Common Review Findings

- Architecture includes NAT, logging, monitoring, registry, bastion, vault, or data transfer but the BOM omits usage assumptions.
- OKE worker sizing is defaulted without saying so.
- Flexible compute memory is not billed separately from OCPU.
- Block Volume performance units are omitted for boot or attached volumes.
- WAF, Load Balancer, Monitoring, or Logging free tiers are represented as free without showing the usage threshold.
- Autonomous Database storage is modeled in TB in the narrative but GB in the SKU quantity without a clear conversion.
- Discounts, support, tax, private pricing, or committed-use discounts are implied but not modeled.

## Pass Criteria

A BOM is presentation-ready when required gates pass, unresolved items are limited to explicit assumptions or warnings, and the user can tell which lines are priced facts versus sizing choices.
