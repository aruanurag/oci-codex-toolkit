# Account Research Workflow

Use this reference when the user asks for full account research, account profiling, OCI pursuit research, target account prioritization, or research across an Excel/CSV list of accounts.

## Start Here: Validation Questions

Before researching, ask a compact validation block. Do not ask every possible question; include the ones that affect execution.

Required unless already answered:

1. `Where do you want me to save the output? Recommended: <cwd>/output/account-research/<YYYY-MM-DD>/ with one folder per account.`
2. `Is the input a single account or an Excel/CSV list? If it is a spreadsheet, should I research every row or only a named segment/sample first?`
3. `Are you logged in to LinkedIn Sales Navigator, and do you want me to use visible Sales Navigator account/lead context for this research?`
4. `Do you want me to click Sales Navigator Account IQ Generate insights for each approved account?`
5. `Do you want me to capture every visible Oracle, CRM, contract, license, renewal, opportunity, owner, and relationship field from the internal sources you authorize?`
6. `Do you want me to research key decision makers, technical stakeholders, and non-executive champion candidates across public web, open jobs, public LinkedIn/profile pages, company technical blogs, and approved Sales Navigator lead context?`
7. `Do you want me to inspect individual employee profiles and open job postings for product/engineering campaign personas, not just account-level company pages?`
8. `Do you want the default DOCX and PDF package, or a custom DOCX/PDF layout?`

Recommended defaults when the user says to proceed without more detail:

- Output root: `<cwd>/output/account-research/<YYYY-MM-DD>/`
- Account folder name: `<account-slug>/`
- Research all rows for lists of 10 or fewer accounts; for larger lists, process a 3-account pilot first and ask before scaling.
- Create DOCX/PDF deliverables, including `07-oci-buying-objection-prep.docx` and `.pdf`, the required `account-research.json` sidecar in each per-account folder, and `account-research-visualizer.html` at the research root for account-list outputs. Do not deliver Markdown, CSV, XLSX, or raw data files unless the user explicitly asks for additional machine-readable exports.
- Capture all visible/user-authorized Oracle, CRM, contract, license, renewal, opportunity, owner, and relationship fields; mark a field `not found in available sources` only after checking the available source set.
- Research named key decision makers, technical stakeholders, likely buying-committee members, and non-executive champion candidates when outreach is requested.
- For account lists, default to 6-12 executive/stakeholder profiles plus 8-15 champion/persona targets per account unless the user provides named targets or asks for a deeper pass.
- Inspect open jobs for the target account before finalizing cloud-provider inference or product/engineering campaigns. For larger companies, inspect up to 20 relevant current roles per account across cloud/platform, SRE/DevOps, data/AI, database, product, security, and architecture personas; if fewer are available, record the actual count checked.
- Open individual public or approved Sales Navigator lead/profile pages for the finite campaign target set. Do not rely only on account-level `Key people`, title lists, or aggregated headcount signals.
- Use public web research by default, with sources and as-of dates.

## No Empty Field Rule

Do not leave research fields blank. For every requested field:

- fill it from public, Sales Navigator, CRM/internal, or user-provided sources when visible
- label the source category and as-of/access date
- use `not found in available sources` when checked but unavailable
- use `needs user-authorized internal source` when the field likely exists internally but no authorized source was provided
- use `not applicable` only when the field does not apply to the account

Do not infer Oracle contracts, license posture, renewal dates, discounts, opportunities, or relationship strength from public guesses. Use authorized internal or CRM-visible values when available; otherwise mark the field using the statuses above.

## Input Handling

For a single account:

- Confirm the legal/company name, website domain, headquarters, and any known opportunity context.
- If there are multiple companies with similar names, resolve identity before research.

For Excel/CSV account lists:

- Inspect workbook/sheet names, headers, row count, account names, domains, owner fields, region, segment, notes, and duplicates.
- Normalize account names and domains into a research queue.
- Preserve the user's original file. Write normalized working files only under the output root.
- Create `account-research-index.docx` and `account-research-index.pdf` summarizing research status, score, go/watch/hold, top wedge, and confidence.

## Directory Structure

Use this structure unless the user asks for another layout:

