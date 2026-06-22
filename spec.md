# CONSULT — Full Work Cycle Plugin: Specification

> Status: **Both slices complete.** Slice 1 (the one-way pipeline: ingest → classify
> → merge → consolidate → gaps → draft → synthesis → render) and Slice 2 (the human
> Word-review loop: docx comments → ingest → apply → re-consolidate → gated `final`)
> are built, test-verified, and demonstrated on a live R2R sample
> (`engagements/r2r-demo`). The Slice-1 e2e regression (`tests/test_slice1_e2e.sh`)
> stays green under all Slice-2 additions. Remaining is optional scope only: the
> ingest format zoo (PDF/PPTX/XLSX/images) and other §10 deferrals. Build status
> inline: ✅ built · ◻ deferred/optional. Tickets in `tickets/`.
> Scope: a Claude Code plugin that runs a finance-consulting engagement end to
> end: intake → diagnose against the CFGI work taxonomy → output two work streams
> (1) Desktop Procedures & SOPs, (2) Process Improvement Opportunities.
>
> **Design artifacts** (this spec is the index): `ingest_contract.md` (S1) ·
> `classify_contract.md` (S2) · `consolidate_contract.md` (S3) ·
> `generation_review_contract.md` (S5–6) · `orchestration_contract.md` (run loop),
> with draft schemas under `schemas/`.

---

## 1. Goals & Philosophy

Turn raw engagement inputs (call transcripts, client documents, data exports) into
two polished, CFGI-branded deliverable streams, with a durable, inspectable **source
of truth** in between.

Design principles:

1. **State files are the source of truth; the agent owns every write.** Structured
   state lives in `.json` files, **only ever mutated by the agent through the
   state/register Python commands** — never hand-edited, never edited by a human
   directly, and **never via a CSV/Excel round-trip** (that mechanism is dropped).
   Humans review on **Word documents** rendered from the analysis MDs and deliverables;
   the LLM **ingests the reviewed Word (body + comments)** and applies the resulting
   updates back through the same commands. One Markdown file per **L2** node holds the
   human-readable synthesis (LLM-owned narrative).
2. **Token efficiency through granular Python.** The model must never load a whole
   state file into context to make a change. The scripts expose **granular discovery**
   (query/get a slice) and **granular mutation** (set one field per call). Deterministic,
   repetitive, or bulk work (parsing, normalizing, state CRUD, validation, assembly) is
   done in Python — not by burning model tokens. The agent **writes/extends Python as
   needed**; we provide starting templates, not a frozen toolset.
3. **LLM for judgment.** Classification, synthesis, gap reasoning, and drafting are done
   by the model. Bulk/parallel reading is **fanned out to Sonnet sub-agents** — one per
   document — each returning a compact structured artifact (yaml/json/md). State
   mutation is *not* a sub-agent task: it is deterministic Python the orchestrator calls
   directly.
4. **Idempotent stages.** Each stage reads state, does its job, writes state back.
   Re-running a stage is safe and only updates what changed. Machine-generated records
   (e.g. structural gaps) use **stable IDs** so re-runs update rather than duplicate.
5. **Everything lives in this repo**, including engagement state (under `engagements/`).

---

## 2. The Taxonomy (diagnostic backbone) ✅

Single source of truth: **`reference/taxonomy.yaml`** — structure only.
Counts: **7 L1 domains · 37 L2 sub-functions · 212 L3 activities.**

Hierarchy:

- **L1** — 7 finance domains (kebab-case `id`):
  `procure-to-pay` · `order-to-cash` · `record-to-report` · `fpa` · `treasury` ·
  `tax` · `risk-policy-controls`
- **L2** — sub-functions within each L1, each with a kebab-case `id`. **This is the
  unit of work** — one MD file and one state node per L2. State-node keys are
  `{l1_id}.{l2_id}` (e.g. `record-to-report.close`).
- **L3** — detailed activities within each L2, a free-form list of names.

**Baseline ratings sidecar: `reference/taxonomy_baselines.yaml`.** The CFGI deck's
generic color-coded ratings (`pain_point` / `automation` / `capability` /
`operating_model`) are preserved here, keyed by `{l1_id}.{l2_id}` then L3 name so they
join back to the core. These are **generic deck baselines, not engagement-specific** —
engagement lens values are filled per engagement into `state.json`.

> **Hard guardrail (credibility):** baselines **never** seed a lens value or a finding, and are
> **never** shown to a classifier/consolidate sub-agent as a prior (anchoring risk). If
> surfaced at all, only as a clearly-labeled **external benchmark**, visually separate from the
> observed lens — never merged into a client finding. Asserting a generic "high pain" rating
> the client never voiced destroys trust in the whole deck.

