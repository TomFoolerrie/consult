# M5 — Change-scoped judgment agents (RACI · dependencies · Appendix-A)

**Depends on:** M3. **Blocks:** none (top of the stack).

## Goal

Fill the remaining genuine-judgment content. Python computes which procedures
changed since a derived region was last built and hands each agent a scoped work
order (changed procedures + M3 extract bundle + the agent's own prior region).
Each agent writes exactly one agent-owned region/file; everything mechanical
already came from M3.

## What's left for agents (r3 shrank this)

The reference registry (M0) turned Systems and the Role Dictionary into Python
joins (M3). The only judgment left — **each a clean single-writer file**, no
regions:
- **RACI** — `84_raci.md` (Responsible / Accountable / Consulted / Informed per
  activity). Seeded by M3's `raci_grid`; the agent assigns A/C/I.
- **Dependencies** — `82_dependencies.md`, from reading each procedure's
  `A. Process Overview` prose.
- **Appendix-A judgment** — `89_appendix-a-judgment.md`: one row per `(slug, id)` from
  M3's `appendix_a_observations`, filling impact / priority / recommendation. M4 joins
  it back to `88_appendix-a-observations.md` on `(slug, id)` at render into one table.

## Change signal: content hash (single mechanism)

Content-hash baseline only — no git-diff path (review #15): covers non-git,
first-run, rebase, squash with one code path and matches folder-as-truth.
- `.hashes.json` (git-ignored) records, per derived region/file, the procedure
  content hashes it was last built from.
- Delta = procedures whose current hash differs/absent. First run → all changed.
- Update `.hashes.json` after a successful write.

> This replaces the earlier "agents read git history" idea — same goal, simpler,
> more robust. Flagged as a deliberate deviation.

## Changes

**Delta engine** (`scope_delta.py`, imports `doc_model.py`): per agent file,
compute changed-procedure set from `.hashes.json`; emit a work order
`{derived_kind, changed_procedure_slugs, mechanical_context (from bundle),
raci_grid | raw_dependencies | appendix_a_observations, prior_file_contents}`.
The **prior file** is included so the agent preserves unaffected judgment
without a synthetic key (review #11).

**Agents** — `raci` (`84_`), `dependencies` (`82_`), `appendix-a-judgment` (`89_`).
Under `.claude/agents/`, tool-scoped (Read + Write to their **one file** +
reconcile/aggregate).
- Single-file writer: the agent rewrites its whole file, re-emits the
  `<!-- derived -->` marker (review #10), and fills judgment cells **only** for
  rows whose source procedure is in `changed_procedure_slugs`; unaffected rows
  carried from `prior_file_contents`. No shared file, no region markers.
- Procedure refs it emits use `[[slug]]` tokens (review #2). Nouns stay canonical
  plain text (from the registry, already in the mechanical rows).

**Orchestration** — the sequence (M3 aggregate → M5 delta → dispatch each agent →
reconcile) is driven by `consult-orchestrate` (M7), not a bespoke driver here.
Single-writer-per-file is guaranteed by ordering + one file per writer.

## Acceptance

- Changing one procedure → work order names only it; only affected RACI/dep/appendix-A
  rows update; mechanical regions and other regions untouched.
- Deleting a procedure → mechanical rows vanish (M3); judgment cells not
  resurrected.
- A manifest-only reorder (no content change) → no synthesis work, yet the
  rendered doc shows correct numbers (M4 resolves `[[slug]]` at render) —
  reorder-staleness bug closed (review #2).
- Non-git folder: hash baseline works with no git (review #15).
- No file is written by both Python and an agent (one writer per file).
- After M5, M4 renders `88_`+`89_` as a single Pain Points & Improvement Opportunities table joined on `(slug, id)`.

## Out of scope

Deciding which procedures exist / registry reassessment — M6.

## Adversarial review resolutions

- **#2/#10/#11/#15** as noted inline.
- **r3 #5:** agents write clean single-writer files (`82/84/89`); no region
  markers; Appendix A merged at render.
- **r3:** scope shrunk to RACI + dependencies + Appendix-A judgment.
