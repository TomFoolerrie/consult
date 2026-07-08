# M5 — Change-scoped specialized synthesis agents

**Depends on:** M3. **Blocks:** none (top of the stack).

## Goal

Add the judgment layer: Python computes which procedures changed since a derived
file was last built and hands each specialized agent a scoped work order
(changed procedures + M3 extract bundle + shared vocabulary + the agent's own
prior file). Each agent rewrites exactly one agent-owned derived file, touching
only judgment cells for affected rows; mechanical rows come straight from M3.

## Why

Some derived content genuinely needs reading, not regex: Systems "Role in
Process" / "Known Limitations", Roles/RACI assignment, Key Dependencies from
prose, Appendix A impact/priority/recommendation. This is the only place tokens
are spent, and they're spent narrowly.

## Change signal: content hash (single mechanism)

Use a **content-hash baseline** as the *only* change mechanism — no git-diff
path (review #15). Rationale: the hash covers every case the git path is fragile
on (non-git folders, first run, rebase, squash-merge) with one code path, and it
matches the folder-as-truth model.

- `.hashes.json` (git-ignored) records, per derived file, the set of procedure
  content hashes it was last built from.
- Delta for a derived file = procedures whose current hash differs from (or is
  absent in) that record. First run → all procedures "changed."
- After a successful agent write, update `.hashes.json` for that file.

> This intentionally replaces the earlier "agents read git history" idea. Same
> goal (know what changed, spend tokens only there); simpler and more robust
> mechanism. Flagged as a deliberate deviation from the original phrasing.

## Changes

**Delta engine** (new Python, e.g. `scope_delta.py`, imports `doc_model.py`):
- Compute the changed-procedure set per derived file from `.hashes.json`.
- Emit a per-section **work order**:
  `{derived_kind, changed_procedure_slugs, mechanical_rows (from M3 bundle),
  raw_systems, raw_roles, raw_dependencies, canonical_hint,
  prior_file_contents}`. The **prior file** is included so the agent preserves
  unaffected judgment cells by reading its own last output — no brittle synthetic
  row key (review #11).

**Specialized agents** — one `derived_kind` each: `roles`, `systems`,
`dependencies`, `risks` (Appendix A judgment cells). Under `.claude/agents/`,
tool-scoped (Read + Write to their one file + reconcile/aggregate scripts).
- Single-file-owner: the agent writes the whole fragment, re-emits the
  `<!-- derived -->` marker (review #10), copies M3's mechanical rows through
  verbatim, and fills judgment cells **only** for rows whose source procedure is
  in `changed_procedure_slugs`; unaffected rows are carried over from
  `prior_file_contents`.
- **Canonicalization lives in the agent** (systems/roles): the agent dedupes the
  raw mention list into canonical entities and keeps that naming stable run-to-run
  by consulting its prior file (review #8, #11). All agents share one
  `canonical_hint` (the union of canonical names seen so far) so terminology stays
  consistent across Roles / Systems / Appendix A without cross-talk.
- Procedure cross-references the agent emits use `[[slug]]` tokens, never numbers
  (review #2).

**Orchestration** — a thin driver (skill or small script) runs, in order:
M3 aggregate → M5 delta → dispatch each agent-owned file's agent with its work
order → reconcile. Ordering guarantees single-writer-per-file: python-owned files
were written by M3; agent-owned files only here.

## Acceptance

- Changing one procedure's systems → work order names only that procedure; the
  systems agent updates only affected rows; other rows and other derived files
  untouched.
- Deleting a procedure → its mechanical rows vanish (M3) and its judgment cells
  are not resurrected.
- A manifest-only reorder (no procedure content change) produces **no** synthesis
  work, yet the rendered doc still shows correct numbers because M4 resolves
  `[[slug]]` at render — confirming the reorder-staleness bug is closed
  (review #2).
- Non-git folder: the hash baseline works with no git present (review #15).
- No derived file is written by both Python and an agent.
- Terminology (system/role names) is consistent across Roles, Systems, and
  Appendix A on a seeded multi-procedure folder.

## Out of scope

Deciding *which* procedures exist (M6). M5 assumes the set is given and reacts to
changes in it.

## Adversarial review resolutions

- **#2:** agent output uses `[[slug]]` tokens; a pure reorder needs no re-synthesis
  and still renders correct numbers (bug closed by the token model + M4).
- **#8:** canonicalization is explicitly the agent's job over M3's raw mentions.
- **#10:** agent re-emits the derived marker.
- **#11:** judgment-cell preservation via the agent reading its own prior file
  (no fragile synthetic key).
- **#15:** single content-hash change signal; git-diff path dropped.
