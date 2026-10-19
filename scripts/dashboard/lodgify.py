"""Read-only Lodgify panel data: upcoming arrivals and guest messages.

Polls Lodgify's Public API v2 (auth: X-ApiKey header) for bookings in the
Upcoming and Current stay filters, then reads each booking's messaging
thread. The panel is deliberately read-only: it flags what needs attention
(check-in, access codes, problems, unanswered guest messages) but never
sends replies — the owner replies in Lodgify, so guests always get a
reviewed human response.

Results are cached for CACHE_SECONDS so dashboard refreshes do not hammer
the API (Lodgify allows 750 requests/minute on v2). Set LODGIFY_API_KEY in
.env or the environment. Optional: LODGIFY_UNANSWERED_MINUTES (default 120)
and LODGIFY_ARRIVAL_HOURS (default 48).
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_PATH = os.path.join(REPO_ROOT, 'data', 'lodgify-cache.json')

API_BASE = 'https://api.lodgify.com'
CACHE_SECONDS = 300
MAX_THREAD_FETCHES = 25
DEFAULT_UNANSWERED_MINUTES = 120
DEFAULT_ARRIVAL_HOURS = 48

URGENT_PATTERNS = [
    ('check-in', re.compile(
        r'check[\s-]?in|check[\s-]?out|arriv|late|early|self[\s-]?service|key[\s-]?collect', re.I)),
    ('access', re.compile(
        r'access\s*code|key\s*code|keycode|pin\s*code|door\s*code|gate\s*code|lock\s*code|'
        r'lockbox|key\s*box|keypad|can\'?t\s*get\s*(in|in\s*to)|door\s*(code|won\'?t|not)', re.I)),
    ('problem', re.compile(
        r'problem|issue|broken|not\s*work|fault|emergency|urgent|leak|flood|smoke|'
        r'no\s*(hot\s*)?water|heating|boiler|wifi|internet\s*(down|not)|locked\s*out', re.I)),
]


def _env_int(name, default):
    try:
        return int(os.environ.get(name, '') or default)
    except ValueError:
        return default


def _request(api_key, path, params=None):
    """GET an Lodgify endpoint. Returns parsed JSON. Raises on failure."""
    url = API_BASE + path
    if params:
        from urllib.parse import urlencode
        url += '?' + urlencode(params)
    try:
        import requests
        resp = requests.get(url, headers={
            'X-ApiKey': api_key,
            'Accept': 'application/json',
            'User-Agent': 'AI-OS-Dashboard/1.0',
        }, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except ImportError:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'X-ApiKey': api_key,
            'Accept': 'application/json',
            'User-Agent': 'AI-OS-Dashboard/1.0',
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())


def _parse_dt(value):
    """Parse an Lodgify date/datetime string. Returns None if unparseable."""
    if not value:
        return None
    text = str(value).strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
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


def strip_html(text):
    """First ~140 plain-text chars of an HTML message body."""
    if not text:
        return ''
    plain = re.sub(r'<[^>]+>', ' ', str(text))
    plain = re.sub(r'&nbsp;?', ' ', plain)
    plain = re.sub(r'&amp;', '&', plain)
    plain = re.sub(r'\s+', ' ', plain).strip()
    return plain[:140]


def classify_urgent(text):
    """Tags for a guest message: check-in, access, problem."""
    if not text:
        return []
    return [tag for tag, pattern in URGENT_PATTERNS if pattern.search(str(text))]


def thread_attention(thread, now=None, unanswered_minutes=DEFAULT_UNANSWERED_MINUTES):
    """Summarise one messaging thread for the panel.

    A thread needs attention when the newest message is from the guest
    (Renter) and nobody has replied. Urgent tags come from the newest guest
    message text. Returns None for threads with no messages.
    """
    messages = thread.get('messages') or []
    if not isinstance(messages, list) or not messages:
        return None
    now = now or datetime.now(timezone.utc)
    renter_msgs = [m for m in messages if str(m.get('type', '')).lower() == 'renter']
    if not renter_msgs:
        return None
    last_guest = max(renter_msgs, key=lambda m: _parse_dt(m.get('date_created')) or datetime.min.replace(tzinfo=timezone.utc))
    guest_at = _parse_dt(last_guest.get('date_created'))
    owner_replied = any(
        str(m.get('type', '')).lower() == 'owner'
        and (_parse_dt(m.get('date_created')) or datetime.min.replace(tzinfo=timezone.utc))
        >= (guest_at or datetime.min.replace(tzinfo=timezone.utc))
        for m in messages
    )
    waiting = None
    if guest_at:
        waiting = max(0, int((now - guest_at).total_seconds() // 60))
    body = strip_html(last_guest.get('message'))
    urgent = classify_urgent(last_guest.get('message')) if not owner_replied else []
    unanswered = (not owner_replied) and waiting is not None and waiting >= unanswered_minutes
    return {
        'threadUid': thread.get('thread_uid', ''),
        'guest': thread.get('guest_name') or '',
        'lastGuestMessageAt': guest_at.isoformat(timespec='seconds') if guest_at else None,
        'waitingMinutes': waiting,
        'unanswered': unanswered,
        'needsReply': not owner_replied,
        'urgent': urgent,
        'snippet': body,
        'route': last_guest.get('route') or '',
        'isRead': bool(thread.get('is_read')),
        'isClosed': bool(thread.get('is_closed')),
    }


def _fetch_bookings(api_key, stay_filter):
    data = _request(api_key, '/v2/reservations/bookings', {
        'stayFilter': stay_filter, 'page': 1, 'size': 50, 'includeCount': 'true'})
    if isinstance(data, dict):
        return data.get('items') or []
    return data if isinstance(data, list) else []


def _property_names(api_key):
    """Map property_id -> name. Tolerates failure (names fall back to ids)."""
    try:
        data = _request(api_key, '/v2/properties')
    except Exception:
        return {}
    rows = data if isinstance(data, list) else (data.get('items') if isinstance(data, dict) else []) or []
    names = {}
    for row in rows:
        if isinstance(row, dict) and row.get('id') is not None:
            names[row['id']] = row.get('name') or row.get('header') or f"Property {row['id']}"
    return names


def _arrival_window_ok(arrival_dt, now, arrival_hours):
    """True when the booking arrives within the prep window.

    Date-only arrivals compare by calendar day so a same-day check-in is
    never dropped just because its midnight timestamp is already past.
    """
    if not arrival_dt:
        return False
    end = now + timedelta(hours=arrival_hours)
    if arrival_dt.hour or arrival_dt.minute or arrival_dt.second:
        return now <= arrival_dt <= end
    today = now.astimezone(timezone.utc).date()
    return today <= arrival_dt.date() <= end.date()


def _summarise_booking(booking, names):
    arrival_dt = _parse_dt(booking.get('arrival'))
    departure_dt = _parse_dt(booking.get('departure'))
    guest = booking.get('guest') or {}
    prop_id = booking.get('property_id')
    return {
        'id': booking.get('id'),
        'guest': guest.get('name') or '(no name)',
        'property': names.get(prop_id, f'Property {prop_id}' if prop_id else 'Unknown property'),
        'arrival': booking.get('arrival'),
        'departure': booking.get('departure'),
        'arrivalAt': arrival_dt.isoformat(timespec='seconds') if arrival_dt else None,
        'departureAt': departure_dt.isoformat(timespec='seconds') if departure_dt else None,
        'status': booking.get('status') or '',
        'source': booking.get('source') or '',
        'isNew': bool(booking.get('is_new')),
        'threadUid': booking.get('thread_uid') or '',
    }


def fetch_panel(api_key, now=None):
    """Fetch arrivals + message attention data. Raises on API failure."""
    now = now or datetime.now(timezone.utc)
    unanswered_minutes = _env_int('LODGIFY_UNANSWERED_MINUTES', DEFAULT_UNANSWERED_MINUTES)
    arrival_hours = _env_int('LODGIFY_ARRIVAL_HOURS', DEFAULT_ARRIVAL_HOURS)

    upcoming = _fetch_bookings(api_key, 'Upcoming')
    current = _fetch_bookings(api_key, 'Current')
    by_id = {}
    for b in upcoming + current:
        if isinstance(b, dict) and b.get('id') is not None:
            by_id[b['id']] = b
    bookings = list(by_id.values())

    names = _property_names(api_key)
    arrivals = []
    for b in bookings:
        summary = _summarise_booking(b, names)
        if _arrival_window_ok(_parse_dt(b.get('arrival')), now, arrival_hours):
            arrivals.append(summary)
    arrivals.sort(key=lambda a: a.get('arrivalAt') or 'zzz')

    messages = []
    fetched = 0
    for b in bookings:
        thread_uid = b.get('thread_uid')
        if not thread_uid or fetched >= MAX_THREAD_FETCHES:
            continue
        fetched += 1
        try:
            data = _request(api_key, f'/v2/messaging/{thread_uid}')
        except Exception:
            continue
        threads = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        for thread in threads:
            if not isinstance(thread, dict):
                continue
            attention = thread_attention(thread, now=now, unanswered_minutes=unanswered_minutes)
            if attention is None:
                continue
            attention['bookingId'] = b.get('id')
            attention['property'] = names.get(b.get('property_id'), f"Property {b.get('property_id')}")
            messages.append(attention)

    messages.sort(key=lambda m: (
        not m.get('urgent'),
        not m.get('unanswered'),
        -(m.get('waitingMinutes') or 0),
    ))
    counts = {
        'arrivals': len(arrivals),
        'needsReply': sum(1 for m in messages if m.get('needsReply')),
        'unanswered': sum(1 for m in messages if m.get('unanswered')),
        'urgent': sum(1 for m in messages if m.get('urgent')),
    }
    return {'arrivals': arrivals, 'messages': messages, 'counts': counts,
            'unansweredMinutes': unanswered_minutes, 'arrivalHours': arrival_hours}


def _cache_read():
    try:
        with open(CACHE_PATH) as f:
            cached = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(cached, dict) or 'savedAt' not in cached or 'panel' not in cached:
        return None
    return cached


def _cache_write(panel):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    payload = {'savedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'panel': panel}
    tmp = CACHE_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(payload, f)
    os.replace(tmp, CACHE_PATH)


def dashboard_data():
    """Dashboard payload for the Lodgify panel (cached, read-only)."""
    api_key = os.environ.get('LODGIFY_API_KEY', '').strip()
    if not api_key:
        return {'configured': False, 'connected': False, 'arrivals': [], 'messages': [],
                'counts': {'arrivals': 0, 'needsReply': 0, 'unanswered': 0, 'urgent': 0},
                'detail': 'Set LODGIFY_API_KEY to connect Lodgify'}

    cached = _cache_read()
    if cached:
        try:
            saved = _parse_dt(cached['savedAt'])
            if saved and (datetime.now(timezone.utc) - saved).total_seconds() < CACHE_SECONDS:
                return dict(cached['panel'], configured=True, connected=True,
                            cachedAt=cached['savedAt'], source='cache')
        except Exception:
            pass

    try:
        panel = fetch_panel(api_key)
    except Exception as e:
        if cached and cached.get('panel'):
            return dict(cached['panel'], configured=True, connected=True,
                        cachedAt=cached['savedAt'], source='cache (live fetch failed)',
                        detail=f'live fetch failed: {type(e).__name__}')
        return {'configured': True, 'connected': False, 'arrivals': [], 'messages': [],
                'counts': {'arrivals': 0, 'needsReply': 0, 'unanswered': 0, 'urgent': 0},
                'detail': f'Lodgify connection error: {type(e).__name__}'}

    _cache_write(panel)
    return dict(panel, configured=True, connected=True,
                cachedAt=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                source='live')
