# Excalidraw authoring format

## Generator input

`generate_excalidraw.py` accepts a JSON object with these fields:

| Field | Required | Description |
| --- | --- | --- |
| `title` | No | Short title placed above the diagram. |
| `direction` | No | `LR` (default) or `TB`. |
| `nodes` | Yes | Objects with unique `id`, non-empty `label`, and optional `group`, `color`, or `fill`. |
| `edges` | No | Objects with `from`, `to`, and optional `label` or `color`. |
| `groups` | No | Objects with `id` or `label`, `label`, optional `nodes`, `color`, and `fill`. |

Use `nodes[].group` for the common case. Add a `groups` entry only when the group needs a custom title or palette.

## Direct scene edits

An editable `.excalidraw` file is JSON with `type: "excalidraw"` and an `elements` list. Keep unknown fields unchanged. Every element needs a unique `id`, `type`, position, dimensions, `version`, and `versionNonce`.

- Use `rectangle` for components and light group boundaries.
- Use `text` for labels. Keep `containerId` aligned with the related shape when the text labels a component.
- Use `arrow` with at least two relative `points`; update `startBinding` and `endBinding` if either endpoint changes.
- Keep a container's `boundElements` list aligned with bound label and arrow IDs.
- Increment `version` and change `versionNonce` when changing an existing element.

Do not delete or regenerate `files` entries unless the requested change affects those files. This local renderer intentionally focuses on ordinary vector shapes and may not preview embedded images or advanced Excalidraw element types exactly.
