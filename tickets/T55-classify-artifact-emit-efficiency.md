# T55 — Classify artifact: emit efficiency (payload trim + NDJSON option)

**Slice 4 (Cost & Runtime Efficiency) · Follow-up · From field run (3 real artifacts) ·
Depends: — · Touches: `schemas/classify_artifact.schema.json`, `skills/consult-classifier/SKILL.md`,
`scripts/classify_merge.py` (reader), `scripts/validate_artifact.py`, `tests/`.**

> **Field observation.** "JSON proved difficult for models to always match." The instinct that
> this is *not purely* a format problem is correct — it is three stacked costs (free-decoding a
> deep nested structure, a full-artifact rewrite on validation failure, and redundant payload).
> **Scope note:** the *only* model-hand-authored JSON-against-schema in the suite is the
> classifier's `classify/{hash}.artifact.json`. Consolidate/draft outputs are **Markdown**; state
> writes go through the **command path** (`state_machine.py`). So this ticket is scoped to that
> one artifact — do not chase a JSON-everywhere problem that does not exist.

## Problem

`consult-classifier` hand-authors a deep nested artifact (`node_hits → evidence → lens_signals →
candidate_findings`) that must validate against `schemas/classify_artifact.schema.json` **and**
pass `validate_artifact.py` cross-field checks. Three costs:

1. **Free-decoding nested JSON with fumble-able enums.** The lens `value` is a *flat union* of all
   lenses' allowed values, so `process: machine` validates structurally but is semantically
   invalid (the validator + merge reject it). The model gets nesting/enums wrong, fails the gate,
   and the skill says "fix and rewrite" → it re-emits the **whole** artifact. That rewrite loop
   is the token waste, not the braces.
2. **Redundant payload — the biggest single trim.** Each evidence entry carries both a `ref`
   (`…#L42-48`, **required**) *and* a verbatim `quote` (**optional**). The ref already locates the
   text in the **immutable** ingested MD; the `quote` is duplicated data the model must reproduce
   **exactly** or risk drift, and it is a fat token sink on every evidence row. Confirmed: schema
   requires only `ref`; the merge already falls back `note → quote` (`classify_merge.py:323`), so
   `quote` is pure redundancy when a short `note` is present.
3. **All-or-nothing retries.** Because the artifact is one nested document, a single bad
   node/evidence row forces a full re-emit instead of re-emitting just the offending record.

## Decision (recorded)

- **Drop `quote` from the emit contract — chosen.** Keep `ref` (required, resolves to the real
  lines) + a short `note`. Highest value-to-change ratio: cuts the #1 matching-failure surface
  and the biggest per-row token cost. Merge already prefers `note`; `quote` removal is
  near-zero-risk.
- **NDJSON / shallow records for retry isolation — chosen as an *option to evaluate*, not a
  mandate.** Emitting one record per line (denormalized: a `node_hit` row, then its `evidence` /
  `lens` / `finding` rows keyed by node) makes a malformed line re-emittable **alone** and lets
  the validator point at a line. It does **not** fix schema-matching (each line still must
  conform) and it costs a merge-reader rewrite. Treat as a measured follow-up gated on whether
  the trim alone (item above) closes enough of the gap.
- **Constrained / tool-call emission (valid-by-construction) — noted, deferred.** The strongest
  reliability fix (emit via a StructuredOutput tool whose input schema *is* the artifact schema →
  no validate-fix-rewrite loop) **requires the API/SDK or Claude Code runtime**; it is **not**
  available to a Claude Desktop skill that writes a file. Record it as the eventual fix for the
  API path; out of scope while the user runs in Desktop.

## Build

**Phase 1 — trim (do first, measure before doing Phase 2):**
1. `consult-classifier/SKILL.md`: stop emitting `quote`. Require a concise `note` on each
   evidence entry instead; keep `ref` exact. Update the worked example (lines ~140-186) to match
   (drop `quote`, keep `ref` + `note`).
2. `schemas/classify_artifact.schema.json`: keep `quote` **permitted but discouraged** (so old
   artifacts still validate) — or remove it if no committed fixture relies on it (check first).
   Do not make `note` strictly required if that breaks existing valid fixtures; prefer "ref +
   (note|quote)" so the merge's existing fallback stays satisfied.
3. `classify_merge.py`: confirm the `note → quote` fallback (`:323`) still behaves when `quote`
   is absent (it already does — `ev.get("quote")` → `None`). No functional change expected;
   add a comment noting `quote` is legacy/optional.
4. `validate_artifact.py`: ensure absence of `quote` is not an error; if it emits guidance,
   point at the missing `note` instead.

**Phase 2 — NDJSON (only if Phase 1 measurement shows retries/size still dominate):**
- Define a flat record grammar (one JSON object per line; `kind` discriminator: `node_hit` /
  `evidence` / `lens` / `finding` / `unmapped`; each keyed by `node`). Write to
  `classify/{hash}.artifact.jsonl`.
- Rewrite the merge reader + `validate_artifact.py` to consume NDJSON, validating **per line** and
  reporting the offending line number. Keep the existing nested `.json` reader for back-compat or
  migrate fixtures in the same change.
- Preserve the atomic-write contract (temp file + `os.rename`) and the "artifact exists +
  validates ⇒ doc classified" readiness predicate the orchestrator depends on.

## Tests

- **Trim (Phase 1):** an artifact with `ref` + `note` and **no** `quote` validates and merges
  identically (same evidence note applied) to the pre-trim form. A committed fixture re-classified
  produces a merge result byte-identical on the state side (evidence/lens/findings unchanged).
- **Enum trap regression:** an artifact with a wrong-lens value (`process: machine`) still fails
  `validate_artifact.py` (the trim must not loosen the cross-field gate).
- **NDJSON (Phase 2, if built):** a malformed single line is the only thing reported (line number
  cited); the other records still merge; re-emitting just that line passes. Atomic write + dedup
  readiness unchanged.
- **No regression:** Slice-1 e2e green; the classify fan-out fixture still drives the same merged
  state.

## DoD

- `quote` removed from the classifier emit contract; `ref` + `note` carry evidence; merge +
  validator behave identically; existing fixtures still validate and merge byte-identically on the
  state side.
- A re-measure (T56) records the token/size delta of the trim on a representative doc.
- NDJSON either shipped with a per-line validator + rewritten reader, or explicitly deferred with
  the measured reason it wasn't needed.
- Constrained/tool-call emission documented as the API/SDK-path fix; not attempted in the Desktop
  runtime.
