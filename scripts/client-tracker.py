#!/usr/bin/env python3
"""
Client tracker for webawesome.co.uk.
Manages a Google Sheet as a lightweight CRM.

Usage:
  python3 client-tracker.py list                    # list all clients
  python3 client-tracker.py add "Name" "Email" "Stage"  # add a client
  python3 client-tracker.py stage "Name" "New Stage"    # move a client to a new stage

Stages: Lead → Contacted → Proposal → Won → Lost
"""

import os
import sys
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_PATH', os.path.join(_SCRIPT_DIR, 'credentials.json'))
SPREADSHEET_ID = os.environ.get('CLIENT_TRACKER_ID', '')  # set after creating the sheet

HEADERS = ['Name', 'Email', 'Stage', 'Last Contact', 'Notes']

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

STAGE_COLORS = {
    'Lead':        {'red': 0.557, 'green': 0.302, 'blue': 1.0},     # electric violet
    'Contacted':   {'red': 0.0, 'green': 0.898, 'blue': 1.0},       # neon cyan
    'Proposal':    {'red': 1.0, 'green': 0.302, 'blue': 0.651},     # hot pink
    'Won':         {'red': 0.231, 'green': 0.6, 'blue': 0.2},       # green-ish
    'Lost':        {'red': 0.8, 'green': 0.2, 'blue': 0.2},         # red-ish
}

# Stage colors with readable foreground (dark text on light backgrounds)
STAGE_STYLE = {
    'Lead':        {'bg': WA_COLORS['electric_violet'], 'fg': WA_COLORS['white']},
    'Contacted':   {'bg': WA_COLORS['neon_cyan'],    'fg': WA_COLORS['midnight']},
    'Proposal':    {'bg': WA_COLORS['hot_pink'],     'fg': WA_COLORS['midnight']},
    'Won':         {'bg': {'red': 0.20, 'green': 0.55, 'blue': 0.20}, 'fg': WA_COLORS['white']},
    'Lost':        {'bg': {'red': 0.72, 'green': 0.20, 'blue': 0.20}, 'fg': WA_COLORS['white']},
}

def get_service():
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def get_sheet_id(service):
    """Get the sheet ID (numeric) of the 'Clients' tab."""
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, fields='sheets.properties').execute()
    for s in meta.get('sheets', []):
        if s['properties']['title'] == 'Clients':
            return s['properties']['sheetId']
    # fallback: first sheet
    return meta['sheets'][0]['properties']['sheetId']

def format_crm(service):
    """Apply professional webawesome styling to the CRM sheet."""
    sheet_id = get_sheet_id(service)
    requests = []

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

def list_clients(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='A1:E'
    ).execute()
    rows = result.get('values', [])
    if not rows or len(rows) < 2:
        print("No clients yet. Add one with: python3 client-tracker.py add")
        return
    for row in rows[1:]:
        # Pad short rows: Sheets trims trailing empty cells on append,
        # so a row added without notes/last-contact can be 3 columns.
        row = (row + [''] * 5)[:5]
        print(f"{row[0]:20s} | {row[2]:12s} | {row[3]:10s} | {row[4]}")

def add_client(service, name, email, stage="Lead"):
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='A1:E',
        valueInputOption='RAW',
        body={'values': [[name, email, stage, '', '']]}
    ).execute()
    print(f"Added {name} as {stage}.")

def update_stage(service, name, new_stage):
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
            return
    print(f"Client '{name}' not found.")

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('list')
    p_add = sub.add_parser('add')
    p_add.add_argument('name')
    p_add.add_argument('email')
    p_add.add_argument('stage', nargs='?', default='Lead')

    p_stage = sub.add_parser('stage')
    p_stage.add_argument('name')
    p_stage.add_argument('new_stage')

    sub.add_parser('format')  # apply professional styling

    args = parser.parse_args()
    if not SPREADSHEET_ID:
        print("ERROR: Set CLIENT_TRACKER_ID env var to your Google Sheet ID.")
        sys.exit(1)

    service = get_service()
    if args.cmd == 'list':
        list_clients(service)
    elif args.cmd == 'add':
        add_client(service, args.name, args.email, args.stage)
    elif args.cmd == 'stage':
        update_stage(service, args.name, args.new_stage)
    elif args.cmd == 'format':
        format_crm(service)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()