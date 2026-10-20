"""Overcomers cleaner departure notices -> daily email digest.

Tells the cleaning team who is checking out and when, so they can slot in a
clean before the next guests arrive. Read-only against Lodgify Public API v2.
No guest names are included — dates, property and turnover gaps only.

Standalone for PyRunner (no repo imports, everything inlined). Reports one
started/ok/idle/failed event to the AI OS dashboard per run.

PyRunner secrets to set:
  LODGIFY_API_KEY          Lodgify dashboard -> Integrations -> API
  CLEANER_EMAILS           comma-separated recipient list (the cleaner)
  GMAIL_ADDRESS            sending mailbox (Gmail address)
  GMAIL_APP_PASSWORD       Gmail app password (Google Account -> Security)
  PYRUNNER_WEBHOOK_SECRET  same value as the AI OS server
Optional:
  CLEANER_WINDOW_DAYS      how many days ahead to list (default 14)
  CLEANER_FROM_NAME        sender label (default "Overcomers Cleaning")
  CLEANER_CC               optional CC address (e.g. your own inbox)

Schedule suggestion: daily, 07:45 Europe/London.
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
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.utils import formatdate
from zoneinfo import ZoneInfo

# ---------- AI OS dashboard reporting (inlined; PyRunner runs standalone) ----------

AIOS_WEBHOOK_URL = "https://aios.webawesome.co.uk/webhook/pyrunner"
AGENT = "overcomers-cleaner-notices"
TZ = ZoneInfo("Europe/London")


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
CHECK_OUT = "11:00"
CHECK_IN = "15:00"

# Lodgify listing name -> the name the cleaning team knows it by.
PROPERTY_LABELS = {
    "stylish city living": "Cutlass Court",
    "cutlass": "Cutlass Court",
    "digbeth": "Modern Digbeth Stay",
}


def _get(path: str, params: dict | None = None) -> object:
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "X-ApiKey": os.environ["LODGIFY_API_KEY"],
        "Accept": "application/json",
        "User-Agent": "AI-OS-Cleaner-Notices/1.0",
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


def label_for(property_name: str) -> str:
    name = (property_name or "").lower()
    for key, label in PROPERTY_LABELS.items():
        if key in name:
            return label
    return (property_name or "Unknown property").split("|")[0].strip()


def _day(value):
    parsed = _parse_dt(value)
    return parsed.astimezone(TZ).date() if parsed else None


def fetch_stays():
    """Upcoming + Current bookings, deduped, still-active statuses only."""
    names = {}
    try:
        props = _get("/v2/properties")
        rows = props if isinstance(props, list) else (props.get("items") if isinstance(props, dict) else [])
        names = {r["id"]: r.get("name") or "" for r in rows or [] if isinstance(r, dict)}
    except Exception as exc:  # noqa: BLE001
        print("property names unavailable:", exc)

    bookings = {}
    for stay_filter in ("Upcoming", "Current"):
        data = _get("/v2/reservations/bookings",
                    {"stayFilter": stay_filter, "page": 1, "size": 50, "includeCount": "true"})
        items = data.get("items") if isinstance(data, dict) else data
        for b in items or []:
            if isinstance(b, dict) and b.get("id") is not None:
                bookings[b["id"]] = b

    stays = []
    include_open = os.environ.get("CLEANER_INCLUDE_OPEN", "").lower() in ("1", "true", "yes")
    for b in bookings.values():
        status = (b.get("status") or "").lower()
        # Only confirmed stays: an Open/Tentative booking could still be
        # cancelled, and the cleaner should not plan a clean around it.
        if status != "booked" and not (include_open and status in ("open", "tentative")):
            continue
        departure = _day(b.get("departure"))
        if not departure:
            continue
        stays.append({
            "property": label_for(names.get(b.get("property_id"), f"Property {b.get('property_id')}")),
            "arrival": _day(b.get("arrival")),
            "departure": departure,
        })
    stays.sort(key=lambda s: (s["property"], s["departure"]))
    return stays


def build_lines(stays, today, window_days):
    """Departure lines per property, with the following arrival and its gap."""
    by_property = {}
    for s in stays:
        by_property.setdefault(s["property"], []).append(s)

    lines = []
    count = 0
    for prop in sorted(by_property):
        entries = sorted(by_property[prop], key=lambda s: s["departure"])
        departures = [e for e in entries if today <= e["departure"] <= today + timedelta(days=window_days)]
        if not departures:
            continue
        lines.append(prop)
        seen_dates = set()
        for dep in departures:
            if dep["departure"] in seen_dates:
                continue  # several stays leaving the same day = one clean
            seen_dates.add(dep["departure"])
            after = [e for e in entries if e["departure"] > dep["departure"]]
            nxt = after[0] if after else None
            gap = (nxt["departure"] - dep["departure"]).days if nxt and nxt["arrival"] else None
            if nxt and nxt["arrival"] == dep["departure"]:
                turn = f"URGENT - next guests arrive the same day ({CHECK_IN})"
            elif nxt and nxt["arrival"]:
                turn = f"next guests arrive {nxt['arrival']:%a %d %b} ({gap} day gap)"
            else:
                turn = "no further bookings yet"
            lines.append(f"  {dep['departure']:%a %d %b}  {CHECK_OUT} checkout  ->  {turn}")
            count += 1
        lines.append("")
    return lines, count


def build_digest(stays, today, window_days) -> MIMEText | None:
    lines, count = build_lines(stays, today, window_days)
    if not count:
        return None
    end = today + timedelta(days=window_days)
    body = [
        f"Departures for {today:%d %b} to {end:%d %b} (check-out {CHECK_OUT}).",
        "Cleaning needs doing before the next guests check in at " + CHECK_IN + ".",
        "",
    ] + lines
    msg = MIMEText("\n".join(body))
    msg["Subject"] = f"Overcomers cleaning: {count} departure{'s' if count != 1 else ''} {today:%d %b}-{end:%d %b}"
    msg["From"] = f"{os.environ.get('CLEANER_FROM_NAME', 'Overcomers Cleaning')} <{os.environ.get('GMAIL_ADDRESS', '')}>"
    msg["To"] = os.environ.get("CLEANER_EMAILS", "")
    cc = os.environ.get("CLEANER_CC", "").strip()
    if cc:
        msg["Cc"] = cc
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
    if not os.environ.get("CLEANER_EMAILS"):
        report("failed", "CLEANER_EMAILS not set")
        print("CLEANER_EMAILS not set")
        return 1

    today = datetime.now(TZ).date()
    window = int(os.environ.get("CLEANER_WINDOW_DAYS", "14") or 14)
    report("started", f"departures {today:%d %b}, next {window} days")

    try:
        stays = fetch_stays()
        msg = build_digest(stays, today, window)
    except Exception as exc:  # noqa: BLE001
        report("failed", f"Lodgify fetch failed: {exc}")
        raise

    if msg is None:
        report("idle", f"no departures in the next {window} days")
        print("No departures in window.")
        return 0

    try:
        send(msg)
    except Exception as exc:  # noqa: BLE001
        report("failed", f"email failed: {exc}")
        raise

    _, count = build_lines(stays, today, window)
    report("ok", f"emailed {count} departure{'s' if count != 1 else ''} to cleaner")
    print(f"Emailed {count} departures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
