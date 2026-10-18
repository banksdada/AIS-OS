# PyRunner → AI OS webhook

PyRunner scripts send short status events to the AI OS dashboard. The
dashboard keeps the latest 100 and shows the newest 20 in the **PyRunner
activity** panel.

- **Endpoint:** `POST https://pyrunner.webawesome.co.uk/webhook/pyrunner`
- **Accepted body:** a JSON object. Known fields are kept, the rest are
  dropped. Lengths are capped: `agent` 100, `status` 32, `message` 500,
  `at` 40 characters. Bodies over 16 KB are rejected.
- **Stored locally:** `data/pyrunner-events.json` (git-ignored).

## Setup

1. Generate a secret once: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
2. In **Coolify** (AI OS app → Environment), set `PYRUNNER_WEBHOOK_SECRET` to that value and redeploy.
3. In **PyRunner**, store the same value as a secret named `PYRUNNER_WEBHOOK_SECRET` for the scripts that report.

Never commit the secret or paste it into logs.

## Signing

Each request carries two headers:

- `X-AIOS-Timestamp`: Unix time in seconds
- `X-AIOS-Signature`: `sha256=` + hex HMAC-SHA256 of `"<timestamp>." + body`, keyed by the secret

The server rejects requests whose timestamp is more than five minutes from
its own clock, and any signature that doesn't match.

## Sending from a PyRunner script

```python
import hashlib
import hmac
import json
import os
import time
import urllib.request

WEBHOOK_URL = 'https://pyrunner.webawesome.co.uk/webhook/pyrunner'


def report(agent, status, message=''):
    secret = os.environ['PYRUNNER_WEBHOOK_SECRET']
    body = json.dumps({'agent': agent, 'status': status, 'message': message}).encode()
    timestamp = str(int(time.time()))
    signature = 'sha256=' + hmac.new(secret.encode(), f'{timestamp}.'.encode() + body,
                                     hashlib.sha256).hexdigest()
    req = urllib.request.Request(WEBHOOK_URL, data=body, method='POST', headers={
        'Content-Type': 'application/json',
        'X-AIOS-Timestamp': timestamp,
        'X-AIOS-Signature': signature,
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status


report('daily-digest', 'ok', 'Sent 12 items')
```

Use a `status` such as `ok`, `failed`, or `started`. Keep `message` to one
line; the panel shows it as plain text.

## Responses

| Code | Meaning |
|---|---|
| 200 | Event recorded |
| 400 | Body is not a JSON object |
| 401 | Bad signature or stale timestamp |
| 411 | Missing `Content-Length` |
| 413 | Body over 16 KB |
| 503 | `PYRUNNER_WEBHOOK_SECRET` not set on the server |
