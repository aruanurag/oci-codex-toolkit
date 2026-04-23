# OCI PowerPoint Output Format

Use this package shape unless the user asks for something different.

## Default Package

1. Planning Summary
2. Assumptions
3. Architecture Summary
4. Final `.pptx`
5. JSON Slide Spec
6. Preview Image
7. Icon Mapping Table
8. Placeholder and Gap Notes

## Planning Summary

Before generating the slide, summarize:

- inferred topology and deployment style
- expected network boundaries
- HA or DR posture
- the closest Oracle PowerPoint reference slide to use as the baseline
- the few gaps that would reduce diagram quality if left unresolved

If important gaps remain, ask targeted questions before generating the slide.

## Assumptions

Keep assumptions short and limited to items that materially affect the architecture or the slide layout.

## Architecture Summary

Summarize:

- what is being deployed
- which OCI services carry the design
- why the topology was chosen

## Final `.pptx`

Unless the user says otherwise:

- create a physical PowerPoint architecture
- include VCNs and labeled public and private subnets for networked workloads
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
- boundary attachment
- icon centering
- label spacing
- label wrapping
- overlaps
- containment
- gateway placement on the VCN boundary
- avoidable connector bends
- top-level canvas margin

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
