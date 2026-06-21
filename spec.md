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

1. **State files are the source of truth; Python owns every write.** Structured
   state lives in `.json` files. These are **only ever mutated by the state-management
   Python scripts** — never hand-edited by the model and never edited by a human
   directly. Humans review and edit via **Excel round-trip** (export to xlsx → edit →
   re-import through the script). One Markdown file per **L2** node holds the
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
  "evidence": [ { "source": "...", "loc": "L42-58", "note": "..." } ],  // loc format provisional (see §8.1)
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
(which takes precedence and is preserved across sync):
- `none` — no evidence **and** no linked items
- `covered` — has evidence **and** all 5 lenses set
- `partial` — anything in between (items but no evidence, evidence but incomplete lenses)

> **Region note:** the *taxonomy* regional variant was dropped (§2), but each engagement
> still carries a `region` attribute (`init --region NA`) — it's an engagement property,
> not a taxonomy axis.

### Layer 2 — unified item register `register.json` ✅ (owned by `improvement_log.py`)

A flat list of every item that hangs off an L2 node, discriminated by `type`:

- `improvement` — a process improvement opportunity (Stream B)
- `gap` — a gap / validation item (from the drafter gap tags / structural scan)
- `screenshot` — a screenshot placeholder (SC-IDs)

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

**The register is the human-reviewable surface:** export to xlsx → human edits → re-import
via `update-json` (with timestamped backups). `state.json` is internal machinery — humans
never edit it directly; they edit the register and the node MDs.

### Layer 3 — per-L2 synthesis `nodes/{l1}/{l2}.md` ✅ (LLM-owned)

The consolidated narrative for one L2: what we learned, evidence digest, diagnosis across
the 5 lenses, open gaps. Markdown with a small YAML frontmatter block mirroring the state
node's key fields (self-describing and diffable). Seeded as a stub at init with the L2's
L3 activities pulled from the taxonomy.

**Invariant:** every L2 has exactly one state node and one MD file. ✅ (checked by
`state_machine.py validate`).

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
| `validate` ✅ | read | Node set vs taxonomy + JSON Schema check. |
| `get-node` ✅ | discovery | Return one node (compact, or `--json`), not the whole file. |
| `query` ✅ | discovery | List node keys matching ANDed filters (`--coverage`, `--lens-missing`, `--has-gaps`, `--has-improvements`, `--l1`, `--count`). |
| `set-lens` ✅ | mutate | Set/clear one lens value on a node (schema-validated). |
| `add-evidence` ✅ | mutate | Append an evidence entry to a node. |
| `set-coverage` ✅ | mutate | Manual coverage override (writes `coverage_override`; `sync` preserves it; `auto` clears it). |
| `set-sop` ✅ | mutate | Update SOP deliverable status/path/rev. |
| `add-item` ✅ | mutate | Add a register row through `improvement_log.py` then auto-`sync`; stable auto IDs (`IMP-/GAP-/SC-NNNN`); orphan node keys rejected. |

### `improvement_log.py` (item register) ✅

`build-xlsx` · `update-json` · `remove` · `validate`. The granular `add-item` ✅ convenience
lives in `state_machine.py` (builds a row → routes through `update-json` → auto-`sync`),
keeping additions granular and node counts consistent automatically.

---

## 5. Pipeline (stages)

```
   INGEST → CLASSIFY → CONSOLIDATE → GAP DIAGNOSE → DRAFT(×2) → REVIEW → OUTPUT
   [py]      [llm]       [llm]          [py+llm]      [llm]      [llm]    [py]
     \________________ all read/write state via state_machine.py / register __________/
```

### Stage 0 — Init ✅
`python scripts/state_machine.py init --engagement X --region NA` seeds `state.json`,
`register.json`, and empty node MDs for every L2.

### Stage 1 — Ingest (Python, "standardize to MD") ◻
Inputs: VTT/transcripts, DOCX, PDF, PPTX, XLSX/CSV, images. `scripts/ingest_normalize.py`
converts each raw artifact to clean Markdown under `engagements/{id}/ingested/`.
`consult-transcript-cleaner` ✅ already handles transcript formats.

### Stage 2 — Classify (LLM fan-out, "one Sonnet per doc") ◻
For each normalized doc, launch a Sonnet sub-agent returning a compact map of: which L2
nodes it touches, candidate evidence spans, lens signals. The orchestrator merges these
into `state.json` via the granular mutation commands.

### Stage 3 — Consolidate (LLM synthesis) ◻
Per L2 with new evidence, synthesize merged signals into the node MD — deduped, reconciled,
cited.

### Stage 4 — Gap Diagnose (Python + LLM) ◻
`scripts/gap_report.py scan` mechanically finds structural gaps (nodes with
`coverage:none`, missing lenses, no evidence, SOP not started) and writes them into the
register as `type: gap` rows with **stable IDs** (`GAP-STRUCT-{l1}-{l2}-{kind}`), then
emits `deliverables/gap_report.md`. The LLM (`consult-gap-analyzer`) adds substantive gaps
(contradictions, thin evidence, undocumented controls) as further gap rows.

### Stage 5 — Draft, two work streams (LLM) — 5A ✅ (drafter) · 5B ◻
- **5A SOP / Desktop Procedures** (`consult-drafter` ✅) — per L2: Purpose → Scope →
  Inputs/Systems → Roles → Step-by-step → Controls → Exceptions → Screenshot placeholders.
- **5B Improvement Opportunities** (`consult-improvement-drafter` ◻) — per L2, organized
  by the 4 lenses, driven by `process`/`automation`/`operating_model`/`capability` and the
  register's improvement rows: Finding → Recommendation → Effort × Impact → Owner.

Both write back `sop.status` / register rows and a deliverable path.

### Stage 6 — Review & Output
Review/audit skills run over drafts: `consult-evidence-auditor` ✅,
`consult-review-comment-resolver` ✅, `consult-improvement-log` ✅. Final assembly via
`consult-docx-builder` ✅ into CFGI-branded Word — one per work stream, plus the gap report.

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
        ├── register.json            ← Layer 2 (machine; xlsx round-trip for humans)
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
4. **Write discipline** — JSON is script-only; humans round-trip the register via Excel.

Open:

1. **Evidence span format** — proposed `path#Lstart-Lend`; currently provisional: a `loc`
   string on node evidence and free-text `source` on register rows. Converge on one format
   when Stage 2 lands.
4. **Machine-record ID schemes** — `add-item` defines stable prefixes for manual register
   rows (`IMP-/GAP-/SC-NNNN`); structural gaps from `gap_report.py` will use
   `GAP-STRUCT-{l1}-{l2}-{kind}`. Open: confirm the two gap-ID spaces (`GAP-NNNN` manual vs
   `GAP-STRUCT-*` machine) coexist cleanly when Stage 4 lands.
2. **Engagement state in git** — kept in-repo per decision. Decide later whether real
   client engagements are committed or git-ignored per-engagement (backups already ignored).
3. **Screenshot items** — supported as a register `type`; decide whether they live in the
   register or stay solely in the SOP's Appendix D when Stage 5A integration lands.

---

## 9. Source documents

- `Work_Taxonomy__Overall.pdf` → `reference/taxonomy.yaml` (+ `taxonomy_baselines.yaml`).
- `BT_Business_Cycle_Taxonomies_Regional.pdf` → dropped (no regional content).
- `CFGI_Brand_Identity.md` → `reference/cfgi_brand_identity.md` (colors, type, tables, callouts).
