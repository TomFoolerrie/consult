# M6 — Scoping / taxonomy reassessment (DEFERRED — do not build yet)

**Status:** stub. Captured so the design isn't lost. **Not in MVP scope.**

## The problem it solves

Something has to decide *which procedures exist* in an area and reassess that set
as new source materials arrive — add a new procedure, split one in two, merge
two, or reorder. This is genuine judgment (an agent), distinct from M5, which
only reacts to changes in an already-decided set.

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
- For the MVP, the `consult-drafter` proposes the initial set by hand; there is
  no automated reassessment.

## Acceptance

Deferred. Do not implement until M1–M5 are complete and exercised on a real area.
