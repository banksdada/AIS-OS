#!/usr/bin/env python3
"""Create the Beauty Booked Up keyword tracking Sheet as the user.

Usage:
  python3 scripts/create-bbu-keywords-sheet.py

Requires a refreshed DRIVE_REFRESH_TOKEN from scripts/gdrive-authorize.py
with Drive and Sheets scopes.
"""

import argparse
import csv
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"
SEED_PATH = REPO_ROOT / "projects" / "beautybookedup" / "keyword-bank.csv"
MICROSITE_SEED_PATH = REPO_ROOT / "projects" / "beautybookedup" / "microsite-keyword-bank.csv"

TITLE = "Beauty Booked Up - keywords (Wigan and Manchester)"
PARENT_FOLDER_ID = "1J8HSyf8QjfCLh5PH8Atm-iGsyQZml-7H"
KEYWORDS_TAB = "Keywords"
MICROSITE_TAB = "Microsites"
INSTRUCTIONS_TAB = "How to use"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def read_env(name):
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        if line.strip().startswith(name + "="):
            return line.strip().split("=", 1)[1].strip()
    return None


def get_credentials():
    token = os.environ.get("DRIVE_REFRESH_TOKEN") or read_env("DRIVE_REFRESH_TOKEN")
    client_id = os.environ.get("GMAIL_CLIENT_ID") or read_env("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET") or read_env("GMAIL_CLIENT_SECRET")
    if not token or not client_id or not client_secret:
        print("ERROR: Drive/Sheets credentials are missing. Run scripts/gdrive-authorize.py first.")
        raise SystemExit(1)

    creds = Credentials(
        token=None,
        refresh_token=token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    try:
        creds.refresh(Request())
    except Exception as exc:
        print("ERROR: could not refresh Drive/Sheets access. Run scripts/gdrive-authorize.py again.")
        print(str(exc))
        raise SystemExit(1)
    return creds


def load_rows(path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = [[row.get(header, "") for header in headers] for row in reader]
    return headers, rows


def column_letter(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def instructions():
    return [
        ["Field", "What it means"],
        ["Owner", "Banks Dada / Sharon Dada. Managed by the AIOS."],
        ["Keywords tab", "730 blog keywords, one per row. Filter by Status to choose what gets drafted."],
        ["Microsites tab", "500 planned microsite ideas built from location, niche business type, challenge and outcome."],
        ["Status: new", "Ready for the next drafting run."],
        ["Status: drafted", "A review draft exists. Check Draft file."],
        ["Status: approved", "Approved by Sharon or Banks. Still not published automatically."],
        ["Status: later", "Future microsite/client-facing keyword. Do not draft for Beauty Booked Up yet."],
        ["PyRunner script", "scripts/pyrunner/bbs-blog-drafter.py reads this Sheet twice daily at 07:00 and 19:00 UK time."],
        ["Draft output", "projects/beautybookedup/content/drafts/"],
        ["Publishing", "Nothing is published automatically. Drafts are for review only."],
        ["Microsite status", "Planned only. Do not create a project, folder or repo without explicit approval."],
        ["Do not edit by hand", "The drafting script updates Status, Draft file, Approved and Last used."],
    ]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spreadsheet-id", help="Update an existing Sheet instead of creating a new one")
    return parser.parse_args()


def main():
    args = parse_args()
    creds = get_credentials()
    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    headers, keyword_rows = load_rows(SEED_PATH)
    microsite_headers, microsite_rows = load_rows(MICROSITE_SEED_PATH)
    keyword_values = [headers] + keyword_rows
    microsite_values = [microsite_headers] + microsite_rows
    instruction_values = instructions()

    if args.spreadsheet_id:
        action = "Updated"
        spreadsheet_id = args.spreadsheet_id
    else:
        action = "Created"
        spreadsheet = sheets.spreadsheets().create(
            body={
                "properties": {"title": TITLE},
                "sheets": [
                    {"properties": {"title": KEYWORDS_TAB}},
                    {"properties": {"title": MICROSITE_TAB}},
                    {"properties": {"title": INSTRUCTIONS_TAB}},
                ],
            }
        ).execute()
        spreadsheet_id = spreadsheet["spreadsheetId"]

    metadata = sheets.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="spreadsheetId,spreadsheetUrl,sheets(properties(sheetId,title))",
    ).execute()
    sheet_ids = {
        sheet["properties"]["title"]: sheet["properties"]["sheetId"]
        for sheet in metadata.get("sheets", [])
    }
    missing_tabs = [
        tab for tab in (KEYWORDS_TAB, MICROSITE_TAB, INSTRUCTIONS_TAB) if tab not in sheet_ids
    ]
    if missing_tabs:
        sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {"addSheet": {"properties": {"title": tab}}} for tab in missing_tabs
                ]
            },
        ).execute()
        metadata = sheets.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="spreadsheetId,spreadsheetUrl,sheets(properties(sheetId,title))",
        ).execute()
        sheet_ids = {
            sheet["properties"]["title"]: sheet["properties"]["sheetId"]
            for sheet in metadata.get("sheets", [])
        }
    spreadsheet = metadata
    required_tabs = (KEYWORDS_TAB, MICROSITE_TAB, INSTRUCTIONS_TAB)
    if any(tab not in sheet_ids for tab in required_tabs):
        print(f"ERROR: expected tabs {required_tabs!r} were not found.")
        raise SystemExit(1)
    keywords_sheet_id = sheet_ids[KEYWORDS_TAB]
    microsites_sheet_id = sheet_ids[MICROSITE_TAB]
    instructions_sheet_id = sheet_ids[INSTRUCTIONS_TAB]
    status_column = headers.index("status") if "status" in headers else 3
    microsite_status_column = (
        microsite_headers.index("status") if "status" in microsite_headers else 1
    )
    sheets.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "RAW",
            "data": [
                {
                    "range": f"{KEYWORDS_TAB}!A1:{column_letter(len(headers))}{len(keyword_values)}",
                    "values": keyword_values,
                },
                {
                    "range": f"{MICROSITE_TAB}!A1:{column_letter(len(microsite_headers))}{len(microsite_values)}",
                    "values": microsite_values,
                },
                {
                    "range": f"{INSTRUCTIONS_TAB}!A1:B{len(instruction_values)}",
                    "values": instruction_values,
                },
            ],
        },
    ).execute()

    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": keywords_sheet_id,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": keywords_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                },
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": keywords_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": len(keyword_values),
                            "startColumnIndex": status_column,
                            "endColumnIndex": status_column + 1,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": "new"},
                                    {"userEnteredValue": "drafted"},
                                    {"userEnteredValue": "approved"},
                                    {"userEnteredValue": "later"},
                                ],
                            },
                            "showCustomUi": True,
                        },
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": keywords_sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": len(headers),
                        }
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": microsites_sheet_id,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": microsites_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                },
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": microsites_sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": len(microsite_values),
                            "startColumnIndex": microsite_status_column,
                            "endColumnIndex": microsite_status_column + 1,
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_LIST",
                                "values": [
                                    {"userEnteredValue": "planned"},
                                    {"userEnteredValue": "building"},
                                    {"userEnteredValue": "live"},
                                    {"userEnteredValue": "archived"},
                                ],
                            },
                            "showCustomUi": True,
                        },
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": microsites_sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": len(microsite_headers),
                        }
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": instructions_sheet_id,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": instructions_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": instructions_sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 2,
                        }
                    }
                },
            ]
        },
    ).execute()

    moved = drive.files().update(
        fileId=spreadsheet_id,
        addParents=PARENT_FOLDER_ID,
        fields="id,parents,webViewLink",
    ).execute()

    keyword_check = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"{KEYWORDS_TAB}!A:A"
    ).execute()
    microsite_check = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=f"{MICROSITE_TAB}!A:A"
    ).execute()

    print(action + ":", TITLE)
    print("Sheet ID:", spreadsheet_id)
    print("URL:", spreadsheet.get("spreadsheetUrl", ""))
    print("Drive URL:", moved.get("webViewLink", ""))
    print("Parent folder:", PARENT_FOLDER_ID)
    print("Keywords seeded:", len(keyword_rows))
    print("Keywords verified:", max(len(keyword_check.get("values", [])) - 1, 0))
    print("Microsites seeded:", len(microsite_rows))
    print("Microsites verified:", max(len(microsite_check.get("values", [])) - 1, 0))


if __name__ == "__main__":
    main()
