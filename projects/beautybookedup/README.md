# Beauty Booked Up — website design project

**Status:** design/build started 2026-11-24. Local, not deployed. No repo created yet.
**Owner:** Sharon Dada (founder, WebAwesome), with Banks.
**Domain:** `beautybookedup.co.uk` (DNS/hosting not yet configured).
**Build code:** `scrollcraft/builds/beautybookedup/` in this repo.
**Reference:** `~/Desktop/WebAwesome for Beauty Businesses — Website (1).pdf`.
**Design reference:** `https://one.nowsorted.co.uk/` (Scroll Studio). The live
site's source was not found locally; the installed scroll-craft engine, CSS,
fonts and `~/Desktop/scroll-craft/site/` demo pattern were reused.

## What it is

A scroll-driven landing page for a service that gets beauty businesses fully
booked online: websites, booking systems, Instagram auto-replies, social media
management, inbox and calendar management, and AI training. Target customers are
beauticians in the Wigan and Manchester axis, found through Google Maps,
Instagram and other platforms.

Audience includes lash techs, nail techs, aestheticians, brow artists, hair
salons, beauty salons, mobile beauty, and African hair and textured hair
specialists (braids, locs, wigs).

MannyChat-style features are a **later build**. This site promises the service;
it does not include the chat product.

## Decisions on record

- Public brand: Beauty Booked Up. Sharon Dada / WebAwesome credited behind it.
- Art direction: high-key editorial, photographic, warm white and raspberry.
- Grammar: rhythmic cutlist. One hero scrub clip plus six short service clips.
- Signature move: a fixed booking diary that fills with real service names as
  the visitor scrolls, then resolves at the CTA.
- Instagram-style square images around the final CTA, cropped from the service
  clips. Placeholders for Sharon's real Instagram work.
- No logo yet: wordmark in type only.
- No prices, statistics, client screenshots or testimonials invented.
- Existing `KIE_API_KEY` in the AIOS `.env` used for generation (697.8 credits
  at probe). No new key was added.
- Registered in the AIOS index on Banks's explicit 2026-11-24 instruction.

## SEO and link previews

- `index.html` has a description, canonical URL, Open Graph tags, Twitter/X card
  tags and a `Service` JSON-LD block so a pasted link explains the business.
- `assets/og-image.png` (1200x630) is the link preview for WhatsApp, LinkedIn,
  Facebook, Slack and X. `assets/og-image-square.png` (1200x1200) is for
  Instagram-style squares. Both are generated locally from the existing hero
  still and the calendar logo by `node make-og.mjs`, with no KIE spend.
- All absolute URLs currently point at the Coolify demo host
  `http://6xkb0hllwqvmcxunqofth1za.169.58.166.226.sslip.io/`. Replace them with
  `https://beautybookedup.co.uk/` in `canonical`, `og:url`, `og:image`,
  `twitter:image` and the JSON-LD `url` before launch.
- No social handles are invented. Add `og:site_name` extras, Instagram and
  WhatsApp links when Sharon confirms them.

## Open before launch

- Beauty Booked Up mailbox and real Instagram/WhatsApp handles (the PDF only has
  `hello@webawesome.co.uk`).
- Logo and Sharon's real client work to replace generated placeholder imagery.
- Booking link for "Book a free call" (currently a mailto).
- Domain, DNS, hosting and the later MannyChat build.
