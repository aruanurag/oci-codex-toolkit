# Artifact Routing

Use this guide after the opportunity frame is clear.

## No Artifact Yet

Recommend more discovery when:

- no target workload is named
- no business outcome is known
- the economic buyer or champion is missing
- the customer only asked for a generic overview
- the next meeting should validate pain, urgency, or ownership first

Output: discovery plan, stakeholder map, and next best action.

## Sales Deck

Use `oci-sales-decks` when the customer needs:

- executive briefing
- solution recommendation
- workshop readout
- POV or POC proposal
- competitive positioning
- migration or modernization narrative

Handoff should include audience, desired decision, known pain, workload, OCI thesis, proof needed, assumptions, risks, and next step.

## Technical Deck

Use `oci-technical-decks` when the customer needs:

- service deep dive
- technical briefing
- workshop lesson
- comparison or decision deck for architects
- mechanism-led explanation of OCI capabilities

Handoff should include technical question, audience depth, constraints, required services, and whether the material must be customer-safe or internal.

## Architecture Diagram

Use `oci-architecture-generator` for editable draw.io diagrams or `oci-architecture-powerpoint-generator` for PowerPoint-native architecture slides when:

- workload scope is clear enough to diagram
- network, security, database, application, or DR boundaries matter
- the next meeting needs architecture alignment

Handoff should include workload, region or deployment model, components, users, integrations, data flows, security boundaries, and open decisions.

## BOM Or Cost Estimate

Use `oci-bom-generator` when:

- the customer has a scoped workload or architecture
- sizing assumptions can be stated and confirmed
- the next decision depends on economics

Handoff should include region, currency, hours per month, compute, storage, database, network, backup, support, traffic, and any assumptions that need user confirmation before pricing.

## Combined Motion

For mature opportunities, recommend a sequence instead of one artifact:

1. Discovery plan to validate the workload and buying committee.
2. Architecture workshop to define target state.
3. BOM assumptions gate to align sizing.
4. Executive recommendation deck to drive the decision.
