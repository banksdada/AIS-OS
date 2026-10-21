"""CRM capture from Sorted, for the server-side dashboard.

When a Sorted user proves they own their email by clicking the magic link,
Sorted POSTs a signed JSON body to /webhook/crm. That is the only signal we
trust — an email that has been verified — so this is where a contact enters
the CRM. The handler appends the contact to the Clients sheet via
client-tracker.py, keeping the sheet schema in one codebase.

Signature matches the other webhooks: HMAC-SHA256 over "<timestamp>.<body>"
using CRM_WEBHOOK_SECRET, rejected if the timestamp is more than five minutes
old. Only name and email are kept, truncated; anything else in the body is
ignored.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACKER = os.path.join(_REPO_ROOT, 'scripts', 'client-tracker.py')

MAX_NAME = 200
MAX_EMAIL = 254
DEFAULT_STAGE = 'Lead'


def sanitize(contact):
    """Keep only a usable name and email. Returns None if the input is junk.

    Rejects objects with no email, since the whole point of this hook is that
    the email is proven. The name falls back to the email's local part.
    """
    if not isinstance(contact, dict):
        return None
    email = str(contact.get('email') or '').strip()[:MAX_EMAIL]
    if not email or '@' not in email:
        return None
    name = str(contact.get('name') or '').strip()[:MAX_NAME]
    if not name:
        name = email.split('@', 1)[0]
    stage = str(contact.get('stage') or DEFAULT_STAGE).strip() or DEFAULT_STAGE
    return {'name': name, 'email': email, 'stage': stage[:32]}


def capture(contact, tracker_path=TRACKER):
    """Append a cleaned contact to the CRM sheet. Returns the subprocess result.

    Runs client-tracker.py as a subprocess so the sheet access and the
    credentials stay in one place. The caller decides what to do on failure.
    """
    return subprocess.run(
        [sys.executable, tracker_path, 'add', contact['name'], contact['email'], contact['stage']],
        capture_output=True,
        text=True,
        timeout=30,
    )


def log_event(contact, ok, note=''):
    """Best-effort audit line in data/crm-captures.json, newest first, capped."""
    path = os.path.join(_REPO_ROOT, 'data', 'crm-captures.json')
    records = []
    if os.path.exists(path):
        try:
            with open(path) as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                records = loaded
        except (OSError, json.JSONDecodeError):
            records = []
    records.insert(0, {
        'name': contact['name'],
        'email': contact['email'],
        'stage': contact['stage'],
        'ok': bool(ok),
        'note': str(note)[:200],
        'at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    })
    del records[100:]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(records, f, indent=2)
    os.replace(tmp, path)
    return records[0]
