---
name: consult-ingest
description: Stage 1 ingest — convert raw client files (transcripts, docx, csv/tsv, text) into clean Markdown with a YAML header under engagements/{id}/ingested/. Immutable, source-hash-keyed artifacts that guarantee Stage 2 evidence refs stay stable. Orchestrator-driven deterministic Python via scripts/ingest_normalize.py.
---

# Skill: Consult Ingest — Raw Files to Immutable Hashed Markdown

## Purpose

This is the **single skill surface over Stage 1 ingest**. It turns raw client
files of any v1 format into clean, uniform **Markdown with a YAML header** under
`engagements/{id}/ingested/`, ready for the Stage 2 classifier (one sub-agent
reads one ingested MD).

It is **orchestrator-driven deterministic Python** — the orchestrator calls
`scripts/ingest_normalize.py` directly. Ingest is **not** a spawned sub-agent
task. It **subsumes** `consult-transcript-cleaner`: the transcript handler
reuses `clean_vtt.py`'s cleaning logic rather than duplicating it.

Goal: strip noise (token efficiency) while **preserving substance, structure,
and provenance**.

## When to Use

Use when raw client material has landed and needs to become ingested MDs before
classification:

- A meeting/walkthrough **transcript** (`.vtt`, `.srt`, or a transcript-like
  `.txt`).
- A **`.docx`** memo, walkthrough write-up, or policy doc.
- A **`.csv` / `.tsv`** export (close calendar, control matrix, account list).
- Plain **`.txt` / `.md`** notes.

**Do NOT use it for:**

- Classification / diagnosis (that is Stage 2, `consult-classify` / T11). Ingest
  never assigns taxonomy nodes or lenses — `hints` in the header are
  best-effort, **non-authoritative** signals only.
- v2/v3 formats (`.pdf .pptx .xlsx`, images). Those handlers are deferred; add
  them to `ingest_normalize.py` as those client files actually arrive.
- Editing or re-cleaning an already-ingested MD. **Ingested MDs are immutable.**

## The Immutability / Provenance Discipline

These constraints are load-bearing and shape every run (ingest_contract.md §2):

1. **Ingested MDs are immutable, source-hashed artifacts.** One source file →
   one MD, named descriptively + dated + the source-hash short prefix, keyed by
   the **sha256 of the raw source bytes**. Once written it is **never
   rewritten**. This is exactly what guarantees Stage 2's `path#Lstart-Lend`
   evidence refs stay valid forever — line numbers cannot move if the file
   cannot change.

2. **Re-running ingest is idempotent.** Before writing, the script does a
   **dir-check dedup** (Slice 1, **no manifest**): it scans the engagement's
   `ingested/*.md` for a header with the same `source_hash` and **skips** if one
   exists. Re-ingesting the same bytes is a no-op.

3. **A changed source is a new artifact.** Different bytes = different hash = a
   **new** MD with a new name; the old MD and any refs into it remain valid.
   Supersession tracking (the manifest) is deferred to a later slice. Handler
   improvements likewise apply only to not-yet-ingested sources — re-ingesting
   with a better handler is a deliberate act that yields a *new* MD.

4. **Determinism.** No timestamps or run-specific data in the body — those live
   only in the YAML header (`ingested_at`, `ingester`).

## Ingested MD Format

Every file starts with a YAML header validated against
`schemas/ingested_header.schema.json`, then a cleaned body:

```markdown
---
source: client/Close Walkthrough 2026-03-01.vtt
source_hash: sha256:9f2c...                  # of the raw source bytes
doc_type: transcript                         # transcript|docx|csv|text|...
ingested_at: 2026-03-02T10:00:00Z
ingester: ingest_normalize.py/transcript@1   # handler + version
title: Close Walkthrough
provenance: { pages: null, slides: null, sheets: null }
hints: { client: null, systems: [], people: [] }   # best-effort, NON-authoritative
immutable: true
---

# Close Walkthrough

**Lead:** We close the sub-ledgers first, then accruals...
```

Body conventions by content: transcripts → cleaned prose (timestamps / cue ids /
speaker-spam stripped); CSV/TSV → a Markdown table; docx → text with headings
preserved and tables as Markdown tables.

## v1 Handlers

| Formats | doc_type | Handler | Notes |
|---|---|---|---|
| `.vtt .srt`, transcript-like `.txt` | `transcript` | reuses `clean_vtt.py` | timestamps/cue-ids/`<v>` tags stripped, speaker turns merged |
| `.txt .md` | `text` | passthrough | whitespace normalized; substance/structure kept |
| `.csv .tsv` | `csv` | table | rendered as a Markdown table |
| `.docx` | `docx` | python-docx | text + tables in document order; heading styles → Markdown headings |

`.txt` is sniffed: WEBVTT/SRT markers, `-->` cue timing, or `<v Speaker>` tags
route it to the transcript handler; otherwise it is treated as plain text.

## Run

From the repo root:

```bash
# Ingest one or more files (each --source may be a file or a directory).
python3 scripts/ingest_normalize.py ingest --engagement {id} \
  --source "client/Close Walkthrough.vtt"

# A directory is recursed for supported extensions.
python3 scripts/ingest_normalize.py ingest --engagement {id} --source client/uploads/

# Several sources at once.
python3 scripts/ingest_normalize.py ingest --engagement {id} \
  --source notes.txt close_calendar.csv memo.docx
```

Output lines report `written` or `skipped` per source and the destination MD
path. Re-running the same command after no source change prints all `skipped`.

**Requires** `pyyaml`, `jsonschema`, and (for `.docx`) `python-docx`
(`pip install python-docx`).

## Extending Handlers

Each handler is a function in `ingest_normalize.py` returning
`(doc_type, ingester_tag, body, provenance)`. To add a format:

1. Write `handle_<format>(path, raw)`; bump the `ingester_tag` version
   (`@2`, ...) when you change cleaning behavior so provenance stays honest.
2. Register the extension in `dispatch()` and the `*_EXTS` sets.
3. For paged/sheeted formats, emit inline provenance markers
   (`<!-- page N -->`, `<!-- sheet: NAME -->`) so refs trace back to the source.

These are templates, not a frozen toolset — extend per format as real client
files arrive. Never weaken the immutability guard or the dir-check dedup.

## Hand-off to Classify

Ingest's only output is the immutable `ingested/*.md` set. Stage 2
(`consult-classify` / T11) reads those MDs (one sub-agent per MD), assigns
taxonomy nodes, sets lenses, and cites evidence as `ingested/<file>.md#Lx-Ly`.
Those refs resolve forever **because** the files are immutable and hashed — so
the discipline above is the contract classify depends on. Ingest itself never
writes engagement state (`state.json` / `register.json`).
