#!/usr/bin/env python3
"""Send the local newsletter status to the AI OS dashboard.

Run on your Mac after building or sending the newsletter:
  python3 scripts/push_newsletter_status.py

Reads NEWSLETTER_WEBHOOK_SECRET and (optionally) NEWSLETTER_WEBHOOK_URL from
the environment or the repo's .env file. Sends nothing if the local probe
doesn't report the newsletter as configured.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, 'scripts'))

from dashboard.pyrunner_events import sign  # noqa: E402

DEFAULT_URL = 'https://aios.webawesome.co.uk/webhook/newsletter'


def _load_env():
    path = os.path.join(_REPO_ROOT, '.env')
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())


def main():
    _load_env()
    secret = os.environ.get('NEWSLETTER_WEBHOOK_SECRET', '')
    if not secret:
        sys.exit('NEWSLETTER_WEBHOOK_SECRET is not set in .env or the environment.')
    url = os.environ.get('NEWSLETTER_WEBHOOK_URL', DEFAULT_URL)

    probe = os.path.join(_REPO_ROOT, 'scripts', 'newsletter-status.py')
    proc = subprocess.run([sys.executable, probe], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        sys.exit(f'Local newsletter probe failed: {proc.stderr.strip()[:200]}')
    status = json.loads(proc.stdout.strip())
    if not status.get('configured'):
        sys.exit('Newsletter is not configured on this Mac; nothing sent.')

    body = json.dumps(status).encode()
    timestamp = str(int(time.time()))
    req = urllib.request.Request(url, data=body, method='POST', headers={
        'Content-Type': 'application/json',
        'X-AIOS-Timestamp': timestamp,
        'X-AIOS-Signature': sign(secret, timestamp, body),
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f'Sent newsletter status to {url}: HTTP {resp.status}')


if __name__ == '__main__':
    main()
