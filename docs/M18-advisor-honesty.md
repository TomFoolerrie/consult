# M18 — Advisor honesty (the resolvable-action invariant)

> **Status: DESIGNED.** No dependencies. Fixes three reproduced livelocks.
> Evidence: `docs/audit-decide-exhaustiveness.md` (F1, F3, F4, F6, F8).

## Goal

Make `decide()` incapable of two lies:

1. returning an action that **cannot change the state that selected it** (three
   reproduced livelocks), and
2. reporting a **reassuring** state it has not actually verified (a nonexistent
   area reads as `done`).

## Why

`decide()` is a total function: twelve guards, first match wins, and every state
maps to *some* action. That is the defect. When no action can resolve a state, the
ladder still picks one, and the driver runs it forever against unchanged input.

Three instances, each reproduced:

| Finding | State | Action returned | Why it can't help |
|---|---|---|---|
| F1 | `_review/x.notes.yaml` with no matching manifest slug | `apply_review` | drafter has no procedure to update; notes archive only on success |
| F7 | new source touching only already-drafted procedures | `taxonomy` (incremental) | proposes nothing new; source can never retire (see M6) |
| F8 | procedure retired, `[[slug]]` refs remain | `reconcile` | reconcile verifies, it cannot regenerate what holds the refs |

F1 is the worst in practice: guard 2 outranks **every** other guard, so on a
brand-new area one stray notes file diverts `taxonomy` → `apply_review` and the
area can never be scoped at all.

`review_triage` already has the right shape — a gate that says "this needs a
human, not a dispatch." The fix generalizes it rather than inventing anything.

## Design

### The invariant

> An action is returnable only if executing it can change the state that selected
> it. When nothing satisfies that, return a gate naming what the human must do.

New terminal result **`unresolvable`** (`human_gate: true`) carrying the evidence:
the state detected, why no stage can clear it, and the specific human action that
would. It is a resting gate like `review`, not an error — the folder is
consistent, the *ladder* is out of moves.

### Guard 2 — partition the notes queue (F1)

`review_notes()` gains a manifest-slug check and returns two sets. Notes matching
a live procedure route to `apply_review` as today. Orphans route to
`review_triage`, whose contract already covers "reviewer material that needs a
human." The triage message names the orphaned slug and the two legitimate
resolutions: restore the procedure, or archive the note.

Additionally: **guard 2 must not outrank guard 3 when there is no manifest.**
Nothing can be applied to an unscoped area, so scoping wins.

### Guards 8 and 9 — verifier must not precede its producer (F8)

The deadlock is ordering, not logic. `reconcile` (8) blocks on dangling
`[[slug]]` references that `synthesize` (9) would regenerate — measured:
`scope_delta` reported all 14 remaining procedures stale, so the producer was
ready and unreachable.

Fix: when reconcile's failures are **confined to agent-derived files** that the
change signal already marks stale, `synthesize` takes precedence — the producer
runs, then reconcile re-verifies. If failures touch **procedure fragments**
(drafter-owned, as they also did in the measured case), no stage can fix them:
that is `unresolvable`, naming the files and the references.

This stays a pure function — "which files hold the failures" is already in
reconcile's output, and staleness is already in the `scope_delta` baseline.

### `resolve_area` — a missing area is not `done` (F3)

`resolve_area()` returns `components/<name>` whether or not it exists, so a typo
reports `done` with *"no manifest and no sources to scope"* — the most reassuring
possible output for an area that is not there. Distinguish the two cases and
return an error result for a nonexistent folder.

### Diagnosis fixes (F4, F6)

- A manifest slug whose fragment file is **absent** currently yields `aggregate`
  with reason *"content changed."* No corruption follows (`aggregate.py` exits 1
  without writing its signal), but `next` points at the wrong cause. Detect it and
  name the slug and the missing file.
- Guard 9's `except` sets `stale_kinds = []`, discarding kinds already detected
  before the failure. Accumulate per kind and let one kind's failure not erase
  another's.

## What this deliberately does not do

It does not make the ladder smarter about novel states — it makes it **honest**
about them. `unresolvable` is the seam where judgment belongs: the orchestrator
may reason about such a state, run scripts, and write notes, but never invent a
stage or write a fragment. Keeping the advisor deterministic is what made these
findings auditable in the first place.

## Acceptance

- An orphan notes file yields `review_triage` naming the slug — never
  `apply_review`; and on an unscoped area with sources waiting, `taxonomy` still
  wins.
- Retired procedure with dangling refs only in `82`/`84`: `synthesize` runs, then
  reconcile passes. With refs in a procedure fragment: `unresolvable`, naming
  file and reference.
- A nonexistent area returns an error, not `done`.
- A manifest slug with no file names the slug and the file.
- One kind raising in guard 9 does not suppress another kind's staleness.
- No state returns the same non-gate action twice with the folder unchanged —
  asserted over the audit's state corpus.
- `next` remains read-only: `git diff` empty after any call.

## Out of scope

- Replacing the ladder with agent judgment (see the audit's closing section).
- M6's incremental re-dispatch (F7) — this ticket only stops the lie; M6 supplies
  the missing capability.
- Retirement as a supported workflow — M6.
