# Sorted / BusinessBots (automation.baseuse.xyz)

**Status:** active — substantial skeleton, not launch-ready
**Live:** https://automation.baseuse.xyz (verified HTTP 200, 2026-10-20)
**Repo:** `git@github.com:banksdada/businessbots.git` (branch **`master`**, 84 commits)
**Local code:** not found on Desktop -> Banks if a local clone exists
**Stack:** Laravel + Blade/Livewire, Filament admin, Python workers, Docker/Coolify

**Brand:** **Sorted**. The repo keeps the legacy name `businessbots` — cosmetic, do not rename the remote.
**Intended domain:** `<TBD — nowsorted.co.uk preferred (purchase planned 2026-10-21); theheadache.co.uk as redirect>`. Not owned yet, so not wired in.

**Positioning (decided 2026-10-21):** Sorted is a **free client-acquisition tool — no payment layer.** Stripe/Cashier stays unbuilt. The goal is getting clients, not MRR from the tool, so the only thing launch-ready really requires is: a visitor describes a problem and lands in Banks's pipeline.

## What it is

Describe what's getting in the way, get a clear fix plan: what's causing it, the simplest fix, what it saves in time and money. A real person checks every plan first. Page line: *"You don't need AI. You need the problem gone."*

Under the hood: multi-vertical SaaS with WhatsApp conversation loop, multi-platform posting (Instagram, LinkedIn, GBP), 8 industry verticals, GDPR-aware legal pages. Stripe/Cashier is wired but intentionally out of scope.

## Launch blockers, in order

1. **Auth scaffolding + `bootstrap/app.php`** — the app does not boot without them. Currently 500s on the magic-link submit (mail env missing in Coolify).
2. **Lead capture -> CRM webhook** — the whole point of the tool. Ready AIOS-side; see Open.
3. **Cookie consent banner** — legal exposure, needed regardless of whether it charges.
4. **`docker-compose.yml`** never assembled into one real file — lower priority, Coolify already runs.
5. Then: tests (currently **zero**), CI/CD, transactional mail, notification system, DPA document.

**Dropped from the blocker list:** LinkedIn/GBP posting analytics (a paying-customer feature), Stripe/Cashier self-serve billing.

## Working rule

`PROJECT-STATUS.md` in that repo is the honest single source of truth — read it cold before changing anything. Docs: `architecture.md`, `build-plan.md`, `code-standards.md`, `ui-rules.md`, `ui-registry.md`, `progress-tracker.md`.

## Decisions on record

**(2026-10-20)**
- **CRM capture on magic-link verify.** `AuthController::verify` at `/login/verify/{token}` is the hook — only emails that are proven real reach the CRM. `SubmitProblem` has no email field; it just uses `auth()->user()`.
- **Transport is a signed webhook into the AIOS** (`/webhook/<event>`, HMAC over `<timestamp>.<body>`), which runs `client-tracker.py add`. Sheet schema stays in one codebase.
- **Mail goes through self-hosted Postal**, not Resend. `MAIL_MAILER=smtp`; clear `RESEND_API_KEY`.

**(2026-10-21)**
- **Free marketing tool — no payment layer.** See positioning above.
- **Rebrand deferred until the domain is bought**, then executed in one pass.

## Rebrand checklist (one pass, once the domain is owned)

Do **not** start before the domain is bought and Postal sends a verified test from it — mail is the only sign-in path.

- [ ] Buy the domain; transfer/publicise DNS
- [ ] Grab matching social handles (LinkedIn/Instagram) before announcing
- [ ] Coolify: add the domain to the Sorted service, reissue the certificate
- [ ] Coolify env: `APP_NAME`, `APP_URL`, `MAIL_FROM_ADDRESS`, `MAIL_FROM_NAME`, `MAIL_EHLO_DOMAIN`
- [ ] Postal: add the sending domain; publish MX/SPF/DKIM/DMARC
- [ ] App: homepage hero, `<title>`, meta/OG tags, legal pages (Terms/Privacy/Cookies)
- [ ] AIOS: rename `projects/sorted/`, update this README, log the change
- [ ] Keep `automation.baseuse.xyz` as a 301 redirect for a few months
- [ ] GitHub repo rename (optional, cosmetic)

## Open

- [ ] **Fix the login 500** — Coolify: copy the GoodTurn mail block, set `MAIL_HOST=postal.webawesome.co.uk`, `MAIL_PORT=25`, `MAIL_SCHEME=null`, redeploy. Verify with `php artisan tinker --execute='dump(config("mail.mailers.smtp.host"), config("mail.mailers.smtp.port"));'`
- [ ] AIOS side: add the CRM webhook route + handler in `scripts/dashboard/serve.py` (pattern already there for `/webhook/pyrunner` and `/webhook/newsletter`) — needs a `*_WEBHOOK_SECRET` in Coolify
- [ ] Sorted side: POST to that webhook from `AuthController::verify` on success
- [ ] Record customer/signing-up numbers so it can count toward the £10k target
