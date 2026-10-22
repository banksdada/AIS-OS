# bankoledada.co.uk — rebuild plan

Status: **proposal, awaiting Banks's decision.** Nothing built yet.
Date: 2026-10-22

## What the site is today (measured, not assumed)

| Item | Value |
|---|---|
| Platform | WordPress 6.8.1, LiteSpeed server |
| Theme | Themify Ultra |
| Page builder | None detected (no Elementor/Divi/WPBakery lock-in) |
| SEO plugin | Squirrly SEO (sitemap generator) |
| Analytics | Site Kit by Google 1.157.0 |
| Posts | **58** |
| Pages | **11** (the pages endpoint publicly reports only "me" — most are not REST-exposed) |
| Categories | **10** |
| Tags | **69** |
| Media | **182** files |
| REST API | **Open** — `wp-json/wp/v2/posts` returns full content, 58 total |

The open REST API is the key fact: content can be exported cleanly as JSON,
including full post bodies, dates, slugs, categories and tags. This is a
straightforward migration, not a scrape.

## The honest recommendation

**Rebuild on Laravel, not Django — and do it as a staged migration, not a
big-bang relaunch.**

Reasons, in order of weight:

1. **SEO preservation is the whole risk.** 58 posts, 69 tags and 10 categories
   are indexed. A rebuild that changes a single URL without a 301 loses ranking.
   Laravel gives clean control over routes, redirects and sitemaps.
2. **Laravel fits the existing estate.** Sorted (businessbots) is already
   Laravel, and Postal mail is already wired for it. One framework to maintain,
   not two. Banks already has a Laravel stack running.
3. **Django would be a second stack.** Banks has Django templates, but adding a
   second framework for one marketing site fragments the estate and the ops
   knowledge.
4. **Static-first rendering keeps rankings safe.** Serve pre-rendered HTML
   (Laravel + a cache, or a static export) so the site is as fast as the
   current LiteSpeed cache, which is currently earning a `x-litespeed-cache: hit`.

Choose Django only if Banks specifically wants Python end to end and will drop
the Laravel estate. Otherwise Laravel.

## What "modern, premium, professional" means concretely

- A real design pass, not a theme. Typography scale, spacing rhythm, a
  considered palette derived from the webawesome identity, and a homepage that
  states what webawesome does in one line.
- Frontend design skill applied deliberately — see `.claude/skills/frontend-design`.
- Performance budget: Core Web Vitals green. LCP under 2.5s, CLS under 0.1.
- Accessibility: WCAG 2.1 AA. Keyboard navigable, proper headings, contrast checked.
- Mobile-first, since a large share of local search is mobile.

## Migration phases

### Phase 0 — Freeze and capture (before any build)
- Export everything via the REST API: 58 posts, categories, tags, media (182
  files), authors, dates, slugs.
- Capture the **current** SEO state: every live URL, its title, meta description,
  canonical, and current search positions. Without before-numbers you cannot
  prove you kept position.
- Capture the Squirrly-generated sitemaps as the URL inventory of record.
- Full XML export from WordPress admin as a backup (Tools → Export).

**Phase 0 is already done (2026-10-22), captured in the repo:**
- `projects/bankoledada-site/url-inventory/urls-2026-10-22.txt` — **148 live
  URLs** across home, posts, pages, categories, tags and archives.
- `projects/bankoledada-site/seo-baseline-2026-10-22.json` — all 58 posts with
  full rendered content, dates, slugs, categories, tags, plus all 10
  categories and 69 tags.
- `projects/bankoledada-site/page-inventory-2026-10-22.json` — all 10 indexable
  pages with their titles, captured from the rendered site, so the 301 map is
  complete even though the REST API exposes only 1 of 11 pages.
- Verified: all 58 posts are published, no drafts exposed. No post has empty
  content. Median post is ~10k characters; the largest is 256k characters of
  HTML, so a handful of posts carry large embedded media that the import must
  handle deliberately.

