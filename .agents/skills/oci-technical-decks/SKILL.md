---
name: oci-technical-decks
description: Create OCI technical PowerPoint decks for instructor-led product overviews, service deep dives, workshop lessons, and technical briefings such as OCI networking, compute shapes, observability, storage, security, or architecture internals. Use when the user wants a technical slide deck, slide outline, or polished `.pptx` with presenter notes on every slide.
---

# OCI Technical Decks

## Overview

Use this skill when the user wants a technical OCI PowerPoint deck that teaches how a service, architecture pattern, or platform capability works.

This skill is instructor-led by default:

- every slide should include presenter notes
- visible slide copy should stay concise enough for live delivery
- the story should answer technical questions, not just market the service
- diagrams, tables, and architecture views should carry the explanation when they can
- design-director review is mandatory before sign-off on any PowerPoint output

This skill is not the right starting point when the user mainly wants:

- an executive `why OCI` deck with business-outcome framing first
- a single OCI architecture diagram or architecture slide
- raw documentation rewritten as slides without presentation design

For executive or presales decks, use [../oci-sales-decks/SKILL.md](../oci-sales-decks/SKILL.md).
For OCI architecture slides, use [../oci-architecture-powerpoint-generator/SKILL.md](../oci-architecture-powerpoint-generator/SKILL.md).

## Use Cases

Use this skill for:

- OCI networking strength decks
- OCI compute-shapes overviews
- OCI observability services overviews
- service-family comparison decks
- instructor-led workshops or lesson decks
- internal field enablement decks
- customer-safe technical briefings
- architecture explainer decks
- topic-based slide outlines, presenter notes, or full `.pptx` creation

## Quick Routing

- If the user provides an Oracle technical deck or a prior workshop deck, audit it first for pacing, technical depth, visuals, and internal-only markings.
- For every customer-facing or field-facing `.pptx`, read [../oci-ppt-design-director/SKILL.md](../oci-ppt-design-director/SKILL.md) and treat its review as mandatory.
- If the deck needs conceptual technical diagrams such as layered host boundaries, control-plane versus data-plane views, comparison frames, annotated screenshot modules, or footprint visuals, read [../oci-diagram-patterns/SKILL.md](../oci-diagram-patterns/SKILL.md) before improvising shapes.
- If the deck needs OCI architecture slides or topology diagrams, use [../oci-architecture-powerpoint-generator/SKILL.md](../oci-architecture-powerpoint-generator/SKILL.md) for those slides instead of improvising the architecture.
- If the deck is really an executive recommendation deck, route to [../oci-sales-decks/SKILL.md](../oci-sales-decks/SKILL.md).

## Workflow

1. Choose the starting artifact:
   - attached Oracle technical deck
   - existing workshop or training deck
   - clean-room deck from scratch
2. Start with a short plan:
   - topic
   - audience
   - teaching goal
   - internal-only vs customer-safe
   - expected depth
   - likely diagrams, tables, screenshots, or demos
3. Identify the deck mode:
   - product overview
   - service-family overview
   - comparison or decision deck
   - architecture explainer
   - workshop lesson deck
   - field-enablement speaker deck
4. Extract the technical facts that shape the story:
   - what the service or capability is
   - why it exists
   - how it works
   - where it fits in OCI
   - when to use it and when not to
   - tradeoffs, constraints, or prerequisites
   - operational implications
5. Ask only the smallest useful set of follow-up questions, usually `1-4`, after the plan and any source-deck audit. Questions must come from real decision gaps, not a hardcoded checklist. Lead with the recommended assumption first.
6. Choose the closest blueprint from [references/slide-blueprints.md](references/slide-blueprints.md).
7. Read [references/topic-patterns.md](references/topic-patterns.md) for the chosen technical topic.
8. Read [references/technical-storytelling.md](references/technical-storytelling.md) to keep the deck mechanism-led and instructor-friendly.
9. If one or more slides need repeatable conceptual diagrams or editable technical motifs, read [../oci-diagram-patterns/SKILL.md](../oci-diagram-patterns/SKILL.md) and create a `Pattern Brief` before slide authoring.
10. For every `.pptx`, read [../oci-ppt-design-director/SKILL.md](../oci-ppt-design-director/SKILL.md) before authoring final slide content and again before sign-off.
11. Build the storyline before drafting slides:
   - the technical question or platform problem
   - the old model or common constraint
   - the OCI mechanism or architecture difference
   - the operational or performance consequence
   - where the service fits
   - tradeoffs, caveats, or comparisons
   - summary and next step
12. Draft the deck slide by slide. For each slide, include:
   - `title`
   - `core message`
   - `supporting points`
   - `recommended visual`
   - `presenter_notes`
   - optional `demo cue` or `transition`
