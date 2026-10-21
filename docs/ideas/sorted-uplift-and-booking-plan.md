# Sorted — Uplift & paid human-intervention calendar

Status: **draft for review.** Nothing here is built or wired yet. Decisions on
payment mechanism, free-session gating and tier shape were confirmed 2026-10-21.

Companion to `sorted-rebrand-plan.md`. That plan owns the rename; this one owns
what the site says and how a human gets paid. They interlock: do the **content
uplift before the copy swaps in Phase 3** of the rebrand, so the text is rewritten
once rather than twice.

## Why this exists

Sorted is positioned as a **free client-acquisition tool** (see
`projects/sorted/README.md` and the decision log). That positioning is deliberate
and this plan must not undermine it. So:

- The **product** stays free. No paywall, ever.
- **Human time** is a separate, clearly labelled service that sits *beside* the
  product, never *behind* it.

The free-tool promise answers "can I fix this myself?" The calendar answers "I'd
rather someone else did, or I'm stuck." Both are honest; neither cannibalises
the other.

Target audience is a UK small-business owner, often non-technical, frequently
arriving stressed because something is broken and costing them money. That
drives everything below.

## Part A — The uplift

"Proper uplift" means make the site look and read like something a business
owner trusts with their problem. Ordered cheapest-to-highest-leverage.

### A1. Message clarity (no code, highest leverage)

- **Hero states the outcome, not the mechanism.** Not "AI-powered problem
  sorting." Something in the shape of: *"Tell us what's broken. We'll point you
  at the fix — or sort it for you."* One sentence, no jargon.
- **Answer the four questions in order**, above the fold: what is this / who is
  it for / what does it cost (free) / what happens when I click.
- **Kill the word "automation" from the front door.** Buyers have a headache,
  not a use case. Sell the relieved headache.
- **Name the free-ness plainly.** "Free to use. No account, no card." If a card
  is needed for the paid session, say so only at that step.

### A2. Trust signals

- A **worked example** on the homepage: one real-ish problem, what Sorted
  returned, how long it took. Concrete beats a features list.
- **Who's behind it** — a short, human "built by WebAwesome" line with a face.
  Small-business buyers trust a named person far more than a logo.
- **Data handling in one plain sentence** — what's stored, for how long, how to
  get it deleted. This matters more once a booking form collects details (GDPR).

### A3. Structure and flow

- Tighten the path: landing → describe problem → result → (only if needed)
  "talk to a human." Every extra screen loses people.
- **Error and empty states get written properly.** These are where non-technical
  users bounce hardest, and they're where the calendar offer is most relevant.
- Mobile-first. Assume a phone, mid-task, one hand.

### A4. Visual and technical polish

- Consistent spacing, type scale and colour — no templated-default feel.
- **Accessibility pass**: contrast, focus states, labels, keyboard-only path
  through the form. Non-negotiable for a public tool.
- **Page weight and speed**: the site should load instantly on a poor
  connection. Slow = untrustworthy for this audience.
- Meta/OG tags so links shared in WhatsApp and email look intentional.

### A5. Where the human offer lives

- A single, quiet **"Prefer to talk to someone?"** link near the result and in
  the footer. Not a popup, not a banner. It should feel like a door, not a
  sales push.
- One short line of context for the paid part: *"The first 10 minutes are free."*

## Part B — The paid human-intervention calendar

### The ladder

| Session | Price | Payment | Purpose |
|---|---|---|---|
| Free intro | £0 | none | Qualify fit. Strictly capped at 10 min. |
| Short call | £25 | Stripe link, upfront | One specific blocker. |
| Working call | £40 | Stripe link, upfront | Diagnose + walk through, notes after. |
| Deep session | £75 | Stripe link, upfront | Real analysis, written recommendations. Credit toward a project if they proceed. |

**Why these numbers.** UK ad-hoc consultancy runs roughly £90–£150/hr for
experienced independents, and £150–£250/hr for specialists (see Sources). At
£25/£40/£75 the effective rates are ~£75/hr, £80/hr and £75/hr — deliberately at
the **accessible end** for a small-business audience, and *below* the
business-analysis and IT-consultant contract medians (~£500–£550/day). That is
intentional: priced above the free tool but below "hire a consultant," it reads
as a fair shortcut, not a hard sell. Revisit once there's booking data.

