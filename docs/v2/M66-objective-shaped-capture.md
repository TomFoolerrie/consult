# M66 — Objective-shaped capture: the deliverable declared is not the shape drafted

**Status: RECORDED** (2026-08-22) — **ruling deliberately open**; the
three candidate shapes are recorded below, none chosen.
Origin: the first live run of the v2 pipeline over the Nordhaven
synthetic engagement (`examples/nordhaven-industrial`). The objective
declared `deliverables: [findings-report]` and every document was
nonetheless scaffolded and drafted as a full seven-section desktop
procedure, under a manifest titled "— Desktop Procedures".

## Why

M41 gave the engagement an objective, and the objective's
`deliverables:` list is validated against real definitions
(`client_config.py:917–929`) and consumed by needs, agenda, analysis,
brief, client_config and engagement. **Neither `scaffold.py` nor
`orchestrate.py` reads it.** Concretely:

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
register, the analyst mints findings from captured CALLOUTS (PAIN /
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
