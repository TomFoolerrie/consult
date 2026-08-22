# M66 — Objective-shaped capture: the deliverable declared is not the shape drafted

**Status: BUILT** (`2.4.0-alpha.6`, gate 77/77 across two work
packages — see Amendment A3). Ruled per Amendment A1;
the ruling goes further than any of the three candidates below. The
candidates are kept as the decision record.
Origin: the first live run of the v2 pipeline over the Nordhaven
synthetic engagement (`examples/nordhaven-industrial`). The objective
declared `deliverables: [findings-report]` and every document was
nonetheless scaffolded and drafted as a full seven-section desktop
procedure, under a manifest titled "— Desktop Procedures".

## Why

M41 gave the engagement an objective, and the objective's
`deliverables:` list is validated against real definitions
(`client_config.py:917–931`) and consumed by needs, agenda, analysis,
brief, client_config and engagement. **Neither `scaffold.py` nor
`orchestrate.py` reads the OBJECTIVE** — precision matters here: the
advisor does carry a per-definition deliverable seam
(`_area_deliverable` and the render signals, `orchestrate.py:1343`
ff.), so it is objective-blind, not deliverable-blind, and a builder
should look for the wiring point there rather than concluding no
seam exists. Concretely:

1. **The confirm-gate scaffold is deliverable-blind.** `do_scaffold`
   resolves the document profile (`client_config.profile`,
   `scaffold.py:1357`) — which defaults to the full seven-section
   activity shape when the engagement ships no `profile.yaml` — and
   writes one desktop-procedure skeleton per procedure
   (`render_skeleton`, `scaffold.py:1409`). The default manifest title
   is literally `"{Area} — Desktop Procedures"` (`scaffold.py:1377`).
   An engagement hired to produce ONLY a findings report gets the
   identical capture surface, identically titled, with no notice.

2. **The fill wave is the only capture path.** `consult-drafter`'s
   whole contract is the desktop procedure (activity or process-step
   unit); the advisor's ladder has no other drafting action. So the
   objective steers the taxonomist's sufficiency emphasis and the
   serviceability reports — and then the expensive stage, capture,
   proceeds as if the objective did not exist.

Part of this is defensible: `findings-report` renders the findings
register, the analyst mints findings from captured CALLOUTS (PP /
GAP / CTRL / IO), and drafted fragments are the only place callouts
live — so some capture drafting is structurally required. The defect
is that nothing derives the capture SHAPE from what the engagement was
hired to produce, and nothing even says so: the user meets a
procedures manual they never asked for, with the recommendation list
they did ask for nowhere in sight until the analysis verbs run.

## The candidate shapes (recorded, not ruled)

### Option 1 — the objective derives the capture profile

When no explicit `profile.yaml` is shipped, scaffold consults
`objective.deliverables` and derives the default profile from the
declared set: a findings-only engagement gets a slimmer,
callout-forward section set (the callout kinds the analyst feeds on
stay in play; sections that exist only for the procedures deliverable
drop), and the manifest title stops claiming "Desktop Procedures". An
explicit `profile.yaml` still wins — human config over derivation,
the M13 order. Moderate build; touches scaffold + client_config +
the skill's confirm row.

