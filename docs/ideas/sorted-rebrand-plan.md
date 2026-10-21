# Sorted Rebrand Plan

**Status:** planned — not started. Blocked on the domain being bought.
**Created:** 2026-10-21
**Review:** on request. Say "review the rebrand plan" and this gets re-read, executed steps ticked, and the checklist re-verified against reality.
**Project:** `projects/sorted/README.md`

---

## The decision this executes

From `decisions/log.md` (2026-10-21):

- The brand stays **Sorted**. The repo keeps the legacy name `businessbots` — cosmetic, do not rename the remote.
- Rebranding is deferred until the domain is owned, then done in **one pass**.
- Preferred domain **`nowsorted.co.uk`**; **`theheadache.co.uk`** bought as a redirect.
- Sorted is a **free client-acquisition tool** — no payment layer.

## Non-negotiable ordering rule

**Nothing in this plan may be executed before the domain is purchased and Postal has sent a verified test message from it.**

Reason: the email address is the only sign-in path (magic link at `/login`). Changing the sending domain before it is verified breaks authentication for every user, including Banks.

---

## Phase 0 — Prerequisites (owner: Banks)

- [ ] Buy `nowsorted.co.uk`
- [ ] Buy `theheadache.co.uk` as a redirect
- [ ] Confirm the **renewal** price, not just the first-year teaser
- [ ] Optional: buy `nowsorted.uk` to stop a squatter (doubles cost; skip if budget-tight)
- [ ] Check `nowsorted` handles are free on LinkedIn and Instagram **before announcing** — if taken, decide whether the mismatch is acceptable
- [ ] Confirm DNS is live and controllable from the registrar

## Phase 1 — Postal: verify the new sending domain (owner: Banks)

Do this first and alone. It is the step that can break production.

- [ ] In Postal, add `nowsorted.co.uk` as a sending domain
- [ ] Publish the DNS records Postal generates: **MX, SPF, DKIM, DMARC**
- [ ] Wait for Postal to show the domain verified/ready
- [ ] Create SMTP credentials for the new domain (or confirm the existing ones cover it)
- [ ] **Send a verified test** from the new domain and confirm delivery to an external inbox
- [ ] Only when that test lands: proceed to Phase 2

## Phase 2 — Coolify: domain + environment (owner: Banks)

- [ ] Add `nowsorted.co.uk` to the Sorted service; let it issue the TLS certificate
- [ ] Confirm HTTPS works before changing `APP_URL`
- [ ] Update the service environment:

```env
APP_NAME=Sorted
APP_URL=https://nowsorted.co.uk
MAIL_FROM_ADDRESS=noreply@nowsorted.co.uk
MAIL_FROM_NAME=Sorted
MAIL_EHLO_DOMAIN=nowsorted.co.uk
```

- [ ] Leave `MAIL_HOST=postal.webawesome.co.uk`, `MAIL_PORT=25`, `MAIL_SCHEME=null`, `MAIL_USERNAME=postal` unchanged — those already work
- [ ] Redeploy
- [ ] Verify the env actually applied:

```sh
php artisan tinker --execute='dump(config("app.url"), config("mail.from.address"), config("mail.mailers.smtp.host"));'
```

- [ ] Request a magic link end-to-end and confirm the mail arrives **from the new address**
- [ ] Keep `automation.baseuse.xyz` running and add a **301 redirect** to the new domain; retain for a few months

## Phase 3 — Application copy (owner: TBD — needs a repo clone)

The Sorted code is **not on this machine** (`projects/sorted/README.md`). This phase needs a local clone or direct edits in GitHub.

- [ ] `resources/views/` homepage hero — brand name and tagline
- [ ] `<title>` and meta/OG tags on the marketing pages
- [ ] Legal pages — Terms, Privacy, Cookies all reference the company name and domain
- [ ] Any hardcoded `automation.baseuse.xyz` or `businessbots.com` strings in views
- [ ] `MAIL_FROM_ADDRESS` fallback in `.env.example` (currently `hello@businessbots.com`)
- [ ] Clear the now-dead `RESEND_API_KEY=` line from `.env.example`
- [ ] Optional cleanup: drop the custom `resend-http` transport from `config/mail.php` and `AppServiceProvider` once nothing references it

## Phase 4 — Record it (owner: me, on request)

- [ ] Rename `projects/sorted/` to match the brand
- [ ] Update `projects/sorted/README.md` — name, domain, live URL, remove the TBD
- [ ] Append the completion decision to `decisions/log.md`
- [ ] Update `context/tasks.md` — close the domain-purchase task
- [ ] Optional: rename the GitHub repo (cosmetic, breaks existing clone URLs)

---

## Defining done

The rebrand is complete when **all** of these are true:

1. `https://nowsorted.co.uk` serves the app over HTTPS with a valid certificate
2. A magic link requested at the new domain arrives, sent from `noreply@nowsorted.co.uk`
3. `automation.baseuse.xyz` 301-redirects to the new domain
4. No user-visible reference to `businessbots`, `automation.baseuse.xyz` or the old from-address remains
5. `theheadache.co.uk` redirects to the new domain

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Sending domain verified **after** `MAIL_FROM_ADDRESS` changes | Magic-link login breaks for everyone | Strict phase ordering: Postal test first, email switch second |
| `MAIL_FROM_ADDRESS` on an unverified domain | Mail silently rejected or spam-foldered | Wait for Postal to report the domain ready before testing |
| `APP_URL` changed before the certificate issues | Mixed-content blocks on CSS/JS/Livewire | Confirm HTTPS by hand before touching `APP_URL` |
| Old domain killed immediately | Anyone with an old link hits a dead page | Keep `automation.baseuse.xyz` as a 301, not a deletion |
| Social handle taken | Brand always looks mismatched across channels | Check handles in Phase 0, before announcing |
| Rebrand executed in dribs and drabs | A half-rebranded product is worse than either name | Do it in one pass, in this order |

## Deliberately not doing

- **Renaming the GitHub repo** — cosmetic, breaks clone URLs; optional at the end
- **Long-term dual-domain hosting** — a redirect is enough
- **A rename from "Sorted" to "The Headache"** — the domain names the pain; the brand carries the outcome. Mixing the two would mean the name and the tagline fight each other
- **Any payment-layer work** — out of scope by decision on 2026-10-21

## Open questions

- Which brand word wins if `nowsorted.co.uk` is taken by purchase time? Fallback candidates checked available: `sortedworks.co.uk`, `getsort.co.uk`, `sortedfast.co.uk`, `rightosorted.co.uk`
- Is `noreply@` right, or a monitored address like `hello@`? A `hello@` invites replies from warm leads — worth having
- Should the tagline live in the `<title>` to compensate for a domain that names the pain rather than the outcome?

---

## Review procedure

When asked to review, in order:

1. Read this file and `projects/sorted/README.md`
2. Ticked boxes: verify, don't trust. Check the live domain, the cert, and the from-address on a real email
3. Report **only** what has changed, is blocked, or is unticked — no restating the plan
4. Update the Status line at the top and the "Defining done" list
5. If every item is ticked, close this plan and log the completion in `decisions/log.md`
