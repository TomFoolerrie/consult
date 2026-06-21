# CONSULT — Full Work Cycle Plugin: Specification

> Status: **Foundation built.** Taxonomy, two-layer state model, unified item
> register, and JSON Schemas are implemented and tested. The diagnostic/drafting
> pipeline stages and their skills are partially built (existing skills) or
> planned. Build status is marked inline: ✅ built · ◻ planned.
> Scope: a Claude Code plugin that runs a finance-consulting engagement end to
> end: intake → diagnose against the CFGI work taxonomy → output two work streams
> (1) Desktop Procedures & SOPs, (2) Process Improvement Opportunities.

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
- `unmapped` ◻ — client content that fits **no** L2 node. Node link is null; it carries an
  `owner` and is surfaced for triage in the gap report. It is **never** auto-bucketed into a
  nearest L2 — this is the safety net against the taxonomy silently dropping client reality.
  (Needs schema/code support: a null-node register path + a `gap_report` Triage section.)

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
| `add-evidence` ✅ | mutate | Append an evidence entry to a node. |
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
header** (source filename, doc type, date, detected hints) under
`engagements/{id}/ingested/`. Driven by `scripts/ingest_normalize.py` with **seeded Python
templates the agent extends per format**. It **subsumes/calls** `consult-transcript-cleaner`
(`clean_vtt.py` ✅) as the transcript handler rather than duplicating it.

### Stage 2 — Classify (LLM fan-out, "one Sonnet per doc") ◻
For each ingested doc, launch a sub-agent that **reads it and returns** a compact structured
artifact: which L2 nodes it touches, candidate evidence spans, lens signals, candidate
findings, and **`unmapped`** content that fits no L2 node. The orchestrator applies the
artifact into state via the granular mutation commands — unmapped content becomes
`type: unmapped` register rows with an owner (never auto-bucketed into a nearest L2, never
extends the taxonomy). **Sub-agents never write state.**

### Stage 3 — Consolidate (LLM synthesis) ◻
Per L2 with new evidence, synthesize merged signals into the node MD — deduped, reconciled,
cited.

### Stage 4 — Gap Diagnose (Python + LLM) ◻
`scripts/gap_report.py scan` mechanically finds structural gaps (nodes with
`coverage:none`, missing lenses, no evidence, SOP not started) and writes them into the
register as `type: gap` rows with **stable IDs** (`GAP-STRUCT-{l1}-{l2}-{kind}`), then
emits `deliverables/gap_report.md` (incl. an **Unmapped Triage** section listing
`type: unmapped` rows with owners). The LLM (`consult-gap-analyzer`) adds substantive gaps
(contradictions, thin evidence, undocumented controls) as further gap rows.

### Stage 5 — Draft, two work streams (LLM) — 5A ✅ (drafter) · 5B ◻
- **5A SOP / Desktop Procedures** (`consult-drafter` ✅) — per L2: Purpose → Scope →
  Inputs/Systems → Roles → Step-by-step → Controls → Exceptions → Screenshot placeholders.
- **5B Improvement Opportunities** (`consult-improvement-drafter` ◻) — per L2, organized
  by the 4 lenses, driven by `process`/`automation`/`operating_model`/`capability` and the
  register's improvement rows: Finding → Recommendation → Effort × Impact → Owner.

Both write back `sop.status` / register rows and a deliverable path.

### Stage 6 — Review & Output
Render deliverables to CFGI-branded Word **per L1 cycle** (`consult-docx-builder` ✅; the
review unit — the drafter's L1-Level mode already produces one doc per cycle). Each render
carries **evidence refs inline** and a **change log** (reviewer-attributed, what moved since
the last round). Humans review **in Word** (edits + tracked comments).
`consult-review-comment-resolver` ✅ performs the **LLM-mediated docx ingestion** —
extracting body text *and* tracked comments (needs a docx-comment extraction helper) into
structured updates the agent applies back through the commands, attributed to a reviewer.
**Gates before `final`:** `consult-evidence-auditor` ✅ passes (procedural claims supported),
and no open `requires_human_review` / SME-validation items remain. Final assembly to Word —
one document per work stream, plus the gap report. **No CSV round-trip.**

### Deliverables & Definition of Done

The client receives **three artifacts**: Stream A (SOP / Desktop Procedures), Stream B
(Process Improvement Opportunities), and the **Gap Report** — all CFGI-branded Word.

**SOP stream DoD** = the drafter's **Quality Checklist** (`consult-drafter/SKILL.md`, *not*
the handlebars shell in `references/`): scope level stated; canonical section order; Source
Materials populated; each procedure has A–H sections (or a logged gap); no unsupported
procedural claims; body gap tags reflected in **Appendix C** (Gap/Validation Log); pain
points in **Appendix A**; improvements in **Appendix B**; screenshots in **Appendix D**;
Cross-Reference Matrix populated; ready for docx.

**Improvement stream DoD** = every improvement row has Finding → Recommendation →
Effort × Impact → Owner (register fields non-empty), tied to a lens.

**Engagement completeness rubric** (not "100% covered" — `coverage:none` is a valid
finding): every L2 node is *triaged* (covered, or an explicit gap explains why not); zero
`unmapped` rows left without an owner; all evidence refs resolve; evidence-auditor passes;
no open SME-validation items. ◻ to wire as gates.

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

Planned ◻:

