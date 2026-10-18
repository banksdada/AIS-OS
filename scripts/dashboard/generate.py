#!/usr/bin/env python3
"""
Dashboard data pipeline.

Gathers every data source the AI OS can reach and writes one JSON file
(data/dashboard.json). The dashboard page renders that file — so adding a
feature means adding one function here, and the HTML never needs to know
the data model.

Usage:
  python3 scripts/dashboard/generate.py            # writes data/dashboard.json
  python3 scripts/dashboard/generate.py --json     # prints JSON to stdout
"""
import argparse
import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, 'scripts'))

# Load .env so the pipeline works without exporting every var into the shell.
_ENV = os.path.join(_REPO_ROOT, '.env')
if os.path.exists(_ENV):
    with open(_ENV) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

OUT = os.path.join(_REPO_ROOT, 'data', 'dashboard.json')


def _domains():
    """Connection-domain health, from the verifier's snapshot."""
    path = os.environ.get('VERIFY_OUTPUT', os.path.join(_REPO_ROOT, 'data', 'dashboard-domains.json'))
    if not os.path.exists(path):
        return {'ok': 0, 'total': 0, 'domains': [],
                'detail': 'no snapshot — run python3 scripts/verify-connections.py first'}
    with open(path) as f:
        return json.load(f)


def _pyrunner():
    """Recent events pushed by PyRunner scripts to /webhook/pyrunner."""
    try:
        from dashboard.pyrunner_events import load_events
        events = load_events(limit=20)
    except Exception as e:
        return {'configured': False, 'events': [], 'detail': f'PyRunner events unavailable: {e}'}
    return {'configured': bool(os.environ.get('PYRUNNER_WEBHOOK_SECRET')), 'events': events}


def summarize_sendfox(campaigns_body, contacts_body):
    """Turn SendFox's campaign list and contact count responses into the dashboard shape.

    Campaigns come back paginated: 'total' is the full count, 'data' is one page.
    Contacts come back from /contacts?count_only=true as {'count': n}.
    Only title, a status inferred from the send dates, and the date are kept.
    """
    items = campaigns_body.get('data', []) if isinstance(campaigns_body, dict) else []
    items = [c for c in items if isinstance(c, dict)]
    total = campaigns_body.get('total', len(items)) if isinstance(campaigns_body, dict) else len(items)
    recent = []
    for c in items[:5]:
        if c.get('sent_at'):
            status = 'sent'
        elif c.get('scheduled_at'):
            status = 'scheduled'
        else:
            status = 'draft'
        recent.append({'title': str(c.get('title') or '(untitled)')[:120],
                       'status': status,
                       'date': str(c.get('sent_at') or c.get('created_at') or '')[:40]})
    contacts = contacts_body.get('count', 0) if isinstance(contacts_body, dict) else 0
    return {'configured': True, 'campaignCount': int(total), 'contactCount': int(contacts),
            'recentCampaigns': recent}


def _sendfox():
    """Read-only SendFox summary: recent campaigns and contact count.

    Needs SENDFOX_API_TOKEN (a personal access token from SendFox's account page,
    sent as 'Authorization: Bearer <token>'). Contact details are never read.
    """
    token = os.environ.get('SENDFOX_API_TOKEN', '').strip()
    if not token:
        return {'configured': False, 'detail': 'Set SENDFOX_API_TOKEN to connect SendFox'}
    import urllib.request
    import urllib.error

    def get(path):
        req = urllib.request.Request('https://api.sendfox.com' + path, headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/json',
            'User-Agent': 'AI-OS-Dashboard/1.0',
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())

    try:
        campaigns = get('/campaigns')
        contacts = get('/contacts?count_only=true')
    except urllib.error.HTTPError as e:
        return {'configured': False, 'detail': f'SendFox returned HTTP {e.code}; check the API token'}
    except Exception as e:
        return {'configured': False, 'detail': f'SendFox connection error: {type(e).__name__}'}
    return summarize_sendfox(campaigns, contacts)


