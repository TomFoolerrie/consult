# CONSULT

A Claude Code **plugin** that turns messy finance-process source material —
interview transcripts, prior SOPs, working notes — into a governed,
evidence-backed **process-knowledge model** ("the brain"), then projects that
model into client deliverables through **user-supplied deliverable
definitions**. Five definitions ship — the CFGI desktop procedure, a process
& controls matrix, an information request, an interview agenda, and a
findings report — and a new document shape is a new YAML file, not a new
engine.

> **v2 is built and tested** — the kernel, the definition language, the
> eight subagents, and the four skills are all in place, exercised by
> **1,199 passing tests**, with the compatibility gate green: v1's own
> desktop procedure, rebuilt through the new engine over a frozen
> engagement, is normalized-identical to the v1 golden, and all 803 v1
> tests run untouched.
> See [`docs/v2/README.md`](docs/v2/README.md) for the v2 charter and tickets
> (M33–M49); [`docs/`](docs/) holds the v1 record (M0–M32).

## The core idea — capture once, project anything

v1 pointed the whole engine at one deliverable shape: a desktop-procedure
Word document per L1 finance area. v2 inverts the flow — knowledge is
captured **once** into typed, evidence-linked entities, and documents become
**projections** you can add without touching the engine:

> **intake (tag) → survey (taxonomy + coverage + information requests) →
> capture (fill the brain, IPO-shaped, evidence-linked) → project (any
> deliverable definition)**

Three layers, and the kernel knows no domain:

