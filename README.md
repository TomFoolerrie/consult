# CONSULT — MVP

A lean, two-skill version of the CONSULT suite for producing evidence-backed
finance process documentation. This is the **dumbed-down MVP** — no engagement
state, taxonomy, orchestration, or multi-agent fan-out. Just the core author →
render path:

```
cleaned sources ──▶ consult-drafter ──▶ process-doc.md ──▶ consult-docx-builder ──▶ CFGI .docx
```

> The full state-driven pipeline (ingest → classify → merge → consolidate →
> gap-scan → draft → synthesize → render, with a human Word-review loop) lives
> on the `main` branch. This `mvp` branch is intentionally minimal.

## The two skills

| Skill | What it does |
|---|---|
| **`consult-drafter`** | Drafts a complete, DOCX-friendly Markdown desktop-procedure deliverable from cleaned source materials. Enforces the canonical L1→L2→L3 / A–H structure (`reference/Template.md`), evidence discipline (no fabricated facts), and consistent IDs (`CTRL-`, `PP-`, `IO-`, `GAP-`, `SC-`, `SRC-`). Ships helper scripts: `reconcile.py` (ID-integrity QC gate), `split_doc.py` / `assemble_doc.py` (edit large drafts as components). |
| **`consult-docx-builder`** | Renders finalized drafter Markdown into a CFGI-branded `.docx` via `cfgi_markdown_to_word.py` — fixed green house style, cover page from the Document Profile table, callouts colored by label, tables auto-styled by kind. Screenshots stay text placeholders. |

## Setup

```bash
pip install -r requirements.txt   # python-docx (needed by the Word converter)
```

## Usage

```bash
# 1. Draft (via the consult-drafter skill) → produces e.g.
#    month-end-close_process-doc_v0.1.md

# 2. QC the IDs before rendering
python3 skills/consult-drafter/scripts/reconcile.py month-end-close_process-doc_v0.1.md

# 3. Render to CFGI Word
python3 skills/consult-docx-builder/scripts/cfgi_markdown_to_word.py \
    month-end-close_process-doc_v0.1.md -o month-end-close_process-doc_v0.1.docx
```

See each skill's `SKILL.md` for the full drafting workflow, callout rules, and
converter options (`--include-toc`, `--landscape`, `--no-cover`).
