# OCI Codex Toolkit Skills Workspace

This repository is a Codex skill workspace for OCI solution work across architecture diagrams, PowerPoint decks, BOMs, Excel workbooks, and customer-ready review gates.

It bundles local skills for:

- OCI physical architecture diagrams in `.drawio`
- OCI architecture slides in `.pptx`
- OCI presales and executive decks
- OCI instructor-led technical decks
- reusable PowerPoint-native diagram patterns
- OCI BOM and cost-estimate workbooks
- Excel workbook creation, inspection, repair, and validation
- visual direction and review gates for customer-ready PPT output

The repo is intentionally simple at the top level. Most logic, assets, references, and scripts live in `.agents/skills/`, and generated artifacts land in `output/`.

## Installation

### Use In This Repo

This repository already uses the local-skill layout Codex expects:

- local skills live in `.agents/skills/`
- they are available inside this workspace
- this is the best mode when the skills are under active development

Nothing extra is required for local use in this repo.

### Install In Another Repo

To use this toolkit inside a different repository, copy the local skills folder into that repo:

```bash
REPO_ROOT=/path/to/OCiArchitecture-CodexSkill
mkdir -p /path/to/other-repo/.agents
cp -R "$REPO_ROOT/.agents/skills" /path/to/other-repo/.agents/
```

That installs the OCI skills only for that repository.

### Install Globally

To make the skills available across repositories, copy the skill suite into the Codex global skills directory:

```bash
REPO_ROOT=/path/to/OCiArchitecture-CodexSkill
mkdir -p ~/.codex/skills
cp -R "$REPO_ROOT/.agents/skills/." ~/.codex/skills/
```

Global notes:

- The typical global location is `~/.codex/skills/`.
- Keep the directory names exactly the same.
- Copy the full suite together, because several skills cross-reference one another.
- Copy `shared/` along with the OCI skills, because review scripts import shared helpers by relative path.
- If the skills do not appear immediately, start a new Codex session in the target workspace.

### Copy Vs Symlink

If you want the global install to track this repo while you continue editing the skills, symlink instead of copying:

```bash
REPO_ROOT=/path/to/OCiArchitecture-CodexSkill
mkdir -p ~/.codex/skills
ln -s "$REPO_ROOT/.agents/skills/oci-architecture-generator" ~/.codex/skills/oci-architecture-generator
ln -s "$REPO_ROOT/.agents/skills/oci-architecture-powerpoint-generator" ~/.codex/skills/oci-architecture-powerpoint-generator
ln -s "$REPO_ROOT/.agents/skills/oci-bom-generator" ~/.codex/skills/oci-bom-generator
ln -s "$REPO_ROOT/.agents/skills/oci-diagram-patterns" ~/.codex/skills/oci-diagram-patterns
ln -s "$REPO_ROOT/.agents/skills/oci-ppt-design-director" ~/.codex/skills/oci-ppt-design-director
ln -s "$REPO_ROOT/.agents/skills/oci-sales-decks" ~/.codex/skills/oci-sales-decks
ln -s "$REPO_ROOT/.agents/skills/oci-technical-decks" ~/.codex/skills/oci-technical-decks
ln -s "$REPO_ROOT/.agents/skills/xlsx" ~/.codex/skills/xlsx
ln -s "$REPO_ROOT/.agents/skills/shared" ~/.codex/skills/shared
```

## Repository Layout

