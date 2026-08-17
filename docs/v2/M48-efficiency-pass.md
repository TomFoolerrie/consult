# M48 — The efficiency pass: split the drafter contract, audit the roster

**Status: BUILT** (`2.2.0-alpha.5`, gate 10/10, suite 1185 — zero skips
remain in the whole suite) — from the 2026-08-16 architecture review,
decision D6
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

For each remaining agent: keep, fold, or retire. **Resolved at close-out
(2026-08-16, as built)** — one ruling per row, applying the audit rule below.
No agent file was deleted in this ticket: every agent listed is either
dispatched today or protected by the v1 compatibility gate.

| Agent | Ruling |
|---|---|
| consult-taxonomist | **KEEP** — the M45 home: scoping, M6 reassessment and curation in one contract. Its CURATION dispatches now carry the cheaper-tier hint documented beside the revise tier in `skills/consult-orchestrate/SKILL.md` (grooming an existing callout population against the needs view is bounded judgment; SCOPING and ADOPT/ROUTE stay strong-tier). |
| consult-intake | **KEEP** — pure tagging, prompt smaller than the judgment it adds (relevance pointer + route/adopt call). Nothing to fold. |
| consult-drafter | **KEEP, SPLIT — built** (Part A). Shared law in `agents/consult-drafter.md`; the two unit paths in `agents/drafting/activity.md` and `agents/drafting/process-step.md`. A dispatch loads shared law + one path. |
| consult-raci / consult-dependencies | **FOLD WHEN THE v1 PIPELINE RETIRES** — not now. `synthesize` is the only dispatcher, and it is manifest-driven: on a v2 area the IPO Inputs/Outputs lines ARE the dependency arrows (`references` relations), so the dependencies view is derivable and the agent's remaining judgment is thin. RACI keeps a little more (performer vs. accountable is a read, not an edge). Both stay untouched while `synthesize` and its v1 views are law; the fold lands with the v1 retirement, not ahead of it. |
| consult-analyst | **KEEP** — separate by design behind the human gate (M39 license). Its missing dispatch path remains the recorded follow-up: `scripts/analysis.py` and the M39 contract exist, no skill passage dispatches it yet. Not this ticket's scope; carried as the standing analyst backlog item. |
| consult-consolidator | **KEEP** — dispatched by `consult-orchestrate` for the M12 within-area pass; the cross-procedure comparison it makes is not derivable from a script. |
| v1-only agents (consult-taxonomy, consult-placement) | **KEEP behind the compatibility gate — never retired here.** `consult-taxonomy` is still dispatched on v1/legacy areas and is named throughout `scripts/` (sources, scaffold, orchestrate); `consult-placement` retired as a *dispatch* at M45 (the taxonomist absorbed it) but the file stays for legacy/mixed-version engagements. v1 tests are law. |

The audit's rule: an agent survives only if it exercises judgment a script
or a definition cannot, and its prompt is smaller than the judgment it
adds.

## Amendment A1 — build friction (recorded at close-out, 2026-08-17)

1. **The token win is smaller than the ticket's framing:** only ~1,800
   words were v1-only and ~620 v2-only; ~7,700 words are shared law every
   dispatch still pays for (activity dispatch ~3% lighter, process-step
   ~14%). The real next cut, if wanted, is INTO the shared file — the
   callout grammar block, the M16-era update procedures, the
   return-format catalogue. Recorded as a candidate, not scheduled.
2. **`consult-placement` is the one plausible retirement:** M45 retired
   its dispatch, nothing in skills/ or scripts/ references it, no test
   greps it — it survives only for documented legacy/mixed-version
   routing. Reported rather than deleted, per the ticket's own rule.
3. **One single-home concession to test law:** the v1 callout grammar
   block (the old `Nature:` enum, `Owner to confirm:`) stays in the
   shared file because `test_needs_m44` pins the M44 unit-scoping
   passage there; doctrinally it belongs in `activity.md`. Move both
   together if that gate is ever revisited.

## Test impact (the licensed edits — verified by grep, 2026-08-16)

New gate: `tests/test_efficiency_m48.py` (committed with this spec, skips
until `agents/drafting/` exists). The gate pins the split's file names
(`agents/drafting/activity.md`, `agents/drafting/process-step.md`) and the
single-home rule: the M43 path heading and the v1 seven-section table move
whole to their path documents; the minting bars stay in the shared
contract and appear in neither path document.

Existing tests this ticket repoints — mechanical, same anchors, new path:

- `tests/test_hygiene_m43.py` — the `needs_path` gate and `TestDraftingPath`
  grep the drafter for the process-step path section; both repoint to
  `agents/drafting/process-step.md`.
- `tests/test_doctrine_m42.py` — **no change expected**: its anchors (the
  minting bars, the interaction contract, the worked example) are shared
  law and stay in `consult-drafter.md`. If the build finds one that is
  genuinely unit-specific, that is a spec amendment, not a silent move.
- `tests/test_needs_m44.py` — no change (its drafter anchors are the M44
  GAP bar, shared law).

**Zero v1 tests change** — verified: no v1 test greps the drafter
contract (only fixture notes and docstrings mention the agent by name).

## Acceptance gate

`tests/test_efficiency_m48.py` — written before the build: the three
drafter documents exist with disjoint normative content (no rule stated
twice — mechanical anchor checks); the brief's YOUR UNIT line names the
path document; a v1-area dispatch surface never references the process-step
path and vice versa; the orchestrate skill carries the revise-tier hint;
every M42/M43 prose gate green after repointing; the roster table above
resolved with a ruling per row at close-out.
