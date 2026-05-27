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

## Account Research Profile

Use the full workflow in [account-research.md](account-research.md) when the user asks for comprehensive account research. Keep this template as the content shape for `01-comprehensive-profile.docx` and `01-comprehensive-profile.pdf`.

```markdown
# Account Research Profile: <Account>

## Executive Snapshot
<120 words or fewer.>

## Known, Estimated, Assumed, Not Found
| Category | Items |
|---|---|
| Publicly verified |  |
| Sales Navigator context |  |
| CRM/internal context |  |
| Estimated |  |
| Assumed |  |
| Not found in available sources | Use only after checking the available public, Sales Navigator, CRM/internal, and user-provided sources |
| Needs user-authorized internal source | Use for likely internal-only fields not visible in the approved source set |

## Business Overview
- What they do:
- Products and services:
- Primary industries/customers:
- Competitors:
- Growth and financial health:
- Global footprint:

## Leadership And Buying Centers
| Leader/role | Tenure | Relevant experience | Public priorities | Oracle relationship signal |
|---|---|---|---|---|

## Stakeholder And Key Employee Profiles
| Person | Role | Buying-committee role | Profile insight | Technical/OCI signal | Email angle | Source/confidence |
|---|---|---|---|---|---|---|

## Company Technical Blog And Employee Content Signals
- Relevant technical blogs/posts:
- Authors or teams to watch:
- Architecture/cloud/data/AI/security signals:
- Outreach implications:

## Tech Stack And Cloud Posture
- Current cloud providers:
- GTM/product cloud partnerships:
- AI strategy:
- VMware/on-prem/colo:
- Oracle apps/licenses/databases:
- Contract and renewal dates:

## OCI Pursuit Hypotheses
| Motion | Evidence | Assumption | 90-day plan | Stakeholders |
|---|---|---|---|---|

## Workload Finder
| Workload | Current platform | OCI equivalent | Pattern | Score | Why |
|---|---|---|---|---:|---|

## Validation Needed
-

## Six-Bullet Executive Summary
-
-
-
-
-
-
```

## Executive One-Pager

```markdown
# Executive One-Pager: <Account>

## Why This Account
<Short account-specific reason.>

## Most Likely OCI Wedge
<Wedge workload or motion.>

## Business Pressure
-

## Technology Signals
-

## Scorecard
| Score | Go/Watch/Hold | Confidence | Reason |
|---:|---|---|---|

## Recommended Next Move
<One customer-facing move.>
```

## Outreach Kit

```markdown
# Outreach Kit: <Account>

## Personalized Executive Messages
| Person | Role | Profile insight | Source/confidence | OCI wedge | Message |
|---|---|---|---|---|---|

## Product/Engineering Campaign
| Persona | Named targets | Technical signal | Theme | Message |
|---|---|---|---|---|

## Named Champion / Persona Targets
| Person | Role/title | Persona | Why this person | Evidence/source | Champion-read | Email angle | First ask |
|---|---|---|---|---|---|---|---|

## Research-Linked Personalization Map
| Person/persona | Sourced insight | Why it matters | Email ask | What to validate |
|---|---|---|---|---|

## Research Coverage Audit
| Source type | Count inspected | Notes / gaps |
|---|---:|---|
| Open job postings |  |  |
| Individual public employee/profile pages |  |  |
| Sales Navigator lead profiles |  |  |
| Technical blog posts/docs/GitHub/talks |  |  |
| Account-level pages only |  | Use this row to clarify when research did not include individual-level inspection |

## First-Touch Email
Subject: <subject>

Hi <name>,

<130-160 words tailored to the stakeholder profile, wedge workload, and timing lever. Use one professional, sourced profile insight or team technical signal.>

## Discovery Questions
1.
2.
3.
4.
5.
6.
7.
8.

## Objection Handles
| Objection | Handle |
|---|---|
| Migration risk |  |
| Unit prices |  |
| Developer preference for incumbent |  |
| Database untouchable |  |
```

## Stakeholder Profile Pack

Use this template for `05-stakeholder-profiles.docx` and `05-stakeholder-profiles.pdf`.

```markdown
# Stakeholder Profiles: <Account>

## Stakeholder Coverage
| Role coverage | Status | Gap or next step |
|---|---|---|
| Economic buyer |  |  |
| CIO/CTO/cloud/platform |  |  |
| CISO/security |  |  |
| Data/AI/database |  |  |
| Product/engineering |  |  |
| Procurement/finance |  |  |
| Known Oracle/CRM contacts |  |  |

## Individual Profiles
| Person | Current role | Buying-committee role | Background | Public priorities | Technical signals | Likely objection | Personalization hook | Source/confidence |
|---|---|---|---|---|---|---|---|---|

## Email Angles By Person
| Person | Best message theme | OCI motion | Specific ask | Research gap to validate |
|---|---|---|---|---|

## Technical Blog / Employee Content Findings
| Source | Author/team | Signal | Relevant stakeholders | Outreach implication |
|---|---|---|---|---|
```

## Champion And Persona Target Pack

Use this template for `06-champion-persona-targets.docx` and `06-champion-persona-targets.pdf`.

```markdown
# Champion And Persona Targets: <Account>

## Coverage Summary
| Research surface | Count inspected | Confidence impact |
|---|---:|---|
| Current open jobs |  |  |
| Individual public profiles |  |  |
| Sales Navigator lead profiles |  |  |
| Technical blogs/docs/talks/GitHub |  |  |

## Job Posting Signals
| Job title | Team/function | Source | Cloud/provider signal | Data/AI/security signal | Persona | OCI discovery question |
|---|---|---|---|---|---|---|

## Named Champion Candidates
| Person | Role/title | Persona | Level | Workload proximity | Relationship path | Technical evidence | Champion-read | Email angle | First ask |
|---|---|---|---|---|---|---|---|---|---|

## Persona Campaign Plan
| Persona | Named targets | Message theme | Relevant OCI motion | Proof to offer | Success metric |
|---|---|---|---|---|---|

## Gaps And Next Searches
| Gap | Why it matters | Next search/action |
|---|---|---|
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
