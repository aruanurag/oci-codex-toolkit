#!/usr/bin/env python3
"""Import Outlook/Zoom activity notes into Opportunity Workbench account notes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ALLOWED_CATEGORIES = {
    "meeting-minutes",
    "phone-conversation",
    "field-insight",
    "customer-insight",
    "internal-note",
    "next-step",
    "other",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: str) -> str:
    normalized = " ".join(value.split()).strip().lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def read_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def note_key(note: dict[str, Any]) -> str:
    external_id = str(note.get("external_id") or "").strip()
    if external_id:
        return f"external:{external_id}"
    return f"body:{stable_hash(str(note.get('body') or ''))}"


def normalize_note(raw: dict[str, Any]) -> dict[str, Any]:
    body = str(raw.get("body") or "").strip()
    if not body:
        raise ValueError("import note body is required")
    category = str(raw.get("category") or "meeting-minutes")
    if category not in ALLOWED_CATEGORIES:
        category = "other"
    timestamp = now_iso()
    source = str(raw.get("source") or "").strip()
    external_id = str(raw.get("external_id") or "").strip()
    metadata_lines = []
    if source and "source:" not in body.lower():
        metadata_lines.append(f"Source: {source}")
    if external_id and "external id:" not in body.lower():
        metadata_lines.append(f"External ID: {external_id}")
    if metadata_lines:
        body = body.rstrip() + "\n\n" + "\n".join(metadata_lines)
    note = {
        "id": str(raw.get("id") or f"note-{uuid4()}"),
        "category": category,
        "body": body,
        "takenAt": str(raw.get("takenAt") or timestamp),
        "createdAt": str(raw.get("createdAt") or timestamp),
        "updatedAt": timestamp,
    }
    if source:
        note["source"] = source
    if external_id:
        note["external_id"] = external_id
    return note


def append_activity(account_dir: Path, event: dict[str, Any]) -> None:
    activity_path = account_dir / "workbench" / "activity.json"
    activity = read_json(activity_path, [])
    if not isinstance(activity, list):
        activity = []
    activity.append({**event, "at": now_iso()})
    write_json(activity_path, activity[-500:])


def import_notes(root: Path, imports: list[dict[str, Any]]) -> dict[str, Any]:
    seen_accounts: set[str] = set()
    summary: dict[str, Any] = {
        "root": str(root),
        "accounts_seen": 0,
        "imported": 0,
        "duplicates": 0,
        "missing_accounts": [],
        "updated_accounts": {},
    }
    for raw in imports:
        slug = str(raw.get("account_slug") or "").strip()
        if not slug or "/" in slug or "\\" in slug:
            raise ValueError(f"invalid account_slug: {slug!r}")
        account_dir = root / slug
        if not (account_dir / "account-research.json").exists():
            summary["missing_accounts"].append(slug)
            continue
        notes_path = account_dir / "workbench" / "notes.json"
        notes = read_json(notes_path, [])
        if not isinstance(notes, list):
            notes = []
        seen_accounts.add(slug)
        existing_keys = {note_key(note) for note in notes if isinstance(note, dict)}
        note = normalize_note(raw)
        key = note_key(note)
        if key in existing_keys:
            summary["duplicates"] += 1
            continue
        notes.append(note)
        write_json(notes_path, notes)
        append_activity(account_dir, {
            "type": "notes.imported",
            "source": note.get("source", "account-activity-refresh"),
            "external_id": note.get("external_id", ""),
            "note_id": note["id"],
        })
        summary["imported"] += 1
        summary["updated_accounts"][slug] = summary["updated_accounts"].get(slug, 0) + 1
    summary["accounts_seen"] = len(seen_accounts)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON import file")
    args = parser.parse_args()
    payload = read_json(args.input)
    if not isinstance(payload, dict):
        raise SystemExit("input must be a JSON object")
    root = Path(str(payload.get("root") or "")).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"root directory not found: {root}")
    imports = payload.get("imports")
    if not isinstance(imports, list):
        raise SystemExit("input.imports must be a list")
    summary = import_notes(root, imports)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
