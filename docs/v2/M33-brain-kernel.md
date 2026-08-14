# M33 — The brain kernel: typed entities, relations, evidence, identity

> **Status: DRAFT — contract under review.** The first v2 ticket. Companions:
> M34 (centralized sources — the engagement-level evidence layer this
> kernel's evidence concept assumes), M35 (the deliverable-definition
> language reads the type declarations this ticket creates), M36 (the
> compatibility gate that re-expresses v1's A–H deliverable on this kernel),
> M37 (surveyor/librarian — taxonomy nodes become kernel entities), M38
> (the second deliverable type this kernel exists to make cheap). Charter:
> [`README.md`](README.md).
>
> **Amendment A1 (2026-08-14):** evidence is engagement-scoped (centralized
> sources); the kernel ships TWO type declarations — the IPO `process-step`
> (v2-native, sketched below) and the v1 `activity` (compatibility) — and
> the charter's pipeline-inversion decisions are folded in.
>
> **Amendment A2 (2026-08-14, visual-review rulings):** (1) the
> transformation's detail layer is promoted to **structured sub-steps**
> (Decision 5 approved); (2) callout authorship clarified: CTRL/GAP/PAIN
> are recorded by the OWNING DRAFTER at capture time — they are part of
> drafting, never a synthesis pass; the strict callout grammar (typed
> label, ID, required fields, PAIN verbatim + SRC id) is what bounds the
> drafter's freedom, and model tier stays per-agent config (v1's
> `model: sonnet` pin carries over as the default).

## The problem this solves

v1's knowledge model is real but **implicit and fused to one deliverable**.
The facts live in the right places — stable slugs, `[[slug]]` tokens,
SRC-registered evidence, callout grammar, `consult-meta` noun bindings,
regenerated views — but the *shape* of a knowledge item is hard-coded as "an
A–H desktop procedure" across four modules:

- `doc_model.py` knows the seven-section registry (`SECTION_TITLES`), the
  manifest schema (`role: procedure`), and the display-number scheme —
  all activity-shaped.
- `callouts.py` knows exactly seven callout labels with fixed home sections.
- `aggregate.py` knows which views exist and which registry files
  (`systems.yaml`, `roles.yaml`) the meta block may bind to.
- `sources.py` is already shape-agnostic in spirit but keys consumption to
  procedure slugs specifically.

A second deliverable shape (a controls matrix, a process narrative, a
findings report) cannot be added without editing all four. **The kernel is
the extraction of what those modules agree on**, with the activity-specific
parts demoted from code to a *declaration* — so that M35's user-supplied
deliverable definitions and M38's second deliverable type consume the same
substrate v1 does.

