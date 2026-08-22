# M70 — Vocabulary-floor leftovers: the last floor-only prefix readers

**Status: RECORDED** (2026-08-22).
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
