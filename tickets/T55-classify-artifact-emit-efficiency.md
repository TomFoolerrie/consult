# T55 — Classify artifact: emit efficiency (constrained emission + payload trim)

**Slice 4 (Cost & Runtime Efficiency) · Follow-up · From field run (3 real artifacts) ·
Depends: T57 (the fan-out workflow + its schema seam) for Phase 2; Phase 1 has no dep · Touches:
`schemas/classify_artifact.schema.json`, `skills/consult-classifier/SKILL.md`,
`.claude/workflows/consult-fanout.*` (the classify `agent()` schema seam), `scripts/classify_merge.py`,
`scripts/validate_artifact.py`, `tests/`.**

> **Runtime correction.** Earlier I deferred constrained/tool-call emission "to the API/SDK path,
> not available in Desktop." **That was wrong** — you run **Claude Code**, whose **Workflow
> `agent(prompt, {schema})`** forces a StructuredOutput tool call and returns a **schema-validated
> object** (confirmed against the live Workflow tool contract, not just docs). So valid-by-
> construction emission is **available now**, under the T57 fan-out workflow. This is the
> primary fix; the `quote` trim is a secondary token win that helps on either path.

> **Scope note.** The *only* model-hand-authored JSON-against-schema in the suite is the
> classifier's `classify/{hash}.artifact.json`. Consolidate/draft outputs are Markdown; state
> writes go through the command path. Keep this ticket to that one artifact.

## Problem

`consult-classifier` hand-authors a deep nested artifact (`node_hits → evidence → lens_signals →
candidate_findings`) that must validate against `schemas/classify_artifact.schema.json` **and**
pass `validate_artifact.py` cross-field checks. Three stacked costs:

1. **Free-decoding nested JSON with fumble-able enums.** The lens `value` is a *flat union* of all
   lenses' allowed values, so `process: machine` passes the schema structurally but is rejected by
   the cross-field check. Wrong nesting/enums → fail the gate → the skill says "fix and rewrite" →
   re-emit the **whole** artifact. **That rewrite loop is the token waste, not the braces.**
2. **Redundant payload.** Each evidence entry carries both a `ref` (`…#L42-48`, **required**) *and*
   a verbatim `quote` (**optional**). The ref already locates the text in the **immutable** MD; the
   `quote` is duplicated data the model must reproduce **exactly**, a fat token sink per row.
   Confirmed: schema requires only `ref`; merge already falls back `note → quote`
   (`classify_merge.py:323`), so `quote` is pure redundancy when a short `note` is present.
3. **All-or-nothing retries** — one bad row forces a full re-emit.

## Decision (recorded)

- **(1) Constrained emission via Workflow `agent({schema})` — chosen, primary.** When classify
  fan-out runs under T57's fan-out workflow, the per-doc `agent()` call passes
  `{schema: <classify_artifact.schema>}`. The runtime forces a StructuredOutput tool call and
  returns a validated object; the workflow writes it to `classify/{hash}.artifact.json`. The
  write→validate→rewrite loop (#1, #3) **disappears** — there is no hand-authored file to fail.
  `validate_artifact.py`'s *cross-field* checks (lens-value-valid-for-its-lens, evidence-ref
  resolves) still run as a post-write gate (schema-validity alone doesn't catch the flat-union
  trap).
- **(2) Drop `quote` from the emit contract — chosen, independent.** Keep `ref` + a short `note`.
  Highest value-to-change ratio; helps tokens on **both** the constrained and the legacy hand-
  authored path. Near-zero risk (merge already prefers `note`).
- **(3) NDJSON shallow records — demoted to fallback.** Only worthwhile if T57's workflow is *not*
  adopted (no constrained emission), to localize retries on the hand-authored path. With (1) in
  place the rewrite loop is gone, so NDJSON's main benefit evaporates. Keep as a documented
  fallback, don't build speculatively.

## Build