**This ticket is an extraction, not an invention.** Every concept below
already exists in v1; the work is naming the general form, putting it in one
module, and declaring v1's specifics as the shipped default instance. No new
knowledge-modeling ideas ride along. Anything the three known consumers (v1's
procedure deliverable, M38's second type, the analysis verbs) do not demand
is out of scope — recorded under Deferred, not built.

## The five kernel concepts

The kernel (`scripts/kernel.py`, stdlib + pyyaml like everything else) owns
five concepts and nothing else:

### 1. Entity types — declared, not coded

An **entity type** declares what a class of hand-authored knowledge item
looks like:

- a **type name** (`process-step` and `activity` are the shipped two, below),
- an ordered set of **part declarations** — the general form of the M23
  section registry: each part has a slug (identity), a canonical title,
  title/slug aliases, and a content kind (`prose` | `table` | `list`),
- the **callout vocabulary** admitted in its parts — the general form of
  `LABEL_TO_PREFIX` + `home_section`: each callout kind has a label, an ID
  prefix, a home part, and its field schema,
- its **binding channels** — which registries a `consult-meta` block on an
  instance of this type may bind (the general form of aggregate's hard-coded
  `systems` + `roles` lists),
- its **relation kinds** (see concept 3).

Type declarations live in **`kernel/types/<name>.yaml`** inside the plugin.
**Two types ship** (A1); the loader treats shipped and user types
identically, and a user project may add its own.

**`kernel/types/activity.yaml` — the v1 compatibility type.** The seven
sections, their aliases (including the frozen A–H letter aliases and the
M16 past-title aliases, verbatim from `SECTION_TITLES` /
`SECTION_TITLE_ALIASES` / `SECTION_LETTER_ALIASES`), the seven callout
labels, and the systems/roles binding channels. This is v1 written down; it
is what the M36 compatibility gate runs on, and it is the golden-comparison
target below.

**`kernel/types/process-step.yaml` — the v2-native type (the backbone).**
The deliverable-neutral shape of a unit of process understanding, per the
charter's IPO decision. Sketch to firm up at build time:

| part slug | content kind | job |
|---|---|---|
| `scope` | prose | what this step is, its trigger/cadence, its owner, what adjoins |
| `inputs` | list | each input: artifact, where it comes from (step/party/system) |
| `transformation` | prose | what is decided / calculated / checked, by whom, in which system |
| `outputs` | list | each output: artifact, where it goes, what is retained as evidence |
| `controls` | prose | the control activities riding this step |
| `issues` | prose | exceptions, defects, gaps, voiced pain points & risks |

Rules that come with the type:

- **The step-granularity rule (charter):** a step is the unit at which
  owner, system, or control changes — that is where accountability shifts,
  so that is what the brain indexes. Anything finer is a sub-step. The
  surveyor's brief coaches drafters on where the breaks go.
- **Sub-steps are structured and optional (A2).** The "how" inside a step
  — the ordered actions, screen paths, keystrokes, screenshots — lives as
  an ordered sub-step list inside `transformation` (same owner, same
  system throughout, by the granularity rule; exact grammar decided at
  build time). The brain never demands them; a deliverable definition
  chooses its altitude — the desktop procedure unfolds sub-steps, a
  controls matrix reads only the step line. Absence of sub-steps is never
  a gap.
- **IPO edges are relation data.** An input naming its producing step and
  an output naming its consuming step are `references` relations — which is
  what makes cross-step dependency derivation mechanical (the charter's
  pressure on `consult-dependencies`).
- Callout vocabulary and binding channels start as the v1 seven + systems/
  roles (they are governance, not presentation, and carry over); pruning or
  extending them is a build-time decision inside this ticket.
- **Pain points are a callout kind** (`PAIN-` prefix, homed to `issues`):
  what an interviewee voiced as a pain, worry, or risk — captured in THEIR
  framing, attributed (who voiced it, via the roles channel), and
  evidenced (SRC id). **Observation, never assessment**: the drafter
  records that it was said; whether it is real, material, or an
  improvement opportunity is the analysis layer's job (M39), which mines
  these callouts as its raw material. This is the same
  align-never-evidence-style discipline line as M30's context entries —
  the drafter contract carries it verbatim, and the distinction from GAP
  is crisp: a GAP is something the DOCUMENT is missing; a PAIN is
  something the BUSINESS is feeling.

`process-step.yaml` has **no v1 golden target** — its acceptance is that it
loads, parses, and serves views through the same code paths as `activity`,
plus a hand-built fixture. Re-authoring real content into IPO shape is
M37+/migration territory, not this ticket.

Fail-loud loader rules (same posture as `validate_manifest`):

- unknown top-level keys, duplicate part slugs, alias collisions across
  parts, a callout homed to an undeclared part, a binding channel without a
  registry filename — each a **load-time error naming the file and key**;
- a type that fails to load never half-registers: the engagement refuses to
  advance with a precise message, exactly like a malformed manifest today.

What is deliberately NOT in a type declaration: display transforms (letters,
numbers), docx styling, agent briefs. Those are deliverable-definition
(M35) and renderer concerns. **The kernel never learns to render.**

### 2. Entities — identity, parts, one writer

An **entity** is one hand-authored file, exactly as a procedure fragment is
today: a slug assigned once at creation (the identity), a declared type, an
ordered set of parts keyed by part slug, a `consult-meta` block, callouts
with local IDs. The kernel provides the one parser:

- `parse_entity(text, etype) -> Entity` — the generalization of
  `aggregate.split_subsections` + `parse_consult_meta` + `parse_callouts`,
  driven by the type declaration instead of module constants. Duplicate
  parts follow the M16 doctrine verbatim: **tolerate + report, never fail,
  concatenate bodies in document order** (`duplicate_sections` generalizes
  to `duplicate_parts`).
- The **manifest** stays the single ordering and membership authority. The
  v1 manifest schema is untouched in this ticket; `role: procedure` is read
  as "entity of type `activity`" through one adapter function. (A
  generalized manifest schema, if ever needed, is an M35+ decision — the
  kernel consumes manifests, it does not redefine them.)
- The **one-writer-per-file rule is unchanged and unweakened**: the kernel
  reads and validates; it never writes an entity. Writers remain the
  scaffold, the owning drafter, and the deterministic verbs.

### 3. Relations — typed, slug-addressed, declared per type

The general form of what v1 has three separate grammars for:

| v1 grammar | kernel relation kind |
|---|---|
| `[[slug]]` / `[[area/slug]]` tokens | `references` (entity → entity, cross-area capable) |
| `consult-meta` slug lists | `binds` (entity → registry noun, per channel) |
| callout ID mentions (`GAP-01` in prose) | `mentions` (prose → callout instance) |

The kernel exposes **one relation extractor** per kind (wrapping today's
`resolve_tokens` slug-scan, `parse_consult_meta`, and `iter_defined_ids` /
mention scanning respectively) and **one integrity contract**: every
relation endpoint must resolve — a dangling `references` is an ERROR at
render (unchanged), an unknown `binds` slug is a WARNING that drives a
registry top-up (unchanged), a `mentions` of an undefined ID is an ERROR
(unchanged, `check_body_gap_refs` generalized). New relation kinds are a
type-declaration edit plus an extractor, not a fourth grammar invented ad
hoc — that is the rule this concept exists to impose.

### 4. Evidence — the SRC chain, kernel-level and engagement-scoped

`sources.py`'s registry is already the right shape; two changes (the second
per A1):

