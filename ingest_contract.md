# CONSULT — Ingest Contract (Stage 1)

> Status: **BUILT** (implemented by `scripts/ingest_normalize.py`). Companion schema:
> `schemas/ingested_header.schema.json`. See `spec.md` §5 Stage 1. Downstream consumer:
> `classify_contract.md` (Stage 2) — which imposes the line-stability constraint below.

## 1. What ingest does

Stage 1 turns raw client files of **any format** into clean, uniform **Markdown with a YAML
header**, under `engagements/{id}/ingested/`, ready for the Stage 2 classifier (one
sub-agent reads one ingested MD). It is **deterministic Python** — a single `consult-ingest`
skill orchestrating `scripts/ingest_normalize.py`, which dispatches to **per-format handlers**
the agent can extend. It **subsumes** `consult-transcript-cleaner` (`clean_vtt.py`) as the
transcript handler rather than duplicating it.

Goal: strip noise (token efficiency) while **preserving substance, structure, and
provenance**.

## 2. Three constraints that shape everything

1. **Ingested MDs are immutable, hashed artifacts.** One source file → one MD, named
   descriptively + dated, keyed by the **source content hash**. Once written it is **never
   rewritten**. This is what guarantees Stage 2's `path#Lstart-Lend` evidence refs stay valid
   forever — line numbers can't move if the file can't change. Re-running ingest is idempotent
   (skip sources whose hash already has an MD). A **changed** source = a different hash = a
   **new** MD (the old one and its refs remain valid; supersession is tracked in the manifest).
   Handler improvements apply only to not-yet-ingested sources; re-ingesting with a better
   handler is a deliberate act that produces a new MD with new refs.
2. **Provenance must survive.** The MD carries lightweight anchors back to the original
   location (`<!-- page 4 -->`, `<!-- slide 7 -->`, `<!-- sheet: Close Calendar -->`), so an
   evidence ref into the MD ultimately traces to the source — the audit trail the deliverables'
   credibility rests on.
3. **Determinism.** Given a source + handler version, output is byte-identical. No timestamps
   or run-specific data in the *body* (those live in the YAML header only).

## 3. The ingested MD format

```markdown
---
source: client/Close Walkthrough 2026-03-01.vtt
source_hash: sha256:9f2c...               # of the raw source bytes
doc_type: transcript                      # transcript|docx|pdf|pptx|xlsx|csv|image|text
ingested_at: 2026-03-02T10:00:00Z
ingester: ingest_normalize.py/transcript@1   # handler + version (provenance for re-ingest)
title: Record-to-Report Close Walkthrough
provenance: { pages: null, slides: null, sheets: null }   # filled per format
hints: { client: "Acme", systems: ["SAP"], people: [] }   # best-effort, NON-authoritative
immutable: true
---

<!-- provenance markers appear inline as the body is sectioned -->

# Record-to-Report Close Walkthrough

We close the sub-ledgers first, then accruals. Accruals are the painful part — all manual
journal uploads, two analysts, three days. There's no documented checklist; people just know
the order.
```

Body conventions by content: transcripts → cleaned prose (timestamps/speaker-spam stripped);
tables (XLSX/CSV/DOCX) → Markdown tables; slides/pages → sections under a provenance marker.
`hints` are *signals for the classifier*, never authoritative — the taxonomy and state remain
the source of truth.

## 4. YAML header schema

`schemas/ingested_header.schema.json` (draft). Required: `source`, `source_hash`, `doc_type`,
`ingested_at`, `immutable`. `hints` is open and best-effort.

## 5. Format handlers (phased)

Each handler is a function in `ingest_normalize.py`; the agent adds/extends them. Phasing
keeps the format-zoo risk bounded (per `spec.md` §10):

| Phase | Formats | Handler notes |
|---|---|---|
| **v1** | `.txt .md .csv .tsv .vtt .srt` | text passthrough + clean; transcript handler = `clean_vtt.py` ✅; CSV/TSV → Markdown table |
| **v1** | `.docx` | extract text + tables (already partially in transcript-cleaner's docx path); preserve headings |
| **v2** | `.pdf` | text + tables per page; `<!-- page N -->` markers; strip headers/footers/page numbers |
| **v2** | `.pptx` | one section per slide; `<!-- slide N -->`; include speaker notes |
| **v2** | `.xlsx` | one section per sheet (`<!-- sheet: NAME -->`); each sheet → Markdown table; skip empty |
| **v3** | images (`.png .jpg`) | **the one non-deterministic handler** — a vision-LLM caption/OCR; generated **once and frozen** into the immutable MD so re-runs don't change line numbers; highest risk, last |

Cleaning rules reuse `consult-transcript-cleaner`'s noise list (timestamps, cue ids, hashes,
meeting artifacts, line-wrap) plus per-format boilerplate (PDF running headers/footers, slide
chrome, empty cells).

## 6. Bookkeeping: `ingested/manifest.json`

Ingest maintains a small manifest (deterministic Python, not engagement state): each entry =
`{ source, source_hash, md_path, doc_type, ingested_at, status }` where `status` is `active`
or `superseded` (when a newer hash for the same source path exists). This is where hash-dedup
and supersession live; classify reads the `active` set.

## 7. Skill / script structure

- **`consult-ingest` skill** — when-to-use, the immutability/provenance discipline, how to run
  and extend handlers, and the hand-off to classify. Orchestration only.
- **`scripts/ingest_normalize.py`** — dispatch by extension to a handler; write the immutable
  MD + update the manifest; idempotent by hash. Seeded with v1 handlers; the agent extends per
  format as real client files arrive (templates, not a frozen toolset).

## 8. Worked example

**Source** `Close Walkthrough.vtt` (raw):
```
WEBVTT

00:00:42.100 --> 00:00:48.000
<v Lead>We close the sub-ledgers first, then accruals. Accruals are the painful part —
all manual journal uploads, two analysts, three days.

00:00:48.500 --> 00:00:52.000
<v Lead>There's no documented checklist; people just know the order.
```

**Ingested MD** → the §3 example. Stage 2 can then cite
`ingested/...close_walkthrough.md#L12-14` and it will resolve to those cleaned lines for the
life of the engagement, because the file is immutable.

## 9. To validate during the vertical slice

- Confirm hash-dedup + immutability actually keep Stage 2 refs stable across a re-run.
- Is one-MD-per-source right for a 200-page PDF, or do huge sources need splitting (which
  complicates refs)?
- Do `<!-- page/slide/sheet -->` markers survive cleanly into the classifier's view and back
  to the reviewer's source trace?
- Decide how far into the format zoo v1 must reach for the R2R slice (transcripts + docx are
  likely enough to prove the pipeline).
- Defer images (v3) unless the slice needs them.
