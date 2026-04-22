# OCI Architecture Generator

Generate finalized OCI architecture diagrams for draw.io that follow the bundled Oracle OCI style guide, icon catalog, and renderer workflow.

This skill is designed for Codex users who want OCI diagrams that are:

- physically accurate and network-complete
- rendered as finished `.drawio` files
- aligned to Oracle-provided OCI icons first
- honest about fallbacks when a direct OCI icon does not exist
- visually reviewed until the linework is clean

## Where This Skill Lives

This repository includes the skill locally at:

- `.agents/skills/oci-architecture-generator`

The Codex global skills folder is typically:

- `~/.codex/skills`

If you copy this skill into the global folder, you can use it across workspaces. If you keep it only in `.agents/skills`, it is available only inside this repository.

## What The Skill Does

The skill helps Codex:

1. interpret an OCI architecture description
2. map requested components to approved OCI icons
3. use the closest honest fallback when an official OCI icon is missing
4. generate a renderable JSON spec
5. render a finalized `.drawio` file
6. export the physical page to PNG
7. iterate until lines, arrows, and labels are visually clean
8. route cross-container traffic through hidden boundary anchors so connectors visibly meet subnet and VCN walls instead of merely approaching them

By default, the skill now produces:

- a physical diagram only
- public and private subnet structure with CIDRs for networked workloads
- iterative visual QA focused on traffic-flow arrows, overlaps, and detached-looking connectors
- boundary-first routing for cross-container traffic, with hidden `*-anchor` shapes on container borders and arrowheads reserved for final destination segments

## When To Use It

Use this skill when you want Codex to:

- create a new OCI architecture diagram
- recreate an Oracle-style OCI diagram from a text description
- convert an architecture idea into a physical draw.io diagram
- compare generated output against an Oracle reference and iterate
- resolve OCI icons and document placeholders honestly
- render and visually review an OCI `.drawio` diagram

## How To Trigger It In Codex

Use the skill name directly in your prompt:

```text
Use $oci-architecture-generator to design a multi-region OCI architecture for an OKE-based SaaS platform and produce a finalized draw.io diagram.
```

You can also ask more directly:

```text
Use $oci-architecture-generator to create a 3-tier OCI architecture with DR, VCNs, public/private subnets, and a final .drawio output.
```

Or provide a reference-driven request:

```text
Use $oci-architecture-generator to recreate this OCI reference pattern, keep the lines clean, and iterate until the physical diagram looks production-ready.
```

## Recommended Prompt Pattern

The best requests include:

- the workload type
- the OCI services involved
- region or multi-region scope
- HA or DR expectations
- network requirements
- whether there is a reference image or Oracle pattern to follow
- whether the output should be a final `.drawio`

Good example:

```text
Use $oci-architecture-generator to create a physical OCI architecture for a SaaS workload.
Use one OCI region with a hub VCN and two spoke VCNs.
Show public and private subnets with CIDRs, DRG, internet gateway, LPG-based peering, route tables, and security lists.
Create the final .drawio and keep iterating until the traffic arrows and lines are clean.
```

## What Inputs Work Best

This skill works well with:

- plain-English architecture descriptions
- OCI service lists
- security and networking constraints
- Oracle reference images
- existing `.drawio` or exported PNG/SVG diagrams to compare against
- bundled Oracle `.drawio` references imported into `assets/reference-architectures/oracle/`

If you provide a reference image, Codex can use it to improve:

- layout symmetry
- connector simplicity
- subnet grouping
- icon placement
- line cleanliness

## Default Skill Behavior

The skill follows these defaults unless you ask otherwise:

### Diagram Type

- physical diagram only
- no logical page unless explicitly requested

### Network Completeness

- VCN boundaries are shown
- public and private subnets are shown
- CIDRs are labeled
- public resources stay in public subnets
- application and data resources stay in private subnets

### Icon Resolution Order

1. direct OCI icon
2. trusted OCI alias
3. logical generic icon on logical pages only
4. clearly labeled closest placeholder on physical pages

### Quality Gate

The skill does not stop after the first render.

It must:

1. render the `.drawio`
2. export a PNG
3. inspect the page visually
4. reroute lines and arrows if needed
5. do at least two cleanup passes plus one confirmatory pass

Broken-looking traffic arrows, overlaps, detached-looking arrowheads, and labels on top of lines are treated as blockers.

### Connector Routing Defaults

- physical flows that cross subnet, VCN, tier, or region boundaries route through hidden `*-anchor` shapes on those borders
- intermediate segments use `endArrow=none;`
- the final segment into the workload keeps the visible arrowhead
- a connector that only almost reaches a boundary or target is considered broken and must be rerouted

## Bundled Oracle References

The skill now includes the Oracle `.drawio` files imported from the user-provided zip archives under:

- `.agents/skills/oci-architecture-generator/assets/reference-architectures/oracle`

The selector can now recommend a primary baseline plus supporting references for mixed requests:

```bash
python3 -B .agents/skills/oci-architecture-generator/scripts/select_reference_architecture.py \
  --query "OKE SaaS platform with DR and public/private subnets" \
  --bundle --top 5
```

Reference details and best-fit use cases are documented in:

- `.agents/skills/oci-architecture-generator/references/reference-architectures.md`

## Expected Outputs

Typical output package:

- final `.drawio`
- renderable `.json` spec
- `.report.json` from the renderer
- exported PNG for visual review
- placeholder notes when fallbacks are used

Typical output folder example:

```text
output/
  architecture-name.drawio
  architecture-name.json
  architecture-name.report.json
  architecture-name-physical.png
```

## How The Skill Is Organized

