---
name: consult-improvement-log
description: Engine for the engagement Item Register (register.json) — the unified, agent-driven item store for improvements, gaps, screenshots, unmapped content, and themes. Writes are JSON-native upserts; build-xlsx is an optional read-only snapshot. Humans review via Word, not Excel.
---

# Skill: Item Register — Agent-Driven JSON Engine

## Purpose

`improvement_log.py` is the engine for the engagement **Item Register** — `register.json`,
the Layer 2 source of truth. It is a single flat item store, discriminated by `type`,
that the pipeline writes programmatically. There is **no human CSV/Excel round-trip**:
agents write structured JSON records; humans review on **Word** (Stage 6), not in a
spreadsheet.

The register holds every item that hangs off an L2 taxonomy node:

- `improvement` — a process improvement opportunity (Stream B)
- `gap` — a gap / validation item (from the drafter gap tags)
- `screenshot` — a screenshot placeholder (SC-IDs)
- `unmapped` — content that did not map to an L2 node yet (carries `disposition`)
- `theme` — a cross-cutting finding spanning multiple L2 nodes (carries `related_nodes`)

Node-bound items (`improvement`, `gap`, `screenshot`) link to their taxonomy node via
`l1_cycle` / `l2_process` (kebab slugs). `unmapped` and `theme` rows are null-node rows.

In a pipeline engagement the file is `engagements/{id}/register.json`.

**Script:** `skills/consult-improvement-log/scripts/improvement_log.py`

---

## MANDATORY: Always Use the Script

**Never modify `register.json` directly with Python or any other method.**

All JSON writes — inserts, updates, archives, deletes — MUST go through
`improvement_log.py`. The script handles timestamping, backup-before-overwrite,
`record_count` sync, and soft vocab validation that raw edits silently skip. The only
permitted direct JSON operation is **reading** (to inspect records or map fields).

---

## How writes happen — agent-driven `upsert-json`

Writes are JSON-native upserts. The pipeline almost always reaches this through
`state_machine.py add-item`, which composes the record, mints the id, calls
`improvement_log.py upsert-json` under the hood, and resyncs node counts. Prefer that
path so the node tracker and register stay consistent:

```bash
python scripts/state_machine.py add-item \
  --engagement "{id}" \
  --type improvement \
  --l1 record-to-report --l2 close \
  --field observation_pain_point="Manual close checklist in email" \
  --field recommended_action="Move checklist into the close tool" \
  --field-json related_nodes='["record-to-report.close"]'
```

(`--l1`/`--l2` are omitted for `unmapped` / `theme` null-node rows. `--field` takes
`KEY=VALUE`; `--field-json` parses the value as JSON for array/object fields.)

To call the engine directly, use `upsert-json` with records as structured JSON via
exactly one of `--records-json` (inline) or `--records-file` (a path):

```bash
python skills/consult-improvement-log/scripts/improvement_log.py upsert-json \
  --json "register.json" \
  --out-json "register.json" \
  --records-json '[{"id":"IMP-0001","type":"improvement","dedup_key":"close::manual-checklist","recommended_action":"..."}]' \
  --modified-by "agent"
```

**Upsert matching precedence**, per incoming record:

1. If the record carries a non-empty `dedup_key`, match an existing record with the same
   `dedup_key` and update in place; otherwise insert.
2. Otherwise match by `id`; update in place if present, else insert.

An insert with no matching `dedup_key` requires a non-empty `id`. `id` is protected —
it is never overwritten on update. Writing to the same `--out-json` path triggers an
automatic timestamped backup before overwrite (one per invocation).

`dedup_key` is what makes re-consolidation idempotent: an LLM-confirmed finding re-emitted
on a later run upserts onto its existing row instead of minting a duplicate id.

---

## Validate

```bash
python skills/consult-improvement-log/scripts/improvement_log.py validate --json "register.json"
```

Reports per-record vocab issues and a count by `type`. Read-only. Add an optional JSON
Schema check with `--schema`:

```bash
python skills/consult-improvement-log/scripts/improvement_log.py validate --json "register.json" --schema "schemas/item_register.schema.json"
```

Vocab validation is **non-fatal**: values outside the controlled sets are flagged (sets
`requires_human_review=true`, `review_status=needs_review`, appends a note to
`change_notes`) rather than rejected, so the register stays extensible.

---

## Remove (archive or hard delete)

Prefer archive over hard delete. Archive marks `record_status=archived` and retains the
row; hard delete drops it.

```bash
# Archive by ID (retained for history)
python skills/consult-improvement-log/scripts/improvement_log.py remove \
  --json "register.json" --ids IMP-0024 \
  --out-json "register.json" --archive --modified-by "agent"

# Hard delete by ID (omit --archive) — for duplicates, test rows, errors
python skills/consult-improvement-log/scripts/improvement_log.py remove \
  --json "register.json" --ids IMP-0024 \
  --out-json "register.json" --modified-by "agent"
```