```text
output/account-research/<YYYY-MM-DD>/
  account-research-index.docx
  account-research-index.pdf
  sources-master.docx
  sources-master.pdf
  account-research-visualizer.html
  <account-slug>/
    00-source-log.docx
    00-source-log.pdf
    01-comprehensive-profile.docx
    01-comprehensive-profile.pdf
    02-executive-one-pager.docx
    02-executive-one-pager.pdf
    03-oci-pursuit-scorecard.docx
    03-oci-pursuit-scorecard.pdf
    04-outreach-kit.docx
    04-outreach-kit.pdf
    05-stakeholder-profiles.docx
    05-stakeholder-profiles.pdf
    06-champion-persona-targets.docx
    06-champion-persona-targets.pdf
    07-oci-buying-objection-prep.docx
    07-oci-buying-objection-prep.pdf
    account-research-pack.docx
    account-research-pack.pdf
    account-research.json
```

For a single account, the same per-account folder is enough; add root index DOCX/PDF only if useful.

For account-list research, the per-account directories are mandatory. A consolidated
all-account brief, rollup, or index may be added at the root for convenience, but it
must not replace the `<account-slug>/` folders or the per-account DOCX/PDF outputs.
If time or source access limits require a reduced deliverable, still create one
folder per account with at least `account-research-pack.docx`,
`account-research-pack.pdf`, `00-source-log.docx`, and `00-source-log.pdf`, and
record any omitted sections inside the pack.

When a spreadsheet contains duplicate or near-duplicate account names, preserve the
row-level account context instead of merging them silently. Disambiguate the folder
name with the source row number or another stable identifier, such as
`006-bentley-systems-inc/` and `007-bentley-systems-inc/`.

Depth parity gate: per-account files must contain substantive research, not thin
shells around a single Sales Navigator snippet. Before delivery, compare a sample
account pack against the required research fields below and any prior user-approved
example pack. Each `01-comprehensive-profile` and `account-research-pack` should
include, when available or explicitly marked not found: executive snapshot,
business/products, industries/customers, competitors, growth/financial health,
leadership/buying centers, stakeholder profiles, technical/employee signals,
cloud-provider inference, tech-stack posture, cloud-spend estimate, workload
finder, OCI pursuit hypotheses, scorecard, contract/timing levers, discovery plan,
executive summary, OCI buying-objection prep, and source log. If those sections
cannot be researched yet, label the pack as a draft and do not present it as the
final comprehensive package.

When the user asks for another review, a missing-insights check, or a more detailed
pass after an initial account-list package, perform a second-pass insight audit
instead of only reformatting the same material. Refresh the approved Sales
Navigator account context when available, review public company/news/investor/job
or official pages for each account, filter noisy or wrong-entity matches, and add
a `Second-Pass Insight Review` section to each comprehensive profile and account
pack with refreshed Sales Navigator signals, public-source signals, source rows
checked, and remaining validation gaps.

## Output File Rule

Final research output files must be `.docx` or `.pdf`, with two required exceptions: each per-account folder must include `account-research.json` for Meeting Memory import, and account-list research roots must include `account-research-visualizer.html`.

- Do not save Markdown, CSV, TXT, XLSX, screenshots, raw browser captures, or raw Sales Navigator exports into the delivered output folder unless the user explicitly asks for those formats.
- If structured working data is useful during execution, keep it transient or outside the final deliverable tree.
- If the user asks for a spreadsheet or extra machine-readable export beyond `account-research.json` and `account-research-visualizer.html`, ask whether to add it as an exception before creating extra non-DOCX/PDF files.
- The source log, account index, scorecard, outreach kit, stakeholder profiles, champion/persona target pack, OCI buying-objection prep, one-pager, and comprehensive profile should all be delivered as DOCX/PDF.

## Meeting Memory JSON Sidecar

Create `account-research.json` in every per-account folder. It is the machine-readable import contract for the Meeting Memory app and must contain only facts, estimates, assumptions, validation gaps, and not-found values already represented in the written research pack.

Use these top-level fields:

