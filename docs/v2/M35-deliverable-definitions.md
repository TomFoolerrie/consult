# M35 — The deliverable-definition language: shape, bindings, skin

> **Status: BUILT (2.0.0-alpha.5)** — `scripts/definitions.py` (four-stage
> loader, serviceability-as-report, compile_plan, resolve_definition with
> the M14 profile alias) + `kernel/deliverables/desktop-procedure.yaml`
> (v1 written down) + `scripts/render_glue.py` (executable-plan proof).
> Gates: `tests/test_definitions_m35.py` 17/17 +
> `tests/test_definitions_d3_m35.py` 9/9; suite 959 passed, zero v1 tests
> edited. Build record: [`M35-build-plan.md`](M35-build-plan.md) (WP-D1–D3).
>
> **Amendment A1 (build notes, 2026-08-15):** (1) a view block's `id` IS
> its derived kind, writer declared on the block; (2) admitted binding
> verbs limited to named consumers (entities, parts, callouts, channels,
> order, group_by) — the spec's illustrative verbs (join, cells, coverage,
> of) wait for their M37/M38 consumers; (3) `kernel.can_serve` is
> declaration-pure, so the engagement-half entity-population check lives
> in `definitions.serviceability` with a type→manifest-role mapping that
> should graduate to a type-declaration key when M37 lands a second
> engagement entity type; (4) profile shading is subtractive-only,
> in-memory `body_omit` (not language syntax), authored definitions win
> whole; (5) render_glue proves EXECUTABILITY with v1 fidelity — assembly
> FROM plan.blocks (writer dispatch, part selection, static injection) is
> M36's owed half, stated verbatim in the module docstring; (6) known gap
> carried to M36: the shipped definition has no appendix-controls block,
> so a profile opting that register in is a silent no-op. Companions: M33 (the type
> declarations and `can_serve` this language is written against), M14 (the
> document profile — the embryo this ticket promotes to a full language,
> kept as a compatibility alias), M13 (whose `_client/` resolution the
> definition files ride), M36 (the compatibility gate: v1's deliverable
> re-expressed IN this language), M37 (whose information-request list is
> this language's first born-v2 deliverable). Charter:
> [`README.md`](README.md).

## The problem this solves

v1 has exactly one deliverable, and its shape lives in code: `render.py` +
the docx-builder skill know the section order, `aggregate.py` knows which
views exist, and the M14 profile can only **subtract** from that fixed shape
(drop sections, hide bodies, prune derived views). A user who wants a
process narrative, a controls matrix, or an information-request list — the
charter's whole point — has no place to put that want except a feature
request against the engine.

The v2 contract (charter): **a deliverable is data the user brings.** This
ticket builds the language those files are written in, the fail-loud loader
that validates them, and the execution plan they compile to. It does NOT
move render onto the kernel — that is M36's build; this ticket's proof
obligations are language-level.

## Where definitions live

```
components/_client/deliverables/<name>.yaml     user-authored definitions
<plugin>/kernel/deliverables/<name>.yaml        shipped definitions
```

- Shipped and user definitions load identically (same posture as M33's
  types); a user file shadows a shipped file of the same name — M13's
  per-top-level-key doctrine, applied per file.
- **The plugin ships `desktop-procedure.yaml`** — v1's deliverable written
  down in this language. It is the M36 gate's subject and the worked
  example every user definition copies from.
- **The M14 profile survives as a compatibility alias**: a `profile:` key
  with no `deliverables/` directory compiles to "desktop-procedure with
  these subtractions" through one adapter. Existing engagements keep
  meaning what they meant; the profile's vocabulary (section slugs, frozen
  letter aliases, `body_omit` cross-field rules) is already
  kernel-friendly by M23's design.

## The language — three layers, one file

A definition is one YAML file with three top-level keys. Layer boundaries
are load-bearing: **shape says what the document is, bindings say what the
brain must supply, skin says how it looks.** Nothing in shape or bindings
may name a font, and nothing in skin may name an entity type.

### 1. `shape:` — ordered blocks

An ordered list of blocks; each block declares:

- `id` — stable block identity (the definition-side analog of a slug),
- `title` — rendered heading (display, not identity),
- `kind` — one of:
  - `entity-part` — projects a part of hand-authored entities
    (e.g. the `transformation` part of every `process-step`),
  - `view` — a derived projection (a table, an index, a matrix), built by
    the deterministic layer or an agent (writer declared, as today),
  - `static` — fixed prose from the definition itself (a boilerplate
    scope statement, a legend),
- `repeat` — optional: the entity query this block repeats over (per
  process step, per taxonomy node, per system…); un-repeated blocks render
  once,
- `binding` — the named binding (below) this block consumes,
- `numbering` — which numbering scheme the block participates in (display
  only, assigned at render — the v1 rule, unchanged and non-negotiable).

### 2. `bindings:` — declared queries against the brain

Named queries the shape refers to. The vocabulary is EXACTLY the kernel's
five concepts — entity types, parts, callout kinds, binding channels,
relations, plus registers (M30) and the SRC ledger (M34). Illustrative:

