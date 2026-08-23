# M72 — One id width: our own contract text mints both

**Status: TICKETED.**
Origin: the second Nordhaven build run (audit 2026-08-23, finding 7.1).
Sixteen drafters minted 2-digit local callout ids (`GAP-01`); three
minted 3-digit (`GAP-001`, `goods-receipt` / `return-to-vendor` /
`vendor-master-maintenance`), and ALL nineteen minted `CTRL-001`.
The audit read this as three drafters diverging from the grammar. The
code reading says otherwise: the divergence is OURS.

## Why

1. **The drafter contract teaches both widths.** `consult-drafter.md`
   demonstrates `CTRL-001`, `GAP-002`, `GAP-011`, `PP-001` in eleven
   places and `GAP-01`, `SC-01`, `GAP-04` in eleven others — the
   worked examples (lines 538–588) run 3-digit while the callout-shape
   reference block (lines 626–663) runs 2-digit. An agent reading the
   examples nearest its task copies what it saw. Three did.

2. **The skeleton itself seeds 3-digit.** The process-step controls
   part's seeded example is `CTRL-001` (`scaffold.py:755`) — which is
   why all nineteen fragments carry 3-digit CTRL ids while GAP split
   16/3. The strongest style signal in the area is the one WE wrote
   into every skeleton.

3. **No correctness hole — established, so nobody re-fixes this as a
   bug.** The id grammar accepts any `[A-Z0-9]+` segment
   (`callouts.py:54–56`), reconcile is width-blind, and
   `doc_model.callout_display_ids` re-mints every id as a global
   2-digit display id keyed by `(slug, local-id)`
   (`doc_model.py:488–525`) — both widths render identically, and the
   run's fragments need no update dispatch. The defect is consistency
   of the record and the ambiguity we hand every future drafter, not
   the document.

## The shape

One width: **2-digit local ids** (`GAP-01`, `CTRL-01`), the width the
display transform already speaks and the majority reading. Then:

- `consult-drafter.md`: every example id in the contract — worked
  examples, shape blocks, citation-grammar lines — uses 2-digit. One
  sentence in the callout-shape block states the rule outright
  ("local ids are 2-digit, `-01` up"), so the rule is declared, not
  inferred from examples.
- `scaffold.py`'s process-step seeded example becomes `CTRL-01`; any
  other skeleton/agent/skill text minting a 3-digit example id in the
  v2 path is swept to match (activity-type v1 text untouched —
  compat surface).
- The tolerance stays: the grammar and `callout_display_ids` continue
  to accept both widths, pinned by test, so the three existing
  3-digit fragments (and any client area like them) never break. The
  rule is prospective style, not retroactive validation — reconcile
  gains NO width check.

## The gate

- Grep-shaped test: no 3-digit example id in `consult-drafter.md` or
  in the process-step skeleton seed text.
- `callout_display_ids` over a fixture mixing `GAP-01` and `GAP-001`
  locals: both map to sequential 2-digit display ids (behavior exists
  today, uncovered).
- The declared width rule appears in the drafter contract (asserted as
  presence, not prose).
- Full suite + compat gate untouched; v1 skeleton bytes unchanged.
