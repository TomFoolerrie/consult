# M52 — One taxonomist brief: the merged agent gets a merged work order

**Status: SPECCED** (backlog line, unscheduled — build on the human's go).
Origin: M45 A1 item 1 — the brief-assembly merge Part B described ("one
taxonomist brief") was not done; recorded as a follow-up "if the
two-dispatch pattern proves annoying in use". Writing the ticket now so
the shape is agreed before anyone gets annoyed.

## Why

M45 merged the surveyor and the librarian into one contract, but their
work orders still assemble on two code paths: survey dispatches read
`brief.py --objective` plus the coverage map; curation dispatches read
`engagement.py brief`. One agent, two brief grammars — the dispatcher
(orchestrate skill) must know which to run, and the two paths can drift
apart in what they tell the same agent about the same engagement.

## The shape

### Part A — the assembled brief

One verb — working name `brief.py taxonomist <area-or-root>` — prints the
merged work order in the brief.py idiom (deterministic, read-only,
deciding nothing):

- the objective block (both dispatch kinds aim at it);
- the coverage map summary (the survey kind's core feed);
- the grooming/needs feeds the curation kind reads today (including the
  `engagement-needs` render, its M44-designed consumer);
- the write-boundary restatement (live-node refinement in place; FRESH
  node sets stage under `.proposed/_taxonomy/` for the confirm gate;
  never delete a live node) — the M45 A1 item 2 split, said once;
- a DISPATCH KIND line the caller sets (`SCOPING` / `CURATION` /
  `ADOPT-ROUTE`), which selects emphasis, not content — one brief, the
  kind names what the agent is being asked to exercise.

### Part B — the two old paths converge

`engagement.py brief` and the survey-side assembly both delegate to (or
are replaced by) Part A's builder so there is exactly one place the
taxonomist's picture of the engagement is composed. Whether the old
entrypoints survive as thin aliases or are retired is a build decision —
retiring them is preferred if no test law pins their exact output;
aliasing is the fallback.

### Part C — the dispatch surface

`skills/consult-orchestrate/SKILL.md`'s taxonomist passages point every
dispatch kind at the one brief command (with its kind flag);
`agents/consult-taxonomist.md` names the brief as its first action (the
drafter/analyst contract pattern). The M48 tier hints (CURATION cheap,
SCOPING/ADOPT-ROUTE strong) survive verbatim beside the new command.

## Test impact

New gate: `tests/test_taxonomist_brief_m52.py` (committed with this spec,
skip-gated on the new subcommand existing). Licensed edits, enumerated at
build: any M37/M41/M45 gate that pins the OLD brief commands or their
output anchors repoints mechanically (same anchors, new assembly);
the build plan lists each by name before the first edit. **Zero v1 tests
change.**

## Acceptance gate

`tests/test_taxonomist_brief_m52.py`: the brief prints objective +
coverage + needs/grooming feeds + write boundary for both a survey-shaped
and a curation-shaped call; the kind line varies, the content does not
drift (the two kinds' briefs share their engagement picture verbatim);
exactly one assembly site exists (mechanical: the old assembly code is
gone or delegates); the skill and the contract name the one command; the
confirm-gate and one-writer anchors of M45's gate stay green.
