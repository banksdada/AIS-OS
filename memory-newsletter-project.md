---
name: newsletter-project
description: WebAwesome newsletter codebase location and WAT framework structure
metadata:
  type: project
---

## WebAwesome newsletter project

Local repo at `/Users/banksdada/Desktop/newsletter-project`, separate from
the AI OS repo. Runs the **WAT framework** (Workflows, Agents, Tools).

**Why:** The AI OS dashboard observes this project — it does not run it.
The newsletter's build/send intelligence lives in its own repo with its own
`.env` and Claude.MD. The dashboard surface is `scripts/newsletter-status.py`,
which reads `.tmp/newsletter/` and reports build state.

**How to apply:** When the user asks about the newsletter, the dashboard
panel (added 2026-10-17) is the live view. To actually build or send, the
context is the newsletter repo, not AI OS. Key files:
- `tools/build_newsletter.py` — renders HTML/txt/SVG from a content JSON
- `tools/send_newsletter.py` — SMTP send, dry-run by default
- `.tmp/newsletter/` — rendered builds, content JSON, send logs
- `.env` — all SMTP/Gmail config commented out; nothing is sendable yet

Reference: `references/newsletter-api.md`.