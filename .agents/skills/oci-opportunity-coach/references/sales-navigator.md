# Sales Navigator Workflow

Use Sales Navigator only when it materially improves the opportunity output and the user has confirmed the specific use.

For account-list research, confirmation must cover the named list or account set. Do not treat permission for one account as permission for every account in a spreadsheet unless the user explicitly approves that list scope.

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

For a spreadsheet of accounts, ask whether `Generate insights` should be used for each approved account, only a pilot subset, or not at all.

## Allowed Uses After Confirmation

- read the visible Sales Navigator home, account, lead, or Account IQ page for the named task
- use visible account descriptions, alerts, relationship signals, buyer intent surfaces, and saved account context to shape discovery
- identify possible stakeholder roles, buying-committee members, and technical influencers when the user asks for lead or account research
- read visible lead profiles for the approved named account, named stakeholders, or approved account set and capture professional opportunity-relevant context
- search for a finite set of product, engineering, platform, cloud, SRE/DevOps, data/AI, database, security, architecture, operations, procurement, or finance personas for the approved account when building campaigns
- identify named non-executive champion candidates from approved lead searches, relationship explorer, technical content authors, and persona searches
- capture public-facing executive themes, buyer personas, professional posts/activity visible in Sales Navigator, relationship signals, and account alerts relevant to the named account or approved account set
- capture visible CRM match, account owner, opportunity summary, website/location, relationship, and internal-account snippets when the user has authorized Sales Navigator/CRM context for the task
- summarize Sales Navigator-derived context as `Sales Navigator context`, not as verified public fact
- summarize CRM-linked snippets as `CRM/internal context`, not as public fact
- click Account IQ `Generate insights` after the separate Generate insights confirmation and use the resulting guidance as hypotheses

## Avoid Unless Explicitly Requested And Confirmed

- saving leads or accounts
- changing lists
- dismissing alerts
- providing feedback on generated Account IQ insights
- sending InMails or messages
- exporting, copying, or reconstructing broad lead lists
- scraping broad lead populations or collecting personal data unrelated to the named opportunity
- treating account-level `Key people`, headcount, or relationship explorer snippets as a substitute for inspecting the individual lead/profile pages needed for a true champion/persona pass
- using Sales Navigator content to populate external systems without confirmation

## Reading Pattern

1. Confirm the named account, lead, or objective.
2. For stakeholder or champion research, identify the finite approved set of named people, roles, or likely buying-committee/persona searches before opening lead profiles.
3. If Account IQ generated guidance would help, confirm before clicking `Generate insights`.
4. Read only the smallest relevant page areas needed for the account and approved lead profiles.
5. Capture all visible account-level, lead-level, and opportunity-relevant signals, including CRM/internal snippets when authorized. Avoid unrelated personal data.
6. Mark each Sales Navigator-derived point as `Sales Navigator context`.
7. Mark generated Account IQ output as `Sales Navigator generated insight`.
8. Mark CRM-linked values as `CRM/internal context`.
9. Count how many account pages, lead searches, and individual lead profiles were inspected.
10. Convert signals into stakeholder profiles, champion candidate maps, questions, hypotheses, personalized email angles, and next actions.

## Good Sales Navigator Signals

- account growth, hiring, or leadership change
- recent account activity or buyer intent
- named personas who match the buying committee
- named leaders, technical decision makers, influencers, and known relationship contacts
- named non-executive champion candidates such as staff/principal engineers, engineering managers, product managers, architects, SRE/DevOps leads, data/AI leads, database leaders, and security architects
- visible professional posts, role descriptions, tenure, prior company context, or skill patterns that explain how to approach a stakeholder
- TeamLink, mutual connections, follows Oracle, CRM marker, recent posts, recent promotions, technical authorship, or role proximity to the top OCI motion
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
- implying that a stakeholder has pain, intent, or budget without evidence
- implying a person is a champion unless the output labels it as a `champion-read` hypothesis with evidence and confidence