```json
{
  "skill_name": "oci-opportunity-coach",
  "research_date": "YYYY-MM-DD",
  "source_folder": "<account-folder-name>",
  "account_name": "<legal or display account name>",
  "account_slug": "<normalized account slug>",
  "executive_snapshot": "",
  "business_overview": {},
  "leadership_buying_centers": [],
  "stakeholders": [],
  "technology_signals": [],
  "tech_stack_cloud_posture": {},
  "oci_pursuit_hypotheses": [],
  "workload_finder": [],
  "scorecard": {},
  "oci_buying_objection_prep": {
    "summary": "",
    "top_objections": [],
    "objection_inventory": [],
    "discovery_questions": [],
    "proof_to_prepare": [],
    "stakeholders_to_engage": [],
    "next_actions": [],
    "source_notes": []
  },
  "recommended_next_move": "",
  "validation_needed": [],
  "source_log": [],
  "artifacts": {
    "source_log_docx": "00-source-log.docx",
    "source_log_pdf": "00-source-log.pdf",
    "comprehensive_profile_docx": "01-comprehensive-profile.docx",
    "comprehensive_profile_pdf": "01-comprehensive-profile.pdf",
    "executive_one_pager_docx": "02-executive-one-pager.docx",
    "executive_one_pager_pdf": "02-executive-one-pager.pdf",
    "scorecard_docx": "03-oci-pursuit-scorecard.docx",
    "scorecard_pdf": "03-oci-pursuit-scorecard.pdf",
    "outreach_kit_docx": "04-outreach-kit.docx",
    "outreach_kit_pdf": "04-outreach-kit.pdf",
    "stakeholder_profiles_docx": "05-stakeholder-profiles.docx",
    "stakeholder_profiles_pdf": "05-stakeholder-profiles.pdf",
    "champion_persona_targets_docx": "06-champion-persona-targets.docx",
    "champion_persona_targets_pdf": "06-champion-persona-targets.pdf",
    "oci_buying_objection_prep_docx": "07-oci-buying-objection-prep.docx",
    "oci_buying_objection_prep_pdf": "07-oci-buying-objection-prep.pdf",
    "research_pack_docx": "account-research-pack.docx",
    "research_pack_pdf": "account-research-pack.pdf"
  }
}
```

The JSON may use strings, arrays, or objects for research sections, but it must remain valid JSON, preserve source-category labels, and avoid adding claims that are not in the DOCX/PDF package.

Each `oci_buying_objection_prep.objection_inventory` object should use these fields:

```json
{
  "objection": "",
  "category": "",
  "customer_language": "",
  "account_specific_trigger": "",
  "evidence_source": "",
  "confidence": "",
  "likely_speaker": "",
  "impact": "",
  "discovery_questions": [],
  "response_strategy": "",
  "proof_to_prepare": [],
  "risk_if_unresolved": "",
  "next_best_action": ""
}
```

## Account Research HTML Visualizer

For account-list research, create `account-research-visualizer.html` at the research root after every per-account `account-research.json` sidecar is present.

Generate it with the bundled script:

```bash
python3 .agents/skills/oci-opportunity-coach/scripts/build_account_research_visualizer.py output/account-research/<YYYY-MM-DD>
```

The visualizer must:

- be a self-contained static HTML file that opens directly from disk without a web server
- embed the sidecar data instead of fetching local JSON files at runtime
- show a searchable and sortable account list with score, disposition, top OCI wedge, buyer intent, and revenue/employee signal when available
- open a detail view for the selected account with tabs for overview, business, leadership, stakeholders, technology, OCI motion, objections, scorecard, sources, and files
- include a files tab with relative links to the DOCX/PDF artifacts and PDF previews when the browser can render them
- preserve source labels and validation gaps from the sidecars, and avoid adding research claims not already represented in the written package or `account-research.json`

## Research Sources

Use public, verifiable, current sources and record the as-of date for each major claim. Prefer primary sources first.

Primary and high-confidence sources:

- company website, product pages, leadership pages, trust/security pages
- annual reports, 10-K/20-F, 10-Q, proxy statements, investor presentations, earnings calls, credit ratings
- official press releases, customer case studies, partner pages, documentation, status pages
- public cloud marketplace listings and official partner announcements
- job postings and engineering blogs when inferring cloud, AI, data, security, or VMware signals
- company leadership pages, management bios, board pages, and public executive interviews
- company technical blogs, engineering blogs, developer pages, architecture posts, and employee-authored technical content
- company career sites, Greenhouse/Lever/Workday/Ashby postings, LinkedIn jobs, and public job descriptions for relevant current roles

Useful secondary sources:

- reputable business and trade press
- analyst reports when accessible
- employee-authored engineering blogs, conference talks, podcasts, GitHub, Medium, Substack, and public technical posts
- public procurement, government contract, patent, or litigation records when relevant
- open job postings, hiring pages, public employee skill/certification signals, and LinkedIn/Sales Navigator skill or headcount patterns for cloud-provider inference
- public LinkedIn/profile pages and visible Sales Navigator lead profiles after confirmation, used only for professional, opportunity-relevant context
- individual public professional profiles, approved Sales Navigator lead profiles, conference speakers, GitHub authors, blog authors, patent authors, docs contributors, and open-source maintainers who map to target campaign personas

Use Sales Navigator only after confirmation. Label it as `Sales Navigator context`. Generated Account IQ output must be labeled `Sales Navigator generated insight`.

