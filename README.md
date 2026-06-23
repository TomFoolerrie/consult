# CONSULT

A Claude Code skill suite that runs a finance-transformation consulting engagement
end to end. It ingests raw engagement inputs (call transcripts, Word docs), diagnoses
them against the **CFGI finance work taxonomy**, and produces four CFGI-branded Word
deliverables with full evidence traceability and a human Word-review loop.

> **CONSULT does the analyst grind, not the judgment.** It maps what was said to the
> right part of the close/finance process, tracks coverage and gaps, drafts the
> deliverables, and keeps every claim tied to a line of evidence. A human reviews in
> Word; the system folds those edits back in.

---

## What it produces

Per engagement, CONSULT generates four deliverables:

| Deliverable | What it is |
|---|---|
| **Synthesis / decision layer** | Cross-cutting executive synthesis — themes, effort×impact, roadmap |
| **SOP / desktop procedures** | Standard operating procedures drafted from the diagnosed process |
| **Process-improvement opportunities** | Actionable improvements, tagged by diagnostic lens |
| **Gap report** | What's missing or unconfirmed — open questions for the client |

Every finding carries an evidence ref (`path#Lstart-Lend`) back to an immutable,
source-hashed copy of the input, so nothing is "confidently wrong."

---

## How it's organized

CONSULT keeps two layers of state per engagement, both written **only** through the
Python engines (never hand-edited):

- **`state.json`** — the node tracker. One node per **L2** taxonomy sub-function,
  carrying coverage, the five diagnostic lenses, evidence, and SOP/improvement status.
- **`register.json`** — a flat item register of every improvement, gap, screenshot,
  unmapped item, and cross-cutting theme, keyed to its taxonomy node.

The taxonomy itself (`reference/taxonomy.yaml`) is the single source of truth:
**7 L1 cycles / 37 L2 sub-functions / 212 L3 activities**. **L2 is the unit of work** —
the level everything maps to and gets diagnosed at. Items are keyed by node slug
`{l1_id}.{l2_id}` (e.g. `record-to-report.close`).

### The five diagnostic lenses
`current_state` · `process` · `automation` · `capability` · `operating_model`

When two documents disagree on a lens, CONSULT leaves the lens null and raises a
`GAP-CONFLICT` rather than guessing.

---

## The pipeline

```
ingest → classify → merge → consolidate → gap-scan → draft → synthesize → render
                                                                              │
                                  human reviews the Word docs ◄───────────────┘
                                              │
                                   review-ingest → mark-dirty → re-consolidate → final gate
```

| Stage | Engine | What happens |
|---|---|---|
| **Ingest** | `scripts/ingest_normalize.py` | Any input → immutable hashed Markdown + YAML header |
| **Classify** | `consult-classifier` skill | One sub-agent per doc emits node_hits (LLM judgment) |
| **Merge** | `scripts/classify_merge.py` | Deterministic, validated merge of hits into `state.json` |
| **Consolidate** | `consult-consolidator` skill | Per-L2 confirmation of findings; authors node MD |
| **Gap scan** | `scripts/gap_report.py` | Structural gap detection |
| **Draft / Synthesize** | `consult-drafter`, `-improvement-drafter`, `-synthesizer` | Author the deliverable Markdown |
| **Render** | `scripts/render_deliverables.py` | CFGI-branded Word output |
| **Review loop** | `scripts/review_ingest.py`, `docx_comments.py` | Extract Word comments → apply → re-consolidate |
| **Final gate** | `scripts/gates.py` | Machine-checkable Definition of Done |

`scripts/orchestrate.py next --engagement <id>` is a read-only advisor that tells you
(or the orchestrating agent) the next action at any point.

---

## Using it

**One-time setup**

```bash
pip install -r requirements.txt
```

**Run an engagement** (drive interactively via the `consult-run` skill, or by hand):

```bash
# 1. Initialize engagement state
python scripts/state_machine.py init --engagement <client-id>

# 2. Ingest raw inputs (transcripts, .docx)
python scripts/ingest_normalize.py ingest --engagement <client-id> --source path/to/input...

# 3. Let the orchestrator tell you the next step
python scripts/orchestrate.py next --engagement <client-id>
#    → classify → merge → consolidate → gap → draft → synthesize → render
#      (each LLM stage runs as a consult-* skill / sub-agent)

# 4. Review the rendered Word deliverables, leave comments/edits in Word, then:
python scripts/review_ingest.py extract --engagement <client-id> --doc <reviewed.docx>
python scripts/review_ingest.py apply   --engagement <client-id>

# 5. Re-run consolidate/render for dirtied nodes, then check the gate
python scripts/gates.py final-check --engagement <client-id>
```

Today CONSULT ingests **call transcripts (.txt/.md/.vtt/.srt/.csv/.tsv) and Word
(.docx)**. PDF / PPTX / XLSX / image-OCR ingest is deferred (see
`tickets/README.md` → Deferred).

---

## Repo layout

```
reference/      taxonomy.yaml (source of truth) + ratings sidecar + CFGI brand
schemas/        JSON Schema (draft-07) for state, register, classify artifacts, ingest header
scripts/        Python engines (state_machine, classify_merge, gap_report, render, orchestrate, gates, …)
skills/         consult-* SKILL.md briefs (one per pipeline stage / sub-agent)
tickets/        Implementation tickets (T01–T20 Slice 1, T30–T39 Slice 2)
tests/          test_slice1_e2e.sh — deterministic end-to-end regression
fixtures/       Synthetic R2R sample inputs + canned artifacts
engagements/    Per-engagement state (r2r-demo is a committed synthetic example)
spec.md         Architecture spec (index)
*_contract.md   Stage contracts: classify, ingest, consolidate, generation_review, orchestration
```

---

## ⚠️ Do not commit real client data

This is a shared repo. The `engagements/r2r-demo/` example is **fully synthetic**.

For a real engagement, either:
- add `engagements/<client>/` to `.gitignore`, **or**
- run it in a **private** repository.

Rendered `*.docx` and `*.xlsx` snapshots are already gitignored.

---

## Status

Both build slices are complete:

- **Slice 1** — the one-way diagnostic pipeline (ingest → render). ✅
- **Slice 2** — the human Word-review loop (comment extraction → re-consolidation → gate). ✅

The Slice-1 end-to-end regression (`tests/test_slice1_e2e.sh`) is green and idempotent,
provided `pip install -r requirements.txt` has been run first (without jsonschema the
e2e fails).