1. **Definitions — user-space data.** A deliverable is a YAML file
   (`kernel/deliverables/*.yaml`) declaring its **shape** (sections),
   **bindings** (declared queries over the brain: "this table = these parts
   of these steps"), and **skin** (docx, orientation). A four-stage
   fail-loud loader checks every name against the type declarations —
   syntax, vocabulary, serviceability (an honest "not yet" report), skin
   capability — then compiles the definition to a plan.
2. **The brain kernel — deliverable-agnostic.** Entity types are YAML
   declarations under `kernel/types/` (`process-step`, `taxonomy-node`, and
   v1's `activity` written down); the parser is generic and reads whatever
   the declarations describe. Entities carry stable slugs and evidence links
   into the `SRC-` ledger; derived views are regenerated, never
   hand-maintained.
3. **Consumers.** Renderers assemble documents *from* a compiled plan;
   analysis verbs read the graph and emit findings — and never write back.

A permanent audit fails the build if document shape is hard-coded anywhere
outside kernel data.

## The backbone entity — inputs → transformation → outputs

Every deliverable is fed from one entity: the **process step**. A step
breaks where **owner, system, or control changes** — the accountability
boundary — and its inputs/outputs name their neighbouring steps, so
cross-step dependencies are derived mechanically instead of judged. The
"how" (numbered sub-steps, navigation detail, screenshots) lives one level
down, so each deliverable picks its altitude: the procedure unfolds it, the
matrix reads only the step line.

Callouts on a step follow a written **doctrine** — what earns one, encoded
in the contracts and readable by the tooling:

- **CTRL** must clear a four-field minting bar (performer / comparison /
  trigger / evidence, declared on the callout type itself). A
  control-shaped sentence stays prose plus one pointed GAP.
- **GAP** mints exactly two facts: a **conflict** (two sources disagree)
  or an **evidenced absence** (the sources confirm something is missing).
  Ranking and asking are never authored — the **needs view** renders the
  per-deliverable gap inventory from the objective and the definitions.
- **PP (pain point)** is recorded *as voiced* — attributed and evidenced,
  never assessed by the recorder.
- Sub-steps carry no callouts; a cross-owner performer is a split signal.

**Coverage is a pure function** — "does this node have enough evidence?" is
computed on demand from evidence links. There is no coverage *file* to
hand-edit and rot (the failure that killed v0).

## One engagement on disk — the ledger is truth

v1 copy-routed each source file into an area folder. v2's central mode
keeps **one** `_sources/` tree and one YAML ledger at the engagement root;
area folders hold no source files, only consumption records ("this area
read SRC-004 into this step"). The ledger mints `SRC-` ids once
(hash-deduped) and records who consumed what — a transcript spanning two
areas is *consumed twice, moved never*. v1-layout areas keep working
through a read-only dual-layout adapter, byte-identical and guarded by
characterization tripwires.

Every engagement states an **objective**: goal, target deliverables,
in-scope cycles — validated config, not decoration — carried into every
taxonomy-agent dispatch so "enough evidence" means *enough for the target
deliverables*. A business-cycle skeleton seeded from the reference taxonomy
can stand the engagement up on day one: every node claimed with zero
evidence, so coverage reads as a work plan and the information request is a
day-one PBC list. Seeded structure enters the brain only through the human
confirm gate.

## The agents, and the one license to judge

Every capture-side agent is contractually forbidden from assessing what it
records — that discipline is what keeps the record trustworthy:

| Agent | Role |
|---|---|
| `consult-intake` | tags sources into the ledger — no copies; relevance judgment survives as tags |
| `consult-taxonomist` | structure: upfront proposes the taxonomy, judges coverage/sufficiency and emits information requests *before* drafting spends tokens; ongoing, proposes reorganizations as knowledge accumulates (its own `_taxonomy/` files it writes; everything else it proposes, never executes) |
| `consult-drafter` | fills steps/procedures from sources (shared law + one path document per unit under `agents/drafting/`); two sources disagree → a conflict record, never a guess |
| `consult-dependencies`, `consult-raci` | author the two v1 judgment views |
| `consult-consolidator` | cross-procedure consistency pass, notes only |
| `consult-analyst` | **the one assessment license**: judges mechanical candidates, proposes findings — never writes into the capture layer, never resolves a conflict |

Findings live in their own register with a full lifecycle
(grounds-or-refused, terminal reject, accepted-only rendering). The
one-direction rule is structural: every findings operation is
fingerprint-tested to leave `components/` and `_sources/` byte-identical,
and a groundless finding is refused — every claim traces to
`SRC`/`PP`/`GAP` ids or it does not exist. Mechanical candidate generators
(control gaps, handoff friction, pain inventory, plus the
engagement-scoped callout-hygiene groomers) feed the analyst; a human
accepts or rejects.

## How you use it

You invoke **one** skill: **`consult-orchestrate`** — "build `<area>`" or
"continue `<area>`". You never run Python by hand. The orchestrator is a
thin coordinator: on each turn it consults a read-only Python state
advisor, performs the single next action it returns, and loops — running
deterministic Python itself, dispatching isolated subagents (each in its
own context, returning only a compact result; all taxonomy work — the
initial survey and ongoing curation — routes to the taxonomist), and stopping at
the human gates: the scope/taxonomy confirm gate, registry top-ups,
findings accept/reject, and review of the rendered document. Reviewers mark
up the `.docx` with tracked changes and comments; the return trip is
deterministic and re-dispatches only the affected drafters. Context stays
flat no matter how large the engagement grows.

## The shipped deliverable definitions

All five render end-to-end. Each is a small YAML file under
`kernel/deliverables/`; a user's fifth deliverable is a copy of one with
different bindings (dropped in `_client/deliverables/` to shadow), and the
engine never learns its name:

- **`desktop-procedure.yaml`** — v1's flagship, written down as a
  definition; gate-proven identical to v1's own output.
- **`process-controls-matrix.yaml`** — one landscape row per step: owner,
  systems, IPO edges, controls, open items. A shape v1 could never draw,
  shipped with zero engine special-cases.
- **`information-request.yaml`** — the taxonomist's coverage output as a
  client document: what we're missing, per taxonomy node.
- **`interview-agenda.yaml`** — the needs view × roles × ledger, rendered
  as questions per interviewee; generation is human-triggered, ad hoc.
- **`findings-report.yaml`** — accepted findings by theme, every claim
  citing its grounds back through the SRC chain; structurally unable to
  show a proposal or a rejection.

## Plugin layout

```
consult/
  .claude-plugin/plugin.json     plugin manifest (2.2.0)
  agents/                        8 isolated subagent definitions +
                                 agents/drafting/ (one path doc per unit)
  skills/                        consult-orchestrate (the entry point),
                                 consult-taxonomy, consult-drafter,
                                 consult-docx-builder
  kernel/                        the domain, as data
    types/                       entity-type declarations
                                 (process-step, taxonomy-node, activity)
    deliverables/                the five shipped definitions
  scripts/                       the deterministic engine (37 modules)
    kernel.py                    declared types + the generic entity parser
    ledger.py                    the engagement-root SRC ledger
    coverage_map.py              coverage as a pure function
    definitions.py               the deliverable-definition language
    render_glue.py / render.py   compiled plan → CFGI .docx
    matrix_views.py / plan_views.py  definition view builders
    analysis.py / findings.py    candidate generators + findings register
                                 (+ the analyst brief CLI)
    hygiene.py                   callout-hygiene candidate generators
    needs.py / agenda.py         the per-deliverable needs view + the
                                 interview-agenda joins
    orchestrate.py               read-only state advisor (next action)
    doc_model.py, aggregate.py, reconcile.py, brief.py, kits.py, …
                                 the v1 engine, intact underneath
  docs/                          v1 design record (M0–M32) +
                                 docs/v2/ (charter + tickets M33–M49)
  tests/                         1,199 pytest cases (803 v1 cases untouched)
  requirements.txt
```

Per-engagement **data** lives in the **user's project**, not in the plugin:
`components/<area>/` (steps or procedures, `_taxonomy/`, derived views,
`manifest.json`) plus, in central mode, the engagement-root `_sources/`
tree, its `sources.yaml` ledger, and the `_registers/` (findings). Client
data can be gitignored or kept in a private repo.

## Requirements

```bash
pip install -r requirements.txt   # python-docx, pyyaml
```

## Status

**v2 complete and under test.** The seventeen-ticket v2 campaign
(M33–M49) is built end to end — the brain kernel, centralized sources,
the definition language, the compatibility gate, the taxonomy agents,
the second deliverable, the analysis verbs, definition views, the
engagement objective, the callout doctrine, the process-step drafting
path, and the engagement-lens line (the needs view, the taxonomist
merge, the interview agenda, the research pass, the efficiency pass,
the analyst dispatch path) — with the suite at **1,199 passing**
(`python3 -m pytest`) and zero of v1's 803 tests edited across the
entire campaign. 2.0.0 and 2.1.0 merged 2026-08-15, 2.2.0 merged
2026-08-17, each on an explicit human go. See
[`docs/v2/README.md`](docs/v2/README.md) for the charter, the ticket index,
and the recorded follow-up candidates, and [`CHANGELOG.md`](CHANGELOG.md)
for the version-by-version story.

## History

Three architectures share this repository:

- **v0** — a taxonomy-driven diagnostic engine on a shared `state.json` /
  `register.json` state machine, preserved at commit **`a119d22`**
  (`git checkout a119d22` to read the tree). Its shared mutable state cost
  an entire hardening slice;
  [`docs/retrospective-v0.md`](docs/retrospective-v0.md) records what
  carried forward. The lens-conflict debt it left — when two sources
  disagree, raise a conflict rather than guess — was paid in M37.
- **v1** (M0–M32) — the desktop-procedure engine: the two-database model,
  one writer per file, fail-loud parsing, the review loop. Preserved on the
  **`v1.20-stable`** branch and still alive inside v2 — every v1 engagement
  keeps working, and the v1 render path is the standing golden for the
  compatibility gate.
- **v2** (M33–M49) — the inversion: the brain, the definition language, and
  the analysis layer, built on everything v1 got right.
