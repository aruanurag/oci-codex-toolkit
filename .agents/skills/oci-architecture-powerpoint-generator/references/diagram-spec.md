# OCI PowerPoint Diagram Spec

Use this JSON contract when you want the skill to render a finalized `.pptx` with `scripts/render_oci_powerpoint.py`.

## Top-Level Shape

```json
{
  "title": "Architecture name",
  "pages": [
    {
      "name": "Physical - Example",
      "page_type": "physical",
      "width": 1600,
      "height": 900,
      "elements": []
    }
  ]
}
```

Each `page` becomes one PowerPoint slide.

## Page Fields

- `name`: slide name used in reports.
- `page_type`: currently `physical`.
- `width`: optional logical canvas width. Default is `1600`.
- `height`: optional logical canvas height. Default is `900`.
- `elements`: ordered slide content. Put grouping elements first, then service icons, then edges.

## Library Elements

Use `query` or `icon_title` for OCI PowerPoint library entries.

```json
{
  "id": "oke",
  "query": "OKE",
  "x": 700,
  "y": 360,
  "w": 150,
  "h": 110,
  "external_label": "Application Cluster"
}
```

Supported fields:

- `id`: stable reference for later edges.
- `query`: preferred icon lookup input.
- `icon_title`: use when you already know the exact PowerPoint catalog title.
- `x`, `y`, `w`, `h`: element placement.
- `parent`: optional parent element id for relative coordinates.
- `boundary_parent`: optional element id whose border this element should be mounted on.
- `boundary_side`: optional side of `boundary_parent`: `left`, `right`, `top`, or `bottom`.
- `boundary_align`: optional alignment along that side: `start`, `center`, or `end`. Defaults to `center`.
- `boundary_align_to`: optional element id whose midpoint should drive placement along the chosen boundary.
- `value`: label override for grouping elements such as VCNs or subnets. Basic HTML like `<b>` and `<br/>` is stripped into plain text.
- `label`: plain-text internal label override.
- `external_label`: preferred service label override. The renderer replaces the native icon-group label when possible instead of adding a detached label.
- `hide_internal_label`: blank the copied native label.

Typical gateway pattern:

```json
{
  "id": "igw",
  "query": "internet gateway",
  "parent": "region",
  "boundary_parent": "vcn",
  "boundary_side": "right",
  "y": 110,
  "w": 95,
  "h": 78
}
```

Keep the gateway parent wide enough to contain the icon, such as the region, while using `boundary_parent` to mount it on the VCN border.

## Text Elements

```json
{
  "type": "text",
  "x": 40,
  "y": 40,
  "w": 320,
  "h": 24,
  "text": "Primary Region",
  "style": "align=left;fontSize=18;fontStyle=1;"
}
```

The `style` field supports a small useful subset:

- `align=left|center|right`
- `fontSize=<number>`
- `fontStyle=1` for bold

Single-line `text` elements are automatically rendered with `wrap="none"` and PowerPoint auto-fit so short headings stay on one line when possible. If a heading still feels crowded, shorten it before increasing complexity elsewhere.

## Placeholder Shapes

```json
{
  "id": "clients",
  "type": "shape",
  "shape": "ellipse",
  "x": 80,
  "y": 320,
  "w": 90,
  "h": 90,
  "label": "Clients"
}
```

Supported `shape` values:

- `rounded-rectangle`
- `ellipse`
- `hexagon`
- `cloud`
- `cylinder`

Use `style` when you need simple overrides such as:

- `fillColor=#FCFBFA`
- `strokeColor=#9E9892`
- `strokeWidth=2`
- `dashed=1`
- `fontSize=11`
- `fontStyle=1`

Hidden routing anchors also use `type: "shape"` with a transparent style and an id ending in `-anchor`. The renderer keeps them in geometry calculations without rendering them visibly.

## Edges

```json
{
  "type": "edge",
  "source": "browser",
  "target": "lb",
  "label": "HTTPS",
  "source_anchor": "right",
  "target_anchor": "left",
  "waypoints": [[240, 380], [240, 300], [820, 300]]
}
```

Supported fields:

- `source`: required element id.
- `target`: required element id.
- `label`: optional connector label.
- `semantic`: optional flow intent hint such as `publish`, `fanout`, `enqueue`, `consume`, `request`, or `read`. The renderer defaults async publish-style semantics to dashed lines when no explicit `style.dashed` override is supplied.
- `source_anchor`: `left`, `right`, `top`, or `bottom`.
- `target_anchor`: `left`, `right`, `top`, or `bottom`.
- `waypoints`: optional explicit route control points.
- `style`: optional subset currently used for:
  - `endArrow=none`
  - `dashed=1`

The renderer orthogonalizes explicit waypoint routes so the final connector stays vertical and horizontal only.

Connector labels render in transparent text boxes by default. Keep labels short enough to stay single-line when possible.
Avoid manual `waypoints` unless they materially improve the route. The renderer will prefer the simpler automatic orthogonal route when explicit waypoints add unnecessary bends.
When two connector families move in opposite directions, prefer using `semantic` so publish/fanout/enqueue lines can be dashed while consume/request/read lines remain solid.
When a topology repeats paired stages such as queues and consumers, align those rows or columns symmetrically before fine-tuning connector routes.

## Recommended Workflow

1. Resolve icon uncertainty with `scripts/resolve_oci_powerpoint_icon.py`.
2. Author the JSON slide spec.
3. Render the `.pptx`:

```bash
python3 scripts/render_oci_powerpoint.py \
  --spec assets/examples/specs/simple-three-tier-oci-adb.json \
  --output output/simple-three-tier-oci-adb.pptx \
  --report-out output/simple-three-tier-oci-adb.report.json \
  --quality-out output/simple-three-tier-oci-adb.quality.json \
  --fail-on-quality
```

4. Export a preview image and inspect it visually. Prefer `python3 scripts/export_powerpoint_preview.py --input output/...pptx --image-out /tmp/...png`.
5. If quality issues or visual issues remain, fix the spec and rerender.
