# Sorted / BusinessBots (automation.baseuse.xyz)

**Status:** active — SEO foundation, legal-email rebrand and legacy WhatsApp removal done 2026-10-27; launch blockers remain
**Live:** https://automation.baseuse.xyz (verified HTTP 200, 2026-10-20)
**Repo:** `git@github.com:banksdada/businessbots.git` (branch **`master`**, 90 commits)
**Local code:** `projects/sorted-app` (separate git repo, branch `master`)
**Stack:** Laravel + Blade/Livewire, Filament admin, Python workers, Docker/Coolify

**Brand:** **Sorted**. The repo keeps the legacy name `businessbots` — cosmetic, do not rename the remote.
**Intended domain:** `nowsorted.co.uk` — **purchased and active 2026-10-23 → 2028-10-23**. `theheadache.co.uk` still to buy as a redirect. The rebrand plan is unblocked and may run in one pass.

**Rebrand plan:** `docs/ideas/sorted-rebrand-plan.md` — phased, with a strict rule that nothing runs before the domain is bought and Postal verifies a test send. Review on request.

**Uplift + paid human-intervention calendar:** `docs/ideas/sorted-uplift-and-booking-plan.md` — site-wide readability and trust uplift, plus a TidyCal ladder (free 10 min → 20/30/60 min at £25/£40/£75) for clients who want a human. Human time is kept deliberately separate from the product, and priced at the accessible end of the UK market, to protect the free-tool positioning.

**Positioning (decided 2026-10-21):** Sorted is a **free client-acquisition tool — no payment layer.** Stripe/Cashier is wired but out of scope for launch. The goal is getting clients, not MRR from the tool, so the only thing launch-ready really requires is: a visitor describes a problem and lands in Banks's pipeline.

## What it is

Describe what's getting in the way, get a clear fix plan: what's causing it, the simplest fix, what it saves in time and money. A real person checks every plan first. Page line: *"You don't need AI. You need the problem gone."*

Under the hood: multi-vertical SaaS with multi-platform posting (Instagram, LinkedIn, GBP), 8 industry verticals, GDPR-aware legal pages. Stripe/Cashier is wired but intentionally out of scope. The legacy WhatsApp automation was removed 2026-10-27.

## Progress

**(2026-10-27)** SEO technical foundation and WhatsApp removal committed in `d177264`: robots.txt, sitemap.xml, OG/Twitter meta, 1200x630 OG image, microsite meta and link fixes, legal pages now use `legal@`/`privacy@nowsorted.co.uk`, and `SeoTest` + `LegalEmailTest` cover the changes. `.env.example` now points `APP_URL` at `https://nowsorted.co.uk`; production Coolify env still needs the same change. Resend was removed — mail is Postal/SMTP only. The legacy WhatsApp webhook, handler, services, model, migration, OAuth channel, onboarding requirement and public copy were removed; Instagram/LinkedIn/GBP posting remains. Final residual cleanup and AI config committed in `5cd8f1f`. Full suite passes: 75 tests, 274 assertions, 0 failures; all 75 are flagged deprecated by a PHP 8.5 vendor PDO warning.

## Launch blockers, in order

1. **Production magic-link verification** — Postal is set up and working; verify live magic-link delivery end-to-end.
2. **Lead capture -> CRM webhook** — the whole point of the tool. Ready AIOS-side; see Open.
3. **Cookie consent banner** — legal exposure, needed regardless of whether it charges.
4. **Production deployment verification** — confirm Coolify env, queue worker, storage link and health check; `docker-compose.yml` and `Dockerfile` exist.
5. Then: CI/CD, transactional-mail monitoring, notification system, DPA document.

**Dropped from the blocker list:** LinkedIn/GBP posting analytics (a paying-customer feature), Stripe/Cashier self-serve billing.

## Working rule

`PROJECT-STATUS.md` in that repo is the honest single source of truth — read it cold before changing anything. Docs: `architecture.md`, `build-plan.md`, `code-standards.md`, `ui-rules.md`, `ui-registry.md`, `progress-tracker.md`.

## Decisions on record

**(2026-10-20)**
- **CRM capture on magic-link verify.** `AuthController::verify` at `/login/verify/{token}` is the hook — only emails that are proven real reach the CRM. `SubmitProblem` has no email field; it just uses `auth()->user()`.
- **Transport is a signed webhook into the AIOS** (`/webhook/<event>`, HMAC over `<timestamp>.<body>`), which runs `client-tracker.py add`. Sheet schema stays in one codebase.
- **Mail goes through self-hosted Postal** over SMTP. `MAIL_MAILER=smtp`; no third-party mail provider.

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
