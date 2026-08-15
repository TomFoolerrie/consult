# M40 — Definition views to manifest: the materialize verb and the missing writers

> **Status: SPEC** — closes the language gap M38 Amendment A1 recorded:
> "nothing reflects a definition's view blocks into an area manifest."
> Companions: M35 (the language whose views this ticket makes buildable),
> M38 (whose builder registry and fixture this ticket extends; whose
> refusal — no materialization inside render_glue — this ticket honors by
> making materialization an explicit verb), M37 (the information-request
> definition renders end-to-end for the first time here), M39 (likewise
> the findings report). Charter: [`README.md`](README.md).

## The problem this solves

Two independent enumerations of a deliverable's views exist, and nothing
joins them:

1. the **definition's `kind: view` blocks** — compiled into `Plan.views`
   (kind + writer) and `Plan.blocks` (title, binding, order);
2. the **area manifest's `role: derived` components** — the six-key
   entries (`file`, `role`, `derived_kind`, `writer`, `heading`, `order`)
   that are the ONLY thing that causes `aggregate` to build a view.

The plan can *refuse* a kind (the pre-flight) and can *authorize* one
(the plan-driven dispatch), but only a manifest entry can *cause* one to
be written — and the plan carries neither a `file` nor an `order`. The
consequences, visible today: the matrix's derived component was
hand-authored into the IPO fixture, and the information-request and
findings-report definitions — both shipped, both loading, both
serviceability-honest — **have never rendered**, because their three
views (`information-requests`, `open-validations`, `findings-by-theme`)
have neither manifest entries anywhere nor `PY_BUILDERS` writers.

M36's WP-G1 refused to materialize inside render_glue (rightly: a
renderer that silently writes manifests is a special case in disguise).
The honest home is an **explicit verb** — the plan-driven counterpart of
v1's `scaffold.sync_profile`, which already does exactly this shape of
work (idempotent derived-entry reconciliation) driven by the M14 profile
instead of a compiled plan.

## Part A — The materialize verb