The 5 diagnostic lenses (the deck's 5 maps), filled per engagement at the **L2** level:

| Lens | Question | Values |
|------|----------|--------|
| `current_state` | What work is done today? | present / absent |
| `process` | Pain point or strength? | pain_high / pain_med / pain_low / strength |
| `automation` | Machine vs human? | machine / mixed / human |
| `capability` | New vs existing work? | new / existing |
| `operating_model` | Central vs local? | central / mixed / local |

These map onto the engagement framework: **Standardization (Process),
Centralization (People), Human & Machine (Technology), Capability Build (New Work).**

> The "Regional" taxonomy variant was dropped: the source PDF contained no regional
> content (different L1 naming, no region columns). `taxonomy.yaml` is the sole authority.

> **Optional enrichment (classification aid):** L1 carries a `description`; L2 does not.
> Adding a short `description` (and optional `keywords`/synonyms) per L2 would improve
> Stage 2 match precision. Purely additive — the only taxonomy change worth considering,
> and even that is optional. The taxonomy is never modified at pipeline runtime.

---

## 3. Source of Truth: a three-layer model

Per engagement, under `engagements/{engagement_id}/`:

### Layer 1 — node tracker `state.json` ✅ (owned by `scripts/state_machine.py`)

The diagnostic backbone. One node per L2, keyed `{l1_id}.{l2_id}`, seeded for **every**
L2 at init (even if empty / `coverage: none` — an empty node *is* a finding). Per node:

```jsonc
"record-to-report.close": {
  "l1": "record-to-report", "l1_name": "Record to Report",
  "l2": "close", "l2_name": "Close",
  "coverage": "none",                        // none | partial | covered (derived)
  "coverage_override": null,                 // manual override; preserved across sync
  "evidence": [ { "source": "ingested/kickoff.md", "loc": "L42-58", "note": "..." } ],  // ref = source#loc → ingested/kickoff.md#L42-58
  "lenses": { "current_state": null, "process": null, "automation": null,
              "capability": null, "operating_model": null },
  "items":  { "improvements": [], "gaps": [], "screenshots": [] },  // links to register
  "counts": { "improvements": 0, "gaps": 0, "screenshots": 0 },
  "sop":    { "status": "not_started", "path": null, "rev": 0 },
  "node_md": "nodes/record-to-report/close.md",
  "updated": "..."
}
```

`sop.status` enum: `not_started → drafting → draft → in_review → revised → final`.
Validated against `schemas/engagement_state.schema.json`. ✅

**Coverage is derived** (by `sync`) from node contents, unless `coverage_override` is set
(which takes precedence and is preserved across sync). **Gaps are absences (open
questions/todos) and never count toward coverage** — only evidence, lenses, and
substantive items (improvements/screenshots) do:
- `none` — no evidence **and** no substantive items
- `covered` — has evidence **and** all 5 lenses set
- `partial` — anything in between (items but no evidence, evidence but incomplete lenses)

> This is what keeps the "empty node ↔ coverage:none" invariant true even after a
> structural-gap scan writes a gap row onto every empty node.

> **Region note:** the *taxonomy* regional variant was dropped (§2), but each engagement
> still carries a `region` attribute (`init --region NA`) — it's an engagement property,
> not a taxonomy axis.

### Layer 2 — unified item register `register.json` ✅ (owned by `improvement_log.py`)

A flat list of every item that hangs off an L2 node, discriminated by `type`:

- `improvement` — a process improvement opportunity (Stream B)
- `gap` — a gap / validation item (from the drafter gap tags / structural scan)
- `screenshot` — a screenshot placeholder (SC-IDs)
- `unmapped` — client content that fits **no** L2 node (null `l1_cycle`/`l2_process`); carries
  an `owner`, surfaced for triage in the gap report, **never** auto-bucketed — the safety net
  against the taxonomy silently dropping client reality. In the schema ✅; **build prereq:** a
  null-node `add-item` path. Closed only when **dispositioned** (reclassified to an L2 / converted
  to a finding / accepted out-of-scope) — see `classify_contract.md` §5b.

Each row links to its node via `l1_cycle` / `l2_process` (taxonomy slugs). The 26-field
schema (validated against `schemas/item_register.schema.json`):

```
id, type, tag, date_identified, source,
l1_cycle, l2_process, l3_activity,
observation_pain_point, root_cause, recommended_action,
impact_type, estimated_impact_benefit, effort, priority,
owner, phase, escalation_status, process_owner_contacts,
notes_next_step, record_status, review_status, requires_human_review,
last_modified_by, last_modified_at, change_notes
```

`tag` is polymorphic: for `improvement` it names the **lens** addressed
(`process`/`automation`/`operating_model`/`capability`); for `gap` it is a normalized
**gap tag** (e.g. `system_unknown`, `owner_unknown`) mapped to a reporting category.
The drafter's bracketed tags auto-normalize on import (`[[GAP — SYSTEM UNKNOWN]]` →
`system_unknown`). Controlled-vocab validation is **non-fatal**: invalid values flag the
row for human review (`requires_human_review=true`) rather than rejecting it, keeping the
register extensible.

**Register writes are agent-driven** through the state/register commands (`add-item`,
`update-json` as an internal write primitive) — there is **no human CSV/Excel
round-trip**. The human-review surface is the **Word renderings** (per-L2 analysis MDs
and the SOP/improvement deliverables); reviewed Word docs are ingested by
`consult-review-comment-resolver` and applied back through the commands. `state.json`
is internal machinery — humans never edit it directly.

### Layer 3 — per-L2 synthesis `nodes/{l1}/{l2}.md` ✅ (LLM-owned)

The consolidated narrative for one L2: what we learned, evidence digest, diagnosis across
the 5 lenses, open gaps. Markdown with a small YAML frontmatter block mirroring the state
node's key fields (self-describing and diffable). Seeded as a stub at init with the L2's
L3 activities pulled from the taxonomy.

**Invariant:** every L2 has exactly one state node and one MD file. ✅ (checked by
`state_machine.py validate`).

### Precedence & coherence (structured ↔ narrative)

