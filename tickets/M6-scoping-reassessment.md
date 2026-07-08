# M6 — Taxonomy + registry reassessment (DEFERRED — do not build yet)

**Status:** stub. Captured so the design isn't lost. **Not in MVP scope.**

## The problem it solves

M0 does the **initial** stand-up (procedure set + `_reference/` registry) from
the first sources. M6 is the **incremental** counterpart: when *new* sources
arrive later, reassess both — add/split/merge/reorder procedures **and** propose
registry additions (a newly-mentioned system, a new role, a new alias). Genuine
judgment (an agent), distinct from M5 which only reacts to content changes within
an already-decided set.

## Why it's deferred

- The base pipeline (M1–M4) must be solid first; reassessment on top of a shaky
  splitter/aggregator would compound problems.
- The can-of-worms risk (renumbering churn) is already defused by the
  identity/number split in `tickets/README.md`: identity = stable slug, number =
  derived. So M6 can be added later without destabilizing existing files.

## Sketch (not a spec)

- A scoping agent reads new/changed sources and proposes a procedure set (slugs +
  short titles + suggested group).
- Diff proposed slugs against existing manifest procedures: **new** → create a
  fragment + manifest entry; **missing** → flag for human (never auto-delete a
  human-authored procedure); **split/merge** → propose, human confirms.
- Registry reassessment reuses M3's "unmatched mention" WARNINGs as the trigger
  list: each flagged system/role is a candidate registry addition for the human
  to confirm.
- For the MVP, M0 proposes the initial set + registry once (human-confirmed);
  there is no automated reassessment.

## Acceptance

Deferred. Do not implement until M1–M5 are complete and exercised on a real area.
