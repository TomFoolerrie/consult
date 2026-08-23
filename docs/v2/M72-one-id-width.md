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
   carries 33 three-digit id occurrences against 7 two-digit (counts
   corrected per review): the worked examples (lines 538–588, plus
   608/612 and the citation-grammar block at 754–770) run 3-digit
   while the callout-shape reference block (626–663, plus 807/836)
   runs 2-digit. An agent reading the examples nearest its task
   copies what it saw. Three did. **Thirteen of the 33 are `SRC-nnn`
   and are CORRECT AS THEY ARE** — see the sweep boundary below.

2. **The skeleton fallback seeds 3-digit.** The seeded examples are
   `CTRL-001` (`scaffold.py:755`) and `PP-001` (`scaffold.py:759,
   764`) in `_FALLBACK_PART_BODIES` (`scaffold.py:727`) — a SHARED
   dict: `keep_sections(_fallback_skeleton(…))` serves the v1
   activity type too when `PROCEDURE_SKELETON` is absent
   (`scaffold.py:906`), so edits here touch both types. It is why all
   nineteen run-2 fragments carry 3-digit CTRL ids while GAP split
   16/3: the strongest style signal in the area is the one WE wrote
   into every skeleton. The process-step sweep targets are the
   `controls` and `issues` bodies (process-step has no `steps` part).

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

One width: **2-digit local CALLOUT ids** (`GAP-01`, `CTRL-01`), the
width the display transform already speaks and the majority reading.

**THE SWEEP BOUNDARY (per review — HIGH):** the rule covers CALLOUT
prefixes only — the declared set derived from `LABEL_TO_PREFIX`
(`callouts.py:12–25`: CONTROL/PP/IO/GAP/SC today). **`SRC-` ids are
NOT callouts and NOT swept**: the engine mints them 3-digit
(`engagement.py:757`, `f"SRC-{…:03d}"`), and 13 of the drafter
contract's 3-digit ids are SRC citations that are correct as they
stand. A sweep that touches them puts the contract at war with the
minter. The width rule sentence names the boundary explicitly.

Then:

- `consult-drafter.md`: every CALLOUT example id in the contract —
  worked examples, shape blocks, citation-grammar lines — uses
  2-digit; SRC examples stay 3-digit. One sentence in the
  callout-shape block states both rules outright ("local callout ids
  are 2-digit, `-01` up; `SRC-` ids are engine-minted 3-digit"), so
  the rule is declared, not inferred from examples.
- `_FALLBACK_PART_BODIES`' seeded examples (`CTRL-001` at
  `scaffold.py:755`, `PP-001` at 759/764) become 2-digit. This dict
  is shared with the v1 fallback path — the compat gate (byte-level
  v1 golden) is the arbiter: if v1 golden output embeds these seeds,
  the build splits the dict per type rather than editing shared
  bytes; if the seeds never reach v1 golden output (skeletons are
  drafted over), the edit is safe as-is. Builder verifies, amendment
  records which.
- **The v1 skeleton file gets an explicit ruling, not silence** (per
  review): `skills/consult-drafter/reference/procedure_skeleton.md`
  itself mixes widths (`GAP-01`/`SC-01` at 81/85 vs
  `CTRL-001`/`PP-001` at 98/110/115) — the exact defect, in the file
  v1 areas stamp from (`scaffold.py:891–892`). RULING: it stays
  byte-identical — v1 output is law and the file is v1's stamp
  source. The one-width rule is v2-prospective; the v1 skeleton's
  mixed widths are recorded here as known-and-accepted, harmless for
  the same reason run 2 was (display re-mints).
- The tolerance stays: the grammar and `callout_display_ids` continue
  to accept both widths, pinned by test, so the three existing
  3-digit fragments (and any client area like them) never break. The
  rule is prospective style, not retroactive validation — reconcile
  gains NO width check.

## The gate

- Grep-shaped test: no 3-digit CALLOUT-prefix example id in
  `consult-drafter.md` or in the process-step skeleton seed text;
  `SRC-` 3-digit examples still present (the boundary pinned from
  both sides).
- `callout_display_ids` over a fixture mixing `GAP-01` and `GAP-001`
  locals: both map to sequential 2-digit display ids (behavior exists
  today, uncovered).
- The declared width rule appears in the drafter contract (asserted as
  presence, not prose).
- Full suite + compat gate untouched; v1 skeleton bytes unchanged.
