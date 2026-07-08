# M5 — Git-delta scoping + specialized synthesis agents

**Depends on:** M3. **Blocks:** none (top of the stack).

## Goal

Add the judgment layer: Python computes which procedures changed and hands each
specialized agent a scoped work order (changed procedures + M3 extract bundle +
shared vocabulary); each agent (re)writes exactly one agent-owned derived file,
touching only judgment cells for affected rows. Mechanical rows come straight
from M3.

## Why

Some derived content genuinely needs reading, not regex: Systems "Role in
Process" / "Known Limitations", Roles/RACI assignment, Key Dependencies from
prose, Appendix A impact/priority/recommendation. This is the only place tokens
are spent, and they're spent narrowly.

## Changes

**Delta engine** (new Python, e.g. `scope_delta.py`):
- Compute the set of `role: procedure` fragments changed since a derived file
  was last regenerated. Primary signal: `git diff --name-only <last>..HEAD` over
  the folder; **fallback** (folder not a git repo / no baseline): a content-hash
  manifest (`.hashes.json`) comparing current vs last-recorded procedure hashes.
- Record per-derived-file "last built at" provenance (commit sha or hash set) so
  the delta is computed against the right baseline.
- Emit a per-section **work order**: `{derived_kind, changed_procedures,
  mechanical_rows (from M3 bundle), canonical_systems, canonical_roles,
  existing_judgment_cells}`.

**Specialized agents** (one `derived_kind` each): `roles`, `systems`,
`dependencies`, `risks` (Appendix A judgment cells).
- Each is single-file-owner: it writes the whole derived fragment, copying M3's
  mechanical rows through verbatim and filling only the judgment cells for rows
  whose source procedure is in `changed_procedures`; unaffected judgment cells
  are preserved from `existing_judgment_cells`.
- All agents receive the same `canonical_systems` / `canonical_roles` vocabulary
  so terminology stays consistent without cross-talk.
- Agent defs live under `.claude/agents/`; tool-scoped (Read + Write to their one
  file + the reconcile/aggregate scripts).

**Orchestration:** a thin driver (skill or small script) that runs, in order:
M3 aggregate → M5 delta → for each agent-owned derived file, dispatch its agent
with the work order → reconcile. Ordering guarantees single-writer-per-file:
Python-owned files were already written by M3; agent-owned files are written only
here.

## Acceptance

- Changing one procedure's systems produces a work order naming only that
  procedure; the systems agent updates only the affected rows; other rows and
  other derived files are untouched.
- Deleting a procedure: its mechanical rows vanish (M3) and its judgment cells
  are not resurrected.
- Fallback hash path works in a non-git folder.
- No derived file is written by both Python and an agent.
- Terminology (system/role names) is consistent across Roles, Systems, and
  Appendix A on a seeded multi-procedure folder.

## Out of scope

Deciding *which procedures exist* (that's M6). M5 assumes the procedure set is
given and reacts to changes in it.
