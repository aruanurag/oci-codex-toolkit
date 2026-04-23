# OCI PowerPoint Style Guide

Use these rules for all generated OCI PowerPoint diagrams.

## Visual Baseline

- Use the bundled Oracle PowerPoint toolkit in `assets/powerpoint/oracle-oci-architecture-toolkit-v24.1.pptx`.
- Reuse Oracle’s native vector icons and grouping shapes instead of redrawing them from scratch.
- Reuse the closest Oracle sample/reference slide as a starting layout when the request clearly matches one.
- Keep the deck in 16:9 landscape format unless the user explicitly asks for portrait.
- Prefer Oracle’s built-in label styling inside copied icon groups when possible.

## Physical Diagram Defaults

- Default to physical diagrams only.
- Show `OCI Region`, `VCN`, and clearly labeled public and private subnets with CIDRs for networked workloads.
- Put public entry services in public subnets and application or data services in private subnets.
- Add more private subnets only when the architecture needs them.
- Show major gateways when they materially affect the topology.

## Gateways

- Put `Internet Gateway`, `NAT Gateway`, and `Service Gateway` on the VCN border.
- Center gateway icons on the border line, not on a corner.
- Do not draw decorative stub lines between a gateway and the VCN border.
- When authoring repeatable specs, prefer renderer-driven boundary placement instead of hand-tuning the x coordinate.

## Connectors

- Use orthogonal connectors only.
- Use one visible connector per semantic relationship.
- Avoid stitched connector chains for a single flow.
- Keep line weight visually consistent with Oracle’s connector samples.
- Keep labels on horizontal segments when possible.
- Keep labels off icons, borders, and arrowheads.
- Use transparent, no-fill connector labels and keep them single-line where practical.
- Do not let connectors overlap container borders or cut through unrelated icons.
- Treat any connector segment that rides along a container border as a blocker.

## Layout Quality

- Leave visible top and bottom margin around the main OCI Region or canvas so it does not crowd the slide header/footer area.
- Keep icons centered within the intended container.
- Keep icon and label spacing tight.
- Do not overcrowd subnets or tiers.
- Do not stretch icons out of proportion.
- Treat floating icons, detached arrowheads, and clipped child elements as blockers.
- Treat any overlap between unrelated connectors as a blocker when extra whitespace or a different lane can solve it.
- Prefer layouts that let the primary user/request flow stay straight or nearly straight before you start hand-tuning connector waypoints.

## Fallback Honesty

- Use a direct OCI PowerPoint icon first.
- If none exists, use the closest honest official fallback only when it is genuinely defensible.
- Otherwise use a clearly labeled placeholder shape.
- Always disclose placeholders and non-direct fallbacks in the mapping table.

## Review Loop

- Do not stop after the first render.
- Run the renderer quality check.
- Export a preview image of the slide through PowerPoint, not just a direct `.pptx` thumbnail path, because nested Oracle vector groups can render incompletely in simpler preview engines.
- Inspect the preview visually.
- Reroute and rerender until the linework, labels, and containment are clean.
- Require two consecutive clean quality passes before final delivery.
