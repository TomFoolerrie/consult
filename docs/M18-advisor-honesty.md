# M18 — Advisor honesty (the resolvable-action invariant)

> **Status: BUILT** (`scripts/orchestrate.py`; one call-site line in
> `scripts/reconcile.py`). Deltas from this design:
>
> - **`unresolvable` carries three named fields**, not prose: `details.state`,
>   `details.why_no_stage`, `details.human_action` (plus the evidence — files,
>   slugs, `dangling_refs`). `reason` repeats `state` so plain `next` output is
>   readable. `human_gate: true`, exit 0 — a resting gate, like `review`.
> - **Guard 2's partition keeps dispatching while any note is applicable.** A
>   live-slug note still returns `apply_review`; a coexisting orphan rides along
>   in `details.orphan_notes` and gates only once the applicable ones are
>   archived. `review_notes()` returns `(applicable, orphaned)`; the driver's
>   `details.notes` contract is unchanged. One case the design left open: an
>   **unscoped** area with notes and *nothing to scope* returns `review_triage`,
>   not `done` — reporting `done` with reviewer material on disk is the same lie
>   in a smaller room.
> - **F3 shape: `decide()` returns a new `action: "error"`** (guard 0, before any
>   state is read) and `next` exits **2**. It is deliberately NOT a gate: a gate
>   rests, and there is nothing here to rest on. `resolve_area()` is unchanged —
>   it still returns the `components/<name>` candidate for a name that was never
>   scaffolded, because `checkpoint` and the "not scoped yet" messages need to
>   name where the area *would* live. Existence became `decide()`'s question.
> - **F8's signal is files only.** `emit_reconcile(folder, clean,
>   failing_files=None)`; the key is omitted when None, so an older signal (or a
>   caller that does not track it) leaves guard 8 behaving exactly as before.
>   reconcile's single emit call site derives the list from its own error strings
>   (all are prefixed `<file>:` or `<file>:<line>:`); the messages stay in
>   reconcile. `decide()` re-derives the *references* itself for the gate message
>   via `callouts.XREF_RE`, so no grammar is restated.
> - **Guard 8 trusts only failures recorded at the CURRENT basis.** With a stale
>   basis the area has moved and re-running the verifier really can change the
>   answer, so it stays `reconcile`.
> - **A third F8 branch was needed.** Failures confined to agent-owned views but
>   with the change signal marking *nothing* stale would make `synthesize`
>   dispatch an empty work order — also a livelock, so also `unresolvable`.
>   Failures naming anything outside the drafter/agent split (`manifest.json`, a
>   python-owned view, `_reference/sources.yaml`) keep routing to `reconcile`:
>   those causes are fixable outside the basis (a registry edit re-stales
>   `aggregate`), so gating them would be its own lie.
> - **F4's gate sits after `fill`/`taxonomy`**, not before: real drafting work
>   still goes first, and the gate is what remains once it is done.
> - **F5 keeps the slug as the OUTER key** — `proc_hashes()` is now
>   `{slug: {file: sha}}`. Per-file inside the slug removes the collision (the
>   inner map mirrors `basis_hash()`'s per-file accumulation) while the slug stays
>   the identity every other component and test reads. A pre-existing
>   `.aggregate.json` in the old `{slug: sha}` shape compares unequal → exactly
>   one harmless `aggregate` pass rewrites it (tested).
> - **F6 was extracted, not patched:** `_synthesis_signal()` computes
>   `(pending, stale_kinds)` per kind once, and guards 8 and 9 share it.
> - **Not done here (out of ownership):** the driver skill
>   (`skills/consult-orchestrate/SKILL.md`) has no handler entry for
>   `unresolvable` / `error` yet, and `docs/M7-orchestrator.md` still shows the
>   pre-M18 precedence table and signal shapes.
>
> Evidence: `docs/audit-decide-exhaustiveness.md` (F1, F3, F4, F5, F6, F8).
> Tests: `tests/test_decide_states.py` (51 — the audit's state corpus A–O),
> `tests/test_advisor_honesty.py` (26 — one per acceptance bullet).

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
