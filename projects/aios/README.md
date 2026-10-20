# AIOS

**Status:** active
**Owner:** Banks

The AI Operating System itself — context, connections, skills, agent, automations.

## What's in it

- Context: `context/about-me.md`, `about-business.md`, `priorities.md`, `tasks.md`
- Connections: 8 domains in `connections.md`, live-checked by `scripts/verify-connections.py`
- Skills: `.claude/skills/` (canonical) mirrored to `.agents/skills/` via `bash scripts/sync-codex-skills.sh`
- Agent: `.opencode/agent/executive-assistant.md`
- PyRunner fleet: 7 scripts reporting to `https://aios.webawesome.co.uk/data`

## Open

- Dashboard parking-permits panel not built
- PyRunner event history lost on redeploy (container FS, not volume-mounted)
- `aios-intake.md` Q2 Sample 2 voice sample still missing
