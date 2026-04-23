---
name: oci-architecture-powerpoint-generator
description: Generate finalized OCI physical architecture `.pptx` diagrams that follow the bundled Oracle PowerPoint toolkit, default to physical slides, and iteratively review connector routing until lines, arrows, labels, and container alignment look clean and machine-generated.
---

# OCI Architecture PowerPoint Generator

## Overview

Use this skill when the user wants an OCI architecture as a finalized PowerPoint, not draw.io.

Keep the same standards we established in the draw.io skill:

- default to physical diagrams unless the user explicitly asks for a logical view
- start with a short planning and ambiguity-analysis pass before drawing
- prefer the closest bundled Oracle PowerPoint reference layout before inventing a layout from scratch
- show VCNs, public and private subnets, CIDRs, and major gateways on networked physical diagrams
- place gateways such as `Internet Gateway`, `NAT Gateway`, and `Service Gateway` directly on the VCN border
- place connector labels in transparent text boxes with no opaque mask over the line
- use one visible connector per semantic relationship
- do not accept stepped, stitched, diagonal, detached, or overlapping traffic arrows
- keep icons centered, contained inside their parent boundaries, and scaled honestly
- use a direct OCI PowerPoint icon first, then a closest honest fallback, then a clearly labeled placeholder shape if no direct map exists

This skill is PowerPoint-native:

- it uses the bundled Oracle PowerPoint toolkit in `assets/powerpoint/oracle-oci-architecture-toolkit-v24.1.pptx`
- it reuses Oracle’s native vector groups and physical grouping boxes from that deck
- it renders a final `.pptx` plus a repeatable JSON spec

## Workflow

1. Read [references/style-guide.md](references/style-guide.md).
2. Read [references/output-format.md](references/output-format.md).
3. Read [references/diagram-spec.md](references/diagram-spec.md).
4. Start with a short planning pass:
   - inferred topology
   - network shape
   - HA or DR posture
   - likely Oracle reference baseline
   - uncertainties that would visibly change the slide
5. Use `python3 scripts/select_reference_architecture.py --query "user request" --bundle --top 5` to find the closest Oracle PowerPoint baseline slide from the uploaded OCI toolkit deck.
6. If the PowerPoint selector does not return a strong enough baseline, optionally consult the sibling draw.io references as a secondary architecture-pattern source.
7. If the request is materially ambiguous, ask the smallest useful set of clarification questions before authoring the slide spec. Focus on region count, HA or DR posture, ingress, subnet structure, and icon or service choice.
8. Resolve icons with `python3 scripts/resolve_oci_powerpoint_icon.py --query "OKE"`.
9. If the Oracle PowerPoint toolkit changes, rebuild the icon catalog with `python3 scripts/build_powerpoint_catalog.py` and the baseline-slide catalog with `python3 scripts/build_powerpoint_reference_catalog.py`.
10. Author the JSON slide spec.
11. Render with `python3 scripts/render_oci_powerpoint.py --spec ... --output ... --report-out ... --quality-out ... --fail-on-quality`.
12. Export a preview image of the rendered `.pptx` and inspect it visually before delivery. Prefer `python3 scripts/export_powerpoint_preview.py --input ... --image-out ...` because it uses PowerPoint for the render pass before generating the image.
13. Do at least three cleanup passes after the first render, even if the first quality pass is already clean.
14. Require two consecutive clean quality reviews before sharing the final deck.

## Clarification Priorities

Ask only the questions that are likely to improve the actual slide:

1. Single-region vs multi-region or DR posture.
2. Public vs private exposure and ingress path.
3. VCN and subnet structure, including whether separate app, data, cache, management, or observability subnets should appear.
4. Service-resolution questions such as `OKE` vs `Compute`, `ADB` vs `Base Database`, or whether a missing icon should use a closest official fallback or a placeholder.
5. Whether the user wants the slide to follow a specific Oracle reference pattern.

When the user gives only a short service list, treat that as ambiguous by default and ask follow-up questions unless they explicitly tell you not to.

## Mapping Rules

Apply this order strictly:

1. Use a direct official OCI PowerPoint icon when it exists in the bundled Oracle deck.
2. Use a trusted alias such as `OKE`, `ADB`, `ATP`, `ADW`, `DRG`, or `WAF`.
3. Use the closest honest official icon only when the skill explicitly documents that it is a deliberate fallback.
4. If no direct official icon exists and no honest official fallback is safe, use a clearly labeled placeholder shape.

Never pretend a placeholder is an official OCI icon.

## Diagram Rules

- Use the bundled Oracle PowerPoint toolkit as the source of truth for icon style, grouping boxes, and palette.
- Preserve icon aspect ratio.
- Prefer Oracle’s native internal label treatment by editing the existing label inside the copied PowerPoint group instead of adding a detached text box below it.
- Keep labels visually snug to icons.
- Keep icons centered inside their parent subnet, tier, or container.
- Keep gateways centered on the VCN boundary line, not floating inside the subnet and not stuck on a corner.
- Keep top-level canvases away from slide headers and footers so the OCI Region and location boxes have visible breathing room.
- Author gateway placement with `boundary_parent` and `boundary_side` when you want the renderer to mount an icon directly on a VCN edge.
- Treat duplicate route-table or security-list markers as blockers.
- Treat any child whose bounds spill outside its parent as a blocker.
- Do not let connectors run on top of container borders when a clean nearby lane is available.
- For OKE clusters, use the official `Container Engine for Kubernetes` icon as the cluster’s identifying icon instead of a generic compute placeholder.

## Connectors

- Use orthogonal routing only.
- Keep connector lines Bark-colored and visually simple.
- Use one visible connector per semantic relationship.
- Do not compose one logical flow out of several tiny visible connector fragments.
- If a connector needs elbows, keep them intentional and aligned.
- Prefer removing manual waypoints when the renderer's default orthogonal route is cleaner.
- Arrange external clients, ingress tiers, application tiers, and data tiers so the dominant flows can stay straight or use the fewest possible bends.
- Keep edge labels single-line where practical, transparent, and offset from the connector instead of masking it.
- If waypoints are supplied, keep the final route orthogonal and fully attached to the target boundary.
- Treat broken-looking arrowheads, almost-touching attachments, and label collisions as blockers.

## Deliverables

Default to producing:

1. Planning summary
2. Assumptions
3. Architecture summary
4. Final `.pptx`
5. JSON slide spec
6. Preview image for visual review
7. Icon mapping table
8. Placeholder notes

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
