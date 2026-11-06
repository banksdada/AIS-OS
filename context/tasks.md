# Tasks

The single task list. Maintained by `@executive-assistant`. Nothing else belongs here.

Entry format: `- [ ] <task> — owner, due YYYY-MM-DD, source`

Close items by marking `[x]` with the date — never delete history.

## Open

- [ ] Apply for the MPLC Business Transformation Consultant role via Steve's work email (round-2 interview likely end of Nov): CV + one-paragraph pitch; attach `~/Desktop/MPLC-AI-Audit/audit-onepager.pdf` framed as "a weekend discovery exercise — corrections welcome"; subject line plain, no AI flourish — Banks, due 2026-11-07, source: interview done 2026-11-06
- [ ] AI audit tool shipped: `scripts/ai-audit.py` + `/ai-audit` skill + tests (10) + break-it 8/8 CAUGHT; MPLC audit PDFs on Desktop — 2026-11-06

- [ ] MOCK RUN Thu 2026-11-05 10:00 — EA plays Steve: his 4 asks + salary + "why permanent". Use `demo-answers.md` as benchmark; run the live transcriber during it to double as the pre-Friday audio test. Demo answers ready 2026-11-02 — Banks/EA, due 2026-11-05, source: LinkedIn/email 2026-11-02
- [ ] Interview practice sheet built locally (SA can't create Drive files): drag `projects/job-search/interviews/simpro-2026-11-06/mplc-practice-sheet.xlsx` into Drive to open it as a Google Sheet — and run `python3 scripts/gdrive-authorize.py` to restore write access so future sheets are automatic — Banks, due 2026-11-04, source: interview prep 2026-11-03
- [ ] Rehearsal-test the live transcriber with real speaker audio BEFORE Friday (`~/.venvs/interview/bin/python scripts/interview-transcribe.py`, Ctrl+C to stop; transcript auto-saved). Offline file mode verified word-perfect; live mic capture verified receiving audio, but speech-through-speaker detection not yet proven headless — needs a human to speak. Set output volume; headphones will break it — Banks, due 2026-11-05, source: build 2026-11-02
- [ ] LaSer CV block redesigned in repo variants (2026-11-02). Banks to: paste same block into the Drive CV originals (util, CMS, legacyR); confirm Stage 1 vs "Stage 12" naming; confirm whether any Centre-of-Excellence-type artefact was actually created; confirm whether work continued past the discovery stage — Banks, due 2026-11-04, source: laser-story.md

- [ ] Set `lodgify-reply-drafter` schedule to daily 07:30 Europe/London — Banks, due 2026-10-21, source: setup 2026-10-20
- [ ] Parking permits loop: set `CONFIG.INTAKE_SECRET` in live Apps Script, new web-app version, paste `scripts/pyrunner/parking-permits.py` into PyRunner every 15 min with `LODGIFY_API_KEY` / `PERMIT_WEBAPP_URL` / `PERMIT_INTAKE_SECRET` — Banks, source: 2026-10-28
- [ ] Share the permits sheet (`1ZAQhPWOShrp0xX-Em4_wZl4reKK48HmLt0CyFIlF5uk`) with a person, remove "anyone with link" — Banks, due 2026-10-22, source: audit 2026-10
- [ ] Share real Google Calendar with aios-bot@aios-credentials.iam.gserviceaccount.com as Viewer (Settings → "Share specific calendar"; API is now enabled — SA cannot grant itself; blocks meeting prep) — Banks, source: verify-connections 2026-10-31
- [ ] Enable HumHub REST API: meetup.mentoringba.org → Administration → REST API → Enable; then I re-run verify-connections to confirm — Banks, source: connections.md, verify-connections 2026-10-31
- [ ] Fill aios-intake.md Q2 Sample 2 voice sample — Banks, source: /onboard
- [ ] Build dashboard parking-permits panel — Banks/DI, source: audit 2026-10
- [ ] Restart opencode, then authorise the TidyCal MCP in-browser and confirm the account is Pro — Banks, due 2026-10-21, source: mcp setup 2026-10-20
- [ ] EA-only week: route everything through @executive-assistant, no ChatGPT or custom GPTs — Banks, due 2026-10-28, source: skills backlog 2026-10-20
- [x] Rebrand Sorted to nowsorted.co.uk — complete 2026-10-27; code defaults, Postal, Coolify env, DNS, redirect done
- [ ] Tunisia hotel deal: follow up with the LinkedIn connection, introduce them to the Skool property group, agree a finders' fee in writing before the intro — Banks, due 2026-10-24, source: LinkedIn 2026-10-21
- [ ] Share the Virgin Active "Master Data Management" doc with aios-bot@aios-credentials.iam.gserviceaccount.com (Viewer), then scan it for software/application keywords to build a tools-worked-with list for the CV — Banks, source: CV/job hunt 2026-10-21
- [ ] Fix Webawesome start date to April 2022 in the Drive CV originals (CMS, legacyR, util variants say April 2024) and fix the NHS Professionals dates in SFCRM — Banks, due 2026-10-23, source: projects/job-search/DATE-FIXES.md

- [ ] Decide Laravel vs Django for the bankoledada.co.uk rebuild, then confirm hosting (Coolify?) and design direction — Banks, source: docs/ideas/bankoledada-rebuild-plan.md
- [ ] Authorise Drive write access AND restore Gmail (refresh token expired/revoked 2026-10-31 — one consent URL fixes both; regenerate with `python3 scripts/gdrive-authorize.py`, then `python3 scripts/gdrive-authorize.py <CODE>`) — Banks, source: 2026-10-22, verify-connections 2026-10-31
- [ ] Post LinkedIn Day 2 (MBA — TEACH) when due under twice-weekly cadence — copy from `projects/linkedin-content/daily/day-02-2026-10-22-mba-teach.txt` or the Drive `linkedin-posts` folder — Banks, source: morning coffee 2026-10-29
- [ ] Sweet Soul Guest Inn — Phase 1: Django rooms + bookings models & API (incl. ExternalBooking for Airbnb iCal sync) — pending
- [ ] Sweet Soul Guest Inn — Phase 2: Embed React design-system bundle into Django, wire to API — pending
- [ ] Sweet Soul Guest Inn — Phase 3: Deploy to Coolify, point domain — pending
- [ ] Sweet Soul Guest Inn — Phase 4: Swap placeholder content for real room data/photos — pending
- [ ] Sweet Soul Guest Inn — Phase 5: iCal sync (export + import) for Airbnb availability — pending
- [ ] Production Coolify env: `APP_URL`, `MAIL_FROM_ADDRESS`; verify live magic-link delivery — Banks, source: 2026-10-27; Postal SMTP confirmed working 2026-10-27
- [ ] Create `legal@`/`privacy@` forwarders and fix SPF duplicate/DMARC — Banks, source: 2026-10-27; site already renders both addresses from `config/legal.php`
- [ ] Create the Google Business Profile for Sorted/nowsorted.co.uk (services, photos, hours, website + TidyCal booking link with UTM) — Banks, due 2026-11-06, source: SEO watch 2026-10-30
- [ ] Create the Google Business Profile for MentoringBA (career coaching categories, booking link, UTM'd website) — Banks, due 2026-11-06, source: SEO watch 2026-10-30
- [x] Fix the WebAwesome Consult UK GBP listing: review category ("Web hosting company" vs Business Consultant/Web Design per seo-visibility-plan), change website link from http to https, and confirm whether the booking link should point to the WebAwesome discovery call instead of tidycal.com/mentoringba/discovery-call — Banks, due 2026-11-02, source: SEO watch 2026-10-30 — complete 2026-10-30

## Waiting on someone else

- [ ] Manny — London/Surrey BA contract: HMRC CV emailed 2026-10-28; no response from recruiter yet
- [ ] TTC Tech Senior BA: applied via email 2026-10-28; no response from recruiter yet

## Parked

- [ ] Persist PyRunner event history across redeploys (container FS, not volume-mounted) — deferred, source: 2026-10-20
- [ ] Permit wording: FAQ says "no permit", flow collects registrations — parked by Banks 2026-10-29
- [ ] Two Overcomers FAQ files are identical; Modern Digbeth FAQ holds Cutlass Court content — parked by Banks 2026-10-29

## Done

- [x] Break-it check run on POgO Payments (`~/Desktop/POgO Build/Property-On-The-Go`): 18 force-skipped payment tests re-enabled, 4 real bugs found+fixed (User fillable missing subscription fields → paid users never got plans; retry() throw:true → Paystack errors crashed instead of handled; missing datetime cast → success page crash; null signature header TypeError → 500), 4 new tests + idempotency strengthened; breakit 4/9→9/9 CAUGHT, 160/160 suite green, files hash-restored. Script: ~/Desktop/breakit_payments.py. NOT committed — Banks reviews diff. Note: package-lock.json + deleted street-frontage.png were pre-existing tree changes, not from this work — 2026-11-04

- [x] Break-it check made a global rule: `.claude/rules/break-it-check.md` + AGENTS.md:31 standing requirement — 2026-11-04
- [x] First break-it run (voice toolchain): 19 tests added (`tests/test_interview_tools.py`), 16/16 CAUGHT, 0 MISSED, files hash-verified restored; two real bugs fixed en route (`--prompt` was dead in both file and stream mode); script kept outside repo at /tmp/opencode/scratch/breakit_voice_tools.py, uncommitted — 2026-11-04

- [x] Stephen O'Leary (Stylish City Living) Lodgify thread — CLOSED, guest checked out 2026-11-04; no reply needed. `lodgify_drafts.py` may still list it until the property thread ages out — ignore it, do not surface in briefs — closed by Banks 2026-11-04

- [x] Replied to Estella Foster in Lodgify — 2026-10-29

- [x] Reply to Manny with the HMRC-based CV for the London/Surrey BA contract — emailed 2026-10-28
- [x] Apply to TTC Tech Senior Business Analyst using the legacyR-based CV — submitted via email 2026-10-28
- [x] Fix FAQ matcher for `Stylish City Living` → Cutlass Court — 2026-10-20
- [x] Closing-sign-off detection in `thread_attention` — 2026-10-20
- [x] Lodgify reply-draft digest live (4/4 drafted) — 2026-10-20
- [x] Cleaner departure notices dropped — client no longer uses cleaner services — 2026-10-21
- [x] Newsletter re-permission 40/40 delivered — 2026-10
- [x] Buy nowsorted.co.uk — 2026-10-23
- [x] Push AIOS homepage section to GitHub — 2026-10-27
- [x] Replied to all Lodgify guest messages — team 2026-10-28 (Estella Foster, Charles Rounce and remaining threads)
- [x] Replied to all Lodgify guest messages — 2026-10-27; 0 awaiting reply at 07:51 UTC
- [x] Review all emails on all pages of the website and change to the provided email — 2026-10-27; legal pages use `config/legal.php` (`legal@`/`privacy@nowsorted.co.uk`); `LegalEmailTest` added
- [x] SEO technical foundation: robots.txt, sitemap.xml, OG/Twitter meta — 2026-10-27; sitemap route fixed, OG image added, microsite meta added
- [x] Re-ran connection check — 2026-10-27; 4/7 live. Calendar needs calendar shared, HumHub needs REST API enabled, TidyCal needs re-auth
- [x] Removed out-of-scope Resend mail integration — 2026-10-27; mail is Postal/SMTP only, `PROJECT-STATUS.md` updated
- [x] Postal confirmed set up and working — 2026-10-27
- [x] Removed legacy WhatsApp automation from sorted-app — 2026-10-27; webhook, handler, services, model, migration, OAuth channel, onboarding requirement and public copy removed; Instagram/LinkedIn/GBP posting preserved; residual refs cleaned and committed in `5cd8f1f`; full suite 79 tests/287 assertions pass (PHP 8.5 vendor deprecation flags only)
- [x] Remove inert lead AI-reply fields and dashboard reply stats before re-enabling social — 2026-10-27; columns dropped in `ab09218`, lead attention follows status, reply metrics replaced with lead/status metrics
