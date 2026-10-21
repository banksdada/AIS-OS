#!/usr/bin/env python3
"""
Client tracker for webawesome.co.uk.
Manages a Google Sheet as a lightweight CRM.

Usage:
  python3 client-tracker.py list                    # list all clients
  python3 client-tracker.py add "Name" "Email" "Stage"  # add a client
  python3 client-tracker.py stage "Name" "New Stage"    # move a client to a new stage

Stages (in pipeline order):
  Lead → Contacted → Qualified → Proposal → Negotiation → Won → Lost → Dormant

The Stage column in the sheet is a strict drop-down limited to these values,
sourced from a hidden 'Stages' tab. Add/stage refuse anything not on the list,
so a typo can't silently split the pipeline or break the colour coding.

Usage:
  python3 client-tracker.py list                    # list all clients
  python3 client-tracker.py add "Name" "Email" "Stage"  # add a client
  python3 client-tracker.py stage "Name" "New Stage"    # move a client to a new stage
  python3 client-tracker.py stages                  # list the valid stages
  python3 client-tracker.py format                  # apply styling + the stage drop-down
"""

import os
import sys
import argparse
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_PATH', os.path.join(_SCRIPT_DIR, 'credentials.json'))
SPREADSHEET_ID = os.environ.get('CLIENT_TRACKER_ID', '')  # set after creating the sheet

HEADERS = ['Name', 'Email', 'Stage', 'Last Contact', 'Notes']

# The pipeline, in order. This is the single source of truth: the sheet
# drop-down, the colour rules and the CLI validation all read from it.
STAGES = [
    'Lead', 'Contacted', 'Qualified', 'Proposal',
    'Negotiation', 'Won', 'Lost', 'Dormant',
]

# The hidden tab that backs the drop-down. Kept as a separate sheet (rather
# than an inline list) so the list can be extended later without editing the
# validation rule itself.
STAGES_TAB = 'Stages'
STAGES_COLUMN = 'C'
CLIENTS_TAB = 'Clients'

# WebAwesome brand colors
WA_COLORS = {
    'royal_violet': {'red': 0.231, 'green': 0.102, 'blue': 0.533},      # #3B1A88
    'midnight':     {'red': 0.043, 'green': 0.086, 'blue': 0.259},      # #0B1642
    'electric_violet': {'red': 0.557, 'green': 0.302, 'blue': 1.0},     # #8E4DFF
    'neon_cyan':    {'red': 0.0, 'green': 0.898, 'blue': 1.0},          # #00E5FF
    'hot_pink':     {'red': 1.0, 'green': 0.302, 'blue': 0.651},        # #FF4DA6
    'mist':         {'red': 0.965, 'green': 0.957, 'blue': 1.0},        # #F6F4FF
    'muted':        {'red': 0.357, 'green': 0.337, 'blue': 0.502},      # #5B5680
    'line':         {'red': 0.890, 'green': 0.867, 'blue': 0.965},      # #E3DDF6
    'deep_night':   {'red': 0.024, 'green': 0.043, 'blue': 0.169},      # #060B2B
    'white':        {'red': 1.0, 'green': 1.0, 'blue': 1.0},            # #FFFFFF
}

STAGE_STYLE = {
    'Lead':        {'bg': WA_COLORS['electric_violet'], 'fg': WA_COLORS['white']},
    'Contacted':   {'bg': WA_COLORS['neon_cyan'],       'fg': WA_COLORS['midnight']},
    'Qualified':   {'bg': {'red': 0.65, 'green': 0.85, 'blue': 1.0}, 'fg': WA_COLORS['midnight']},
    'Proposal':    {'bg': WA_COLORS['hot_pink'],        'fg': WA_COLORS['midnight']},
    'Negotiation': {'bg': {'red': 1.0, 'green': 0.78, 'blue': 0.30}, 'fg': WA_COLORS['midnight']},
    'Won':         {'bg': {'red': 0.20, 'green': 0.55, 'blue': 0.20}, 'fg': WA_COLORS['white']},
    'Lost':        {'bg': {'red': 0.72, 'green': 0.20, 'blue': 0.20}, 'fg': WA_COLORS['white']},
    'Dormant':     {'bg': {'red': 0.72, 'green': 0.72, 'blue': 0.78}, 'fg': WA_COLORS['midnight']},
}


def valid_stage(stage: str) -> bool:
    """Exact (case-insensitive) match against the pipeline."""
    return any(stage.lower() == s.lower() for s in STAGES)


def canonical_stage(stage: str) -> str:
    """Return the properly-cased stage name, or the input if it isn't valid."""
    for s in STAGES:
        if stage.lower() == s.lower():
            return s
    return stage

