---
name: oci-opportunity-coach
description: Prepare OCI reps and sales engineers for customer opportunities by turning customer notes, CRM context, meeting transcripts, public account research, or user-approved Sales Navigator context into account briefs, discovery plans, deal hypotheses, stakeholder maps, mutual action plans, follow-up messages, CRM summaries, and handoffs to OCI deck, diagram, BOM, or technical skills.
---

# OCI Opportunity Coach

## Overview

Use this skill as the front door for OCI opportunity strategy. It helps reps and Sales Engineers decide what to say, ask, build, or send before generating a deck, architecture, BOM, or technical briefing.

This skill is for messy early and mid-stage sales context: partial notes, a named account, a meeting transcript, a renewal or migration motion, an executive sponsor request, a competitor displacement opportunity, or a request like "help me prep for this account."

## Use Cases

Use this skill for:

- account and meeting preparation
- discovery call plans
- opportunity qualification and deal hypotheses
- stakeholder maps and missing-role analysis
- mutual action plans
- follow-up emails and CRM summaries
- SE handoff briefs
- artifact routing into OCI sales decks, technical decks, architecture diagrams, or BOMs
- Sales Navigator assisted account or lead research after explicit user confirmation

Do not use this skill as the final authoring workflow for PowerPoint decks, OCI diagrams, or cost estimates. Use it to shape the opportunity and then hand off to the right sibling skill.

## Core Rules

- Separate `known`, `assumed`, and `recommended` in every customer-facing or field-facing output.
- Do not invent pricing, discounts, OCI commitments, region availability, customer priorities, stakeholder intent, or competitor details.
- Ask only the smallest useful set of follow-up questions, usually `1-3`, when missing information would materially change the recommendation.
- Keep outputs practical for field use: concise, specific, and tied to a next customer action.
- Treat CRM notes, meeting transcripts, Sales Navigator pages, and account data as sensitive customer context.
- Before reading or using Sales Navigator for a specific account, lead, list, or search, ask the user to confirm:
  `Do you want me to look at Sales Navigator for <account or objective> and use visible account or lead context to prepare this output?`
- Before clicking Sales Navigator Account IQ `Generate insights`, ask a separate action-specific confirmation unless the user already explicitly requested generated insights for that same account and objective:
  `Do you want me to click Generate insights in Sales Navigator for <account> and use the generated Account IQ guidance in this output?`
- Do not bulk scrape Sales Navigator, automate outreach, export broad lead lists, dismiss alerts, save leads/accounts, or change lists unless the user explicitly asks and the browser confirmation policy allows it.
- If Sales Navigator content is used, identify it as Sales Navigator context and do not present it as independently verified public fact.
- If generated Account IQ guidance is used, identify it as `Sales Navigator generated insight` and convert it into hypotheses and discovery questions rather than treating it as verified fact.
- Confirm before transmitting sensitive customer or personal data to third-party sites, forms, messages, or uploads.

## Workflow

1. Identify the request:
   - account brief
   - discovery plan
   - meeting prep
   - deal strategy
   - stakeholder map
   - mutual action plan
   - follow-up or CRM update
   - SE handoff
   - artifact recommendation
2. Identify the available source context:
   - user-provided account notes
   - CRM or opportunity notes
   - meeting transcript
   - public research
   - Sales Navigator context
   - prior deck, architecture, BOM, or email thread
3. If Sales Navigator is relevant and has not already been confirmed for this specific task, ask the Sales Navigator confirmation question from `Core Rules` before opening, reading, or extracting page context.
   - If Account IQ `Generate insights` would materially improve the output, ask the separate Generate insights confirmation before clicking it.
4. Build a quick opportunity frame:
   - customer and industry
   - likely business pressure
   - current technology posture
   - opportunity stage
   - target workload or initiative
   - stakeholders and missing roles
   - known constraints such as security, compliance, region, incumbent platform, timeline, or budget
5. Choose the output shape:
   - for role-based questions, read [references/discovery-plays.md](references/discovery-plays.md)
   - for account briefs, mutual action plans, follow-ups, and CRM summaries, read [references/output-templates.md](references/output-templates.md)
   - for Sales Navigator usage, read [references/sales-navigator.md](references/sales-navigator.md)
   - for handoffs to sibling skills, read [references/artifact-routing.md](references/artifact-routing.md)
6. Create the field-ready output with:
   - the deal hypothesis
   - what to validate next
   - recommended discovery questions
   - stakeholder view
   - next best action
   - artifact handoff when appropriate
7. If a downstream artifact is needed, route to the sibling skill rather than drafting that artifact inside this skill.

## Opportunity Frame

Every opportunity should reduce to these questions:

- Why change: what pressure makes the current state unacceptable?
- Why now: what event, deadline, renewal, risk, or executive goal creates urgency?
- Why OCI: what OCI advantage matters for this workload or buyer?
- Why this path: what sequence reduces risk and helps the customer decide?
- Who decides: what stakeholders are involved, missing, supportive, or blocking?
- What proof is needed: architecture, economics, migration plan, POV, security review, or executive narrative?

## Output Contract

Default to a concise field brief unless the user asks for a longer plan.

Include:

- `Situation`: what is known about the account or opportunity
- `Deal hypothesis`: the most likely value story and OCI fit
- `Validation needed`: what must be confirmed before committing to a recommendation
- `Discovery plan`: role-specific questions for the next meeting
- `Stakeholder map`: known roles, missing roles, and likely concerns
- `Next best action`: one concrete customer-facing move
- `Artifact handoff`: which OCI skill should be used next, with a short brief

## Sales Engineering Guardrails

- Lead with customer outcomes before OCI services.
- Translate service features into buyer language such as risk reduction, speed, security posture, operational simplicity, performance, data gravity, or economics.
- Keep the rep and SE roles distinct: reps own commercial motion and stakeholder alignment; SEs own technical validation, architecture, and proof.
- Make the recommended next step executable in a real sales cycle.
- Avoid generic discovery checklists. Tailor questions to the account, role, workload, and stage.
- Surface risks early: unclear champion, missing economic buyer, no compelling event, unvalidated workload fit, security blocker, pricing uncertainty, or weak migration path.
- Keep competitor positioning tied to the customer's stated priorities.

## Sibling Skill Routing

- Use [../oci-sales-decks/SKILL.md](../oci-sales-decks/SKILL.md) for executive briefings, solution recommendation decks, workshop readouts, POV proposals, and competitive positioning decks.
- Use [../oci-technical-decks/SKILL.md](../oci-technical-decks/SKILL.md) for service deep dives, technical briefings, workshops, or field enablement.
- Use [../oci-architecture-generator/SKILL.md](../oci-architecture-generator/SKILL.md) for editable draw.io OCI architecture diagrams.
- Use [../oci-architecture-powerpoint-generator/SKILL.md](../oci-architecture-powerpoint-generator/SKILL.md) for PowerPoint-native OCI architecture slides.
- Use [../oci-bom-generator/SKILL.md](../oci-bom-generator/SKILL.md) for OCI BOMs, assumptions, and cost-estimator inputs.

## Resources

- [references/discovery-plays.md](references/discovery-plays.md): role-based discovery questions and qualification prompts.
- [references/output-templates.md](references/output-templates.md): concise account brief, mutual action plan, follow-up, CRM update, and SE handoff templates.
- [references/sales-navigator.md](references/sales-navigator.md): gated Sales Navigator workflow and safety rules.
- [references/artifact-routing.md](references/artifact-routing.md): when to hand off to OCI decks, diagrams, BOMs, and technical skills.
