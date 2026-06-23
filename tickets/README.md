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

## Slice 2 — prove the human loop ✅ COMPLETE

| # | Title | Status |
|---|---|---|
| T30 | docx comment extraction helper (OOXML comment anchors + tracked changes) | ✅ |
| T31 | Review ingestion wiring (extract → resolve → apply, log + consumed marker) | ✅ |
| T32 | Review edits → `mark-dirty` → re-consolidation (+ microsecond-timestamp fix) | ✅ |
| T33 | Review-path conflict detection (override applied but audited via `GAP-CONFLICT...REVIEW`) | ✅ |
| T34 | `unmapped` disposition lifecycle + machine-checkable `final` gate (`gates.py`); merges T38 | ✅ |
| T35 | `validate` coherence check (MD-cited IDs exist; front-matter lenses match state) | ✅ |
| T36 | Structural re-scan preserves human `review_status`/`owner` on `GAP-STRUCT` rows | ✅ |
| T37 | State-driven orchestration: review re-entry + gated `final` + `next --all` | ✅ |
| T39 | Register engine doc-debt: `consult-improvement-log` SKILL rewritten (no CSV) | ✅ |

## Slice 3 — Remediation & Hardening (from codebase review)

Bug fixes + robustness + doc-drift cleanup. **Grouped into waves for parallel execution.**
Tickets in the same wave touch disjoint files and can be built concurrently; tickets that
share a file are placed in different waves (per the same-file-sequential rule above).

### Wave 1 — foundation (build first, alone)
| # | Title | Touches |
|---|---|---|
| T40 | Shared atomic-write + advisory-lock IO util | `scripts/consult_io.py` (new) |

### Wave 2 — parallel (depend only on T40 where noted; mutually disjoint files)
| # | Title | Depends | Touches |
|---|---|---|---|
| T41 | `state_machine.py` hardening (init order, atomic writes, malformed-node guards, id race, ISO compare) | T40 | state_machine.py |
| T42 | `classify_merge.py` hardening (rollback/re-entrancy, conflict-gap guard, evidence path canon, silent-drop report, unmapped dedup) | T40 | classify_merge.py |
| T43 | `ingest_normalize.py` hardening (remove `exec` hack, atomic write, exclude own output, per-file isolation, table newlines) | T40 | ingest_normalize.py, clean_vtt.py |
| T44 | `review_ingest.py` bug fixes (`add-evidence` allowlist, re-apply idempotency, json guard, dead code) | T40 | review_ingest.py |
| T45 | `orchestrate.py` predicate unification + guards | — | orchestrate.py |
| T46 | `render_deliverables.py` + `gates.py` fixes (`--l1` validation, partial render, path-escape, final-file existence) | T40 | render_deliverables.py, gates.py |
| T47 | `gap_report.py` + `docx_comments.py` fixes (malformed node, temp-CSV leak, tag preserve, comment-range balance, headers) | — | gap_report.py, docx_comments.py |
| T48 | Documentation & schema drift reconciliation (stale banners, schema desc, SKILL path, template removal) | — | docs/schemas only |

### Wave 3 — after Wave 2 (run T50 before T49)
| # | Title | Depends | Touches |
|---|---|---|---|
| T50 | Finish removing CSV transport (**Option A decided**) | T47, T48 | improvement_log.py, gap_report.py, spec.md, README.md, requirements.txt |
| T49 | Test coverage hardening (schema-validate assertion, lens-conflict, phantom-ref, Slice-2 e2e, xlsx) | T41–T47, T50 | tests/, fixtures/ |

**Decisions locked** (post-review): engagement-level lock (T40); fail-closed pre-flight
validate, no merge cursor (T42); add `add-evidence` to allowlist + minimal idempotency
(non-fatal mark-dirty + pre-flight validate, no per-action ledger) (T44); `drafted_any`
gates synthesize (T45); document the docx headers/footers limitation, don't extend (T47);
**Option A** — finish removing pandas/CSV (T50).

### Follow-up (surfaced during Slice 3 review)
| # | Title | Depends | Touches |
|---|---|---|---|
| T51 | `validate` also schema-checks `register.json` (report-only; soft vocab contract preserved) | — | state_machine.py, tests/ |

> **Highest-priority real bugs** (do first within their wave): T44 (`add-evidence`
> unreachable), T46 (`--l1` no-op validation), T44 (review re-apply double-write),
> T41 (`cmd_init` dir ordering).

