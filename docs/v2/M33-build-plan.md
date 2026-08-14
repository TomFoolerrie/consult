# M33 build plan — work packages for the kernel build

> Orchestration foundation for building
> [`M33-brain-kernel.md`](M33-brain-kernel.md). The acceptance tests are
> ALREADY WRITTEN (`tests/test_kernel_m33.py`) — they skip until
> `scripts/kernel.py` exists, then become the gate. **Build to the tests;
> never edit them.** If an implementation disagrees with a test, that is a
> spec conversation with the orchestrator, not a test edit.

## Ground rules (every work package)

- Branch: `v2`. Run `python3 -m pytest -q` before finishing ANY package —
  the pre-existing suite (803 tests + the fixture guard) must stay green.
- One writer per file: each package OWNS its files below; touch nothing
  owned by another package. Integration edits are the orchestrator's.
- The frozen fixture (`tests/fixtures/p2p-complete/`) is read-only. The IPO
  fragment (`tests/fixtures/ipo-fragment.md`) is read-only for implementers
  (its grammar is the contract).
- Style: match `doc_model.py` — stdlib(+pyyaml) only, dataclasses, module
  docstring stating ownership, fail-loud errors naming file + key.
- `console_compat` import first, like every other engine module.

## The API contract (what the tests pin)

```
kernel.load_type(name) -> TypeDecl            # from <repo>/kernel/types/<name>.yaml
kernel.load_type_file(path) -> TypeDecl       # same loader, explicit path
kernel.is_type_loaded(name) -> bool           # False after a refused load
kernel.TypeDeclError                          # names file + offending key
kernel.parse_entity(text, tdecl, slug=None) -> Entity
Entity.parts_bodies()   == aggregate.split_subsections(text)
Entity.bindings()       == aggregate.parse_consult_meta(text)
Entity.callout_dicts()  == aggregate.parse_callouts(slug, text)
Entity.duplicate_parts()== doc_model.duplicate_sections(text)
kernel.can_serve(requirements: dict, area) -> [error strings]

TypeDecl.parts     : ordered, each .slug .title .kind (+ optional aliases)
TypeDecl.title_aliases / .letter_aliases / .slug_aliases : dicts (v1 shapes)
TypeDecl.callouts  : each .label .prefix .home
TypeDecl.channels  : each .name .registry
```

Equivalence classes above mean EQUAL RESULTS BY DELEGATION where sensible:
wrapping the v1 implementation is correct M33 style (the heavy migration is
M36); a reimplementation that drifts from v1 output is wrong even if tests
pass.

## Work packages

### WP1 — type loader + `activity.yaml`
- **Owns:** `scripts/kernel.py` (TypeDecl, loader, registry, errors),
  `kernel/types/activity.yaml`.
- **Target tests:** `TestActivityParity`, `TestLoaderRefusals`.
- `activity.yaml` is v1 WRITTEN DOWN: derive every entry from
  `doc_model.SECTION_*` and `callouts.LABEL_TO_PREFIX`/`home_section` —
  the parity tests diff against those tables directly. Channels:
  systems→`systems.yaml`, roles→`roles.yaml`.
- Loader refusals must name the file and the offending key/value; a
  refused type never half-registers.

### WP2 — `parse_entity` (depends on WP1)
- **Owns:** the Entity dataclass + parse half of `scripts/kernel.py`
  (coordinate with WP1 if same file — orchestrator sequences, WP2 lands
  after WP1 merges).
- **Target tests:** `TestParseEquivalence` (runs over all fixture
  fragments).
- Correct approach: DELEGATE to `aggregate.split_subsections`,
  `aggregate.parse_consult_meta`, `aggregate.parse_callouts`,
  `doc_model.duplicate_sections`, dispatched through the type declaration
  (the activity declaration must reproduce v1 behavior exactly; a second
  type routes through the same generic paths driven by ITS declaration).

### WP3 — `process-step.yaml` + sub-step grammar (depends on WP1+WP2)
- **Owns:** `kernel/types/process-step.yaml`; may propose (not commit) a
  one-page sub-step grammar note for the orchestrator.
- **Target tests:** `TestProcessStepType` (the IPO fragment
  `tests/fixtures/ipo-fragment.md` shows the expected grammar: parts
  titled Scope/Inputs/Transformation/Outputs/Controls/Issues; numbered
  list inside Transformation = sub-steps; v1 callout syntax; pain kind =
  label `PAIN POINT`, prefix `PP`, home `issues` — the continuity ruling).
- The six part slugs and order are fixed by the M33 spec (A1 table).

### WP4 — `can_serve` (depends on WP1)
- **Owns:** the serviceability half of `scripts/kernel.py`.
- **Target tests:** `TestCanServe`.
- Pure function over declarations + area state; errors name the missing
  thing ("not yet" vs "never" distinction is M35's — here just precise
  strings).

### WP5 — back-compat shims + delegation audit (last; orchestrator-led)
- `doc_model.SECTION_TITLES` etc. re-exported from the kernel's activity
  type (or verified identical), so nothing off-spine breaks. Full 803 must
  pass; no v1 test edited.

## Sequencing

WP1 → WP2 → {WP3, WP4 in parallel} → WP5. Each package ends with the full
suite green and reports: files touched, tests now passing, any spec
friction encountered (verbatim — friction is design signal, not noise).

## Escalation rules for implementers

1. A target test seems wrong → STOP, report the disagreement; never edit.
2. The v1 modules disagree with the M33 spec → the v1 BEHAVIOR wins for
   the activity type (parity is the contract); report the spec gap.
3. Anything requiring a change to a file another package owns → report;
   the orchestrator integrates.
