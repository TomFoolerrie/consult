# M54 — Table-row comment routing: the pinned xfail gets paid

**Status: BUILT** (`2.3.0-alpha.6`, gate 7/7, suite 1261 with ZERO
xfails — the standing M38 xfail retired here; see Amendments A0/A1).
Scheduled by the human 2026-08-18 ("all, in order"); last of the line
to land (M55 took alpha.5 by finishing first).
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

### Amendment A0 — the shared-line ruling (pre-build, 2026-08-18)

Part A's characterization triggered the stop condition: there is no
separate v1 table-routing path — v1 appendix tables and the matrix flow
through the one `extract_document` → heading-stack → `resolve_slug`
line. Ruled on the characterization's evidence:

1. **The first-cell rule is a FALLBACK, never an override:** it applies
   only when the heading stack yields NO slug. In-procedure tables (v1
   pain-point tables inside bodies) keep routing by heading stack —
   pinned by the characterization.
2. **v1 outcome-neutrality is provable and pinned:** v1 appendix first
   cells never resolve a slug (`PP-…` prefixes defeat number/title
   resolution), so their comments land `_unassigned` before and after —
   the gate's `test_v1_appendix_outcome_unmoved_by_the_resolver` is the
   evidence, and the v1 characterization tests must pass byte-identical.
3. **Row-wide semantics** (the M38 docstring's mapping): any cell in a
   matrix row resolves via that row's first cell under the fallback.
4. **Scope: comments and tracked changes alike** — they share the
   routing line, so the rule covers both; the gate exercises comments
   (the M38 gap scenario), and tracked-change coverage is noted as
   inherited, not separately pinned.

### Part B — first-cell slug resolution (as amended by A0)

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

## Amendment A1 — build friction (recorded at close-out, 2026-08-18)

1. **The raw matrix cell is not resolver-ready:** the step cell renders
   `"Title (N.N)"`, which `resolve_slug` does not accept as-is (the M38
   evidence test proved the KEYS resolve, not the raw text). The
   fallback tries the raw text, then reorders a TRAILING parenthesized
   number to `"N.N Title"` for one more resolve. Mid-text numbers (the
   v1 appendix's `"PP-33 (5.1) — …"`) never match, so the pinned v1
   invariance holds by shape, not by luck. No resolver change — only
   the fallback's input is normalized.
2. **The seam serves all three attribution points** (comment
   finalization, tracked-change emission, unterminated-range cleanup) —
   A0 item 4's comments-and-tracked-changes scope came out of the seam's
   location for free; the comment path snapshots the fallback at
   commentRangeStart beside the location snapshot.
3. Part A's characterization surfaced an undocumented working behavior
   worth knowing: v1 in-procedure pain-point tables already route
   correctly by heading stack — now pinned so nothing regresses it.

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
