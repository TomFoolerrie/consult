# T50 — Finish removing the CSV transport (Option A — DECIDED)

**Slice 3 · Wave 3 (do before T49) · Depends: T47 (gap_report.py), T48 (prose) ·
Touches: `skills/consult-improvement-log/scripts/improvement_log.py`, `scripts/gap_report.py`,
`spec.md`, `README.md`, `requirements.txt`**

## Decision
**Option A — make the code match the docs.** Confirmed by review: the hard part is already
done, so this is small and contained to ~2 files.

## Where this lives (scope, corrected by review)
The register engine is `improvement_log.py` — the single chokepoint for all `register.json`
writes. It is **not** in the LLM/judgment path or the Word-render path; only the optional
`.xlsx` register export touches pandas.
- The interactive `add-item` path is **already JSON-native** (`state_machine.py` calls
  `upsert-json`; `upsert_records()` exists in `improvement_log.py`). ✅
- The **only** remaining temp-CSV caller is `gap_report.py:228` (`write_register`).
- `pandas` is imported once (`improvement_log.py:38`) and used in exactly **4 places**:
  3 trivial calls in `clean_value` (`pd.isna`/`pd.to_datetime`, lines ~196/210/211) and
  1 substantive call in `build_xlsx` (`pd.DataFrame(...).to_excel(engine="openpyxl")`).

## Build
1. **`gap_report.write_register`** — replace the `NamedTemporaryFile(.csv)` + `update-json`
   subprocess (`:228-248`) with the JSON upsert path (pass row dicts to `upsert-json` /
   `upsert_records`). No temp CSV.
2. **`clean_value`** — swap the 3 pandas calls for stdlib (`x is None`/`""` checks;
   `datetime` parsing). 
3. **`build_xlsx`** — rewrite the DataFrame→Excel as a direct `openpyxl` `ws.append(...)`
   loop. openpyxl is already imported/used here for headers/styling, so no new dep.
4. **Remove the `import pandas`** and drop `pandas` from `requirements.txt`
   (leaves `openpyxl, pyyaml, jsonschema, python-docx`).
5. **Prose** — delete the self-contradicting "not done" admissions in `spec.md:515-517`,
   `:668-669` (Open-item 1); the "dropped" claims in §1/§4 (`spec.md:31-33`, `:260-262`,
   README:34) are now simply true.

## Tests
- `improvement_log.py` imports with `pandas` **uninstalled**;
- e2e register assertions pass with pandas uninstalled; no temp-CSV artifacts created;
- `build_xlsx` still produces a valid, openable workbook (assert sheet + a row).

## DoD
Code and prose agree; pandas gone from requirements; e2e green with the reduced dep set;
no scratch left.
