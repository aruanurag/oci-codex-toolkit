# OCI Draw.io Diagram Spec

Use this JSON contract when you want the skill to render a finished `.drawio` file with `scripts/render_oci_drawio.py`.

## Top-Level Shape

```json
{
  "title": "Architecture name",
  "pages": [
    {
      "name": "Logical - Example",
      "page_type": "logical",
      "width": 1800,
      "height": 1100,
      "elements": []
    }
  ]
}
```

## Page Fields

- `name`: draw.io page name.
- `page_type`: `logical` or `physical`. This controls icon resolution and default connector style.
- `width`: optional page width. Default is `1600`.
- `height`: optional page height. Default is `900`.
- `elements`: ordered page content. Put background grouping shapes first, then service icons, then edges.

## Element Types

### Library Elements

Use for OCI groupings, service icons, and special connectors.

```json
{
  "id": "oke",
  "query": "OKE",
  "x": 250,
  "y": 500,
  "w": 150,
  "h": 115,
  "external_label": "Regional OKE"
}
```

Supported fields:

- `id`: optional stable reference for later edges or relative positioning.
- `query`: preferred input. The renderer resolves this through `scripts/resolve_oci_icon.py`.
- `icon_title`: use when you already know the exact Oracle icon title.
- `x`, `y`, `w`, `h`: placement and size.
- `size_policy`: optional. Use `native` only when you intentionally want the raw OCI toolkit size. When omitted, service icons normalize to a common max dimension while grouping shapes and special connectors keep their native sizing.
- `parent`: optional coordinate reference to a previously placed element. This offsets `x` and `y` relative to that element's top-left corner. It does not create XML nesting.
- `label`: plain-text internal label override when the Oracle snippet has exactly one text cell.
- `value`: raw HTML label override for the first Oracle text cell. Use this for VCNs, subnets, and formatted group labels.
- `text_values`: ordered raw HTML overrides for snippets that have multiple text cells.
- `external_label`: renders a separate Oracle Sans text box below the icon.
- `hide_internal_label`: optional boolean. When `true`, blanks the snippet's built-in text cells.
- `preserve_internal_label`: optional boolean. When `true`, keeps the built-in snippet text even if `external_label` is present.

Fallback behavior is automatic:

1. direct official icon
2. trusted alias
3. logical generic icon when the page is logical
4. placeholder shape when no honest official mapping exists for a physical component

On physical diagrams, prefer explicit VCN and subnet groupings with CIDR labels, and place public and private resources inside the appropriate subnet boxes.

Sizing notes:

- If you omit both `w` and `h` for a service icon, the renderer normalizes it to the skill's default icon box.
- If you provide only one of `w` or `h`, the renderer preserves the icon's aspect ratio automatically.
- Grouping shapes and special connectors keep their native dimensions unless you override them.

### Text Elements

```json
{
  "type": "text",
  "x": 420,
  "y": 70,
  "w": 300,
  "h": 24,
  "text": "Primary Region"
}
```

Supported fields:

- `text`: plain text by default.
- `html`: set to `true` if the text value already contains draw.io HTML.
- `style`: optional draw.io style suffix to append.

### Placeholder Shapes

```json
{
  "type": "shape",
  "shape": "ellipse",
  "x": 90,
  "y": 175,
  "w": 140,
  "h": 70,
  "label": "Analyst Users"
}
```

Supported placeholder shapes:

- `rounded-rectangle`
- `cylinder`
- `hexagon`
- `cloud`
- `ellipse`

Additional supported fields:

- `style`: optional draw.io style suffix to append. Use this when a placeholder needs a more specific Oracle-like stroke, fill, or rounding treatment.

Use an explicit `type: "shape"` entry when you already know the bundled OCI assets do not contain an honest direct icon for that component. This avoids pretending that a `query` resolves to an official icon when the correct result should really be a placeholder.

Hidden routing anchors also use `type: "shape"`, usually with a tiny `rounded-rectangle` and a fully transparent style:

```json
{
  "id": "app-subnet-egress-anchor",
  "type": "shape",
  "shape": "rounded-rectangle",
  "x": 359,
  "y": 169,
  "w": 2,
  "h": 2,
  "label": "",
  "style": "rounded=0;arcSize=0;fillColor=none;strokeColor=none;dashed=0;"
}
```

Use hidden anchors as routing primitives on subnet, VCN, tier, or region boundaries. Name them with an `-anchor` suffix and place them directly on the boundary you want the connector to visibly meet. The renderer treats these as anchors rather than placeholder shapes.

For boundary-attached OCI network controls such as `Internet Gateway`, `NAT Gateway`, and `Service Gateway`, prefer placing the icon directly on the relevant subnet or VCN border instead of drawing a short connector line into that same boundary. Use an explicit edge only when the gateway participates in a larger traffic lane that must be shown.

When a container stands for an OKE cluster, place the official `Container Engine for Kubernetes` icon in the container header area or as a container badge. Treat it as the cluster's identifying icon, not as a separate floating service node disconnected from the container. When the icon is being used purely as a badge, set `hide_internal_label: true` so the snippet text does not render as a second pseudo-node label.

### Edges

```json
{
  "type": "edge",
  "source": "waf",
  "target": "oke",
  "connector": "logical-dataflow",
  "label": "HTTPS",
  "source_anchor": "bottom",
  "target_anchor": "top"
}
```

Supported edge fields:

- `source`: required element `id`.
- `target`: required element `id`.
- `connector`: `physical`, `logical-dataflow`, or `logical-user`.
- `label`: optional connector label.
- `style`: optional draw.io style suffix to append for manual routing or display tweaks.
- `source_anchor`: `left`, `right`, `top`, or `bottom`.
- `target_anchor`: `left`, `right`, `top`, or `bottom`.
- `waypoints`: optional list of `[x, y]` pairs or `{"x": ..., "y": ...}` objects.

For traffic-flow arrows on physical diagrams, use anchors and waypoints deliberately to reserve clean lanes. Do not accept a route that looks detached, overlaps another major arrow, forces the label through a boundary or icon, or relies on an uncontrolled diagonal segment.

When a physical edge crosses a container boundary:

- route the connector to a hidden boundary anchor first
- bridge across lanes with anchor-to-anchor segments when needed
- use `style: "endArrow=none;"` on intermediate segments
- keep the visible arrowhead only on the final segment into the destination workload
- treat a connector that only almost reaches a boundary or icon as incorrect

## Recommended Workflow

1. Resolve icon uncertainty with `scripts/resolve_oci_icon.py`.
2. Author the JSON spec.
3. Render the final diagram and quality-check it:

```bash
python3 scripts/render_oci_drawio.py \
  --spec assets/examples/specs/multi-region-oke-saas.json \
  --output /tmp/multi-region-oke-saas.drawio \
  --report-out /tmp/multi-region-oke-saas.report.json \
  --quality-out /tmp/multi-region-oke-saas.quality.json \
  --fail-on-quality
```

4. Validate with `scripts/test_render_oci_drawio.py` or `validate_drawio_file(...)`.
5. If the quality review fails, fix the spec and rerender until it passes.
6. After the first passing quality review, do one more rerender and require a second passing quality review before delivery.
7. Export the physical page to PNG and do at least one final visual confirmatory pass focused on arrowheads, traffic-flow routing, boundary attachment, icon sizing, and label collisions.

## Bundled Examples

- `assets/examples/specs/multi-region-oke-saas.json`
- `assets/examples/specs/oke-genai-rag.json`
- `assets/examples/specs/mushop-oke-ecommerce.json`
- `assets/examples/specs/oke-multidatabase-modern-app.json`