def get_service():
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def get_clients_tab(service) -> str:
    """Title of the tab holding client rows.

    Prefers 'Clients', falls back to the first sheet — the live sheet's tab is
    named 'Sheet1', so the fallback is what's actually in use. Resolved rather
    than hardcoded so renaming the tab later doesn't break anything.
    """
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='sheets.properties').execute()
    sheets = meta.get('sheets', [])
    for s in sheets:
        if s['properties']['title'] == CLIENTS_TAB:
            return CLIENTS_TAB
    return sheets[0]['properties']['title'] if sheets else CLIENTS_TAB


def get_sheet_id(service):
    """Get the sheet ID (numeric) of the 'Clients' tab."""
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='sheets.properties').execute()
    for s in meta.get('sheets', []):
        if s['properties']['title'] == 'Clients':
            return s['properties']['sheetId']
    # fallback: first sheet
    return meta['sheets'][0]['properties']['sheetId']


def ensure_stages_tab(service):
    """Make sure the hidden 'Stages' tab exists, is up to date, and is hidden.

    Returns its numeric sheet id. The list lives in A1:A of this tab so the
    drop-down can reference a real range — extension later is just adding rows.
    """
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='sheets.properties').execute()
    stages_sheet = None
    for s in meta.get('sheets', []):
        if s['properties']['title'] == STAGES_TAB:
            stages_sheet = s['properties']
            break

    if stages_sheet is None:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': STAGES_TAB}}}]},
        ).execute()
        meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='sheets.properties').execute()
        for s in meta.get('sheets', []):
            if s['properties']['title'] == STAGES_TAB:
                stages_sheet = s['properties']
                break

    # Write the stage list, then blank any leftover rows from a longer old list.
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{STAGES_TAB}'!A1",
        valueInputOption='RAW',
        body={'values': [[s] for s in STAGES]},
    ).execute()

    # Hide the tab so it stays out of the way but remains editable by hand.
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [{'updateSheetProperties': {
            'properties': {'sheetId': stages_sheet['sheetId'], 'hidden': True},
            'fields': 'hidden',
        }}]},
    ).execute()

    return stages_sheet['sheetId']

def format_crm(service):
    """Apply professional webawesome styling to the CRM sheet."""
    sheet_id = get_sheet_id(service)
    ensure_stages_tab(service)
    requests = []

    # 0. Stage drop-down (strict) on the Stage column, existing rows only.
    #    Referencing the hidden Stages tab means extending the list later is
    #    just adding a row there — no need to touch this rule.
    used = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"'{get_clients_tab(service)}'!A1:A"
    ).execute().get('values', [])
    last_row = max(len(used), 1)  # header at least, so the rule is never empty
    requests.append({
        'setDataValidation': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'endRowIndex': last_row,
                'startColumnIndex': 2,
                'endColumnIndex': 3,
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{'userEnteredValue': f"='{STAGES_TAB}'!$A$1:$A${len(STAGES)}"}],
                },
                'strict': True,
                'showCustomUi': True,
            },
        }
    })

    # 1. Header row formatting (row 0, index 0)
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': WA_COLORS['royal_violet'],
                    'textFormat': {
                        'foregroundColor': WA_COLORS['white'],
                        'fontFamily': 'Space Grotesk',
                        'fontSize': 11,
                        'bold': True
                    },
                    'horizontalAlignment': 'CENTER',
                    'verticalAlignment': 'MIDDLE',
                    'borders': {
                        'bottom': {'style': 'SOLID', 'width': 2, 'color': WA_COLORS['electric_violet']}
                    }
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,borders)'
        }
    })

    # 2. Freeze header row
    requests.append({
        'updateSheetProperties': {
            'properties': {'sheetId': sheet_id, 'gridProperties': {'frozenRowCount': 1}},
            'fields': 'gridProperties.frozenRowCount'
        }
    })

    # 3. Column widths
    col_widths = [180, 220, 110, 140, 300]
    for i, width in enumerate(col_widths):
        requests.append({
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': i, 'endIndex': i + 1},
                'properties': {'pixelSize': width},
                'fields': 'pixelSize'
            }
        })

    # 4. Clear any existing banding (so re-runs don't stack)
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='sheets(bandedRanges)').execute()
    for sh in meta.get('sheets', []):
        for br in sh.get('bandedRanges', []):
            requests.append({
                'deleteBanding': {
                    'bandedRangeId': br['bandedRangeId']
                }
            })

    # 5. Alternating row colors via repeatCell (data rows only, starting from row 1)
    # Using repeatCell instead of addBanding: banding's headerColor was being applied
    # to the first data row, making text invisible on dark backgrounds.
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'endRowIndex': 1000},
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': WA_COLORS['mist'],
                    'textFormat': {'foregroundColor': WA_COLORS['midnight']}
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat.foregroundColor)'
        }
    })
    requests.append({
        'repeatCell': {
            'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'endRowIndex': 1000, 'startColumnIndex': 0, 'endColumnIndex': 5},
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': WA_COLORS['white'],
                    'textFormat': {'foregroundColor': WA_COLORS['midnight']}
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat.foregroundColor)'
        }
    })

    # 6. Conditional formatting for Stage column (C)
    # Dark text on light stage backgrounds so it stays readable
    for stage, style in STAGE_STYLE.items():
        requests.append({
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{'sheetId': sheet_id, 'startRowIndex': 1, 'startColumnIndex': 2, 'endColumnIndex': 3}],
                    'booleanRule': {
                        'condition': {
                            'type': 'TEXT_EQ',
                            'values': [{'userEnteredValue': stage}]
                        },
                        'format': {
                            'backgroundColor': style['bg'],
                            'textFormat': {
                                'foregroundColor': style['fg'],
                                'bold': True
                            }
                        }
                    }
                },
                'index': 0
            }
        })

    # 7. Filter view on header row
    requests.append({
        'setBasicFilter': {
            'filter': {
                'range': {'sheetId': sheet_id, 'startRowIndex': 0},
                'sortSpecs': []
            }
        }
    })

    # Execute all formatting requests in one batch
    body = {'requests': requests}
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print("Applied webawesome professional formatting to CRM sheet.")