---

## build-xlsx — optional read-only snapshot

```bash
python skills/consult-improvement-log/scripts/improvement_log.py build-xlsx \
  --json "register.json" \
  --xlsx "Item Register.xlsx"
```

Add `--active-only` to exclude archived/inactive records. The XLSX is a **read-only
snapshot** of the register for quick inspection — it is **not** a review surface and is
**never re-imported**. Humans review deliverables in **Word at Stage 6**
(`consult-docx-builder` renders; `consult-review-comment-resolver` ingests the reviewed
Word). There is no CSV/Excel review cycle.

> Legacy: a CSV merge command (`update-json`, with `--apply-deletes` / `--delete-missing`)
> still exists in the script for back-compat with old hand-edited CSV exports. It is **not**
> the workflow and should not be used for new engagements — use `upsert-json` (via
> `state_machine.py add-item`).

---

## Register fields

`DEFAULT_RECORD_FIELDS` defines the canonical field order. Records allow additional
properties for forward-compatibility. Key fields beyond the classic set:

| Field | Meaning |
|---|---|
| `dedup_key` | Stable key for LLM-confirmed findings; upsert matches on this first so re-consolidation updates rather than duplicates. |
| `evidence_tier` | Defensibility of supporting evidence: `verbal`, `documentary`, `system_observed`. |
| `disposition` | For `unmapped` rows — how content was resolved: `pending`, `reclassified`, `converted`, `out_of_scope`. The final gate requires non-`pending`. |
| `related_nodes` | For `theme` rows — list of `l1.l2` node slugs the cross-cutting finding spans. |

Other canonical fields include `id`, `type`, `tag`, `date_identified`, `source`,
`l1_cycle`, `l2_process`, `l3_activity`, `observation_pain_point`, `root_cause`,
`recommended_action`, `impact_type`, `estimated_impact_benefit`, `effort`, `priority`,
`owner`, `phase`, `escalation_status`, `process_owner_contacts`, `notes_next_step`,
`record_status`, `review_status`, `requires_human_review`, `last_modified_by`,
`last_modified_at`, `change_notes`. `id` is protected — it is the primary key and is never
overwritten on upsert.

---

## Controlled vocabulary

| `type` | `tag` holds | Allowed `tag` values |
|---|---|---|
| `improvement` | the diagnostic **lens** it addresses | `process`, `automation`, `operating_model`, `capability` |
| `gap` | a normalized **gap tag** | `not_documented`, `unconfirmed`, `confirm`, `owner_unknown`, `reviewer_unknown`, `approver_unknown`, `system_unknown`, `timing_unknown`, `frequency_unknown`, `input_unknown`, `output_unknown`, `navigation_unknown`, `field_unknown`, `control_not_evidenced`, `approval_not_evidenced`, `evidence_retention_unknown`, `archive_location_unknown`, `exception_handling_unknown`, `downstream_dependency_unknown`, `upstream_dependency_unknown` |
| `screenshot` | SC status | free text (e.g. `pending`) |
| `unmapped` | (use `disposition`) | — |
| `theme` | (use `related_nodes`) | — |

Bracketed drafter tags are auto-normalized on write — e.g. `[[GAP — SYSTEM UNKNOWN]]`
→ `system_unknown`.

Other enums: `impact_type` ∈ {cost, time, risk, quality, control} · `effort` ∈ {low,
med, high} · `priority` ∈ {p1, p2, p3}.

---

## Record Status & Review Status

| `record_status` | Meaning |
|---|---|
| `active` | Open or in-progress item |
| `archived` / `inactive` | No longer active; retained for history; not rolled into node counts |
| `deleted_candidate` | Marked for hard delete (legacy CSV path only) |

| `review_status` | Meaning |
|---|---|
| `needs_review` | Newly added or unvalidated |
| `reviewed` | Human has reviewed (via Word, Stage 6) |
| `approved` | Accepted into the official log |
| `rejected` | Not moving forward; retained for history |

---

## Control Rules

1. **Always use the script.** `improvement_log.py` is the only permitted write path.
   Prefer `state_machine.py add-item`, which calls `upsert-json` and resyncs node counts.
2. **JSON is the source of truth.** The XLSX snapshot is read-only and never re-imported.
3. **No human CSV/Excel review round-trip.** Humans review on Word at Stage 6.
4. **Never change an existing `id`.** It is the primary key; upsert dedups on `dedup_key`
   first, then `id`.
5. **Prefer archive over hard delete.** Hard delete is for duplicates, test rows, errors.
6. **Use `change_notes`** for any meaningful update.
