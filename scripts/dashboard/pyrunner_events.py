"""Signed event intake for PyRunner scripts.

PyRunner scripts POST a small JSON summary to the dashboard server. Each
request is signed with HMAC-SHA256 over "<timestamp>.<body>" using a shared
secret, and rejected if the timestamp is more than five minutes off. Accepted
events are kept in data/pyrunner-events.json, newest first, capped at MAX_EVENTS.
"""
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVENTS_PATH = os.path.join(_REPO_ROOT, 'data', 'pyrunner-events.json')

MAX_BODY_BYTES = 16 * 1024
MAX_EVENTS = 100
MAX_SKEW_SECONDS = 300
FIELD_LIMITS = {'agent': 100, 'status': 32, 'message': 500, 'at': 40}


def sign(secret, timestamp, body):
    """Return the signature header value for a request body."""
    digest = hmac.new(secret.encode(), f'{timestamp}.'.encode() + body, hashlib.sha256)
    return 'sha256=' + digest.hexdigest()


def verify(secret, timestamp, body, signature, now=None):
    """True only for a fresh request whose signature matches the body."""
    try:
        sent_at = int(timestamp)
    except (TypeError, ValueError):
        return False
    current = time.time() if now is None else now
    if abs(current - sent_at) > MAX_SKEW_SECONDS:
        return False
    expected = sign(secret, timestamp, body)
    return hmac.compare_digest(expected, signature or '')


def sanitize(event):
    """Keep only the known fields, as short strings. Returns None if not a dict."""
    if not isinstance(event, dict):
        return None
    clean = {}
    for key, limit in FIELD_LIMITS.items():
        value = event.get(key)
        if value is None:
            continue
        clean[key] = str(value)[:limit]
    clean.setdefault('status', 'unknown')
    clean.setdefault('agent', 'unnamed')
    clean['received'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    return clean


def load_events(limit=20):
    """Newest-first events for the dashboard panel."""
    if not os.path.exists(EVENTS_PATH):
        return []
    try:
        with open(EVENTS_PATH) as f:
            events = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return events[:limit] if isinstance(events, list) else []


def record(event):
    """Prepend a cleaned event and write the file atomically."""
    events = load_events(limit=MAX_EVENTS)
    events.insert(0, event)
    del events[MAX_EVENTS:]
    os.makedirs(os.path.dirname(EVENTS_PATH), exist_ok=True)
    tmp = EVENTS_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(events, f, indent=2)
    os.replace(tmp, EVENTS_PATH)
    return event
