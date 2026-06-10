---
name: oci-opportunity-coach
description: Prepare OCI reps and sales engineers for customer opportunities by turning a single account, an Excel/CSV list of accounts, customer notes, CRM context, meeting transcripts, public research, key decision maker research, champion/persona target research, or user-approved Sales Navigator context into account research profiles, executive summaries, stakeholder profiles, champion maps, OCI pursuit hypotheses, account-tailored OCI buying-objection prep, stakeholder maps, outreach campaigns, discovery plans, mutual action plans, CRM summaries, and handoffs to OCI deck, diagram, BOM, or technical skills.
---

# OCI Opportunity Coach

## Overview

Use this skill as the front door for OCI opportunity strategy. It helps reps and Sales Engineers decide what to say, ask, build, or send before generating a deck, architecture, BOM, or technical briefing.

This skill is for messy early and mid-stage sales context: partial notes, a named account, a spreadsheet of target accounts, a meeting transcript, a renewal or migration motion, an executive sponsor request, a competitor displacement opportunity, or a request like "help me prep for this account."

## Use Cases

Use this skill for:

- account and meeting preparation
- comprehensive account research from one account or an Excel/CSV account list
- discovery call plans
- opportunity qualification and deal hypotheses
- stakeholder maps and missing-role analysis
- named stakeholder, key decision maker, and technical influencer research
- non-executive champion and persona target discovery for product, engineering, platform, data, security, SRE, architecture, and operations campaigns
- account-tailored customer objection prep for concerns against buying OCI
- executive one-pagers and outreach campaign kits
- mutual action plans
- follow-up emails and CRM summaries
- SE handoff briefs
- artifact routing into OCI sales decks, technical decks, architecture diagrams, or BOMs
- Sales Navigator assisted account or lead research after explicit user confirmation

Do not use this skill as the final authoring workflow for PowerPoint decks, OCI diagrams, or cost estimates. Use it to shape the opportunity and then hand off to the right sibling skill.

## Core Rules

- Separate `known`, `assumed`, and `recommended` in every customer-facing or field-facing output.
- For account research, separate `publicly verified`, `Sales Navigator context`, `CRM/internal context`, `estimated`, `assumed`, and `not found in available sources`.
- For current company facts, financials, leadership, partnerships, cloud/AI signals, social posts, and tech-stack clues, browse or use current source material and cite sources with as-of dates.
- For cloud-provider posture, use job postings, hiring pages, engineering blogs, public resumes/employee skill aggregates, certifications, and LinkedIn/Sales Navigator skill signals to infer AWS/Azure/GCP/OCI/private-cloud likelihood. Label this as `inferred`, include evidence, confidence, and counter-signals.
- For personalized outreach and decision-maker research, profile relevant named executives, technical leaders, product leaders, platform/cloud owners, security/data leaders, and known CRM contacts using public web, company pages, company technical blogs, public professional profiles, public posts, and user-approved LinkedIn/Sales Navigator lead context. Use only professional opportunity-relevant information, label sources, and do not infer sensitive personal attributes.
- For product/engineering campaigns, identify named non-executive champion candidates as well as senior leaders. Inspect relevant open jobs and individual public or approved Sales Navigator lead profiles for engineers, product managers, architects, platform/cloud owners, SRE/DevOps, data/AI, database, security, and operations personas. Record how many job postings, employee profiles, Sales Navigator lead profiles, and technical posts were checked.
- Do not invent pricing, discounts, OCI commitments, region availability, customer priorities, stakeholder intent, or competitor details.
- Ask only the smallest useful set of follow-up questions, usually `1-3`, when missing information would materially change the recommendation. For account research or account-list research, ask the required validation block before starting.
- Keep outputs practical for field use: concise, specific, and tied to a next customer action.
- Treat CRM notes, meeting transcripts, Sales Navigator pages, and account data as sensitive customer context.
- Do not leave Oracle contract, license, renewal, opportunity, account-owner, CRM-match, or internal relationship fields blank when they are visible in user-authorized internal, CRM, Oracle, or Sales Navigator surfaces. Capture every visible relevant field, label the source and as-of/access date, and use `not found in available sources` only when the field was actually checked and not visible.
- For comprehensive account research, deliver final output files as DOCX and PDF, plus the required `account-research.json` sidecar in each per-account folder and the root `account-research-visualizer.html` for account-list outputs. Do not place Markdown, CSV, XLSX, raw browser captures, screenshots, or text exports in the delivered output folder unless the user explicitly requests those extra formats.
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
   - account research profile
   - account list research from Excel/CSV
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
3. For account research from a named account or account spreadsheet, read [references/account-research.md](references/account-research.md) and ask the validation questions there before beginning research.
   - If the user provides an Excel or CSV account list, use the spreadsheet/xlsx workflow first to inspect headers, row count, account names, domains, and any notes before normalizing the research queue.
   - If the user wants file outputs, recommend the default folder structure from `references/account-research.md` unless they specify another location.
