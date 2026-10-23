# Hosting Health Report — Implementation Plan

**Date:** 2026-10-23 · **Status:** planned · **Supersedes:** the "what the report contains" section in `docs/ideas/hosting-health-report-scope.md`

## Design constraint (drives everything)

The existing reminder script is **stdlib-only** — no `requests`, no `pip install` — because PyRunner can't be relied on to have packages. The health-check module must follow the same rule. That means: `urllib` for HTTP, stdlib `ssl` for cert checks, no external monitoring API.

## Architecture

Add one new module, `health_check.py`, imported by `hosting-renewal-reminders.py`. It produces a `HealthReport` dataclass per client; the reminder script attaches it to the renewal email.

```
hosting-renewal-reminders.py
  └── health_check.py          (NEW)
        ├── check_uptime()     — HTTP probe, recent history
        ├── check_ssl()        — cert expiry, issuer, chain
        ├── check_wordpress()  — core/plugin updates, posts in year
        ├── check_backups()    — last backup date (best-effort)
        └── render_report()    → HTML + PDF
```

## Data sources, per check

**1. Uptime & availability**
Probe `GET https://<site>/` every run (cheap, and it's the only uptime signal available without a monitoring service — ecoWebhosting offers no uptime monitoring). Keep a rolling 30-day history in the sheet (`Uptime 30d` column: `up 30/30`) so the annual report isn't based on one day. HTTP status + response time. Mark "not verified" honestly if history is thin.

**2. Security**
- WordPress: `GET /wp-json/wp/v2/posts?per_page=1` plus the core/version endpoint. Check `core_update_available`, plugin update status via the REST API (or the `wp-json/wp/v2/plugins` route if the WP version supports it). Flag any plugin/core behind.
- SSL: connect with `ssl` module, read the cert, report expiry date and days remaining. This is stdlib, no deps — and cert expiry is a real renewal risk, so it earns its place.
- Note honestly: this is a *surface* check, not a penetration test. Say so in the report.

**3. Backups**
Best-effort. ecoWebhosting runs **JetBackup** (automated daily or weekly depending on plan, retained for a defined period, restorable via the control panel) — but exposes **no API** to read the last backup date. So the report can only state that automated backups are configured per the plan, and mark it *not independently verified*. **Never claim a restore was tested unless it was.**

**4. Performance**
Measure `GET /` response time over the probe. Flag slow (>3s). No synthetic testing — say plainly this is a single sample, not a lab measurement.

**5. What changed this year**
WordPress REST API: count posts published in the last 365 days, last post date. This is the honest "we looked after your site" evidence — and it's genuinely useful to a client who thinks their site is static and forgotten.

**6. Recommendations**
2–3 plain-language items generated from the findings, e.g.:
- "Your SSL certificate expires in 42 days — renew it before it lapses."
- "3 plugins are behind on updates."
- "You published 4 posts this year — a regular blog keeps the site alive for search."

## Report format

HTML body (inline, no CSS framework — keeps it email-safe) **plus** a PDF attachment. The email leads with the report, not the invoice:

> "Here's your annual website health report for [site]. It shows your site was up 30/30 days this month, your SSL is valid, and backups are configured. Here's what we did for it this year: [summary]. Your renewal of £55 is due [date]. The full report is attached. Reply with any questions."

## Sheet columns to add

| Column | Written by |
|---|---|
| `Health Report Sent` | date when report emailed |
| `Report Date` | the report's as-of date |
| `Uptime 30d` | `up 30/30` rolling history |

## Implementation order

1. **`check_wordpress()`** — the richest data source, and the one that proves "we maintained your site". Test on 2–3 real client sites.
2. **`check_ssl()`** — stdlib, no deps, immediate value (cert expiry is a real renewal risk).
3. **`check_uptime()` + rolling history** — needs the sheet columns first.
4. **`render_report()` + email rewrite** — wire it into `build_email()`.
5. **Dry-run on 2–3 clients**, review the actual output with Banks, fix, then batch.

## Risks

- **A wrong report is worse than no report.** Step 5 is not optional. Read the output before it goes to 15 clients.
- **PyRunner env.** The script already runs there. The new module must stay stdlib-only — `requests` is out.
- **Honesty over polish.** Where a check can't be verified, the report says so. A client who learns their backup isn't real will never trust a report again.
- **ecoWebhosting has no API**, so every data point comes from probing the live site. That's slower and less complete than a host API — say so plainly in the report rather than implying a deeper check.

## Next step

Say the word and I'll write the actual `health_check.py` code.