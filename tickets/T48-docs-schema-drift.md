# T48 — Documentation & schema drift reconciliation

**Slice 3 · Wave 2 (parallel, doc-only — independent of all code tickets) · Depends: — ·
Touches: `*_contract.md`, `spec.md`, `README.md`, `schemas/*.json` descriptions,
`skills/consult-improvement-log/SKILL.md`, `skills/.../canonical_sop_deliverable_template.md`**

## Fixes (from review)
1. **Stale "no code yet" banners** — `classify_contract.md:3`, `ingest_contract.md:3`,
   `consolidate_contract.md:3`, `generation_review_contract.md:3`, `orchestration_contract.md:3`,
   plus `classify_artifact.schema.json:5` and `ingested_header.schema.json:5`
   ("Not yet wired into code"). All these stages are built. Update banners to reflect built
   status + the implementing script.
2. **Schema description drift** — `item_register.schema.json:5` top-line says
   "improvements, gaps, screenshots" but the `type` enum has 5 (`unmapped`, `theme`). Fix the
   description; keep the node-level `items`/`counts` shape as-is (intentional).
3. **`consult-improvement-log/SKILL.md` wrong script path** — calls `scripts/improvement_log.py`
   (`:29,68,93,100,116,121,131`) but the file is at
   `skills/consult-improvement-log/scripts/improvement_log.py`. Fix to the full path
   (match `consult-state-machine/SKILL.md`).
4. **Remove the contradictory SOP template** — `canonical_sop_deliverable_template.md` is an
   all-`{{handlebars}}` shell that contradicts `consult-drafter/SKILL.md:285` ("not a shell
   template"); spec Open-item 10 already flags removal. Remove it (and any references).
5. **Status honesty** — README:153 / spec.md:1-10 "green and idempotent": add the
   `pip install -r requirements.txt` precondition (without pandas/jsonschema the e2e fails).

> **Note (do not fix here):** the "CSV transport dropped" contradiction (spec.md §1/§4 vs the
> still-present pandas/CSV path in `improvement_log.py`/`gap_report.py`) is resolved in **T50**,
> which requires a code-vs-docs decision. Leave that prose alone until T50 lands.

## Tests
- `python scripts/state_machine.py validate` still green on r2r-demo;
- grep check (add to e2e or a lint step): no contract/schema still says "no code yet"/"not
  yet wired"; no SKILL references a bare `scripts/improvement_log.py`.

## DoD
Docs consistent with built code; schemas re-validate; template removed; no broken refs.
