#!/usr/bin/env python3
"""
Hosting Renewal Reminder Job
=============================

Reads a Google Sheet of hosting clients and emails renewal reminders at
three points before each client's expiry date: 30 days, 14 days, and 7
days out. Designed to run once per day (cron, or as a PyRunner scheduled
job) — it is safe to re-run: each reminder is only ever sent once per
client, tracked via "sent" columns written back to the sheet.

Sheet columns expected (header row, any order, matched by name):
    Website URL
    Customer Name
    Customer Email
    Renewal Cost
    Expiry Date            (YYYY-MM-DD)
    Hosting Type
    30-Day Reminder Sent    (written by this script)
    14-Day Reminder Sent    (written by this script)
    7-Day Reminder Sent     (written by this script)
    Notes                   (optional, ignored)

Configuration is read from environment variables — see .env.example.

NO THIRD-PARTY DEPENDENCIES. This uses only the Python standard library
(urllib, json, smtplib, email) so it runs anywhere Python 3 runs — no
`pip install` step, no requirements.txt needed, which matters on a
platform like PyRunner where you can't be sure what's installable.

Instead of the Google Sheets API + a service account, this talks to a
small Google Apps Script "web app" bound to the sheet (see
google_apps_script.gs and the README) using plain HTTP + JSON.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from email.mime.text import MIMEText


# --------------------------------------------------------------------------
# AI OS dashboard reporting (inlined: PyRunner runs each script standalone)
# --------------------------------------------------------------------------

AIOS_WEBHOOK_URL = "https://aios.webawesome.co.uk/webhook/pyrunner"


def report(agent: str, status: str, message: str = "") -> bool:
    """Send one status event to the AI OS dashboard. Never raises."""
    secret = os.environ.get("PYRUNNER_WEBHOOK_SECRET", "")
    if not secret:
        print("AIOS report skipped: PYRUNNER_WEBHOOK_SECRET not set")
        return False
    try:
        data = {"agent": agent, "status": status, "message": str(message)[:500]}
        body = json.dumps(data).encode()
        ts = str(int(time.time()))
        signed = f"{ts}.".encode() + body
        sig = "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-AIOS-Timestamp": ts,
            "X-AIOS-Signature": sig,
        }
        req = urllib.request.Request(AIOS_WEBHOOK_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("AIOS report sent:", resp.status)
        return True
    except Exception as exc:
        print("AIOS report failed:", exc)
        return False


def _load_dotenv_if_present(path: str = ".env") -> None:
    """Tiny stdlib-only .env loader (for local testing). Never overrides a
    variable that's already set in the real environment, so this is safe
    to leave in when running on a platform that injects real env vars."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_dotenv_if_present()

# --------------------------------------------------------------------------
# Configuration (all from environment variables)
# --------------------------------------------------------------------------

SHEETS_WEBAPP_URL = os.environ.get("SHEETS_WEBAPP_URL", "")
SHEETS_WEBAPP_SECRET = os.environ.get("SHEETS_WEBAPP_SECRET", "")
WORKSHEET_NAME = os.environ.get("WORKSHEET_NAME", "Sheet1")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
SENDER_NAME = os.environ.get("SENDER_NAME", "Webawesome Consult UK")
REPLY_TO = os.environ.get("REPLY_TO", GMAIL_ADDRESS)

BANK_ACCOUNT_NAME = os.environ.get("BANK_ACCOUNT_NAME", "")
BANK_SORT_CODE = os.environ.get("BANK_SORT_CODE", "")
BANK_ACCOUNT_NUMBER = os.environ.get("BANK_ACCOUNT_NUMBER", "")
BANK_NAME = os.environ.get("BANK_NAME", "")

DRY_RUN = os.environ.get("DRY_RUN", "false").strip().lower() in ("1", "true", "yes")