```yaml
bindings:
  steps:            {entities: process-step, order: manifest}
  pains:            {callouts: PAIN, group_by: taxonomy-node}
  role-matrix:      {channel: roles, join: entities, cells: responsibility}
  open-questions:   {coverage: thin, of: taxonomy}   # M37 serves this
```

**Discipline: this is a binding vocabulary, not a query engine.** The verb
set is exactly what the three committed consumers demand — the
desktop-procedure definition, the M37 information-request list, and one
matrix-shaped deliverable (M38) — and grows only when a real definition
cannot be expressed. A binding names WHAT to select and how to group/join;
layout is the renderer's job; computation beyond join/group/filter is an
analysis verb's job (M39), not a binding's.

### 3. `skin:` — the render target

- `format` — `docx` is the only shipped target in this ticket (`pptx`,
  `xlsx` deferred; the layer boundary is what makes them cheap later).
- Style mapping (heading levels, table styles), branding (the CFGI look as
  the shipped default), TOC, document-control block, numbering display
  formats.
- **Renderers declare capabilities; the loader checks skin against them**
  — a skin asking the docx renderer for something it cannot do is a
  load-time error, not a rendering surprise.

## The fail-loud loader — four stages, precise errors

1. **Syntax** — YAML parses, top-level keys are exactly the three, unknown
   keys named and refused (the M33 loader posture).
2. **Vocabulary** — every type, part, callout kind, channel, and relation a
   binding names exists in the loaded type declarations. Checked against
   DECLARATIONS, so a definition validates with zero engagement content.
3. **Serviceability** — `can_serve(definition, engagement)` (M33): the
   engagement's actual state can supply every binding. A definition can be
   vocabulary-valid but unserviceable ("no process-step entities exist
   yet") — reported as a gate, not an error, because it is often just
   "not yet" (the advisor can sequence it).
4. **Skin capability** — skin demands vs. the target renderer's declared
   capabilities.

Every failure names the definition file, the block/binding id, and the
missing thing. **A definition never half-loads** — the M33 rule.

## Execution model — definition compiles to a plan

A loaded definition compiles to a deterministic **build plan**: which
derived views must be (re)built and by which writer (python views directly;
agent-written views dispatch the declared synthesis agent — the M5 pattern,
now definition-driven), which blocks read which entities, what the render
adapter assembles. The plan slots into the existing advisor loop: scope
delta and staleness per view work exactly as today (M21's render signal
generalizes per-definition). One engagement can carry N definitions; each
compiles and renders independently — deliverables are views, so they never
contend for writes.

The review loop attaches to the SKIN, per the charter: the docx skin brings
the v1 tracked-changes/kits/extract/apply pipeline with it; a future xlsx
skin brings a workbook return-trip. Review is a property of the render
target, not of the definition language.

## Acceptance sketch (firm up at build time)

- `desktop-procedure.yaml` loads through all four stages against the M33
  `activity` type and compiles to a plan whose view set, writer map, and
  block order match v1's hard-coded pipeline — a structural comparison
  (the byte-level render proof is M36's).
- A hand-written toy definition (three blocks: one entity-part with
  repeat, one python view, one static) loads, compiles, and renders
  through the docx adapter.
- Loader refusals, each naming file + id + missing thing: unknown top-level
  key, binding naming an undeclared part, block referencing an undefined
  binding, skin demanding an undeclared renderer capability, shape block
  naming a font (layer violation).
- Serviceability reports "not yet" (empty engagement) distinctly from
  "never" (vocabulary error) — the advisor consumes the difference.
- A `profile:`-only engagement resolves to the shaded desktop-procedure
  definition; `Profile.report_line` provenance behavior preserved.
- Two definitions in one engagement compile and render independently; no
  shared mutable state (the one-writer audit extends to plan outputs).

## Complexity accounting (the standing test)

New state files: definitions are `_client/` config (human-authored ground
truth, M13's category — not state). New gates: one, and it is a REPORT
(serviceability "not yet"), consumed by the advisor like any other
precondition. New agent judgment: zero — agents receive briefs generated
from the plan exactly as they receive briefs today. The bill is the loader,
the compiler, and the docx adapter refactor. The review risk to police:
**query-engine creep** — every binding verb must have a named consumer
among the three committed definitions; a verb added "because someone might
need it" gets cut.

## Deferred (recorded, not built)

- **pptx / xlsx skins** — the skin layer's job is to make these adapters,
  not engine changes; first real demand wins (the CFGI deck style guide
  already exists plugin-side).
- **Multi-document packs** (one definition emitting a document per
  taxonomy node) — `repeat` at document level; wait for a real engagement.
- **Conditional blocks** ("include this section only if PAIN callouts
  exist") — an empty-binding block already renders nothing; explicit
  conditionality waits for a case that rule can't express.
- **User-authored agent-written views** (user definitions dispatching
  custom synthesis briefs) — powerful and sharp; needs the M37/M39 agent
  experience first.
