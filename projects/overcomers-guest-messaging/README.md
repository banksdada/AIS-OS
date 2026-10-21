# Overcomers guest messaging

**Status:** active
**Owner:** Banks / Overcomers

Daily Lodgify reply drafts for two properties — Cutlass Court (`Stylish City Living with free 2-Bay Secure parking`) and Modern Digbeth Stay.

## What runs

- `scripts/pyrunner/lodgify-reply-drafter.py` — read-only Lodgify v2 fetch, AI-drafted plain-text replies, emailed digest. Schedule: daily 07:30 Europe/London. Live 2026-10-20, 4/4 drafts.
- `scripts/pyrunner/overcomers-cleaner-notices.py` — **shelved 2026-10-21.** The client stopped using cleaner services, so this is committed but unscheduled.

## Rules

- Never send on-platform. Banks pastes into Lodgify. Lodgify v2 has no send endpoint, and that is deliberate.
- Plain text only in guest messages — no links, phone, email, emoji, images or HTML (Vrbo forbids them).
- Lodgify auto-sends booking confirmation, check-in info and house rules. Keep drafts minimal; the FAQ answers specific questions only.

## Open

- Permit wording conflict: FAQ says no permit, the flow collects registrations.
- Both FAQ files are currently identical; `references/overcomers-faq-modern-digbeth-stay.md` holds Cutlass Court content.