def _leads():
    """Coaching leads flagged from community activity."""
    path = os.path.join(_REPO_ROOT, 'data', 'community-leads.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def _drafts():
    """Posts awaiting human approval."""
    path = os.path.join(_REPO_ROOT, 'data', 'pending-drafts.json')
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def _crm():
    """CRM pipeline from the Google Sheet client tracker.

    Runs the tracker in JSON mode so the dashboard reflects the live sheet
    without a separate cron job. Returns an empty shape when the tracker
    isn't configured or the sheet is unreachable.
    """
    tracker = os.path.join(_REPO_ROOT, 'scripts', 'client-tracker.py')
    if not os.path.exists(tracker):
        return {'configured': False, 'clients': [], 'stages': {},
                'detail': 'client-tracker.py not found'}
    try:
        import subprocess
        env = dict(os.environ)
        proc = subprocess.run(
            [sys.executable, tracker, 'list', '--json'],
            capture_output=True, text=True, timeout=30, env=env)
        if proc.returncode != 0:
            return {'configured': True, 'clients': [], 'stages': {},
                    'detail': f'tracker failed: {proc.stderr.strip()[:120]}'}
        data = json.loads(proc.stdout.strip())
        return {'configured': True,
                'clients': data.get('clients', []),
                'stages': data.get('stages', {})}
    except subprocess.TimeoutExpired:
        return {'configured': True, 'clients': [], 'stages': {},
                'detail': 'tracker timed out'}
    except Exception as e:
        return {'configured': True, 'clients': [], 'stages': {},
                'detail': f'connection error: {e}'}


def _wordpress():
    """Blog post + activity status for each configured WordPress site.

    Set WP_SITES in .env as a JSON list, e.g.:
      WP_SITES='[{"name":"webawesome","url":"https://webawesome.co.uk",
                  "user":"aios","app_password":"xxxx xxxx"}]'
    Auth is an Application Password (Users -> Edit -> Application Passwords).
    """
    raw = os.environ.get('WP_SITES', '').strip()
    if not raw:
        return {'configured': False, 'sites': [],
                'detail': 'no WP_SITES set in .env'}
    try:
        sites = json.loads(raw)
    except json.JSONDecodeError as e:
        return {'configured': True, 'sites': [], 'detail': f'bad WP_SITES JSON: {e}'}

    import base64
    try:
        # requests handles SSL/TLS more gracefully than the stdlib
        # urllib, which resets connections on these hosts.
        import requests
        HAS_REQUESTS = True
    except ImportError:
        HAS_REQUESTS = False
        import urllib.request
        import urllib.error

    out = []
    for s in sites:
        url = s.get('url', '').rstrip('/')
        user = s.get('user', '')
        pw = s.get('app_password', '')
        if not url or not user or not pw:
            out.append({'name': s.get('name', '?'), 'ok': False,
                        'detail': 'missing url / user / app_password'})
            continue
        token = base64.b64encode(f"{user}:{pw}".encode()).decode()
        # WordPress hosts reject the default python-requests User-Agent with 403.
        headers = {'Authorization': 'Basic ' + token, 'Accept': 'application/json',
                   'User-Agent': 'AI-OS-Dashboard/1.0'}
        try:
            if HAS_REQUESTS:
                resp = requests.get(url + '/wp-json/wp/v2/posts?per_page=1',
                                    headers=headers, timeout=30)
                resp.raise_for_status()
                posts = resp.json()
            else:
                req = urllib.request.Request(
                    url + '/wp-json/wp/v2/posts?per_page=1',
                    headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    posts = json.loads(resp.read().decode())
            latest = posts[0] if posts else None
            out.append({
                'name': s.get('name', url),
                'url': url,
                'ok': True,
                'postCount': len(posts),
                'latestTitle': (latest or {}).get('title', {}).get('rendered', '(none)'),
                'latestDate': (latest or {}).get('date', ''),
            })
        except Exception as e:
            out.append({'name': s.get('name', url), 'url': url, 'ok': False,
                        'detail': f"connection error: {str(e)[:120]}"})
    return {'configured': True, 'sites': out}


def _tidycal():
    """Read upcoming TidyCal bookings through the local OAuth/MCP connector."""
    try:
        from tidycal_mcp import dashboard_data
        return dashboard_data()
    except Exception as e:
        return {'configured': False, 'connected': False, 'bookings': [],
                'bookingTypes': [], 'detail': f'TidyCal integration unavailable: {e}'}


def _newsletter():
    """Newsletter status: the local probe if it works here, else the status pushed from the Mac."""
    local = _newsletter_local()
    if local.get('configured'):
        return local
    from dashboard.newsletter_status import load
    pushed = load()
    if pushed:
        return dict(pushed, source='pushed from the Mac')
    return local


def _newsletter_local():
    """WebAwesome newsletter build/send status from the local newsletter-project.

    The newsletter codebase lives at /Users/banksdada/Desktop/newsletter-project
    (WAT framework: workflows/, tools/, .tmp/). This probe is read-only — it
    reports what is built and ready to send, it never sends anything.
    """
    probe = os.path.join(_REPO_ROOT, 'scripts', 'newsletter-status.py')
    if not os.path.exists(probe):
        return {'configured': False, 'detail': 'newsletter-status.py not found'}
    try:
        import subprocess
        proc = subprocess.run(
            [sys.executable, probe],
            capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return {'configured': False,
                    'detail': f'probe failed: {proc.stderr.strip()[:120] or proc.stdout.strip()[:120]}'}
        return json.loads(proc.stdout.strip())
    except subprocess.TimeoutExpired:
        return {'configured': False, 'detail': 'newsletter probe timed out'}
    except Exception as e:
        return {'configured': False, 'detail': f'connection error: {e}'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true', help='print JSON to stdout instead of writing the file')
    args = ap.parse_args()

    payload = {
        'generatedAt': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
        'domains': _domains(),
        'crm': _crm(),
        'leads': _leads(),
        'drafts': _drafts(),
        'wordpress': _wordpress(),
        'tidycal': _tidycal(),
        'newsletter': _newsletter(),
        'pyrunner': _pyrunner(),
        'sendfox': _sendfox(),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"Dashboard data written to {OUT}")


if __name__ == '__main__':
    main()
