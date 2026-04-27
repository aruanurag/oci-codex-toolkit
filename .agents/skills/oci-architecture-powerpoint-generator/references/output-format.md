# OCI PowerPoint Output Format

Use this package shape unless the user asks for something different.

When the request includes a specific Oracle solution link or another explicit reference, switch into reference replication mode. Read `references/oracle-solution-patterns.md`, extract a structured `Reference Summary`, synthesize a `Recreation Prompt`, and report a `Reference Alignment Review` with a `0-100` similarity score, the key differences, and the next meaningful improvements after each material render.

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
- whether public ingress visually traverses the Internet Gateway before entering the VCN when an Internet Gateway is shown
- whether gateway icons are mounted on the VCN boundary instead of floating decoratively
- whether AD grouping lanes avoid swallowing the private data tier or implying a regional database is single-AD scoped
- whether support, security, observability, or operations panels overlap the VCN, subnet, or AD boundaries
- whether native OCI labels are hidden when a custom side label repeats the same service name
- whether any unrelated icons, labels, grouping boxes, connectors, arrowheads, or boundaries overlap or nearly touch in a way that reads as overlap
- whether any separate top-level icons or location groups overlap even if they are not siblings in the spec
- whether any icon was stretched to solve spacing instead of moving the surrounding layout

Run `python3 scripts/review_visual_preview.py --preview ... --report ... --spec ... --output ...visual-review.json --fail-on-issues` as the exported-preview gate. If the gate or the manual review finds an issue, update the slide spec, rerender, re-export, and rerun the gate before final delivery.

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
- run the exported-preview visual gate with `--fail-on-issues` and do not accept output while it reports issues
- when presenter-only guidance is needed, store it in PowerPoint presenter notes instead of visible footer bars or summary strips

## JSON Slide Spec

Include the renderable JSON spec when repeatability matters or when the slide may be iterated later.

Include the top-level `clarification_gate` object in that spec so the recorded follow-up questions, recommended options, and selected answers are preserved with the renderable artifact.

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
- public ingress traversal through the Internet Gateway when shown
- support/ops panel separation from network boundaries
- duplicate native/custom service labels
- avoidable connector bends
- top-level canvas margin

Do not treat a clean preview as sufficient if the architecture review still finds a design problem.

Prefer `python3 scripts/export_powerpoint_preview.py --input ... --image-out ...` so the preview goes through Microsoft PowerPoint before becoming an image.
Run `python3 scripts/review_visual_preview.py --preview ... --report ... --spec ... --output ...visual-review.json --fail-on-issues` after export and treat every finding as a blocker until the spec is fixed and the preview gate passes.

If the slide intentionally includes presenter notes, confirm they stay in PowerPoint notes and do not leak onto the visible preview canvas.

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