```text
.
|-- .agents/
|   `-- skills/
|       |-- oci-architecture-generator/
|       |-- oci-architecture-powerpoint-generator/
|       |-- oci-bom-generator/
|       |-- oci-diagram-patterns/
|       |-- oci-ppt-design-director/
|       |-- oci-sales-decks/
|       |-- oci-technical-decks/
|       |-- shared/
|       `-- xlsx/
|-- output/
`-- README.md
```

## Skills At A Glance

| Skill | Primary Job | Main Output | Best Used When |
| --- | --- | --- | --- |
| `oci-architecture-generator` | OCI architecture generation for draw.io | `.drawio`, `.json`, review reports, previews | You want an editable OCI architecture diagram |
| `oci-architecture-powerpoint-generator` | OCI architecture generation for PowerPoint | `.pptx`, `.json`, review reports, previews | You want an OCI architecture slide in PowerPoint |
| `oci-bom-generator` | OCI BOM and price-estimate generation | `.xlsx`, `.md`, `.csv`, `.json` | You want a confirmed-assumption OCI BOM or cost workbook |
| `oci-sales-decks` | OCI presales and executive storytelling | slide outline, notes, `.pptx` | You want a customer-facing sales or briefing deck |
| `oci-technical-decks` | OCI instructor-led technical presentations | slide outline, presenter notes, `.pptx` | You want a technical deck with notes on every slide |
| `oci-ppt-design-director` | visual system and design review | design brief, review findings, direction | You want cleaner, more polished PowerPoint output |
| `oci-diagram-patterns` | reusable conceptual diagram motifs | pattern brief, optional PPT JSON fragment | You need editable conceptual visuals, not full topology |
| `xlsx` | Excel workbook creation, inspection, repair, and validation | `.xlsx`, workbook inspection JSON | You want spreadsheet deliverables or workbook QA |
| `shared` | helper utilities for preview review | Python helpers | The OCI skills need shared audit logic |

## Skill Details And Sample Prompts

### `oci-architecture-generator`

Creates finalized OCI physical architecture diagrams as editable `.drawio` files. It uses bundled Oracle draw.io assets, planning and clarification gates, official OCI icon resolution, architecture review, visual QA, and repeated render-review cycles.

Sample prompts:

```text
Use the oci-architecture-generator skill to create a physical OCI architecture for a highly available 3-tier web application with regional subnets and multi-AD deployment.
```

```text
Use the oci-architecture-generator skill to recreate this Oracle reference architecture as an editable draw.io file, then review the routing and icon mapping before delivery.
```

### `oci-architecture-powerpoint-generator`

Creates OCI architecture slides as PowerPoint-native `.pptx` output. It uses the bundled Oracle OCI PowerPoint toolkit and applies PowerPoint-specific review for spacing, containment, connector routing, package integrity, and customer-readiness.

Sample prompts:

```text
Use the oci-architecture-powerpoint-generator skill to create a physical OCI architecture slide for an OKE application with WAF, load balancer, private workers, and Autonomous Database.
```

```text
Use the oci-architecture-powerpoint-generator skill to build a customer-ready PowerPoint architecture slide from this service list and include presenter notes for the solution walkthrough.
```

### `oci-bom-generator`

Generates OCI BOMs and list-price estimates from architecture specs, service lists, prompts, or image-derived assumptions. It always runs an assumption confirmation gate before customer-facing pricing, uses Oracle Cost Estimator pricing data with a 48-hour local cache, and emits an Excel-first deliverable with support files.

Default outputs:

- `.xlsx` primary customer-facing BOM workbook
- `.md` readable summary
- `.csv` flat line-item export
- `.json` machine-readable estimate, assumptions, warnings, and review gates

Sample prompts:

```text
Use the oci-bom-generator skill to create an Excel BOM from this OCI architecture diagram. First extract and confirm assumptions before fetching prices.
```

```text
Use the oci-bom-generator skill to price this service list: OKE, 3 worker nodes, public load balancer, OCIR, and a two-node Base Database RAC system. Generate an Excel workbook after I confirm the assumptions.
```

### `oci-sales-decks`

Creates or adapts OCI customer-facing PowerPoint decks for presales, executive briefings, workshops, POCs, migrations, and recommendation narratives. It keeps the story anchored in outcomes, recommendation logic, proof, and next steps rather than a service catalog.

Sample prompts:

```text
Use the oci-sales-decks skill to create an OCI executive recommendation deck for a customer CTO, including speaker notes and one supporting architecture slide.
```

```text
Use the oci-sales-decks skill to turn this discovery summary into a customer-facing migration proposal deck with business outcomes, OCI recommendations, risks, and next steps.
```

### `oci-technical-decks`

Creates OCI technical decks for workshops, product overviews, architecture explainers, service deep dives, and field enablement. It treats decks as instructor-led by default, keeps visible slide copy concise, and puts deeper guidance in presenter notes.

Sample prompts:

```text
Use the oci-technical-decks skill to create an instructor-led OCI containers deck with presenter notes on every slide and one architecture explainer slide.
```

```text
Use the oci-technical-decks skill to build a technical deep-dive deck on OCI networking, including control-plane/data-plane explanation, common patterns, and workshop speaker notes.
```

### `oci-ppt-design-director`

Acts as the visual direction and review layer for OCI PowerPoint work. It defines visual thesis, slide archetypes, spacing rules, density limits, and review gates before rendering or sign-off.

Sample prompts:

```text
Use the oci-ppt-design-director skill to improve the visual system, spacing, and review quality of this OCI customer deck before final delivery.
```

```text
Use the oci-ppt-design-director skill to review this generated PowerPoint for clipping, note leakage, crowded text, weak hierarchy, and customer-readiness.
```

### `oci-diagram-patterns`

Creates reusable, editable PowerPoint-native conceptual diagram patterns. It is best for control-plane/data-plane views, layered system diagrams, comparison frames, annotated screenshot layouts, packet-flow diagrams, and subsystem maps.

Sample prompts:

```text
Use the oci-diagram-patterns skill to create a reusable control-plane and data-plane comparison motif for an OCI technical deck.
```

```text
Use the oci-diagram-patterns skill to design an editable packet-flow diagram pattern for a slide explaining private OKE ingress and service gateway access.
```

### `xlsx`

Creates, inspects, edits, repairs, and validates Excel `.xlsx` workbooks. It is used directly for spreadsheet tasks and as a helper skill for BOM workbooks.

Sample prompts:

```text
Use the xlsx skill to create a presentation-ready Excel workbook from this CSV, with a summary sheet, filters, frozen headers, formulas, and validation.
```

```text
Use the xlsx skill to inspect this workbook, identify formulas, hidden sheets, tables, charts, and any workbook-integrity risks before I send it to a customer.
```

### `shared`

Holds shared helper code used by the OCI skills. You normally do not invoke it directly, but it should be copied or installed with the rest of the suite because preview-review scripts import it by relative path.

Sample prompt:

```text
Use the OCI skill suite normally; keep shared installed because architecture and PowerPoint review scripts depend on it.
```

## How The Skills Work Together

Use the skills as a small OCI content system rather than isolated tools:

- `oci-architecture-generator` creates editable draw.io architecture source.
- `oci-architecture-powerpoint-generator` creates OCI-native architecture slides.
- `oci-bom-generator` creates confirmed-assumption Excel BOMs and cost-estimate support files.
- `oci-sales-decks` creates presales, executive, and recommendation stories.
- `oci-technical-decks` creates instructor-led product and architecture teaching decks.
- `oci-ppt-design-director` sets the visual contract and reviews PowerPoint output.
- `oci-diagram-patterns` creates conceptual slide diagrams that are not full OCI topologies.
- `xlsx` creates and validates spreadsheet deliverables.

Typical combinations:

- Customer deck: `oci-sales-decks` + `oci-ppt-design-director` + optional `oci-architecture-powerpoint-generator`
- Technical deck: `oci-technical-decks` + `oci-ppt-design-director` + optional `oci-diagram-patterns`
- Architecture-only slide: `oci-architecture-powerpoint-generator` + `oci-ppt-design-director`
- Editable source diagram: `oci-architecture-generator`
- Customer BOM: `oci-bom-generator` + `xlsx`
- Architecture package: `oci-architecture-generator` or `oci-architecture-powerpoint-generator` + `oci-bom-generator`

## How To Invoke The Skills

In Codex, name the skill directly in the prompt:

```text
Use the oci-architecture-generator skill to create a multi-AD OCI web application diagram.
```

```text
Use the oci-bom-generator skill to create an Excel BOM from this architecture image after confirming assumptions with me.
```

```text
Use the oci-sales-decks skill to create an OCI presales deck for a customer executive team.
```

```text
Use the oci-technical-decks skill to create a technical deck on OCI observability services with presenter notes on every slide.
```

## Output Artifacts

Generated files land in `output/`. Depending on the workflow, a run may produce:

- `.drawio` diagrams
- `.pptx` presentations
- `.xlsx` BOMs and workbooks
- `.md` summaries
- `.csv` BOM exports
- `.json` render specs, BOM metadata, assumptions, and execution summaries
- `.report.json` execution reports
- `.quality.json` review outputs
- preview images for visual QA

Example artifact categories:

- customer or executive OCI decks
- instructor-led OCI technical decks
- editable OCI architecture diagrams
- PowerPoint-native architecture slides
- Excel BOM workbooks

## Quality Expectations

These skills are built for iterative, review-driven output rather than one-pass drafts. Shared expectations across the suite are:

- ask targeted clarification questions when answers change the architecture, deck, BOM, or sizing assumptions
- confirm BOM assumptions before fetching prices or producing customer-facing totals
- prefer official OCI icons and honest fallbacks
- keep connector routing simple and avoid unnecessary elbows
- prevent overlaps, clipped text, cramped text, and elements crossing container boundaries
- keep presenter guidance in notes instead of leaking it onto slides
- validate Excel workbooks before delivery
- rerender or regenerate until the artifact is presentation-ready
