# Break-It Check — global testing requirement

Set by Banks 2026-11-04. Applies to EVERY product or feature built through
AIOS from this date forward. One topic per rule; the procedure lives nowhere else.

## What it is

A break-it check proves the TESTS protect the feature, not just that the code
runs. A script deliberately breaks the code ONE rule at a time, runs the
feature's tests, and records the result:

- **CAUGHT** — at least one test failed. The tests protect that rule.
- **MISSED** — every test still passed. The tests have a gap.

## Procedure

1. **List the rules.** Read the feature's actual code and write a plain-English
   list of every rule it enforces: who is allowed, what is refused, what is
   checked before saving, limits, expiry times, what must never be shown.
   Show the list and get confirmation before continuing. Only list rules that
   are genuinely in the code — read it, don't remember it.
2. **Feature tests must exist and pass.** Run the normal feature tests once.
   If they fail, stop and report. If the feature has NO tests, that is a hard
   stop: write the tests first (and say so), because a break-it with no tests
   measures nothing.
3. **Write ONE script, `breakit_<feature>.py`, saved OUTSIDE the project
   folder** (e.g. the Desktop or the temp dir — never inside the repo, and
   never committed unless Banks asks). For each rule:
   - copy the original file first;
   - break that ONE rule in the code (remove a check, flip a condition, change
     a number, skip a permission test);
   - run ONLY this feature's tests;
   - record CAUGHT if any test fails, MISSED if all pass;
   - ALWAYS restore the original, even on crash — every mutation runs inside
     try/finally. No change may ever be left behind.
4. **Print a final table**: rule, CAUGHT or MISSED, plus a count of each.
5. **Verify cleanliness**: `git status` and `git diff` on the touched files
   must show nothing.
6. **Handle MISSED results**: in plain English, say what each gap means, then
   either write a test that catches it or explain why it is genuinely
   redundant (e.g. the framework already enforces it). Re-run the script until
   every MISSED is resolved or consciously accepted.
7. **Deliver** the final table plus the commands to run, one at a time.

## Standing rules for the agent doing it

- Banks is a beginner: plain English, explain every technical term at first use.
- Never invent rules. If unsure a check exists, read the code and cite the line.
- Local testing only. Never run a break-it against live sites, real customer
  data, or production anything.
- The break-it script and any mutation of code live in a copy or get restored
  within the same step. The working tree ends every run exactly as it started.
