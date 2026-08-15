# M40 build plan — definition views to manifest

> Foundation for [`M40-definition-views.md`](M40-definition-views.md).
> Deterministic gate: `tests/test_views_m40.py` (skips until
> `scripts/plan_views.py` exists; materialize tests until the verb does).
> Ground rules as ever: exclusive file ownership, zero v1 tests edited,
> friction reported verbatim, the whole suite green before hand-back.
> The IPO fixture is the substrate (frozen; tests work on tmp copies).

## Design pins

- **The verb**: `definitions.materialize_views(area, name=None)` —
  plan-driven `scaffold.sync_profile` (READ IT FIRST; mirror its
  idempotence, preservation, and never-delete discipline). Six canonical
  keys per new derived component; file/order policy per the spec
  (max existing order + 10, then +1 per view, `<order>_<kind>.md`);
  existing kinds preserved byte-for-byte; manifest re-validated;
  refuses on cross-kind file collision; returns a delta report.
  compile_plan stays READ-ONLY — materialize is the one writer, and
  render_glue stays out of it (the M38 refusal is the law here).
- **The writers**: one module, `scripts/plan_views.py`, three builders
  (`build_information_requests`, `build_open_validations`,
  `build_findings_by_theme`), registered in `aggregate.PY_BUILDERS`
  (one import + three entries — the M38 mechanism, nothing else in
  aggregate changes). ctx contract: read `ctx["area"]`, optional
  `ctx["bindings"]`; derive the engagement root the way the existing
  machinery does (read engagement.py for a helper first). Vocabulary
  through bindings + declarations ONLY (matrix_views' discipline);
  target: zero shape-audit allowlist entries. Findings reached only
  through `findings.renderable`/`by_theme` (accepted-only structural).
  `thin` collapses where definitions.py documents the alias — expose a
  tiny helper there if needed (additive only).
- **Derived-view idiom**: bodies in aggregate's house style (lead-in
  line, tables or lists, `[[#slug]]` tokens only for slugs render.py can
  resolve in-area, `—` for empties). write_derived owns the file write.

## Work packages

### WP-V1 — the materialize verb
Owns the `materialize_views` addition to `scripts/definitions.py` (and
nothing else in that file beyond what the verb needs). May read
scaffold.py/doc_model.py; must not edit them.
Targets: TestMaterialize (7 tests). NOTE: the end-to-end class also
needs this package, but lands only when WP-V2 is in too.

### WP-V2 — the writers module
Owns `scripts/plan_views.py` (new) + the registry lines in
`scripts/aggregate.py` (import + three PY_BUILDERS entries — nothing
else in aggregate). May add ONE additive helper to definitions.py for
the thin alias ONLY if WP-V1 has landed first (else report the need).
Targets: TestOpenValidations, TestInformationRequests,
TestFindingsByTheme, TestRegistry.

### WP-V3 — end-to-end verification + audit sweep (orchestrator or agent)
No new files. Run the full suite; confirm TestEndToEnd passes with both
packages in; confirm the shape audit needed zero new entries; report
any friction verbatim.

## Sequencing
WP-V1 ∥ WP-V2 → WP-V3 → close-out (alpha.10): ticket status BUILT +
amendment, CHANGELOG entry, charter spine table row, version bump.
