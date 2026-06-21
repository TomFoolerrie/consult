# T10 — `consult-ingest` v1 (transcript + docx → immutable hashed MD + YAML header)

- **Slice:** 1 · **Depends:** — (independent of the floor; parallelizable with T01) · **Touches:** `scripts/ingest_normalize.py` (new), `skills/consult-ingest/` (new)
- **Refs:** `ingest_contract.md` (esp. §2 immutability, §3 format, §5 v1 row, §8 dir-check dedup); spec §5 Stage 1.

## Goal
A single entry that converts raw files to clean Markdown with a YAML header under
`engagements/{id}/ingested/`, with **immutable, source-hashed** artifacts (the line-stability guarantee
classify depends on). v1 handlers only: `.txt .md .csv .tsv .vtt .srt` and `.docx`.

## Scope (build)
1. **`scripts/ingest_normalize.py`** — `ingest --engagement E --source PATH [PATH...]` (or a dir):
   - Compute `source_hash` (sha256 of raw bytes). **Dir-check dedup:** if an ingested MD for that hash
     already exists, **skip** (idempotent). Slice 1 uses a directory check, **no manifest** (deferred).
   - Dispatch by extension to a handler. **Transcript** (`.vtt/.srt/.txt` transcript-like) reuses the
     existing `skills/consult-transcript-cleaner/scripts/clean_vtt.py` logic (import or call) — do not
     duplicate. **CSV/TSV** → Markdown table. **.docx** → text + tables, headings preserved (python-docx).
   - Write an **immutable** MD: descriptive dated filename, YAML header per
     `schemas/ingested_header.schema.json` (`source, source_hash, doc_type, ingested_at, ingester, title,
     immutable:true`), then cleaned body. **Never rewrite an existing ingested MD.**
2. **`skills/consult-ingest/SKILL.md`** — when-to-use, the immutability/provenance discipline, run/extend
   handlers, hand-off to classify. Match the house skill style.
3. Validate produced headers against `schemas/ingested_header.schema.json`.

## Out of scope
v2/v3 formats (pdf/pptx/xlsx/images), the manifest + supersession, provenance page/slide markers beyond
what docx headings give for free (note as TODO). Classification (T11).

## Tests (scratch `__t10__`, remove at end; do not commit)
1. Ingest a small `.vtt` → an `ingested/*.md` with a valid YAML header (schema-checked) and cleaned body
   (no timestamps/cue-ids); `doc_type:transcript`, `immutable:true`.
2. **Immutability/idempotency:** re-ingest the same file → **skipped** (same hash, file unchanged
   byte-for-byte; capture mtime/content and assert unchanged).
3. A changed source (different bytes) → a **new** MD (different hash-derived name); the old one untouched.
4. A `.csv` → a Markdown table; a `.docx` (create a tiny one with python-docx in the test) → text + heading.
5. Header validates against `schemas/ingested_header.schema.json`.

## Done when
Tests pass; script compiles; SKILL.md present; report output + any deviation.
