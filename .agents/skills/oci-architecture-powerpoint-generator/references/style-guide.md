# OCI PowerPoint Style Guide

Use these rules for all generated OCI PowerPoint diagrams.

## Visual Baseline

- Use the bundled Oracle PowerPoint toolkit in `assets/powerpoint/oracle-oci-architecture-toolkit-v24.1.pptx`.
- Reuse Oracle’s native vector icons and grouping shapes instead of redrawing them from scratch.
- Reuse the closest Oracle sample/reference slide as a starting layout when the request clearly matches one.
- Keep the deck in 16:9 landscape format unless the user explicitly asks for portrait.
- Prefer Oracle’s built-in label styling inside copied icon groups when possible.

## Planning And Clarification

- Before drafting the actual diagram, do a short plan pass.
- Always ask 2 to 4 targeted clarification questions before authoring unless the user explicitly waives questions or the current thread already answered them.
- If there are no blocking questions, say so explicitly before creating the slide spec.
- Treat icon uncertainty as a real blocker when it could make the diagram misleading.
- When no direct icon exists or the component itself is not fully understood, confirm with the user when possible and present recommended icon or placeholder options with the most honest one first.
- Treat symmetry and stage-alignment preferences as layout-affecting inputs when the topology is staged, mirrored, or fanout-based.

## Physical Diagram Defaults

- Default to physical diagrams only.
- Show `OCI Region`, `VCN`, and clearly labeled public and private subnets with CIDRs for networked workloads.
- Put public entry services in public subnets and application or data services in private subnets.
- Add more private subnets only when the architecture needs them.
- Show major gateways when they materially affect the topology.
- Keep subnet grouping boxes inset from the VCN border on all sides so borders do not visually merge.

## Architectural Quality

- Review the architecture itself before you declare the slide done.
- Do not place compute tiers in a public subnet for a production-style web app unless the user explicitly asks for public compute.
- For 3-tier application patterns, prefer `public ingress`, `private web`, `private app`, and `private data` placement.
- If HA or DR is requested or implied, represent it explicitly with OCI-native constructs such as multiple nodes, instance pools, ADs, fault domains, or standby regions.
- Do not let labels imply resilience or security posture that the diagram does not visibly support.
- For internet-facing applications, consider whether WAF, DNS or certificate flow, and egress controls are necessary to keep the design architecturally honest.
- If a simplifying omission is intentional, keep the labels and summary honest about that simplification.

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
- When flows go in opposite directions, give each semantic class a stable visual treatment. Default to dashed for async publish, fanout, event, or enqueue flows, and solid for consume, request, read, or synchronous flows.
- Treat shared or nearly collinear lanes between different semantic flows as overlaps even if the automated quality checker does not flag them.
- Keep labels on horizontal segments when possible.
- Keep labels off icons, borders, and arrowheads.
- Use transparent, no-fill connector labels and keep them single-line where practical.
- Do not let connectors overlap container borders or cut through unrelated icons.
- Treat any connector segment that rides along a container border as a blocker.

## Layout Quality

- Leave visible top and bottom margin around the main OCI Region or canvas so it does not crowd the slide header/footer area.
- Keep icons centered within the intended container.
- Keep icon and label spacing tight.
- Keep sibling containers visibly separated. Do not allow producer, processor, queue, cache, or database boxes to overlap.
- Keep mirrored or repeated stages visually balanced. When queue and consumer tiers repeat, align them symmetrically before hand-tuning connectors.
- Do not let publish, consume, and database-write paths ride the same lane just because they fit geometrically. Separate them into distinct lanes or a dedicated bus so the reader can parse them at a glance.
- Shorten labels and reduce font size before accepting awkward heading wraps.
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
- If the fallback choice required user confirmation, document which recommendation was used.

## Review Loop

- Do not stop after the first render.
- Perform an architecture review after the first coherent render.
- Run the renderer quality check.
- Export a preview image of the slide through PowerPoint, not just a direct `.pptx` thumbnail path, because nested Oracle vector groups can render incompletely in simpler preview engines.
- Inspect the preview visually.
- Fix architectural issues before treating the diagram as final, even if the linework is already clean.
- Reroute and rerender until the linework, labels, and containment are clean.
- Require an architecture-review pass and two consecutive clean quality passes before final delivery.