13. If the user wants an actual `.pptx`:
   - keep the deck instructor-led rather than document-like
   - put presenter coaching, transitions, caveats, and deeper explanation into notes on every slide
   - keep visible slide copy audience-facing and compact
   - preserve Oracle-native technical deck feel without copying source-deck text
   - use [../oci-diagram-patterns/SKILL.md](../oci-diagram-patterns/SKILL.md) for editable conceptual diagrams instead of ad hoc shapes whenever the same motif could recur
   - use [../oci-architecture-powerpoint-generator/SKILL.md](../oci-architecture-powerpoint-generator/SKILL.md) for architecture slides
   - export a preview and review for clipping, overlap, leaked notes, pacing problems, and any text escaping its intended card or container
   - treat text that spills outside a card, box, or summary strip as a hard blocker, not a polish item
   - if PowerPoint-native shrink makes a card technically fit but visibly cramped, rewrite the copy or enlarge the container instead of accepting the slide
   - use the renderer quality output as a hard gate and rerender until there are no unresolved `text-overflow` findings, using the renderer's `--fail-on-text-overflow` mode for final deck passes
14. Before sign-off, explicitly record:
   - that presenter notes exist on every slide
   - whether the deck is internal-only or customer-safe
   - that design-director review passed, or the findings that were fixed

## Default Deck Sizes

- Product overview: `8-12` slides
- Service-family overview: `6-10` slides
- Comparison deck: `6-9` slides
- Customer-safe technical briefing: `8-14` slides
- Workshop lesson deck: `10-20` slides

Increase slide count only when the teaching objective really needs step-by-step explanation or appendix detail.

## Technical Deck Guardrails

- Lead with the technical question, architecture problem, or operational challenge first.
- Keep one teaching point per slide.
- Prefer diagrams, comparisons, and annotated visuals over bullet-heavy narration.
- Every slide should include presenter notes. Do not treat notes as optional.
- Keep visible slide copy concise enough for instructor-led delivery.
- Use customer-safe language by default unless the user explicitly asks for Oracle-internal or restricted material.
- Remove inherited confidentiality labels, safe-harbor pages, internal reminders, or product-direction language unless the user explicitly wants that internal deck behavior.
- Verify precise OCI facts against official Oracle sources when correctness materially matters.
- Separate what is `known`, `assumed`, and `recommended`.
- Avoid service-catalog dump slides. Group services by job-to-be-done, architecture role, or operator workflow.
- State tradeoffs honestly on comparison slides.
- Do not drop dense screenshots or terminal output onto the slide without cropping, scaling, or framing them so they are readable.
- Reduce table rows before shrinking the font into clutter.
- Keep presenter prompts, transition cues, and explanations in notes, not on the canvas.
- Use one architecture diagram, one comparison frame, or one hero visual per slide when possible.
- If the deck covers networking, observability, or another control-plane-heavy topic, be explicit about data path, control path, and where the service sits.
- Treat visible text escaping its intended card, chip, callout, strip, or container as a blocker.
- Do not accept a deck just because PowerPoint can auto-fit the text; if the box becomes cramped or visibly strained, revise the slide.

## Review Checklist

Before sharing the deck or outline, check:

- Is the teaching goal explicit?
- Does each slide answer one technical question?
- Are presenter notes present on every slide?
- Is the visible copy concise enough for instructor-led delivery?
- Did the deck pass design-director review?
- Did any presenter notes, speaker coaching, or author prompts leak into visible slide text?
- Did any internal-only label, safe-harbor text, or confidentiality footer remain unintentionally?
- Are any comparisons or product statements outdated, overstated, or missing key caveats?
- If diagrams are present, did architecture and visual review pass?
- Does any visible text clip, overlap, or collide with a border?
- Did the final render pass the hard text-containment gate with no unresolved `text-overflow` findings?
- Did the generated `.pptx` open and export cleanly through a PowerPoint-native path?

## Deliverables

Default to producing:

1. A short planning summary.
2. A source-deck audit summary when a source deck exists.
3. The recommended deck type and why it fits.
4. The slide-by-slide outline.
5. Presenter notes for every slide.
6. Diagram-pattern handoff notes when conceptual diagrams are needed.
7. Architecture-slide handoff notes when OCI diagrams are needed.
8. A final `.pptx` when the user asks for an actual deck.
9. Assumptions, risks, and next steps.

## Resources

- Read [references/oracle-technical-deck-north-star.md](references/oracle-technical-deck-north-star.md) when the deck should feel like an Oracle technical presentation rather than a presales pitch.
- Read [references/slide-blueprints.md](references/slide-blueprints.md) after you know the deck mode.
- Read [references/topic-patterns.md](references/topic-patterns.md) after you know the OCI topic.
- Read [references/technical-storytelling.md](references/technical-storytelling.md) when you need to sharpen the teaching flow, comparisons, or presenter notes.
- Read [../oci-diagram-patterns/SKILL.md](../oci-diagram-patterns/SKILL.md) when the deck needs layered system diagrams, packet or control flows, comparison motifs, annotated screenshots, or other reusable conceptual visuals.
- Read [../oci-ppt-design-director/SKILL.md](../oci-ppt-design-director/SKILL.md) for every PowerPoint deck before final rendering and sign-off.
- Read [../oci-architecture-powerpoint-generator/SKILL.md](../oci-architecture-powerpoint-generator/SKILL.md) when the deck needs OCI architecture slides or Oracle toolkit visuals.
- Use [../oci-architecture-powerpoint-generator/scripts/export_powerpoint_preview.py](../oci-architecture-powerpoint-generator/scripts/export_powerpoint_preview.py) to preview a generated deck when visual QA matters.
