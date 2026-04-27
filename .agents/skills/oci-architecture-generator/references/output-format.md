# OCI Architecture Output Format

Use this contract unless the user asks for a different deliverable.

Before authoring a new architecture from scratch, find the closest bundled reference with `python3 scripts/select_reference_architecture.py --query "..." --bundle --top 5` and use the primary reference's layout discipline as the baseline whenever it is a good fit.

If the selector recommends supporting references, use them only to borrow specific patterns such as DR posture, security flow, or networking motifs. Do not let a supporting reference replace the primary topology baseline unless it is clearly the better fit.

When the request includes a specific Oracle solution link or another explicit reference, switch into reference replication mode. Read `references/oracle-solution-patterns.md`, extract a structured `Reference Summary`, synthesize a `Recreation Prompt`, and report a `Reference Alignment Review` with a `0-100` similarity score, the key differences, and the next meaningful improvements after each material render.

## Default Package

1. Planning Summary
2. Clarifying Questions and Answers
3. Assumptions
4. Architecture Summary
5. Spacing and Overlap Review and Applied Fixes
6. Architectural Review and Applied Fixes
7. Final `.drawio` Diagram
8. JSON Diagram Spec
9. Icon Mapping Table
10. Placeholder and Gap Notes

## Reference Replication Mode Additions

When the request is tied to a specific Oracle reference, add these sections to the package:

1. Reference Summary
2. Recreation Prompt
3. Reference Alignment Review

The `Reference Alignment Review` should include:

- `Similarity Score` from `0` to `100`
- missing or extra components
- structural or layout differences
- flow mismatches
- icon, grouping, or subnet-scope mismatches
- the next meaningful fixes to apply

Stop iterating when similarity reaches `>= 95`, when no meaningful improvement remains, or after `10` iterations.

## Planning Summary

Before generating the diagram, briefly summarize:

- inferred topology and deployment style
- expected network boundaries
- probable HA or DR model
- closest bundled reference architecture to use as the baseline
- the key gaps or ambiguities that might reduce diagram quality

If important gaps remain, ask the user the smallest useful set of clarification questions before generating the diagram. Build that question set from the planning pass instead of asking a fixed schema-driven script. Favor questions whose answers change layout, topology, HA or DR posture, database choice, subnet structure, region usage, gateway placement, or service/icon selection.

When the request is primarily a list of OCI services rather than a full architecture description, ask follow-up questions by default before generating. At minimum, clarify ingress or exposure, single-region vs multi-region or HA posture, database meaning, and any service-placement or icon-resolution choice that would visibly change the diagram.

Even when the request seems mostly clear, still ask a few targeted clarification questions when they lock in the intended visual pattern unless the user explicitly waives questions or the current thread already answered them. One good unresolved question is better than four redundant ones.

## Clarifying Questions and Answers

Before authoring the diagram:

- ask the smallest useful set of targeted questions, usually 1 to 4, based on the planning gaps that remain around topology, ingress, HA or DR posture, subnet framing, service meaning, icon choice, or symmetry and stage-alignment intent
- clarify whether OCI subnets should be treated as regional or AD-specific when that choice would change the diagram
- keep questions focused on what would materially change the diagram
- if icon meaning is uncertain or a requested component maps only weakly to the catalog, ask for confirmation, provide recommended options, and present the most honest recommendation first

If the current thread already answered those questions, say that the clarification gate is satisfied and summarize the answers you are using.
When a renderable JSON spec is part of the package, preserve the same questions, recommended options, and selected answers in the top-level `clarification_gate`. The renderer now refuses to render when that object is missing or incomplete.
Treat the required `clarification_gate` topics as decision-recording buckets, not as a mandatory verbatim question list. If the planning pass already resolves a topic, record it from `thread_context`, `recommendation_accepted`, `assumed`, or `not_applicable` instead of asking a redundant question.

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

## Spacing And Overlap Review And Applied Fixes

Before final delivery, review whether the diagram has enough breathing room and whether any visual collisions remain after the render pass.

Check:

- whether every requested service resolved to an official OCI icon and whether any `closest` or `placeholder` fallback remains unresolved
- whether external location groups, clients, WAF, and first-hop OCI ingress services have visible separation
- whether icons and labels have enough spacing to avoid crowding, clipping, or misleading associations
- whether subnet labels still read cleanly when AD background lanes, cluster containers, or other large grouping boxes sit behind them
- whether public ingress visually traverses the Internet Gateway before entering the VCN when an Internet Gateway is shown
- whether gateway icons are mounted on the VCN boundary instead of floating decoratively
- whether AD grouping lanes avoid swallowing the private data tier or implying a regional database is single-AD scoped
- whether support, security, observability, or operations panels overlap the VCN, subnet, or AD boundaries
- whether native OCI labels are hidden when a custom side label repeats the same service name
- whether any unrelated icons, labels, grouping boxes, connectors, arrowheads, or boundaries overlap or nearly touch in a way that reads as overlap
- whether any separate top-level icons or location groups overlap even if they are not siblings in the spec
- whether any icon was stretched to solve spacing instead of moving the surrounding layout

