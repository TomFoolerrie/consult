---
name: consult-improvement-log
description: Maintain the Improvement Log by merging edits into JSON and rebuilding the Excel workbook. Outputs updated JSON and XLSX each cycle.
---

# Skill: Improvement Log — JSON/CSV/XLSX Sync

## Purpose

Maintain a structured process improvement log across chat sessions using a JSON source of truth, human-edited CSV, and a generated Excel workbook.

**Script:** `scripts/improvement_log.py`

---

## MANDATORY: Always Use the Script

**Never modify the JSON directly with Python or any other method.**

All JSON writes — inserts, updates, archives, deletes — MUST go through `improvement_log.py`. This applies even when direct Python manipulation seems faster or simpler. The script handles timestamping, backup-before-overwrite, `record_count` sync, and field validation that raw Python edits silently skip.

The only permitted JSON operations outside the script are **reading** (to inspect records, determine the next ID, or map fields).

If you find yourself writing Python that opens and mutates the JSON file directly: **stop, delete that code, and use the script instead.**

---

## Per-Session Workflow

Every session starts with the current JSON. Claude then determines which path applies:

```
User provides: Improvement Log - Source of Truth.json
        ↓
   ┌────┴────┐
   │         │
Path A     Path B
CSV file   Freeform improvements described in chat
   │         │
   └────┬────┘
        ↓
Claude runs: update-json
        ↓
Claude runs: build-xlsx
        ↓
Claude presents updated JSON + XLSX
```

### What Claude produces each cycle (both paths)

1. **Updated JSON** — `Improvement Log - Source of Truth.json` (presented in chat)
2. **Rebuilt XLSX** — `Improvement Log Review.xlsx` (presented in chat)

The user saves both files to the working folder to replace the prior versions.

---

## Path A — JSON + CSV

### Step 1 — Receive inputs

User provides:
1. `Improvement Log - Source of Truth.json`
2. `Improvement Log Review.csv` (exported from Excel via `File → Save As → CSV UTF-8`)

---

### Step 2 — Ask about deletes

Before running `update-json`, ask the user:

> "Does the CSV contain any rows marked `deleted_candidate` that should be hard-deleted? (yes / no)"

- **Yes** → include `--apply-deletes`
- **No** → omit `--apply-deletes`

---

### Step 3 — Merge CSV into JSON

```bash
python scripts/improvement_log.py update-json \
  --json "Improvement Log - Source of Truth.json" \
  --csv "Improvement Log Review.csv" \
  --out-json "Improvement Log - Source of Truth.json" \
  --modified-by ""
```

> Writing to the same `--out-json` path triggers an automatic timestamped backup before overwrite.

---

## Path B — JSON + Freeform

### Step 1 — Receive inputs

User provides:
1. `Improvement Log - Source of Truth.json`
2. Natural language description of one or more improvements to add or update

---

### Step 2 — Parse and confirm

Claude reads the JSON to determine the current highest ID (e.g. `PP-024`) and inspects existing records for context.

For each improvement described, Claude maps it to the record schema and presents a structured summary for confirmation before writing anything:

```
New record — PP-025
  l1_cycle:               [value]
  l2_process:             [value]
  observation_pain_point: [value]
  recommended_action:     [value]
  priority:               [value]
  effort:                 [value]
  owner:                  [value]
  phase:                  [value]
  review_status:          needs_review
  record_status:          active
```

Ask the user to confirm or correct before proceeding.

---

### Step 3 — Synthesize CSV and merge into JSON

**This is the only permitted way to write changes to the JSON.** Do not manipulate the JSON file directly.

Claude constructs a minimal CSV containing **only the affected rows** (new inserts or targeted updates). Untouched records are not included — the script matches by `id` and leaves everything else as-is. Claude writes this minimal CSV to a temporary file, then runs:

```bash
python scripts/improvement_log.py update-json \
  --json "Improvement Log - Source of Truth.json" \
  --csv "_freeform_input.csv" \
  --out-json "Improvement Log - Source of Truth.json" \
  --modified-by ""
```

The temporary CSV is discarded after the run.

---

## Shared Final Steps (both paths)

### Rebuild Excel

```bash
python scripts/improvement_log.py build-xlsx \
  --json "Improvement Log - Source of Truth.json" \
  --xlsx "Improvement Log Review.xlsx"
```

To exclude archived records, add `--active-only`.

### Present outputs

Provide both files to the user for download or local save:

- `Improvement Log - Source of Truth.json`
- `Improvement Log Review.xlsx`

Report a summary:

```
Rows updated: X | inserted: X | unchanged: X | archived: X | deleted: X
```

---

## Other Commands

> These script commands are also mandatory for archives and deletes — do not set `record_status` to `archived` or `deleted_candidate` by editing the JSON directly.

### Archive records by ID

```bash
python scripts/improvement_log.py remove \
  --json "Improvement Log - Source of Truth.json" \
  --ids PP-024 \
  --out-json "Improvement Log - Source of Truth.json" \
  --archive \
  --modified-by ""
```

### Hard-delete records by ID

```bash
python scripts/improvement_log.py remove \
  --json "Improvement Log - Source of Truth.json" \
  --ids PP-024 \
  --out-json "Improvement Log - Source of Truth.json" \
  --modified-by ""
```

### Delete records missing from CSV (use carefully)

```bash
python scripts/improvement_log.py update-json \
  --json "Improvement Log - Source of Truth.json" \
  --csv "Improvement Log Review.csv" \
  --out-json "Improvement Log - Source of Truth.json" \
  --delete-missing \
  --modified-by ""
```

---

## Editable Fields

These fields may be changed in the CSV and will be merged into the JSON:

```
priority, effort, owner, phase, escalation_status,
process_owner_contacts, date_updated, notes_next_step,
review_status, change_notes, record_status
```

The `id` field is protected — changing it creates a new record.

---

## Record Status Values

| Value | Meaning |
|---|---|
| `active` | Open or in-progress item |
| `archived` | No longer active; retained for history |
| `deleted_candidate` | Hard-deleted on next run if `--apply-deletes` is passed |

## Review Status Values

| Value | Meaning |
|---|---|
| `needs_review` | Newly added or unvalidated |
| `reviewed` | Human has reviewed |
| `approved` | Accepted into the official log |
| `rejected` | Not moving forward; retained for history |

---

## Control Rules

1. **Always use the script.** `improvement_log.py` is the only permitted write path for the JSON. Raw Python edits bypass timestamping, backup, and validation — never do them.
2. **JSON is the source of truth.** Excel and CSV are review/import formats only.
3. **Never change an existing `id`.** It is the primary key; a changed ID creates a new record.
4. **Prefer archive over hard delete.** Hard delete is for duplicates, test rows, and errors.
5. **Use `change_notes`** for any meaningful update — e.g., `"Updated priority to High after client review."`

---

## Validation Checklist (before presenting output)

- Every record has a non-empty `id`
- No duplicate IDs exist
- `record_count` in metadata matches the records array length
- `last_modified_at` was updated
- XLSX can be regenerated cleanly from the updated JSON
