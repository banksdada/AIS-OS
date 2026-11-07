# Registry before build — where existing things live

Set by Banks 2026-11-07 after the ai-audit mix-up (proposed creating a repo
that already existed because it was not in the index).

## The rule

Before creating, deploying, or "scaffolding" anything that could already
exist, check in this order — and say out loud what you checked:

1. `projects/` in the AIOS — every active product/workstream has a README
   with its repo URL. If the thing is not there, it may still exist.
2. `git remote -v` across `~/Desktop/*/` (one loop) — local repos reveal their
   GitHub names.
3. `git ls-remote git@github.com:banksdada/<guess>.git HEAD` for plausible
   names — the SSH key answers without auth tooling.

Only after all three come up empty may an agent propose a new repo — and it
must show what it checked.

## The duty that goes with it

Discovery is not registration. When an agent finds or creates a project that
is not in the index, it *reports* it and asks whether to register — the
`projects/<name>/README.md` entry is only written when Banks says so (see
`project-registration.md`). The index is how the AIOS and future sessions
find things; a repo that exists only on GitHub is invisible from next time —
which is why registration is worth asking for, not doing silently.
