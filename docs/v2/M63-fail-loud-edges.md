# M63 — Fail-loud edges: three silent drops become refusals or reports

**Status: BUILT** (`2.4.0-alpha.8`, gate 8/8 — see Amendment A1).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-21, F-22, F-23 — plus a fourth defect found while
fact-checking this ticket line (the discarded `validate_manifest`
return, item 4 below).

## Why

The repo's own doctrine is fail-loud — a permanent audit exists to
enforce it structurally — yet four edges still drop content or defects
with exit 0:

1. **`split_doc` discards front matter** (`split_doc.py:132`).
   On import, everything before the first `##` except the H1 title and
   the first italic subtitle line is written to no fragment and
   mentioned in no output — scope paragraphs, preambles, disclaimers,
   gone without a note.

2. **One unknown bookmark silences every deletion warning**
   (`review_apply.py:620`). The untracked-deletion sweep reports a
   vanished map anchor only `if bm not in seen_bms and not unknown_bms`.
   The `not unknown_bms` guard — meant to avoid double-reporting — is
   GLOBAL: a single renamed or corrupted `cw_` bookmark anywhere in the
   document suppresses the warning for every genuinely vanished anchor.

3. **`aggregate` drops procedures with an unlisted L2**
   (`aggregate.py:858–861` grouping vs 391, 475 iteration). Grouping
   accepts any `l2`, but every L2-grouped builder iterates only
   `ctx['l2_order']` — a procedure filed under an L2 absent from that
   list vanishes from the procedure index, both appendices, the gap
   log, and the screenshot index, with no diagnostic from aggregate
   itself. (`doc_model.validate_manifest` DOES report an unlisted L2 —
   `doc_model.py:136–139` — and reconcile surfaces it at
   `reconcile.py:990`; the rule exists, aggregate just doesn't run it.)

4. **`render` calls the validator and throws away its answer**
   (`render.py:852`). The "M14 enforcement point 2" line reads
   `doc_model.validate_manifest(manifest)` — but `validate_manifest`
   returns a `list[str]` of errors and never raises, so the call is a
   no-op: a manifest defect that reconcile would refuse sails through
   the render unexamined. Found while fact-checking this ticket line,
   not in the original review.

## The shape

### Part A — front matter is preserved or refused

`split_doc` writes unconsumed front-matter body to a dedicated
fragment (`_front-matter.md` in the split output, round-tripped by the
consolidator) — or, if the ruling is that v2 documents must not carry
free front matter, refuses the import naming the lines it will not
carry. Either way the import reports what it did with those lines;
silence stops being an option.

### Part B — the warning guard goes per-anchor

`review_apply` reports each vanished tracked anchor unless THAT anchor
is accounted for; unknown bookmarks are reported separately as their
own defect ("bookmark present in document but absent from map"). Two
lists, no cross-suppression.

### Part C — aggregate refuses the unlisted L2

An `l2` outside `l2_order` fails the aggregate with a named error
listing the offending procedures and the known order — by RUNNING the
rule `validate_manifest` already owns (`doc_model.py:136–139`), not by
minting a parallel one. (If a deliberate "unfiled" bucket is ever
wanted, that is a definition-space decision, not a silent drop.)

### Part D — the render's validator call gets teeth

`render.py:852` consumes the return: a non-empty error list fails the
render naming every error, matching the enforcement-point comment that
already sits above the call. Survey the tree for other discarded
`validate_manifest` returns while there (reconcile's is consumed; any
other bare call gets the same fix).

## The gate

- Import fixture with two paragraphs of front matter: both reachable
  in the split output (or refusal naming them); consolidate → render
  round-trips them.
- Review-kit fixture with one corrupted bookmark AND one genuinely
  vanished anchor: both reported, distinctly.
- Aggregate fixture with a procedure under an unlisted L2: named
  failure listing procedure and L2; with the L2 added to `l2_order`
  the same fixture passes and the procedure appears in index,
  appendices, gap log.
- A manifest defect `validate_manifest` reports (e.g. the unlisted L2)
  fails the render with the error text; a clean manifest renders as
  before.
- Full suite + compat gate untouched.

## Amendment A1 — build rulings (2026-08-20)

* **Part A's "preserve or refuse":** preserve — leftover front-matter lines
  become a `00_front-matter.md` static component (heading "Front Matter",
  order 1, ahead of the band-10 procedures), so consolidate → render carries
  them; the import prints how many lines it preserved and where.
* Part B's rename case now reports twice (unknown bookmark + vanished map
  anchor) — accepted per the two-lists-no-cross-suppression rule; the
  pre-existing corrupted-bookmark test was updated from `noted == 1` to the
  three distinct reports.
* Part C runs the FULL `validate_manifest` in aggregate (not just the L2
  rule): fail-loud doctrine, and the rule stays owned in one place. The
  refusal appends the known `l2_order` after the validator's own error lines.
* Part D survey: scaffold (×2), definitions and reconcile already consume
  the return; render.py:852 was the only bare call. Fixed.
