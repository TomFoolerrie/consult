# M5 — Change-scoped judgment agents (RACI · dependencies)

**Depends on:** M3. **Blocks:** none (top of the stack).

## Goal

Fill the remaining genuine-judgment content. Python computes which procedures
changed since a derived region was last built and hands each agent a scoped work
order (changed procedures + M3 extract bundle + the agent's own prior region).
Each agent writes exactly one agent-owned region/file; everything mechanical
already came from M3.

## What's left for agents (r3 shrank this)

The reference registry (M0) turned Systems and the Role Dictionary into Python
joins (M3), and Appendix A is fully mechanical (the drafter authors impact +
severity in the PP/IO callouts). The only judgment left — **each a clean
single-writer file**:
- **RACI** — `84_raci.md` (Responsible / Accountable / Consulted / Informed per
  activity). Reads M3's `raci_inputs` (Preparer/Reviewer + step prose + role
  slugs); the agent infers R/A/C/I from that prose.
- **Dependencies** — `82_dependencies.md`, from reading each procedure's
  `A. Process Overview` prose.

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
`{derived_kind, changed_procedure_slugs, bundle_path}` (the bundle holds
`raci_inputs` / `raw_dependencies`). The agent **reads its own prior file from
disk** (it has Read) to preserve unaffected judgment without a synthetic key
(review #11); the orchestrator does **not** pass prior-file content in the work
order — that would pull a derived draft into its context (r3 review #13).

*Concrete shape of `scope_delta.py`:*

- **`.hashes.json`** (per area, git-ignored) is `{derived_kind: {slug: hash}}` —
  one baseline map per **agent-owned** derived kind (`dependencies`, `raci`),
  each recording the procedure content hashes that kind's file was last built
  from. Mechanical (python-owned) files are not tracked here; M3 rebuilds them in
  full every run, so they need no delta.
- **Content hash = SHA-256 of the procedure file's bytes** (via
  `doc_model` manifest enumeration — `role: procedure` components). Hashing the
  raw file, not the assembled/numbered text, is what makes a manifest-only
  reorder a no-op: `order`/`l2_order` change but no procedure file does, so the
  delta is empty and numbers still come out right at render (M4). One content-hash
  mechanism only — **no git-diff path** (review #15): works with no git, on first
  run, after rebase/squash, identically.
- **Delta** for a kind = procedures whose current hash **differs from or is absent
  in** that kind's baseline map. No baseline entry for the kind (first run) => all
  current procedures. A deleted procedure simply drops out of the current map (its
  rows are M3's / the agent's concern, not the delta's).
- **API:** `work_order(folder, kind) -> dict`, `changed_procedure_slugs(folder,
  kind) -> [slug]`, and `commit(folder, kind)` which rebaselines only that kind's
  map to the current hashes **after a successful agent write**. `bundle_path`
  points at M3's `<area>.extract.json`. The work order deliberately omits
  prior-file contents.
- **CLI** (what `consult-orchestrate` runs — invocation prefix `scripts/` stays
  stable per README): `python3 scripts/scope_delta.py work-order --folder <dir>
  --kind <dependencies|raci>` prints the work order JSON; `... commit --folder
  <dir> --kind <k>` rebaselines after the write; `... changed ...` prints just the
  slug list. The commit step is the orchestrator's, not the agent's — the agent
  only writes its file and returns status.

**Agents** — `raci` (`84_`), `dependencies` (`82_`). Under `.claude/agents/`,
tool-scoped (Read + Write to their **one file** + reconcile/aggregate).
- Single-file writer: the agent rewrites its whole file, re-emits the
  `<!-- derived -->` marker (review #10), and fills judgment cells **only** for
  rows whose source procedure is in `changed_procedure_slugs`; unaffected rows
  carried from its **prior file read from disk**. No shared file, no region markers.
- Procedure refs it emits use `[[slug]]` tokens (review #2). Nouns stay canonical
  plain text (from the registry, already in the mechanical rows).

**Orchestration** — the sequence (M3 aggregate → M5 `work-order` per kind →
dispatch each agent → agent writes its one file → reconcile → M5 `commit` per kind
to rebaseline `.hashes.json`) is driven by `consult-orchestrate` (M7), not a
bespoke driver here. Baselining happens **after** a successful write, so a failed
or skipped agent leaves the prior baseline intact and the procedures stay "changed"
for the next pass. Single-writer-per-file is guaranteed by ordering + one file per
writer.

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

## Out of scope

Deciding which procedures exist / registry reassessment — M6.

## Adversarial review resolutions

- **#2/#10/#11/#15** as noted inline.
- **r3 #5:** agents write clean single-writer files (`82/84/89`); no region
  markers; Appendix A merged at render.
- **r3:** scope shrunk to RACI + dependencies.
- **r3 refinement:** Appendix-A judgment agent dropped — Appendix A is fully
  mechanical (M3), impact + severity authored by the drafter in the callouts.
