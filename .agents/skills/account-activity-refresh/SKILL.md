---
name: account-activity-refresh
description: Refresh account workbench notes and prepare account status or meeting prep from Outlook activity, Zoom-generated meeting notes, Outlook Calendar meetings, Slack conversations from internal or external account channels, and existing Opportunity Workbench account notes. Use when the user asks to refresh notes for this week, import Zoom/Outlook/Slack context into researched account folders, summarize account status from notes and conversations, find upcoming account meetings, or prepare for a meeting using the account's workbench notes plus Outlook and Slack activity.
---

# Account Activity Refresh

## Overview

Use this skill after `oci-opportunity-coach` has created account research folders and the Opportunity Workbench has initialized `workbench/notes.json`. This skill keeps those account notes current from Outlook, Zoom, and Slack activity, then uses the refreshed notes for account status and meeting prep.

This skill is an activity-sync and prep layer. Use `oci-opportunity-coach` for new account research, pursuit strategy, stakeholder mapping, outreach kits, and deeper opportunity recommendations.

## Account Layout

Default account root is the folder the user names, commonly `Kellin`. Each researched account folder should contain:

- `account-research.json`
- `workbench/notes.json`
- `workbench/activity.json`

Workbench notes are JSON objects with:

- `id`
- `category`: one of `meeting-minutes`, `phone-conversation`, `field-insight`, `customer-insight`, `internal-note`, `next-step`, `other`
- `body`
- `takenAt`
- `createdAt`
- `updatedAt`

When importing Outlook, Zoom, or Slack notes, preserve existing user notes. Append only new, de-duplicated notes. Treat a calendar invite, Zoom AI summary, Zoom transcript, Slack conversation digest, Slack file summary, and user-authored meeting note as separate source artifacts; import each useful artifact once.

## Source Rules

- Treat Outlook emails, Zoom AI notes, calendar entries, Slack messages/files, account research, and workbench notes as sensitive customer context.
- Prefer user-authored notes when the user says "look only at notes I have taken".
- Do not use public research unless the user explicitly asks for account research or external context.
- Label each imported note with its source in the note body, such as `Source: Zoom AI Companion meeting summary email`.
- Do not consider a refresh complete for a Zoom meeting until Zoom-generated minutes have been searched for through available mail tools or saved local files.
- If Outlook mail tools are unavailable, say so and use Outlook Calendar plus existing workbench notes only. Mark the sync as partial and do not claim Zoom email notes were imported.
- If a saved transcript or Zoom summary file is found locally, verify it matches the account, meeting title, participants, or meeting date before importing it.
- For Slack, use public-channel search when sufficient. Use private-channel, DM, or external shared-channel search only when the available Slack tool allows it and the user request authorizes account-related Slack context.
- Do not import raw Slack dumps. Summarize relevant conversation threads into concise account notes with links/source identifiers when available.
- If multiple accounts could match a meeting, ask the smallest clarifying question unless attendee domains or the title clearly identify one account.

## Refresh Notes Workflow

When the user asks to "refresh notes for this week" or similar:

1. Locate the account root:
   - Use the user-provided root if present.
   - Otherwise inspect Opportunity Workbench rep roots or use `Kellin` if it exists.
2. Scan account folders for `account-research.json`.
3. Build an account matching index from:
   - folder slug
   - `account_name`
   - `_summary.account_name`
   - known domains and stakeholder email domains in `account-research.json`
4. Determine the refresh window:
   - Default to the current calendar week in the user's timezone.
   - Respect explicit ranges like "last week", "this month", or exact dates.
5. Query Outlook Calendar for meetings in the window.
6. Search Slack for account-relevant conversations in the window when Slack tools are available:
   - Search by account name, common abbreviation, folder slug tokens, stakeholder names, customer domains, opportunity names, and known channel names from user notes or prior results.
   - For known account channels, search within the channel first. For unknown channels, search broadly and then narrow to likely internal or external account channels.
   - Include Slack files only when they are account-relevant and useful, such as meeting notes, architecture docs, screenshots, issue summaries, or customer shared docs.
7. For every matched Zoom meeting, search for Zoom-generated minutes before writing the final sync report:
   - Outlook mail source, when available:
     - likely senders include Zoom, Zoom AI Companion, `no-reply@zoom.us`, `no-reply@zoom.com`, or Oracle Zoom relay addresses
     - likely subjects include `meeting summary`, `AI Companion`, `meeting notes`, `transcript`, `recording`, account name, meeting title, or Zoom meeting ID
     - search by meeting title, account name, participant email domain, meeting ID, and a time window from meeting start through 48 hours after the meeting
   - Local files, when mail is unavailable or the user has exported summaries:
     - search likely folders such as `Downloads` and the account output folder for account name, meeting title, participant names, Zoom meeting ID, `AI Companion`, `meeting summary`, `transcript`, or `quick recap`
     - inspect candidate files before importing and reject unrelated transcripts
8. Match each meeting, calendar invite, Zoom summary, transcript, Slack thread, Slack channel digest, Slack file, or note to one account.
9. Convert each relevant artifact into a workbench note:
   - category `meeting-minutes`
   - `takenAt` from the meeting start time or email received time
   - body with title, date, attendees, source, summary, decisions, risks, and next steps
   - for Zoom AI summaries, preserve the AI-generated sections such as `Quick recap`, `Summary`, `Next steps`, and topic sections when present
   - for Slack summaries, use category `internal-note` for internal Oracle/account-team conversations, `customer-insight` for customer-visible/external shared-channel signals, or `next-step` when the thread is primarily an action item