**Honesty note on Option 1's ceiling (from the adversarial review):**
callouts are HOMED to sections (`kernel/types/activity.yaml:65–68` —
CTRL→controls, GAP→steps, PP/IO→issues), and `dropped_sections`
removes a section outright. Holding this ticket's own invariant 1
(the analyst's feed kinds stay capturable) therefore PINS `steps`,
`controls` and `issues` — the derived profile can only slim `scope`,
`quick-reference`, `before-you-start` and `outputs`. Option 1 is a
real but MODEST reshaping (four droppable sections plus the title);
anyone expecting capture to become findings-shaped should weigh
Option 3 instead. Recorded so the ruling is made with the ceiling in
view, not discovered at build time.

### Option 2 — capture stays as is, the gate says so

The desktop-procedure shape remains the one capture surface (it IS
the evidence corpus the analyst reads). Scaffold prints — and the
confirm gate relays — an explicit notice when the objective's
deliverables do not include a procedures-shaped definition: capture ≠
deliverable, the declared report is a separate render over what
capture records. Cheapest; purely informational; the Nordhaven
surprise becomes a stated design instead of a silent one.

### Option 3 — findings-only engagements capture on the nodes

Extend the `taxonomy-node` type's deliberately-one-kind callout
vocabulary so evidence capture for findings-only engagements happens
directly on the survey's nodes, skipping procedure skeletons
entirely. Biggest build; contradicts the recorded design pin in
`kernel/types/taxonomy-node.yaml` (one kind is load-bearing for
`coverage_map.py`) and moves v2 furthest from the v1 corpus — listed
for completeness, not momentum.

## The gate

Set by the ruling. Whatever is chosen must hold two invariants:

- The analyst's feed does not thin: every callout kind
  `analysis.py`'s generators read remains capturable under the chosen
  shape.
- An engagement that DOES declare a procedures deliverable (or ships
  an explicit profile) scaffolds exactly as today — the compat gate
  and the frozen fixtures see no diff.

## Amendment A1 — the ruling (2026-08-22)

The human's ruling goes one step past Option 1: **capture is the
brain, and every document is a render over it.** In the human's own
framing: "if I was going to do another desktop procedure, it would
end up being a renderer. This is just meant to be the brain."

1. **`process-step` becomes THE v2 capture unit — always, not just
   for findings-only engagements.** All six declared parts (scope /
   inputs / transformation / outputs / controls / issues,
   `kernel/types/process-step.yaml`), none dropped: the callout homes
   pin controls, issues and transformation; inputs and outputs are
   cheap lists and are exactly where integration/automation friction
   shows (a manual re-key is one step's output arriving as a
   hand-typed input of the next); scope is one paragraph. Scaffold
   stops consulting the activity seven-section default for v2
   capture, and the manifest title stops claiming "Desktop
   Procedures".

2. **The desktop procedure is DEMOTED to what it already is in the
   kernel: a deliverable definition** (`kernel/deliverables/
   desktop-procedure.yaml`) — a render over the brain, requested
   through the objective like any other deliverable, never a capture
   template. No engagement drafts "in the desktop procedure shape"
   again; one that declares the deliverable renders it from
   process-step capture. (Definition rework to bind process-step
   parts is part of the build; the v1 ACTIVITY type and the frozen
   corpus stay untouched behind the compat gate — invariant 2 below
   narrows to that.)

2b. **The document furniture stops being scaffolded into capture.**
   The confirm-gate scaffold today also writes the desktop
   procedure's STATIC pieces and derived-view stubs into the area —
   `04_process-overview`, `06_procedure-index`, `07_role-dictionary`,
   `08_systems`, `82_dependencies`, `84_raci`, the three appendices
   (`STATIC_FILES` at `scaffold.py:1406`, `profile_derived_files` at
   `scaffold.py:1425–1426`). Those are pieces of a DOCUMENT, not of
   the brain: under this ruling the scaffold writes only the
   process-step fragments plus the manifest, and every
   static/derived block is produced by the render/materialize path
   (M40's definition views) for whichever deliverable the objective
   declares, at render time, outside the capture corpus. The v1
   activity path keeps its scaffolding unchanged behind the compat
   gate. (Gate addition: a fresh v2 confirm leaves NO
   `0x_`/`8x_`/`9x_` document files in the area; a desktop-procedure
   render still contains all of those blocks in the output document.)

3. **Option 2's honesty line ships too:** the confirm gate states,
   in one sentence, that capture records evidence step-by-step and
   the declared deliverables are renders over it.

4. **The taxonomist's survey feeds the drafter — read-only.** The
   drafter's brief lists the procedure's live taxonomy node
   (`_taxonomy/<slug>.md`, alive per M65) as a READ-ONLY input, so
   the survey's scope notes inform the draft instead of being
   re-derived. The one-writer rule is restated mechanically: a
   drafter writes exactly its own fragment; `_taxonomy/` is written
   only at the confirm gate (promotion). The build adds the
   mechanical guard — reconcile (or the audit) fails an area whose
   `_taxonomy/` files changed outside a confirm — so "the drafter
   overwrote the survey" is structurally impossible, not just
   contractually forbidden.

The gate (making the ticket's two invariants concrete):

- A v2 engagement scaffolds process-step skeletons: six part
  headings, no quick-reference/before-you-start, title without
  "Desktop Procedures".
- Every analyst-read callout kind mints and parses on the
  process-step unit (feed does not thin).
- An objective declaring `desktop-procedure` renders the definition
  over process-step capture (or the definition's rework refuses with
  a named "not yet" until it lands — never a silent wrong render).
- The v1 compat gate and frozen activity fixtures pass byte-identical.
- Drafter brief lists the live node read-only; the guard fails an
  area where `_taxonomy/` changed outside a confirm.
- The confirm gate prints the capture-vs-render sentence.

## Amendment A2 — the v1-residue sweep: build items the ruling implied
## but did not name (2026-08-22)

A code survey for v1 artifacts on the v2 path (post-A1) found the
ruling's blast radius is wider than the scaffold. These are BUILD
ITEMS of this ticket — without them the A1 gate can pass at scaffold
time while the rest of the engine silently mis-reads process-step
fragments:

1. **The section parser splits by type — the highest-leverage item.**
   `doc_model.section_of_heading` (registry `doc_model.py:194–271`)
   is the one heading parser used by aggregate, render, reconcile,
   kits, consolidate and the advisor — and its table is v1's seven.
   On process-step it mis-files `### Inputs` → `before-you-start`
   (alias table), and returns None for `### Transformation` and
   `### Issues`. The v2 path routes through the kernel's tdecl-driven
   twins (`kernel._part_of_heading` / `_split_parts` /
   `parse_entity`, kernel.py:332/388/548); `doc_model`'s table stays
   as the v1 parser. Consumers that inherit the fix in the same
   stroke: `orchestrate._present_sections` (:323, feeding the
   reprofile guard — else guard 4.5 reports transformation/issues
   permanently missing and dispatches an unterminating reprofile
   wave), `engagement.py:242`'s scope extraction.

2. **Profile vocabulary becomes a function of the capture type.**
   `client_config._declared_part_slugs/_declared_callout_labels/
   _declared_home` all load `"activity"` (`client_config.py:266,
   275, 285`), so `ALL_SECTIONS` is the seven and
   `MANDATORY_SECTIONS` demands `quick-reference`/`steps` — a v2
   area that ships a `profile.yaml` is REFUSED at
   `client_config.py:524–531`, and `transformation` is an "unknown
   section". The A1 escape hatch ("an explicit profile still wins")
   is a trap until this lands.

3. **Render-time lettering and hiding come from the bound type.**
   `render._apply_profile` (`render.py:426–428`) letters sections
   via the activity map — a rendered process-step fragment gets
   `### C. Before You Start` stamped over its authored `### Inputs`,
   and Transformation/Issues are invisible to the hide logic.
   `render_glue` already computes `_hidden_parts` from the tdecl
   (`render_glue.py:157`); lettering joins that seam.
   (`review_extract`'s `A–H` location regex, :180, is decided with
   this item.)

4. **The brief's unit line and seam sections derive from the type,
   not the furniture.** `brief.py:599` defaults `activity`, and unit
   discovery reads the manifest's DERIVED components — which §2b of
   A1 removes, so post-A1 the fallback chain lands on
   `definitions.DEFAULT_DEFINITION = "desktop-procedure"` and every
   v2 drafter is told "YOUR UNIT: activity" again. Coupled, not a
   follow-up. `SEAM_SECTIONS` (`brief.py:574` — "Quick
   Reference"-era titles printed into every brief) derives from the
   tdecl in the same stroke.

5. **The deliverable default dies with the template default.**
   `definitions.DEFAULT_DEFINITION` / `orchestrate.py:1346` fall
   back to `desktop-procedure` for every area's render signal; the
   OBJECTIVE names the area's deliverable(s), and an area with no
   objective-named deliverable reports that honestly instead of
   claiming desktop-procedure.

6. **Skeleton source per unit.** `PROCEDURE_SKELETON`
   (`scaffold.py:110`, the v1 seven-section file) WINS over the type
   declaration whenever it exists (`render_skeleton`, 767–781); the
   process-step path scaffolds from the declaration (or its own
   skeleton file) — `declared_parts()`'s hard-coded
   `load_type("activity")` at `scaffold.py:679` resolves per area.

Gate additions: a process-step fragment round-trips aggregate →
reconcile → render with all six parts read (no part filed under a
v1 alias, none dropped); a v2 `profile.yaml` naming process-step
parts resolves instead of refusing; the brief prints
`YOUR UNIT: process-step` and seam titles from the declaration on a
furniture-free area; the v1 golden corpus stays byte-identical.

Split out (not this build): the derived-view READERS that go quietly
empty on process-step (aggregate ctx, kits preparer, consolidation
digest) → M69; the M62 vocabulary-floor leftovers (floor-only
`ID_STRICT_RE` callers, two re-typed prefix regexes) → M70.

## Amendment A3 — build rulings (2026-08-22, two work packages)

**WP1 (the engine reads the type, A2 items 1-3):**
* `client_config.capture_type(area)`: process-step when
  `sources.central_root` resolves, else activity; a `_client` override
  would be one edit inside it. `SectionVocabulary` /
  `section_vocabulary` / `area_vocabulary` / `default_profile` derive
  profile vocabulary per type; `Profile` carries its capture type.
* `kernel.heading_resolver(type)` is the one type-aware `###` parser —
  for activity it returns `doc_model.section_of_heading` itself, so v1
  reads cannot shift a byte. Routed: orchestrate `_present_sections` /
  `profile_drift`, engagement scope digest, `aggregate.
  split_subsections`, reconcile parse/merged-section checks, render
  letters/hides/titles (plus `BODY_OMIT_REGISTERS` via the profile).
* Mandatory sections for a non-activity type derive as `scope` + every
  callout-home part (process-step: scope, transformation, controls,
  issues); activity keeps its frozen three verbatim. Process-step gets
  no invented letter aliases; letters derive from declared order and
  the review-kit `[A-H]` location regex needs no change (A-F subset).

**WP2 (capture becomes process-step, A1 items 1-4 + A2 items 4-6):**
* Scaffold skeletons render from the type declaration in v2;
  `PROCEDURE_SKELETON` is consulted only for activity. v2 default
  title "{Area} — Process Capture", subtitle "Current-state process
  capture"; v1 defaults byte-identical.
* No furniture in v2: `build_manifest(furniture=)` — central-mode
  areas get fragments + manifest only. The desktop-procedure
  definition over process-step capture was NOT already safe (the
  `_TYPE_MANIFEST_ROLE` shortcut counted v2 procedure components as
  activity entities and would have rendered wrong); the role shortcut
  now applies only when the role's type IS the area's capture type,
  so the definition reports honestly unserviceable instead.
* The brief's unit line derives from `capture_type` (the
  furniture-read is gone); seam titles translate through the type's
  declaration; live `_taxonomy/*.md` are listed as read-only inputs.
* The deliverable authority is `definitions.area_deliverable(area)`
  (v1 → desktop-procedure; v2 → first objective deliverable, else
  honest `unset`); `orchestrate.area_definition` reads it (the ticket
  named a nonexistent `_area_deliverable`). `resolve_definition`'s
  default deliberately stands — plan-view existence must not become a
  refusal.
* The node guard: `<area>/.taxonomy.json` (nodes → sha256) written at
  confirm and refreshed by `--promote-taxonomy`; reconcile check 15.5
  errors on changed/added/deleted live nodes, silent with no record.
* The confirm gate prints `CAPTURE_NOT_RENDER` in v2: "capture is not
  a render: this area records the process step by step, and the
  deliverables the objective declares are renders over it."
* Recorded for follow-up: `scaffold --sync-profile` is v1-shaped and
  would re-add derived components on a v2 area — out of scope here.
