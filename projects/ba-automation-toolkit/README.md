# BA Automation Lab

Repo: `~/Desktop/ba-automation-toolkit` → https://github.com/banksdada/mentoringba-automation-toolkit (private)

A mentoringba teaching toolkit implementing the *Complete BA Automation
Practical Guide*: 8-stage traceable BA workflow — meeting notes → requirements
→ stories/AC → Jira/Confluence (MCP) → SQL validation → API requirements →
UAT (browser automation) → RTM → independent QA review — with 4 human approval
gates.

Agent-neutral by design: rules in `AGENTS.md`/`CLAUDE.md`, prompts in
`PLAYBOOK.md`, pure-Python SQL checks, one `mcp.example.json`. Works with
Claude Code, Codex, opencode, Cursor, Copilot, Gemini CLI.

## Status (2026-11-01)

- Built and verified locally: `tools/init_db.py` + `tools/run_sql_checks.py`
  pass all 3 checks against the demo banking dataset (incl. planted orphan
  record and 101 reconciliation trap).
- Case study: fictional online-banking address update.

## Next

1. Push to a GitHub repo for mentoringba (public-safe: all data fictitious).
2. Dry-run Stage 1–2 with a real student prompt to sanity-check teaching flow.
3. Optional: demo Jira/Confluence sandbox org for Stage 3.
