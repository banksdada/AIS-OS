#!/usr/bin/env python3
"""
Parking permit intake: Lodgify guest messages -> Google Sheet "Guests" tab.

For each confirmed (Booked) Lodgify stay, reads the guest's messages, finds a
UK registration plate and a car make/colour, and appends one row (columns A-F)
to the Guests tab. The Apps Script in the sheet then takes over: it emails the
processor, sends reminders, and handles the Confirm button.

Rules:
  * Only Booked bookings. Only Renter (guest) messages are read.
  * A plate counts only when the message also mentions reg/registration/plate/
    car/vehicle, which avoids picking up random capitalised words.
  * No make/model is fine (registration only); the Vehicle column gets
    'Not provided' so the Apps Script still starts the row.
  * No guest email is also fine: the row is written with a note asking the
    team to collect an email. No confirmation is ever emailed to a guest
    without an address (the Apps Script guards that side).
  * A row is skipped if the sheet already has the same guest email + check-in,
    or the same registration + check-in. The sheet is the source of truth.

Usage:
  python3 scripts/parking_permits.py            # dry run: print candidates, write nothing
  python3 scripts/parking_permits.py --write    # append new rows to the sheet
"""
import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, 'scripts'))

_ENV = os.path.join(_REPO_ROOT, '.env')
if os.path.exists(_ENV):
    with open(_ENV) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from dashboard import lodgify as lg  # noqa: E402

SHEET_ID = os.environ.get('PERMIT_SHEET_ID', '1ZAQhPWOShrp0xX-Em4_wZl4reKK48HmLt0CyFIlF5uk')
SHEET_TAB = os.environ.get('PERMIT_SHEET_TAB', 'Guests')
CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS_PATH',
                             os.path.join(_REPO_ROOT, 'scripts', 'credentials.json'))
TIMEZONE = ZoneInfo('Europe/London')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
NOT_PROVIDED = 'Not provided'
NO_EMAIL_NOTE = ('No email on file - ask the guest via Lodgify to provide one '
                 'so they can receive parking permit confirmations.')

# UK formats: current "AB12 CDE" / "AB12CDE", and prefix-style "J25 STV"
PLATE_RE = re.compile(r'\b([A-Z]{2}\d{2}\s?[A-Z]{3}|[A-Z]\d{1,3}\s?[A-Z]{3})\b', re.I)
KEYWORD_RE = re.compile(r'\b(reg|regs|registration|plate|vehicle|car)\b', re.I)

MAKES = [
    'Alfa Romeo', 'Audi', 'BMW', 'Citroen', 'Dacia', 'Fiat', 'Ford', 'Honda', 'Hyundai',
    'Jaguar', 'Jeep', 'Kia', 'Land Rover', 'Lexus', 'Mazda', 'Mercedes', 'MG', 'Mini',
    'Mitsubishi', 'Nissan', 'Peugeot', 'Polestar', 'Porsche', 'Range Rover', 'Renault',
    'Seat', 'Skoda', 'Subaru', 'Suzuki', 'Tesla', 'Toyota', 'Vauxhall', 'Volkswagen',
    'VW', 'Volvo',
]
MAKE_RE = re.compile(r'\b(' + '|'.join(re.escape(m) for m in MAKES) + r')\b', re.I)
COLOURS = ['black', 'white', 'silver', 'grey', 'gray', 'blue', 'red', 'green', 'yellow',
           'orange', 'brown', 'gold', 'beige', 'purple']
COLOUR_RE = re.compile(r'\b(' + '|'.join(COLOURS) + r')\b', re.I)


def plain_text(raw):
    """Message body with HTML removed and entities decoded (no truncation)."""
    text = re.sub(r'<[^>]+>', ' ', str(raw or ''))
    return ' '.join(html.unescape(text).split())


def find_plates(text):
    """Normalised UK plates in the text, only if a vehicle keyword is present."""
    if not text or not KEYWORD_RE.search(text):
        return []
    plates = []
    for m in PLATE_RE.finditer(text):
        plate = m.group(1).replace(' ', '').upper()
        if plate not in plates:
            plates.append(plate)
    return plates


def find_vehicle(text):
    """Make/model (and colour if stated near it), e.g. 'Honda Civic, silver'."""
    m = MAKE_RE.search(text or '')
    if not m:
        return ''
    tail = text[m.start():m.start() + 60]
    tail = re.split(r'[.,;!?\n]', tail)[0].strip()
    colour = ''
    before = text[max(0, m.start() - 25):m.start()]
    cm = COLOUR_RE.search(before)
    if cm:
        colour = cm.group(1).lower()
    value = ' '.join(tail.split())[:60]
    return f'{value}, {colour}' if colour and colour not in value.lower() else value


def _date_text(value):
    """'dd/mm/yyyy' in UK time from a Lodgify date or datetime string, or ''."""
    parsed = lg._parse_dt(value)
    if not parsed:
        return ''
    return parsed.astimezone(TIMEZONE).strftime('%d/%m/%Y')


def _day(value):
    parsed = lg._parse_dt(value)
    return parsed.astimezone(TIMEZONE).date() if parsed else None


