# WebAwesome AI Audit — product repo

The customer-facing AI readiness audit tool (12-question questionnaire →
scored Crawl/Walk/Run maturity → report, PDF export). Lives in its own repo,
not in the AIOS.

- **Repo:** `github.com/banksdada/webawesome-ai-audit` (Laravel 12, PHP 8.4)
- **Local clone:** none yet — work happens in a scratch clone; clone to
  `~/Desktop/webawesome-ai-audit` if doing persistent dev.
- **Production:** https://ai-audit.webawesome.co.uk (Coolify, deploy files
  merged to main 2026-11-07; same Dockerfile pattern as Speakrite:
  php-fpm + nginx + supervisor, trusted-proxy, `RUN_MIGRATIONS` env,
  healthcheck `/up`)
- **Coolify env needed:** `APP_KEY`, `ANTHROPIC_API_KEY` (optional — without
  it the app falls back to a rules-based report), Postgres DB vars,
  `RUN_MIGRATIONS=true` on first deploy.
- **Tests:** `php artisan test` — 7 (questionnaire, scoring, AI report, PDF,
  validation, proxy x2).
- **Relationship to the AIOS:** the internal generator (`scripts/ai-audit.py`,
  agent-grade evidence audits) stays in the AIOS; this repo is the public
  self-service funnel product. Both are part of the same offer.
- **Landing snippet:** `wordpress-landing--paste-into-WP-page-ai-audit.html`
  for webawesome.co.uk/ai-audit.
