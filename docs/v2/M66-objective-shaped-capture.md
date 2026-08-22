# M66 — Objective-shaped capture: the deliverable declared is not the shape drafted

**Status: RULED, ready to build** (2026-08-22) — see Amendment A1;
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
