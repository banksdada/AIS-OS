# Sorted → AIOS CRM webhook (the Sorted side)

**Status:** written and tested, **not applied to the businessbots repo yet.**
Patch: `sorted-crm-webhook.patch` (in this folder). Verified locally: 5 new
tests pass, 21 assertions.

This is the sending half of the "CRM capture on magic-link verify" decision
(see the decision log and `projects/sorted/README.md`). The AIOS receiving half
is built, deployed and verified live (`/webhook/crm` on `aios.webawesome.co.uk`).

## What it does

When a user clicks their magic link and `AuthController::verify()` logs them in,
Sorted POSTs the contact to the AIOS. The AIOS appends them to the Clients
sheet via `client-tracker.py`. That one click is the only signal we trust — it
proves the email is real — so it's the only place a contact enters the CRM.

## Files changed

| File | Change |
|---|---|
| `app/Services/Crm/CrmCaptureService.php` | **New.** Signs and POSTs the contact; never throws. |
| `app/Http/Controllers/Auth/AuthController.php` | Calls `$crm->capture($user)` inside `verify()`, after login. |
| `config/services.php` | New `crm` block: url, secret, timeout, user agent. |
| `.env.example` | Documents `CRM_WEBHOOK_URL` / `CRM_WEBHOOK_SECRET`. |
| `tests/Feature/CrmCaptureTest.php` | **New.** 5 tests. |

## Key design decisions

- **Fail-safe.** `capture()` catches everything and returns a bool, logging on
  failure. A CRM or network outage can never block a login — the user is
  already authenticated by the time it runs. This is the opposite of the usual
  "throw on failure" service style, and deliberately so.
- **No secret → capture disabled.** Local/dev with no secret logs a warning and
  does nothing. Nothing breaks, nothing is sent.
- **Exact signature scheme as the AIOS expects.** HMAC-SHA256 over
  `"<timestamp>.<body>"`, headers `X-AIOS-Timestamp` / `X-AIOS-Signature`. Same
  scheme the AIOS already tests for PyRunner and newsletter webhooks.
- **Email lowercased, name passed through**, stage fixed to `Lead`. The AIOS
  sanitises again on receipt, so this is the friendly end of a double check.

## To apply

Either apply the patch:

```bash
cd <businessbots repo>
git apply /path/to/sorted-crm-webhook.patch
composer test   # or: php artisan test --filter=CrmCaptureTest
```

Or apply the same edits by hand (five files; the patch shows each).

Then, on the Sorted service in **Coolify**, add:

```
CRM_WEBHOOK_URL=https://aios.webawesome.co.uk/webhook/crm
CRM_WEBHOOK_SECRET=<same value as the AIOS CRM_WEBHOOK_SECRET>
```

Redeploy, then do a real magic-link login with an email you own and confirm the
row appears in the Clients sheet.

## Known local-test caveat (not a code problem)

Running the suite on the Mac needed three untracked directories created
(`bootstrap/cache`, `storage/framework/{cache/data,sessions,views}`,
`storage/logs`) and an `.env.testing` with `APP_KEY` — these aren't in git, and
Docker/Coolify already provides them. On PHP 8.5 the run also emits
`PDO::MYSQL_ATTR_SSL_CA` deprecations from Laravel's own config; the repo's
Docker runs PHP 8.3, where these don't appear. Neither affects the change.

## Not done yet

- The patch is **unapplied** — the repo still has no CRM capture.
- No project-level rate limit on captures. Acceptable while sign-ups are
  low-volume; revisit if the tool gets attention.
- The AIOS logs every capture attempt to `data/crm-captures.json` for audit;
  nothing reads that file yet (no dashboard panel).