**Phase 1 — trim (do first; independent of T54):**
1. `consult-classifier/SKILL.md`: stop emitting `quote`; require a concise `note` per evidence
   entry; keep `ref` exact. Update **both** `quote` references: the worked example (~lines 140-186)
   **and the inline evidence-schema contract line at `:62`** (`` `evidence[]` — `{ ref, quote, note }` ``).
   Editing only the example leaves `:62` still advertising `quote`.
2. `schemas/classify_artifact.schema.json`: keep `quote` **permitted but discouraged** (old
   artifacts still validate). **Do NOT remove `quote` from the schema** without a full fixture
   sweep — `additionalProperties: false` (`:54`) means a lingering `quote` in any committed fixture
   would then fail validation. Don't make `note` strictly required if that breaks valid fixtures;
   prefer "ref + (note|quote)".
3. `classify_merge.py`: confirm the `note → quote` fallback (`:323`) is fine when `quote` is
   absent (`ev.get("quote") → None` — already graceful); add a comment marking `quote` legacy.
4. `validate_artifact.py`: absence of `quote` is not an error; guidance points at missing `note`.

**Phase 2 — constrained emission (with T57's workflow):**
- In the fan-out workflow's classify stage, the per-doc `agent()` call uses the **`consult-classifier`
  custom agent type** (T57 Decision A) **plus** `{schema}` loaded from
  `schemas/classify_artifact.schema.json`, so there is **one** schema source of truth (the
  StructuredOutput schema and the `validate_artifact.py` schema must not drift).
- **Write owner (reconciled with T57):** on the schema path the **workflow** persists the returned
  validated object atomically (temp file + `os.rename`) to `classify/{hash}.artifact.json` (the
  classifier sub-agent returns the object; the workflow writes it), then runs `validate_artifact.py`
  for the **cross-field** gate. Preserve the "artifact exists + validates ⇒ doc classified"
  readiness predicate. (On the standalone hand-authored path the classifier writes its own file, as
  today.)
- Keep the classifier SKILL usable **standalone** (hand-authored path) for non-workflow runs —
  the schema is the contract either way.

**Phase 3 — NDJSON:** build only if Phase 2 is declined; otherwise document as deferred fallback.

## Tests

- **Trim (note-bearing):** an artifact with `ref` + `note` and **no** `quote` validates and merges
  identically (same evidence note applied; **state side** byte-identical) to the pre-trim form. Use
  a `note`-bearing fixture — the byte-identity holds only when `note` is present.
- **Trim (quote-only, the behavioral edge):** an evidence row with `quote` but **no** `note` merges
  **note-less** after the trim (the `note → quote` fallback has nothing to fall back to). Assert
  this expected, non-identical outcome rather than pretending it's identical.
- **Back-compat:** a legacy `quote`-bearing artifact still **schema-validates** after Phase 1
  (since `quote` stays declared in the schema). Guards the "don't delete `quote` from the schema"
  rule.
- **Enum trap regression:** `process: machine` still fails `validate_artifact.py` (cross-field
  gate not loosened) — this must hold on **both** the hand-authored and constrained paths.
- **Constrained path (Phase 2):** the workflow classify stage returns an object that schema-
  validates; a deliberately schema-violating model attempt is auto-retried by the runtime, never
  written half-formed; the written artifact passes the cross-field gate; one schema source (no
  drift between StructuredOutput and validator).
- **No regression:** Slice-1 e2e green; the classify fan-out fixture drives the same merged state.

## DoD

- `quote` removed from the emit contract; `ref` + `note` carry evidence; merge + validator behave
  identically; existing fixtures validate + merge byte-identically on the state side.
- Under T57's workflow, classify emission is schema-validated by construction — no write→validate→
  rewrite loop — with cross-field checks still enforced and a single schema source of truth.
- NDJSON either unneeded (constrained path adopted) or documented as the fallback for the hand-
  authored path.
- A re-measure (T56) records the token delta of the trim + constrained emission on a sample doc.
