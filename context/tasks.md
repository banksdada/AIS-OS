# Tasks

The single task list. Maintained by `@executive-assistant`. Nothing else belongs here.

Entry format: `- [ ] <task> — owner, due YYYY-MM-DD, source`

Close items by marking `[x]` with the date — never delete history.

## Open

- [ ] Set `lodgify-reply-drafter` schedule to daily 07:30 Europe/London — Banks, due 2026-10-21, source: setup 2026-10-20
- [ ] Share the permits sheet (`1ZAQhPWOShrp0xX-Em4_wZl4reKK48HmLt0CyFIlF5uk`) with a person, remove "anyone with link" — Banks, due 2026-10-22, source: audit 2026-10
- [ ] Enable Google Calendar API in GCP project 266063022919 — Banks, source: connections.md (blocks meeting prep)
- [ ] Enable HumHub REST API in admin panel, then verify post-redeploy — Banks, source: connections.md
- [ ] Fill aios-intake.md Q2 Sample 2 voice sample — Banks, source: /onboard
- [ ] Build dashboard parking-permits panel — Banks/DI, source: audit 2026-10
- [ ] Restart opencode, then authorise the TidyCal MCP in-browser and confirm the account is Pro — Banks, due 2026-10-21, source: mcp setup 2026-10-20
- [ ] EA-only week: route everything through @executive-assistant, no ChatGPT or custom GPTs — Banks, due 2026-10-28, source: skills backlog 2026-10-20
- [ ] Rebrand Sorted to the new domain — code-side defaults updated; Coolify/DNS/Postal/redirect outstanding — Banks, source: rebrand plan 2026-10-21
- [ ] Tunisia hotel deal: follow up with the LinkedIn connection, introduce them to the Skool property group, agree a finders' fee in writing before the intro — Banks, due 2026-10-24, source: LinkedIn 2026-10-21
- [ ] Share the Virgin Active "Master Data Management" doc with aios-bot@aios-credentials.iam.gserviceaccount.com (Viewer), then scan it for software/application keywords to build a tools-worked-with list for the CV — Banks, source: CV/job hunt 2026-10-21
- [ ] Fix Webawesome start date to April 2022 in the Drive CV originals (CMS, legacyR, util variants say April 2024) and fix the NHS Professionals dates in SFCRM — Banks, due 2026-10-23, source: projects/job-search/DATE-FIXES.md
- [ ] Reply to Manny with the HMRC-based CV for the London/Surrey BA contract — Banks, due 2026-10-22 (before 17:00), source: job search 2026-10-22
- [ ] Apply to TTC Tech Senior Business Analyst using the legacyR-based CV, stating the travel/cruise gap plainly — Banks, source: job search 2026-10-22
- [ ] Decide Laravel vs Django for the bankoledada.co.uk rebuild, then confirm hosting (Coolify?) and design direction — Banks, source: docs/ideas/bankoledada-rebuild-plan.md
- [ ] Authorise Drive write access: open the consent URL (already copied to clipboard, regenerate with `python3 scripts/gdrive-authorize.py`), then run `python3 scripts/gdrive-authorize.py <CODE>` — Banks, source: 2026-10-22
- [ ] Post LinkedIn Day 2 (MBA — TEACH) — copy from `projects/linkedin-content/daily/day-02-2026-10-22-mba-teach.txt` or the Drive `linkedin-posts` folder — Banks, due 2026-10-22, source: morning coffee 2026-10-22
- [ ] Sweet Soul Guest Inn — Phase 1: Django rooms + bookings models & API (incl. ExternalBooking for Airbnb iCal sync) — pending
- [ ] Sweet Soul Guest Inn — Phase 2: Embed React design-system bundle into Django, wire to API — pending
- [ ] Sweet Soul Guest Inn — Phase 3: Deploy to Coolify, point domain — pending
- [ ] Sweet Soul Guest Inn — Phase 4: Swap placeholder content for real room data/photos — pending
- [ ] Sweet Soul Guest Inn — Phase 5: iCal sync (export + import) for Airbnb availability — pending
- [ ] Production Coolify env: `APP_URL`, Postal SMTP, `MAIL_FROM_ADDRESS`; verify live magic-link delivery — Banks, source: 2026-10-27; Postal confirmed working 2026-10-27
- [ ] Create `legal@`/`privacy@` forwarders and fix SPF duplicate/DMARC — Banks, source: 2026-10-27; site already renders both addresses from `config/legal.php`

## Waiting on someone else

- [ ] Permit wording: FAQ says "no permit", flow collects registrations — Banks deferred, source: 2026-10-20
- [ ] Two Overcomers FAQ files are identical; Modern Digbeth FAQ holds Cutlass Court content — Banks deferred, source: 2026-10-20

## Parked

- [ ] Persist PyRunner event history across redeploys (container FS, not volume-mounted) — deferred, source: 2026-10-20

## Done

- [x] Fix FAQ matcher for `Stylish City Living` → Cutlass Court — 2026-10-20
- [x] Closing-sign-off detection in `thread_attention` — 2026-10-20
- [x] Lodgify reply-draft digest live (4/4 drafted) — 2026-10-20
- [x] Cleaner departure notices dropped — client no longer uses cleaner services — 2026-10-21
- [x] Newsletter re-permission 40/40 delivered — 2026-10
- [x] Buy nowsorted.co.uk — 2026-10-23
- [x] Push AIOS homepage section to GitHub — 2026-10-27
- [x] Replied to all Lodgify guest messages — 2026-10-27; 0 awaiting reply at 07:51 UTC
- [x] Review all emails on all pages of the website and change to the provided email — 2026-10-27; legal pages use `config/legal.php` (`legal@`/`privacy@nowsorted.co.uk`); `LegalEmailTest` added
- [x] SEO technical foundation: robots.txt, sitemap.xml, OG/Twitter meta — 2026-10-27; sitemap route fixed, OG image added, microsite meta added
- [x] Re-ran connection check — 2026-10-27; 4/7 live. Calendar needs calendar shared, HumHub needs REST API enabled, TidyCal needs re-auth
- [x] Removed out-of-scope Resend mail integration — 2026-10-27; mail is Postal/SMTP only, `PROJECT-STATUS.md` updated
- [x] Removed legacy WhatsApp automation from sorted-app — 2026-10-27; webhook, handler, services, model, migration, OAuth channel, onboarding requirement and public copy removed; Instagram/LinkedIn/GBP posting preserved; residual refs cleaned and committed in `5cd8f1f`; full suite 79 tests/287 assertions pass (PHP 8.5 vendor deprecation flags only)
- [x] Remove inert lead AI-reply fields and dashboard reply stats before re-enabling social — 2026-10-27; columns dropped in `ab09218`, lead attention follows status, reply metrics replaced with lead/status metrics
