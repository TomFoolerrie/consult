# M39 build plan — analysis verbs

> Foundation for [`M39-analysis-verbs.md`](M39-analysis-verbs.md).
> Deterministic gate: `tests/test_findings_m39.py` (skips until
> `scripts/findings.py` exists). Ground rules as ever. The IPO fixture is
> the substrate (frozen; every test works on tmp copies).

## Design pins

- Findings live at the ENGAGEMENT root (a register-class citizen; the
  file layout is the implementer's call — `_registers/findings.yaml` or
  M30's register home, read registers.py/engagement.py first and land
  where the register machinery already points). The lifecycle M30 A1
  deferred is built here: proposed → accepted | rejected (terminal,
  kept). Grounds are MANDATORY and must resolve against the engagement
  (SRC ids in the ledger; PP/GAP callout ids in the area corpus; entity
  slugs in manifests) — refusal names the unresolvable ground.
- One direction: no findings operation may write under components/ or
  _sources/ (pinned by fingerprint).
- Candidate generators are read-only pure Python over the corpus
  (kernel-parsed, declaration-driven — the shape audit is watching):
  control gaps (steps with outputs and no CTRL), handoff friction
  (orphan outputs, shared inputs, owner changes across an artifact),
  pain inventory (every PP with its SRC ids). Generators produce
  CANDIDATES with mechanical grounds; judgment (materiality, clustering)
  is the analyst agent's.
- `findings.renderable(root)` = accepted only — the findings-report
  definition binds through it.

## Work packages

### WP-F1 — the findings module + report definition
Owns `scripts/findings.py` (new), `kernel/deliverables/findings-report.yaml`
(new), any small `definitions.py` verb admission the report needs (named
consumer), and — if the register machinery needs a findings register
entry class — the minimal additive change there (read M30's
registers.py first; do not refactor it).
Targets: TestLifecycle, TestOneDirection, TestFindingsReport.
NOTE the M38-recorded language gap (definition views need manifest
components to render): the findings-report definition should ship
loadable and serviceability-honest; RENDERING it end-to-end may hit the
same gap — if so, state it, don't force it (the gap's fix is a named
follow-up ticket, not this package).

### WP-F2 — the candidate generators
Owns `scripts/analysis.py` (new). Declaration-driven parsing (no shape
literals — derive from kernel.load_type("process-step")); the three
generators with the fixture-pinned outcomes; read-only.
Targets: TestCandidates.

### WP-F3 — the consult-analyst brief (prose; orchestrator reviews)
Owns `agents/consult-analyst.md` (new) + a self-review note
(docs/v2/notes/m39-analyst-self-review.md). The license: assess and
PROPOSE findings (via the structured return; the deterministic layer
writes through findings.propose at the human gate) — never write, never
resolve, never adjudicate a conflict (conflict support = lay out both
claims and propose a RESOLUTION QUESTION); model-pinned like the other
workers; candidates handed in precomputed (never re-derive mechanics —
the coverage-map discipline). Verbs: pain synthesis (cluster the
inventory), control coverage, conflict support, handoff friction.

## Sequencing
WP-F1 ∥ WP-F2 → WP-F3 → close-out (alpha.9) — which is also the SPINE
close-out: the v2 charter's ticket list is then fully BUILT.