### Payment mechanism — Stripe Payment Link per duration (confirmed)

- One **TidyCal booking type per duration** (20 / 30 / 60 min), each pointing at
  its own **Stripe Payment Link** (one-time price, no subscription).
- Payment is taken **at booking**, so a no-show costs the client, not you.
- No code on the Sorted side, nothing to maintain, works with the Monzo-linked
  Stripe already connected.
- **Deferred to the rebrand:** when the domain is bought (rebrand Phase 0–1),
  re-issue the Stripe links and the TidyCal booking types so the checkout and
  confirmation pages carry the new brand and the new `hello@`/`noreply@`
  sender. Don't build links you'll throw away.

### Gating — open, with a short intake form (confirmed)

Anyone can book the free 10 minutes, but the booking type carries a required,
short form. Keep it to three fields:

1. What are you trying to fix? (free text, one line)
2. What have you already tried?
3. Best email to reach you at.

Rationale: it filters "pick your brain" bookings without adding real friction,
gives you prep before the call, and produces a lead record. The "what did you
try" answer is the single best predictor of whether someone becomes a client.

### Rules of the ladder (the guardrails)

- **The 10 minutes is a hard stop.** Free intro is qualification only. If real
  analysis starts, the next step is a paid booking — say so kindly, once.
- **Never let the free tool feel worse than the paid call.** No locked features,
  no artificial waits, no "upgrade to see results."
- **Paid session = a deliverable.** Working and deep sessions get a short written
  summary afterwards. That is what the price buys, and it's what makes the £75 a
  credit-worthy session rather than a chat.
- **Cancellation policy, stated upfront:** free reschedule up to 24h before;
  inside 24h the fee isn't refunded. Written on the booking page, not buried.
- **GDPR:** booking details are used to run the session and follow up, nothing
  else. Say so in one line at the point of booking, matching A2.

### Implementation order (TidyCal / Stripe side)

1. Confirm the TidyCal plan supports the number of booking types you need (note:
   the AIOS TidyCal MCP requires TidyCal **Pro**; every call errors otherwise).
2. Create the four booking types: Free 10 / £25 / £40 / £75 — see the ladder.
3. Create four Stripe Payment Links (one-time), then attach each to its booking
   type.
4. Add the three intake questions to the free type; add a lighter version (just
   "what do you want to cover?") to the paid types.
5. Write the confirmation email copy so it sets expectations: what to bring,
   cancellation terms, and what the free 10 minutes is for.
6. Only then surface the link on the site (A5). **Do not advertise a booking
   path that isn't proven** — same rule as the rebrand plan's ordering.

## Definition of done

- Hero and the four questions rewritten and reviewed against the voice samples.
- Worked example live on the homepage.
- Accessibility and mobile passes done; a keyboard-only run reaches the result
  and the booking link.
- Four TidyCal booking types exist; each paid one takes payment at booking.
- Cancellation terms and the GDPR line are visible before payment.
- The booking link appears in exactly two places on the site (result + footer).

## Risks

| Risk | Mitigation |
|---|---|
| Paid calls undercut the "free tool" story | Keep it a separate service; never gate the product; label the paid part as human time |
| Free 10 minutes becomes a free 30 | Hard stop rule, stated on the booking page |
| No-shows on paid bookings | Payment upfront at booking |
| Booking links built before rebrand → throwaway work | Defer link creation to rebrand Phase 0–1 |
| Pricing too low to be sustainable | Revisit against booking data; treat £25/£40/£75 as a starting ladder |

## Open questions

- **Paid-tier email sender.** A monitored `hello@` (invites replies from warm
  leads) vs `noreply@`. Leaning `hello@` — same open question as the rebrand plan.
- **Do paid sessions get recorded / notes shared?** Affects the deliverable
  promise and the deep-session price.
- **Is £75 credited toward a project, or standalone?** Credit is the stronger
  offer but commits you to project pricing.

## Sources

- UK consultant day/hourly rates 2026 (business-accounting.co.uk; consultingdemand.com)
- HR/independent consultant ad-hoc rates £90–£150/hr, specialists £150–£250/hr
  (maarifaconsultancy.co.uk; business-accounting.co.uk)
- Freelance business-consultant UK benchmark £41–£246/hr (solohourly.com)
- Free-10-min → paid-session ladder pattern (solopricing.com; ruul.io)