```text
oci-architecture-generator/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── drawio/
│   ├── reference-architectures/
│   └── examples/
├── references/
│   ├── reference-architectures.md
│   ├── style-guide.md
│   ├── output-format.md
│   ├── diagram-spec.md
│   └── icon-catalog.md
└── scripts/
    ├── resolve_oci_icon.py
    ├── select_reference_architecture.py
    ├── render_oci_drawio.py
    ├── build_icon_catalog.py
    ├── test_icon_resolver.py
    ├── test_reference_selector.py
    └── test_render_oci_drawio.py
```

## Important Files

### `SKILL.md`

Core behavior, workflow, fallback rules, and default expectations.

### `references/style-guide.md`

Oracle-specific visual and diagram guardrails.

### `references/output-format.md`

Expected package shape and quality bar.

### `references/diagram-spec.md`

JSON contract for renderable diagrams.

### `references/reference-architectures.md`

Imported Oracle reference corpus and the best-fit use for each bundled `.drawio`.

### `scripts/resolve_oci_icon.py`

Resolves requested components to OCI icons or honest placeholders.

### `scripts/select_reference_architecture.py`

Ranks the bundled Oracle references and can recommend one primary plus supporting references.

### `scripts/render_oci_drawio.py`

Renders the JSON spec into the final `.drawio`.

## Common Workflows

### 1. Generate A New Diagram

Prompt example:

```text
Use $oci-architecture-generator to create a physical OCI architecture for a payments platform with OKE, API Gateway, Autonomous Database, and DR across two regions.
```

Expected flow:

1. Codex reads the skill
2. resolves icons
3. creates the spec
4. renders the diagram
5. exports PNG
6. iterates visually

### 2. Recreate A Reference Pattern

Prompt example:

```text
Use $oci-architecture-generator and make this diagram visually similar to the attached Oracle reference. Keep iterating until the connectors are equally clean.
```

### 3. Update An Existing Diagram

Prompt example:

```text
Use $oci-architecture-generator to update the existing draw.io architecture by adding a DR region, route tables, security lists, and cleaner traffic arrows.
```

### 4. Compare Generated Output To A Reference

Prompt example:

```text
Use $oci-architecture-generator to create the architecture, compare it to the attached Oracle example, and keep iterating until the layout and line quality are close.
```

## Fallback And Placeholder Rules

The skill is strict about not faking OCI icons.

If no direct OCI icon exists:

- it uses the closest similar placeholder shape
- it records the fallback in the report
- it may mention the closest official OCI icon considered

Examples:

- missing network/security control: `hexagon`
- missing generic application or system: `rounded-rectangle`
- missing external service or internet-like object: `cloud`

## Visual QA Rules

The skill specifically checks for:

- overlapping connector segments
- labels sitting on top of lines
- detached-looking arrowheads
- awkward bends through subnet or VCN boundaries
- connectors that visually miss container boundaries or workload icons
- traffic arrows that look broken or overly busy
- crowded placements that reduce readability

Preferred line behavior:

- straight lines where possible
- reserved horizontal or vertical lanes for major traffic paths
- minimal bends
- boundary-to-boundary routing through hidden anchors when a flow crosses containers
- labels placed near lines instead of directly breaking them

## Testing The Skill

If you make changes to the skill or renderer, run:

```bash
python3 -B .agents/skills/oci-architecture-generator/scripts/test_icon_resolver.py
python3 -B .agents/skills/oci-architecture-generator/scripts/test_reference_selector.py
python3 -B .agents/skills/oci-architecture-generator/scripts/test_render_oci_drawio.py
```

To render a diagram manually:

```bash
python3 -B .agents/skills/oci-architecture-generator/scripts/render_oci_drawio.py \
  --spec /path/to/spec.json \
  --output /path/to/output.drawio \
  --report-out /path/to/output.report.json
```

To resolve a component manually:

```bash
python3 -B .agents/skills/oci-architecture-generator/scripts/resolve_oci_icon.py \
  --page physical \
  --query "local peering gateway"
```

## Installing Into Codex Global Skills

If you want this skill available everywhere, copy the folder into:

- `~/.codex/skills/oci-architecture-generator`

Once installed globally, you can invoke it from other workspaces with:

```text
Use $oci-architecture-generator ...
```

## Local Vs Global

### Local Skill

- location: `.agents/skills/oci-architecture-generator`
- best when the skill is specific to this repository
- easy to edit and test alongside the renderer and examples

### Global Skill

- location: `~/.codex/skills/oci-architecture-generator`
- best when you want to reuse the skill across many repos
- may need to be refreshed if the local version changes

## Troubleshooting

### Skill does not trigger

- mention it explicitly as `$oci-architecture-generator`
- make sure the global or local skill folder exists
- verify `SKILL.md` is present

### Diagram looks too crowded

- ask for a larger canvas
- ask Codex to match a cleaner reference layout
- tell it to simplify traffic lanes and reduce connector count

### Wrong icon chosen

- specify the exact OCI service name
- ask Codex to verify icon resolution
- ask for placeholder honesty if no exact icon exists

### Lines still look messy

Ask explicitly:

```text
Keep iterating until the traffic arrows are clean, labels are off the lines, every cross-container route uses boundary anchors, and no connector looks broken.
```

## Best Practice Prompt

If you want the highest-quality output, use a prompt like this:

```text
Use $oci-architecture-generator to create a finalized physical OCI architecture diagram in draw.io.
Follow the OCI style guide strictly.
Show VCNs, public and private subnets, CIDRs, route tables, security lists, and all major gateways.
If a direct OCI icon does not exist, use the closest honest placeholder.
Route cross-container traffic through boundary anchors and keep arrowheads only on final destination segments.
Export and visually review the result, then keep iterating until the lines, arrows, and labels are clean.
```