4. If Sales Navigator is relevant and has not already been confirmed for this specific task, ask the Sales Navigator confirmation question from `Core Rules` before opening, reading, or extracting page context.
   - If Account IQ `Generate insights` would materially improve the output, ask the separate Generate insights confirmation before clicking it.
5. Build a quick opportunity frame:
   - customer and industry
   - likely business pressure
   - current technology posture
   - opportunity stage
   - target workload or initiative
   - stakeholders and missing roles
   - known constraints such as security, compliance, region, incumbent platform, timeline, or budget
6. For comprehensive account research or outreach, build stakeholder profiles before writing emails:
   - identify the likely buying committee and technical influencers
   - research each named person from public and approved LinkedIn/Sales Navigator sources
   - identify non-executive champion candidates and persona targets who can influence technical validation, introduce workload context, or become internal advocates
   - inspect current open roles for persona, skill, cloud, database, AI, security, and platform signals
   - open individual employee/lead profiles for the finite target set when public or approved, rather than relying only on account-level people lists
   - use company technical blogs and employee-authored posts to understand technical priorities
   - tie each personalized email to a specific profile insight, source category, and OCI wedge
7. Choose the output shape:
   - for comprehensive account research, read [references/account-research.md](references/account-research.md)
   - for role-based questions, read [references/discovery-plays.md](references/discovery-plays.md)
   - for account briefs, mutual action plans, follow-ups, and CRM summaries, read [references/output-templates.md](references/output-templates.md)
   - for Sales Navigator usage, read [references/sales-navigator.md](references/sales-navigator.md)
   - for handoffs to sibling skills, read [references/artifact-routing.md](references/artifact-routing.md)
8. Create the field-ready output with:
   - the deal hypothesis
   - what to validate next
   - recommended discovery questions
   - stakeholder view
   - next best action
   - artifact handoff when appropriate
   - for account-list file outputs, run `scripts/build_account_research_visualizer.py <output-root>` after every per-account `account-research.json` sidecar exists
9. If a downstream artifact is needed, route to the sibling skill rather than drafting that artifact inside this skill.

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
- `Champion/persona map`: named non-executive campaign targets and likely technical champions when outreach is requested
- `Next best action`: one concrete customer-facing move
- `Artifact handoff`: which OCI skill should be used next, with a short brief

For comprehensive account research, deliver the package described in [references/account-research.md](references/account-research.md): a full research profile, one-page executive summary, source log, scorecard, outreach kit, stakeholder profiles, champion/persona target pack, OCI buying-objection prep, the `account-research.json` app-import sidecar, and the account-list HTML visualizer when multiple accounts are researched.

## Sales Engineering Guardrails

- Lead with customer outcomes before OCI services.
- Translate service features into buyer language such as risk reduction, speed, security posture, operational simplicity, performance, data gravity, or economics.
- Keep the rep and SE roles distinct: reps own commercial motion and stakeholder alignment; SEs own technical validation, architecture, and proof.
- Make the recommended next step executable in a real sales cycle.
- Avoid generic discovery checklists. Tailor questions to the account, role, workload, and stage.
- Surface risks early: unclear champion, missing economic buyer, no compelling event, unvalidated workload fit, security blocker, pricing uncertainty, or weak migration path.
- Keep competitor positioning tied to the customer's stated priorities.
- Treat OCI buying-objection prep as Oracle internal field preparation: make likely customer concerns explicit, tailor them to account evidence, and pair each inferred concern with validation questions and proof to prepare.
- Do not turn objection prep into discount guidance, concession strategy, or unsupported claims about private customer sentiment.

## Sibling Skill Routing

- Use [../oci-sales-decks/SKILL.md](../oci-sales-decks/SKILL.md) for executive briefings, solution recommendation decks, workshop readouts, POV proposals, and competitive positioning decks.
- Use [../oci-technical-decks/SKILL.md](../oci-technical-decks/SKILL.md) for service deep dives, technical briefings, workshops, or field enablement.
- Use [../oci-architecture-generator/SKILL.md](../oci-architecture-generator/SKILL.md) for editable draw.io OCI architecture diagrams.
- Use [../oci-architecture-powerpoint-generator/SKILL.md](../oci-architecture-powerpoint-generator/SKILL.md) for PowerPoint-native OCI architecture slides.
- Use [../oci-bom-generator/SKILL.md](../oci-bom-generator/SKILL.md) for OCI BOMs, assumptions, and cost-estimator inputs.

## Resources

- [references/account-research.md](references/account-research.md): comprehensive account research workflow, validation questions, source plan, directory structure, research fields, scoring, and outreach deliverables.
- [references/discovery-plays.md](references/discovery-plays.md): role-based discovery questions and qualification prompts.
- [references/output-templates.md](references/output-templates.md): concise account brief, mutual action plan, follow-up, CRM update, and SE handoff templates.
- [references/sales-navigator.md](references/sales-navigator.md): gated Sales Navigator workflow and safety rules.
- [references/artifact-routing.md](references/artifact-routing.md): when to hand off to OCI decks, diagrams, BOMs, and technical skills.