The structured layers and the narrative MD are two representations of one diagnosis and can
drift, so the rule is explicit:

- **`state.json` / `register.json` are authoritative for *facts*** (lenses, coverage,
  evidence, findings). The node MD is authoritative for *prose*. **On conflict, structured
  state wins and the MD is re-rendered** from it.
- Findings referenced in an MD must cite their **register ID** (not restate the data).
- `validate` gains a **coherence check** ◻: every register ID cited in a node MD exists, and
  every lens/finding asserted in prose has a matching state/register record. This is what
  makes drift *detectable* rather than silent — critical the moment a human edits a Word
  narrative in review.

### Evidence references

Evidence is recorded as a node-evidence entry (`source` = ingested doc path, `loc` =
`Lstart-Lend`) and on register rows' `source`, composing to the canonical form
**`path#Lstart-Lend`** (e.g. `ingested/kickoff.md#L42-58`). Evidence refs **must render
inline** in the Word review docs — reviewers validate conclusions *with* their source, never
blind.

**Evidence tiering (defensibility):** each evidence entry / finding carries an `evidence_tier`
— `verbal` (a transcript assertion), `documentary` (a policy/doc), or `system_observed`. A
transcript line is *traceable* but a single uncorroborated assertion. **Control claims and
procedure-critical steps require ≥ `documentary`** or carry an open validation gap — a control
attested only verbally must not look identical to one backed by a policy/system. Effort × Impact
on improvements is **`directional` pending SME sizing** unless a quantified source exists
(never a hard number from LLM judgment).

---

## 4. State-management command surface (token-efficient API)

All state/register reads and writes go through Python. The model issues narrow commands
and gets compact output — it never round-trips a whole file through context.

### `scripts/state_machine.py` (node tracker)

| Command | Kind | Purpose |
|---|---|---|
| `init` ✅ | seed | Seed `state.json` + `register.json` + node MD stubs + deliverable dirs from the taxonomy. |
| `sync` ✅ | derive | Roll **active** register rows (not archived/inactive/deleted-pending) up into node item links/counts; recompute coverage; report orphan rows. |
| `show` ✅ | read | Coverage summary. |
| `validate` ✅ | read | Node set vs taxonomy + JSON Schema check. ◻ adds a coherence check (MD-cited register IDs exist; prose lenses/findings match state). |
| `get-node` ✅ | discovery | Return one node (compact, or `--json`), not the whole file. |
| `query` ✅ | discovery | List node keys matching ANDed filters (`--coverage`, `--lens-missing`, `--has-gaps`, `--has-improvements`, `--l1`, `--count`). |
| `set-lens` ✅ | mutate | Set/clear one lens value on a node (schema-validated). |
| `add-evidence` ✅ | mutate | Append an evidence entry to a node; stamps `last_evidence_at`. ◻ must **dedup by ref** (idempotency the classify merge depends on). |
| `set-coverage` ✅ | mutate | Manual coverage override (writes `coverage_override`; `sync` preserves it; `auto` clears it). |
| `set-sop` ✅ | mutate | Update SOP deliverable status/path/rev. |
| `add-item` ✅ | mutate | Add a register row through `improvement_log.py` then auto-`sync`; stable auto IDs (`IMP-/GAP-/SC-NNNN`); orphan node keys rejected. |

### `improvement_log.py` (item register) ✅

`update-json` · `remove` · `validate` remain as **agent-driven** write/QC primitives. The
granular `add-item` ✅ convenience lives in `state_machine.py` (routes through `update-json`
→ auto-`sync`). The **human CSV import path is dropped** — `update-json` is now only an
internal write primitive (target: refactor to a JSON-native upsert so CSV transport goes
away entirely). `build-xlsx` is retained only as an optional read-only snapshot, **not** a
review round-trip.

---

## 5. Pipeline (stages)

```
   INGEST → CLASSIFY → CONSOLIDATE → GAP DIAGNOSE → DRAFT(×2) → REVIEW → OUTPUT
   [py]      [llm]       [llm]          [py+llm]      [llm]      [llm]    [py]
     \________________ all read/write state via state_machine.py / register __________/
                                                        ▲                  │
                                        Word review (body + comments) ◀─────┘
                                  ingested by consult-review-comment-resolver,
                                  applied back through the agent commands
```

### Essential workflow (the human-in-the-loop loop)

The end-to-end loop, with **no CSV/Excel round-trip** — humans review on Word, the LLM
ingests it, and the agent applies every change through the commands:

1. **Init** the engagement (`state_machine.py init`).
2. **Ingest** — drop raw files of any format; `consult-ingest` normalizes each to a clean
   MD with a YAML header under `ingested/` (Python; templates the agent can extend).
3. **Classify** — fan out one sub-agent per ingested doc; each *reads* the doc and *returns*
   a structured artifact (which L2 nodes it touches, lens signals, evidence spans `path#L-L`,
   candidate findings, and **`unmapped`** content that fits no L2). The orchestrator applies
   it via `set-lens` / `add-evidence` / `add-item` (unmapped → `type: unmapped` register rows
   with an owner). Sub-agents never touch state. The taxonomy is read-only.
4. **Consolidate** — per L2 with new evidence, author `nodes/{l1}/{l2}.md`: the narrative
   analysis (what we learned, the 5-lens diagnosis incl. pain points, called-out
   improvements/gaps **referencing register IDs**). Structured facts live in state/register;
   prose lives in the MD; they stay coupled.
