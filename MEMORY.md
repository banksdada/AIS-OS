# Memory — PyRunner fleet reporting + Parking Permits + AI OS fixes

Last updated: 2026-10-19

## What was built

- **PyRunner scripts repaired with inlined `report()`** (all in `scripts/pyrunner/`, all compile-checked, each reports `started` → `ok`/`idle`/`failed` to `https://aios.webawesome.co.uk/webhook/pyrunner`):
  - `blog-drafter.py` — paste damage fixed; **user confirmed working**
  - `content-repurposer.py` — reports started/ok/failed; deliberately no idle events
  - `bhs-blog-poster.py` — Best Homes Support poster; reports started/failed/idle/ok
  - `mentoringba-blog-poster.py` — MentoringBA copy; separate WP secrets + `mentoringba_blog_processed` datastore
  - `lead-reply-drafter.py` — webhook-triggered web enquiry drafter; AI failure still posts the hand-reply fallback draft and reports `failed`
  - `hosting-renewal-reminders.py` — daily job; one summary event per run (counts sent/failed), no per-client flooding
  - `rota-health-check.py` — RotaMate health checker; `fail()` reports; ok message carries score/summary
- **Parking Permits flow**: extractor `scripts/parking_permits.py` + `tests/test_parking_permits.py` (16 tests); full replacement Apps Script `scripts/parking-permits-apps-script.gs` (permit length in days, notes column, no-email rows, guest confirmation commented out for testing, new `CONFIG.WEB_APP_URL`); sheet `1ZAQhPWOShrp0xX-Em4_wZl4reKK48HmLt0CyFIlF5uk` tab Guests rows 10–13 live (Status Sent; L column = inclusive-days formula), rows 5–9 = junk test data
- **HumHub fix** in `scripts/verify-connections.py` (browser UA + retry + WAF message) — commit `82a6434`
- **Dashboard**: Lodgify panel + PyRunner events panel (`scripts/dashboard/pyrunner_events.py` HMAC intake, serve.py POST routes, index.html) — commit `975ba28`

## Decisions made

- Permit length = **inclusive calendar days** (`F−E+1`), no maximum; shown in sheet + processor email
- No guest confirmation emails during testing (guest send commented out in Apps Script); `TEST_MODE: true`, manager `ademolajoyce@yahoo.co.uk`, shared inbox `bankoledada@gmail.com`
- Guests with no email still get sheet rows, note in column M asking for one via Lodgify
- Vehicle column = `Not provided` when make/model absent; registration only extracted
- Lodgify webhooks deferred (no signature scheme); polling via bookings API instead
- **PyRunner pattern (locked in)**: workspace-wide secrets; scripts run standalone → `report()` is inlined in every script, never imported; agent name = script name; scheduled jobs emit ONE summary event per run to avoid dashboard flooding
- `hosting-renewal-reminders` smoke run posted 2 real events (started + failed-setup) to the live dashboard — test artifact, ignore

## Problems solved

- PyRunner events were missing because `pyrunner.webawesome.co.uk` serves Traefik's default cert (TLS-dead) — always use `aios.webawesome.co.uk`
- PyRunner cannot import sibling modules (`aios_report.py` failed) — hence the inlined report() pattern
- HumHub 403 → browser User-Agent (needs Coolify redeploy to take effect)

## Current state

- User closed with "nice, all done" — pasting/deploy steps treated as complete
- Pushed: `975ba28`, `82a6434`. **Uncommitted working tree**: parking extractor, tests, Apps Script replacement, all 7 PyRunner scripts, dashboard pieces — user never asked to commit
- Server NOT redeployed at last check (live HumHub still 403, 6/7) — Coolify builds from GitHub so `82a6434` needs a redeploy trigger
- PyRunner event history lives on container FS (`data/pyrunner-events.json`, not volume-mounted) — lost on redeploy

## Next session starts with

Nothing forced. If resuming: run `python3 scripts/verify-connections.py` (expect HumHub 7/7 after redeploy), then optional wins — parking-permits dashboard panel (masked regs, last 3 chars), clear sheet junk rows 5–9, tighten the sheet's "anyone with link" sharing, commit the working tree if durability in git is wanted.

## Open questions

- Did the Coolify redeploy happen? (HumHub fix + stale scheduled check)
- Is the Parking Permits sheet still shared "anyone with the link"? (guest car data readable to anyone with the URL — flagged, unresolved)
- Commit the uncommitted work?

---

## Session memory hooks (from earlier sessions)

- [WordPress API credentials](memory-wordpress-api.md)
- [Newsletter project](memory-newsletter-project.md)
