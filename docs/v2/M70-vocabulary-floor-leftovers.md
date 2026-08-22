# M70 — Vocabulary-floor leftovers: the last floor-only prefix readers

**Status: BUILT** (`2.4.0-alpha.4`, gate 12/12 — see Amendment A1).
Origin: the v1-residue code survey run after M66's ruling. Small,
deliberately separate from M66: harmless for process-step today
(identical prefix set), but each one re-creates the M62 defect for
the first type that declares a new callout prefix.

## Why

M62 made the callout id grammar a function of the declared prefixes
(`callouts.id_strict_re(prefixes)`), keeping `ID_STRICT_RE` as the
floor-only constant for the compat-gated v1 path. Three readers still
hold the floor where declarations should flow:

1. `aggregate.py:259` and `reconcile.py:941` call the floor-only
   `callouts.ID_STRICT_RE` instead of `id_strict_re(declared)` — on
   a type declaring a new prefix (M62's own gate example, `RSK`),
   aggregate/reconcile would refuse ids the parser accepted.
2. `aggregate.py:489` and `render.py:192` re-type the alternation
   inline — `\b(?:CTRL|GAP|PP|IO|SC)-…` — instead of building it
   from `callouts.PREFIXES`/the declared set: two copies of the
   vocabulary that drift silently the day it grows.

## The shape

Every prefix alternation on the v2 path is BUILT from the loaded
declarations (the M62 seam); the floor-only constant remains only
where the compat-gated v1 path reads it, and each remaining caller
carries a one-line comment saying so. No behavior change for the
shipped five prefixes.

## The gate

- A test type declaring a new prefix: aggregate and reconcile accept
  its ids end-to-end (parse → aggregate → reconcile), matching the
  M62 parser gate.
- The two inline regexes are gone (asserted by grep-shaped test or
  by exercising the new-prefix fixture through those code paths).
- Full suite + compat gate untouched; the shipped five parse
  byte-identically.

## Amendment A1 — build rulings (2026-08-22)

* Prefixes alone would not have opened the gate: aggregate and
  reconcile also hard-code the LABEL->prefix map, so a declared RISK
  label was refused before its RSK id was ever tested. The fix
  threads one declaration-shaped `label_to_prefix` argument (the
  kernel twin's shape); prefix sets derive from it. Floor-only
  defaults keep every existing caller byte-identical.
* `callouts` grew the single alternation builder (`_prefix_alt`) plus
  `id_inline_re`/`id_mention_re`; aggregate/render/reconcile build
  from it. Alternation order is now sorted — provably matching-
  neutral since no prefix prefixes another (pinned by test).
* Sweep: `reconcile.py:978` was a third declaration-path floor reader
  (rewired); `reconcile.py:810` and `:1442` are genuinely
  floor/compat sites (commented as such); `kernel.py:329`'s noqa
  re-export of ID_STRICT_RE is dead and left for a future tidy.