def build_candidates(bookings, messages_by_thread, today, thread_emails=None):
    """Pure function: rows to add, plus a list of skipped bookings with reasons.

    bookings: Lodgify booking dicts (already filtered to Booked).
    messages_by_thread: {thread_uid: [message texts]} for Renter messages.
    today: date in UK time. Stays that have already ended are ignored.
    thread_emails: {thread_uid: guest email} used when the booking has none.
    """
    thread_emails = thread_emails or {}
    rows, skipped = [], []
    for b in bookings:
        guest = b.get('guest') or {}
        name = (guest.get('name') or '').strip()
        email = (guest.get('email') or thread_emails.get(b.get('thread_uid')) or '').strip()
        checkin = _date_text(b.get('arrival'))
        checkout = _date_text(b.get('departure'))
        label = name or f"booking {b.get('id')}"

        departure_day = _day(b.get('departure'))
        if departure_day and departure_day < today:
            continue  # stay already over

        messages = messages_by_thread.get(b.get('thread_uid'), [])
        plate, vehicle = '', ''
        for text in messages:
            found = find_plates(text)
            if found:
                plate = found[-1]
            v = find_vehicle(text)
            if v:
                vehicle = v

        if not plate:
            skipped.append((label, 'no registration in messages'))
            continue
        # Registration only: the Apps Script needs a non-empty Vehicle column to start.
        vehicle = vehicle or NOT_PROVIDED
        if not (name and checkin and checkout):
            skipped.append((label, 'missing name or dates'))
            continue
        # Columns A-M: A-F data, G-L left for the Apps Script, M = Notes.
        note = '' if email else NO_EMAIL_NOTE
        rows.append({'booking_id': b.get('id'),
                     'row': [name, email, plate, vehicle, checkin, checkout,
                             '', '', '', '', '', '', note]})
    return rows, skipped


def drop_duplicates(candidates, existing_rows):
    """Remove candidates already in the sheet (by email+check-in, or reg+check-in).

    A blank email never dedupes on email - only the registration matches.
    """
    seen_email = set()
    seen_reg = set()
    for r in existing_rows:
        r = list(r) + [''] * 6
        if str(r[1]).strip():
            seen_email.add((str(r[1]).strip().lower(), str(r[4]).strip()))
        seen_reg.add((str(r[2]).replace(' ', '').upper(), str(r[4]).strip()))
    fresh, dupes = [], []
    for c in candidates:
        name, email, plate = c['row'][0], c['row'][1], c['row'][2]
        checkin = c['row'][4]
        key_e = (email.lower(), checkin) if email else None
        key_r = (plate, checkin)
        if key_r in seen_reg or (key_e and key_e in seen_email):
            dupes.append(c)
        else:
            fresh.append(c)
            if key_e:
                seen_email.add(key_e)
            seen_reg.add(key_r)
    return fresh, dupes


def mask(plate):
    return ('*' * max(0, len(plate) - 3)) + plate[-3:]


def fetch_lodgify(api_key, now):
    """Booked stays (current and upcoming) plus their guest messages.

    Returns (bookings, messages_by_thread, thread_emails).
    """
    raw = lg._fetch_bookings(api_key, 'Upcoming') + lg._fetch_bookings(api_key, 'Current')
    seen, bookings = set(), []
    for b in raw:
        if not isinstance(b, dict) or b.get('id') in seen:
            continue
        seen.add(b.get('id'))
        if str(b.get('status', '')).lower() == 'booked':
            bookings.append(b)

    messages_by_thread = {}
    thread_emails = {}
    for b in bookings:
        uid = b.get('thread_uid')
        if not uid:
            continue
        try:
            data = lg._request(api_key, f'/v2/messaging/{uid}')
        except Exception:
            continue
        threads = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        texts = []
        for t in threads:
            if t.get('guest_email'):
                thread_emails[uid] = str(t['guest_email']).strip()
            for m in (t.get('messages') or []):
                if str(m.get('type', '')).lower() == 'renter':
                    texts.append(plain_text(m.get('message')))
        messages_by_thread[uid] = texts
    return bookings, messages_by_thread, thread_emails


def sheets_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds, cache_discovery=False)


def read_existing(svc):
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f"'{SHEET_TAB}'!A2:F").execute()
    return result.get('values', [])


def append_rows(svc, rows):
    return svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID, range=f"'{SHEET_TAB}'!A:M",
        valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
        body={'values': rows}).execute()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='append rows to the sheet (default: dry run)')
    ap.add_argument('--json', action='store_true', help='print machine-readable output')
    args = ap.parse_args()

    api_key = os.environ.get('LODGIFY_API_KEY', '').strip()
    if not api_key:
        sys.exit('LODGIFY_API_KEY is not set')

    now = datetime.now(timezone.utc)
    today = now.astimezone(TIMEZONE).date()

    bookings, messages, thread_emails = fetch_lodgify(api_key, now)
    candidates, skipped = build_candidates(bookings, messages, today, thread_emails)

    svc = sheets_service()
    existing = read_existing(svc)
    fresh, dupes = drop_duplicates(candidates, existing)

    report = {
        'mode': 'write' if args.write else 'dry-run',
        'bookingsBooked': len(bookings),
        'toAdd': [{'name': c['row'][0], 'reg': mask(c['row'][2]), 'vehicle': c['row'][3],
                   'checkin': c['row'][4], 'checkout': c['row'][5],
                   'noEmail': not c['row'][1]} for c in fresh],
        'alreadyInSheet': len(dupes),
        'skipped': skipped,
    }

    if args.write and fresh:
        append_rows(svc, [c['row'] for c in fresh])
        report['written'] = len(fresh)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Mode: {report['mode']} | Booked stays: {report['bookingsBooked']} | "
              f"to add: {len(fresh)} | already in sheet: {len(dupes)} | skipped: {len(skipped)}")
        for r in report['toAdd']:
            flag = '  [no email - note added]' if r['noEmail'] else ''
            print(f"  + {r['name']} | {r['reg']} | {r['vehicle']} | "
                  f"{r['checkin']} -> {r['checkout']}{flag}")
        for label, why in skipped:
            print(f"  - {label}: {why}")


if __name__ == '__main__':
    main()
