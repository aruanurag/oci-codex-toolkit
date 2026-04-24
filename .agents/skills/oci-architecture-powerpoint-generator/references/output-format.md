# OCI PowerPoint Output Format

Use this package shape unless the user asks for something different.

## Default Package

1. Planning Summary
2. Clarifying Questions and Answers
3. Assumptions
4. Architecture Summary
5. Spacing and Overlap Review and Applied Fixes
6. Architectural Review and Applied Fixes
7. Final `.pptx`
8. JSON Slide Spec
9. Preview Image
10. Icon Mapping Table
11. Placeholder and Gap Notes

## Planning Summary

Before generating the slide, summarize:

- inferred topology and deployment style
- expected network boundaries
- HA or DR posture
- the closest Oracle PowerPoint reference slide to use as the baseline
- the few gaps that would reduce diagram quality if left unresolved

Always do this planning step before authoring the actual slide spec.

After the planning step, ask targeted clarification questions before generating the slide unless the user explicitly waives questions or the current thread already answered them.

## Clarifying Questions and Answers

Before authoring the slide spec:

- always ask 2 to 4 targeted questions that lock in topology, ingress, HA or DR posture, subnet framing, service meaning, icon choice, or symmetry and stage-alignment intent
- clarify whether OCI subnets should be treated as regional or AD-specific when that choice would change the slide
- keep questions focused on what would materially change the slide
- if icon meaning is uncertain or a requested component only maps weakly to the icon catalog, ask for confirmation and provide recommended options
- put the most honest recommendation first

If the current thread already answered those questions, state that the clarification gate is satisfied and summarize the answers you are using.

## Assumptions

Keep assumptions short and limited to items that materially affect the architecture or the slide layout.

## Architecture Summary

Summarize:

- what is being deployed
- which OCI services carry the design
- why the topology was chosen

## Spacing And Overlap Review And Applied Fixes

Before final delivery, review whether the slide has enough breathing room and whether any visual collisions remain after the PowerPoint render pass.

Check:

- whether every requested service resolved to an official OCI icon and whether any `closest` or `placeholder` fallback remains unresolved
- whether external location groups, clients, WAF, and first-hop OCI ingress services have visible separation
- whether icons and labels have enough spacing to avoid crowding, clipping, or misleading associations
- whether subnet labels still read cleanly when AD background lanes, cluster containers, or other large grouping boxes sit behind them
- whether any unrelated icons, labels, grouping boxes, connectors, arrowheads, or boundaries overlap or nearly touch in a way that reads as overlap
- whether any separate top-level icons or location groups overlap even if they are not siblings in the spec
- whether any icon was stretched to solve spacing instead of moving the surrounding layout

If the review finds an issue, update the slide spec and rerender before final delivery.

When recent passes found material issues such as missing icons, overlap, avoidable elbows, or package-repair warnings, increase the number of review passes and require fresh clean passes after the fix instead of stopping at the minimum review count.

## Architectural Review and Applied Fixes

Before final delivery, review whether the diagram is architecturally honest, not just visually clean.

Check:

- whether only ingress components are public for internet-facing designs
- whether web, app, and data tiers are isolated correctly for a 3-tier pattern
- whether regional subnets were used by default for OCI workloads unless the user explicitly asked for AD-specific subnets
- whether HA or DR claims are explicit in the drawing rather than implied only by labels
- whether ingress security, egress, and management omissions materially weaken the design
- whether any simplifying assumptions should be disclosed

If the review finds an issue, update the slide spec and rerender before final delivery.

If the review changes the architecture materially, refresh the assumptions or clarifying-answer notes too.

## Final `.pptx`

Unless the user says otherwise:

- create a physical PowerPoint architecture
- include VCNs and labeled public and private subnets for networked workloads, defaulting those OCI subnets to regional scope unless the user explicitly asked for AD-specific subnet framing
- place gateways on the VCN edge
- render to a finished `.pptx`, not just prose
- use the repo-level `output/` directory during testing
- visually review the exported preview and keep iterating until the diagram is clean

## JSON Slide Spec

Include the renderable JSON spec when repeatability matters or when the slide may be iterated later.

Use [diagram-spec.md](diagram-spec.md) for the contract.

## Preview Image

Export a preview image from the rendered `.pptx` and inspect:

- connector straightness
- whether any connector still uses avoidable elbows
- boundary attachment
- spacing between external location groups and ingress services
- visible separation between sibling containers
- icon centering
- label spacing
- label wrapping
- overlaps
- containment
- subnet inset from the VCN border
- whether the subnet framing truthfully reflects regional vs AD-specific scope
- visual distinction between opposing connector flows
- gateway placement on the VCN boundary
- avoidable connector bends
- top-level canvas margin

Do not treat a clean preview as sufficient if the architecture review still finds a design problem.

Prefer `python3 scripts/export_powerpoint_preview.py --input ... --image-out ...` so the preview goes through Microsoft PowerPoint before becoming an image.

## Icon Mapping Table

Use this table for every architecture package:

| Requested Component | Resolved Icon | Resolution Type | Notes |
| --- | --- | --- | --- |

Resolution types:

- `direct`
- `alias`
- `closest`
- `placeholder`

## Placeholder and Gap Notes

List every placeholder explicitly.

Include:

- the requested component
- the placeholder shape
- why no direct official icon was used
- the closest official icon considered, if one existed but would have been misleading

When the icon choice was uncertain enough to require confirmation, note the recommended option that was accepted.

List every non-direct official fallback explicitly too.
