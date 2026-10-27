"""Lodgify guest message notifier -> instant email alert.

Standalone PyRunner script (no repo imports). Polls Lodgify's read-only
Public API v2 for messaging threads where the guest spoke last and no
Owner reply has been sent yet, and emails a short alert to a list of
recipients. Run on a frequent schedule (e.g. every 15 minutes).

Dedup: a small state file (LODGIFY_NOTIFY_STATE, default
lodgify-notified.json) records which thread UIDs have already been
alerted. A thread is alerted only once per guest message; once an Owner
reply lands, the thread is cleared from state so a later new guest
message re-alerts. No repeat emails for the same unanswered message.

It never messages a guest. Read-only.

PyRunner secrets:
  LODGIFY_API_KEY          Lodgify dashboard -> Integrations -> API
  GMAIL_ADDRESS            sending mailbox (Gmail address)
  GMAIL_APP_PASSWORD       Gmail app password
  LODGIFY_NOTIFY_TO        comma-separated recipients (default: the two
                           addresses requested)
  PYRUNNER_WEBHOOK_SECRET  same value as the AI OS server (optional)
Optional:
  LODGIFY_NOTIFY_FROM_NAME display name on the alert email
  LODGIFY_NOTIFY_STATE     path to the dedup state file

Schedule suggestion: every 15 minutes, Europe/London.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import smtplib
import time
import urllib.request
from email.mime.text import MIMEText
from email.utils import formatdate

AIOS_WEBHOOK_URL = "https://aios.webawesome.co.uk/webhook/pyrunner"
AGENT = "lodgify-message-notifier"

LODGIFY_BASE = "https://api.lodgify.com/v2"
DEFAULT_RECIPIENTS = "bankoledada@gmail.com,ademolajoyce@yahoo.co.uk"
STATE_PATH = os.environ.get("LODGIFY_NOTIFY_STATE", "lodgify-notified.json")


def report(status, message=""):
    secret = os.environ.get("PYRUNNER_WEBHOOK_SECRET", "")
    if not secret:
        return False
    try:
        body = json.dumps({"agent": AGENT, "status": status, "message": str(message)[:500]}).encode()
        ts = str(int(time.time()))
        sig = "sha256=" + hmac.new(secret.encode(), (ts + ".").encode() + body, hashlib.sha256).hexdigest()
        req = urllib.request.Request(AIOS_WEBHOOK_URL, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "X-AIOS-Timestamp": ts,
            "X-AIOS-Signature": sig,
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status < 300
    except Exception as e:
        print("AIOS report failed:", e)
        return False


def lodgify_get(path):
    key = os.environ["LODGIFY_API_KEY"]
    req = urllib.request.Request(LODGIFY_BASE + path, headers={"X-ApiKey": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def load_state():
    try:
        with open(STATE_PATH) as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_state(s):
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(sorted(s), f)
    except Exception as e:
        print("state save failed:", e)


def thread_last_type(thread_uid):
    """Return ('renter'|'owner'|'', last_message_id_or_None)."""
    try:
        msgs = lodgify_get("/messaging/" + thread_uid)
    except Exception as e:
        print("thread fetch failed:", thread_uid, e)
        return "", None
    if not isinstance(msgs, list) or not msgs:
        return "", None
    last = msgs[-1] if isinstance(msgs[-1], dict) else None
    t = ((last.get("type") if last else "") or "").lower()
    if t not in ("renter", "guest", "owner"):
        thread = msgs[0] if isinstance(msgs[0], dict) else {}
        arr = thread.get("messages") or []
        if not arr:
            return "", None
        last = arr[-1]
        t = (last.get("type") or "").lower()
    mid = None
    if isinstance(last, dict):
        mid = last.get("id")
    if t in ("renter", "guest"):
        t = "renter"
    return t, mid


def main():
    report("started", "polling Lodgify for fresh guest messages")
    try:
        bookings = lodgify_get("/reservations/bookings?stayFilter=Upcoming&page=1&size=50&includeCount=true")
    except Exception as e:
        report("failed", "bookings fetch failed: " + str(e))
        return
    items = bookings.get("items", []) if isinstance(bookings, dict) else []

    notified = load_state()
    fresh = []
    for b in items:
        tu = b.get("thread_uid")
        if not tu:
            continue
        ltype, mid = thread_last_type(tu)
        if ltype == "renter":
            if tu not in notified:
                guest = (b.get("guest") or {}).get("name") or "Guest"
                fresh.append((guest, tu, b.get("property_id"), mid))
        elif ltype == "owner":
            # thread got a reply -> clear so a future new message re-alerts
            notified.discard(tu)

    if not fresh:
        save_state(notified)
        report("idle", "no new guest messages to alert")
        return

    to_raw = os.environ.get("LODGIFY_NOTIFY_TO", DEFAULT_RECIPIENTS)
    recipients = [x.strip() for x in to_raw.split(",") if x.strip()]
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    from_name = os.environ.get("LODGIFY_NOTIFY_FROM_NAME", "AIOS Lodgify Notifier")

    lines = ["Fresh guest messages needing a reply:", ""]
    for guest, tu, pid, mid in fresh:
        lines.append("- " + guest + " (thread " + str(tu) + ", property " + str(pid) + ")")
    lines.append("")
    lines.append("Reply in Lodgify. This is an automated alert only.")
    body = "\n".join(lines)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "[Lodgify] " + str(len(fresh)) + " fresh guest message(s) need a reply"
    msg["From"] = from_name + " <" + sender + ">"
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(sender, password)
            s.sendmail(sender, recipients, msg.as_string())
        for _, tu, _, _ in fresh:
            notified.add(tu)
        save_state(notified)
        report("ok", "emailed " + str(len(recipients)) + " recipients about " + str(len(fresh)) + " new message(s)")
    except Exception as e:
        report("failed", "email send failed: " + str(e))


if __name__ == "__main__":
    main()
