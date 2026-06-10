#!/usr/bin/env python3
"""Build a static account research visualizer from account-research.json files."""

from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any


ARTIFACT_LABELS = {
    "source_log": "Source Log",
    "comprehensive_profile": "Comprehensive Profile",
    "executive_one_pager": "Executive One-Pager",
    "scorecard": "Scorecard",
    "outreach_kit": "Outreach Kit",
    "stakeholder_profiles": "Stakeholder Profiles",
    "champion_persona_targets": "Champion/Persona Targets",
    "oci_buying_objection_prep": "OCI Buying Objection Prep",
    "research_pack": "Research Pack",
}


def load_sidecars(root: Path) -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    for sidecar in sorted(root.glob("*/account-research.json")):
        with sidecar.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        data["_sidecar_path"] = sidecar.relative_to(root).as_posix()
        data["_folder_path"] = sidecar.parent.relative_to(root).as_posix()
        data["_summary"] = summarize_account(data)
        accounts.append(data)
    return accounts


def summarize_account(data: dict[str, Any]) -> dict[str, Any]:
    scorecard = as_dict(data.get("scorecard"))
    business = as_dict(data.get("business_overview"))
    sales_nav = as_dict(business.get("sales_navigator_context"))
    raw_scorecard = as_text(scorecard.get("raw"))

    score = first_number(scorecard.get("score")) or first_regex(raw_scorecard, r"Overall score:\s*(\d+(?:\.\d+)?)")
    disposition = (
        as_text(scorecard.get("disposition"))
        or first_regex(raw_scorecard, r"Disposition:\s*([A-Za-z -]+)")
        or "Not scored"
    )
    top_wedge = (
        as_text(scorecard.get("top_wedge"))
        or first_regex(raw_scorecard, r"Top wedge:\s*([^\n]+)")
        or top_wedge_from_hypotheses(data.get("oci_pursuit_hypotheses"))
        or "Not specified"
    )
    confidence = (
        as_text(scorecard.get("confidence"))
        or first_regex(raw_scorecard, r"Confidence:\s*([A-Za-z -]+)")
        or "Not specified"
    )
    employees_revenue = (
        as_text(sales_nav.get("employees_revenue"))
        or as_text(sales_nav.get("employees/revenue"))
        or as_text(business.get("employees_revenue"))
        or "Not found in sidecar"
    )
    buyer_intent = (
        as_text(sales_nav.get("buyer_intent_visible"))
        or first_line_matching(data, "buyer intent")
        or "Not found in sidecar"
    )

    return {
        "account_name": as_text(data.get("account_name")) or as_text(data.get("account_slug")),
        "account_slug": as_text(data.get("account_slug")),
        "score": score,
        "score_sort": float(score) if score not in ("", None) else -1,
        "disposition": clean_label(disposition),
        "top_wedge": clean_label(top_wedge),
        "confidence": clean_label(confidence),
        "employees_revenue": clean_label(employees_revenue),
        "buyer_intent": clean_label(buyer_intent),
        "source_folder": as_text(data.get("source_folder")),
    }


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def first_number(value: Any) -> str:
    text = as_text(value)
    match = re.search(r"\d+(?:\.\d+)?", text)
    return match.group(0) if match else ""


def first_regex(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.I)
    return match.group(1).strip() if match else ""


def top_wedge_from_hypotheses(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    for item in value:
        text = as_text(item)
        match = re.search(r"Top wedge from existing research:\s*(.+)", text, flags=re.I)
        if match:
            return match.group(1).strip()
    return ""


def first_line_matching(data: dict[str, Any], needle: str) -> str:
    needle = needle.lower()
    for value in walk_values(data):
        text = as_text(value)
        if needle in text.lower():
            return text
    return ""


def walk_values(value: Any):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)
    else:
        yield value


def clean_label(value: Any) -> str:
    return re.sub(r"\s+", " ", as_text(value)).strip()


