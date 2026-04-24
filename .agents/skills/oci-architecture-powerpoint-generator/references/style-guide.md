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
- Treat regional vs AD-specific subnet scope as a layout-affecting input for OCI networked workloads.
- Treat icon uncertainty as a real blocker when it could make the diagram misleading.
- When no direct icon exists or the component itself is not fully understood, confirm with the user when possible and present recommended icon or placeholder options with the most honest one first.
- Treat `closest` and `placeholder` icon resolutions as review findings that fail the clean-quality bar until they are explicitly disclosed and accepted.
- Treat symmetry and stage-alignment preferences as layout-affecting inputs when the topology is staged, mirrored, or fanout-based.

## Physical Diagram Defaults

- Default to physical diagrams only.
- Show `OCI Region`, `VCN`, and clearly labeled public and private subnets with CIDRs for networked workloads.
- Default OCI subnets to regional scope unless the user explicitly wants AD-specific subnets.
- Put public entry services in public subnets and application or data services in private subnets.
- Add more private subnets only when the architecture needs them.
- When a design is HA across multiple ADs inside one region, let the subnet span those ADs by default and show the official Oracle `Availability Domain` grouping boxes as tall vertical background containers inside the VCN but outside the subnet boundaries, following the bundled sample-slide treatment on toolkit slides 31 and 32, with duplicated workloads, AD labels, fault domains, or role markers instead of drawing one subnet per AD.
- Show major gateways when they materially affect the topology.
- Keep subnet grouping boxes inset from the VCN border on all sides so borders do not visually merge.

## Architectural Quality

- Review the architecture itself before you declare the slide done.
- Do not place compute tiers in a public subnet for a production-style web app unless the user explicitly asks for public compute.
- For 3-tier application patterns, prefer regional `public ingress`, `private web`, `private app`, and `private data` subnet placement unless the user explicitly asks for AD-specific subnets.
- If the workload is single-region and multi-AD, do not imply AD-scoped subnet boundaries unless the request explicitly called for AD-specific subnets. Still make the AD split visually explicit with aligned per-AD placement cues when HA is part of the claim.
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
- Prefer straight connectors first and treat avoidable elbows as blockers.
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
- When one regional subnet contains resources deployed across multiple ADs, keep the regional subnet running horizontally across the VCN while the official `Availability Domain` grouping boxes run vertically as background lanes outside the subnet boundaries, matching the Oracle sample-slide composition used on toolkit slides 31 and 32.
- Keep sibling containers visibly separated. Do not allow producer, processor, queue, cache, or database boxes to overlap.
- Keep mirrored or repeated stages visually balanced. When queue and consumer tiers repeat, align them symmetrically before hand-tuning connectors.
- Do not let publish, consume, and database-write paths ride the same lane just because they fit geometrically. Separate them into distinct lanes or a dedicated bus so the reader can parse them at a glance.
- Shorten labels and reduce font size before accepting awkward heading wraps.
- Do not overcrowd subnets or tiers.
- Do not stretch icons out of proportion.
- For multi-AD OKE layouts, represent `OKE` as a cluster-level container in the app subnet and place worker-node elements inside it with one worker grouping per AD.
- Keep worker-node icons especially close to the Oracle aspect ratio; if they look horizontally stretched, shrink width first rather than flattening the icon further.
- Treat floating icons, detached arrowheads, and clipped child elements as blockers.
- Treat any overlap between unrelated connectors as a blocker when extra whitespace or a different lane can solve it.
- Prefer layouts that let the primary user/request flow stay straight or nearly straight before you start hand-tuning connector waypoints.

## Spacing And Overlap Review

- Treat spacing and overlap review as a required visual gate, separate from architecture review and separate from the renderer quality check.
- Run it on the exported PowerPoint preview, not only on the JSON spec or renderer report.
- Check spacing between external location groups and ingress services so elements like `Internet`, `Clients`, and `WAF` do not crowd or visually merge.
- Check that every requested service resolved to an official OCI icon and that any fallback or placeholder is explicitly called out.
- Check spacing between icons and labels so native Oracle labels do not collide with connectors, neighboring icons, or grouping borders.
- Check spacing between subnet labels, AD background lanes, cluster containers, and service icons so background structure stays visually behind the foreground content.
- Treat any overlap between unrelated icons, labels, grouping boxes, connectors, arrowheads, or location boundaries as a blocker.
- Treat overlaps between separate top-level icons or location groups as blockers even when they are not siblings in the JSON structure.
- Treat near-touches that read as overlap at presentation scale as blockers even when the underlying geometry technically clears.
- If a spacing fix would require stretching an icon, move or resize the surrounding layout instead and preserve the icon’s aspect ratio.

## Fallback Honesty

- Use a direct OCI PowerPoint icon first.
- If none exists, use the closest honest official fallback only when it is genuinely defensible.
- Otherwise use a clearly labeled placeholder shape.
- Always disclose placeholders and non-direct fallbacks in the mapping table.
- Do not treat a slide as clean while any `closest` or `placeholder` icon resolution remains unresolved in the review notes.
- If the fallback choice required user confirmation, document which recommendation was used.

## Review Loop

- Do not stop after the first render.
- Perform an architecture review after the first coherent render.
- Run the renderer quality check.
- Export a preview image of the slide through PowerPoint, not just a direct `.pptx` thumbnail path, because nested Oracle vector groups can render incompletely in simpler preview engines.
- Inspect the preview visually.
- Perform a dedicated spacing and overlap review on that preview before declaring the slide clean.
- Fix architectural issues before treating the diagram as final, even if the linework is already clean.
- Reroute and rerender until the linework, spacing, labels, overlaps, and containment are clean.
- Treat two consecutive clean quality passes as the minimum bar, not the usual stopping point.
- Increase the review count after any recent icon-resolution issue, overlap, avoidable elbow, PowerPoint repair warning, or other material regression.
- After a material fix, restart the clean-pass count and require fresh clean reviews.
- Require a spacing-and-overlap review pass, an architecture-review pass, and at least two consecutive clean quality passes before final delivery, increasing to three or more consecutive clean passes when the slide was unstable in the previous review cycle.
