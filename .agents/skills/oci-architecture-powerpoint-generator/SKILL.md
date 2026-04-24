---
name: oci-architecture-powerpoint-generator
description: Generate finalized OCI physical architecture `.pptx` diagrams that follow the bundled Oracle PowerPoint toolkit, default to physical slides, and iteratively review both architectural correctness and connector routing until the result looks clean, honest, and machine-generated.
---

# OCI Architecture PowerPoint Generator

## Overview

Use this skill when the user wants an OCI architecture as a finalized PowerPoint, not draw.io.

Keep the same standards we established in the draw.io skill:

- default to physical diagrams unless the user explicitly asks for a logical view
- start with a visible planning and ambiguity-analysis pass before drawing
- run a mandatory clarification gate before authoring any new diagram: ask a short set of targeted questions unless the user explicitly says not to ask questions or the current thread already answered them
- prefer the closest bundled Oracle PowerPoint reference layout before inventing a layout from scratch
- show VCNs, public and private subnets, CIDRs, and major gateways on networked physical diagrams
- default subnet scope to regional unless the user explicitly asks for AD-specific subnets or the workload genuinely needs AD-specific framing
- run an explicit architectural review before final delivery so public/private placement, HA or DR posture, ingress security, and tier isolation are correct instead of only visually tidy
- place gateways such as `Internet Gateway`, `NAT Gateway`, and `Service Gateway` directly on the VCN border
- place connector labels in transparent text boxes with no opaque mask over the line
- use one visible connector per semantic relationship
- do not accept stepped, stitched, diagonal, detached, or overlapping traffic arrows
- treat any connector elbow as a blocker unless the user explicitly accepts a bent route for that relationship
- treat shared or nearly collinear lanes between different semantic flows, such as publish, consume, and database-write paths, as overlap even when the renderer's quality checker passes
- keep icons centered, contained inside their parent boundaries, and scaled honestly
- treat missing direct icons, unofficial fallbacks, and placeholders as review findings that must be surfaced explicitly before sign-off
- keep sibling containers visibly separated and keep nested grouping boxes inset from their parent borders
- preserve symmetry when the architecture is staged, mirrored, or fanout-based by aligning repeated blocks and balancing whitespace before optimizing for the shortest connector
- shorten headings and reduce font size before accepting crowded or awkwardly wrapped labels
- use a direct OCI PowerPoint icon first, then a closest honest fallback, then a clearly labeled placeholder shape if no direct map exists

This skill is PowerPoint-native:

- it uses the bundled Oracle PowerPoint toolkit in `assets/powerpoint/oracle-oci-architecture-toolkit-v24.1.pptx`
- it reuses Oracle’s native vector groups and physical grouping boxes from that deck
- it renders a final `.pptx` plus a repeatable JSON spec

## Workflow

1. Read [references/style-guide.md](references/style-guide.md).
2. Read [references/output-format.md](references/output-format.md).
3. Read [references/diagram-spec.md](references/diagram-spec.md).
4. Start with a short planning pass and share it before authoring the slide spec:
   - inferred topology
   - network shape
   - HA or DR posture
   - likely Oracle reference baseline
   - uncertainties that would visibly change the slide
