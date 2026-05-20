# Sales Navigator Workflow

Use Sales Navigator only when it materially improves the opportunity output and the user has confirmed the specific use.

## Confirmation Gate

Before opening, reading, searching, or extracting Sales Navigator context, ask:

```text
Do you want me to look at Sales Navigator for <account or objective> and use visible account or lead context to prepare this output?
```

Proceed only after the user confirms. A prior login or an open Sales Navigator tab is not confirmation for a new account, lead, list, or search.

## Generate Insights Gate

Account IQ `Generate insights` is a separate action. Before clicking it, ask:

```text
Do you want me to click Generate insights in Sales Navigator for <account> and use the generated Account IQ guidance in this output?
```

Proceed only after the user confirms, unless the user's current prompt already explicitly asks to generate Account IQ insights for that same account and objective. After generation, summarize the result as `Sales Navigator generated insight`, not as independently verified fact.

## Allowed Uses After Confirmation

- read the visible Sales Navigator home, account, lead, or Account IQ page for the named task
- use visible account descriptions, alerts, relationship signals, buyer intent surfaces, and saved account context to shape discovery
- identify possible stakeholder roles when the user asks for lead or account research
- summarize Sales Navigator-derived context as `Sales Navigator context`, not as verified public fact
- click Account IQ `Generate insights` after the separate Generate insights confirmation and use the resulting guidance as hypotheses

## Avoid Unless Explicitly Requested And Confirmed

- saving leads or accounts
- changing lists
- dismissing alerts
- providing feedback on generated Account IQ insights
- sending InMails or messages
- exporting, copying, or reconstructing broad lead lists
- scraping many pages or collecting personal data unrelated to the named opportunity
- using Sales Navigator content to populate external systems without confirmation

## Reading Pattern

1. Confirm the named account, lead, or objective.
2. Read only the smallest relevant page area.
3. If Account IQ generated guidance would help, confirm before clicking `Generate insights`.
4. Capture high-level signals, not exhaustive personal data.
5. Mark each Sales Navigator-derived point as `Sales Navigator context`.
6. Mark generated Account IQ output as `Sales Navigator generated insight`.
7. Convert signals into questions, hypotheses, and next actions.

## Good Sales Navigator Signals

- account growth, hiring, or leadership change
- recent account activity or buyer intent
- named personas who match the buying committee
- alerts that indicate cloud, data, security, AI, migration, or cost pressure
- Account IQ themes that suggest business challenges or strategic priorities
- generated Account IQ ways that OCI may help the account, after confirmation

## Output Language

Prefer:

- `Sales Navigator context suggests...`
- `Sales Navigator generated insight suggests...`
- `Visible account signals point to...`
- `This should be validated with the customer...`

Avoid:

- presenting inferred priorities as confirmed facts
- listing unnecessary personal details
- claiming that Sales Navigator AI summaries or generated insights are independently verified