## Slice 4 — Cost & Runtime Efficiency (from field run: 3 real artifacts, ~$10)

Surfaced running the suite on real client artifacts. **Runtime confirmed: Claude Code hosted in
the Claude Desktop app** — has sub-agents, skills-in-sub-agents, and the **Workflow** tool. The
keystone is **T57** (the deterministic fan-out Workflow): T54 wires `consult-run` to invoke it,
and T55 (schema emission) + T56 (`budget.spent()` cost) plug into its seams. That one substrate
makes delegation structural, unlocks valid-by-construction JSON, and exposes per-phase cost.

**Status: specs LOCKED, build DEFERRED** (owner decision). Reviewed by 5 sub-agents; review fixes
+ the four design decisions below are folded in. No implementation until the owner says go.

**Build order (when greenlit):** Wave A (parallel, no deps) = T54 Tier 1 prose + T55 Phase 1
`quote`-trim → Wave B (foundation) = **T57** → Wave C (plug in) = T54 Tier 2 wiring + T55 Phase 2
+ T56 → Wave D (last) = **T58** integration. Same-file rule: T54 & T57 touch different files.

| # | Title | Depends | Touches |
|---|---|---|---|
| T54 | Orchestrator delegation enforcement — blocking prose + explicit content prohibition (Tier 1, a *nudge* not a gate) + wire `consult-run` to the committed `.claude/workflows/consult-fanout` by name (Tier 2) | T57 (for Tier 2) | skills/consult-run |
| T57 | **Fan-out Workflow scaffold** (foundation) — correct per-stage dispatch (classify=#docs, consolidate=#nodes, draft=2×#L1s, synthesize=1); classify `merge` + consolidate **emit-JSONL→serial-apply** post-steps; 5 custom agent types; schema + budget seams; structural human-gate guard. NB: draft/synth workers DO write state via `state_machine.py`. | — | .claude/workflows, .claude/agents (5), consolidate_merge.py (new) |
| T55 | Classify artifact emit efficiency — drop redundant `quote` (Phase 1, no dep) + constrained emission via the `consult-classifier` agent type + `{schema}` (Phase 2, NDJSON = fallback) | T57 (Phase 2) | schemas/classify_artifact.schema.json, skills/consult-classifier, classify_merge.py, validate_artifact.py |
| T56 | Per-phase cost instrumentation — `budget.spent()` deltas persisted to content-free `cost_map.json` + input-size complement | T57 | .claude/workflows, orchestrate.py, *_inputs.py gatherers, cost_report.py (new) |
| T58 | **Slice-4 integration & regression** (build last) — given identical *stubbed* LLM outputs, the workflow and prose dispatch paths produce byte-identical **spine** output (state/register/render, normalized); LLM-authored MDs validate structurally only; constrained emission validates; gates fire; cost map content-free | T54, T55, T56, T57 | tests/, fixtures/ |

> **Decisions locked** (owner, post-review): **(A)** skill invocation = **custom agent types** —
> 5 `.claude/agents/` defs preloading their skills, tool-scoped, `agent()` sets `agentType`; **(B/D)**
> consolidate = **parallel emit to per-node JSONL → deterministic serial apply** (no concurrent
> shared-state writes; resolves the parallelism-vs-conflict tension; classify pattern generalized);
> **(C)** `consult-run` invokes the **committed named workflow** `.claude/workflows/consult-fanout`
> by name. Build sequencing: **specs locked, build deferred**.

> **Runtime note (resolved):** earlier drafts hedged a "Desktop has no sub-agents / no constrained
> output / no token meter" branch — **all three are false for Claude Code**. The Workflow tool
> provides `agent({schema})` (valid-by-construction JSON) and a `budget` object (`budget.spent()`),
> confirmed against the live tool contract. Human-in-the-loop is preserved by scoping each Workflow
> to **one fan-out stage**, never the whole engagement (the render gate stays a human hand-off).

## Deferred / optional (not blocking a working system)

| Area | Notes |
|---|---|
| Ingest format zoo | v2 (PDF/PPTX/XLSX) + v3 (images/OCR) handlers; ingest manifest + supersession |
| Live full-fan-out hardening | bounded concurrency, atomic artifact writes (per `orchestration_contract.md` §6) |

## Definition of done (every ticket)
Code + prescribed tests written and passing; schemas still valid; no scratch artifacts left;
a one-paragraph report of what was built, test output, and any contract deviation.
