# Output Templates

Keep visible outputs short enough for a rep or SE to use immediately.

## Account Brief

```markdown
## Account Brief: <Customer>

### Situation
- Known:
- Assumed:
- Open:

### Deal Hypothesis
<One paragraph explaining why change, why now, and why OCI may fit.>

### Likely Buyer Priorities
- 
- 
- 

### What To Validate Next
- 
- 
- 

### Discovery Plan
1. <Role>: <question>
2. <Role>: <question>
3. <Role>: <question>

### Stakeholder Map
| Role | Person or team | Current read | Next move |
|---|---|---|---|
| Champion | Unknown | Missing | Identify owner for workload pain |
| Economic buyer | Unknown | Missing | Ask who funds the initiative |

### Next Best Action
<One concrete customer-facing action.>

### Artifact Handoff
<Recommended sibling skill and the brief it should receive.>
```

## Mutual Action Plan

```markdown
## Mutual Action Plan

| Step | Owner | Outcome | Due | Exit criteria |
|---|---|---|---|---|
| Confirm workload scope | Customer app owner + SE | Named first workload | <date> | Scope includes users, data, dependencies, and success metric |
| Architecture workshop | SE + customer architect | Target pattern and risks | <date> | Agreed logical architecture and open decisions |
| Cost assumptions review | Rep + SE + finance buyer | Validated sizing assumptions | <date> | BOM assumptions confirmed before pricing |
| Decision readout | Rep + economic buyer | Go or no-go on next phase | <date> | Decision criteria and next step documented |
```

## SE Handoff Brief

```markdown
## SE Handoff

### Customer Objective
<What the customer is trying to accomplish.>

### Current Understanding
- Workload:
- Current platform:
- Pain:
- Timeline:
- Stakeholders:
- Constraints:

### Technical Unknowns
- 
- 

### Recommended SE Action
<Discovery, workshop, architecture, estimate, security review, or POV plan.>

### Artifact Needed
<Deck, diagram, BOM, technical briefing, or none yet.>
```

## Follow-Up Email

```markdown
Subject: Next steps on <initiative>

Hi <name>,

Thank you for the conversation today. My read is that the priority is <outcome>, with the first area of focus around <workload or decision>.

To keep momentum, I suggest we use the next session to confirm:

- <decision point 1>
- <decision point 2>
- <decision point 3>

After that, we can provide <artifact or recommendation> that maps the recommended OCI path to your success criteria.

Best,
<sender>
```

## CRM Summary

```markdown
Customer is exploring <initiative/workload>. Known drivers: <drivers>. Current blockers or unknowns: <unknowns>. Next step: <meeting/action> with <stakeholders> by <date>. Recommended internal action: <SE handoff/artifact/qualification step>.
```
