---
name: pulse-check
description: Use when someone asks how their projects are doing, wants a project pulse check, "what needs attention", "review my projects", or asks which workstream is at risk. Reviews every active project and flags only what needs a decision or has gone stale.
---

# Pulse check

A weekly (or on-demand) review of every active workstream. Report exceptions, not summaries — re-reading the READMEs back to Banks wastes his time.

## Steps

1. **Enumerate** — list `projects/*/`. Each folder with a `README.md` is an active workstream. Note the `**Status:**` line.
2. **Per project, read the README** and answer three things only:
   - Has anything in **Open** become overdue or obsolete?
   - Is **Status** still accurate? (`active`, `blocked`, `shipped`, `on hold`)
   - Is there a decision or next action that needs Banks?
3. **Live systems** — run `python3 scripts/dashboard/generate.py` and read `data/dashboard.json`. Flag agents reporting `failed`, and any PyRunner script that has not reported in > 24 hours despite being scheduled.
4. **Connections** — check `connections.md` for anything last-checked more than 7 days ago that was previously verified. Verify it live with `python3 scripts/verify-connections.py` if Banks wants proof.
5. **Tasks** — read `context/tasks.md` for anything sitting in *Waiting on someone else* for more than 7 days. Those are the silent killers.

## Output format

```
Pulse — <date>

At risk:
  <project> — <one line: what is wrong and the decision needed>

Stale:
  <project or connection> — <how long untouched>

Healthy, no action:
  <project names only, one line>

Actions for you:
  1. ...
```

## Rules

- Only flag what changed, is overdue, or needs a decision.
- If every project is healthy, say so in two lines. Do not pad.
- Do not edit project READMEs or tasks as part of this run unless Banks asks — report first, then act on his say-so.
- Use `projects/` as the source of truth for what is active. Do not invent workstreams from memory.
