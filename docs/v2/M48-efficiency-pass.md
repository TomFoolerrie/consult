# M48 — The efficiency pass: split the drafter contract, audit the roster

**Status: SPEC** — from the 2026-08-16 architecture review, decision D6
(ruled LOOKS RIGHT, with the human's note: **"If the revise drafter was
cheaper it makes more sense to have the drafter only touch the brain using
the notes workflow."**). Fifth of the review's five tickets.

## Why (the ruling)

Token efficiency. The drafter contract is ~1,048 lines and every dispatch
pays for all of it, though any one dispatch walks exactly one path: the v1
seven-section activity or the v2 process step (the M43 YOUR UNIT line
already tells the drafter which — it selects instructions that today all
travel together). Beyond the drafter, the roster carries propose-only and
one-trick agents whose whole job is smaller than their prompt.

## The shape

### Part A — split the drafter contract by unit

- `agents/consult-drafter.md` keeps the SHARED law: evidence discipline,
  canonical nouns, minting bars (M42/M44), notes routing, one-writer,
  return format.
- The unit-specific drafting paths move to two companion documents (e.g.
  `agents/drafting/activity.md`, `agents/drafting/process-step.md`); the
  YOUR UNIT line in the brief names which ONE to read. A dispatch loads
  shared law + one path, never both.
- Nothing normative is lost or duplicated: every rule lives in exactly one
  of the three files, and the M42/M43 prose gates are repointed
  mechanically (same anchors, new homes) where a section moved.

### Part B — the revise path (the human's note)

- The notes-driven revise pass gets its own slim dispatch surface: shared
  law + the notes-routing section + the one unit path, with a **model-tier
  hint** in the orchestrate skill (revise dispatches default to a cheaper
  tier; first drafts stay on the strong tier). The hint is dispatch
  documentation, not engine machinery.

### Part C — the roster audit

For each remaining agent: keep, fold, or retire — with the ruling recorded
in this ticket at close-out. Starting posture from the review:

| Agent | Posture going in |
|---|---|
| consult-taxonomist | new home (M45) — absorbs surveyor + librarian |
| consult-intake | keep (pure tagging, small) |
| consult-drafter | keep, split (Part A) |
| consult-raci / consult-dependencies | fold candidates — IPO edges made dependencies largely derivable (charter note); audit what judgment remains |
| consult-analyst | keep, separate by design (M39 license) — and give it the missing dispatch path (the backlog's analyst item rides along here or immediately after) |
| v1-only agents | keep untouched behind the compatibility gate |

The audit's rule: an agent survives only if it exercises judgment a script
or a definition cannot, and its prompt is smaller than the judgment it
adds.

## Acceptance gate

`tests/test_efficiency_m48.py` — written before the build: the three
drafter documents exist with disjoint normative content (no rule stated
twice — mechanical anchor checks); the brief's YOUR UNIT line names the
path document; a v1-area dispatch surface never references the process-step
path and vice versa; the orchestrate skill carries the revise-tier hint;
every M42/M43 prose gate green after repointing; the roster table above
resolved with a ruling per row at close-out.
