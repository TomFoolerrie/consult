# T11 — `consult-classifier` skill + artifact validator

- **Slice:** 1 · **Depends:** T10 (ingested-MD format) · **Touches:** `skills/consult-classifier/` (new), `scripts/validate_artifact.py` (new)
- **Refs:** `classify_contract.md` (§2a, §3 schema, §4 sub-agent I/O, §3 schema-limitation note); `schemas/classify_artifact.schema.json`.

## Goal
Two deliverables: (1) the **`consult-classifier` skill** — the brief a per-doc sub-agent follows to read one
ingested MD + a taxonomy slice and emit a per-doc artifact; (2) **`scripts/validate_artifact.py`** — the
deterministic validator the orchestrator/merge runs on each artifact before trusting it.

## Scope (build)
1. **`scripts/validate_artifact.py`** — `validate --artifact PATH [--engagement E]`:
   - JSON-Schema validate against `schemas/classify_artifact.schema.json` (shape).
   - **Cross-field checks the schema can't do:** every `node` exists in `reference/taxonomy.yaml`;
     every `lens_signal.value` is valid **for its named lens** (per `state_machine.LENS_VALUES`);
     every `evidence_ref` / `lens_signal.evidence_ref` **resolves** to real lines in the cited ingested MD
     (parse `path#Lstart-Lend`, open the file under `engagements/{E}/`, assert the line range exists).
   - Exit nonzero with a clear per-issue report on any failure; exit 0 + "ok" when clean.
2. **`skills/consult-classifier/SKILL.md`** — when invoked (one ingested MD), read it + the taxonomy
   slice (L1/L2 ids+names; optional L2 descriptions); emit an artifact per the schema:
   `node_hits` (confidence, l3_hints, evidence refs `path#L-L`, lens_signals, candidate_findings with
   `dedup_key` proposals + `evidence_tier`) + `unmapped`. **Never write state.** Write the artifact
   atomically to `classify/{hash}.artifact.json` and return a one-line summary. Honesty rules from
   `classify_contract.md` §4 (real refs only; honest confidence; anything that fits no L2 → `unmapped`).
   Include a short worked example mirroring `classify_contract.md` §6.

## Out of scope
The merge (T12). Tuning the lens thresholds. Actually running fan-out (T19).

## Tests (for the validator; scratch as needed, clean up; do not commit)
1. The `classify_contract.md` §3 worked-example artifact (write it to a temp file) **passes** the validator
   when its cited MD lines exist (create a matching fake ingested MD with enough lines).
2. **Bad node** (`node: bad.key`) → nonzero, names the offending node.
3. **Bad lens value** (`process: machine`) → nonzero, names it (schema's flat enum wouldn't catch this).
4. **Hallucinated ref** (`#L9999` on a 5-line MD) → nonzero, names the unresolvable ref.
5. A clean artifact → exit 0.
6. SKILL.md exists, names the schema, and its embedded example validates with the validator.

## Done when
Validator + SKILL present; tests pass; `validate_artifact.py` compiles; report output + deviations.