5. **Gap diagnose** — `gap_report.py scan` (structural) + `consult-gap-analyzer` (substantive)
   → `type: gap` register rows + `gap_report.md` (incl. an **unmapped Triage** section).
6. **Draft** — 5A SOPs (`consult-drafter`) and 5B improvements (`consult-improvement-drafter`)
   from state/register.
7. **Render to Word** — `consult-docx-builder` renders the deliverables per **L1 cycle**
   (the review unit; the drafter's L1-Level mode already does this), with **evidence refs
   inline** and a reviewer-facing **change log** of what moved since the last round.
8. **Human review in Word** — reviewers comment/edit the per-L1 docs.
9. **Ingest the review** — `consult-review-comment-resolver` extracts the reviewed Word
   (**body text + tracked comments** — LLM-mediated docx ingestion), attributes changes to a
   reviewer, and the agent applies them back through the commands. No CSV.
10. **Re-run** any stage idempotently; assemble **final output** to Word.

Steps 7–9 are the review loop that replaces the former Excel/CSV reimport.

### Stage 0 — Init ✅
`python scripts/state_machine.py init --engagement X --region NA` seeds `state.json`,
`register.json`, and empty node MDs for every L2.

### Stage 1 — Ingest (Python, "standardize to MD") ◻
A **single `consult-ingest` skill** takes raw files of any format (VTT/transcripts, DOCX,
PDF, PPTX, XLSX/CSV, images) and emits, for each, a clean Markdown file with a **YAML
header** under `engagements/{id}/ingested/`. Driven by `scripts/ingest_normalize.py` with
**seeded Python handlers the agent extends per format**; it **subsumes** `consult-transcript-cleaner`
(`clean_vtt.py` ✅) as the transcript handler. Ingested MDs are **immutable, source-hashed
artifacts** (one source → one MD, never rewritten) with **provenance markers** back to the
original (page/slide/sheet) — this is what satisfies Stage 2's `path#Lstart-Lend`
line-stability requirement. Format/handler details, the header schema, phasing, and a worked
example are in **`ingest_contract.md`** (+ `schemas/ingested_header.schema.json`) ✅ design-drafted.

### Stage 2 — Classify (LLM fan-out, "one Sonnet per doc") ◻
For each ingested doc, launch a sub-agent that **reads it and returns** a compact structured
artifact: which L2 nodes it touches, candidate evidence spans, lens signals, candidate
findings, and **`unmapped`** content that fits no L2 node. The orchestrator applies the
artifact into state via the granular mutation commands — unmapped content becomes
`type: unmapped` register rows with an owner (never auto-bucketed into a nearest L2, never
extends the taxonomy). **Sub-agents never write state.** The artifact schema, the
deterministic merge rules (2b), and a worked example are specified in
**`classify_contract.md`** (+ `schemas/classify_artifact.schema.json`) ✅ design-drafted.

### Stage 3 — Consolidate (LLM synthesis) ◻
Per **dirty L2** (new evidence), one sub-agent **confirms staged findings** into the register
(dedup/judgment gate; IDs assigned *before* the MD cites them) and **authors the node MD**
(diagnosis narrative citing register IDs + evidence refs), then sets `node.consolidated_at`.
Structured state wins; the MD is its render. Specified in **`consolidate_contract.md`** ✅
design-drafted.

### Stage 4 — Gap Diagnose (Python + LLM) ◻
`scripts/gap_report.py scan` mechanically finds structural gaps (nodes with
`coverage:none`, missing lenses, no evidence, SOP not started) and writes them into the
register as `type: gap` rows with **stable IDs** (`GAP-STRUCT-{l1}-{l2}-{kind}`), then
emits `deliverables/gap_report.md` (incl. an **Unmapped Triage** section listing
`type: unmapped` rows with owners). The LLM `consult-gap-analyzer` runs **after consolidate**
(it needs the synthesis) and adds substantive gaps (contradictions, thin/single-source
evidence, undocumented controls, conflicting lens signals) as further gap rows
(`consolidate_contract.md` §7).

### Stage 5 — Draft, two work streams (LLM, per L1) — 5A ✅ (drafter) · 5B ◻
- **5A SOP / Desktop Procedures** (`consult-drafter` ✅, L1-Level mode) — from the L1's node
  MDs + lenses + register rows (improvements→App. B, gaps→App. C, screenshots→App. D, pain
  points→App. A); canonical SOP per the Quality Checklist DoD; writes back `sop.*`.
- **5B Improvement Opportunities** (`consult-improvement-drafter` ◻) — from register
  `type:improvement` rows grouped by lens: Finding → Recommendation → Effort × Impact → Owner.

Specified in **`generation_review_contract.md`** ✅ design-drafted.

### Stage 5C — Synthesis & themes (LLM, the decision layer) ◻
The 5A/5B streams are bottom-up enumerations; a client pays for a **point of view**. Stage 5C
produces `deliverables/synthesis.md`: an **executive summary**, an **effort × impact
prioritization** of all improvements (quick-wins vs. 0–6mo vs. 6–18mo **roadmap**, using the
register `effort`/`priority`/`phase` fields as the sequencing spine), and a per-L1
**current → future operating model** summary driven off the lens scores (esp. `capability:new`).
It also lifts **cross-cutting findings** the per-L2 grid would shred (e.g. "no master-data
single source of truth across cycles") into `type:theme` register rows that **reference
multiple nodes** (`related_nodes[]`). This is what turns the binder into a recommendation.

### Stage 6 — Review & Output
Render deliverables to CFGI-branded Word **per L1 cycle** (`consult-docx-builder` ✅; the
review unit — the drafter's L1-Level mode already produces one doc per cycle). Each render
carries **evidence refs inline** and a **change log** (reviewer-attributed, what moved since
the last round). Humans review **in Word** (edits + tracked comments).
`consult-review-comment-resolver` ✅ performs the **LLM-mediated docx ingestion** —
extracting body text *and* tracked comments (needs a docx-comment extraction helper) into
structured updates the agent applies back through the commands, attributed to a reviewer
(substance changes mark nodes dirty → re-consolidate/redraft next loop).
**Gates before `final`:** `consult-evidence-auditor` ✅ passes (procedural claims supported),
no open `requires_human_review` / SME items, every `unmapped` row **dispositioned**
(`disposition ≠ pending` — a machine-checkable field, *not* merely "has an owner"). Final assembly to
Word — one document per work stream, plus the gap report. **No CSV round-trip.**
(`generation_review_contract.md`.)

### Deliverables & Definition of Done

The client receives **four artifacts**: the **Synthesis** (exec summary + prioritized roadmap +
current→future, Stage 5C — the lead document), Stream A (SOP / Desktop Procedures), Stream B
(Process Improvement Opportunities), and the **Gap Report** — all CFGI-branded Word.

**SOP stream DoD** = the drafter's **Quality Checklist** (`consult-drafter/SKILL.md`, *not*
the handlebars shell in `references/`): scope level stated; canonical section order; Source
Materials populated; each procedure has A–H sections (or a logged gap); no unsupported
procedural claims; body gap tags reflected in **Appendix C** (Gap/Validation Log); pain
points in **Appendix A**; improvements in **Appendix B**; screenshots in **Appendix D**;
Cross-Reference Matrix populated; ready for docx.

**Improvement stream DoD** = every improvement row has Finding → Recommendation →
Effort × Impact → Owner (register fields non-empty), tied to a lens; Effort×Impact labeled
`directional` unless quantified-source-backed.

**Synthesis DoD** = exec summary present; every improvement placed on the effort×impact /
roadmap; per-L1 current→future stated; cross-cutting `type:theme` findings surfaced.

**Evidence DoD** = every control claim and procedure-critical step is ≥ `documentary` tier or
carries an open validation gap (a verbal-only control is not "done").

**Engagement completeness rubric** (not "100% covered" — `coverage:none` is a valid
finding): every L2 node is *triaged* (covered, or an explicit gap explains why not); every
`unmapped` row **dispositioned** (reclassified/converted/out-of-scope — not merely owned); all
evidence refs resolve; evidence-auditor passes; no open SME-validation items. ◻ to wire as gates.
Every review/consolidate round appends to the required change log
`deliverables/review_log.md`. ◻ to wire as gates.

> Cleanup: `references/canonical_sop_deliverable_template.md` is a redundant handlebars
> variable-catalog shell that contradicts the SKILL.md's "produce completed Markdown"
> instruction — reconcile or remove.

---

## 6. Skills (capabilities)

Existing ✅:

| Skill | Role in pipeline |
|-------|------------------|
| `consult-transcript-cleaner` | Stage 1 — transcript → clean MD (`clean_vtt.py`) |
| `consult-improvement-log` | Layer 2 — the unified item register engine (`improvement_log.py`) |
| `consult-state-machine` | Layer 1 — single skill surface over `state_machine.py` + register (discovery + mutation; orchestrator-driven) |
| `consult-drafter` | Stage 5A — SOP drafting (templates + evidence/gap rules) |
| `consult-evidence-auditor` | Stage 6 — evidence completeness audit |
| `consult-review-comment-resolver` | Stage 6 — resolve reviewer comments |
| `consult-docx-builder` | Stage 6 — MD → CFGI-branded Word |

Built in Slice 1 ✅:

| Skill | Role |
|-------|------|
| `consult-run` | Orchestration — Slice-1 linear `orchestrate.py next` advisor + playbook |
| `consult-ingest` | Stage 1 — multi-format normalizer (`ingest_normalize.py`, immutable hashed MD) |
| `consult-classifier` | Stage 2 — one sub-agent per doc → artifact (+ `validate_artifact.py`); merge = `classify_merge.py` |
| `consult-consolidator` | Stage 3 — confirm findings + author node MD (`consolidate_inputs.py`) |
| `consult-gap-analyzer` | Stage 4 — substantive gaps (structural = `gap_report.py`) |
| `consult-improvement-drafter` | Stage 5B — improvements by lens (`draft_inputs.py`) |
| `consult-synthesizer` | Stage 5C — synthesis.md + `type:theme` (`synthesis_inputs.py`) |

Planned ◻ (Slice 2):

| Skill | Role |
|-------|------|
| review ingestion | docx comment extraction → resolver → apply via commands (T30–T33) |

---

## 7. Repo layout (current + planned)

> ✅ paths exist on disk; ◻ paths are planned. `engagements/` is created on first `init`.

```
/
├── .claude-plugin/plugin.json
├── spec.md                          ← this file
├── .gitignore                       ← register backups, workbooks, build artifacts
├── reference/                       ← CFGI IP, static
│   ├── taxonomy.yaml                ← ✅ single source of truth (structure)
│   ├── taxonomy_baselines.yaml      ← ✅ deck baseline ratings sidecar
│   └── cfgi_brand_identity.md
├── schemas/                         ← ✅
│   ├── engagement_state.schema.json
│   └── item_register.schema.json
├── scripts/                         ← ✅ state_machine.py (+ ingest/gap_report planned)
├── templates/                       ← ◻ SOP / improvement / gap-report skeletons
├── skills/                          ← existing + planned (see §6)
└── engagements/                     ← STATE LIVES HERE, in-repo
    └── {engagement_id}/
        ├── state.json               ← Layer 1 (machine)
        ├── register.json            ← Layer 2 (machine; agent-written, no CSV round-trip)
        ├── ingested/                ← normalized MD per raw artifact
        ├── nodes/{l1}/{l2}.md       ← Layer 3 (human-readable, LLM-owned)
        ├── classify/                ← per-doc artifacts {hash}.artifact.json (Stage 2)
        └── deliverables/
            ├── synthesis.(md|docx)  ← decision layer (Stage 5C, lead doc)
            ├── gap_report.(md|docx)
            ├── review_log.md        ← required change log (every consolidate/review round)
            ├── sop/                 ← Stream A
            └── improvements/        ← Stream B
```

---

## 8. Resolved decisions & open items

Resolved:

1. **Region model** — dropped; `taxonomy.yaml` (7 L1) is the sole authority.
2. **L2 slug canonicalization** — kebab-case `id` generated per node in `taxonomy.yaml`;
   that file is the naming authority. State keys are `{l1_id}.{l2_id}`.
3. **Improvement/gap unification** — one register, discriminated by `type`; gaps and
   improvements (and screenshots) are first-class rows, not node-embedded strings.
4. **Write discipline** — JSON is **agent-written only**, through the state/register
   commands. **No CSV/Excel human round-trip.** Humans review on Word; the LLM ingests the
   reviewed Word (body + comments) and applies updates through the commands.
5. **Evidence span format** — `path#Lstart-Lend` (node evidence `source` + `loc`; register
   `source`). Must render inline in review docs. Line-stability guaranteed by **immutable,
   source-hashed ingest artifacts** (`ingest_contract.md`).
6. **Structured↔narrative precedence** — structured state wins on conflict; MD re-rendered;
   findings cite register IDs; `validate` gains a coherence check (§3).
7. **`unmapped` content** — first-class register `type: unmapped` (null node, owner), surfaced
   in the gap report's Unmapped Triage; never auto-bucketed (§3, §5).
8. **Review unit** — per **L1 cycle** (decoupled from per-L2 storage); the drafter's L1-Level
   mode already renders this.

Open:

1. **Register write primitive → JSON-native** — `add-item`/`gap_report.py` still feed
   `update-json` via a temp CSV. Refactor to a direct JSON upsert so CSV transport is gone
   entirely (human CSV import is already dropped). `build-xlsx` stays only as optional read-only.
3. **docx comment extraction** — Stage 6 review ingestion needs a helper that pulls **tracked
   comments** (not just body text) out of reviewed Word docs for `consult-review-comment-resolver`.
4. **Machine-record ID schemes** — `add-item` manual `IMP-/GAP-/SC-NNNN`; `gap_report.py` owns
   `GAP-STRUCT-*` (structural); `classify_merge.py` owns `GAP-CONFLICT-*` (lens conflicts).
   Distinct prefixes → no collision (**resolved**).
11. **Prereq build tasks the contracts lean on** (S-sized, on the slice's critical path — must
    precede the R2R integration test): (a) register `type:unmapped` **null-node add path**
    (`add-item` rejects null nodes today); (b) **`add-evidence` ref-dedup** + `last_evidence_at`
    stamp; (c) evidence-specific **diagnosis-dirty** signal (`last_evidence_at > consolidated_at`)
    + Stream-B `improvement.*` node status (parallel to `sop.*`).
5. **Engagement state in git** — kept in-repo. Decide whether real client engagements are
   committed or git-ignored per-engagement (backups already ignored).
6. **Screenshot items** — supported as a register `type`; decide whether they live in the
   register or stay solely in the SOP's Appendix D when Stage 5A integration lands.
7. **Optional L2 taxonomy enrichment** — add per-L2 `description`/`keywords` to aid Stage 2
   classification (additive; see §2).
8. **Review versioning** — round-over-round diff + reviewer-attributed change log surfaced in
   the Word render; re-runs must not silently overwrite human edits. Define rev semantics
   (node-level, beyond `sop.rev`).
9. **DoD gates** — wire evidence-auditor pass + zero open SME/`requires_human_review` items as
   hard gates before `final` (§5 Deliverables & DoD).
10. **Drafter shell template** — reconcile/remove the redundant handlebars
    `canonical_sop_deliverable_template.md` (§5 cleanup note).

---

## 9. Source documents

- `Work_Taxonomy__Overall.pdf` → `reference/taxonomy.yaml` (+ `taxonomy_baselines.yaml`).
- `BT_Business_Cycle_Taxonomies_Regional.pdf` → dropped (no regional content).
- `CFGI_Brand_Identity.md` → `reference/cfgi_brand_identity.md` (colors, type, tables, callouts).

---

## 10. Roadmap & build plan

### Status snapshot

**Slice 1 is built end to end** (tickets `T01–T20`, all green): the correctness floor
(idempotent `add-evidence`, register write-path/upsert, node status, `status`/`next`), the
full pipeline (`consult-ingest` → `consult-classifier` + `classify_merge.py` →
`consult-consolidator` → `gap_report.py` + `consult-gap-analyzer` → `consult-drafter` +
`consult-improvement-drafter` → `consult-synthesizer` → `render_deliverables.py`), the
`consult-run` linear orchestration advisor, and a deterministic R2R end-to-end regression
test (`tests/test_slice1_e2e.sh`, idempotent). All S1 build-hardening items below are done.

**What remains: Slice 2** — the human Word-review loop (T30–T39): docx comment extraction,
review ingestion + reconciliation, versioning/`review_log`, the `unmapped` disposition gate,
the `validate` coherence check, the DoD `final` gates, and generalizing orchestration from
linear to the state-driven readiness loop. Plus deferred infra (full ingest format zoo,
ingest manifest, the `consult-improvement-log` CSV-doc rewrite).

### Remaining work (size: S/M/L · risk)

**A. Intake & Diagnosis — the unique IP, and the riskiest**

| Item | Role | Size | Key risk |
|---|---|---|---|
| `consult-ingest` (Stage 1) ◻ | all formats → immutable MD + YAML header (`ingest_contract.md` ✅ drafted) | M–L | format zoo: PDF tables, PPTX, XLSX, images/OCR |
| `consult-classifier` (Stage 2) ◻ | **keystone**: doc → artifact → state | L | the artifact schema + cross-doc merge + evidence fidelity |
| `consult-consolidator` (Stage 3) ◻ | confirm findings + author node MD (`consolidate_contract.md` ✅ drafted) | M | keeping prose ↔ structured coupled |
| `consult-gap-analyzer` (Stage 4 LLM) ◻ | substantive gaps, post-consolidate (`consolidate_contract.md` §7) | S–M | overlap with structural scan |

**B. Generation & Review — mostly wiring existing skills to the state/register model**

| Item | Role | Size | Note |
|---|---|---|---|
| `consult-drafter` wiring ◻ | SOP from state/register, per L1 (`generation_review_contract.md` ✅ drafted) | S–M | skill exists; predates state model |
| `consult-improvement-drafter` (5B) ◻ | improvements from lenses + register (`generation_review_contract.md`) | M | new |
| `consult-synthesizer` (5C) ◻ | exec summary + effort×impact roadmap + current→future + `type:theme` cross-cutting findings | M | the "binder → recommendation" lift; leads Slice 1 |
| Evidence tiering ◻ | `evidence_tier` on evidence/findings; control claims need ≥documentary | S | defensibility |
| Review ingestion (Stage 6) ◻ | docx **comment** extraction + apply via commands (`generation_review_contract.md`) | M | the LLM-mediated Word→state loop |
| `unmapped` handling ◻ | register `type: unmapped` (null node) + gap-report Triage | S–M | the diagnostic-completeness safety net |
| `validate` coherence check ◻ | MD-cited IDs exist; prose lenses match state | S | makes structured↔narrative drift detectable |
| Per-L1 render + evidence-inline + change log ◻ | review-unit rendering with reviewer-attributed diffs | M | review usability |
| DoD gates ◻ | evidence-auditor + open-SME items block `final` | S | deliverable trust |
| Output assembly ◻ | per-stream Word + gap report | S | `consult-docx-builder` wiring |

**C. Glue & Infra — what makes it a product, not a toolbox**

| Item | Role | Size |
|---|---|---|
| **Orchestration** (`consult-run`) ◻ | state-driven "run the engagement" loop + `status`/`next` command (`orchestration_contract.md` ✅ drafted) | M–L |
| `update-json` → JSON-native upsert ◻ | kill CSV transport (see §8) | S |
| `consult-improvement-log` rewrite ◻ | recast as the agent-driven register JSON engine (doc-debt) | S–M |
| `templates/` dir ◻ | SOP / improvement / gap-report / node-synthesis skeletons | S |
| Dev/repro setup ◻ | `requirements.txt` + SessionStart hook (pandas/openpyxl/pyyaml/jsonschema) | S |
| End-to-end sample engagement ◻ | proof + regression fixture | S–M |

### Critical path

```
ingest ─▶ classify ─▶ consolidate ─▶ gap-analyzer ─▶ draft(5A/5B) ─▶ render Word ─▶ review ingest ─▶ output
  │           │                                                                          │
  └ transcripts already cleanable (classify can be prototyped without full ingest)       └ needs docx comment extraction
                        orchestration wraps the whole line (skeleton early to lock contracts)
```

**Classify is the keystone and the gate** — consolidate, gap-analyzer, and both drafters all
consume the state it produces. Its real deliverable is not code volume but the **artifact
contract** (see below); design that before building it.

### Build strategy: two vertical slices (thesis first)

Narrow vertical slices over horizontal completion — but **split into two**, because the full-
design review found the single-slice plan was scoped to test the *product*, not the *thesis*,
re-importing the most speculative third (the review-ingestion subsystem) before the core was
proven.

**Slice 1 — prove the thesis, one-way.** On one L1 (Record-to-Report) with a synthesized R2R
transcript sample: `init → ingest(v1) → classify → consolidate → gap → draft(5A/5B) → 5C
synthesis → render Word → STOP`. A human *reads* a credible SOP + improvement + synthesis. **No
review-ingestion loop.** Acceptance: the output reads like real consulting (synthesis present,
evidence inline, ≥1 `unmapped` item *captured* and surfaced in Triage), and a re-run is
idempotent (no duplicate evidence/findings). This is the falsifiable core and the regression
fixture.

**Slice 2 — prove the human loop.** Adds Stage 6 review ingestion (docx comments → commands),
a **second review round** (versioning / no-silent-overwrite), and the full `unmapped`
**disposition** lifecycle as a gate. This is where the coherence check, the evidence-specific
dirty signal's protective role, `review_log`, and review-path conflict detection earn their cost.

**Build the correctness floor before Slice 1's integration test** — see the hardening checklist
below; the review found these are not optional hardening but the load-bearing floor the
contracts already assume.

### Build-hardening checklist (from the full-design review)

The architecture is sound; these are the seams the contracts assert as if implemented. **(S1)**
= required for Slice 1, **(S2)** = Slice 2.

- **(S1) `add-evidence`: dedup by ref + stamp `last_evidence_at`.** Without dedup, routine merge
  re-runs duplicate every evidence entry. Without the stamp, the diagnosis-dirty predicate
  (`last_evidence_at > consolidated_at`) **can never fire → consolidate never runs → silent
  stall.** Build with a re-run assertion.
- **(S1) `unmapped` null-node add path** — `add-item --type unmapped` with no `--l1/--l2`,
  explicitly carrying `type` (the CSV path defaults missing type → `improvement`); **and `sync`
  must exclude null-node `unmapped` rows from the orphan list** (else every one is flagged an
  orphan forever, burying real misroutes).
- **(S1) Stable `dedup_key` / upsert for LLM-confirmed findings** — confirmed findings get fresh
  `IMP-/GAP-NNNN` ids today, so re-consolidation **duplicates** them (unlike self-healing
  structural gaps). Consolidate must upsert by `dedup_key`.
- **(S1) Atomic, schema-validated classify artifacts** — a truncated/invalid artifact currently
  counts as "classified" and its content is dropped; a partial fan-out must not let a node be
  marked `covered`/drafted from an incomplete evidence set. Write temp+rename; validate before
  counting done; gate coverage on fan-out completeness.
- **(S1) Merge-time evidence-ref-resolves check** — verify each `path#L-L` points to real lines
  in the cited MD before writing (the schema only checks shape; an LLM `#L9999` otherwise sails
  through to a phantom citation a reviewer "validates").
- **(S1) `update-json`/`add-item` JSON-native refactor** — kill the temp-CSV transport;
  **fix the insert path that force-sets `requires_human_review=true` on every row** (it silently
  overrides consolidate's judgment); stop the backup-file-per-write churn.
- **(S1) Decide the seam: classify artifact filename key = `{hash}`** (not `{doc}`), so the
  "classified set = artifacts vs manifest active hashes" derivation works across re-ingest.
- **(S2) Review-round-consumed marker** — a crash mid-ingest must not re-apply comments 1–8 on
  the next loop (duplicate `add-item`s). Gate re-ingest on a "round N consumed" flag.
- **(S2) Review-path conflict detection** — a review `set-lens` that contradicts an
  evidence-backed value should raise `GAP-CONFLICT`, not silently overwrite.
- **(S2) Structural re-scan must not reset a human's `review_status`** on `GAP-STRUCT` rows
  (gap_report should set review fields on insert only, preserving human dispositions).

### Persona, invocation & success metrics

- **Persona / invocation** ✅ — an engagement associate/lead (not a developer) invokes one
  entry, `consult-run` ("run/continue engagement {id}"); the agent advances the state-driven
  loop to the next human gate and reports what it needs. (Form decided — see
  `orchestration_contract.md`.)
- **Success metrics** — set targets so "good enough to bill on" is falsifiable: classify
  **precision/recall** (tie to the artifact contract), evidence-support rate (claims with a
  resolving ref), reviewer-edit rate, and time-to-first-draft. The biggest linked risk is
  **classification fidelity × the unmapped path × evidence visibility** — if the diagnosis
  silently mis-buckets or drops content and the reviewer can't see the evidence to catch it,
  the deliverable is confidently wrong. Treat those three as one risk.

### Two explicit planned components (newly called out)

1. **Orchestration ✅ design-drafted** (`orchestration_contract.md`) — **decided**: a
   `consult-run` skill the **agent** follows (only the agent can spawn the LLM stages'
   sub-agents), **state-driven not linear** (asks "what does state need next?" → resumable +
   idempotent across sessions). Backed by Python helpers and a `status`/`next` reporting
   command. Build follows the vertical slice.
2. **Classify artifact contract ✅ design-drafted** (`classify_contract.md` +
   `schemas/classify_artifact.schema.json`) — the per-doc artifact a classifier sub-agent
   returns, the deterministic Python merge rules (confidence/conflict policy, evidence dedup,
   staged findings, unmapped→register), and a worked example. Four decisions locked:
   classify at **L2**; **conflict → null lens + contradiction gap** (never confidently wrong);
   evidence refs require **line-stable ingest**; **findings staged** for consolidate, only
   evidence+lenses auto-merged. Build follows the vertical slice.

### Recommended next move

Design the **classify artifact contract**, then build the **Record-to-Report vertical
slice** through it — proving classify → consolidate → draft on real transcript input before
widening ingest or going horizontal.
