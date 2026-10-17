# WebAwesome Newsletter — local project reference

Local codebase at `/Users/banksdada/Desktop/newsletter-project`. Runs the
**WAT framework** (Workflows, Agents, Tools): `workflows/` (SOPs),
`tools/` (deterministic scripts), `.tmp/` (disposable intermediates).

## Layout

```
newsletter-project/
├── tools/
│   ├── build_newsletter.py      # render HTML + plain text + SVG infographic
│   └── send_newsletter.py       # SMTP send (dry-run by default)
├── workflows/                  # SOPs (currently empty — .gitkeep)
├── brand/webawesome-brand-kit  # brand tokens, logo, palette
├── .tmp/newsletter/            # rendered builds, content JSON, send logs
└── .env                        # SMTP/Gmail config (gitignored, never committed)
```

## Build

```bash
cd /Users/banksdada/Desktop/newsletter-project
python3 tools/build_newsletter.py --content .tmp/newsletter/content-2026-10-ai-automation.json
# writes .tmp/newsletter/webawesome-newsletter-<campaign>.html + .txt + infographic-<campaign>.svg
```

Content JSON schema (validated by `build_newsletter.py`): `meta`,
`hero`, `cta`, `footer` are required. Optional: `insights`, `case_studies`,
`capabilities`, `articles`, `testimonial`, `header`.

## Send

```bash
# dry run — reports recipients, subject, SMTP config, nothing sent
python3 tools/send_newsletter.py --html .tmp/newsletter/webawesome-newsletter-*.html

# test send to one address
python3 tools/send_newsletter.py --html ... --to you@example.com --send

# send to the full list
python3 tools/send_newsletter.py --html ... --send
```

Send config (`.env`): `SMTP_HOST`/`SMTP_PORT`/`SMTP_SECURITY`/`SMTP_USER`/
`SMTP_PASSWORD`, or the Gmail shortcut `GMAIL_USER` + `GMAIL_APP_PASSWORD`
(app password, not your regular password). Also `NEWSLETTER_FROM_EMAIL`,
`NEWSLETTER_FROM_NAME`, `NEWSLETTER_REPLY_TO`, `UNSUBSCRIBE_URL`,
`PREFERENCES_URL`, `MAX_PER_RUN` (default 100), `SEND_DELAY` (default 1.5s).

## Dashboard integration

`scripts/newsletter-status.py` is the read-only probe the AI OS dashboard
calls. It scans `.tmp/newsletter/` for the latest build, content JSON,
recipient list and send logs and reports:

- `latestBuild` — newest rendered HTML (file, size, last modified)
- `latestCampaign` — campaign name, subject, preheader from the content JSON
- `buildCount` — total rendered builds
- `recipientCount` — addresses in `.tmp/newsletter/recipients.txt`
- `lastSendLog` — most recent `send-log-*.csv` filename
- `envConfigured` — whether `.env` has any non-comment lines

The probe never writes or sends. The dashboard panel renders the build state
and a one-line send command; it does not press send.

## Notes

- The `.env` is **not** populated — all sending config is commented out.
  Nothing can be sent until `GMAIL_USER`/`GMAIL_APP_PASSWORD` or an SMTP block
  is added.
- No recipients file exists yet (`recipientCount: 0`).
- The build from 2026-10-07 ("AI at work: what's actually working in 2026")
  is the only rendered campaign so far.