**What the site actually is:** a personal brand site — "Bankole Dada, Business
Analyst, Agile consultant" — with a blog (58 posts), a resume page
(`/my-resume/`), a resume-writing service page (`/resume-workshop/`), a
contact page, and a `websites` showcase. The title tag pattern is
`Page | Bankole Dada`.

**This matters for the rebuild:** the site ranks for a person's name and for
"business analyst" terms, and it carries a paid service page
(`/resume-workshop/`). Two consequences:

1. **The title tag pattern is a ranking asset.** `Page | Bankole Dada` should
   be preserved exactly in v1, not redesigned.
2. **`/resume-workshop/` is a revenue page.** It must not be dropped, reordered
   out of the nav, or lose its call to action. It should be checked against
   `context/priorities.md` — it is a sellable product.

### Phase 1 — Content model and URL map
- Design the new content model (post, page, category, tag, author, media).
- Build a **complete 1:1 URL map** from old WordPress URLs to new Laravel routes.
  Every URL must have a destination. Anything ambiguous gets a 301 to the
  nearest equivalent, never a 404.
- Decide the URL scheme now and do not change it later.

### Phase 2 — Build
- Laravel app, Blade views (or Inertia + a frontend framework if the design
  needs it). Static-first with a cache layer.
- Import script: read the REST export, write to the new database. Idempotent,
  so it can be re-run against the live WordPress until cutover.
- Media migration: 182 files, rewritten references, consistent filenames.
- SEO layer: per-page title/meta, canonical tags, Open Graph, XML sitemap,
  robots.txt, structured data (Person/Organization/Article).

### Phase 3 — Parity and redirects
- Serve the full 301 map. Test every captured URL resolves.
- Verify sitemaps match the captured inventory.
- Run Lighthouse / Core Web Vitals against staging.
- Side-by-side visual and content parity check on all 11 pages and a sample of posts.

### Phase 4 — Cutover
- DNS/domain switch at a low-traffic window.
- Keep WordPress live on a subdomain until the new site is verified.
- Submit the new sitemap in Search Console, monitor coverage and errors daily
  for two weeks.
- Keep the 301s permanently (do not retire them after a month).

## What I need from Banks

1. **Decision: Laravel or Django.** Recommendation is Laravel, above.
2. **Reach into the WordPress admin** (or a full XML export) — the pages
   endpoint does not expose all 11 pages, so pages need the admin export or
   manual capture.
3. **The design direction** — any brand assets, colours, fonts, or a reference
   site Banks likes.
4. **Where the new site will be hosted** — Coolify, same as Sorted?
5. **Confirm nothing else consumes the current URLs** (email links, newsletter
   archives) before any redirect changes.

## My recommendation on the open items

- **Framework: Laravel.** It matches the Sorted estate and Postal mail setup,
  and one framework beats two. Django only if Banks wants Python-only and is
  willing to run a second stack.
- **Hosting: Coolify**, same as Sorted and the AIOS. One deployment process,
  one set of secrets, one place to look when something breaks.
- **Design: keep the existing identity, sharpen it.** The site has 58 posts of
  established voice and audience. A redesign should feel like the same
  publication, better made — not a different company. Reusing the current
  colours and type keeps recognition and avoids a repositioning project on top
  of a migration project.
- **Content: migrate as-is, then improve.** Editing 58 posts while the
  platform is also changing is how sites lose their voice. Migration first, a
  separate content pass after.
- **Scope v1 to: home, blog index, post, category, tag, page, author, about,
  contact, 301 map, sitemaps, robots.txt, analytics.** Parity. Then enhance.

## Risks

| Risk | Mitigation |
|---|---|
| Losing search position | Phase 0 capture, 1:1 redirect map, monitor Search Console |
| Missing pages (REST hides most) | Get the admin XML export before building |
| 182 media files with broken links | Rewrite references in the import script, verify |
| Two stacks to maintain | Choose Laravel to match the estate |
| Big-bang relaunch | Stage it, keep WordPress live until verified |

## Not doing

- No rewriting of content. Posts migrate as-is. Editing is a separate job.
- No new features in v1. Parity first, then improve.
- No deployment or push without explicit instruction.
