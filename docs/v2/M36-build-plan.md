# M36 build plan — the compatibility gate

> Orchestration foundation for
> [`M36-compatibility-gate.md`](M36-compatibility-gate.md) (read it: the
> four proof obligations, what must NOT happen, A1's normalized-XML
> ruling). Ground rules as ever; the extra one for this ticket: **v1 test
> files are read-only** — a failing v1 test means the re-expression is
> wrong, full stop.
>
> Starting point (M35 A1): render_glue proves plans EXECUTABLE with v1
> fidelity; this build owes assembly FROM plan.blocks. Known gap carried
> in: the shipped definition lacks an appendix-controls block.

## Work packages (sequential)

### WP-G0 — the golden harness (tests-side only)
Owns `tests/docx_compare.py` (new helper), `tests/test_render_golden_m36.py`
(new), `tests/fixtures/golden/` (new, committed reference).
- Normalized comparison per M36 A1: extract document.xml + styles +
  numbering from a .docx; strip volatile material (timestamps, rsids,
  revision ids, zip metadata/ordering); RETAIN text, element structure,
  ordering, numbering references, style references. Compare as
  canonicalized trees/strings with a precise first-difference report.
- Generate the golden ONCE from the frozen p2p fixture through the
  CURRENT v1 render path (tmp copy of the area; the fixture itself is
  never written) and COMMIT the normalized artifacts under
  tests/fixtures/golden/. Record the exact generation command in a
  README beside them.
- The golden test: render the fixture (tmp copy) fresh and compare to
  the committed golden — this pins v1 self-consistency TODAY and becomes
  the migration's tripwire.
- Harness self-test: corrupt a rendered docx three ways (a changed word,
  a reordered section, a renumbered item) and assert the comparison
  catches EACH with a named difference. Also: render twice and assert
  the normalized forms are identical (determinism check — if v1 render
  is nondeterministic anywhere, STOP and report what).

### WP-G1 — assembly from the plan (render side)
The docx is built FROM plan.blocks: block order/titles from the
definition, static text injected, entity-part part-selection and
body_omit honored, view blocks placed where the plan puts them.
Desktop-procedure definition over the fixture must render golden-equal.
Owns render-side modules (render.py may now change — the golden is the
guard); adds the missing appendix-controls block to the shipped yaml
(profile opt-in stops being a no-op).

### WP-G2 — the deterministic layer follows the definition
aggregate builds exactly the plan's python views (hard-coded list dies);
scaffold skeletons from the type declaration; scope_delta/render-signal
keyed per definition. Advisor replay equivalence over the fixture.

### WP-G3 — retirement + audits
Shims retired (doc_model table re-exports); the grep-level
shape-lives-in-data audit (no engine module outside kernel + docx
adapter names an activity part slug or callout label as a code
constant); landing note lists every import-path fix forced.

## Sequencing
G0 first and alone — its verdicts shape G1-G3's briefs. Then G1 → G2 →
G3, full suite + golden green at every package end.
