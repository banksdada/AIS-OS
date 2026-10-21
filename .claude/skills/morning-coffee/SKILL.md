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
4. **Guest messages needing a reply** — only if Overcomers work is active: `python3 scripts/lodgify_drafts.py`. Report the count and the oldest unanswered thread; do not draft replies here.
5. **Calendar** — Google Calendar API is not enabled in GCP project `266063022919`. If the TidyCal MCP server is connected, use `list-bookings` for today. Otherwise state plainly that the calendar is unreachable — **never invent meetings**.

## Output format

```
Coffee — <date>

One thing: <the single highest-leverage action today>
Due today: <items from context/tasks.md>
Needs your decision: <blocked items waiting on Banks>
Waiting on others: <chases outstanding>
If you have time: <the useful but non-urgent item>
```

## Rules

- "One thing" must connect to a priority in `context/priorities.md`. If it does not, pick again.
- Lead with action. No preamble, no "here's your brief".
- If there is genuinely nothing to do, say it in one line and stop.
- Never send, publish or commit anything as part of this run.
