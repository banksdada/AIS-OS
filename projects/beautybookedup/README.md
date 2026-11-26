# Beauty Booked Up — website design project

**Status:** design/build started 2026-11-24. Local, not deployed. No repo created yet.
**Owner:** Sharon Dada (partner at WebAwesome Consult UK), with Banks. Reference Gmail: `sharon.darasimi@gmail.com`.
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
- Keyword Sheet: `Beauty Booked Up - keywords (Wigan and Manchester)`, ID
  `1dd6jA1dgYb1ymqitsY2bEo21EZOt2GE19HUWXyPo3cU`,
  https://docs.google.com/spreadsheets/d/1dd6jA1dgYb1ymqitsY2bEo21EZOt2GE19HUWXyPo3cU/edit
  Shared with `bankoledada@gmail.com` and `sharon.darasimi@gmail.com`. Tabs:
  `Keywords` (730 rows), `Microsites` (500 planned rows), `How to use`.
  Local seeds: `projects/beautybookedup/keyword-bank.csv` and
  `projects/beautybookedup/microsite-keyword-bank.csv`.
- Shared image dump: `Beauty Booked Up - Canva image dump`, ID
  `1KAzpO3N6bBOh81LERQ2qgcFBeI3kHlgy`,
  https://drive.google.com/drive/folders/1KAzpO3N6bBOh81LERQ2qgcFBeI3kHlgy
  Subfolders: `01 Raw uploads`, `02 Approved`, `03 Used in drafts`, `Prompt bank`.
  Shared with `bankoledada@gmail.com` and `sharon.darasimi@gmail.com`.
- Canva prompt Doc: `Beauty Booked Up - Canva image prompts (244)`, ID
  `13AES7aHePVPz4DEh7KgZ1H2NRsPhFUf1BPC7OT6luDk`,
  https://docs.google.com/document/d/13AES7aHePVPz4DEh7KgZ1H2NRsPhFUf1BPC7OT6luDk/edit?usp=drivesdk
  Local source: `projects/beautybookedup/canva-image-prompts.txt` (244 prompts).
- Image manifest Sheet: `Beauty Booked Up - image manifest`, ID
  `1VnvqhEqamVjqBAKj3LkIoJKtK4e_YO1Yl3MvysLB14Q`,
  https://docs.google.com/spreadsheets/d/1VnvqhEqamVjqBAKj3LkIoJKtK4e_YO1Yl3MvysLB14Q/edit
- Contacts: general enquiries `hello@beautybookedup.co.uk`; Sharon's reference
  Gmail `sharon.darasimi@gmail.com`.
- All absolute URLs currently point at the Coolify demo host
  `http://6xkb0hllwqvmcxunqofth1za.169.58.166.226.sslip.io/`. Replace them with
  `https://beautybookedup.co.uk/` in `canonical`, `og:url`, `og:image`,
  `twitter:image` and the JSON-LD `url` before launch.
- No social handles are invented. Add `og:site_name` extras, Instagram and
  WhatsApp links when Sharon confirms them.

## Open before launch

- Real Instagram/WhatsApp handles. Confirmed public mailbox:
  `hello@beautybookedup.co.uk`; the old PDF address was `hello@webawesome.co.uk`.
- Logo and Sharon's real client work to replace generated placeholder imagery.
- Booking link for "Book a free call" (currently a mailto).
- Domain, DNS, hosting and the later MannyChat build.
