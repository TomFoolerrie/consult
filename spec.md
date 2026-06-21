# CONSULT — Full Work Cycle Plugin: Specification

> Status: **DRAFT spec — no code scaffolded yet.** This document is the agreed design.
> Scope: a Claude Code plugin that runs a finance-consulting engagement end to end:
> intake → diagnose against the CFGI work taxonomy → output two work streams
> (1) Desktop Procedures & SOPs, (2) Process Improvement Opportunities.

---

## 1. Goals & Philosophy

Turn raw engagement inputs (call transcripts, client documents, data exports) into
two polished, CFGI-branded deliverable streams, with a durable, inspectable **source
of truth** in between.

Design principles:

1. **State machine + MD files are the source of truth.** Everything else is derived
   and reproducible. A `.json` state machine (manipulated by Python) holds structured
   status; one Markdown file per **L2** taxonomy node holds the human-readable synthesis.
2. **Python for token efficiency.** Deterministic, repetitive, or bulk work (parsing,
   normalizing, state CRUD, validation, assembly) is done in Python scripts — not by
   burning model tokens. The agent **writes/extends Python as needed**; we provide
   starting templates, not a frozen toolset.
3. **LLM for judgment.** Classification, synthesis, gap reasoning, and drafting are done
   by the model. Bulk/parallel reading is **fanned out to Sonnet sub-agents** — one per
   document — each returning a compact structured artifact (yaml/json/md).
4. **Idempotent stages.** Each stage reads state, does its job, writes state back. Re-running
   a stage is safe and only updates what changed.
5. **Everything lives in this repo**, including engagement state (under `engagements/`).

---

## 2. The Taxonomy (diagnostic backbone)

Source: CFGI Work Taxonomy deck + Regional companion (simplified into
`reference/taxonomy_overall.yaml` and `reference/taxonomy_regional.yaml`).

Hierarchy:

- **L1** — 7 finance domains:
  Procure to Pay · Order to Cash · Record to Report · FP&A · Treasury · Tax · Risk, Policy & Controls
- **L2** — sub-functions within each L1 (e.g. R2R → Pre-Close Set-Up, Close, Consolidation,
  Reporting, Accounting Policy). ~35–40 total. **This is the unit of work** — one MD file
  and one state node per L2.
- **L3** — detailed activities within each L2 (the "Detailed View" boxes).

Each node carries up to **5 diagnostic lenses** (the deck's 5 maps):

| Lens | Question | Values |
|------|----------|--------|
| `current_state` | What work is done today? | present / absent |
| `process` | Pain point or strength? | pain_high / pain_med / strength |
| `automation` | Machine vs human? | machine / mixed / human |
| `capability` | New vs existing work? | new / existing |
| `operating_model` | Central vs local? | central / local |

These lenses map directly onto the engagement framework: **Standardization (Process),
Centralization (People), Human & Machine (Technology), Capability Build (New Work).**

---

## 3. Source of Truth: two coupled artifacts

### 3a. State machine — `engagements/{engagement_id}/state.json`

Python-owned. One entry per L2 node, keyed `{l1_slug}.{l2_slug}`. Conceptual shape:

```jsonc
{
  "engagement": { "id": "...", "client": "...", "region": "NA", "created": "...", "updated": "..." },
  "nodes": {
    "record-to-report.close": {
      "coverage": "partial",                       // none | partial | covered
      "evidence": [                                 // pointers into ingested MD
        { "source": "transcripts/2026-03-01_close.md", "loc": "L42-58", "note": "..." }
      ],
      "lenses": {
        "process": "pain_high",
        "automation": "human",
        "capability": "existing",
        "operating_model": "local"
      },
      "gaps": ["no documented close checklist", "accrual cutoff undefined"],
      "sop": { "status": "draft", "path": "deliverables/sop/r2r-close.md", "rev": 2 },
      "improvement": { "status": "not_started", "path": null },
      "updated": "2026-06-21T00:00:00Z"
    }
  }
}
```

`status` enums (both `sop` and `improvement`): `not_started → drafting → draft → in_review → revised → final`.

Validated against `schemas/engagement_state.schema.json`.

### 3b. Per-L2 synthesis — `engagements/{engagement_id}/nodes/{l1}/{l2}.md`

LLM-owned. The consolidated narrative for one L2: what we learned, evidence digest,
diagnosis across the 5 lenses, open gaps. The drafters read this + the state node to
produce deliverables. Markdown with a small YAML frontmatter block mirroring the state
node's key fields (so it's self-describing and diffable).

**Invariant:** every L2 in the taxonomy has exactly one state node and one MD file,
created at engagement init (even if empty/`coverage: none`). This is what makes gaps
visible — an empty node *is* a finding.

---

## 4. Pipeline (stages)

```
   INGEST → CLASSIFY → CONSOLIDATE → GAP DIAGNOSE → DRAFT(×2) → REVIEW → OUTPUT
   [py]      [llm]       [llm]          [py+llm]      [llm]      [llm]    [py]
     \________________ all read/write state.json + node MDs _____________/
```

### Stage 0 — Init
`python scripts/state_machine.py init --engagement X --region NA` seeds `state.json`
and empty node MDs for every L2 from `reference/taxonomy_*.yaml`.

### Stage 1 — Ingest (Python, "standardize to MD")
Inputs: **all sorts** — VTT/transcripts, DOCX, PDF, PPTX, XLSX/CSV, images.
`scripts/ingest_normalize.py` converts each raw artifact to clean Markdown under
`engagements/{id}/ingested/`, stripping timestamps/speaker noise/boilerplate for token
efficiency. The agent extends this script for new formats as needed.

