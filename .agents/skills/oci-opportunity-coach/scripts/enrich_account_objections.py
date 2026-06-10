#!/usr/bin/env python3
"""Add account-tailored OCI buying-objection prep to account research folders."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
import zipfile
from datetime import date
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape


DOCX_NAME = "07-oci-buying-objection-prep.docx"
PDF_NAME = "07-oci-buying-objection-prep.pdf"


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def walk_text(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_text(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_text(child)
    else:
        text = as_text(value)
        if text:
            yield text


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", as_text(value)).strip()


def first_regex(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.I)
    return clean(match.group(1)) if match else ""


def first_snippet(context: str, keywords: list[str], fallback: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", context)
    for keyword in keywords:
        for sentence in sentences:
            if keyword.lower() in sentence.lower() and len(sentence.strip()) > 20:
                return truncate(clean(sentence), 280)
    return fallback


def truncate(text: str, limit: int = 220) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def unique(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else clean(value).lower()
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def account_summary(data: dict[str, Any]) -> dict[str, str]:
    business = as_dict(data.get("business_overview"))
    sales_nav = as_dict(business.get("sales_navigator_context"))
    scorecard = as_dict(data.get("scorecard"))
    raw_scorecard = as_text(scorecard.get("raw"))
    hypotheses = " ".join(walk_text(data.get("oci_pursuit_hypotheses")))
    context = "\n".join(walk_text(data))

    top_wedge = (
        as_text(scorecard.get("top_wedge"))
        or first_regex(raw_scorecard, r"Top wedge:\s*([^\n]+)")
        or first_regex(hypotheses, r"Top wedge from existing research:\s*([^.\n]+)")
        or "workload economics and resilience discovery"
    )
    disposition = as_text(scorecard.get("disposition")) or first_regex(raw_scorecard, r"Disposition:\s*([A-Za-z /-]+)")
    confidence = as_text(scorecard.get("confidence")) or first_regex(raw_scorecard, r"Confidence:\s*([A-Za-z -]+)")
    industry = (
        as_text(sales_nav.get("industry"))
        or as_text(business.get("industries"))
        or as_text(business.get("industry"))
        or "industry not found in sidecar"
    )
    employees_revenue = (
        as_text(sales_nav.get("employees_revenue"))
        or as_text(sales_nav.get("employees/revenue"))
        or as_text(business.get("employees_revenue"))
        or "not found in sidecar"
    )
    buyer_intent = as_text(sales_nav.get("buyer_intent_visible")) or first_snippet(
        context, ["buyer intent"], "buyer intent not found in sidecar"
    )

    return {
        "name": as_text(data.get("account_name")) or as_text(data.get("account_slug")),
        "slug": as_text(data.get("account_slug")) or as_text(data.get("source_folder")),
        "industry": truncate(industry, 180),
        "employees_revenue": truncate(employees_revenue, 120),
        "buyer_intent": truncate(buyer_intent, 160),
        "top_wedge": truncate(top_wedge, 120),
        "disposition": disposition or "not scored",
        "confidence": confidence or "not specified",
        "context": context,
        "context_lower": context.lower(),
        "scorecard_raw": raw_scorecard,
    }


def objection(
    objection_text: str,
    category: str,
    customer_language: str,
    trigger: str,
    evidence: str,
    confidence: str,
    speaker: str,
    impact: str,
    questions: list[str],
    response: str,
    proof: list[str],
    risk: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "objection": objection_text,
        "category": category,
        "customer_language": customer_language,
        "account_specific_trigger": trigger,
        "evidence_source": evidence,
        "confidence": confidence,
        "likely_speaker": speaker,
        "impact": impact,
        "discovery_questions": questions,
        "response_strategy": response,
        "proof_to_prepare": proof,
        "risk_if_unresolved": risk,
        "next_best_action": next_action,
    }


def industry_objection(summary: dict[str, str]) -> dict[str, Any]:
    industry = summary["industry"]
    lower = (summary["industry"] + " " + summary["context_lower"]).lower()
    if contains_any(lower, ["legal", "e-discovery", "compliance", "investigation"]):
        concern = "Data custody, evidentiary integrity, and compliance proof may be required before OCI is credible."
        language = "We cannot risk data-chain, compliance, or legal workflow disruption just to change infrastructure."
        proof = ["security and compliance control mapping", "data residency and encryption design", "migration rollback plan"]
        speaker = "CISO, legal technology owner, or compliance leader"
    elif contains_any(lower, ["cyber", "security", "password", "risk", "background", "screening"]):
        concern = "Security and trust review may dominate the OCI decision."
        language = "Before we consider OCI, we need evidence it meets our security, identity, audit, and incident-response expectations."
        proof = ["security architecture review", "identity and key-management mapping", "support and escalation plan"]
        speaker = "CISO or security architecture leader"
    elif contains_any(lower, ["government", "federal", "public sector", "defense", "aerospace"]):
        concern = "Regulatory, sovereignty, and procurement requirements may raise the proof bar for OCI."
        language = "We need region, compliance, procurement, and operational evidence before adding another cloud."
        proof = ["region and compliance matrix", "procurement path review", "sovereignty and isolation pattern"]
        speaker = "CIO, compliance, procurement, or public-sector program owner"
    elif contains_any(lower, ["manufacturing", "industrial", "construction", "materials", "supply chain"]):
        concern = "Operational disruption and site-level reliability concerns may slow OCI adoption."
        language = "Our operations cannot absorb cloud migration risk without proof of uptime, latency, and rollback."
        proof = ["resilience design", "latency benchmark", "phased migration plan"]
        speaker = "operations, platform, or application owner"
    elif contains_any(lower, ["real estate", "property", "facilities", "benefits", "payroll", "hr", "human capital"]):
        concern = "Customer-facing workflow continuity and sensitive data handling may be the first OCI objections."
        language = "We need to protect user experience and sensitive data before moving any core workflow."
        proof = ["PII/security control mapping", "pilot success criteria", "support and rollback plan"]
        speaker = "CIO, CISO, product owner, or operations leader"
    elif contains_any(lower, ["retail", "commerce", "marketing", "loyalty", "consumer"]):
        concern = "Peak traffic, data latency, and customer-experience risk may require proof before OCI is considered."
        language = "If OCI cannot prove performance during campaign or customer traffic peaks, it is not worth the risk."
        proof = ["performance benchmark", "data movement cost model", "resilience test plan"]
        speaker = "digital product, data, or platform leader"
    elif contains_any(lower, ["saas", "software", "platform", "cloud"]):
        concern = "SaaS platform reliability, developer workflow, and operating-model fit may be challenged."
        language = "We run a cloud software business; adding OCI has to improve reliability or economics without slowing delivery."
        proof = ["reference architecture", "DevOps/IaC integration plan", "unit economics model"]
        speaker = "CTO, VP engineering, or platform leader"
    else:
        concern = "Industry-specific risk needs validation because the existing sidecar does not fully prove the buyer's operating constraints."
        language = "Before OCI is credible, we need to understand how it fits our operating model and risk requirements."
        proof = ["account-specific discovery workshop", "architecture validation", "risk and control checklist"]
        speaker = "economic buyer, CIO, or workload owner"

    return objection(
        concern,
        "Industry-specific risk",
        language,
        f"Existing research describes the account context as: {industry}",
        "Existing account-research.json industry/business fields; no new research performed.",
        "medium inferred" if industry != "industry not found in sidecar" else "low inferred",
        speaker,
        "Could raise the proof bar or slow the first OCI workload.",
        [
            "Which industry or operating constraints would make OCI unacceptable for the first workload?",
            "What evidence format would let the risk owner approve a scoped OCI evaluation?",
        ],
        "Anchor the discussion in the account's operating constraints first, then map OCI proof to the narrow workload under consideration.",
        proof,
        "OCI may be viewed as generic cloud positioning rather than a fit for the customer's actual risk model.",
        "Run a workload-specific risk and proof workshop before broad OCI positioning.",
    )


def build_objections(data: dict[str, Any]) -> dict[str, Any]:
    summary = account_summary(data)
    name = summary["name"]
    context = summary["context"]
    lower = summary["context_lower"]
    top_wedge = summary["top_wedge"]
    disposition = summary["disposition"]
    confidence = summary["confidence"]
    employees = summary["employees_revenue"]
    buyer_intent = summary["buyer_intent"]

    provider_terms = ["aws", "azure", "gcp", "google cloud", "microsoft", "cloud provider", "incumbent"]
    has_provider_signal = contains_any(lower, provider_terms)
    has_ai = contains_any(lower, ["ai", "automation", "machine learning", "gpu", "model", "data platform"])
    has_security = contains_any(lower, ["security", "compliance", "sovereign", "risk", "audit", "encryption", "identity"])
    has_saas = contains_any(lower, ["saas", "platform", "cloud software", "subscription", "customer success"])
    has_hiring = contains_any(lower, ["hiring", "job", "headcount", "employee", "skills"])
    has_database = contains_any(lower, ["database", "oracle database", "sql", "erp", "exadata"])
    has_resilience = contains_any(lower, ["resilience", "dr", "disaster", "uptime", "latency", "performance"])

    cloud_evidence = first_snippet(
        context,
        ["Cloud posture", "cloud provider", "AWS", "Azure", "GCP", "provider mix", "cloud transition"],
        "Existing research requires validation of incumbent providers, commitments, and workload portability.",
    )
    portability_evidence = first_snippet(
        context,
        ["Workload portability", "Depends on architecture validation", "migration", "portability", "cutover"],
        "The scorecard requires architecture and portability validation before broad OCI positioning.",
    )
    business_case_evidence = first_snippet(
        context,
        ["Cloud wallet size", "renewal", "timing pressure", "economics", "cost", "TCO"],
        "Existing scorecard asks to validate renewal calendar and economics before committing to an OCI motion.",
    )
    proof_evidence = first_snippet(
        context,
        ["Top wedge", "AI/data", "benchmark", "resilience", "performance", "proof"],
        f"Existing research identifies the top OCI wedge as {top_wedge}.",
    )

    objections: list[dict[str, Any]] = [
        objection(
            "The customer may prefer to stay with its current cloud standard or operating model.",
            "Cloud standardization",
            "We are already standardized on our current cloud and tooling; OCI would add another operating model.",
            cloud_evidence,
            "Existing sidecar cloud posture and scorecard fields; provider mix should be validated in discovery.",
            "medium inferred" if has_provider_signal else "low inferred",
            "CIO, CTO, platform leader, or cloud operations owner",
            "Could block OCI before workload proof if the team sees this as a cloud-standardization debate.",
            [
                "Which cloud platforms are approved standards today, and where are exceptions allowed?",
                "Is the first OCI workload expected to replace an incumbent platform or solve a specific workload problem?",
            ],
            "Position OCI around the specific workload and proof point, not as a broad cloud replacement. Ask for the approved exception path and the technical owner who can validate it.",
            ["incumbent-cloud comparison matrix", "narrow workload proof plan", "operating model integration plan"],
            "OCI may be rejected as an extra cloud before the team evaluates workload-level value.",
            "Confirm the current cloud standard, exception criteria, and first workload owner.",
        ),
        objection(
            "Developer and platform teams may question OCI skills, tooling, and day-2 ownership.",
            "Developer preference and skills",
            "Our teams know the incumbent cloud; OCI skills and tooling could slow us down.",
            first_snippet(
                context,
                ["hiring", "headcount", "skills", "developer", "platform", "job"],
                "Existing research does not prove OCI skills or operating ownership in the account.",
            ),
            "Existing sidecar employee, hiring, technology, and validation fields.",
            "medium inferred" if has_hiring or has_saas else "low inferred",
            "platform team, VP engineering, SRE/DevOps leader, or application owner",
            "Could create technical resistance even when the business case is attractive.",
            [
                "Which team would operate the first OCI workload after go-live?",
                "What tools, IaC patterns, observability, and support processes must OCI fit on day one?",
            ],
            "Create an enablement and operating-plan path for a bounded workload. Emphasize familiar tooling integration where the evidence supports it.",
            ["day-2 operations plan", "skills enablement plan", "DevOps/IaC integration checklist"],
            "The technical team may view OCI as added operational burden.",
            "Ask the platform owner to name the minimum day-2 requirements for a pilot.",
        ),
        objection(
            "Migration risk may outweigh the perceived value of the OCI motion.",
            "Migration risk",
            "The migration risk, rollback complexity, and potential disruption are not worth it unless the first workload is very clear.",
            portability_evidence,
            "Existing sidecar scorecard and workload validation fields.",
            "medium inferred",
            "application owner, platform leader, CIO, or operations leader",
            "Could delay the opportunity until the account team can prove a safe first workload.",
            [
                "Which workload is small enough to move first but meaningful enough to prove OCI value?",
                "What downtime, rollback, data movement, and integration constraints are non-negotiable?",
            ],
            "Lead with a phased migration plan, cutover pattern, and rollback criteria tied to the top wedge.",
            ["migration wave plan", "rollback plan", "dependency map", "architecture review"],
            "The customer may keep OCI at a conceptual level and never approve technical validation.",
            "Build a first-workload migration proof with explicit entry and exit criteria.",
        ),
        objection(
            "The business case may not be clear enough to justify OCI evaluation.",
            "Commercial and business case",
            "Show us the business case. We need more than unit-price comparisons or generic savings claims.",
            business_case_evidence,
            "Existing sidecar scorecard, renewal/timing, and economics fields.",
            "medium inferred",
            "CFO, procurement, CIO, economic buyer, or cloud financial operations owner",
            "Could reduce OCI to a price comparison before scope and value are defined.",
            [
                "What cost baseline should OCI be compared against: current run rate, renewal, commit drawdown, or target unit economics?",
                "Which costs matter most: compute, storage, database, egress, support, migration, or operations?",
            ],
            "Avoid discount-led positioning. Build a scoped TCO and value model around the first workload, operational risk, and proof criteria.",
            ["TCO model", "BOM assumptions", "cost baseline worksheet", "migration funding assumptions"],
            "Procurement may treat OCI as a pricing benchmark rather than a serious platform option.",
            "Request the current cost baseline and commercial decision criteria before pricing discussion.",
        ),
        objection(
            "Procurement may use OCI mainly as leverage against an incumbent vendor.",
            "Procurement and vendor strategy",
            "We are comparing options, but the incumbent already has the relationship and contract path.",
            first_snippet(
                context,
                ["renewal", "timing pressure", "Disposition", "Confidence", "buyer intent"],
                f"Existing scorecard disposition is {disposition} with confidence {confidence}; decision criteria still need validation.",
            ),
            "Existing sidecar scorecard, buyer intent, and validation gaps.",
            "medium inferred" if "watch" in disposition.lower() or "hold" in disposition.lower() else "low inferred",
            "procurement, CFO, CIO, or vendor-management owner",
            "Could waste sales cycles if Oracle is not tied to a real workload and selection path.",
            [
                "What has to be true for Oracle to be selected, not just used as a comparison point?",
                "Who owns the technical recommendation and who owns the commercial decision?",
            ],
            "Qualify for workload ownership, decision criteria, and proof acceptance before investing in detailed pricing or architecture work.",
            ["mutual action plan", "decision criteria worksheet", "technical proof acceptance criteria"],
            "The account team may over-invest before there is a real path to selection.",
            "Ask procurement and the technical owner to confirm selection criteria and next-step owners.",
        ),
        objection(
            "Oracle licensing, audit, or lock-in perception may create resistance even when OCI fit is plausible.",
            "Database and licensing concerns",
            "We are concerned that Oracle cloud discussions will create licensing complexity or lock-in.",
            first_snippet(
                context,
                ["Oracle relationship and license posture", "database", "license", "Oracle Database", "ERP"],
                "Existing research marks Oracle relationship and license posture as unknown or needing an authorized internal source.",
            ),
            "Existing sidecar scorecard and Oracle relationship/license posture fields.",
            "medium inferred" if has_database else "low inferred",
            "CIO, database leader, procurement, or application owner",
            "Could introduce trust friction or slow commercial/legal review.",
            [
                "Which Oracle contracts, databases, or licenses are actually in scope for this discussion?",
                "Are there specific licensing, audit, or lock-in concerns we need to separate from the OCI workload case?",
            ],
            "Separate verified contract/license facts from OCI workload value. Do not infer internal Oracle posture without authorized sources.",
            ["authorized Oracle relationship review", "license scope clarification", "workload-specific OCI architecture"],
            "Unresolved Oracle commercial perception may overshadow the technical value story.",
            "Use authorized internal context to validate Oracle relationship and license posture before making claims.",
        ),
        industry_objection(summary),
        objection(
            "Security, compliance, and sovereignty proof may be required before technical enthusiasm converts.",
            "Security, compliance, and sovereignty",
            "We need security, compliance, identity, data residency, and audit evidence before considering OCI.",
            first_snippet(
                context,
                ["security", "compliance", "sovereign", "risk", "audit", "identity", "data residency"],
                "Existing scorecard includes compliance/sovereign fit; validate required controls and evidence format.",
            ),
            "Existing sidecar security/compliance, industry, and scorecard fields.",
            "medium inferred" if has_security else "low inferred",
            "CISO, compliance leader, security architect, or risk owner",
            "Could block evaluation until Oracle produces the right evidence format.",
            [
                "Which controls, certifications, identity integrations, or residency requirements must be proven first?",
                "Who signs off on security and compliance for the first OCI workload?",
            ],
            "Prepare evidence in the customer's control language and focus on the first workload's data and identity path.",
            ["security control mapping", "identity integration diagram", "data residency and encryption plan"],
            "The opportunity may stall in security review after business or technical interest.",
            "Schedule a security architecture review with the CISO or delegated control owner.",
        ),
        objection(
            "The customer may require stronger architecture and performance proof for the top OCI wedge.",
            "Architecture and performance proof",
            f"OCI sounds interesting for {top_wedge}, but we need proof it performs and operates reliably for our workload.",
            proof_evidence,
            "Existing sidecar top wedge, OCI hypotheses, technology signals, and scorecard fields.",
            "medium inferred" if has_ai or has_resilience else "low inferred",
            "CTO, chief architect, data/AI leader, platform owner, or application owner",
            "Could make the deal dependent on a benchmark, pilot, or architecture workshop.",
            [
                f"What measurable proof would make {top_wedge} credible for this account?",
                "Which latency, throughput, resilience, data, or cost metric would decide the evaluation?",
            ],
            "Convert the OCI wedge into a measurable proof plan with named success metrics and customer-owned test data or workload assumptions.",
            ["benchmark plan", "reference architecture", "POV success criteria", "performance and resilience test plan"],
            "Without proof, OCI remains a hypothesis rather than a qualified buying path.",
            "Define success metrics and proof artifact owners before the next technical meeting.",
        ),
        objection(
            "Operational maturity and support expectations may need to be proven for production workloads.",
            "Operational maturity and support",
            "We need confidence in OCI support, escalation, observability, and day-2 operations before we trust production workloads.",
            first_snippet(
                context,
                ["customer success", "support", "operations", "resilience", "managed", "platform"],
                "Existing research points to production or platform concerns; day-2 ownership should be validated.",
            ),
            "Existing sidecar technology, business, and stakeholder fields.",
            "medium inferred" if has_saas or has_resilience else "low inferred",
            "operations leader, SRE/DevOps owner, platform leader, or CIO",
            "Could block production commitment even after a successful technical demo.",
            [
                "What support and escalation model is required for the first OCI workload?",
                "Which observability, incident, backup, DR, and runbook requirements must be in place before production?",
            ],
            "Treat support and operations as part of the proof, not as post-sale details.",
            ["support model", "runbook outline", "observability mapping", "DR test plan"],
            "The customer may approve a demo but resist production adoption.",
            "Bring support/operations owners into the proof-planning conversation.",
        ),
        objection(
            "Partner ecosystem or implementation capacity may be questioned.",
            "Ecosystem and marketplace",
            "We need confidence that partners, integrations, and implementation resources exist for our environment.",
            first_snippet(
                context,
                ["partner", "alliance", "marketplace", "Deloitte", "integrations", "ecosystem", "competitors"],
                "Existing research does not fully validate required partners, integrations, or delivery capacity.",
            ),
            "Existing sidecar business, partner, competitor, and validation fields.",
            "medium inferred" if contains_any(lower, ["partner", "alliance", "integrations", "marketplace"]) else "low inferred",
            "CIO, procurement, application owner, or implementation lead",
            "Could slow adoption if the customer sees OCI as harder to implement or integrate.",
            [
                "Which ISVs, partners, managed services, or integrations are mandatory for the first workload?",
                "Does the customer need Oracle, a partner, or their own team to lead implementation?",
            ],
            "Identify the required partner/integration path early and avoid presenting OCI as a standalone infrastructure decision.",
            ["partner delivery plan", "integration checklist", "implementation responsibility matrix"],
            "OCI may lose to an incumbent with a clearer delivery ecosystem.",
            "Validate required partners and integrations before proposing a migration path.",
        ),
        objection(
            "Strategic trust and Oracle brand perception may need active handling.",
            "Strategic trust and brand perception",
            "Oracle may be strong in databases, but we are not sure we want Oracle as a broader cloud platform.",
            first_snippet(
                context,
                ["Avoid broad cloud-replacement positioning", "Why OCI Can Win", "Oracle ecosystem", "Oracle relationship"],
                "Existing scorecard warns against broad cloud-replacement positioning until workload portability and renewal timing are validated.",
            ),
            "Existing sidecar scorecard and Oracle relationship fields.",
            "medium inferred",
            "CIO, CTO, CFO, procurement, or executive sponsor",
            "Could require executive-level trust building before technical proof is accepted.",
            [
                "What concerns does the team associate specifically with Oracle versus the proposed workload solution?",
                "Would an executive reference, architecture proof, or commercial clarity do the most to reduce trust risk?",
            ],
            "Acknowledge the perception risk and move quickly to customer-specific proof, references, and operating commitments.",
            ["executive reference path", "workload-specific proof", "clear support/escalation model"],
            "The discussion may remain stuck in brand perception instead of workload fit.",
            "Ask the sponsor which Oracle-specific concern must be addressed first.",
        ),
        objection(
            "Internal ownership and buying-committee alignment may be incomplete.",
            "Internal change management",
            "We do not yet have the right owners aligned to sponsor, validate, and operate this OCI workload.",
            first_snippet(
                context,
                ["decision-makers", "stakeholders", "champion", "validation", "confidence", "buyer intent"],
                f"Existing research shows {buyer_intent}; stakeholder ownership and validation path still need confirmation.",
            ),
            "Existing sidecar stakeholder, buyer-intent, scorecard, and validation fields.",
            "medium inferred",
            "account sponsor, CIO, platform owner, workload owner, or procurement",
            "Could create a long evaluation with no accountable decision path.",
            [
                "Who is the economic buyer, technical validator, workload owner, and operations owner for the first OCI workload?",
                "Who could say no even if the pilot succeeds?",
            ],
            "Map the buying committee and tie each objection to an owner, proof point, and next meeting.",
            ["stakeholder map", "mutual action plan", "objection owner map"],
            "OCI may have interest but no champion or accountable path to close.",
            "Create a stakeholder/objection map and validate it with the account owner.",
        ),
    ]

    if has_ai:
        objections.insert(
            8,
            objection(
                "AI/data workload value may be challenged without data locality, model, and economics proof.",
                "Architecture and performance proof",
                "If this is about AI or data, we need to see data locality, performance, governance, and cost proof.",
                first_snippet(
                    context,
                    ["AI", "automation", "data", "model", "GPU", "AI/data"],
                    "Existing research identifies AI/data as a discovery topic; production workload shape requires validation.",
                ),
                "Existing sidecar AI/data, OCI hypotheses, and technology signals.",
                "medium inferred",
                "data/AI leader, CTO, CISO, or platform leader",
                "Could stop an AI/GPU or data-platform motion unless the proof is measurable.",
                [
                    "Which AI/data workload is in scope: training, inference, analytics, data movement, or governance?",
                    "What data locality, security, GPU, performance, or cost metric would make OCI compelling?",
                ],
                "Frame OCI as a proof-backed AI/data workload option, not as generic AI infrastructure.",
                ["AI/data benchmark", "data locality design", "GPU or analytics TCO model", "security/governance mapping"],
                "OCI AI/data positioning may sound generic or risky without workload-specific proof.",
                "Define one AI/data workload and the acceptance metrics for a 60-day proof.",
            ),
        )

    objections = unique(objections)[:12]
    top = [item["objection"] for item in objections[:5]]
    all_questions = unique([q for item in objections for q in item["discovery_questions"]])[:12]
    proof = unique([p for item in objections for p in item["proof_to_prepare"]])[:12]
    stakeholders = unique([item["likely_speaker"] for item in objections])[:10]
    next_actions = unique([item["next_best_action"] for item in objections])[:8]

    return {
        "summary": (
            f"{name} objection prep is generated from the existing account-research sidecar only. "
            f"The most likely OCI buying objections center on {top_wedge}, incumbent cloud/operating model fit, "
            f"migration risk, business-case proof, and stakeholder alignment. Disposition is {disposition}; "
            f"confidence is {confidence}; employee/revenue signal is {employees}; buyer-intent signal is {buyer_intent}. "
            "Treat all concerns as field-prep hypotheses until validated with the customer."
        ),
        "top_objections": top,
        "objection_inventory": objections,
        "discovery_questions": all_questions,
        "proof_to_prepare": proof,
        "stakeholders_to_engage": stakeholders,
        "next_actions": next_actions,
        "source_notes": [
            f"Generated on {date.today().isoformat()} from existing account-research.json. No new research was performed.",
            "Objections labeled as inferred are preparation hypotheses, not verified customer statements.",
            "Do not use this section as discount, concession, or private contract guidance.",
        ],
    }


def section_lines(data: dict[str, Any]) -> list[str]:
    name = as_text(data.get("account_name")) or as_text(data.get("account_slug"))
    prep = as_dict(data.get("oci_buying_objection_prep"))
    lines = [
        "OCI Buying-Objection Prep",
        f"Account: {name}",
        "Audience: Oracle internal field preparation",
        "",
        "Executive Objection Summary",
        as_text(prep.get("summary")),
        "",
        "Top Objections",
    ]
    for item in prep.get("top_objections", []):
        lines.append(f"- {as_text(item)}")
    lines.extend(["", "Prioritized Objection Inventory"])
    for idx, item in enumerate(prep.get("objection_inventory", []), 1):
        lines.extend(
            [
                "",
                f"{idx}. {item.get('objection', '')}",
                f"Category: {item.get('category', '')}",
                f"Likely speaker: {item.get('likely_speaker', '')}",
                f"Confidence: {item.get('confidence', '')}",
                f"Impact: {item.get('impact', '')}",
                f"Customer language: {item.get('customer_language', '')}",
                f"Account-specific trigger: {item.get('account_specific_trigger', '')}",
                f"Evidence source: {item.get('evidence_source', '')}",
                "Discovery questions:",
            ]
        )
        for question in item.get("discovery_questions", []):
            lines.append(f"- {question}")
        lines.extend(
            [
                f"OCI response strategy: {item.get('response_strategy', '')}",
                "Proof to prepare:",
            ]
        )
        for proof in item.get("proof_to_prepare", []):
            lines.append(f"- {proof}")
        lines.extend(
            [
                f"Risk if unresolved: {item.get('risk_if_unresolved', '')}",
                f"Next best action: {item.get('next_best_action', '')}",
            ]
        )
    lines.extend(["", "Source Notes"])
    for note in prep.get("source_notes", []):
        lines.append(f"- {note}")
    return lines


def paragraph_xml(text: str) -> str:
    text = text.rstrip()
    if not text:
        return "<w:p/>"
    is_heading = not text.startswith("- ") and (
        text in {
            "OCI Buying-Objection Prep",
            "Executive Objection Summary",
            "Top Objections",
            "Prioritized Objection Inventory",
            "Source Notes",
        }
        or re.match(r"^\d+\. ", text)
    )
    bold = "<w:b/>" if is_heading else ""
    size = "<w:sz w:val=\"32\"/>" if text == "OCI Buying-Objection Prep" else "<w:sz w:val=\"22\"/>"
    return (
        "<w:p><w:r><w:rPr>"
        f"{bold}{size}"
        "</w:rPr><w:t xml:space=\"preserve\">"
        f"{xml_escape(text)}"
        "</w:t></w:r></w:p>"
    )


def write_docx(path: Path, lines: list[str]) -> None:
    document = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        "<w:body>"
        + "".join(paragraph_xml(line) for line in lines)
        + "<w:sectPr><w:pgSz w:w=\"12240\" w:h=\"15840\"/><w:pgMar w:top=\"720\" w:right=\"720\" w:bottom=\"720\" w:left=\"720\"/></w:sectPr>"
        "</w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>"
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>"
            "</Relationships>",
        )
        zf.writestr("word/document.xml", document)


def pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(path: Path, lines: list[str]) -> None:
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        prefix = "- " if line.startswith("- ") else ""
        body = line[2:] if prefix else line
        for idx, chunk in enumerate(textwrap.wrap(body, width=92) or [""]):
            wrapped.append((prefix if idx == 0 else "  ") + chunk)

    pages = [wrapped[i : i + 58] for i in range(0, len(wrapped), 58)] or [[]]
    objects: list[bytes] = []

    def add(obj: str | bytes) -> int:
        objects.append(obj.encode("latin-1", "replace") if isinstance(obj, str) else obj)
        return len(objects)

    catalog_id = add("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add("")
    font_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []

    for page in pages:
        commands = ["BT", "/F1 9 Tf", "54 748 Td", "12 TL"]
        for line in page:
            commands.append(f"({pdf_escape(line)}) Tj")
            commands.append("T*")
        commands.append("ET")
        content = "\n".join(commands).encode("latin-1", "replace")
        content_id = add(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
        page_id = add(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{pid} 0 R' for pid in page_ids)}] /Count {len(page_ids)} >>"
    ).encode("latin-1")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{idx} 0 obj\n".encode("latin-1"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode(
            "latin-1"
        )
    )
    path.write_bytes(output)


def enrich_account(sidecar: Path) -> None:
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    data["oci_buying_objection_prep"] = build_objections(data)
    artifacts = as_dict(data.get("artifacts"))
    artifacts["oci_buying_objection_prep_docx"] = DOCX_NAME
    artifacts["oci_buying_objection_prep_pdf"] = PDF_NAME
    data["artifacts"] = artifacts

    sidecar.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = section_lines(data)
    write_docx(sidecar.parent / DOCX_NAME, lines)
    write_pdf(sidecar.parent / PDF_NAME, lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_root", type=Path, help="Research root containing per-account account-research.json files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.research_root.resolve()
    sidecars = sorted(root.glob("*/account-research.json"))
    if not sidecars:
        raise SystemExit(f"No account-research.json files found under {root}")
    for sidecar in sidecars:
        enrich_account(sidecar)
    print(f"Updated accounts: {len(sidecars)}")
    print(f"Research root: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
