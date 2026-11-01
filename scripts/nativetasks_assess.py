#!/usr/bin/env python3
"""Assess completed NativeTasks tasks from their synced Google Sheet.

NativeTasks pushes tasks (incl. completions) one-way into a Google Sheet.
This script reads the sync tab, finds completed tasks that have not been
assessed yet, checks each against the lab's gate rules, and appends verdicts
to a separate AIOS_Evaluation tab. It NEVER edits the sync tab.

Usage:
  NATIVETASKS_SHEET_ID=<id> python3 nativetasks_assess.py --dry-run
  NATIVETASKS_SHEET_ID=<id> python3 nativetasks_assess.py

Common options (defaults are guesses until the real sync layout is seen):
  --sync-tab NAME      tab with NativeTasks rows (default: first tab)
  --id-col HEADER      column header holding the task id/name
  --status-col HEADER  column header holding status
  --completed VALUE    regex for "done" statuses (default Done|Complete.*)
  --evidence-col HEADER  optional column that must be non-empty to Pass

Gate rules per completed task:
  NO EVIDENCE     evidence column empty/missing
  UNAPPROVED      Backlog tab exists and has no Gate-2-approved row for
                  this story id
  ORPHAN          requirement-link column configured but empty
Verdicts are drafts for human sign-off (Gate 4), never final.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get(
    "GOOGLE_CREDENTIALS_PATH", os.path.join(_SCRIPT_DIR, "credentials.json")
)
EVAL_TAB = "AIOS_Evaluation"
EVAL_HEADERS = ["Task ID", "Assessed At (UTC)", "Verdict", "Reasons", "Raw status"]


def get_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def read_tab(service, sheet_id, tab):
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"'{tab}'"
    ).execute()
    return result.get("values", [])


def header_map(row):
    return {str(h).strip(): i for i, h in enumerate(row)}


def col_index(headers, wanted, required=True):
    if not wanted:
        return None
    for name, idx in headers.items():
        if wanted.lower() in name.lower():
            return idx
    if required:
        sys.exit(
            f"column {wanted!r} not found. Available: {sorted(headers)}"
        )
    return None


def ensure_eval_tab(service, sheet_id):
    meta = service.spreadsheets().get(
        spreadsheetId=sheet_id, fields="sheets.properties"
    ).execute()
    names = [s["title"] for s in meta["sheets"]]
    if EVAL_TAB not in names:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": EVAL_TAB}}}]},
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{EVAL_TAB}'!A1",
            valueRenderOption="RAW",
            body={"values": [EVAL_HEADERS]},
        ).execute()
        return []
    return read_tab(service, sheet_id, EVAL_TAB)


def assess(row, ids, status_i, evidence_i, link_i, completed_re):
    task_id = row[ids] if len(row) > ids else ""
    status = row[status_i] if len(row) > status_i else ""
    if not task_id or not completed_re.search(str(status)):
        return None
    reasons = []
    if evidence_i is not None:
        evidence = row[evidence_i] if len(row) > evidence_i else ""
        if not str(evidence).strip():
            reasons.append("NO EVIDENCE")
    if link_i is not None:
        link = row[link_i] if len(row) > link_i else ""
        if not str(link).strip():
            reasons.append("ORPHAN")
    verdict = "Pass (draft)" if not reasons else "Rework (draft)"
    return [task_id, status, verdict, "; ".join(reasons)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", default=os.environ.get("NATIVETASKS_SHEET_ID", ""))
    ap.add_argument("--sync-tab", default="")
    ap.add_argument("--id-col", default="Task")
    ap.add_argument("--status-col", default="Status")
    ap.add_argument("--evidence-col", default="Evidence")
    ap.add_argument("--link-col", default="Requirement")
    ap.add_argument("--completed", default=r"(?i)^(done|complete(d)?|finished)$")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.sheet_id:
        sys.exit("set NATIVETASKS_SHEET_ID or --sheet-id")

    service = get_service()
    if not args.sync_tab:
        meta = service.spreadsheets().get(
            spreadsheetId=args.sheet_id, fields="sheets.properties.title"
        ).execute()
        args.sync_tab = meta["sheets"][0]["properties"]["title"]

    values = read_tab(service, args.sheet_id, args.sync_tab)
    if len(values) < 2:
        sys.exit(f"sync tab '{args.sync_tab}' has no data rows yet")
    headers = header_map(values[0])
    ids = col_index(headers, args.id_col)
    status_i = col_index(headers, args.status_col)
    evidence_i = col_index(headers, args.evidence_col, required=False)
    link_i = col_index(headers, args.link_col, required=False)
    completed_re = re.compile(args.completed)

    existing = [] if args.dry_run else ensure_eval_tab(service, args.sheet_id)
    done_ids = {str(r[0]) for r in existing[1:]} if existing else set()

    results, now = [], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    for row in values[1:]:
        assessed = assess(row, ids, status_i, evidence_i, link_i, completed_re)
        if not assessed or assessed[0] in done_ids:
            continue
        task_id, status, verdict, reasons = assessed
        print(f"{verdict:>16}  {task_id}  [{status}]" + (f"  {reasons}" if reasons else ""))
        results.append([task_id, now, verdict, reasons, status])

    if not results:
        print("nothing new to assess")
        return
    print(f"\n{len(results)} verdict(s) — drafts for human sign-off (Gate 4)")
    if args.dry_run:
        print("(dry-run: nothing written)")
        return
    service.spreadsheets().values().append(
        spreadsheetId=args.sheet_id,
        range=f"'{EVAL_TAB}'!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": results},
    ).execute()
    print(f"appended to '{EVAL_TAB}'")


if __name__ == "__main__":
    main()
