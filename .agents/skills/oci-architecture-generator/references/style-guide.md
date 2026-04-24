# OCI Draw.io Style Guide

This reference distills the Oracle-provided files bundled in `assets/drawio/`.

## Source Files

- `assets/drawio/oci-style-guide-readme.drawio`
- `assets/drawio/oci-architecture-toolkit-v24.2.drawio`
- `assets/drawio/oci-library.xml`

## Non-Negotiables

- Use Oracle-provided OCI icons and grouping shapes first.
- Do not use pink or Courier New in final diagrams. Oracle uses those only for instructional callouts inside the source files.
- Default to physical diagrams only. Add a logical view only when the user explicitly asks for one.
- Treat example pages as layout guidance. The toolkit explicitly says the examples are not always complete or technically correct.
- Keep iterating until connectors look attached, readable, and non-overlapping in a visual export.
- Treat broken-looking traffic arrows, arrowheads that seem detached, and labels colliding with arrows as blockers.

## Oracle Asset Usage

- Use `oci-architecture-toolkit-v24.2.drawio` as the primary visual source.
- Use `oci-library.xml` as the machine-readable library for scripted icon lookup.
- Remember that the toolkit is newer than the standalone library. The local catalog merges the library titles with a curated supplement for newer toolkit-only icons.

## Planning And Clarification

- Before drafting the actual diagram, do a short plan pass.
- Always ask 2 to 4 targeted clarification questions before authoring unless the user explicitly waives questions or the current thread already answered them.
- Treat regional vs AD-specific subnet scope as a layout-affecting input for OCI networked workloads.
- Treat symmetry and stage-alignment preferences as layout-affecting inputs when the topology is staged, mirrored, or fanout-based.
- Treat icon uncertainty as a blocker when it could make the diagram misleading.

## Logical Diagram Guidance

Use logical pages only when the user explicitly requests them.

Use logical pages for conceptual system flow and responsibility boundaries.

- Use location canvases for Oracle Cloud, On-Premises, Internet, and 3rd Party Cloud.
- Use logical components for OCI, Oracle on-premises, and third-party systems.
- Use atomic or composite component shapes when the system needs drill-down views.
- Use the logical connector styles for user interaction and data flow.
- Prefer official generic logical components over plain geometry when the element is conceptual and no direct service icon exists.

## Physical Diagram Guidance

Use physical pages for deployable infrastructure layout.

- Use grouping shapes for Tenancy, Compartment, OCI Region, Availability Domain, Fault Domain, VCN, Subnet, Tier, and User Group.
- Use special connector shapes for FastConnect, Site-to-site VPN, and Remote Peering.
- Use service icons for OCI products and managed services.
- Use public and private subnet boundaries with CIDR labels on networked workloads.
- Default OCI subnet boundaries to regional scope unless the user explicitly requests AD-specific subnets.
- Attach `Internet Gateway`, `NAT Gateway`, and `Service Gateway` to the VCN edge by default, even when subnet boundaries are also shown. Let the VCN border line pass through the gateway icon center instead of leaving the icon fully inside the VCN.
- Keep public-facing resources inside public subnets and application or data tiers inside private subnets.
- For single-region multi-AD HA, let one regional subnet span the ADs by default and show AD placement with the official Oracle `Availability Domain` grouping shapes as tall vertical containers inside the VCN, while the regional subnets span horizontally across them. Match the Oracle HA sample treatment rather than drawing one subnet per AD.
- Add extra private subnets for data, cache, or observability tiers when that reduces crowding and makes the network clearer.
- In HA layouts, leave a visible left-side label gutter so subnet names and CIDRs stay readable before the AD grouping columns begin.
- Increase the canvas and route connectors with waypoints before letting lines pile up on top of each other.
- Keep icon labels close to the icon by default. Only open up extra vertical gap when a multi-line label or crossing connector needs the room.
- Reserve dedicated traffic lanes when multiple arrows traverse the same area of the page.
- Keep mirrored or repeated stages visually balanced. When queue and consumer tiers repeat, align them symmetrically before hand-tuning connectors.
- Treat shared or nearly collinear lanes between different semantic flows as overlaps even if the automated quality checker does not flag them.
- Represent one flow as one visible connector. Use waypointed routes and tiny hidden attach anchors instead of splitting the same relationship into several stitched connector objects.
- Do not let a connector visually sit on top of a VCN, subnet, or dashed workload-container border. Use a dedicated lane instead of sharing the boundary line.
- Do not layer standalone `Route Table` or `Security List` icons on top of subnet groupings that already render those markers on the subnet boundary. Duplicate `RT` or `SL` visuals are blockers.
- If a direct connector into a service icon makes the arrowhead kink, tilt, or stop awkwardly near the destination, use a tiny invisible attach anchor on the service boundary so the visible connector still reads as one clean machine-routed line.
- Export the physical page and inspect it visually. If any route looks detached, ambiguous, broken by labels, or unnecessarily overlapped, reroute and rerender.
- Prefer more whitespace and clearer attachment points over compactness.
- Use geometry placeholders only when there is no direct OCI icon.

## Fallback Policy

Apply this order:

1. Direct official icon.
2. Official icon reached through a trusted alias, such as `OKE`, `ADW`, or `DRG`.
3. Approved closest official fallback icon when the local skill documents a known physical catalog gap and the fallback is disclosed in the mapping table.
4. Official generic logical component when the page is logical and the element is clearly OCI, Oracle on-premises, or third-party.
5. Closest similar placeholder shape with a clear label when the page is physical and no OCI icon or approved official fallback exists.
6. Mention the closest official OCI icon considered only in notes when it would otherwise be ambiguous.

## Placeholder Shapes

Use the simplest honest placeholder:

- `rounded-rectangle` for generic applications, compute nodes, services, and middleware.
- `cylinder` for databases, warehouses, data lakes, and storage-like data services.
- `hexagon` for network and security controls.
- `cloud` for external SaaS or generic cloud services.
- `ellipse` for people or user actors.

Choose the shape that is closest to the missing component's role, not just the first generic shape that fits.
Prefix the label with `PLACEHOLDER:` when the diagram itself needs to signal the fallback directly.
