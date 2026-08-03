---
name: excalidraw-diagrams
description: Create, inspect, and revise editable Excalidraw `.excalidraw` diagrams with local SVG previews and layout-quality checks. Use when Codex needs to turn an architecture, process flow, system context, user journey, workshop whiteboard, stakeholder map, or node-and-edge JSON spec into an editable Excalidraw file; update an existing Excalidraw scene; or validate and preview a local diagram without uploading it to a third-party service.
---

# Excalidraw Diagrams

Create real Excalidraw scene JSON rather than a static image. Use simple shapes, labels, arrows, and grouped regions so the result remains easy to edit in Excalidraw.

## Workflow

1. Identify the audience, diagram type, elements, important relationships, and desired orientation. Ask only for information that would materially change the diagram.
2. Choose a readable composition. Use grouped regions for architecture zones, layers, swimlanes, or ownership boundaries instead of a single undifferentiated row of boxes.
3. Write a compact JSON spec, then generate and validate the scene:

```bash
SKILL_DIR=.agents/skills/excalidraw-diagrams
python3 "$SKILL_DIR/scripts/generate_excalidraw.py" spec.json output.excalidraw --preview
python3 "$SKILL_DIR/scripts/validate_scene.py" output.excalidraw
```

4. Run the layout review, then inspect the SVG preview before delivery:

```bash
SKILL_DIR=.agents/skills/excalidraw-diagrams
python3 "$SKILL_DIR/scripts/review_layout.py" output.excalidraw --strict
```

Treat every layout-review finding as a delivery failure. Reposition or resize elements, re-render, and repeat the review until it is clean. Then visually check the preview for issues that geometry cannot reliably infer: crowded hierarchy, labels that are hard to scan, arrows that obscure meaning, long text in shapes, and excessive empty space. Read [references/quality-gate.md](references/quality-gate.md) for the complete checks.
5. Return the `.excalidraw` file first. Also return its SVG preview when it helps the user review the result. Explain that the `.excalidraw` file can be opened and edited at [Excalidraw](https://excalidraw.com/).

Keep output local by default. Do not upload a scene, generate a public web link, or claim that the chat contains a live Excalidraw widget unless the available environment explicitly provides that integration.

## Optional interactive Excalidraw MCP

When an Excalidraw MCP server is actually exposed (for example, `excalidraw-local`), use it for collaborative in-chat sketching, streamed previews, and fullscreen editing. Follow the server's schema and checkpoint instructions; do not assume that an MCP server is configured.

Pair the optional MCP with this skill rather than treating it as a replacement:

1. Use MCP for visible, iterative diagram development when the user benefits from reviewing the canvas in chat.
2. Create or update the local `.excalidraw` scene when the user needs a durable, portable artifact.
3. Generate the local SVG preview and complete structural and layout review before delivery.

MCP-only work is appropriate for a quick interactive whiteboard. For a file handoff, proposal attachment, or repeatable artifact, retain the local scene and quality-gate workflow.

## Spec format

Read [references/format.md](references/format.md) before creating a spec or directly editing a scene. This is the minimal input format:

```json
{
  "title": "Checkout flow",
  "direction": "LR",
  "nodes": [
    {"id": "buyer", "label": "Buyer"},
    {"id": "store", "label": "Storefront", "group": "Customer experience"},
    {"id": "payment", "label": "Payment API", "group": "Platform"}
  ],
  "edges": [
    {"from": "buyer", "to": "store", "label": "places order"},
    {"from": "store", "to": "payment", "label": "authorizes"}
  ]
}
```

Use `direction: "LR"` for short sequences and `"TB"` for layered systems. The generator also accepts a top-level `groups` list for explicit grouped regions. Prefer short labels; place detail in a nearby note or a supporting document instead of cramming it into a node.

## Editing an existing scene

1. Parse the supplied `.excalidraw` JSON and preserve unfamiliar top-level fields, `files`, and elements outside the requested change.
2. Keep element IDs stable whenever an element is being changed rather than replaced. Update `version` and `versionNonce` for edited elements.
3. Modify bindings when adding, removing, or replacing an arrow or container label. Do not leave a text element pointing at a deleted container.
4. Create a refreshed SVG preview and validate it:

```bash
SKILL_DIR=.agents/skills/excalidraw-diagrams
python3 "$SKILL_DIR/scripts/render_preview.py" revised.excalidraw revised-preview.svg
python3 "$SKILL_DIR/scripts/validate_scene.py" revised.excalidraw
```

For a follow-up request that refers to the previous generated diagram, use `scripts/session_state.py show`. Only save state with `session_state.py save` when continuity across turns is useful; state contains a local copy of the scene and optional source spec.

## Scripts

- `scripts/generate_excalidraw.py`: Turn the supported node-and-edge spec into an editable scene and optional SVG preview.
- `scripts/render_preview.py`: Render an SVG preview from any local Excalidraw scene that uses basic shapes, arrows, and text.
- `scripts/validate_scene.py`: Check scene structure, IDs, bindings, dimensions, and likely-unreadable labels.
- `scripts/review_layout.py`: Flag overlapping peer elements, text collisions or spill, arrow-through-node collisions, and tightly packed elements. Run it with `--strict` before delivery.
- `scripts/session_state.py`: Save or retrieve one local latest-diagram record for incremental revisions.

The generator is intentionally a fast path for diagrams that can be represented as nodes and edges. For a spatial, editorial, map-like, swimlane, or custom-composed request, author the scene directly while following the format and quality references rather than forcing it into a generic layout.