10. Write imports through `scripts/import_activity_notes.py`.
11. Report:
   - accounts updated
   - notes imported
   - whether Zoom-generated minutes were found and imported
   - whether Slack context was searched, which channels or searches were used, and how many Slack notes were imported
   - skipped ambiguous items
   - unavailable sources, especially Outlook mail or Slack if not connected
   - partial-sync status when calendar context was imported but Zoom-generated minutes could not be accessed

## Slack Import Rules

Use these rules when Slack context is available:

- Import summarized Slack context as account notes, not raw message logs.
- Preserve enough source detail for traceability:
  - Slack channel or DM type when visible
  - message/thread date range
  - key participants when relevant
  - message or thread links/IDs when available
  - search terms used when no channel is known
- Choose the source label deliberately:
  - `Source: Slack internal account channel`
  - `Source: Slack external shared account channel`
  - `Source: Slack account search`
  - `Source: Slack file summary`
- Use `external_id` values that de-duplicate refreshes, such as:
  - `slack-channel:<channel-id-or-name>:<start-date>:<end-date>:<hash-of-topic>`
  - `slack-thread:<channel-id-or-name>:<thread-ts>`
  - `slack-file:<file-id>`
- Separate signal from noise. Import only threads that contain one or more of:
  - customer priorities, blockers, risks, escalations, decisions, asks, objections, technical findings, consumption/cost signals, meeting outcomes, action items, stakeholder updates, or next steps
- For high-volume channels, create one digest note per account per refresh window unless individual threads are important enough to stand alone.
- For external Slack Connect or customer-visible channels, label the note as customer-visible context and avoid adding private Oracle-only commentary into that same note.
- For internal Oracle channels, label the note as internal context and do not present it as customer-stated fact unless the underlying message came from a customer-visible source.
- If Slack search finds ambiguous conversations across similarly named accounts, do not import until the account mapping is clear.

Suggested Slack note body shape:

```text
Slack activity digest: <account> - <date range>

Source: Slack internal account channel
Channel/search: <channel or search terms>
Participants: <key names if useful>

Summary
- <short account-relevant summary>

Signals
- <customer or internal signal>

Risks / blockers
- <risk or blocker>

Decisions / next steps
- <owner>: <action>

Source details
- <message/thread/file links or IDs if available>
```

## Zoom Minutes Import Rules

Use these rules when the meeting source is Zoom:

- Import the calendar invite only as `Source: Outlook Calendar invite`.
- Import the autogenerated Zoom minutes separately as `Source: Zoom AI Companion meeting summary email` or `Source: Saved Zoom transcript file`.
- Prefer the Zoom AI summary over a raw transcript for the main meeting-minutes note. If both are available, import the summary and either skip the transcript or import a concise transcript-derived note only when it adds decisions, objections, or next steps not present in the summary.
- Do not import a transcript only because it is in `Downloads`; it must match the account or meeting.
- If only Zoom logistics are present in the calendar body, write that limitation into the sync report, not as a customer insight.
- If a previous calendar-only note exists and the Zoom summary is later found, import the Zoom summary as a new note. Do not overwrite the calendar note unless the user asks.

## Status Workflow

When the user asks for status for an account:

1. Identify the account folder.
2. Read `workbench/notes.json` first.
3. Read `account-research.json` only for account identity, stakeholders, and existing pursuit context.
4. Query Outlook Calendar for upcoming and recent meetings for the account if calendar tools are available.
5. Query Slack for recent account activity if Slack tools are available and account Slack context is in scope.
6. Return a concise status with:
   - recent activity
   - observed customer priorities
   - open risks or blockers
   - next scheduled meetings
   - recent Slack signals when available
   - recommended next actions
   - assumptions and source limits

## Meeting Prep Workflow

When the user asks to prepare for a meeting with an account:

1. If no meeting is named, search Outlook Calendar for upcoming meetings this week whose title, attendees, or notes match the account.
2. If exactly one meeting matches, use it. If several plausible meetings match, ask which meeting.
3. Read the account's `workbench/notes.json`.
4. Use account research only for stable background and known stakeholders.
5. Query recent Slack account context when available, especially for customer asks, blockers, escalations, or internal prep threads related to the meeting.
6. Prepare:
   - likely agenda
   - what the user should share from their notes
   - questions to ask
   - customer-specific risks and follow-ups
   - suggested talk track
   - post-meeting note template

## Import Script

Use `scripts/import_activity_notes.py` to merge notes into account workbench files.

Input is a JSON file:

```json
{
  "root": "/absolute/path/to/Kellin",
  "imports": [
    {
      "account_slug": "008-blue-yonder-inc",
      "category": "meeting-minutes",
      "takenAt": "2026-06-23T14:00:00Z",
      "source": "Outlook Zoom meeting notes",
      "external_id": "outlook-message-or-event-id",
      "body": "Meeting title...\nSource: Outlook Zoom meeting notes\n..."
    },
    {
      "account_slug": "008-blue-yonder-inc",
      "category": "internal-note",
      "takenAt": "2026-06-23T20:00:00Z",
      "source": "Slack internal account channel",
      "external_id": "slack-channel:blue-yonder:2026-06-22:2026-06-28:cost-drift",
      "body": "Slack activity digest...\nSource: Slack internal account channel\n..."
    }
  ]
}
```

Run:

```bash
python3 .agents/skills/account-activity-refresh/scripts/import_activity_notes.py /tmp/account-note-imports.json
```

The script de-duplicates by `external_id` when present and by normalized body hash otherwise.

## Output Style

- Be explicit about what was imported versus already present.
- Keep field output concise and action-oriented.
- Separate `known from notes`, `calendar-derived`, `imported from Outlook/Zoom`, `imported from Slack`, and `assumptions`.
- Never bury ambiguity. List ambiguous meetings or notes that need user mapping.
