#!/usr/bin/env python3
"""
Verify every connection domain in connections.md against the live service.

Runs read-only probes and prints a status line per domain. Exit code 0 if all
probed domains succeed, 1 if any fail (so it can be wired into /audit).

Usage:
  python3 scripts/verify-connections.py
"""
import json
import os
import sys

# Load .env from the repo root if present, so the script works without the
# caller exporting every variable into the shell environment.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_REPO_ROOT, '.env')
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_PATH', os.path.join(_SCRIPT_DIR, 'credentials.json'))
CRM_ID = os.environ.get('CLIENT_TRACKER_ID', '1OuqO9tpzgH-zd9BIGujL_u2dKelSbmMAo_iRtz3gvnY')
HUMHUB_BASE = 'https://meetup.mentoringba.org'
HUMHUB_USER = os.environ.get('HUMHUB_USER', 'aios-bot')
HUMHUB_PASS = os.environ.get('HUMHUB_PASSWORD', '')
# Gmail now uses OAuth 2.0 (refresh-token flow), not the service account —
# the target mailbox is a consumer gmail.com address, which service accounts
# cannot reach. See references/gmail-api.md.
GMAIL_CLIENT_ID = os.environ.get('GMAIL_CLIENT_ID', '')
GMAIL_CLIENT_SECRET = os.environ.get('GMAIL_CLIENT_SECRET', '')
GMAIL_REFRESH_TOKEN = os.environ.get('GMAIL_REFRESH_TOKEN', '')

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
]

results = []

def record(domain, ok, detail):
    results.append((domain, ok, detail))
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {domain}: {detail}")

def main():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: credentials not found at {CREDENTIALS_FILE}")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)

    # --- Domain 7: Knowledge / files (Drive) ---
    try:
        s = build('drive', 'v3', credentials=creds, cache_discovery=False)
        r = s.files().list(pageSize=5, fields='files(id,name)').execute()
        names = [f['name'] for f in r.get('files', [])]
        record("Drive (knowledge/files)", True, f"listed {len(names)} files: {names}")
    except HttpError as e:
        record("Drive (knowledge/files)", False, f"{e.status_code} {e._get_reason()[:120]}")

    # --- Domain 5: Project / task tracking (Sheets CRM) ---
    try:
        s = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        r = s.spreadsheets().values().get(spreadsheetId=CRM_ID, range='A1:E').execute()
        rows = r.get('values', [])
        clients = [row[0] for row in rows[1:]] if rows else []
        record("CRM (project tracking)", True, f"{len(clients)} clients: {clients}")
    except HttpError as e:
        record("CRM (project tracking)", False, f"{e.status_code} {e._get_reason()[:120]}")

    # --- Domain 2 & 4: Gmail (customer interactions + communication) ---
    # OAuth 2.0 refresh-token flow — the target mailbox is a consumer gmail.com
    # address, which the service account cannot reach.
    try:
        if not (GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN):
            raise ValueError("missing GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN")
        from google.oauth2.credentials import Credentials
        gcreds = Credentials(
            token=None,
            refresh_token=GMAIL_REFRESH_TOKEN,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=GMAIL_CLIENT_ID,
            client_secret=GMAIL_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.readonly'])
        s = build('gmail', 'v1', credentials=gcreds, cache_discovery=False)
        r = s.users().messages().list(userId='me', maxResults=1).execute()
        record("Gmail (customer + communication)", True,
               f"API reachable via OAuth, est. {r.get('resultSizeEstimate')} messages")
    except HttpError as e:
        record("Gmail (customer + communication)", False, f"{e.status_code} {e._get_reason()[:120]}")
    except Exception as e:
        record("Gmail (customer + communication)", False, f"config error: {e}")

    # --- Domain 3: Calendar ---
    try:
        s = build('calendar', 'v3', credentials=creds, cache_discovery=False)
        r = s.calendars().get(calendarId='primary').execute()
        record("Calendar", True, f"calendar: {r.get('summary','primary')}")
    except HttpError as e:
        record("Calendar", False, f"{e.status_code} {e._get_reason()[:120]}")

    # --- Domain 8: Community (HumHub) ---
    if not HUMHUB_PASS:
        record("HumHub (community)", False, "no HUMHUB_PASSWORD set in .env")
    else:
        import base64
        import urllib.request
        import urllib.error
        token = base64.b64encode(f"{HUMHUB_USER}:{HUMHUB_PASS}".encode()).decode()
        req = urllib.request.Request(
            HUMHUB_BASE + '/api/v1/auth/current',
            headers={'Authorization': 'Basic ' + token, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode())
            record("HumHub (community)", True,
                   f"auth OK as {body.get('username', HUMHUB_USER)} "
                   f"({body.get('email', '?')})")
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:120]
            record("HumHub (community)", False, f"{e.code} {detail}")
        except Exception as e:
            record("HumHub (community)", False, f"connection error: {e}")

    # --- Domain 1: Stripe (read-only restricted key) ---
    stripe_key = os.environ.get('STRIPE_API_KEY', '')
    if not stripe_key:
        record("Stripe (revenue)", False, "no STRIPE_API_KEY set in .env")
    else:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            'https://api.stripe.com/v1/balance',
            headers={'Authorization': 'Bearer ' + stripe_key, 'User-Agent': 'AI-OS-Dashboard/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                balance = json.loads(resp.read().decode())
            currencies = sorted({a.get('currency', '?').upper() for a in balance.get('available', [])})
            record("Stripe (revenue)", True, f"balance readable; currencies: {', '.join(currencies) or 'none'}")
        except urllib.error.HTTPError as e:
            record("Stripe (revenue)", False, f"HTTP {e.code} from Stripe (check the key's read permissions)")
        except Exception as e:
            record("Stripe (revenue)", False, f"connection error: {type(e).__name__}")

    # --- Domain 6: TidyCal (OAuth 2.1 + read-only MCP) ---
    try:
        from tidycal_mcp import dashboard_data
        tidycal = dashboard_data()
        record("TidyCal (meeting intelligence)", tidycal.get('connected', False),
               tidycal.get('detail') or f"OAuth connected; {len(tidycal.get('bookings', []))} upcoming bookings")
    except Exception as e:
        record("TidyCal (meeting intelligence)", False, f"connection error: {e}")

    print()
    ok = sum(1 for _, v, _ in results if v)
    fail = len(results) - ok
    print(f"Verified: {ok}/{len(results)} domains live. Failed: {fail}.")

    # Machine-readable snapshot for the dashboard. The page renders whatever
    # is here, so adding a domain means adding one probe — the HTML never
    # needs to know the domain list.
    import datetime
    _out = os.environ.get('VERIFY_OUTPUT', os.path.join(_REPO_ROOT, 'data', 'dashboard-domains.json'))
    os.makedirs(os.path.dirname(_out), exist_ok=True)
    with open(_out, 'w') as _f:
        json.dump({'checkedAt': datetime.datetime.now().isoformat(timespec='seconds'),
                   'ok': ok, 'total': len(results),
                   'domains': [{'name': n, 'ok': v, 'detail': d} for n, v, d in results]},
                  _f, indent=2)
    print(f"Snapshot written to {_out}")

    sys.exit(0 if fail == 0 else 1)

if __name__ == '__main__':
    main()
