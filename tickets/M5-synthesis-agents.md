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
joins (M3). The only judgment left:
- **RACI** — the `region: judgment` block of `80_roles.md` (Responsible /
  Accountable / Consulted / Informed per activity). Seeded by M3's role×procedure
  incidence grid; the agent assigns A/C/I.
- **Dependencies** — `82_dependencies.md`, from reading each procedure's
  `A. Process Overview` prose.
- **Appendix-A judgment** — the `region: judgment` block of `88_appendix-a-risks.md`
  (impact / priority / recommendation per `PP-`/`IO-` row).

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

**Delta engine** (`scope_delta.py`, imports `doc_model.py`): per agent region,
compute changed-procedure set from `.hashes.json`; emit a work order
`{derived_kind, changed_procedure_slugs, mechanical_context (from bundle),
raci_grid | raw_dependencies | appendix_observations, prior_region_contents}`.
The **prior region** is included so the agent preserves unaffected judgment
without a synthetic key (review #11).

**Agents** — `raci`, `dependencies`, `risks-judgment`. Under `.claude/agents/`,
tool-scoped (Read + Write to their one region/file + reconcile/aggregate).
- Region-scoped writer: the agent rewrites only its `region: judgment` block (or
  the whole `82_` file), re-emits markers (review #10), and fills judgment cells
  **only** for rows whose source procedure is in `changed_procedure_slugs`;
  unaffected rows carried from `prior_region_contents`. It never touches the
  mechanical region.
- Procedure refs it emits use `[[slug]]` tokens (review #2). Nouns stay canonical
  plain text (from the registry, already in the mechanical rows).

**Orchestration** — thin driver runs: M3 aggregate → M5 delta → dispatch each
agent → reconcile. Single-writer-per-region guaranteed by ordering + region
markers.

## Acceptance

- Changing one procedure → work order names only it; only affected RACI/dep/risk
  rows update; mechanical regions and other regions untouched.
- Deleting a procedure → mechanical rows vanish (M3); judgment cells not
  resurrected.
- A manifest-only reorder (no content change) → no synthesis work, yet the
  rendered doc shows correct numbers (M4 resolves `[[slug]]` at render) —
  reorder-staleness bug closed (review #2).
- Non-git folder: hash baseline works with no git (review #15).
- No region is written by both Python and an agent (marker-scoped).

## Out of scope

Deciding which procedures exist / registry reassessment — M6.

## Adversarial review resolutions

- **#2/#10/#11/#15** as noted inline.
- **r3:** scope shrunk to RACI + dependencies + Appendix-A judgment; agents write
  only their `region: judgment` block, never the mechanical region.
