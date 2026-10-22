# bankoledada.co.uk (personal site rebuild)

**Status:** proposed — plan written, no build started
**Live:** https://www.bankoledada.co.uk (HTTP 200, verified 2026-10-22)
**Plan:** `docs/ideas/bankoledada-rebuild-plan.md`

## What it is today

A personal brand site: "Bankole Dada, Business Analyst, Agile consultant".
WordPress 6.8.1 on LiteSpeed, Themify Ultra theme, Squirrly SEO, Site Kit by
Google. No page-builder lock-in.

| Asset | Count |
|---|---|
| Posts | 58 (all published) |
| Pages | 11 (10 indexable) |
| Categories | 10 |
| Tags | 69 |
| Media | 182 files |
| Indexable URLs | 148 |

## The plan in one line

Rebuild on **Laravel** (matching the Sorted estate) with static-first rendering,
migrating all content via the open WordPress REST API, behind a 1:1 redirect map
so search position is preserved. Django only if Banks wants Python-only and is
willing to run a second framework.

## Phase 0 — done (2026-10-22)

Captured in this folder as the before-numbers:

- `url-inventory/urls-2026-10-22.txt` — 148 live URLs
- `seo-baseline-2026-10-22.json` — all 58 posts (full content, dates, slugs,
  categories, tags) + 10 categories + 69 tags
- `page-inventory-2026-10-22.json` — all 10 indexable pages with titles

## Two things v1 must not break

1. **The `Page | Bankole Dada` title pattern.** It is a ranking asset.
2. **`/resume-workshop/`.** A revenue page. It must keep its call to action and
   its place in the nav. See `context/priorities.md` — a sellable product.

## Why it is not a quick swap

The risk is not the build, it is the 148 indexed URLs. Phase 0 exists so that
"we kept our position" is provable rather than assumed.

## Not doing

- No content rewriting in the migration. A separate pass afterwards.
- No new features in v1. Parity first.
- No deployment or push without explicit instruction.
