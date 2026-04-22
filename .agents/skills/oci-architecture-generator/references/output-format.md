# OCI Architecture Output Format

Use this contract unless the user asks for a different deliverable.

Before authoring a new architecture from scratch, find the closest bundled reference with `python3 scripts/select_reference_architecture.py --query "..." --bundle --top 5` and use the primary reference's layout discipline as the baseline whenever it is a good fit.

If the selector recommends supporting references, use them only to borrow specific patterns such as DR posture, security flow, or networking motifs. Do not let a supporting reference replace the primary topology baseline unless it is clearly the better fit.

## Default Package

1. Assumptions
2. Architecture Summary
3. Final `.drawio` Diagram
4. JSON Diagram Spec
5. Icon Mapping Table
6. Placeholder and Gap Notes

## Assumptions

Keep this short. Include only items that materially affect the design, such as:

- regions or multi-region posture
- HA or DR targets
- security or compliance constraints
- user traffic pattern
- integration boundaries

## Architecture Summary

Summarize the workload in plain language:

- what is being deployed
- which OCI services carry the design
- why the topology was chosen

## Final `.drawio` Diagram

Default to delivering a finished `.drawio` file, not just prose.

Unless the user says otherwise:

- include a physical page by default
- include a logical page only when the user explicitly requests one
- include VCN and public/private subnet structure with CIDR labels on physical pages for networked workloads
- keep public resources visually inside public subnets and private resources inside private subnets
- enlarge the page or reroute edges before accepting overlapping or crowded connector paths
- render with the renderer's quality gate enabled and do not accept output while it reports issues
- pick the closest bundled reference architecture first and preserve its spacing, icon scale, and routing lanes when it is a good fit
- when a request mixes patterns, keep one primary reference and only borrow targeted details from supporting references
- perform at least three cleanup passes plus one confirmatory pass after the first clean review
- export the physical page to PNG and perform one final visual QA pass before finalizing
- treat overlapping lines, broken-looking traffic arrows, disconnected-looking attachments, stretched icons, and crowded labels as blockers, not polish items
- note the output path clearly

## JSON Diagram Spec

Include this when the user wants the renderable source, when the diagram may be iterated later, or when repeatability matters.

Use [diagram-spec.md](diagram-spec.md) for the JSON contract.

For each page, define:

- page name and page type
- canvas size
- ordered elements
- edges and connector labels
- network boundaries such as VCNs and public/private subnets when the page is physical

Default to physical page specs only. Add logical page specs only when the user explicitly requests a logical view.

## Icon Mapping Table

Use this table for every architecture package:

| Requested Component | Resolved Icon | Resolution Type | Notes |
| --- | --- | --- | --- |

Use these resolution types:

- `direct`
- `alias`
- `closest`
- `generic`
- `placeholder`

## Placeholder and Gap Notes

List every placeholder explicitly.

Include:

- the requested component
- the placeholder shape
- why no direct official icon was used
- the closest official icon considered, if one existed but would have been misleading
- why the chosen shape is the closest similar fallback for that workload role

## If You Need to Create or Update `.drawio`

- Prefer rendering with `python3 scripts/render_oci_drawio.py --quality-out ... --fail-on-quality`.
- Default to a physical page only. Add a logical page only on explicit request.
- Keep labels concise and service-specific.
- Keep physical examples network-complete with VCNs and labeled subnets when the workload is deployed in a VCN.
- Let the renderer normalize icon sizes when the spec omits `w` and `h`. Override icon sizes only deliberately.
- Use more whitespace, extra tiers, explicit anchors, and waypointed connectors instead of allowing overlapping lines or crowded clusters.
- For physical diagrams, route cross-container traffic boundary-first: use hidden `*-anchor` shapes on subnet or VCN borders, keep intermediate segments arrowless with `endArrow=none;`, and reserve the visible arrowhead for the final segment into the destination workload.
- Export the rendered page and visually inspect it. If a connector appears detached, partially attached, stacked on another route, broken by labels, forced through labels or boundaries, or shaped by a diagonal segment, reroute and rerender.
- Treat connectors that only almost reach a subnet wall, VCN wall, or workload icon as defects. The line should visibly terminate on the intended boundary or target.
- Prioritize traffic-flow arrows during visual QA and assign dedicated routing lanes when they would otherwise overlap.
- Require one more confirmatory render and clean quality review after the first clean render before delivering the diagram.
- Preserve the exact official icon name in your mapping notes, especially for toolkit-only additions.
- Keep the JSON spec beside the final diagram when repeatability matters.
