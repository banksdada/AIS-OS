"""Newsletter status pushed from the Mac, for the server-side dashboard.

The newsletter project lives on the Mac, so the Coolify server can't read it.
A script on the Mac (scripts/push_newsletter_status.py) runs the local probe
and POSTs the result to /webhook/newsletter, signed with
NEWSLETTER_WEBHOOK_SECRET. The latest accepted status is kept in
data/newsletter-status.json. Only the fields below are kept; recipient
addresses never leave the Mac.
"""
import json
import os
from datetime import datetime, timezone

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATUS_PATH = os.path.join(_REPO_ROOT, 'data', 'newsletter-status.json')

MAX_STRING = 200
BUILD_FIELDS = ('file', 'modified', 'sizeKb')
CAMPAIGN_FIELDS = ('campaign', 'subject', 'preheader')


def _text(value):
    return str(value)[:MAX_STRING] if value is not None else None


def sanitize(status):
    """Keep only the known fields. Returns None if the input isn't an object."""
    if not isinstance(status, dict):
        return None
    clean = {
        'configured': bool(status.get('configured')),
        'envConfigured': bool(status.get('envConfigured')),
        'buildCount': int(status.get('buildCount') or 0),
        'recipientCount': int(status.get('recipientCount') or 0),
        'lastSendLog': _text(status.get('lastSendLog')),
        'projectPath': _text(os.path.basename(str(status.get('projectPath') or '').rstrip('/'))),
        'pushedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    build = status.get('latestBuild')
    if isinstance(build, dict):
        clean['latestBuild'] = {k: _text(build.get(k)) for k in BUILD_FIELDS}
    campaign = status.get('latestCampaign')
    if isinstance(campaign, dict):
        clean['latestCampaign'] = {k: _text(campaign.get(k)) for k in CAMPAIGN_FIELDS}
    return clean


def store(status):
    """Write the cleaned status atomically."""
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    tmp = STATUS_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(status, f, indent=2)
    os.replace(tmp, STATUS_PATH)
    return status


def load():
    """The last pushed status, or None if none has arrived yet."""
    if not os.path.exists(STATUS_PATH):
        return None
    try:
        with open(STATUS_PATH) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None