## Research Profile Fields

Every comprehensive account profile should include:

- Executive snapshot: 120 words or fewer.
- Core business: what the company does, products/services, best-selling or strategically important products when visible, revenue contribution when public.
- Customer and industry footprint: primary industries served, biggest customers if public, geography, global deployment, buying centers.
- Competitive landscape: direct competitors, substitute approaches, and ecosystem partners.
- Growth and financial health: growing/stagnant/declining, revenue, profitability, cash/debt signals, major acquisitions/divestitures, risks. Use public financials when available; mark private-company estimates clearly.
- Leadership: CEO, CFO, CIO/CTO/CISO/product/operations leaders when relevant; tenure, prior experience, public priorities, and any public Oracle relationships or Oracle-linked career history. Do not infer private relationships.
- Stakeholder and key employee profiles: named decision makers, technical influencers, platform/cloud/data/security/product leaders, known CRM contacts, role in buying committee, professional priorities, public posts/interviews, technical signals, likely objections, and outreach personalization hooks.
- Champion and persona target map: named non-executive employees who match the outreach personas, why each might help, their technical domain, relationship path, champion-read, email angle, and source confidence.
- Research coverage audit: counts of open jobs inspected, individual employee/profile pages opened, Sales Navigator lead profiles opened, technical blog posts/docs inspected, and gaps that limited confidence.
- Current cloud and infrastructure posture: AWS, Azure, GCP, OCI, private cloud, colo, data centers, edge, SaaS platform dependencies, deeper GTM/product partnerships, and cloud-provider inference from jobs/employee skills.
- Tech stack signals: AI strategy, VMware, Oracle apps/licenses, Oracle Database, Microsoft SQL Server, mainframe, storage platforms, DR posture, security/compliance drivers.
- Contract and renewal timing: public, Sales Navigator, CRM/internal, user-provided, or inferred renewal cliffs for cloud commits, Oracle contracts/licenses, VMware ELAs, database support, colo leases, storage refreshes, and hardware EOLs. If a date or field is not visible, write `not found in available sources` or `needs user-authorized internal source`.
- OCI buying-objection prep: account-specific concerns the customer may raise against buying OCI products, why each concern is plausible, discovery questions, response strategy, proof to prepare, likely speaker, risk if unresolved, and next best action.
- 10-K/annual report and financial-report findings: strategic priorities, risk factors, capex/opex, cloud/software spend language, AI/data/security mentions, supply chain or operational pressure.
- Employee-authored technical content: blogs, Substacks, conference talks, GitHub, patents, or papers that reveal architectural direction.

## Cloud Spend And Infrastructure Estimates

When the user asks for spend estimates, provide defensible triangulation, not false precision.

Include:

- Estimated annual cloud spend by provider: AWS, Azure, GCP, OCI, and other/unknown.
- Estimated spend by category: compute, storage, database, networking/egress, data/analytics, AI/GPU, managed services, support/TAM.
- On-prem/colo intensity signals: owned data centers, colo providers and locations, VMware estate, storage arrays, Oracle/MS SQL footprint, mainframe, DR, refresh/EOL notes.
- Four-quarter trend when visible; otherwise explain why it is not visible.
- Confidence for every numeric estimate: high, medium, low.
- Method: briefly state the triangulation logic, such as revenue scale, employee count, digital product intensity, job-posting signals, known cloud partnerships, public infrastructure statements, or comparable companies.

Do not present estimates as verified spend unless a public source explicitly supports them.

## Cloud Provider Inference From Jobs And Skills

Use open roles and employee skill signals to make a provider hypothesis when direct disclosure is unavailable. Never present this as confirmed provider usage unless the source explicitly says so.

Collect signals from:

- current engineering, SRE, DevOps, platform, security, data, AI/ML, database, and cloud architect job postings
- public hiring pages and role descriptions that mention cloud services, certifications, IaC, Kubernetes, data platforms, or managed databases
- engineering blogs, conference talks, GitHub repos, public docs, status pages, and architecture posts
- public employee skill aggregates and visible LinkedIn/Sales Navigator profile patterns when authorized
- partner listings, marketplace listings, procurement notices, and customer case studies

Classify each provider as:

| Confidence | Meaning |
|---|---|
| High | Multiple current roles or official docs mention provider-specific services, certifications, or architecture. |
| Medium | Repeated provider-specific skills appear across roles/employee signals, but no official architecture confirmation. |
| Low | Weak or old references, generic cloud language, or single-role evidence. |
| Not found | Checked available sources and found no usable provider signal. |

Provider-specific examples:

- AWS: EC2, EKS, ECS, Lambda, S3, RDS, Redshift, Glue, Athena, IAM, CloudWatch, Kinesis, SageMaker, Bedrock, AWS GovCloud, AWS Marketplace, AWS certification requirements.
- Azure: AKS, Functions, App Service, Blob Storage, SQL Database, Synapse, Fabric, Event Hubs, Entra ID, Monitor, Azure OpenAI, Azure DevOps, Microsoft/Azure certification requirements.
- GCP: GKE, Cloud Run, Compute Engine, BigQuery, Cloud Storage, Pub/Sub, Dataflow, Vertex AI, Looker, Apigee, GCP certification requirements.
- OCI: OKE, OCI Compute, Object Storage, Autonomous Database, Exadata, MySQL HeatWave, OCI AI Infrastructure, GoldenGate, FastConnect, Oracle Database or Oracle Cloud certification requirements.
- Private cloud/VMware/colo: vSphere, ESXi, vCenter, NSX, vSAN, Tanzu, OpenShift on-prem, Nutanix, bare metal, data center operations, colo provider names, storage arrays, backup/DR appliances.

Output a provider inference table:

| Provider | Confidence | Evidence | Counter-signals | What to validate |
|---|---|---|---|---|

Use this inference in cloud spend and OCI motion selection, but keep it separate from verified cloud-provider disclosures.

## Stakeholder And Decision-Maker Research

Build stakeholder profiles before writing personalized emails. The goal is to understand each person well enough to make outreach specific, useful, and grounded in professional context.

Identify stakeholders from:

- company leadership and management pages
- LinkedIn public pages and Sales Navigator lead lists after confirmation
- CRM/internal contacts and relationship maps when authorized
- annual reports, proxy statements, investor events, interviews, webinars, podcasts, and conference talks
- company technical blogs, engineering posts, product blogs, developer docs, GitHub, patents, papers, and employee-authored Substacks or Medium posts
- job postings that mention the leader's function or technical domain

Profile all user-named people. When the user asks for account research without named people, profile the likely buying committee:

- economic buyer: CEO, CFO, COO, business-unit president, GM, or procurement leader when relevant
- technology decision makers: CIO, CTO, CISO, chief architect, VP infrastructure, VP cloud/platform, VP engineering
- workload owners: data/AI, database, product, application, ERP, analytics, security, SRE, and operations leaders
- influencers: principal engineers, platform architects, database leaders, security architects, DevOps/SRE leads, and known Oracle relationship contacts

For each stakeholder, include:

| Field | Guidance |
|---|---|
| Name and role | Current title, function, location only when professionally relevant |
| Buying-committee role | Economic buyer, technical decision maker, champion, influencer, blocker, evaluator, procurement, unknown |
| Tenure and background | Prior roles, cloud/database/security/product experience, board/advisor roles when public |
| Public priorities | Public quotes, posts, interviews, product announcements, earnings-call remarks, or role-based priorities |
| Technical signals | Cloud, data, AI, security, VMware, Oracle, database, Kubernetes, engineering blog, or job-posting signals tied to their domain |
| Oracle relationship signal | Public Oracle history, Oracle partner/customer mentions, CRM/internal relationship context when authorized, or `not found in available sources` |
| Likely pains or objections | Clearly label as `inferred` unless directly stated |
| Personalization hook | One professional, non-creepy reason the outreach is relevant to that person |
| Email angle | Recommended message theme, OCI wedge, and ask |
| Source category and confidence | Publicly verified, Sales Navigator context, CRM/internal context, inferred, or not found |

Do not include sensitive personal attributes, private contact details, family information, political views, health information, or unrelated personal trivia. If a public post is personal but not relevant to the opportunity, ignore it.

If a company has a technical blog, mine it for stakeholder-specific and team-specific signals:

- technologies and architectures mentioned
- authors and teams associated with cloud, data, AI, security, platform, database, or reliability work
- recurring engineering priorities such as performance, scale, modernization, developer velocity, resilience, compliance, or cost efficiency
- open-source projects, SDKs, APIs, model/AI content, data platforms, Kubernetes, VMware, Oracle, or database mentions

Use stakeholder research to shape every personalized email. Each named email should have:

- the stakeholder's role and likely business or technical priority
- one sourced profile insight or team/company technical signal
- one relevant OCI wedge or discovery hypothesis
- a specific ask, such as executive alignment, architecture exchange, cost review, DR workshop, GPU pilot, or workload discovery
- a source/confidence note in the outreach kit, even if the email text itself stays natural

