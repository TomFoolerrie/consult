# M35 build plan — the definition language

> Orchestration foundation for
> [`M35-deliverable-definitions.md`](M35-deliverable-definitions.md).
> Gate: `tests/test_definitions_m35.py` (skips until
> `scripts/definitions.py` exists). Ground rules as ever: branch `v2`,
> full suite green to finish, one writer per file, frozen fixtures
> read-only, NEVER edit existing tests, escalate friction verbatim.

## The API contract (what the gate pins)

```
definitions.DefinitionError                    # names file + offending thing
definitions.load_definition_file(path) -> Definition
definitions.load_definition(name, area=None) -> Definition
    # resolution: <engagement _client/deliverables/<name>.yaml> shadows
    # <plugin kernel/deliverables/<name>.yaml> (area=None -> shipped only)
definitions.serviceability(defn, area) -> [gap strings]   # stage 3: "not
    # yet" REPORT (kernel.can_serve under the hood), NEVER an exception
definitions.compile_plan(defn, area) -> Plan
Definition: .name, .shape (blocks: .id .title .kind .binding .repeat
    .numbering), .bindings, .skin (.format, .requires)
Plan: .views — ordered, each .kind + .writer (python|agent)
```

Loader stages (each refusal names file + offending key/id/value):
1. **Syntax** — top-level keys exactly {deliverable, shape, bindings,
   skin}; blocks need id/title/kind; kinds in {entity-part, view,
   static}; block.binding must name a defined binding; duplicate block
   ids refused.
2. **Vocabulary** — binding entities/parts/callouts/channels checked
   against kernel type DECLARATIONS (`kernel.load_type`), zero
   engagement needed.
3. **Serviceability** — `kernel.can_serve` per binding against a real
   area; returns gap strings (a "not yet"), never raises.
4. **Skin** — format must be a registered renderer; skin.requires ⊆
   that renderer's declared capabilities. This ticket registers ONE
   renderer: docx, with a small honest capability list (e.g. toc,
   portrait tables) — the registry mechanism matters, not the list.

## Work packages

### WP-D1 — loader + Definition + shipped desktop-procedure.yaml
Owns `scripts/definitions.py` (new) + `kernel/deliverables/desktop-procedure.yaml` (new).
Stages 1, 2, 4 (a static renderer-capability table is fine this
package), resolution/shadowing, and the shipped definition itself —
desktop-procedure.yaml is v1's document written down: blocks for the
static overview, the per-procedure entity-part body (repeat over
manifest order), and the eight derived views with their writers
(procedure-index/role-dictionary/systems/appendix-a/gap-log/
screenshot-index = python; dependencies/raci = agent), bindings drawn
from the activity type's vocabulary.
Targets: TestSyntaxStage, TestVocabularyStage, TestSkinStage,
TestDesktopProcedure::test_ships_and_loads, TestIndependence::
test_user_definition_shadows_shipped.

### WP-D2 — serviceability + compile_plan (extends definitions.py after D1)
Stage 3 via `kernel.can_serve` (per binding, aggregated, gap strings
carry the binding name); `compile_plan` — deterministic, read-only:
view blocks -> Plan.views in shape order with writers from the
definition; entity-part/static blocks compile to plan entries too but
the gate only pins views. NOTE for the desktop-procedure plan: view
ORDER must match the v1 manifest order (index -> deps -> raci ->
appendix-a; the gate pins relative order, not positions).
Targets: TestServiceabilityStage, TestDesktopProcedure (plan tests),
TestIndependence::test_compile_never_writes.

### WP-D3 — the M14 profile alias + toy end-to-end (after D2)
- `resolve_definition(area)`: no deliverables/ dir + a `profile:` key ->
  the shipped desktop-procedure definition with the profile's
  subtractions applied (sections dropped from shape, body_omit ->
  block flags, derived prunes -> views removed). Reuse
  client_config.profile — do not re-parse.
- A toy 3-block definition (entity-part + python view + static)
  compiled and RENDERED to a real .docx through the existing render
  path over the p2p fixture — the smoke that the plan is executable.
  This may require a thin adapter entry point (render_plan) that maps
  plan entries onto the existing render.py machinery WITHOUT modifying
  render.py's v1 behavior (wrapper module or additive function only).
- Package authors its own tests (tests/test_definitions_d3_m35.py):
  profile-alias equivalence (profile-only area resolves to shaded
  desktop-procedure; report_line provenance preserved) + the toy
  render smoke (docx exists, non-empty, contains the static text).
Targets: its own tests + full suite.

## Explicitly OUT of scope

Moving render/aggregate onto the plan path (M36's build), any new
binding verbs beyond what desktop-procedure needs (M37/M38 add theirs
with named consumers), pptx/xlsx skins.

## Sequencing

WP-D1 -> WP-D2 -> WP-D3, each ending with the full suite green except
later-package gate classes (report exact failures).
