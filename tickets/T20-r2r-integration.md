# T20 — Synthesized R2R sample + end-to-end Slice-1 integration fixture

- **Slice:** 1 (capstone) · **Depends:** T19 + everything · **Touches:** `fixtures/r2r/` (new), `tests/` (new)
- **Refs:** spec §10 (the slice + its acceptance criteria); all stage contracts.

## Goal
Prove the Slice-1 thesis on realistic input and lock it as a **regression fixture**. Because the LLM stages
(classify/consolidate/draft/synthesis) aren't deterministic, the **automated** test drives the deterministic
spine with **canned LLM-stage outputs**; the live LLM run is exercised separately via `consult-run`.

## Scope (build)
1. **`fixtures/r2r/`** — a small **synthesized** Record-to-Report sample (no real client data):
   - 2 transcripts (`.vtt`/`.txt`) — a close walkthrough + a reconciliation walkthrough — written to touch
     several R2R L2s (close, account reconciliations, consolidation), include **one control claim stated only
     verbally** (for the evidence-tier gap), and **one clearly out-of-taxonomy snippet** (for `unmapped`).
   - `fixtures/r2r/canned/` — pre-made **classify artifacts** (schema-valid, refs resolving into the ingested
     MDs) standing in for the LLM classifier output, and 1–2 canned consolidated node MDs.
2. **`tests/test_slice1_e2e.sh`** (or `.py`) — deterministic end-to-end:
   `init` → `ingest_normalize.py` the transcripts → copy canned artifacts into `classify/` →
   `classify_merge.py` → (apply canned findings via `add-item`) → `gap_report.py scan` →
   `draft_inputs.py`/`synthesis_inputs.py gather` (assert bundles) → `render_deliverables.py render --what all`.
   Assert: lenses set + evidence present on R2R nodes; register has improvements + gaps + **≥1 unmapped** +
   a **verbal-tier** gap; deliverables render to `.docx`; and a **second full run is idempotent** (no
   duplicate evidence/findings/unmapped — exercises the floor). Clean up the scratch engagement.

## Out of scope
Live LLM fan-out (run separately via `consult-run`); review loop (S2).

## Tests (the deliverable IS the test)
Running `tests/test_slice1_e2e.sh` exits 0 with every assertion PASS, including the **idempotent second run**.
Document any canned-vs-live divergence. The fixture engagement must be removed at the end (or live under a
git-ignored scratch id).

## Done when
Fixtures + e2e test present and green on two consecutive runs; report output + any deviation. (This is the
Slice-1 regression fixture and the basis for the live `consult-run` demo.)
