---
name: morning-coffee
description: Use when someone asks for a morning brief, "plan my day", "what does my day look like", "brief me", or opens the working day. Reads priorities, the task list and live system status, then returns one short plan for today.
---

# Morning coffee

A short daily plan, not a status report. Output under 20 lines or it has failed.

## Steps

1. **Priorities** — read `context/priorities.md`. These decide what counts as progress today; do not restate them back.
2. **Tasks** — read `context/tasks.md`. Pull only overdue items and anything due today. If nothing is due today, say so.
3. **Live status** — run `python3 scripts/dashboard/generate.py`, then read `data/dashboard.json`. Flag any agent that reports `failed`, and any connection that has gone stale.
4. **Open feature requests** — read `context/feature-requests.md`. List items with status `todo` or `in-progress` (max 3, oldest first). If none, skip.
5. **Guest messages needing a reply** — only if Overcomers work is active: `python3 scripts/lodgify_drafts.py`. Report the count and the oldest unanswered thread; do not draft replies here.
6. **Calendar** — Google Calendar API is not enabled in GCP project `266063022919`. If the TidyCal MCP server is connected, use `list-bookings` for today. Otherwise state plainly that the calendar is unreachable — **never invent meetings**.
7. **Today's LinkedIn post** — read `data/linkedin-tracker.json` and `references/linkedin-content-bank.md`. Cadence is **twice weekly** (advised 2026-10-29: daily posting on the page can read as spam).
   - If `startedOn` is null, say only: `Post: start the bank whenever you like — say "start posting" and I'll number the days.`
   - Next day number = highest day in `posted` + 1 (bank sequence, not calendar days).
   - Only surface the post when ≥3 days have passed since the last entry in `posted`. If too soon, say: `Post: next is Day <N> — twice-weekly cadence, not due yet.` and move on.
   - Otherwise pull that post from the bank and report the **page**, **pillar** and the **hook line** (the first line only — never paste the whole post here).
   - Do **not** mark anything posted yourself. Only append to `posted` when Banks confirms he posted, and only then.

## Output format

```
Coffee — <date>

One thing: <the single highest-leverage action today>
Due today: <items from context/tasks.md>
Needs your decision: <blocked items waiting on Banks>
Waiting on others: <chases outstanding>
Post: <WA|MBA> — <pillar> — "<hook line>"
If you have time: <the useful but non-urgent item>
```

## Spoken delivery

The brief is both shown and **spoken**. After printing it, write the same text
to `/tmp/morning-coffee-brief.txt` and run:

```bash
python3 scripts/speak.py --file /tmp/morning-coffee-brief.txt
```

It speaks with the macOS voice (default Daniel; set `AIOS_VOICE` to change).
Skip the spoken part if the user said "silent", "just text", or "no voice" —
and never let a speak error block or repeat the printed brief.

## Rules

- "One thing" must connect to a priority in `context/priorities.md`. If it does not, pick again.
- Lead with action. No preamble, no "here's your brief".
- If there is genuinely nothing to do, say it in one line and stop.
- Never send, publish or commit anything as part of this run.
- The Post line is one line only. If the bank has run out, say `Post: bank finished — 30 days done.` and suggest reviewing which pillar got the most comments.

## Starting the bank

When Banks says "start posting", set `startedOn` in `data/linkedin-tracker.json` to today's date. Day numbers follow the bank sequence (1, 2, 3…); post twice a week, not daily. Never set `startedOn` without being asked.
