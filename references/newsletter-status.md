# Newsletter status to the AI OS dashboard

The newsletter project lives on your Mac, so the Coolify server can't read it.
Running `scripts/push_newsletter_status.py` on the Mac sends the newsletter
status to the dashboard. The dashboard shows it when its local check can't
run.

Only counts, the build file name and date, and the latest campaign's subject
and preheader are sent. Recipient addresses never leave the Mac.

## Setup

1. Create a secret, separate from the PyRunner one:
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
2. In **Coolify** (AI OS app → Environment Variables), add `NEWSLETTER_WEBHOOK_SECRET` with that value, then redeploy.
3. On your **Mac**, add the same value to the repo's `.env`:
   `NEWSLETTER_WEBHOOK_SECRET=<value>`

## Sending

After building or sending the newsletter, run from the repo folder:

```sh
python3 scripts/push_newsletter_status.py
```

It sends nothing if the newsletter isn't configured on your Mac.

## Responses from the endpoint

| Code | Meaning |
|---|---|
| 200 | Status stored |
| 400 | Body is not a JSON object |
| 401 | Bad signature or stale timestamp |
| 503 | `NEWSLETTER_WEBHOOK_SECRET` not set on the server |
