# CONSULT — Implementation Tickets

Build tickets derived from `spec.md` + the stage contracts. Each ticket is a self-contained
brief a sub-agent can build from. **Every ticket prescribes the tests the agent must write and
pass before reporting.** Read the referenced contract sections before building.

## Conventions (apply to every ticket)
- **No client data needed for the floor + most of Slice 1** (R2R sample is synthesized in T20).
- All state/register writes go through the Python commands — never hand-edit JSON.
- Scratch engagements for tests use a `__tNN__` id and are **removed at the end**; do **not**
  `git commit` from a build agent; report test output + any contract deviation.
- Match existing code style (`scripts/state_machine.py`, `improvement_log.py`). Re-validate
  schemas after touching them.
- Keep state files schema-valid (`scripts/state_machine.py validate`).

## Sequencing & dependency notes
- **Floor tickets T01–T04 all edit `scripts/state_machine.py` / `improvement_log.py` → build
  them SEQUENTIALLY** (not parallel) to avoid edit conflicts. They precede Slice-1 integration.
- LLM-stage skills (T11, T13, T14, T15, T16, T17) touch separate `skills/` dirs and can be
  built in parallel once their Python deps exist.
- T20 (integration) is last and depends on everything in Slice 1.

## Slice 1 — prove the thesis, one-way (no review loop)

| # | Title | Depends | Touches |
|---|---|---|---|
| T01 | `add-evidence` idempotency + `last_evidence_at` + dirty predicate | — | state_machine.py |
| T02 | Register write-path overhaul (JSON-native upsert, dedup_key, unmapped null-node, sync orphan-exclusion, requires_human_review fix) | T01 | improvement_log.py, state_machine.py |
| T03 | Node status shape: `improvement.*` + render/review rev markers + `consolidated_at` stamping | T02 | state_machine.py, schema |
| T04 | `status`/`next` reporting command | T03 | state_machine.py |
| T10 | `consult-ingest` v1 (transcript + docx → immutable hashed MD + YAML header) | — | scripts/ingest_normalize.py, skill |
| T11 | `consult-classifier` skill + artifact validator | T10 | skill, scripts/validate_artifact.py |
| T12 | `classify_merge.py` (deterministic merge) | T01,T02,T11 | scripts/classify_merge.py |
| T13 | `consult-consolidator` skill + flow (confirm via dedup_key, author MD, stamp consolidated_at) | T02,T03,T12 | skill |
| T14 | `consult-gap-analyzer` skill (substantive gaps) | T13 | skill |
| T15 | `consult-drafter` wiring → SOP from state/register, per L1 | T13 | skill |
| T16 | `consult-improvement-drafter` (5B) | T13 | skill |
| T17 | `consult-synthesizer` (5C: synthesis.md + `type:theme`) | T15,T16 | skill |
| T18 | Render per-L1 to Word (docx-builder wiring + evidence inline) | T15,T16,T17 | skill/script |
| T19 | `consult-run` orchestration — Slice-1 linear sequence | T04,T10–T18 | skill, scripts |
| T20 | Synthesized R2R sample + end-to-end Slice-1 integration test (regression fixture) | T19 | tests/, fixtures/ |

## Slice 2 — prove the human loop (backlog; expand when Slice 1 is green)

| # | Title | Notes |
|---|---|---|
| T30 | docx comment extraction helper (OOXML comment anchors + tracked changes) | research spike; size M–L |
| T31 | Review ingestion wiring (resolver → commands, reviewer attribution) | `generation_review_contract.md` §2 |
| T32 | Review-round-consumed marker + 2nd-round versioning | adversarial P1 #6 |
| T33 | Review-path conflict detection (`set-lens` conflict → `GAP-CONFLICT`) | adversarial P2 #11 |
| T34 | `unmapped` disposition lifecycle + `final` gate (`disposition ≠ pending`) | `classify_contract.md` §5b |
| T35 | `validate` coherence check (MD-cited IDs exist; prose lenses match state) | spec §3 |
| T36 | Structural re-scan preserves human `review_status` on `GAP-STRUCT` rows | adversarial P2 #13 |
| T37 | Generalize orchestration: linear → state-driven readiness loop | `orchestration_contract.md` §3 |
| T38 | DoD gates wired (evidence-auditor + open-SME + disposition block `final`) | spec §5 DoD |
| T39 | Register engine doc-debt: rewrite `consult-improvement-log` SKILL.md (no CSV) | spec §10 |

## Definition of done (every ticket)
Code + prescribed tests written and passing; schemas still valid; no scratch artifacts left;
a one-paragraph report of what was built, test output, and any contract deviation.
