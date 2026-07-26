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

---

# Part 2 — workflow cycles

Realistic engagement workflows run against the built area. Same method: build the
state, ask `decide()`, run the stages it routes to.

Verified working: a reviewer kit landing in `_review/returned/` routes to
`ingest_returns` (guard 1.5); re-stamping the `unfilled` sentinel by hand
correctly forces a re-draft of one procedure via guard 4.

## F7 — A new source that only enriches existing procedures never converges — **high**

The designed behaviour is stated at `docs/README.md:60` — a new file in
`_sources/new/` "triggers reassessment (M6) and re-dispatch of the drafters it
touches." M6 is DEFERRED (`:459`), and this is what the gap does.

Guard 4 dispatches on the `unfilled` sentinel, which only new skeletons carry.
An already-drafted procedure a new source `touches` has no sentinel and no note,
so nothing dispatches an update drafter for it. Measured:

```
drop new source → taxonomy (incremental) → confirm → scaffold creates nothing
               → taxonomy (incremental) → taxonomy (incremental) → ...
mark-processed --filled <slug> → moved 0 source(s)
```

The source cannot retire (`touches` never becomes a subset of newly-filled
slugs), so guard 5 re-fires forever, re-spending a taxonomy dispatch per lap.

**Direction.** Incremental taxonomy writes a `_review/{slug}.notes.yaml` per
touched *existing* procedure, so guard 2 dispatches update drafters for exactly
the mapped slugs. Two consequences: `apply_review`'s dispatch carries no
`sources` list by design, so the note must carry the `SRC-` id for the drafter to
resolve; and `mark-processed --filled` must count successful *update* slugs, or
the source still never retires.

## F8 — Retiring a procedure deadlocks the ladder — **high**

Removing a procedure from the manifest leaves `[[slug]]` references behind.
Python-derived views regenerate clean, but two classes do not:

- **sibling procedures** (`10_goods-receipt.md`, `10_po-invoice-…`) — drafter-owned
- **agent-derived views** (`82_dependencies.md`, `84_raci.md`) — agent-owned

`reconcile.py` correctly reports every dangling reference and exits 1, so
`decide()` returns `reconcile` forever. The deadlock is an **ordering** one:
`scope_delta` reports all remaining procedures stale, so `synthesize` (guard 9)
would regenerate `82`/`84` — but `reconcile` (guard 8) precedes it and never
clears. The verifier runs before the producer that would satisfy it. The sibling
procedures need drafter updates, which need notes that nothing writes.

Retiring a procedure is therefore a hand-edit operation with no support, and the
orphaned fragment left on disk is never noticed by any component.

## F9 — A registry rename leaves every procedure's prose stale, silently — **medium**

Renaming a canonical system (`name: NetSuite` → `Oracle NetSuite ERP`, old name
kept as an alias — the designed path) regenerates the Systems view via slug
bindings, while all fifteen procedures keep saying "NetSuite" in prose.
`aggregate` exits 0 with **no** unmatched-mention warning, because the old name is
still a legitimate alias. The deliverable ships with the table and the steps
disagreeing.

This follows correctly from the two-database design (identity by slug, prose as
plain text) — the gap is that no workflow re-words prose after a rename. M12
cannot supply it: its `naming` rule is a mechanical majority, and here the
majority *is* the old name, while alias-matching classifies it as a legitimate
synonym warranting no dispatch.

## F10 — `--mode final` overwrites the review signal — **medium**

Final-mode render writes the same `.render.json` as working mode: it sets
`awaiting_review: true` again and replaces `docx` with the client-facing file.
So producing the deliverable re-opens the review gate, silently discards an
`accept` that already happened, and points the recorded artifact at the final
export. The signal has no `mode` field, so working and final are
indistinguishable afterwards.

**Direction.** `--mode final` should behave like `--slugs` and never write the
signal — it is a terminal export, not a state transition.

## F11 — No cross-area orchestration — **informational**

`next` requires a single `--area`. A six-area engagement means running the
advisor six times with no combined view of what is outstanding. M13 shares
client *config* across areas; nothing shares *orchestration*.

---

# The pattern behind F1, F7 and F8

All three are one failure mode: **`decide()` returns an action that cannot change
the state it was chosen for.** An orphan note routes to a drafter with no
procedure; a source touching only drafted procedures routes to taxonomy that
proposes nothing new; dangling references route to a reconcile that cannot
regenerate what holds them.

The invariant worth enforcing: *an action is only returnable if executing it can
change the state that selected it.* When nothing satisfies that, the correct
result is a **gate naming what the human must do** — never a stage that will be
re-selected unchanged on the next call. `review_triage` is already this shape and
is the model to follow.

---

# Part 3 — invariant enforcement

A second sweep (five lenses over the ticket set and code, high-severity claims
adversarially verified) asked a different question: which of the invariants the
docs state are actually enforced by code? Method as before — every claim below
was checked against the named files, not inferred.

**Result: the constitution is prose.** The core invariants are stated in
`docs/README.md` and restated in tickets, and almost none has a mechanical check:

- **F12 — One writer per file (docs/README.md:242): unenforced.** Every subagent
  carries an unscoped `Write` tool (`agents/consult-drafter.md`,
  `consult-raci.md`, `consult-dependencies.md`), and reconcile checks only that a
  derived file contains a `<!-- derived:` marker — the marker's kind and writer
  are never compared against the manifest's `derived_kind`/`writer`. A drafter
  overwriting a sibling's fragment or a Python-owned view passes every gate.
- **F13 — Evidence traceability: decorative.** `grep -r 'SRC-' scripts/` matches
  nothing. No script parses, validates, or joins an SRC- citation; a fragment
  citing a nonexistent `SRC-99`, or citing nothing at all, passes reconcile and
  renders. The system's headline claim rests entirely on drafter-prompt prose.
- **F14 — `touches` slugs unvalidated → a new livelock.** No code checks
  `sources.yaml` `touches` entries against manifest slugs. `mark_processed`
  retires a source only when `touches ⊆ filled` (`scripts/sources.py:86-90`), so
  one typo'd slug makes a source permanently unretirable; guard 5 then re-fires
  `taxonomy` forever — the same shape M18 forbids, selected by a state M18 does
  not enumerate. Survives M6 as specced.
- **F15 — The heading contract ("the one rule", docs/README.md:139-142):
  unchecked.** A fragment beginning `# Title` sails through parse, assemble, and
  every gate.
- **F16 — Baked display numbers: unchecked.** Nothing detects `see 2.1` written
  in prose instead of `[[slug]]` — the exact defect the r1→r2 revision existed
  to eliminate, silently stale on the first reorder.
- **F17 — Callout IDs quoted in agent-view prose: unchecked.** Reconcile
  validates IDs in derived-table rows only; an ID quoted in `82`/`84` prose is
  not display-transformed at render and disagrees with the document's numbering.
- **F18 — Credibility guardrail (registry descriptions "never invented"):
  prompt-only, and currently uncheckable** — registry entries have no citation
  field for a validator to read. Recorded as a schema gap, not an M22 check.

Also verified in this sweep, recorded for later work (not invariant
enforcement): review rounds have no bookkeeping (kit index destroyed on each
render, git-ignored, no sent/returned state); per-person kits do not compose
across areas; M17's gate as first specced re-keyed on `basis_hash` and demanded
two accepts per pass (fixed in the ticket); `mark-processed` counting was
kind-blind across the five notes producers (fixed by M6's bus contract); no
structural run-to-run diff exists anywhere, and uuid4 `.maps/` names plus
display-ID cascades guarantee raw git diff between build branches is
noise-dominated.