- **consumption keys to entity slugs** rather than procedure slugs (a
  rename-level generalization — `note_src_ids`, `mark_processed`, and
  `touches` validation gain no new semantics);
- **the registry's home is the engagement root**, per the charter's
  centralized-sources decision. This ticket defines the kernel API as
  engagement-scoped (source identity is engagement-global; consumption
  records are per-consumer); the physical flattening of `_sources/` trees,
  the per-consumer processed lifecycle, and intake-as-tagging are **M34's
  build**, which implements against this API. Until M34 lands, the kernel
  reads v1's per-area layout through the same adapter posture as manifests.

The kernel states the evidence contract once, where every consumer can cite
it:

> Every hand-authored claim traces to a SRC id. Registers carry provenance.
> Context aligns, never evidences. A claim without a citation path is a GAP,
> never prose.

### 5. Views — regenerated projections with declared inputs

A **view** is what `aggregate.py`'s builders and the synthesis agents
produce today: derived content, one writer (`python` | `agent`), never
hand-maintained. The kernel addition is small but load-bearing: a view
**declares which entity types, parts, callout kinds, and binding channels
it reads** (today implicit in each builder's code). That declaration is
what lets M35's deliverable definitions ask "can this brain serve this
binding?" and fail loud at load time instead of rendering half-empty — the
kernel provides `can_serve(view_requirements, engagement) -> [errors]` as a
pure function over the declarations.

## What moves, what wraps, what stays

This ticket's migration stance — chosen so the v1 suite is the regression
harness rather than a casualty:

- **MOVES into the kernel** (cut-and-generalize, old call sites delegate):
  the section registry + its resolvers (`SECTION_TITLES` through
  `section_headings`, becoming type-driven with `activity.yaml` supplying
  the data), `split_subsections`, `parse_consult_meta`, the callout
  vocabulary tables in `callouts.py`.
- **WRAPS** (kernel functions call the v1 implementation unchanged):
  manifest load/validate, `display_numbers`, `resolve_tokens`, `assemble`,
  the SRC registry. These migrate fully in M36 when render/aggregate move
  onto the kernel; wrapping first keeps this diff reviewable.
- **STAYS untouched**: every agent definition, every skill brief, the
  orchestrator/advisor, render, kits, review loop, all `_client/` and
  area-folder layouts. **A v1 engagement folder is byte-for-byte a v2
  engagement folder.** No migration script exists because no file format
  changes.
- **Back-compat shims**: `doc_model.SECTION_TITLES` etc. remain importable,
  re-exported from the kernel's activity type, so nothing off-spine breaks
  silently. Removed only after M36.

## Acceptance sketch (firm up at build time)

- `kernel/types/activity.yaml` loads; every entry byte-derivable from
  today's `doc_model.py` / `callouts.py` constants — verified by a test
  that diffs the loaded declaration against the (temporarily retained)
  v1 tables.
- `parse_entity` over every fragment in the procure-to-pay fixture
  (`claude/repo-primer-bidlgp` lineage) yields identical parts, meta, and
  callouts to the v1 parsers — a golden-comparison test.
- Loader refuses, with a message naming file and key: a duplicate part
  slug, an alias collision, a callout homed to an undeclared part, an
  unknown top-level key, a binding channel without a registry file.
- `process-step.yaml` loads and parses through the SAME code paths as
  `activity` (the generality proof lives in-ticket): a hand-built IPO
  fixture round-trips parts, callouts, meta, and IPO-edge relations.
- `can_serve` returns precise errors for a requirement naming an unknown
  type, part, callout kind, or channel; empty list for the v1 view set.
- **The full v1 suite (803 tests) passes unchanged.** New kernel tests are
  additive.

## Complexity accounting (the standing test)

New state files: **zero** (type declarations are plugin data, not
engagement state). New gates: **zero** (loader errors surface through the
existing reconcile/advisor path). New agent judgment: **zero** — this ticket
is entirely deterministic-layer; no brief changes, no new verbs. The bill
is one new module, one data file that writes down what code already said,
and shims. The risk to police at review: **invention creep** — any concept
in `kernel.py` that `activity.yaml` + the toy type + `can_serve` do not
exercise gets cut, not documented.

## Deferred (recorded, not built)

- **Generalized manifest schema** (`type:` on components) — M35+ decides
  when a second real type forces it; the adapter suffices until then.
- **Cross-entity-type relations** (an analysis finding referencing an
  activity) — needed by M39; the `references` kind is designed not to
  preclude it (endpoints are slugs, not activity slugs), but no second
  entity type exists in engagement state until content is authored
  IPO-shaped (M37+).
- **Registry generalization beyond systems/roles** (user-declared noun
  channels with their own YAML schemas) — M35's binding language decides
  how much of this users can declare; the kernel's channel list is already
  data, so the option is bought.
- **Kernel-level query language** — `can_serve` + the extractors are the
  API; a general query layer waits until M35's bindings show what queries
  actually look like.
