# OCI Architecture Output Format

Use this contract unless the user asks for a different deliverable.

Before authoring a new architecture from scratch, find the closest bundled reference with `python3 scripts/select_reference_architecture.py --query "..." --bundle --top 5` and use the primary reference's layout discipline as the baseline whenever it is a good fit.

If the selector recommends supporting references, use them only to borrow specific patterns such as DR posture, security flow, or networking motifs. Do not let a supporting reference replace the primary topology baseline unless it is clearly the better fit.

## Default Package

1. Planning Summary
2. Clarifying Questions and Answers
3. Assumptions
4. Architecture Summary
5. Final `.drawio` Diagram
6. JSON Diagram Spec
7. Icon Mapping Table
8. Placeholder and Gap Notes

## Planning Summary

Before generating the diagram, briefly summarize:

- inferred topology and deployment style
- expected network boundaries
- probable HA or DR model
- closest bundled reference architecture to use as the baseline
- the key gaps or ambiguities that might reduce diagram quality

If important gaps remain, ask the user the smallest useful set of clarification questions before generating the diagram. Favor questions whose answers change layout, topology, subnet structure, region usage, gateway placement, or service/icon selection.

When the request is primarily a list of OCI services rather than a full architecture description, ask follow-up questions by default before generating. At minimum, clarify ingress or exposure, single-region vs multi-region or HA posture, and any service-placement or icon-resolution choice that would visibly change the diagram.

Even when the request seems mostly clear, still ask 2 to 4 targeted clarification questions that lock in the intended visual pattern unless the user explicitly waives questions or the current thread already answered them.

## Clarifying Questions and Answers

Before authoring the diagram:

- always ask 2 to 4 targeted questions that lock in topology, ingress, HA or DR posture, subnet framing, service meaning, icon choice, or symmetry and stage-alignment intent
- clarify whether OCI subnets should be treated as regional or AD-specific when that choice would change the diagram
- keep questions focused on what would materially change the diagram
- if icon meaning is uncertain or a requested component maps only weakly to the catalog, ask for confirmation and present the most honest recommendation first

If the current thread already answered those questions, say that the clarification gate is satisfied and summarize the answers you are using.

## Assumptions

Keep this short. Include only items that materially affect the design, such as but not limited to:

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
- include VCN and public/private subnet structure with CIDR labels on physical pages for networked workloads, defaulting OCI subnets to regional scope unless the user explicitly asks for AD-specific subnets
- when HA spans multiple ADs inside one region, keep the Oracle-style framing explicit: `Availability Domain` grouping shapes should form vertical columns inside the VCN, and the regional subnets should span horizontally across them
- keep public resources visually inside public subnets and private resources inside private subnets
- when gateways such as `IGW`, `NAT`, or `SGW` are shown, attach them to the VCN edge by default unless the user explicitly requests a subnet-edge style
- enlarge the page or reroute edges before accepting overlapping or crowded connector paths
- render with the renderer's quality gate enabled and do not accept output while it reports issues
- pick the closest bundled reference architecture first and preserve its spacing, icon scale, and routing lanes when it is a good fit
- when a request mixes patterns, keep one primary reference and only borrow targeted details from supporting references
- perform at least three cleanup passes plus one confirmatory pass after the first clean review
- export the physical page to PNG and perform one final visual QA pass before finalizing
- treat overlapping lines, broken-looking traffic arrows, disconnected-looking attachments, stretched icons, and crowded labels as blockers, not polish items
- note the output path clearly
- ask targeted clarification questions first when unresolved ambiguity would materially change the resulting diagram

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
- `closest-official-fallback`
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
- For multi-AD HA, prefer official `Availability Domain` grouping shapes over improvised darker boxes, and preserve the regional-subnet-as-horizontal-band framing.
- Let the renderer normalize icon sizes when the spec omits `w` and `h`. Override icon sizes only deliberately.
- Use more whitespace, extra tiers, explicit anchors, and waypointed connectors instead of allowing overlapping lines or crowded clusters.
- Keep repeated queues, consumers, or mirrored stages symmetrically aligned when that improves scanability without misleading the architecture.
- For physical diagrams, prefer one clean orthogonal connector for cross-container traffic when it can stay visually attached and readable. Use hidden `*-anchor` shapes on subnet or VCN borders only when the direct connector would otherwise create broken-looking, crowded, or diagonal routing.
- Export the rendered page and visually inspect it. If a connector appears detached, partially attached, stacked on another route, broken by labels, forced through labels or boundaries, or shaped by a diagonal segment, reroute and rerender.
- Treat connectors that only almost reach a subnet wall, VCN wall, or workload icon as defects. The line should visibly terminate on the intended boundary or target.
- Prioritize traffic-flow arrows during visual QA and assign dedicated routing lanes when they would otherwise overlap.
- Require one more confirmatory render and clean quality review after the first clean render before delivering the diagram.
- Preserve the exact official icon name in your mapping notes, especially for toolkit-only additions.
- Keep the JSON spec beside the final diagram when repeatability matters.