5. Use `python3 scripts/select_reference_architecture.py --query "user request" --bundle --top 5` to find the closest Oracle PowerPoint baseline slide from the uploaded OCI toolkit deck.
6. If the PowerPoint selector does not return a strong enough baseline, optionally consult the sibling draw.io references as a secondary architecture-pattern source.
7. After the planning pass, always ask 2 to 4 targeted clarification questions before authoring the slide spec unless the user explicitly says not to ask questions or the current thread already answered them. Focus on region count, HA or DR posture, ingress, subnet structure including regional vs AD-specific scope, icon choice, service meaning, and any symmetry or stage-alignment preference that would change the slide.
8. If answers are already present in the current thread, say that the clarification gate is satisfied and name the layout-affecting choices you are carrying forward before authoring.
9. Resolve icons with `python3 scripts/resolve_oci_powerpoint_icon.py --query "OKE"`.
10. If icon resolution returns `closest` or `placeholder`, or if you do not fully understand the requested component, pause before drafting the slide and confirm with the user when possible. Present one to three recommended icon choices or fallback shapes, explain the tradeoff briefly, and identify the most honest recommendation first.
11. If the user has already authorized recommended choices up front, you may proceed with the top recommendation but still disclose it in the mapping table and notes.
12. If the Oracle PowerPoint toolkit changes, rebuild the icon catalog with `python3 scripts/build_powerpoint_catalog.py` and the baseline-slide catalog with `python3 scripts/build_powerpoint_reference_catalog.py`.
13. Author the JSON slide spec only after the planning and clarification gate is complete.
14. Render with `python3 scripts/render_oci_powerpoint.py --spec ... --output ... --report-out ... --quality-out ... --fail-on-quality`.
15. Export a preview image of the rendered `.pptx` and inspect it visually before delivery. Prefer `python3 scripts/export_powerpoint_preview.py --input ... --image-out ...` because it uses PowerPoint for the render pass before generating the image.
16. Run a dedicated spacing and overlap review against the preview before sign-off:
   - verify every requested service resolved to an official OCI icon; treat `closest` and `placeholder` outcomes as blockers until they are disclosed and intentionally accepted
   - check spacing between external location groups, ingress services, and the first OCI boundary so `Internet`, `Clients`, `WAF`, and similar entry elements do not crowd each other
   - check spacing between icons and their labels, especially when Oracle icon groups have native labels that can drift into nearby lines or containers
   - check spacing between subnet labels, AD background lanes, cluster containers, and service icons so background structure does not visually consume foreground labels
   - treat any overlap between unrelated icons, labels, grouping boxes, connectors, arrowheads, or location boundaries as a blocker even if the renderer quality checker passes
   - treat top-level overlaps between separate icons or location groups as blockers even when the elements are not siblings in the JSON spec
   - treat clipped labels, near-touches that read like overlap, and obviously stretched icons caused by over-tight spacing as blockers
17. Run an architectural review against the request before sign-off:
   - only ingress services belong in public subnets for internet-facing patterns unless the user explicitly wants public compute
   - web, app, and data tiers should be isolated honestly when a 3-tier pattern is requested
   - regional subnets are the default OCI assumption when subnet scope is unspecified; do not duplicate one subnet per AD unless the user explicitly asked for AD-specific subnets or the architecture requires them
   - HA or DR claims must be explicit in the diagram through ADs, FDs, instance pools, standby regions, or similarly honest constructs
   - ingress protection, egress pattern, and management path should be present when they materially affect whether the design reads as production-ready
   - do not let labels such as `2x VM`, `HA`, or `DR` imply resilience that the drawing does not actually show
18. If the spacing and overlap review finds a gap, fix the spec and rerender before architectural sign-off.
19. If the architectural review finds a gap, fix the spec and rerender before visual polish sign-off.
20. Do at least three cleanup passes after the first render, even if the first quality pass is already clean.
21. Treat two consecutive clean quality reviews as the minimum bar, not the default stopping point.
22. Increase the number of review and rerender passes whenever the recent passes found icon-resolution issues, overlaps, avoidable elbows, package-integrity issues such as PowerPoint repair prompts, or any visually obvious regression.
23. After any material fix, require fresh clean passes again instead of counting earlier clean reviews toward sign-off.
24. Require a spacing-and-overlap review pass, an architectural-review pass, and at least two consecutive clean quality reviews before sharing the final deck, increasing to three or more consecutive clean passes when the slide was unstable in the prior review cycle.

## Clarification Priorities

Ask only the questions that are likely to improve the actual slide:

1. Single-region vs multi-region or DR posture.
2. Public vs private exposure and ingress path.
3. VCN and subnet structure, including whether separate app, data, cache, management, or observability subnets should appear and whether subnet scope should be regional or AD-specific.
4. Service-resolution questions such as `OKE` vs `Compute`, `ADB` vs `Base Database`, or whether a missing icon should use a closest official fallback or a placeholder.
5. Whether the user wants the slide to follow a specific Oracle reference pattern.
6. Layout-discipline preferences such as symmetry, one block vs multiple blocks, paired rows or columns, and whether repeated stages should align vertically or horizontally.

