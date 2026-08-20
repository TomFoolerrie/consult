# M63 — Fail-loud edges: three silent drops become refusals or reports

**Status: RECORDED** (not scheduled).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-21, F-22, F-23.

## Why

The repo's own doctrine is fail-loud — a permanent audit exists to
enforce it structurally — yet three edges still drop content with
exit 0:

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
   log, and the screenshot index, with no diagnostic.

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
listing the offending procedures and the known order — the same
posture the taxonomy hygiene checks already take upstream. (If a
deliberate "unfiled" bucket is ever wanted, that is a definition-space
decision, not a silent drop.)

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
- Full suite + compat gate untouched.