| Skill | Role |
|-------|------|
| `consult-ingest` | Stage 1 — multi-format normalizer (`ingest_normalize.py`) |
| `consult-classifier` | Stage 2 — fan-out Sonnet-per-doc → state |
| `consult-consolidator` | Stage 3 — per-L2 synthesis into node MD |
| `consult-gap-analyzer` | Stage 4 — substantive gaps (structural gaps are `gap_report.py`) |
| `consult-improvement-drafter` | Stage 5B — improvement opportunities |

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
        └── deliverables/
            ├── gap_report.(md|docx)
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
   `source`). Must render inline in review docs.
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
4. **Machine-record ID schemes** — `add-item` uses `IMP-/GAP-/SC-NNNN`; structural gaps use
   `GAP-STRUCT-{l1}-{l2}-{kind}`. Confirm the manual (`GAP-NNNN`) and machine (`GAP-STRUCT-*`)
   gap-ID spaces coexist cleanly (they do today; keep an eye as Stage 4 integrates).
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

The **spine is built and tested**: taxonomy, Layer 1 state machine (full discovery +
mutation API), Layer 2 unified register, JSON schemas, `gap_report.py` (Stage 4
structural), node-MD seeding, and the `consult-state-machine` skill. Today you can init an
engagement, hand-drive a diagnosis, scan structural gaps, and (via existing skills) draft
SOPs and build Word. **Not yet built: the automated intake/diagnosis (ingest → classify →
consolidate) and a top-level way to run the whole pipeline as one motion.**

### Remaining work (size: S/M/L · risk)

**A. Intake & Diagnosis — the unique IP, and the riskiest**

| Item | Role | Size | Key risk |
|---|---|---|---|
| `consult-ingest` (Stage 1) ◻ | all formats → MD + YAML header | M–L | format zoo: PDF tables, PPTX, XLSX, images/OCR |
| `consult-classifier` (Stage 2) ◻ | **keystone**: doc → artifact → state | L | the artifact schema + cross-doc merge + evidence fidelity |
| `consult-consolidator` (Stage 3) ◻ | per-L2 node-MD synthesis | M | keeping prose ↔ structured coupled |
| `consult-gap-analyzer` (Stage 4 LLM) ◻ | substantive gaps | S–M | overlap with structural scan |

**B. Generation & Review — mostly wiring existing skills to the state/register model**

| Item | Role | Size | Note |
|---|---|---|---|
| `consult-drafter` wiring ◻ | SOP from state/register | S–M | skill exists; predates state model |
| `consult-improvement-drafter` (5B) ◻ | improvements from lenses + register | M | new |
| Review ingestion (Stage 6) ◻ | docx **comment** extraction + apply via commands | M | the LLM-mediated Word→state loop |
| `unmapped` handling ◻ | register `type: unmapped` (null node) + gap-report Triage | S–M | the diagnostic-completeness safety net |
| `validate` coherence check ◻ | MD-cited IDs exist; prose lenses match state | S | makes structured↔narrative drift detectable |
| Per-L1 render + evidence-inline + change log ◻ | review-unit rendering with reviewer-attributed diffs | M | review usability |
| DoD gates ◻ | evidence-auditor + open-SME items block `final` | S | deliverable trust |
| Output assembly ◻ | per-stream Word + gap report | S | `consult-docx-builder` wiring |

**C. Glue & Infra — what makes it a product, not a toolbox**

| Item | Role | Size |
|---|---|---|
| **Orchestration** ◻ | top-level "run the engagement" entry; idempotent stage sequencing | M–L |
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

### Build strategy: vertical slice first

Prefer a **narrow vertical slice end-to-end** over finishing each stage horizontally across
all 37 L2s. Pick a couple of real transcripts for one L1 (e.g. Record-to-Report) and get
`init → classify → consolidate → gap → draft → Word → review → output` working on *just
that*, with stubs elsewhere. Rationale: it surfaces the integration seams (the classify
artifact contract and the Word review loop) while they are cheap to change, yields a
demoable result fastest, and becomes the regression fixture. Building ingest's full format
zoo before proving classify would be effort at risk.

The slice should deliberately exercise the parts that only bite at scale: a **second review
round** (to prove versioning / no-silent-overwrite) and at least **one `unmapped` item** (to
prove the triage path) — not just a happy-path single pass.

### Persona, invocation & success metrics

- **Persona / invocation** — define who runs this (engagement associate vs. lead) and the
  single entry point they invoke; this is the open **orchestration form** decision (skill /
  Python driver / `CLAUDE.md`). For a "runs an engagement end to end" product the entry
  point *is* the product — don't leave it implicit.
- **Success metrics** — set targets so "good enough to bill on" is falsifiable: classify
  **precision/recall** (tie to the artifact contract), evidence-support rate (claims with a
  resolving ref), reviewer-edit rate, and time-to-first-draft. The biggest linked risk is
  **classification fidelity × the unmapped path × evidence visibility** — if the diagnosis
  silently mis-buckets or drops content and the reviewer can't see the evidence to catch it,
  the deliverable is confidently wrong. Treat those three as one risk.

### Two explicit planned components (newly called out)

1. **Orchestration ◻** — the top-level entry that sequences the stages idempotently and
   applies every state write through the commands. **Open decision — its form:** a
   skill/playbook the agent follows, a Python driver that invokes stages, or `CLAUDE.md`
   instructions. To be decided before/with the vertical slice.
2. **Classify artifact contract ◻** — the schema a per-doc classifier sub-agent *returns*
   (never writing state itself): node hits, lens signals (with confidence), evidence spans,
   candidate findings, and `unmapped` flags — plus the orchestrator's rules for merging
   conflicting signals across documents. This is the contract everything downstream binds
   to; design it as the next concrete artifact.

### Recommended next move

Design the **classify artifact contract**, then build the **Record-to-Report vertical
slice** through it — proving classify → consolidate → draft on real transcript input before
widening ingest or going horizontal.
