"""Lodgify guest reply drafter -> daily email digest.

Runs on a schedule in PyRunner (standalone — no repo imports, everything
inlined). Reads Lodgify's read-only Public API v2 for messaging threads
where the guest spoke last, skips pure sign-offs, drafts a short reply for
each with the AI, and emails the ready-to-paste drafts to the owner.

It never sends anything to a guest. The owner copies each draft into its
Lodgify thread and sends it by hand. That human-in-the-loop step is what
keeps this inside Lodgify's and the OTAs' (Airbnb/Vrbo/Booking.com) rules.

PyRunner secrets to set:
  LODGIFY_API_KEY          Lodgify dashboard -> Integrations -> API
  AI_BASE_URL              e.g. https://opencode.ai/zen/v1
  AI_MODEL                 e.g. minimax-m2.5
  AI_API_KEY               the AI provider key
  GMAIL_ADDRESS            sending mailbox (Gmail address)
  GMAIL_APP_PASSWORD       Gmail app password (Google Account -> Security)
  LODGIFY_DRAFT_TO         who receives the digest (default the sender)
  PYRUNNER_WEBHOOK_SECRET  same value as the AI OS server
Optional:
  REPLY_TO                 reply-to on the digest (default the sender)
  LODGIFY_UNANSWERED_MINUTES  only drafts waiting at least this long (default 0)

Schedule suggestion: every day at 07:30 Europe/London.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import smtplib
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.utils import formatdate

# ---------- AI OS dashboard reporting (inlined; PyRunner runs standalone) ----------

AIOS_WEBHOOK_URL = "https://aios.webawesome.co.uk/webhook/pyrunner"
AGENT = "lodgify-reply-drafter"


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


# ---------- Lodgify (read-only v2) ----------

API_BASE = "https://api.lodgify.com"
MAX_THREADS = 25

# Both Overcomers listings share one guest FAQ. Kept as a compact digest:
# drafts stay minimal, so the AI uses this only to answer a specific question
# — never to pour house rules into a reply (Lodgify already auto-sends those).
FAQ_DIGEST = """\
Check-in from 3:00pm, check-out by 11:00am. Self check-in: keys in a key safe,
check-in instructions sent on arrival day. Late arrivals are fine. Early bag
drop only if the apartment is empty.
Parking: free, own car park under the building; two bays are reserved for the
apartment; enter with the fob on the key bunch. Indoors, so tall/large vehicles
may not fit. Car park is monitored. EV charging not available. A third car can
park on-street in front of the building.
Apartment: 5th floor; steps from the street to the front door (not step-free).
~10-minute walk to Utilita Arena, Sea Life Centre and Brindleyplace. Nearest
station is Birmingham New Street. Taxis drop off in front of the building.
Sleeps four, two bedrooms with double beds (a sofa bed does not raise the max).
Two shower rooms. Linen, towels and toiletries provided. Cot/high chair on
request. Balcony has no furniture and shouldn't be used at night; no smoking on
it.
Kitchen is fully equipped; washing machine; welcome tea/coffee; heating and air
conditioning; hairdryer, iron, ironing board; TV with Netflix; dining table for
four; fast Wi-Fi (tested 350-500 Mbps); desk. You may hear noise from nearby
events on busy days; other residents live in the building; quiet hours are in
the afternoons.
Rules: no pets, no smoking or vaping, no parties/events, visitors by
arrangement (overnight visitors may cost extra). Lead guest must be 18+; no ID
asked at check-in. Guests are responsible for damage or lost keys.
Contact: message through the booking platform; we usually reply within the
hour.
"""


def _get(path: str, params: dict | None = None) -> object:
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "X-ApiKey": os.environ["LODGIFY_API_KEY"],
        "Accept": "application/json",
        "User-Agent": "AI-OS-Lodgify-Drafter/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _parse_dt(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(text[:10])
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _plain(raw) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(raw))
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"&amp;", "&", text)
    return re.sub(r"\s+", " ", text).strip()


CLOSING_PATTERN = re.compile(
    r"\b(thanks?(\s+you|\s+a\s+lot|\s+so\s+much)?|thank\s+you|many\s+thanks|cheers|\bta\b|"
    r"bye|goodbye|see\s+you|will\s+do|much\s+appreciated|appreciate\s+it|"
    r"all\s+good|no\s+worries|perfect|great|lovely|brilliant|ok(ay)?|noted|understood)\b",
    re.I)
QUESTION_PATTERN = re.compile(
    r"\b(please|could|can\s+you|would\s+you|need|require|question|how|what|when|"
    r"where|why|which|who|any\s+chance|let\s+me\s+know)\b", re.I)


def looks_like_closing(raw) -> bool:
    """True for a pure guest sign-off that needs no reply."""
    plain = _plain(raw)
    if not plain or "?" in plain or QUESTION_PATTERN.search(plain):
        return False
    if not CLOSING_PATTERN.search(plain):
        return False
    residue = CLOSING_PATTERN.sub(" ", plain)
    residue = re.sub(r"[^A-Za-z\s]", " ", residue)
    return len(residue.split()) <= 3


def fetch_needs_reply():
    """Threads where the guest spoke last and left real content. Read-only."""
    bookings = {}
    for stay_filter in ("Upcoming", "Current"):
        data = _get("/v2/reservations/bookings",
                    {"stayFilter": stay_filter, "page": 1, "size": 50, "includeCount": "true"})
        items = data.get("items") if isinstance(data, dict) else data
        for b in items or []:
            if isinstance(b, dict) and b.get("id") is not None:
                bookings[b["id"]] = b

    try:
        props = _get("/v2/properties")
        rows = props if isinstance(props, list) else (props.get("items") if isinstance(props, dict) else [])
        names = {r["id"]: (r.get("name") or f"Property {r['id']}") for r in rows or [] if isinstance(r, dict)}
    except Exception:  # noqa: BLE001
        names = {}

    out, fetched = [], 0
    for b in bookings.values():
        uid = b.get("thread_uid")
        if not uid or fetched >= MAX_THREADS:
            continue
        fetched += 1
        try:
            data = _get(f"/v2/messaging/{uid}")
        except Exception as exc:  # noqa: BLE001
            print("thread fetch failed:", uid, exc)
            continue
        threads = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        for thread in threads:
            if not isinstance(thread, dict):
                continue
            messages = thread.get("messages") or []
            renter = [m for m in messages if str(m.get("type", "")).lower() == "renter"]
            if not renter:
                continue
            last = max(renter, key=lambda m: _parse_dt(m.get("date_created")) or datetime.min.replace(tzinfo=timezone.utc))
            last_at = _parse_dt(last.get("date_created"))
            owner_after = any(
                str(m.get("type", "")).lower() == "owner"
                and (_parse_dt(m.get("date_created")) or datetime.min.replace(tzinfo=timezone.utc))
                >= (last_at or datetime.min.replace(tzinfo=timezone.utc))
                for m in messages)
            if owner_after:
                continue
            if looks_like_closing(last.get("message")):
                continue
            waiting = max(0, int((datetime.now(timezone.utc) - last_at).total_seconds() // 60)) if last_at else None
            convo = []
            for m in sorted(messages, key=lambda x: _parse_dt(x.get("date_created")) or datetime.min.replace(tzinfo=timezone.utc)):
                who = "GUEST" if str(m.get("type", "")).lower() == "renter" else "HOST"
                convo.append(f"{who}: {_plain(m.get('message'))}")
            out.append({
                "guest": thread.get("guest_name") or (b.get("guest") or {}).get("name") or "Guest",
                "property": names.get(b.get("property_id"), f"Property {b.get('property_id')}"),
                "waitingMinutes": waiting,
                "lastMessage": _plain(last.get("message")),
                "conversation": convo,
            })
    out.sort(key=lambda t: -(t.get("waitingMinutes") or 0))
    return out


# ---------- AI drafting ----------

PROMPT = """You draft a short reply from a UK short-stay host to a guest message. \
A human reviews it and sends it inside the Lodgify inbox. Reply as the host.
Rules:
- Warm, human, concise: one to three short sentences. Plain text only.
- NEVER include links, URLs, email addresses, phone numbers, emojis or HTML \
(Vrbo forbids links and contact details in messages).
- Answer only what the guest actually raised. Routine info is already sent \
automatically, so do not repeat house rules or dump FAQ content.
- Use the FAQ reference only if it answers the guest's specific question.
- Never invent prices, discounts, deposits or policies. If something is \
genuinely unknown, keep the reply neutral and put a one-line note for the host \
after a NOTE: line, e.g. "NOTE: confirm the earlier check-in is possible".
Output exactly:
REPLY:
<the reply text>
NOTE:
<one short line for the host, or "none">
"""


def draft_one(thread) -> tuple[str, str]:
    """Return (reply, note). Falls back to a hand-reply note on failure."""
    base = os.environ.get("AI_BASE_URL", "").rstrip("/")
    model = os.environ.get("AI_MODEL", "")
    key = os.environ.get("AI_API_KEY", "")
    if not (base and model and key):
        return ("", "AI not configured - reply by hand")
    user = (f"Property: {thread['property']}\n"
            f"Conversation:\n" + "\n".join(thread["conversation"]) +
            f"\n\nFAQ reference:\n{FAQ_DIGEST}")
    try:
        body = json.dumps({"model": model, "messages": [
            {"role": "system", "content": PROMPT}, {"role": "user", "content": user}]}).encode()
        req = urllib.request.Request(base + "/chat/completions", data=body, method="POST", headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            # Same UA as the other PyRunner scripts: providers WAF-block the
            # default Python-urllib UA with a bare 403.
            "User-Agent": "Mozilla/5.0 (compatible; WebAwesomeBot/1.0)",
        })
        with urllib.request.urlopen(req, timeout=90) as resp:
            text = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
        text = re.sub(r"```.*?```", "", text, flags=re.S).strip()
        note = ""
        if "NOTE:" in text:
            text, _, note = text.partition("NOTE:")
        reply = text.split("REPLY:", 1)[-1].strip()
        note = note.strip()
        return (reply, "" if note.lower() in ("", "none") else note)
    except Exception as exc:  # noqa: BLE001
        detail = ""
        if hasattr(exc, "read"):
            try:
                detail = exc.read().decode()[:400]
            except Exception:  # noqa: BLE001
                detail = ""
        print("AI draft failed:", type(exc).__name__, exc, "|", detail)
        return ("", f"AI draft failed ({type(exc).__name__} {exc}) - reply by hand")


# ---------- email digest ----------

def humanize(minutes):
    if minutes is None:
        return "unknown"
    if minutes < 60:
        return f"{minutes} min"
    if minutes < 60 * 24:
        return f"{minutes // 60} h"
    return f"{minutes // (60 * 24)} d"


def build_digest(threads) -> MIMEText:
    now = datetime.now(timezone.utc)
    n = len(threads)
    lines = [f"{n} Lodgify thread{'s' if n != 1 else ''} need a reply.",
             "Copy each draft into its Lodgify thread, then send it yourself.", ""]
    for i, t in enumerate(threads, 1):
        lines += ["-" * 60,
                  f"{i}. {t['guest']} - {t['property']}  (waiting {humanize(t.get('waitingMinutes'))})",
                  f'Last message: "{t["lastMessage"]}"', ""]
        if t.get("reply"):
            lines += ["Draft:", t["reply"], ""]
        if t.get("note"):
            lines += [f"Host note: {t['note']}", ""]
    msg = MIMEText("\n".join(lines))
    msg["Subject"] = f"Lodgify: {n} guest repl{'y' if n == 1 else 'ies'} to send - {now:%d %b}"
    msg["From"] = os.environ.get("GMAIL_ADDRESS", "")
    msg["To"] = os.environ.get("LODGIFY_DRAFT_TO") or os.environ.get("GMAIL_ADDRESS", "")
    msg["Reply-To"] = os.environ.get("REPLY_TO") or os.environ.get("GMAIL_ADDRESS", "")
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
    if not os.environ.get("LODGIFY_API_KEY"):
        report("failed", "LODGIFY_API_KEY not set")
        print("LODGIFY_API_KEY not set")
        return 1

    report("started", "checking Lodgify for guest replies")
    try:
        threads = fetch_needs_reply()
    except Exception as exc:  # noqa: BLE001
        report("failed", f"Lodgify fetch failed: {exc}")
        raise

    min_wait = int(os.environ.get("LODGIFY_UNANSWERED_MINUTES", "0") or 0)
    if min_wait:
        threads = [t for t in threads if (t.get("waitingMinutes") or 0) >= min_wait]

    if not threads:
        report("idle", "no guest replies needed")
        print("No threads need a reply.")
        return 0

    for t in threads:
        t["reply"], t["note"] = draft_one(t)

    drafted = sum(1 for t in threads if t.get("reply"))
    try:
        send(build_digest(threads))
    except Exception as exc:  # noqa: BLE001
        report("failed", f"{len(threads)} drafted but email failed: {exc}")
        raise

    if drafted == len(threads):
        report("ok", f"emailed {len(threads)} draft repl{'y' if len(threads) == 1 else 'ies'}")
    else:
        report("ok", f"emailed {len(threads)} threads ({drafted} drafted, rest need hand-reply)")
    print(f"Emailed digest with {len(threads)} threads ({drafted} drafted).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
