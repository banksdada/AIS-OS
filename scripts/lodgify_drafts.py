"""Collect Lodgify threads that need a reply into a draft packet.

Read-only against Lodgify (X-ApiKey, v2). Reuses the dashboard panel's
booking/thread fetching, finds threads where the guest spoke last, and
writes a per-thread packet — full conversation + the matching Overcomers
property FAQ — to data/lodgify-draft-packet.json and stdout.

The packet is the drafting context; replies are drafted from it (in a
session or later via an AI key) and pasted into Lodgify by the owner.
Nothing is ever sent to the guest automatically.

Usage:
    python3 scripts/lodgify_drafts.py            # packet for all needs-reply threads
    python3 scripts/lodgify_drafts.py --unanswered  # only waiting >= LODGIFY_UNANSWERED_MINUTES
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dashboard import lodgify  # noqa: E402  (needs scripts/ on sys.path first)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, 'data', 'lodgify-draft-packet.json')


def _load_dotenv(path):
    """Minimal .env loader; never overrides the real environment."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(os.path.join(REPO_ROOT, '.env'))

# Property name (from Lodgify) -> extracted FAQ markdown, slug-matched.
FAQ_MAP = {
    'cutlass': 'references/overcomers-faq-cutlass-court.md',
    'digbeth': 'references/overcomers-faq-modern-digbeth-stay.md',
}


def faq_for(property_name):
    slug = (property_name or '').lower()
    for key, path in FAQ_MAP.items():
        if key in slug:
            full = os.path.join(REPO_ROOT, path)
            if os.path.exists(full):
                return open(full, encoding='utf-8').read()
    return None


def message_text(msg):
    plain = lodgify.strip_html(msg.get('message') or '')
    return plain


def thread_conversation(thread):
    """Full thread as ordered text blocks."""
    blocks = []
    for m in sorted(thread.get('messages') or [],
                    key=lambda x: lodgify._parse_dt(x.get('date_created')) or datetime.min.replace(tzinfo=timezone.utc)):
        who = 'GUEST' if str(m.get('type', '')).lower() == 'renter' else 'HOST'
        at = lodgify._parse_dt(m.get('date_created'))
        blocks.append({
            'when': at.isoformat(timespec='seconds') if at else '',
            'who': who,
            'route': m.get('route') or '',
            'text': message_text(m),
        })
    return blocks


def build_packet(unanswered_only=False):
    api_key = os.environ.get('LODGIFY_API_KEY', '').strip()
    if not api_key:
        raise SystemExit('error: LODGIFY_API_KEY not set (.env)')

    panel = lodgify.fetch_panel(api_key)
    threads = [m for m in panel.get('messages', []) if m.get('needsReply')]
    if unanswered_only:
        threads = [m for m in threads if m.get('unanswered')]

    packet = []
    for summary in threads:
        uid = summary.get('threadUid')
        if not uid:
            continue
        try:
            data = lodgify._request(api_key, f'/v2/messaging/{uid}')
        except Exception as exc:
            print(f'  warn: could not fetch thread {uid}: {exc}', file=sys.stderr)
            continue
        raw = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
        thread = next((t for t in raw if isinstance(t, dict)), None)
        if not thread:
            continue
        prop = summary.get('property', '')
        packet.append({
            'threadUid': uid,
            'guest': summary.get('guest') or thread.get('guest_name') or '',
            'guestEmail': thread.get('guest_email') or '',
            'property': prop,
            'waitingMinutes': summary.get('waitingMinutes'),
            'unanswered': bool(summary.get('unanswered')),
            'urgent': summary.get('urgent') or [],
            'route': summary.get('route') or '',
            'conversation': thread_conversation(thread),
            'faq': faq_for(prop),
            'faqMatched': faq_for(prop) is not None,
        })
    return panel, packet


def main():
    parser = argparse.ArgumentParser(description='Build a drafting packet for Lodgify threads needing a reply.')
    parser.add_argument('--unanswered', action='store_true',
                        help='Only threads waiting >= LODGIFY_UNANSWERED_MINUTES.')
    args = parser.parse_args()

    panel, packet = build_packet(unanswered_only=args.unanswered)

    payload = {
        'generatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'counts': panel.get('counts', {}),
        'threads': packet,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    print(f"needs-reply threads in packet: {len(packet)} (panel: {panel.get('counts', {})})")
    for p in packet:
        tags = ','.join(p['urgent']) or '-'
        faq = 'FAQ ok' if p['faqMatched'] else 'NO FAQ MATCH'
        last = p['conversation'][-1]['text'][:100] if p['conversation'] else '(no messages)'
        print(f"  - {p['guest']} @ {p['property']} | waiting {p['waitingMinutes']}m | "
              f"urgent: {tags} | {faq}")
        print(f"    last: {last}")
    print(f'\npacket -> {OUT_PATH}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
