# Audit — `decide()` exhaustiveness

Reachable folder states tested against the twelve guards in
`scripts/orchestrate.py:237`. Each finding below was reproduced by constructing
the state and calling `decide()`, then running the stage scripts it routes to.
No code was changed.

Guards behaving exactly as designed (verified, no action): dotfile-only
`.proposed/` is correctly ignored; notes outrank `fill` (H); `fill` outranks
incremental `taxonomy` (I); a manifest with zero procedures reports `done`.

---

## F1 — Orphan review notes halt an area permanently — **high**

`review_notes()` globs `_review/*.notes.yaml` with no check that the basename
corresponds to a manifest slug, and guard 2 outranks **every** other guard.
Notes are archived only after a drafter succeeds, so a note whose procedure does
not exist can never be cleared by the machine.

Reproduced:

- On a fully drafted area, three consecutive `next` calls all return
  `apply_review` — unchanged state, no progress.
- On a **brand-new area** with sources waiting and no manifest, adding one
  stray `.notes.yaml` diverts the action from `taxonomy` to `apply_review`. The
  area can never be scoped.

Not hypothetical: `review_extract.py` writes these files automatically, and
incremental `taxonomy` can retire or rename a procedure while notes for it are
still pending. That orphans the note and halts the area.

**Direction.** Partition guard 2's notes into those matching a manifest slug and
those that do not. Orphans belong at `review_triage` — the gate that already
exists for "reviewer material that needs a human, not a drafter dispatch" — never
at `apply_review`. Separately, guard 2 should not outrank guard 3 when there is
no manifest at all; nothing can be applied to an unscoped area.

## F2 — An empty fragment is indistinguishable from a finished one — **medium**

A zero-byte procedure file carries no `unfilled` sentinel, so `unfilled_slugs()`
skips it and guard 4 never re-fills it. Verified downstream: `aggregate.py` exits
0, and `reconcile.py` reports **"No blocking errors."** The procedure then
renders as an empty section.

So a drafter that crashes or is interrupted mid-write leaves a procedure the
system considers complete and empty, with no detector anywhere in the pipeline.

**Direction.** `reconcile.py` owns structural integrity and already parses every
fragment — a zero-byte or heading-only fragment should be a blocking error there.

## F3 — A typo'd area name reports `done` — **medium-low**

`resolve_area()` falls back to `components/<name>` even when that path does not
exist, so `decide()` on a nonexistent area returns action `done`, reason *"no
manifest and no sources to scope"* — the most reassuring possible output for an
area that isn't there.

**Direction.** Distinguish "the area folder does not exist" from "the area exists
and has nothing to do." The first is an error, not `done`.

## F4 — `decide()` misdiagnoses a missing fragment — **low**

A manifest slug whose file is absent is skipped by both `unfilled_slugs()` and
`proc_hashes()`, so guard 4 does not fire and the action becomes `aggregate` with
reason *"procedure/registry content changed since last aggregate."*

No corruption results — `aggregate.py` catches it properly (`ERROR: missing
procedure file …`, exit 1, signal file not written), so the pipeline stalls
loudly. The defect is only that `next` alone points at the wrong cause; the human
learns the truth by running the stage.

## F5 — Duplicate slug: blocked, with one signal gap — **low / informational**

`reconcile.py` catches it correctly (exit 1, naming both the duplicate `order`
and the duplicate `slug`), so the pipeline does stop.

The gap is upstream: `proc_hashes()` is a dict comprehension keyed by slug, so
with 16 procedure entries over 15 unique slugs it returns 15 hashes — one file's
hash is silently dropped, and guard 6 cannot see edits to the shadowed file.
`basis_hash()` appends per file and is unaffected. Matters only if reconcile is
bypassed; recorded as defense-in-depth.

## F6 — Guard 9 discards accumulated staleness on exception — **low**

In the `synthesize` guard, `stale_kinds = []` inside the `except` wipes kinds
already detected earlier in the loop. If `dependencies` was found stale and then
`raci` raised, both are dropped and `synthesize` fires only when `pending` is
non-empty.

---

## Reproduction

The harness that builds these states and prints the resulting action is not yet
in the repo (it lives in scratch). It is worth landing under `tests/` as a
regression suite — F1 and F2 are both the kind of defect that returns silently.
