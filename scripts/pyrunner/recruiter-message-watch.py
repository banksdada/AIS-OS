"""Recruiter message watch -> daily email digest.

Runs on a schedule in PyRunner (standalone — no repo imports, everything
inlined). Reads Gmail (read-only, OAuth refresh-token flow) for LinkedIn
notification emails and anything that looks like recruiter contact, classifies
each one, and emails a short digest of what needs a human reply.

Why Gmail and not LinkedIn itself: LinkedIn has no API for reading messages,
and scraping it breaks their Terms of Service — a real risk to the very account
being used to apply for jobs. LinkedIn emails about every message, so the
mailbox is the legitimate way in. This never replies to anything: a recruiter
conversation is human work, same rule as guest messages.

PyRunner secrets to set:
  GMAIL_CLIENT_ID          OAuth client id (GCP project 266063022919)
  GMAIL_CLIENT_SECRET      OAuth client secret
  GMAIL_REFRESH_TOKEN      OAuth refresh token (scope gmail.readonly)
  GMAIL_ADDRESS            sending mailbox (Gmail address)
  GMAIL_APP_PASSWORD       Gmail app password
  AI_BASE_URL              e.g. https://opencode.ai/zen/v1
  AI_MODEL                 e.g. minimax-m2.5
  AI_API_KEY               the AI provider key
  PYRUNNER_WEBHOOK_SECRET  same value as the AI OS server
Optional:
  RECRUITER_DIGEST_TO      who receives the digest (default the sender)
  RECRUITER_LOOKBACK_DAYS  how far back to scan, default 2
  RECRUITER_ROLE_KEYWORDS  comma-separated role terms to prioritise
                           (default: business analyst,product owner,product manager)

Schedule suggestion: every weekday at 07:45 Europe/London.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import smtplib
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.utils import formatdate

# ---------- AI OS dashboard reporting (inlined; PyRunner runs standalone) ----------

AIOS_WEBHOOK_URL = "https://aios.webawesome.co.uk/webhook/pyrunner"
AGENT = "recruiter-message-watch"


def report(status: str, message: str = "") -> bool:
    """Send one status event to the AI OS dashboard. Never raises."""
    secret = os.environ.get("PYRUNNER_WEBHOOK_SECRET", "")
    if not secret:
        print("AIOS report skipped: PYRUNNER_WEBHOOK_SECRET not set")
        return False
    try:
        body = json.dumps({"agent": AGENT, "status": status, "message": str(message)[:500]}).encode()
        ts = str(int(time.time()))
        sig = "sha256=" + hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        req = urllib.request.Request(AIOS_WEBHOOK_URL, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "X-AIOS-Timestamp": ts,
            "X-AIOS-Signature": sig,
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("AIOS report sent:", resp.status)
        return True
    except Exception as e:  # noqa: BLE001
        print("AIOS report failed:", e)
        return False


# ---------- Gmail (read-only) ----------

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
DEFAULT_ROLE_KEYWORDS = ["business analyst", "product owner", "product manager"]

# LinkedIn alert emails come from a small set of senders. Kept loose on purpose:
# the classifier decides what's real, this only decides what's worth reading.
LINKEDIN_SENDER_HINTS = ("linkedin.com", "linkedin")
RECRUITER_SUBJECT_HINTS = (
    "job", "role", "opportunity", "recruiter", "hiring", "position",
    "interview", "application", "vacancy", "career", "talent", "contract",
)
# Things that look like recruiter mail but are noise — LinkedIn's own marketing.
NOISE_SUBJECT_HINTS = (
    "people you may know", "your network", "new connection", "liked your",
    "commented on", "shared a post", "jobs you may be interested",
    "newsletter", "weekly update", "digest of", "suggested for you",
    "is hiring", "work anniversary", "birthday",
)


def gmail_token() -> str:
    """Exchange the refresh token for a short-lived access token."""
    cid = os.environ.get("GMAIL_CLIENT_ID", "")
    secret = os.environ.get("GMAIL_CLIENT_SECRET", "")
    refresh = os.environ.get("GMAIL_REFRESH_TOKEN", "")
    if not (cid and secret and refresh):
        raise RuntimeError("GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN must be set")
    data = urllib.parse.urlencode({
        "client_id": cid,
        "client_secret": secret,
        "refresh_token": refresh,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["access_token"]


def gmail_get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"{GMAIL_API}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_recent_messages(days: int) -> list[dict]:
    """Messages from the last N days that could be recruiter contact."""
    token = gmail_token()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = f"after:{since:%Y/%m/%d} -in:spam -in:trash"
    listed = gmail_get(
        "/messages?" + urllib.parse.urlencode({"q": query, "maxResults": 50}),
        token,
    )
    out = []
    for stub in listed.get("messages", []):
        msg = gmail_get(f"/messages/{stub['id']}?format=full", token)
        parsed = parse_message(msg)
        if parsed:
            out.append(parsed)
    return out


def header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def body_text(msg: dict, limit: int = 1200) -> str:
    """Best-effort plain text from a Gmail message payload."""
    def walk(part) -> str:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            raw = base64.urlsafe_b64decode(part["body"]["data"] + "===")
            return raw.decode("utf-8", "replace")
        for child in part.get("parts", []) or []:
            found = walk(child)
            if found:
                return found
        return ""

    text = walk(msg.get("payload", {}))
    # LinkedIn notification mails carry the real text in the snippet; fall back
    # to it when there's no plain part (they're mostly HTML).
    if not text:
        text = msg.get("snippet", "")
    return re.sub(r"\s+", " ", text).strip()[:limit]


def parse_message(msg: dict) -> dict | None:
    subject = header(msg, "Subject")
    sender = header(msg, "From")
    if not subject and not sender:
        return None
    return {
        "id": msg.get("id", ""),
        "from": sender,
        "subject": subject,
        "snippet": body_text(msg),
        "internalDate": int(msg.get("internalDate") or 0),
    }


# ---------- classification ----------

def classify(msg: dict, role_keywords: list[str]) -> str | None:
    """Return 'recruiter', 'role_match', 'alert' or None to ignore.

    Deliberately conservative: anything LinkedIn's own marketing sends gets
    dropped, because a digest full of noise is one nobody reads.
    """
    subject = (msg.get("subject") or "").lower()
    sender = (msg.get("from") or "").lower()
    text = ((msg.get("snippet") or "") + " " + subject).lower()

    if any(n in subject for n in NOISE_SUBJECT_HINTS):
        return None

    role_hit = any(k in text for k in role_keywords)
    # Words that mean a human is talking to you about a job. Missing an
    # interview is far worse than one extra line, so this stays generous.
    recruiter_hit = any(h in text for h in (
        "recruiter", "recruitment", "talent", "hiring manager",
        "interview", "your application", "shortlist", "cv", "resume",
        "available for", "notice period",
    ))
    linkedin = any(h in sender for h in LINKEDIN_SENDER_HINTS)
    subject_hit = any(h in subject for h in RECRUITER_SUBJECT_HINTS)

    if role_hit and (recruiter_hit or not linkedin):
        return "role_match"
    if recruiter_hit:
        return "recruiter"
    if linkedin and subject_hit:
        return "alert"
    # A non-LinkedIn human writing about a "role" or "opportunity" is almost
    # always a recruiter approach, even without the word "recruiter".
    if not linkedin and any(w in text for w in ("role", "opportunity", "vacancy", "position")):
        return "recruiter"
    return None


def rank(kind: str) -> int:
    return {"role_match": 0, "recruiter": 1, "alert": 2}.get(kind, 3)


def when(msg: dict) -> str:
    ts = msg.get("internalDate")
    if not ts:
        return "unknown"
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    return f"{dt:%d %b %H:%M}"


def summarise(msg: dict) -> str:
    """One-line AI summary of what the sender actually wants. Best-effort."""
    base = os.environ.get("AI_BASE_URL", "").rstrip("/")
    key = os.environ.get("AI_API_KEY", "")
    model = os.environ.get("AI_MODEL", "")
    if not (base and key and model):
        return ""
    prompt = (
        "Summarise this recruiter/job email in one short line for a busy job "
        "seeker. Say who it's from and what they want. No greeting, no fluff.\n\n"
        f"From: {msg.get('from')}\nSubject: {msg.get('subject')}\nBody: {msg.get('snippet')}"
    )
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 80,
    }).encode()
    req = urllib.request.Request(
        f"{base}/chat/completions", data=payload, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.load(resp)
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001
        print("AI summary failed:", e)
        return ""


# ---------- digest + send ----------

def build_digest(items: list[dict]) -> MIMEText:
    now = datetime.now(timezone.utc)
    n = len(items)
    lines = [
        f"{n} message{'s' if n != 1 else ''} worth a look.",
        "These are notifications only — nothing has been replied to. Open the",
        "real thread in LinkedIn or your inbox and reply yourself.",
        "",
    ]
    for i, it in enumerate(items, 1):
        label = {"role_match": "ROLE MATCH", "recruiter": "RECRUITER", "alert": "LINKEDIN"}[it["kind"]]
        lines += ["-" * 60, f"{i}. [{label}] {when(it['msg'])}", f"From: {it['msg']['from']}",
                  f"Subject: {it['msg']['subject']}"]
        if it.get("summary"):
            lines += [f"-> {it['summary']}"]
        else:
            lines += [f"-> {it['msg']['snippet'][:200]}"]
        lines += [""]
    msg = MIMEText("\n".join(lines))
    msg["Subject"] = f"Job watch: {n} message{'s' if n != 1 else ''} - {now:%d %b}"
    msg["From"] = os.environ.get("GMAIL_ADDRESS", "")
    msg["To"] = os.environ.get("RECRUITER_DIGEST_TO") or os.environ.get("GMAIL_ADDRESS", "")
    msg["Date"] = formatdate(localtime=True)
    return msg


def send(msg: MIMEText) -> None:
    addr = os.environ.get("GMAIL_ADDRESS", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not addr or not pw:
        raise RuntimeError("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(addr, pw)
        smtp.send_message(msg)


# ---------- main ----------

def main() -> int:
    report("started", "scanning Gmail for recruiter messages")
    days = int(os.environ.get("RECRUITER_LOOKBACK_DAYS", "2") or 2)
    roles = os.environ.get("RECRUITER_ROLE_KEYWORDS", "")
    role_keywords = [r.strip().lower() for r in roles.split(",") if r.strip()] or DEFAULT_ROLE_KEYWORDS

    try:
        messages = fetch_recent_messages(days)
    except Exception as exc:  # noqa: BLE001
        report("failed", f"Gmail fetch failed: {exc}")
        raise

    items = []
    for m in messages:
        kind = classify(m, role_keywords)
        if kind:
            items.append({"kind": kind, "msg": m})

    items.sort(key=lambda it: (rank(it["kind"]), -it["msg"].get("internalDate", 0)))

    if not items:
        report("idle", f"nothing worth flagging in {len(messages)} messages")
        print("Nothing worth flagging.")
        return 0

    for it in items[:10]:
        it["summary"] = summarise(it["msg"])

    try:
        send(build_digest(items[:10]))
    except Exception as exc:  # noqa: BLE001
        report("failed", f"{len(items)} found but email failed: {exc}")
        raise

    role_matches = sum(1 for it in items if it["kind"] == "role_match")
    report("ok", f"emailed {len(items[:10])} of {len(items)} flagged ({role_matches} role matches)")
    print(f"Emailed digest with {len(items[:10])} of {len(items)} flagged messages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