When the user gives only a short service list, treat that as ambiguous by default and ask follow-up questions unless they explicitly tell you not to.

Even when the request seems mostly clear, still ask at least one or two targeted questions that lock in the intended visual pattern unless the user explicitly waives questions.

If icon meaning is uncertain, ask that before drawing too. Do not treat icon ambiguity as a minor note when it could make the slide misleading.

## Mapping Rules

Apply this order strictly:

1. Use a direct official OCI PowerPoint icon when it exists in the bundled Oracle deck.
2. Use a trusted alias such as `OKE`, `ADB`, `ATP`, `ADW`, `DRG`, or `WAF`.
3. Use the closest honest official icon only when the skill explicitly documents that it is a deliberate fallback.
4. If no direct official icon exists and no honest official fallback is safe, use a clearly labeled placeholder shape.
5. If you are not confident that the requested component and the resolved icon mean the same thing, confirm with the user before rendering whenever possible and offer recommendations in descending honesty.

Never pretend a placeholder is an official OCI icon.
Do not let `closest` or `placeholder` resolutions silently pass the quality gate; they must appear in the review notes and be treated as blockers until intentionally accepted.

## Diagram Rules

- Use the bundled Oracle PowerPoint toolkit as the source of truth for icon style, grouping boxes, and palette.
- Preserve icon aspect ratio.
- Prefer Oracle’s native internal label treatment by editing the existing label inside the copied PowerPoint group instead of adding a detached text box below it.
- Keep labels visually snug to icons.
- Keep icons centered inside their parent subnet, tier, or container.
- Keep subnets and other grouping boxes visibly inset from their parent boundaries instead of letting borders touch.
- Default OCI subnet containers to regional scope when the request does not say otherwise. For multi-AD HA, let a regional subnet span the VCN or region and show AD placement with the official Oracle `Availability Domain` grouping boxes arranged as tall vertical background containers inside the VCN but outside the subnet boundaries, matching the bundled sample-slide treatment on toolkit slides 31 and 32, plus duplicated workloads, AD or FD labels, or database role markers instead of cloning the subnet once per AD.
- Keep sibling containers separated by a visible gap; treat overlapping app, queue, or data boxes as blockers.
- When a flow is expressed as repeated paired stages such as queue-to-consumer or publisher-to-fanout branches, prefer symmetrical rows or columns when that keeps the diagram honest and easier to scan.
- Keep gateways centered on the VCN boundary line, not floating inside the subnet and not stuck on a corner.
- Keep top-level canvases away from slide headers and footers so the OCI Region and location boxes have visible breathing room.
- Author gateway placement with `boundary_parent` and `boundary_side` when you want the renderer to mount an icon directly on a VCN edge.
- Treat duplicate route-table or security-list markers as blockers.
- Treat any child whose bounds spill outside its parent as a blocker.
- Prefer shorter container headings such as `Publisher`, `Processors`, or `Queue A` when the longer service name creates wrap noise.
- Do not let connectors run on top of container borders when a clean nearby lane is available.
- For OKE clusters, use the official `Container Engine for Kubernetes` icon as the cluster’s identifying icon instead of a generic compute placeholder.
- When OKE spans multiple ADs, represent it as a cluster-level container in the application subnet and place worker-node constructs inside that container with one worker grouping per AD.
- Keep worker-node and similar compute icons at an honest, unstretched aspect ratio; if the icon starts looking wider or flatter than the Oracle original, reduce the width before increasing the height.

## Architectural Review

- Treat architecture review as a required gate, not an optional afterthought.
- Check whether public subnets contain only components that genuinely need public exposure.
- For 3-tier web apps, default to regional `public ingress`, `private web`, `private app`, and `private data` subnets unless the user explicitly asks for AD-specific subnets or another pattern.
- If multi-AD HA is shown inside one region, prefer regional subnets that span the ADs and show resilience with Oracle-style vertical `Availability Domain` background grouping boxes plus per-AD placement of compute or database roles instead of implying each AD needs its own subnet.
- If the diagram implies high availability, show it explicitly with ADs, FDs, instance pools, multiple nodes, or equivalent honest OCI constructs.
- If the workload is internet-facing, review whether WAF, DNS or certificate flow, and egress controls should appear. Include them when they materially improve correctness or the user asked for production-style posture.
- Avoid claiming production readiness with a diagram that omits the security or resilience elements needed to support that claim.
- If a tier-to-tier relationship would normally require an internal load balancer, service discovery, or another mediation layer, either show it or keep the labels honest and simplified.

