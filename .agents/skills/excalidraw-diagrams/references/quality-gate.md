# Diagram quality gate

Before delivery, verify all of the following:

- The diagram conveys one primary story that can be understood at a glance.
- Node labels are short, readable, and do not overlap arrows or other labels.
- Every arrow has an obvious source, destination, and direction.
- Group boundaries clarify ownership, layer, or flow; they are not decorative boxes.
- Related nodes align on a consistent grid and whitespace is balanced.
- Colors distinguish meaning sparingly and retain high label contrast.
- The SVG preview is visually inspected, not just generated successfully.
- The final `.excalidraw` file passes `validate_scene.py` with no errors.

## Crowding and collision review

Run `scripts/review_layout.py <scene> --strict` before delivery. Treat each finding as a failure, then reposition or resize the affected elements and repeat the review.

- Do not allow peer nodes, free text, or notes to overlap. Bound labels may overlap only their own container.
- Do not route an arrow through a node that is not its source or destination.
- Leave clear whitespace between peer elements; do not compress labels and arrows simply to reduce canvas size.
- Prefer horizontal and vertical connectors. Use a diagonal only when an orthogonal route would add an unnecessary elbow or weaken the overall alignment.
- Visually inspect the SVG after the automated pass. Resolve clipped labels, near-misses, tangled arrow paths, visual imbalance, and anything that makes the primary story harder to scan.

For technical diagrams, make trust boundaries, external actors, ingress, primary processing, and durable data stores visually distinct when they matter to the explanation. Avoid inventing security controls or production guarantees that the source requirements do not establish.