Run `python3 scripts/review_visual_preview.py --preview ... --report ... --spec ... --output ...visual-review.json --fail-on-issues` as the exported-preview gate. If the gate or the manual review finds an issue, update the diagram spec, rerender, re-export, and rerun the gate before final delivery.

## Architectural Review and Applied Fixes

Before final delivery, review whether the diagram is architecturally honest, not just visually clean.

Check:

- whether only ingress components are public for internet-facing designs
- whether web, app, and data tiers are isolated correctly for a 3-tier pattern
- whether regional subnets were used by default for OCI workloads unless the user explicitly asked for AD-specific subnets
- whether HA or DR claims are explicit in the drawing rather than implied only by labels
- whether ingress security, egress, and management omissions materially weaken the design
- whether any simplifying assumptions should be disclosed

If the review finds an issue, update the diagram spec and rerender before final delivery.

## Final `.drawio` Diagram

Default to delivering a finished `.drawio` file, not just prose.

Unless the user says otherwise:

- include a physical page by default
- include a logical page only when the user explicitly requests one
- include VCN and public/private subnet structure with CIDR labels on physical pages for networked workloads, defaulting OCI subnets to regional scope unless the user explicitly asks for AD-specific subnets
- when HA spans multiple ADs inside one region, keep the Oracle-style framing explicit: `Availability Domain` grouping shapes should form tall vertical background containers inside the VCN but outside the subnet boundaries, and the regional subnets should span horizontally across them
- keep public resources visually inside public subnets and private resources inside private subnets
- when OKE spans multiple ADs, represent it as a cluster-level container in the application subnet and place worker-node groups inside it with one grouping per AD
- when gateways such as `IGW`, `NAT`, or `SGW` are shown, attach them to the VCN edge by default unless the user explicitly requests a subnet-edge style
- enlarge the page or reroute edges before accepting overlapping or crowded connector paths
- render with the renderer's quality gate enabled and do not accept output while it reports issues
- run the exported-preview visual gate with `--fail-on-issues` and do not accept output while it reports issues
- pick the closest bundled reference architecture first and preserve its spacing, icon scale, and routing lanes when it is a good fit
- when a request mixes patterns, keep one primary reference and only borrow targeted details from supporting references
- run a dedicated spacing and overlap review before sign-off
- run an architectural review before sign-off
- perform at least three cleanup passes plus one confirmatory pass after the first clean review
- export the physical page to PNG and perform one final visual QA pass before finalizing
- treat overlapping lines, broken-looking traffic arrows, disconnected-looking attachments, avoidable elbows, stretched icons, and crowded labels as blockers, not polish items
- note the output path clearly
- ask targeted clarification questions first when unresolved ambiguity would materially change the resulting diagram

## JSON Diagram Spec

Include this when the user wants the renderable source, when the diagram may be iterated later, or when repeatability matters.

Use [diagram-spec.md](diagram-spec.md) for the JSON contract.

Include the top-level `clarification_gate` object in that spec so the recorded follow-up questions, recommended options, and selected answers are preserved with the renderable artifact.

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
- For multi-AD HA, prefer official `Availability Domain` grouping shapes over improvised darker boxes, and preserve the regional-subnet-as-horizontal-band framing with the AD groupings rendered as tall vertical background containers inside the VCN but outside the subnet boundaries.
- Let the renderer normalize icon sizes when the spec omits `w` and `h`. Override icon sizes only deliberately.
- Use more whitespace, extra tiers, explicit anchors, and waypointed connectors instead of allowing overlapping lines or crowded clusters.
- Keep repeated queues, consumers, or mirrored stages symmetrically aligned when that improves scanability without misleading the architecture.
- When OKE spans multiple ADs, represent it as one cluster container inside the application subnet and use one worker grouping per AD rather than stretching one worker icon across the whole cluster.
- For physical diagrams, prefer one clean orthogonal connector for cross-container traffic when it can stay visually attached and readable. Use hidden `*-anchor` shapes on subnet or VCN borders only when the direct connector would otherwise create broken-looking, crowded, or diagonal routing.
- Prefer straight connectors first. If a route can be drawn straight, do not accept an elbowed alternative.
- If a connector truly must bend, keep the elbows orthogonal, aligned, and easy to justify.
- Export the rendered page and visually inspect it. If a connector appears detached, partially attached, stacked on another route, broken by labels, forced through labels or boundaries, or shaped by a diagonal segment, reroute and rerender.
- Run `python3 scripts/review_visual_preview.py --preview ... --report ... --spec ... --output ...visual-review.json --fail-on-issues` after export and treat every finding as a blocker until the spec is fixed and the preview gate passes.
- Treat connectors that only almost reach a subnet wall, VCN wall, or workload icon as defects. The line should visibly terminate on the intended boundary or target.
- Prioritize traffic-flow arrows during visual QA and assign dedicated routing lanes when they would otherwise overlap.
- Perform spacing and overlap review separately from the renderer quality check and the architecture review.
- Require one more confirmatory render and clean quality review after the first clean render before delivering the diagram.
- Preserve the exact official icon name in your mapping notes, especially for toolkit-only additions.
- Keep the JSON spec beside the final diagram when repeatability matters.
