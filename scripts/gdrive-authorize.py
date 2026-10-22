#!/usr/bin/env python3
"""
Get (or extend) a Google Drive refresh token for the user account.

The service account cannot own files: Drive gives service accounts no storage
quota, so any file it creates is rejected with storageQuotaExceeded. To write
into a folder you own, the AIOS needs to act as you — OAuth delegation.

This prints the consent URL, then exchanges the code you paste back for a
refresh token and stores it in .env as DRIVE_REFRESH_TOKEN.

Usage:
  python3 scripts/gdrive-authorize.py            # print the consent URL
  python3 scripts/gdrive-authorize.py CODE       # exchange the code, save it
"""

import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
ENV_FILE = os.path.join(_REPO_ROOT, '.env')

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.readonly',
]
REDIRECT_URI = 'http://localhost:8085/'


def _env(name):
    """Read a value from .env without requiring python-dotenv."""
    path = os.environ.get(name + '_FROM_ENV')
    if path:
        return path
    if not os.path.exists(ENV_FILE):
        return None
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith(name + '='):
                return line.split('=', 1)[1].strip()
    return None


def _save_env(name, value):
    """Write or replace a key in .env, keeping the file's existing order."""
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.read().split('\n')
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith(name + '='):
            lines[i] = f'{name}={value}'
            replaced = True
            break
    if not replaced:
        while lines and lines[-1] == '':
            lines.pop()
        lines.append(f'{name}={value}')
        lines.append('')
    with open(ENV_FILE, 'w') as f:
        f.write('\n'.join(lines))


def consent_url(client_id):
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
    }
    return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)


def exchange(code, client_id, client_secret):
    data = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    client_id = os.environ.get('GMAIL_CLIENT_ID') or _env('GMAIL_CLIENT_ID')
    client_secret = os.environ.get('GMAIL_CLIENT_SECRET') or _env('GMAIL_CLIENT_SECRET')
    if not client_id or not client_secret:
        print('ERROR: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set (.env).')
        sys.exit(1)

    if len(sys.argv) < 2:
        print('Step 1 — open this URL, sign in as bankoledada@gmail.com, approve.\n')
        print(consent_url(client_id))
        print('\nThe browser will land on a localhost page that will not load.')
        print('That is expected. Copy the code from the URL bar.\n')
        print('Step 2 — run:')
        print('  python3 scripts/gdrive-authorize.py <CODE>')
        return

    code = sys.argv[1].strip()
    try:
        resp = exchange(code, client_id, client_secret)
    except urllib.error.HTTPError as e:
        print('Exchange failed:', e.read().decode()[:300])
        sys.exit(1)

    token = resp.get('refresh_token')
    if not token:
        print('No refresh token returned. Re-run with prompt=consent and approve again.')
        sys.exit(1)

    _save_env('DRIVE_REFRESH_TOKEN', token)
    print('DRIVE_REFRESH_TOKEN saved to .env')
    print('Granted scope:', resp.get('scope'))
    print('Token issued:', datetime.now().isoformat(timespec='seconds'))


if __name__ == '__main__':
    main()