If stakeholder evidence is thin, use a role-based message and state the research gap in the stakeholder profile.

## Champion And Persona Target Research

Do not stop at executives. For product/engineering campaigns, find named people who can become champions, technical validators, workload guides, or warm entry points. These targets may be managers, staff/principal ICs, architects, product managers, SRE/DevOps leads, database leads, security architects, data/AI engineers, cloud platform owners, or technical program leaders.

Use a finite, account-relevant target set. For each account, default to:

- 8-15 named champion/persona targets when enough sources are available
- 2-4 targets per high-priority persona, such as platform/cloud, product engineering, data/AI, database, security, SRE/DevOps, infrastructure, or operations
- a balanced mix of senior ICs, managers, directors, and product owners; do not make the list executive-only
- at least one likely technical champion for each top OCI motion, when visible

Inspect current open jobs before writing persona campaigns:

- count how many relevant job postings were inspected
- capture title, team/function, location, job URL/source, cloud/provider mentions, database mentions, Kubernetes/IaC/DevOps signals, AI/GPU/data signals, security/compliance signals, and likely hiring initiative
- map each job signal to a campaign persona and an OCI discovery question
- use job postings as evidence of priorities and skill demand, not as proof of deployed architecture unless the role explicitly says so

Inspect individual employee profiles for campaign targets when public or approved:

- open the individual public profile, public author page, company bio, GitHub, conference page, patent page, or approved Sales Navigator lead profile
- capture only professional, opportunity-relevant context: title, function, tenure when visible, technical domain, public posts, authored technical content, certifications/skills when visible, team, likely workload ownership, and relationship path
- record the source category and access/as-of date for every profile
- avoid sensitive personal attributes, unrelated personal details, private contact info, and broad scraping

Score each champion candidate:

| Criterion | Guidance |
|---|---|
| Persona fit | Product engineering, platform/cloud, SRE/DevOps, data/AI, database, security, architecture, operations, finance/procurement, customer success |
| Workload proximity | How close the person appears to the wedge workload or technical problem |
| Influence level | IC, manager, director, VP, executive; lower title can still be high value |
| Relationship path | TeamLink, mutual connection, follows Oracle, CRM contact, authored public content, conference touchpoint, unknown |
| Technical evidence | Public profile, job posting, blog, GitHub, patent, talk, docs, Sales Navigator context |
| Champion-read | High, medium, low, or unknown; explain why |
| Outreach angle | The most relevant technical ask and OCI motion |
| Risk | Why outreach may miss or need a different path |

Output a campaign-target table:

| Person | Role/title | Persona | Why this person | Evidence/source | Champion-read | Email angle | First ask |
|---|---|---|---|---|---|---|---|

If individual profiles cannot be accessed, say exactly what was checked and create role-based target hypotheses separately from named champion candidates.

## Unit Economics And Waste Hypotheses

If enough data exists, estimate useful ratios:

- cloud spend as percent of revenue
- cost per employee, customer, transaction, shipment, store, endpoint, GB, or user, depending on the business model
- AI/GPU cost drivers if relevant

Provide 3-5 savings hypotheses with percentage ranges, clearly labeled as hypotheses:

- idle or oversized compute
- low CPU or memory utilization
- stranded volumes/IPs/snapshots
- over-replicated storage or backup tiers
- underused reservations, savings plans, or cloud commits
- egress-heavy data movement
- high-cost managed database or analytics workloads

## Workload Finder

Identify 8-12 workloads when possible. Score each 0-5 on:

- current platform clarity
- OCI equivalent strength
- migration pattern simplicity: rehost, replatform, refactor
- portability
- cutover ease
- user disruption risk
- time-to-value
- expected savings or value

Sort by total score and bold the top 3 `No Brainers`.

Include likely OCI equivalents, such as Compute, OKE, OCVS, Exadata Database Service, Exadata Cloud@Customer, Autonomous Database, MySQL HeatWave, Object Storage, Data Flow, GoldenGate, OCI Data Integration, OCI AI Infrastructure, DR patterns, FastConnect, Azure Interconnect, Dedicated Region, or sovereign cloud patterns when appropriate.

## AI/GPU Angle

When relevant, include:

- AI strategy and public AI product roadmap
- current or implied model sizes, training cadence, inference concurrency, and data sensitivity
- GPU/accelerator provider signals
- simple incumbent-vs-OCI TCO hypothesis for H100/H200 bare metal with RDMA only when assumptions are available
- 60-day pilot outline with success metrics

If AI relevance is weak, say so and focus the OCI motion elsewhere.