`definitions.materialize_views(area, name=None)` (module placement is the
implementer's call; the contract is not):

- **Resolution**: `name` picks the definition; `None` falls back to
  `resolve_definition(area)`. The definition is loaded through the
  ordinary four-stage loader — an unloadable definition refuses before
  any write.
- **What it writes**: for each `kind: view` block of the compiled plan,
  ensure the area manifest carries a `role: derived` component with the
  canonical six keys — `derived_kind` = the block `id`, `writer` = the
  block's writer, `heading` = the block's `title`, `file`/`order` minted
  by the documented mechanical policy below — and ensure the stub file
  exists (heading + `<!-- derived: kind; writer: w -->` marker + pending
  line, `scaffold.render_derived`'s shape). Agent-writer views get the
  same entry with `writer: agent` (aggregate's placeholder discipline
  then applies).
- **File/order policy (mechanical, documented, not configurable)**: a
  new entry's `order` starts at max(existing component orders) + 10 and
  increments by 1 per subsequent new view, so materialized views land
  after everything already in the area, in the definition's block order;
  `file` is `<order>_<kind>.md`. A definition key for placement is
  deliberately NOT added — position is display, and a future ticket can
  add vocabulary if a user ever needs it.
- **Idempotence and preservation** (`sync_profile`'s discipline): an
  existing component whose `derived_kind` matches is preserved
  byte-for-byte — never renamed, re-ordered, or re-titled (a hand-tuned
  entry, like the fixture's matrix at order 20, outranks the policy).
  A second call is a no-op. Nothing is ever deleted: a view the
  definition dropped keeps its component and file (removal is a human
  edit). Non-derived components are never touched.
- **Fail-loud**: the manifest is re-validated (`doc_model.validate_manifest`)
  after the write; a validation error refuses and leaves the manifest
  unchanged (write-aside then replace, or equivalent). A minted `file`
  that collides with an existing file of a DIFFERENT kind refuses by
  name.
- **Report, not silence**: returns what it added and what it preserved,
  so a caller (and a test) can see the delta.

The verb is opt-in and v2-only in practice: nothing in v1's pipeline
calls it, so every v1 area remains byte-identical.

## Part B — The missing writers

One new module, `scripts/plan_views.py` (M38's sanctioned extension
mechanism: a new builder module registered through `aggregate.PY_BUILDERS`,
one import + one entry per kind; nothing in the loader, compiler, or
renderer learns these names). Three builders:

1. **`information-requests`** (the M37 coverage feeder): computes
   `coverage(root, node_steps)` on demand — `node_steps` derived
   mechanically by the matrix's own published grouping rules
   (`matrix_views` reuse, not a copy) — selects the nodes at the
   binding's statuses, and emits the request list: per node, what is
   missing and why, phrased as ASKS (the definition's preamble owns the
   framing; the view carries node title, status, and the evidence
   already held). The `thin` alias collapses to claimed-or-sourced where
   definitions.py documents it — the builder types no status literal of
   its own.
2. **`open-validations`** (the M37 step feeder): the bound callout kind's
   entries per step, in manifest order, with SRC attribution — labels
   and prefixes resolved through the binding + the type declaration
   (matrix_views' `_prefixes` discipline; no literals).
3. **`findings-by-theme`** (the M39 feeder): `findings.by_theme(root)` —
   accepted only, structurally (the module refuses any other status at
   load; the builder reaches the register only through
   `findings.renderable`/`by_theme`). Per theme, each finding's claim
   with its grounds rendered as citations.

Builders are read-only over the engagement except through
`aggregate.write_derived` (which owns the file write). Each reads its
own definition's bindings when the ctx does not carry them
(matrix_views' `_definition_bindings` pattern). The engagement root is
derived from the area the way the existing machinery does it — read
`engagement.py` for the published helper first; derive-and-document only
if none exists.

## Part C — The proof: two definitions render end-to-end

The acceptance that matters: over a tmp copy of the IPO fixture,

- `materialize_views(area, "information-request")` → `aggregate.run` →
  `render_plan` produces the information-request docx: the request list
  reflects the fixture's computed coverage; Open Validation Points
  carries GAP-01..04.
- Seed accepted findings through `findings.propose`/`accept`, materialize
  `findings-report`, aggregate, render: the report carries the accepted
  claim grouped under its theme; rejected and proposed claims appear
  nowhere.
- Materializing over the fixture with the matrix definition adds
  NOTHING (the hand-authored entry is recognized — the idempotence
  proof against real data).

## Acceptance sketch (pinned in tests/test_views_m40.py, written first)

- Materialize: adds six-key entries + stub files for the definition's
  view blocks in block order after existing components; idempotent;
  preserves the fixture's matrix entry byte-for-byte; never touches
  procedure components; manifest validates after; refuses on a file
  collision with a different kind.
- Each builder over the fixture: content pinned to fixture facts
  (GAP-01..04; coverage computed in-test through the same pure
  function; accepted-only for findings); builders read-only.
- End-to-end: both never-rendered definitions produce a docx.
- Shape audit: the new module needs zero allowlist entries (vocabulary
  through bindings + declarations).
- v1 suite green; zero v1 tests edited.

## Complexity accounting (the standing test)

New state files: zero (the manifest is existing state; stubs are the
existing derived-file idiom). New gates: zero. New agent judgment: zero —
all three writers are pure projections of existing judgment (the
surveyor's coverage, the drafters' callouts, the analyst's accepted
findings). The bill is one verb with sync_profile's proven discipline
and one builder module. The review risk to police: **placement policy
creep** — the moment file/order policy grows configuration, position has
stopped being display; and **register leakage** — the findings builder
must be structurally unable to render a non-accepted finding.

## Deferred (recorded, not built)

- A definition-level placement key (order/file vocabulary) — until a
  user needs it, position is display and the mechanical policy stands.
- Removal reconciliation (a dropped view block retiring its component) —
  deletion stays a human edit, as everywhere else in the system.
- The per-area findings filter (M39 A1 point 6) — the observations
  appendix still waits on it; not this ticket.