def grouped_artifacts(artifacts: dict[str, Any]) -> list[dict[str, str]]:
    groups: dict[str, dict[str, str]] = {}
    for key, filename in artifacts.items():
        if not isinstance(filename, str) or not filename:
            continue
        suffix = "_pdf" if key.endswith("_pdf") else "_docx" if key.endswith("_docx") else ""
        base = key[: -len(suffix)] if suffix else key
        group = groups.setdefault(base, {"key": base, "label": ARTIFACT_LABELS.get(base, titleize(base))})
        group[suffix.replace("_", "") or "file"] = filename
    return list(groups.values())


def titleize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def build_payload(root: Path, accounts: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = []
    scores = []
    for account in accounts:
        summary = account["_summary"]
        if summary["score_sort"] >= 0:
            scores.append(summary["score_sort"])
        normalized.append(
            {
                **account,
                "_artifact_groups": grouped_artifacts(as_dict(account.get("artifacts"))),
            }
        )

    dispositions: dict[str, int] = {}
    for account in normalized:
        disposition = account["_summary"]["disposition"] or "Not scored"
        dispositions[disposition] = dispositions.get(disposition, 0) + 1

    return {
        "generated_by": "oci-opportunity-coach",
        "research_root": root.name,
        "account_count": len(normalized),
        "average_score": round(mean(scores), 1) if scores else None,
        "dispositions": dispositions,
        "accounts": normalized,
    }


def safe_json_script(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_html(payload: dict[str, Any]) -> str:
    data = safe_json_script(payload)
    title = f"Account Research Visualizer - {payload['research_root']}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --panel-2: #f0f3f6;
      --ink: #18212c;
      --muted: #5d6a76;
      --line: #d8dee6;
      --accent: #c74634;
      --accent-2: #1f7a8c;
      --good: #19764b;
      --warn: #a06400;
      --hold: #8c2f39;
      --shadow: 0 10px 24px rgba(31, 42, 55, 0.08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); }}
    a {{ color: var(--accent-2); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .app {{ min-height: 100vh; display: grid; grid-template-columns: minmax(320px, 410px) 1fr; }}
    .sidebar {{ border-right: 1px solid var(--line); background: var(--panel); min-height: 100vh; position: sticky; top: 0; align-self: start; }}
    .sidebar-head {{ padding: 20px; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0 0 12px; font-size: 22px; line-height: 1.2; letter-spacing: 0; }}
    .meta {{ color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 16px; }}
    .stat {{ background: var(--panel-2); border: 1px solid var(--line); border-radius: 8px; padding: 10px; }}
    .stat b {{ display: block; font-size: 18px; }}
    .stat span {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }}
    .controls {{ display: grid; gap: 10px; padding: 14px 20px; border-bottom: 1px solid var(--line); }}
    input, select {{ width: 100%; border: 1px solid var(--line); background: #fff; border-radius: 8px; padding: 10px 12px; font: inherit; color: var(--ink); }}
    .account-list {{ overflow: auto; max-height: calc(100vh - 235px); }}
    .account-row {{ width: 100%; text-align: left; border: 0; border-bottom: 1px solid var(--line); background: transparent; padding: 14px 20px; cursor: pointer; display: grid; gap: 8px; color: var(--ink); }}
    .account-row:hover, .account-row.active {{ background: #f8ece9; }}
    .account-row.active {{ box-shadow: inset 4px 0 0 var(--accent); }}
    .row-title {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; font-weight: 700; }}
    .row-sub {{ color: var(--muted); font-size: 12px; line-height: 1.35; }}
    .badge {{ display: inline-flex; align-items: center; min-height: 22px; border-radius: 999px; padding: 3px 8px; background: #eef3f4; color: #26343d; font-size: 12px; white-space: nowrap; }}
    .badge.go {{ color: var(--good); background: #eaf6ef; }}
    .badge.watch {{ color: var(--warn); background: #fff4df; }}
    .badge.hold {{ color: var(--hold); background: #fae8eb; }}
    .score {{ font-variant-numeric: tabular-nums; background: #242b35; color: white; border-radius: 7px; padding: 4px 7px; font-size: 12px; }}
    main {{ padding: 24px; min-width: 0; }}
    .detail {{ max-width: 1280px; margin: 0 auto; }}
    .detail-head {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 22px; box-shadow: var(--shadow); }}
    .detail-title {{ display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; }}
    h2 {{ margin: 0; font-size: 28px; line-height: 1.2; letter-spacing: 0; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 18px; }}
    .summary-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; min-height: 82px; background: #fff; }}
    .summary-card span {{ color: var(--muted); font-size: 12px; display: block; margin-bottom: 6px; }}
    .summary-card strong {{ font-size: 14px; line-height: 1.35; display: block; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 12px; }}
    .tab {{ border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 9px 12px; cursor: pointer; font: inherit; color: var(--ink); }}
    .tab.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 20px; box-shadow: var(--shadow); min-height: 360px; }}
    .section-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .block {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fff; min-width: 0; }}
    .block h3 {{ margin: 0 0 10px; font-size: 15px; }}
    .block h4 {{ margin: 0; font-size: 15px; line-height: 1.35; }}
    .prose {{ white-space: pre-wrap; line-height: 1.5; color: #26323d; overflow-wrap: anywhere; }}
    .muted {{ color: var(--muted); }}
    .kv {{ display: grid; grid-template-columns: 180px 1fr; gap: 8px 14px; font-size: 14px; }}
    .kv dt {{ color: var(--muted); }}
    .kv dd {{ margin: 0; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); padding: 9px; }}
    th {{ color: var(--muted); font-weight: 700; background: var(--panel-2); }}
    .file-tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .file-tab {{ border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 8px 10px; cursor: pointer; }}
    .file-tab.active {{ border-color: var(--accent-2); color: var(--accent-2); }}
    .file-frame {{ width: 100%; height: 620px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }}
    .file-actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }}
    .objection-panel {{ margin-top: 14px; }}
    .objection-list {{ display: grid; gap: 14px; }}
    .objection-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fff; display: grid; gap: 12px; }}
    .objection-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }}
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .chip {{ display: inline-flex; align-items: center; border-radius: 999px; background: var(--panel-2); border: 1px solid var(--line); color: #34404c; padding: 3px 8px; font-size: 12px; }}
    .field-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .field {{ border-top: 1px solid var(--line); padding-top: 9px; min-width: 0; }}
    .field > span {{ display: block; color: var(--muted); font-size: 12px; font-weight: 700; margin-bottom: 4px; }}
    .empty {{ color: var(--muted); padding: 36px; text-align: center; }}
    @media (max-width: 980px) {{
      .app {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: relative; min-height: auto; }}
      .account-list {{ max-height: 420px; }}
      .summary-grid, .section-grid, .field-grid {{ grid-template-columns: 1fr; }}
      .detail-title {{ display: grid; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-head">
        <h1>Account Research</h1>
        <div class="meta" id="datasetMeta"></div>
        <div class="stats">
          <div class="stat"><b id="statAccounts">0</b><span>Accounts</span></div>
          <div class="stat"><b id="statAvg">-</b><span>Avg score</span></div>
          <div class="stat"><b id="statGo">0</b><span>Go</span></div>
        </div>
      </div>
      <div class="controls">
        <input id="search" type="search" placeholder="Search accounts, wedge, intent, leadership">
        <select id="sort">
          <option value="score-desc">Score high to low</option>
          <option value="name-asc">Account A-Z</option>
          <option value="name-desc">Account Z-A</option>
          <option value="score-asc">Score low to high</option>
        </select>
      </div>
      <div class="account-list" id="accountList"></div>
    </aside>
    <main>
      <div class="detail" id="detail"></div>
    </main>
  </div>
  <script id="researchData" type="application/json">{data}</script>
  <script>
    const payload = JSON.parse(document.getElementById('researchData').textContent);
    let accounts = payload.accounts || [];
    let selectedSlug = accounts[0]?._summary?.account_slug || '';
    let selectedTab = 'overview';
    let selectedFileKey = '';

    const tabs = [
      ['overview', 'Overview'],
      ['business', 'Business'],
      ['leadership', 'Leadership'],
      ['stakeholders', 'Stakeholders'],
      ['technology', 'Technology'],
      ['oci', 'OCI Motion'],
      ['objections', 'Objections'],
      ['scorecard', 'Scorecard'],
      ['sources', 'Sources'],
      ['files', 'Files']
    ];

    function init() {{
      document.getElementById('datasetMeta').textContent = `${{payload.research_root}} · generated static viewer`;
      document.getElementById('statAccounts').textContent = payload.account_count || accounts.length;
      document.getElementById('statAvg').textContent = payload.average_score ?? '-';
      document.getElementById('statGo').textContent = payload.dispositions?.Go || 0;
      document.getElementById('search').addEventListener('input', renderList);
      document.getElementById('sort').addEventListener('change', renderList);
      renderList();
      renderDetail();
    }}

    function accountHaystack(account) {{
      return JSON.stringify(account).toLowerCase();
    }}

    function filteredAccounts() {{
      const query = document.getElementById('search').value.trim().toLowerCase();
      const sort = document.getElementById('sort').value;
      let result = query ? accounts.filter(a => accountHaystack(a).includes(query)) : [...accounts];
      result.sort((a, b) => {{
        const sa = a._summary || {{}};
        const sb = b._summary || {{}};
        if (sort === 'name-asc') return sa.account_name.localeCompare(sb.account_name);
        if (sort === 'name-desc') return sb.account_name.localeCompare(sa.account_name);
        if (sort === 'score-asc') return (sa.score_sort ?? -1) - (sb.score_sort ?? -1);
        return (sb.score_sort ?? -1) - (sa.score_sort ?? -1);
      }});
      return result;
    }}

    function renderList() {{
      const list = document.getElementById('accountList');
      const result = filteredAccounts();
      list.innerHTML = result.map(account => {{
        const s = account._summary || {{}};
        const active = s.account_slug === selectedSlug ? ' active' : '';
        return `<button class="account-row${{active}}" data-slug="${{escAttr(s.account_slug)}}">
          <div class="row-title"><span>${{esc(s.account_name)}}</span><span class="score">${{esc(s.score || '-')}}</span></div>
          <div><span class="badge ${{badgeClass(s.disposition)}}">${{esc(s.disposition || 'Not scored')}}</span></div>
          <div class="row-sub">${{esc(s.top_wedge || 'No wedge')}} · ${{esc(s.buyer_intent || 'No intent signal')}}</div>
        </button>`;
      }}).join('') || '<div class="empty">No accounts match the current filter.</div>';
      list.querySelectorAll('.account-row').forEach(button => {{
        button.addEventListener('click', () => {{
          selectedSlug = button.dataset.slug;
          selectedTab = 'overview';
          selectedFileKey = '';
          renderList();
          renderDetail();
        }});
      }});
    }}

    function renderDetail() {{
      const account = accounts.find(a => a._summary?.account_slug === selectedSlug) || accounts[0];
      const detail = document.getElementById('detail');
      if (!account) {{
        detail.innerHTML = '<div class="empty">No account research sidecars found.</div>';
        return;
      }}
      const s = account._summary || {{}};
      detail.innerHTML = `
        <section class="detail-head">
          <div class="detail-title">
            <div>
              <h2>${{esc(s.account_name)}}</h2>
              <div class="meta">${{esc(s.source_folder || account.source_folder || '')}} · ${{esc(account.research_date || '')}}</div>
            </div>
            <div class="badge ${{badgeClass(s.disposition)}}">${{esc(s.disposition || 'Not scored')}}</div>
          </div>
          <div class="summary-grid">
            ${{summaryCard('Score', s.score || '-')}}
            ${{summaryCard('Top wedge', s.top_wedge || 'Not specified')}}
            ${{summaryCard('Intent', s.buyer_intent || 'Not found')}}
            ${{summaryCard('Employees / Revenue', s.employees_revenue || 'Not found')}}
          </div>
        </section>
        <nav class="tabs">${{tabs.map(([key, label]) => `<button class="tab ${{key === selectedTab ? 'active' : ''}}" data-tab="${{key}}">${{label}}</button>`).join('')}}</nav>
        <section class="panel" id="panel">${{renderPanel(account)}}</section>
      `;
      detail.querySelectorAll('.tab').forEach(button => {{
        button.addEventListener('click', () => {{
          selectedTab = button.dataset.tab;
          selectedFileKey = '';
          renderDetail();
        }});
      }});
      bindFileTabs(account);
    }}

    function summaryCard(label, value) {{
      return `<div class="summary-card"><span>${{esc(label)}}</span><strong>${{esc(value)}}</strong></div>`;
    }}

    function renderPanel(account) {{
      if (selectedTab === 'overview') return renderOverview(account);
      if (selectedTab === 'business') return renderBusiness(account);
      if (selectedTab === 'leadership') return renderArraySection('Leadership And Buying Centers', account.leadership_buying_centers);
      if (selectedTab === 'stakeholders') return renderArraySection('Stakeholders', account.stakeholders);
      if (selectedTab === 'technology') return renderTechnology(account);
      if (selectedTab === 'oci') return renderOci(account);
      if (selectedTab === 'objections') return renderObjections(account);
      if (selectedTab === 'scorecard') return renderScorecard(account);
      if (selectedTab === 'sources') return renderArraySection('Source Log', account.source_log);
      if (selectedTab === 'files') return renderFiles(account);
      return '';
    }}

    function renderOverview(account) {{
      return `<div class="section-grid">
        <div class="block"><h3>Executive Snapshot</h3><div class="prose">${{esc(account.executive_snapshot || 'Not found in sidecar.')}}</div></div>
        <div class="block"><h3>Recommended Next Move</h3><div class="prose">${{esc(account.recommended_next_move || 'Not found in sidecar.')}}</div></div>
        <div class="block"><h3>Validation Needed</h3>${{renderListItems(account.validation_needed)}}</div>
        <div class="block"><h3>OCI Hypotheses</h3>${{renderListItems(account.oci_pursuit_hypotheses)}}</div>
      </div>`;
    }}

    function renderBusiness(account) {{
      const business = account.business_overview || {{}};
      const sales = business.sales_navigator_context || {{}};
      return `<div class="section-grid">
        <div class="block"><h3>Business Overview</h3>${{renderObject(business, ['sales_navigator_context'])}}</div>
        <div class="block"><h3>Sales Navigator Context</h3>${{renderObject(sales)}}</div>
      </div>`;
    }}

    function renderTechnology(account) {{
      return `<div class="section-grid">
        <div class="block"><h3>Technology Signals</h3>${{renderListItems(account.technology_signals)}}</div>
        <div class="block"><h3>Cloud / Stack Posture</h3>${{renderObject(account.tech_stack_cloud_posture || {{}})}}</div>
      </div>`;
    }}

    function renderOci(account) {{
      return `<div class="section-grid">
        <div class="block"><h3>OCI Pursuit Hypotheses</h3>${{renderListItems(account.oci_pursuit_hypotheses)}}</div>
        <div class="block"><h3>Workload Finder</h3>${{renderListItems(account.workload_finder)}}</div>
      </div>`;
    }}

    function renderScorecard(account) {{
      const scorecard = account.scorecard || {{}};
      const criteria = Array.isArray(scorecard.criteria) ? scorecard.criteria : [];
      return `<div class="section-grid">
        <div class="block"><h3>Scorecard Summary</h3>${{renderObject(scorecard, ['raw', 'criteria'])}}</div>
        <div class="block"><h3>Criteria</h3>${{criteria.length ? renderCriteria(criteria) : '<div class="prose">' + esc(scorecard.raw || 'Not found in sidecar.') + '</div>'}}</div>
      </div>`;
    }}

    function renderObjections(account) {{
      const prep = account.oci_buying_objection_prep || {{}};
      if (!Object.keys(prep).length) return '<div class="empty">Not found in sidecar.</div>';
      const top = Array.isArray(prep.top_objections) ? prep.top_objections : [];
      const inventory = Array.isArray(prep.objection_inventory) ? prep.objection_inventory : [];
      const cardItems = inventory.length ? inventory : top;
      return `<div class="section-grid">
        <div class="block"><h3>Executive Objection Summary</h3>${{renderValue(prep.summary || 'Not found in sidecar.')}}</div>
        <div class="block"><h3>Top Objections</h3>${{renderListItems(top)}}</div>
        <div class="block"><h3>Discovery Questions</h3>${{renderListItems(prep.discovery_questions)}}</div>
        <div class="block"><h3>Proof To Prepare</h3>${{renderListItems(prep.proof_to_prepare)}}</div>
        <div class="block"><h3>Stakeholders To Engage</h3>${{renderListItems(prep.stakeholders_to_engage)}}</div>
        <div class="block"><h3>Next Actions</h3>${{renderListItems(prep.next_actions)}}</div>
      </div>
      <div class="block objection-panel"><h3>Prioritized Objection Inventory</h3>${{renderObjectionCards(cardItems)}}</div>
      <div class="block objection-panel"><h3>Source Notes</h3>${{renderListItems(prep.source_notes)}}</div>`;
    }}

    function renderObjectionCards(items) {{
      if (!Array.isArray(items) || !items.length) return '<div class="muted">Not found in sidecar.</div>';
      return `<div class="objection-list">${{items.map((item, index) => renderObjectionCard(item, index)).join('')}}</div>`;
    }}

    function renderObjectionCard(item, index) {{
      if (!item || typeof item !== 'object') {{
        return `<article class="objection-card">
          <div class="objection-head"><h4>${{esc(String(item || 'Objection ' + (index + 1)))}}</h4><span class="badge">#${{index + 1}}</span></div>
        </article>`;
      }}
      const chips = [
        item.category,
        item.confidence ? `Confidence: ${{item.confidence}}` : '',
        item.likely_speaker ? `Speaker: ${{item.likely_speaker}}` : '',
        item.impact ? `Impact: ${{item.impact}}` : ''
      ].filter(Boolean);
      return `<article class="objection-card">
        <div class="objection-head">
          <h4>${{esc(item.objection || 'Objection ' + (index + 1))}}</h4>
          <span class="badge">#${{index + 1}}</span>
        </div>
        <div class="chip-row">${{chips.map(chip => `<span class="chip">${{esc(chip)}}</span>`).join('')}}</div>
        <div class="field-grid">
          ${{objectionField('Customer language', item.customer_language)}}
          ${{objectionField('Account-specific trigger', item.account_specific_trigger)}}
          ${{objectionField('Evidence source', item.evidence_source)}}
          ${{objectionField('Discovery questions', item.discovery_questions)}}
          ${{objectionField('OCI response strategy', item.response_strategy)}}
          ${{objectionField('Proof to prepare', item.proof_to_prepare)}}
          ${{objectionField('Risk if unresolved', item.risk_if_unresolved)}}
          ${{objectionField('Next best action', item.next_best_action)}}
        </div>
      </article>`;
    }}

    function objectionField(label, value) {{
      if (value === undefined || value === null || value === '') return '';
      if (Array.isArray(value) && !value.length) return '';
      return `<div class="field"><span>${{esc(label)}}</span>${{renderValue(value)}}</div>`;
    }}

    function renderArraySection(title, value) {{
      return `<div class="block"><h3>${{esc(title)}}</h3>${{renderListItems(value)}}</div>`;
    }}

    function renderFiles(account) {{
      const groups = account._artifact_groups || [];
      if (!groups.length) return '<div class="empty">No linked artifacts found in this sidecar.</div>';
      if (!selectedFileKey) selectedFileKey = groups[0].key;
      const selected = groups.find(g => g.key === selectedFileKey) || groups[0];
      const folder = account._folder_path || account.source_folder || account.account_slug;
      const pdf = selected.pdf ? `${{folder}}/${{selected.pdf}}` : '';
      const docx = selected.docx ? `${{folder}}/${{selected.docx}}` : '';
      const frame = pdf ? `<iframe class="file-frame" src="${{escAttr(pdf)}}"></iframe>` : '<div class="empty">No PDF preview for this artifact. Use the document link above.</div>';
      return `<div class="file-tabs">${{groups.map(g => `<button class="file-tab ${{g.key === selected.key ? 'active' : ''}}" data-file-key="${{escAttr(g.key)}}">${{esc(g.label)}}</button>`).join('')}}</div>
        <div class="file-actions">
          ${{pdf ? `<a href="${{escAttr(pdf)}}" target="_blank">Open PDF</a>` : ''}}
          ${{docx ? `<a href="${{escAttr(docx)}}">Open DOCX</a>` : ''}}
          <a href="${{escAttr(folder + '/account-research.json')}}" target="_blank">Open JSON</a>
        </div>
        ${{frame}}`;
    }}

    function bindFileTabs(account) {{
      document.querySelectorAll('.file-tab').forEach(button => {{
        button.addEventListener('click', () => {{
          selectedFileKey = button.dataset.fileKey;
          document.getElementById('panel').innerHTML = renderFiles(account);
          bindFileTabs(account);
        }});
      }});
    }}

    function renderObject(obj, omit = []) {{
      const entries = Object.entries(obj || {{}}).filter(([key]) => !key.startsWith('_') && !omit.includes(key));
      if (!entries.length) return '<div class="muted">Not found in sidecar.</div>';
      return `<dl class="kv">${{entries.map(([key, value]) => `<dt>${{esc(titleize(key))}}</dt><dd>${{renderValue(value)}}</dd>`).join('')}}</dl>`;
    }}

    function renderValue(value) {{
      if (Array.isArray(value)) return renderListItems(value);
      if (value && typeof value === 'object') return renderObject(value);
      return `<span class="prose">${{esc(value ?? '')}}</span>`;
    }}

    function renderListItems(items) {{
      if (!Array.isArray(items)) {{
        const text = items ? String(items) : '';
        return text ? `<div class="prose">${{esc(text)}}</div>` : '<div class="muted">Not found in sidecar.</div>';
      }}
      if (!items.length) return '<div class="muted">Not found in sidecar.</div>';
      return `<ul>${{items.map(item => `<li class="prose">${{esc(typeof item === 'object' ? JSON.stringify(item, null, 2) : item)}}</li>`).join('')}}</ul>`;
    }}

    function renderCriteria(criteria) {{
      return `<table><thead><tr><th>Criterion</th><th>Values / Notes</th></tr></thead><tbody>
        ${{criteria.map(row => `<tr><td>${{esc(row.criterion || '')}}</td><td>${{esc((row.following_values || []).join(' · '))}}</td></tr>`).join('')}}
      </tbody></table>`;
    }}

    function badgeClass(value) {{
      const v = String(value || '').toLowerCase();
      if (v.includes('go')) return 'go';
      if (v.includes('watch')) return 'watch';
      if (v.includes('hold')) return 'hold';
      return '';
    }}

    function titleize(key) {{
      return String(key).replaceAll('_', ' ').replaceAll('/', ' / ').replace(/\\b\\w/g, c => c.toUpperCase());
    }}

    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}

    function escAttr(value) {{
      return esc(value).replace(/`/g, '&#96;');
    }}

    init();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_root", type=Path, help="Account research root containing per-account folders")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output HTML path. Defaults to <research_root>/account-research-visualizer.html",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.research_root.resolve()
    if not root.exists():
        raise SystemExit(f"Research root does not exist: {root}")
    accounts = load_sidecars(root)
    if not accounts:
        raise SystemExit(f"No account-research.json files found under {root}")
    payload = build_payload(root, accounts)
    output = args.output.resolve() if args.output else root / "account-research-visualizer.html"
    output.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Accounts: {len(accounts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