## OCI Sales Motions

Pick 2-4 motions per account. Use only motions that fit the evidence:

- Exadata Cloud@Customer
- Autonomous Database or MySQL HeatWave
- OCVS for VMware
- DR to OCI, cold/warm/hot
- data platform consolidation
- AI/GPU burst training or inference
- Azure interconnect or multicloud co-location
- Dedicated Region, sovereign cloud, or edge
- app modernization on Compute/OKE

For each motion, include:

- one-sentence customer value proposition
- 90-day plan
- stakeholders to target
- proof artifact needed
- evidence and assumptions

## OCI Buying-Objection Prep

Create `07-oci-buying-objection-prep.docx` and `.pdf` for every comprehensive account package. This is Oracle internal field preparation, not customer-facing copy. The goal is to anticipate the customer concerns that could block OCI, test whether they are real, and prepare the proof the rep and SE need.

For existing account-list packages whose sidecars already exist, add objection prep from the captured research before rebuilding the visualizer:

```bash
python3 .agents/skills/oci-opportunity-coach/scripts/enrich_account_objections.py output/account-research/<YYYY-MM-DD>
python3 .agents/skills/oci-opportunity-coach/scripts/build_account_research_visualizer.py output/account-research/<YYYY-MM-DD>
```

Evaluate the full objection library for each account, then include only objections that are materially plausible for that account:

| Category | Common customer language |
|---|---|
| Cloud standardization | We are already committed to AWS, Azure, or GCP; we do not want another cloud; our platform tooling is standardized elsewhere. |
| Developer preference and skills | Our engineers know the incumbent cloud; OCI talent is harder to hire; developer experience may slow us down. |
| Migration risk | Downtime, data gravity, cutover complexity, refactoring, rollback risk, operational disruption, or unclear migration factory. |
| Application fit | Application dependencies, latency, SaaS/platform coupling, Kubernetes portability, middleware, or integration complexity. |
| Database and licensing concerns | Oracle licensing complexity, audit fear, lock-in perception, database stability, or reluctance to move mission-critical systems. |
| Commercial and business case | Unclear TCO, discount comparison, support cost, egress/networking cost, migration funding, cloud commit conflicts, or budget timing. |
| Procurement and vendor strategy | OCI used as a price benchmark, incumbent leverage, multi-vendor policy, procurement skepticism, or contract-term concern. |
| Security, compliance, and sovereignty | Regulatory controls, data residency, key management, identity integration, audit evidence, FedRAMP/industry controls, or region availability. |
| Operational maturity and support | Support quality, incident response, observability, managed-service maturity, DR operations, escalation path, or SRE runbooks. |
| Ecosystem and marketplace | Partner availability, ISV integrations, managed services partners, marketplace depth, or consulting capacity. |
| Architecture and performance proof | Benchmark skepticism, network/storage/database latency, GPU/HPC proof, resilience claims, or reference architecture gaps. |
| Strategic trust and brand perception | Oracle is only for databases; Oracle is hard to work with; lock-in concerns; executive trust gaps. |
| Incumbent relationship risk | Existing AWS/Azure/GCP commit, strategic partnership, board or executive alignment, or strong incumbent account team. |
| Industry-specific risk | Healthcare, financial services, government, retail, manufacturing, telecom, media, SaaS, or regulated-industry concerns. |
| Internal change management | Missing champion, weak economic buyer, platform-team resistance, unclear owner, or workload owner not engaged. |

Tailoring rules:

- Produce a prioritized list of account-specific objections, not a generic checklist.
- Tie every objection to at least one account signal: public source, Sales Navigator context, CRM/internal context, job posting, tech-stack clue, leadership priority, industry pattern, financial pressure, or explicit validation gap.
- Label inferred objections as `inferred` and include the discovery question needed to confirm or disprove them.
- Include the likely speaker or owner when possible: CIO, CTO, CISO, CFO, procurement, platform team, app owner, database team, security, compliance, developer leader, or economic buyer.
- Default to 8-15 tailored objections per account when evidence supports it. Use fewer only when the research is thin, and state the source gap that limited confidence.
- Do not fabricate private pricing, discount thresholds, contract terms, renewal dates, support history, stakeholder sentiment, or competitor details.

Each objection prep file should include:

- Executive Objection Summary: top 3-5 objections most likely to affect the deal.
- Prioritized Objection Table: objection, category, likely speaker, account-specific trigger, confidence, impact, and stage risk.
- Customer Language: how the customer might phrase the concern in a meeting.
- Why They Might Believe It: evidence, assumptions, or validation gaps.
- Discovery Questions: targeted questions to test whether the objection is real.
- OCI Response Strategy: concise guidance for the rep and SE, grounded in the account context.
- Proof To Prepare: architecture, benchmark, TCO model, migration plan, security mapping, customer reference, support plan, workshop, or BOM.
- Stakeholders To Engage: who should be pulled into the next conversation.
- Risk If Unresolved: how the objection could slow, shrink, or kill the opportunity.
- Next Best Action: one concrete step for the account team.

Objection prep should sharpen the next customer conversation; it should not become a list of generic OCI advantages or a concession plan.

## Ranked Scorecard

Score each account 0-100:

| Criterion | Weight |
|---|---:|
| Oracle relationship and license posture | 20 |
| Workload portability | 25 |
| OCI workload fit | 25 |
| Cloud wallet size and growth | 10 |
| Renewal/timing pressure | 10 |
| Compliance/sovereign fit | 5 |
| AI/HPC fit | 5 |

Use `OCI workload fit` as the broad primary workload signal for database,
app modernization, VMware/OCVS, OKE/Kubernetes, storage, DR, observability,
security, Oracle applications, integration, and cloud cost optimization. Treat
`AI/HPC fit` as a bonus signal unless the user explicitly says the target motion
is AI infrastructure, GPU, HPC, or model workload led.

Output:

| Rank | Account | Score | Why OCI can win | Wedge workload | Go/Watch/Hold | Confidence |
|---:|---|---:|---|---|---|---|

If Oracle relationship or license posture is not visible, mark it `not found in available sources` or `needs user-authorized internal source` rather than leaving it blank or forcing a score. Explain how that affects total confidence.

## Outreach Kit

Create two buckets.

Personalized executive messages:

- Target named executives and decision makers only when public, approved LinkedIn/Sales Navigator, CRM/internal, or user-provided sources support the personalization.
- Use public executive quotes, interviews, posts, earnings-call remarks, key initiatives, role priorities, technical blog signals, and stakeholder profile findings.
- Keep messages concise, specific, and tied to a plausible OCI wedge.
- Do not imply a relationship, private knowledge, or unstated pain.
- For every named message, record the profile insight, source category, confidence, OCI wedge, and what to validate.

General product/engineering campaign:

- Write scalable messages for engineers, product managers, platform teams, data leaders, security leaders, and infrastructure owners.
- Identify named employees for each campaign persona where public or approved individual profiles are available. Do not send only persona-generic copy when named technical champion candidates can be found.
- Anchor on product-based or architecture-based themes from company technical blogs, job postings, product docs, engineering posts, and public architecture signals rather than personal details.
- Include a clear ask, such as a 30-minute architecture exchange, cost review, DR workshop, GPU pilot, or workload discovery.
- Include a research coverage audit: number of jobs inspected, number of employee profiles inspected, number of Sales Navigator lead profiles inspected, number of technical posts/docs inspected, and what was not found.

Include:

- first-touch email, 130-160 words, tailored to the top wedge workload and timing lever
- 8 discovery questions tied to measurable outcomes
- 4 objection handles: migration risk, unit prices, developer preference for incumbent cloud, database untouchable

## Deliverable Order

For each account, deliver in this order:

1. `01-comprehensive-profile.docx` and `.pdf`
2. `02-executive-one-pager.docx` and `.pdf`
3. `03-oci-pursuit-scorecard.docx` and `.pdf`
4. `04-outreach-kit.docx` and `.pdf`
5. `05-stakeholder-profiles.docx` and `.pdf`
6. `06-champion-persona-targets.docx` and `.pdf`
7. `07-oci-buying-objection-prep.docx` and `.pdf`
8. `00-source-log.docx` and `.pdf`

End the profile or root index with a six-bullet executive summary per account.

## Quality Bar

- Be explicit about assumptions and confidence for every numeric metric.
- Cite or log sources for the five most important claims per account at minimum.
- Prefer fewer, stronger hypotheses over generic cloud sales language.
- For outreach packages, state how many open jobs, individual employee profiles, Sales Navigator lead profiles, and technical posts/docs were inspected. Never imply a deep people/job pass was done if only account-level pages were reviewed.
- For OCI buying-objection prep, include only objections that are plausible for the account, label inferred concerns, and pair each with validation questions and proof to prepare.
- Do not fill Oracle internal fields from public guesses; fill them from authorized visible sources or mark them `not found in available sources` / `needs user-authorized internal source`.
- If evidence is thin, state the gap and convert it into a discovery question.
