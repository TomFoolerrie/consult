# M54 — Table-row comment routing: the pinned xfail gets paid

**Status: SPECCED** (backlog line, unscheduled — build on the human's go).
Origin: M38 A1 item 3 — matrix cell edits and the view-rebuild loop all
prove out, but ROW-LEVEL comment routing lands in `_unassigned`; "the
exact fix (table-row first-cell slug resolution) is pinned as a strict
xfail and needs its own small ticket with v1 appendix-table routing
characterized first." This is that ticket. The suite's one standing
xfail (`tests/test_matrix_roundtrip_m38.py`) retires here.

## Why

A reviewer who drops a Word comment on a matrix ROW (not a cell) is
addressing the step that row renders — the return trip should re-dispatch
that step's drafter. Today the comment cannot be attributed and falls to
`_unassigned`, which means a human re-routes it by hand: the one leak in
an otherwise deterministic review loop.

## The shape

### Part A — characterize v1 appendix-table routing FIRST

Before any change: characterization tests over the v1 appendix-table
comment path (the nearest existing table-routing behavior) pinning
exactly what it does today — including any quirks. These are new tests
over old behavior; they exist so Part B provably changes matrix routing
and nothing else. If characterization reveals the v1 path shares code
with the matrix path, the ticket STOPS for a spec amendment before
touching the shared line.

### Part B — first-cell slug resolution

A comment anchored to a matrix table row (or to text within a row-spanning
range) resolves to the step slug rendered in that row's FIRST CELL — the
mechanical identity the matrix build already writes. Resolution failures
(no slug in the first cell, a malformed anchor) still land in
`_unassigned` — the fix narrows the leak, it never guesses. Cell-level
routing (already working) takes precedence when both could apply.

### Part C — the xfail retires

The strict xfail in `tests/test_matrix_roundtrip_m38.py` flips to a
positive assertion — the licensed edit this ticket exists for. The
routing behavior lands in whichever module owns comment routing today
(kits.py's territory); no new module.

## Test impact

New gate: `tests/test_table_routing_m54.py` (characterization Part A +
positive routing Part B; committed with this spec, skip-gated on the
resolver existing). Licensed edits: exactly one — the M38 xfail flip.
**Zero v1 tests change** (Part A's characterization tests are NEW tests
pinning v1 behavior, not edits; if they cannot pass against today's tree,
the quirk is recorded and pinned as-is).

## Acceptance gate

`tests/test_table_routing_m54.py`: v1 appendix-table behavior pinned
byte-identical before and after; a row-anchored comment routes to the
first-cell step slug; a first cell without a slug still lands
`_unassigned`; cell-level routing unaffected; the M38 strict xfail is
gone and its scenario asserts positively; suite green with zero xfails.