## Planning And Clarification Gate

- Before creating the actual diagram, always produce a short plan.
- After the plan, always ask 2 to 4 targeted clarification questions unless the user explicitly waives questions or the current thread already answered them.
- If there are no blocking questions, say that explicitly before moving into spec authoring.
- If a requested component is unfamiliar, underspecified, or maps only weakly to the icon catalog, do not silently improvise. Confirm with the user when possible and present recommended options.
- Put the recommended option first and explain why it is the most honest fit.

## Connectors

- Use orthogonal routing only.
- Keep connector lines Bark-colored and visually simple.
- Use one visible connector per semantic relationship.
- Prefer straight connectors first. If a route can be drawn straight, do not accept an elbowed alternative.
- Do not compose one logical flow out of several tiny visible connector fragments.
- If a connector truly must use elbows, keep them intentional and aligned and document why a straight route was not honest or feasible.
- Prefer removing manual waypoints when the renderer's default orthogonal route is cleaner.
- Arrange external clients, ingress tiers, application tiers, and data tiers so the dominant flows can stay straight or use the fewest possible bends.
- When opposite-direction flows coexist, differentiate them visually by semantic class. Default to dashed lines for async publish, fanout, event, or enqueue flows, and solid lines for consume, request, read, or synchronous service-to-service flows.
- Do not let different semantic connector families share the same visible lane for convenience. If publish, consume, or database-write paths look stacked or ambiguous, reroute them onto distinct lanes or a dedicated bus.
- Keep edge labels single-line where practical, transparent, and offset from the connector instead of masking it.
- If waypoints are supplied, keep the final route orthogonal and fully attached to the target boundary.
- Treat broken-looking arrowheads, almost-touching attachments, and label collisions as blockers.

## Deliverables

Default to producing:

1. Planning summary
2. Clarifying questions and answers, or a note that the answers were already provided earlier in the thread
3. Assumptions
4. Architecture summary
5. Spacing and overlap review findings and applied fixes
6. Architectural review findings and applied fixes
7. Final `.pptx`
8. JSON slide spec
9. Preview image for visual review
10. Icon mapping table
11. Placeholder notes

Use the repo-level `output/` directory for generated architecture files during testing unless the user asks for another location.

## Resources

- Read [references/style-guide.md](references/style-guide.md) for PowerPoint-specific layout and QA rules.
- Read [references/output-format.md](references/output-format.md) for the default package shape.
- Read [references/diagram-spec.md](references/diagram-spec.md) for the renderable JSON contract.
- Read [references/icon-catalog.md](references/icon-catalog.md) only when you need manual catalog browsing.
- Run `python3 scripts/build_powerpoint_catalog.py` after updating the Oracle PowerPoint toolkit.
- Run `python3 scripts/build_powerpoint_reference_catalog.py` after updating the Oracle PowerPoint toolkit or when you want to refresh the baseline-slide catalog.
- Run `python3 scripts/export_powerpoint_preview.py --input ... --image-out ...` when you need a faithful preview image for visual QA.
- Run `python3 scripts/resolve_oci_powerpoint_icon.py --query "service"` to resolve icons.
- Run `python3 scripts/select_reference_architecture.py --query "request text" --bundle --top 5` to find the closest bundled Oracle PowerPoint baseline before laying out a new slide.
- Run `python3 scripts/render_oci_powerpoint.py --spec ... --output ... --report-out ... --quality-out ... --fail-on-quality` to generate the final deck.
- Run `python3 scripts/test_powerpoint_icon_resolver.py` before trusting resolver changes.
- Run `python3 scripts/test_render_oci_powerpoint.py` before trusting renderer changes.
- Reuse the bundled example spec in `assets/examples/specs/` when you want a known-good starting point.
- Read [references/powerpoint-reference-catalog.md](references/powerpoint-reference-catalog.md) when you want a quick human-readable list of Oracle baseline slides.