# Reminder bands: (threshold_days, sheet_column_name, notice_label)
# A reminder fires once days-until-expiry falls to at or below the
# threshold, but only within its own band, so a client added late doesn't
# get every earlier reminder all at once.
REMINDER_BANDS = [
    (30, "30-Day Reminder Sent", "1 Month"),
    (14, "14-Day Reminder Sent", "2 Weeks"),
    (7, "7-Day Reminder Sent", "1 Week"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("hosting_renewal_reminders")


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class ClientRow:
    row_number: int  # 1-indexed sheet row, for writing back
    website_url: str
    customer_name: str
    customer_email: str
    renewal_cost: str
    expiry_date: date
    hosting_type: str
    sent_flags: dict  # column name -> raw cell value


REQUIRED_COLUMNS = [
    "Website URL",
    "Customer Name",
    "Customer Email",
    "Renewal Cost",
    "Expiry Date",
    "Hosting Type",
]


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    # Belt-and-braces: if a Date-formatted cell ever slips through as a
    # full ISO timestamp (e.g. "2026-10-09T07:00:00.000Z") instead of the
    # plain date the Apps Script bridge normally sends, just take the date
    # part. The Apps Script side already normalizes this; this is a backup.
    if "T" in raw:
        raw = raw.split("T", 1)[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    log.warning("Could not parse expiry date %r — skipping row", raw)
    return None


# --------------------------------------------------------------------------
# Google Sheets, via the Apps Script web app bridge (no SDK, no auth lib)
# --------------------------------------------------------------------------

class SheetClient:
    """Talks to the Apps Script web app deployed from google_apps_script.gs.
    Mirrors just the two operations this script needs, using plain HTTP."""

    def __init__(self, webapp_url: str, secret: str, sheet_name: str):
        self.webapp_url = webapp_url.rstrip("/")
        self.secret = secret
        self.sheet_name = sheet_name

    def _request(self, req: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach Sheets web app: {exc}") from exc
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"Sheets web app error: {data['error']}")
        return data

    def get_all_values(self) -> list[list[str]]:
        query = urllib.parse.urlencode({"secret": self.secret, "sheet": self.sheet_name})
        req = urllib.request.Request(f"{self.webapp_url}?{query}", method="GET")
        data = self._request(req)
        return data.get("rows", [])

    def update_cell(self, row: int, col: int, value: str) -> None:
        payload = json.dumps(
            {
                "secret": self.secret,
                "sheet": self.sheet_name,
                "row": row,
                "col": col,
                "value": value,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self.webapp_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        self._request(req)


def open_worksheet() -> SheetClient:
    if not SHEETS_WEBAPP_URL or not SHEETS_WEBAPP_SECRET:
        log.error(
            "SHEETS_WEBAPP_URL and SHEETS_WEBAPP_SECRET must be set — see .env.example"
        )
        sys.exit(1)
    return SheetClient(SHEETS_WEBAPP_URL, SHEETS_WEBAPP_SECRET, WORKSHEET_NAME)


def load_clients(ws: SheetClient) -> tuple[list[ClientRow], dict]:
    values = ws.get_all_values()
    if not values:
        return [], {}

    header = values[0]
    col_index = {name: i for i, name in enumerate(header)}

    missing = [c for c in REQUIRED_COLUMNS if c not in col_index]
    if missing:
        log.error("Sheet is missing required columns: %s", ", ".join(missing))
        sys.exit(1)

    clients: list[ClientRow] = []
    for i, row in enumerate(values[1:], start=2):  # sheet rows are 1-indexed, row 1 is header
        def cell(name: str) -> str:
            idx = col_index.get(name)
            return str(row[idx]).strip() if idx is not None and idx < len(row) else ""

        website_url = cell("Website URL")
        customer_email = cell("Customer Email")
        if not website_url and not customer_email:
            continue  # blank row

        expiry = parse_date(cell("Expiry Date"))
        if expiry is None or not customer_email:
            continue

        sent_flags = {}
        for _, colname, _ in REMINDER_BANDS:
            idx = col_index.get(colname)
            sent_flags[colname] = str(row[idx]).strip() if idx is not None and idx < len(row) else ""

        clients.append(
            ClientRow(
                row_number=i,
                website_url=website_url,
                customer_name=cell("Customer Name"),
                customer_email=customer_email,
                renewal_cost=cell("Renewal Cost"),
                expiry_date=expiry,
                hosting_type=cell("Hosting Type"),
                sent_flags=sent_flags,
            )
        )

    return clients, col_index


def mark_sent(ws: SheetClient, row_number: int, col_index: dict, colname: str) -> None:
    idx = col_index.get(colname)
    if idx is None:
        log.warning(
            "Column %r not found in sheet — add it so future runs can track this reminder",
            colname,
        )
        return
    if DRY_RUN:
        log.info("[DRY RUN] Would mark row %s column %r as sent", row_number, colname)
        return
    ws.update_cell(row_number, idx + 1, date.today().isoformat())


# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------

def build_email(client: ClientRow, notice_label: str) -> MIMEText:
    days_left = (client.expiry_date - date.today()).days
    payment_lines = []
    if BANK_ACCOUNT_NAME:
        payment_lines.append(f"Account Name: {BANK_ACCOUNT_NAME}")
    if BANK_NAME:
        payment_lines.append(f"Bank: {BANK_NAME}")
    if BANK_SORT_CODE:
        payment_lines.append(f"Sort Code: {BANK_SORT_CODE}")
    if BANK_ACCOUNT_NUMBER:
        payment_lines.append(f"Account Number: {BANK_ACCOUNT_NUMBER}")
    payment_lines.append(f"Payment Reference: {client.website_url}")
    payment_block = "\n".join(payment_lines)

    cost_line = f"£{client.renewal_cost}" if client.renewal_cost else "the amount on your plan"

    body = f"""Hi {client.customer_name or 'there'},

This is a friendly reminder that the {client.hosting_type or 'web'} hosting for
{client.website_url} is due for renewal on {client.expiry_date.strftime('%d %B %Y')}
({days_left} day{'s' if days_left != 1 else ''} from now).

Renewal amount due: {cost_line}

Payment details:
{payment_block}

If you have already made this payment, please ignore this email — no action is needed.

If you decide you dont want to renew please note that all services such as the emails
and website attached to the service will stop working and you will be required to set
up new services at a cost to you!

Got any questions?, just reply to this email and we'll be happy to help.

Thanks,
{SENDER_NAME}
"""

    subject = (
        f"Hosting renewal reminder ({notice_label} notice) — {client.website_url} "
        f"renews {client.expiry_date.strftime('%d %b %Y')}"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = client.customer_email
    if REPLY_TO:
        msg["Reply-To"] = REPLY_TO
    return msg


def send_email(msg: MIMEText) -> None:
    if DRY_RUN:
        log.info("[DRY RUN] Would send email to %s: %s", msg["To"], msg["Subject"])
        return
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        log.error("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set — see .env.example")
        sys.exit(1)
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)


# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------

def band_for(days_left: int) -> tuple[int, str, str] | None:
    """Return the reminder band a client currently falls into, if any."""
    for i, (threshold, colname, label) in enumerate(REMINDER_BANDS):
        lower_bound = REMINDER_BANDS[i + 1][0] if i + 1 < len(REMINDER_BANDS) else -1
        if lower_bound < days_left <= threshold:
            return threshold, colname, label
    return None


def process_client(ws: SheetClient, col_index: dict, client: ClientRow) -> str:
    """Process one client; returns 'sent' if a reminder went out, else 'skipped'."""
    days_left = (client.expiry_date - date.today()).days
    if days_left < 0:
        log.info("%s (%s) already expired %s days ago — skipping", client.website_url,
                  client.customer_email, -days_left)
        return "skipped"

    band = band_for(days_left)
    if band is None:
        return "skipped"  # more than 30 days out, or between bands with nothing due

    threshold, colname, label = band
    if client.sent_flags.get(colname):
        return "skipped"  # already sent for this band

    log.info(
        "Sending %s reminder to %s for %s (expires %s, %s days left)",
        label, client.customer_email, client.website_url, client.expiry_date, days_left,
    )
    msg = build_email(client, label)
    send_email(msg)
    mark_sent(ws, client.row_number, col_index, colname)
    return "sent"


def main() -> None:
    report("hosting-renewal-reminders", "started", "DRY RUN" if DRY_RUN else "live")
    ws = open_worksheet()
    clients, col_index = load_clients(ws)
    log.info("Loaded %d client row(s) from sheet", len(clients))

    sent_count = 0
    failed_count = 0
    for client in clients:
        try:
            if process_client(ws, col_index, client) == "sent":
                sent_count += 1
        except Exception:
            failed_count += 1
            log.exception("Failed processing row %s (%s)", client.row_number, client.customer_email)

    if failed_count:
        report("hosting-renewal-reminders", "failed",
               f"{sent_count} sent, {failed_count} of {len(clients)} row(s) failed — check PyRunner logs")
    elif sent_count:
        report("hosting-renewal-reminders", "ok",
               f"{sent_count} reminder(s) sent ({len(clients)} client(s) checked)")
    else:
        report("hosting-renewal-reminders", "idle",
               f"nothing due ({len(clients)} client(s) checked)")

    log.info("Done.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        if err.code not in (0, None):
            report("hosting-renewal-reminders", "failed", "setup problem — check PyRunner logs")
        raise
    except Exception as err:
        report("hosting-renewal-reminders", "failed", str(err))
        raise