def list_clients(service, json_out=False):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='A1:E'
    ).execute()
    rows = result.get('values', [])
    if not rows or len(rows) < 2:
        if json_out:
            print(json.dumps({'clients': [], 'stages': {}}))
        else:
            print("No clients yet. Add one with: python3 client-tracker.py add")
        return
    clients = []
    for row in rows[1:]:
        # Pad short rows: Sheets trims trailing empty cells on append,
        # so a row added without notes/last-contact can be 3 columns.
        row = (row + [''] * 5)[:5]
        clients.append({
            'name': row[0], 'email': row[1], 'stage': row[2],
            'lastContact': row[3], 'notes': row[4],
        })
    if json_out:
        stages = {}
        for c in clients:
            stages[c['stage']] = stages.get(c['stage'], 0) + 1
        print(json.dumps({'clients': clients, 'stages': stages}))
    else:
        for c in clients:
            print(f"{c['name']:20s} | {c['stage']:12s} | {c['lastContact']:10s} | {c['notes']}")

def add_client(service, name, email, stage="Lead"):
    if not valid_stage(stage):
        print(f"Unknown stage '{stage}'.")
        print_stages()
        return False
    stage = canonical_stage(stage)
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='A1:E',
        valueInputOption='RAW',
        body={'values': [[name, email, stage, '', '']]}
    ).execute()
    print(f"Added {name} as {stage}.")
    return True

def update_stage(service, name, new_stage):
    if not valid_stage(new_stage):
        print(f"Unknown stage '{new_stage}'.")
        print_stages()
        return False
    new_stage = canonical_stage(new_stage)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='A1:E'
    ).execute()
    rows = result.get('values', [])
    for i, row in enumerate(rows[1:], start=2):
        if row[0].lower() == name.lower():
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f'C{i}',
                valueInputOption='RAW',
                body={'values': [[new_stage]]}
            ).execute()
            print(f"Moved {name} to {new_stage}.")
            return True
    print(f"Client '{name}' not found.")
    return False

def print_stages():
    print("Valid stages: " + " -> ".join(STAGES))

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    p_list = sub.add_parser('list')
    p_list.add_argument('--json', action='store_true',
                        help='emit CRM data as JSON (for the dashboard pipeline)')
    p_add = sub.add_parser('add')
    p_add.add_argument('name')
    p_add.add_argument('email')
    p_add.add_argument('stage', nargs='?', default='Lead')

    p_stage = sub.add_parser('stage')
    p_stage.add_argument('name')
    p_stage.add_argument('new_stage')

    sub.add_parser('format')  # apply professional styling
    sub.add_parser('stages')  # list the valid stages

    args = parser.parse_args()
    if not SPREADSHEET_ID:
        print("ERROR: Set CLIENT_TRACKER_ID env var to your Google Sheet ID.")
        sys.exit(1)

    service = get_service()
    if args.cmd == 'list':
        list_clients(service, json_out=getattr(args, 'json', False))
    elif args.cmd == 'add':
        if not add_client(service, args.name, args.email, args.stage):
            sys.exit(1)
    elif args.cmd == 'stage':
        if not update_stage(service, args.name, args.new_stage):
            sys.exit(1)
    elif args.cmd == 'format':
        format_crm(service)
    elif args.cmd == 'stages':
        print_stages()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()