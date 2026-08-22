# M69 — The derived-view readers read the capture type: aggregate, kits, consolidate stop assuming activity

**Status: BUILT** (`2.4.0-alpha.7`, gate 14/14 — see Amendment A1).
Origin: the v1-residue code survey run after M66's ruling (Amendment
A2 names this split-out). Three consumers of drafted fragments key
their reads on ACTIVITY part slugs, so on a process-step area each
one goes quietly empty — no error, no warning, just missing
substance. M66 A2 item 1 gives them a type-driven parser; this
ticket makes them USE the right parts once they can.

## Why

1. **`aggregate` loses the substance of every step**
   (`aggregate.py:820–844`). The per-fragment ctx reads
   `sections["quick-reference"]` and `section_e = sections["steps"]`
   — parts process-step does not have — and never reads
   `transformation`. Guard 6 forces aggregate on every area, v2
   included, so the procedure index, role dictionary and RACI inputs
   are built from fragments whose actual content was never read.

2. **`kits` loses the preparer** (`kits.py:130–133`). The review-kit
   owner/escalation resolution reads `quick-reference`; `_step_of`
   (:91) keys on `####` step headings. On process-step both come up
   empty, so every kit's send-to contact resolution collapses.

3. **`consolidate` is blind to the process content**
   (`consolidate.py:78, 419, 461`). `PRIMER_SECTIONS = ("scope",
   "quick-reference")` and the digest's `steps` branch mean the
   M12/M48 cross-procedure consistency pass on a v2 area digests
   scope paragraphs only — `transformation` resolves to None and is
   dropped.

## The shape

All three key their part reads on the fragment's DECLARED type (the
tdecl parsing seam M66 A2 item 1 lands), with the part CHOICES made
explicit per verb:

- **aggregate**: the ctx carries the type's parts; the views read
  their natural homes — the index/role/RACI substance comes from
  `transformation` (+ `controls`) on process-step, from
  `steps`/`quick-reference` on v1 activity, chosen by declaration,
  not by hard-coded slug.
- **kits**: the preparer/owner source on process-step is declared
  data — the CONTROL callout's `Performer` field (declared on the
  type, `kernel/types/process-step.yaml`) and the roles channel —
  not a Quick Reference table that does not exist. Step location
  keys on the type's part structure.
- **consolidate**: primer and digest parts per type
  (`scope` + `transformation` on process-step).

v1 areas byte-identical throughout — same parts, same output.

## The gate

- A process-step fixture area: aggregate's index/role-dictionary/
  RACI inputs contain the transformation substance (non-empty,
  correct); kits resolve a preparer from the CONTROL Performer;
  consolidate's digest carries transformation text.
- Empty-read regression: the three verbs on a process-step area
  produce NO silently-empty view that a v1 run would have filled.
- v1 golden corpus + compat gate byte-identical.

## Amendment A1 — build rulings (2026-08-22)

* Landed as VIEW SLOTS (`kernel.view_parts(type)`): scope→scope,
  body→steps/transformation, at_a_glance→quick-reference/None,
  controls→controls — the one place a derived view asks which part
  fills a slot.
* Preparer/owner on process-step: declared CONTROL `Performer` (most
  frequent, ties by first) → roles channel; `reviewer` has no
  declared process-step home and stays honestly empty; `frequency`
  renders the explicit em-dash rather than a blank.
* Kits step location: `####` heading, else the enclosing part heading
  when the type's body is not v1's steps.
* Consolidate primer on process-step is `(scope,)` — NOT the ticket's
  literal `(scope, transformation)`, which would dump whole
  transformation bodies into the digest and break the module's
  context bound; transformation reaches the digest through the body
  branch (step headings, or a labeled 3-line opening digest), which
  still delivers the gate's "digest carries transformation text".
* Shape-audit allowlist updated to match reality: aggregate no longer
  names read-parts; kits' quick-reference literal is gone.
