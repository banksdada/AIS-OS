"""NativeTasks webhook receiver: third-party senders, URL-token auth, raw log.

Unlike the PyRunner fleet webhooks (HMAC in headers), NativeTasks can only
POST plain JSON to a URL, so authentication is a secret token in the query
string. Every event is appended verbatim to data/nativetasks-events.json —
including the payload shape, which we are still learning.
"""
import hmac
import json
import os
import re
from datetime import datetime, timezone

MAX_BODY_BYTES = 16 * 1024
_MAX_EVENTS = 500
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVENTS_PATH = os.path.join(_ROOT, 'data', 'nativetasks-events.json')

_COMPLETED_RE = re.compile(r'(?i)^(done|complete|completed|finished)$')


def check_token(secret, token):
    return bool(secret) and hmac.compare_digest(secret, token or '')


def _walk(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)
    else:
        yield node


def looks_completed(payload):
    return any(_COMPLETED_RE.match(str(v)) for v in _walk(payload))


def record(body: bytes) -> bool:
    """Append the raw event; return True if any field looks like a completion."""
    try:
        payload = json.loads(body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {'raw': body.decode('utf-8', 'replace')[:MAX_BODY_BYTES]}
    completed = looks_completed(payload)
    events = []
    if os.path.exists(EVENTS_PATH):
        try:
            with open(EVENTS_PATH) as fh:
                events = json.load(fh)
        except (OSError, json.JSONDecodeError):
            events = []
    events.append({
        'received_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'completed': completed,
        'payload': payload,
    })
    events = events[-_MAX_EVENTS:]
    os.makedirs(os.path.dirname(EVENTS_PATH), exist_ok=True)
    tmp = EVENTS_PATH + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(events, fh, indent=2)
    os.replace(tmp, EVENTS_PATH)
    return completed
