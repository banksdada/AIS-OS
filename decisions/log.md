# Decisions Log

## 2026-09-06 - Audit evidence and routing maintenance

Decision: Ship audit rubric v2 and a small /link skill. Audit scores working evidence across the Four Cs, checks operating-manual routing and freshness, and passes one concrete gap into /level-up. A selected repair can improve an existing workflow instead of creating another skill.

Why: File counts, configured keys, named rituals, and recent edits do not prove an operational AIOS. Source findability and freshness need explicit checks.

Alternatives considered: Keeping presence-based scoring or requiring a hot cache. Neither reliably establishes retrieval quality or successful execution.

## 2026-09-06 - Portable skills and automatic audit history

Decision: Ship all four skills for Claude Code and Codex, with bundled resources, matching operating manuals, and a script for regenerating Codex copies. Audit reports are saved automatically, preserve previous runs, and track findings across comparable inspections.

Why: Students need the same shared guidance when switching assistants and evidence of actual improvements over time. Intentional runtime adaptations, unknown verification, and confirmed defects are reported separately.

## 2026-09-06 - Portable 3D Brain skill

Decision: Add `/3d-brain` for Claude Code and Codex. Ask for a name and categories, map selected local folders, and scaffold a bundled, configurable application with spherical placement, Cinema, and interactive growth replay.

Why: Shipping the working renderer preserves the intended appearance and interactions across AIOS installations. A prose-only prompt would produce inconsistent recreations. User config and graph data remain local; the public package includes only code, documentation, dependency notices, and fictional test inputs.

## 2026-09-06 - Add ongoing context interviews

Decision: Adapt Herk-2's grill-me skill for the student kit and ship matching Claude/Codex packages. Save every answer to brainstorms/, preserve resumable Q&A history, and update canonical context only with confirmed facts during requested context-building sessions.

Why: Onboarding is an initial snapshot. Ongoing interviews capture changing priorities, decisions, and preferences while keeping tentative ideas distinct from current business facts.

## 2026-10-14 - AGENTS.md migration repair

Decision: Migrated CLAUDE.md content to AGENTS.md to fix template placeholders. This establishes the root operating manual for all AI tools and enables routing to actual user context.

Why: The audit found AGENTS.md retained template placeholders while CLAUDE.md had been customized with business details. This mismatch prevents proper routing and AIOS functionality.

Alternatives considered: Keeping duplicate context in both files (rejected due to maintenance burden), or leaving AGENTS.md as template (rejected because no AI tool would read actual user context).

Owner: Banks Dada (self)

## 2026-10-14 - Google Drive connection verified and CRM sheet wired

Decision: Copied the service account JSON from Downloads into scripts/credentials.json and verified the Google Drive connection. Updated gdrive-list.py and client-tracker.py to resolve credentials relative to the script directory so they run from any working directory.

Why: The audit finding F4/F7 required live evidence of at least one verified connection. The credentials file existed but was not in the expected location, blocking verification.

Outcome: Drive API verified — service account `aios-bot@aios-credentials.iam.gserviceaccount.com` lists the Drive root and finds the "aios folder". connections.md and AGENTS.md now record verified auth and last-checked date. Sheets API also reachable, but the service account cannot create its own spreadsheets (no Drive quota), so the CRM sheet must be created in the main Google account and shared with the service account as Editor.

Alternatives considered: Using application-default OAuth credentials instead of a service account (rejected — service account is the durable, non-interactive auth the AIOS needs).

## 2026-10-15 - Gmail auth switched from service account to OAuth 2.0 refresh-token flow

Decision: Read `bankoledada@gmail.com` via OAuth 2.0 (refresh token) instead of the service account, and treat the service account as Drive/Calendar-only.

Why: The service-account path is a dead end for this mailbox. Gmail's "Grant access to your account" rejects service-account identities outright ("Google account address you have specified is invalid"), and domain-wide delegation requires a verified Google Workspace domain that a consumer gmail.com account does not have. OAuth 2.0 is the only path that works for a personal gmail.com address.

Outcome: OAuth app configured (External consent screen, app `webawesome AIOS`, test user `bankoledada@gmail.com`), refresh token exchanged and stored in `.env` as `GMAIL_REFRESH_TOKEN`. `python3 scripts/verify-connections.py` reports Gmail live at ~201 messages. connections.md, AGENTS.md, and the brainstorm capture updated.

Note: The verifier's `Credentials.from_Refresh_token(...)` call was incorrect for the installed google-auth version. The working form is `Credentials(token=None, refresh_token=..., token_uri='https://oauth2.googleapis.com/token', client_id=..., client_secret=..., scopes=[...])`. Fixed in scripts/verify-connections.py, which now also loads `.env` directly.

Owner: Banks Dada (self)

## 2026-10-19 - Lodgify guest-messaging panel: polling first, webhooks deferred

Decision: Build the Lodgify integration as a read-only polling panel first (Step 1). The dashboard polls the Public API v2 with a 5-minute cache for upcoming arrivals (48h window) and guest message threads, flags unanswered messages over 2 hours, tags urgent keywords (check-in, access, problem), and never sends automatic replies — the owner replies in Lodgify. Webhooks (Step 2, instant updates) are deferred until Lodgify's request signing is confirmed.

Why: Lodgify's public OpenAPI spec defines `POST /webhooks/v1/subscribe` but documents no request-signature scheme, so a webhook endpoint cannot be built fake-post-safe from docs alone. Polling works on any plan that allows API access, needs no account-side setup, and shipped immediately. Live verification on build day found 1 arrival in 48h and 5 guest messages awaiting reply (oldest 28 days).

Outcome: `scripts/dashboard/lodgify.py` wired into the dashboard payload and "Lodgify inbox" panel. Auth via `LODGIFY_API_KEY` (`X-ApiKey` header); the key must also be added to Coolify's Environment tab and the repo pushed to `main` before redeploy. Property names resolve via `/v2/properties` (not `/v2/properties/info`, which 404s). Setup and the Step 2 build plan are in references/lodgify-api.md; connections.md domain 11.

Alternatives considered: Webhooks-first (rejected — signing unconfirmed, would risk accepting forged posts); auto-replies to guests (rejected — owner must review before guests hear from the system).

Owner: Banks Dada (self)