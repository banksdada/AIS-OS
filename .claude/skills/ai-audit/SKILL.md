---
name: ai-audit
description: Use when asked to run/prepare an "AI audit", "AI adoption audit" or "AI readiness assessment" for a company (pitch, interview homework, client proposal). Researches from public evidence, fills a structured spec, renders a one-page A4 summary plus full document, PDFs included.
---

# AI adoption audit

Produces an external, evidence-based AI adoption audit for any company in two
artefacts: a print-ready one-page A4 and a full document. The product is the
method: evidence in, assumptions labelled, humans in the loop, everything
measured. Never pretend to have seen inside a company.

## Steps

1. **Research pass (public only).** Web-search: company model and size; the CIO/CTO/decision-maker profile (their published words become the audit's spine — echo one phrase deliberately); technology signals from job adverts and stack mentions; policy/industry context that changes the game; enforcement/operations detail where relevant. Record a source for every claim.
2. **Write the spec.** `python3 scripts/ai-audit.py spec --company "X" --out spec.json`, then fill every field with the research. Non-negotiable content rules:
   - `ratings.state`: 0 none visible / 1 nascent / 2 building / 3 established — the number is a discovery question, never a verdict;
   - every `evidence` string names its public source;
   - `opportunities` always carry `boundary` (what stays human) and `measure` (the number that proves it earned its keep);
   - `strategic` is the one finding that reframes AI as revenue, not cost — most companies have one; if you cannot find it honestly, leave the section out;
   - `first90` describes the auditor in the seat, not a slide.
3. **Render.** `python3 scripts/ai-audit.py render --spec spec.json --out-dir OUT --pdf` — one-pager and full HTML + PDF (headless Chrome). Verify the one-pager fits one page; tighten copy, don't shrink fonts below the template defaults.
4. **Presentation advice to the user.** Hand over the one-pager; keep the full doc as backup. Open with the method, invite correction on the ratings ("tell me where this is wrong" is the strongest line in the pack). Never lecture the decision-maker about their own company.

## Rules

- Public evidence only. Inferences labelled. No invented internal knowledge.
- Human-boundary column is mandatory — an opportunity without one gets cut.
- Check the tool's tests before shipping a new spec shape that stresses the renderer: `python3 -m unittest discover -s tests -p test_ai_audit.py`.
- If this skill or the renderer changes, re-run the break-it (`~/Desktop/breakit_ai_audit.py` or rewrite it per `.claude/rules/break-it-check.md`) before calling it done.