### Stage 2 — Classify (LLM fan-out, "one Sonnet per doc")
For each normalized doc, **launch a Sonnet sub-agent** that reads it and returns a
compact structured map (yaml/json/md) of: which L2 nodes it touches, candidate evidence
spans, and lens signals. The orchestrator merges these into `state.json`. Parallel,
bounded context per agent.

### Stage 3 — Consolidate (LLM synthesis)
Per L2 with new evidence, synthesize the merged signals into the node MD — deduped,
reconciled, cited. This is the "single source of truth" write.

### Stage 4 — Gap Diagnose (Python + LLM)
`scripts/gap_report.py` mechanically finds structural gaps (nodes with `coverage:none`,
missing lenses, no evidence). The LLM adds substantive gaps (contradictions, thin
evidence, undocumented controls). Emits `deliverables/gap_report.md` and updates each
node's `gaps[]`.

### Stage 5 — Draft, two work streams (LLM)
- **5A SOP / Desktop Procedures** — per L2: Purpose → Scope → Inputs/Systems → Roles →
  Step-by-step procedure → Controls → Exceptions → Screenshot placeholders.
- **5B Improvement Opportunities** — per L2, organized by the 4 lenses: Finding →
  Recommendation → Effort × Impact → Owner. Driven by `process`/`automation`/
  `operating_model`/`capability` scores.

Both write back `sop.status` / `improvement.status` and a deliverable path.

### Stage 6 — Review & Output
Review/audit skills run over drafts (evidence completeness, comment resolution,
improvement log). Final assembly via the DOCX builder into CFGI-branded Word documents —
one per work stream, plus the gap report.

---

## 5. Skills (capabilities) — target set

Existing (already seeded), to be wired into the pipeline:

| Skill | Role in pipeline |
|-------|------------------|
| `consult-transcript-cleaner` | Stage 1 — VTT → clean MD (`clean_vtt.py`) |
| `consult-drafter` | Stage 5A — SOP drafting (templates + evidence/gap rules) |
| `consult-evidence-auditor` | Stage 6 — evidence completeness audit |
| `consult-review-comment-resolver` | Stage 6 — resolve reviewer comments |
| `consult-improvement-log` | Stage 6 — track improvements/changes |
| `consult-docx-builder` | Stage 6 — MD → CFGI-branded Word |

New (to be designed later — NOT in this spec's scope to build):

| Skill | Role |
|-------|------|
| `consult-ingest` | Stage 1 — multi-format normalizer (orchestrates `ingest_normalize.py`) |
| `consult-classifier` | Stage 2 — fan-out Sonnet-per-doc → state |
| `consult-consolidator` | Stage 3 — per-L2 synthesis into node MD |
| `consult-gap-analyzer` | Stage 4 — structural + substantive gaps |
| `consult-improvement-drafter` | Stage 5B — improvement opportunities |

---

## 6. Templates to provide (not freeze)

- `templates/sop_desktop_procedure.md` — SOP skeleton (already partly in consult-drafter).
- `templates/improvement_opportunity.md` — per-L2 improvement block (4 lenses).
- `templates/node_synthesis.md` — the per-L2 MD with YAML frontmatter.
- `templates/gap_report.md` — gap roll-up.
- Python templates: `state_machine.py`, `ingest_normalize.py`, `gap_report.py` —
  documented, extensible starting points; the agent scripts further Python ad hoc.

---

## 7. Proposed repo layout

```
/
├── .claude-plugin/plugin.json
├── spec.md                          ← this file
├── reference/                       ← CFGI IP, static (simplified from source PDFs)
│   ├── taxonomy_overall.yaml
│   ├── taxonomy_regional.yaml
│   └── cfgi_brand_identity.md
├── schemas/
│   ├── engagement_state.schema.json
│   └── node_synthesis.schema.json
├── templates/                       ← starting points, agent extends
├── scripts/                         ← Python: state CRUD, ingest, gap report
├── skills/                          ← existing + new (see §5)
└── engagements/                     ← STATE LIVES HERE, in-repo
    └── {engagement_id}/
        ├── state.json               ← source of truth (machine)
        ├── ingested/                ← normalized MD per raw artifact
        ├── nodes/{l1}/{l2}.md       ← source of truth (human, per L2)
        └── deliverables/
            ├── gap_report.(md|docx)
            ├── sop/                 ← Stream A
            └── improvements/        ← Stream B
```

---

## 8. Open items to resolve before building

1. **Region model** — `taxonomy_regional.yaml` was processed and contains **no regional
   content** — it is a 6-L1 global taxonomy variant that uses different L1 naming
   (RTR, QTC, STP, FP&A, HTR, ATR) vs. the 7-domain overall deck. The "regional" label
   may indicate a different business unit or the PDF may have more pages than were
   rendered. **A human must verify the source PDF's full page count.** Until confirmed,
   `taxonomy_overall.yaml` is the authoritative taxonomy. Default: single `region` field
   per engagement.
2. **Evidence span format** — line ranges vs anchors. Proposed: `path#Lstart-Lend`.
3. **Engagement state in git** — kept in-repo per decision. Decide later whether real
   client engagements are committed or git-ignored per-engagement.
4. **L2 slug canonicalization** — generate slugs from `reference/taxonomy_overall.yaml`
   once finalized; that file is the naming authority.

---

## 9. Source documents

- `Work_Taxonomy__Overall.pdf` → `reference/taxonomy_overall.yaml` (7 L1 × ~5 L2 × L3 + 5 lenses).
- `BT_Business_Cycle_Taxonomies_Regional.pdf` → `reference/taxonomy_regional.yaml`.
- `CFGI_Brand_Identity.md` → `reference/cfgi_brand_identity.md` (colors, type, tables, callouts).
