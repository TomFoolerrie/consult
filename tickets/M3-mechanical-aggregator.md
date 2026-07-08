# M3 — Mechanical aggregator (zero-token views)

**Depends on:** M0 (scaffolded folder + `_reference/`), M1, M2 (`doc_model.py`).
**Blocks:** M5.

## Goal

A deterministic Python engine that reads all procedure fragments + the
`_reference/` registry and (a) regenerates every python-owned derived view in
full, (b) writes the python region of the split-writer files, (c) writes a
`> _Pending synthesis (M5)._` placeholder into the agent regions/files, and
(d) emits an extract bundle for the M5 agents.

## Why

Strict-syntax IDs and registry-backed nouns are `SELECT`s, not synthesis — do
them in Python for zero tokens, idempotently, correct on delete/rename. The
reference registry lets Systems and the Role Dictionary become joins too, which
is why they moved here from M5. Reserve agents for genuine prose judgment.

## Changes

New `skills/consult-drafter/scripts/aggregate.py`. Imports `doc_model.py`
(manifest + `display_numbers`) and the shared ID logic factored out of
`reconcile.py` (do not duplicate). Reads `manifest.json`, every `role:
procedure` fragment, and `_reference/*.yaml`.

**Python-owned files — full rebuild each run, markers re-emitted:**
- `70_procedure-index.md` (`procedure-index`) — In-Scope index: one row per
  procedure `{[[slug]] token, title, group, Direction/Frequency/Owner from
  B. Quick Reference}`.
- `81_systems.md` (`systems`) — **registry × usage join**: one row per
  `systems.yaml` entry (canonical name, description, limitations) + a "Related
  Procedures" cell = the `[[slug]]` tokens of procedures whose canonical mentions
  matched that entry (by name or alias).
- `90_appendix-b-gaps.md` (`gap-log`) / `91_appendix-c-screens.md`
  (`screenshot-index`) — one row per `GAP-` / `SC-`, with a Source Procedure
  `[[slug]]` column (IDs are procedure-local, so the column disambiguates).

**Split-writer files — Python writes ONLY the `region: mechanical` block:**
- `80_roles.md` → **Role Dictionary** block = join from `roles.yaml`
  (role, reports-to, responsibilities) + "Appears In" `[[slug]]` list from matched
  Preparer/Reviewer mentions. The `region: judgment` (RACI) block is left with the
  pending placeholder for M5.
- `88_appendix-a-risks.md` → **observation rows** = one per `PP-`/`IO-` callout
  (id, observation text, Source Procedure `[[slug]]`). The `region: judgment`
  (impact/priority/recommendation) block gets the pending placeholder.

**Agent-only files — placeholder:**
- `82_dependencies.md` → heading + marker + `> _Pending synthesis (M5)._`.

**Extract bundle `<area>.extract.json` (scratch, git-ignored)** for M5:
- Per split-writer file, the mechanical rows M3 just wrote (so the agent copies
  them through and only fills its region).
- `raw_dependencies`: each procedure's `A. Process Overview` text, tagged by slug.
- For RACI: role × procedure/step incidence (which matched role appears in which
  procedure's steps) as a candidate grid.

**Registry matching (nouns) — flag, don't drop:** match canonical mentions from
`B. Quick Reference` / step `**System:**` fields against `systems.yaml` /
`roles.yaml` names + aliases. A mention matching nothing → **WARNING** naming the
mention + procedure ("add an entry or alias"); it is never silently dropped and
never guessed into a new entry.

**Fail-loud IDs (nonzero exit, nothing dropped):** bare gap tag;
referenced-but-undefined ID; ID prefix not matching its callout label (**new code
owned here**); conflicting duplicate ID **within a procedure** (IDs are
procedure-local — the check is per-procedure, review-scoping-safe). Delimiter
tolerant (`-`/`–`/`—`); ID grammar strict.

**Idempotent:** two runs, no procedure/registry change → byte-identical outputs.

## Acceptance

- `70/81/90/91` and the Python regions of `80/88` are rebuilt from the
  procedures + registry; deleting a procedure removes its rows/usages next run.
- `81_systems.md` shows every `systems.yaml` entry with correct "Related
  Procedures" back-references; a system used but absent from the registry raises a
  WARNING (not dropped).
- `80_roles.md` Role Dictionary block comes from `roles.yaml`; its RACI region
  holds the pending placeholder.
- `88` observation rows come only from callouts; `H. Known Issues` is not read.
- Two procedures each defining a local `CTRL-001` do **not** collide; the
  per-procedure duplicate check still catches a real intra-procedure dup.
- `[[GAP — no id]]` and a `PAIN POINT — CTRL-9` mismatch each cause nonzero exit.
- En-dash vs em-dash delimiter difference does not error.
- Two consecutive runs are byte-identical; no committed scratch files.

## Out of scope

RACI, dependency prose, Appendix-A judgment cells — M5.

## Adversarial review resolutions

- **#5:** In-Scope index python-owned.
- **#2:** derived cross-refs use `[[slug]]` tokens.
- **#8:** systems/roles are registry joins (canonical), not fake-mechanized free
  text; dependencies stay agent prose.
- **#9:** Appendix A observation from callouts only; H not parsed.
- **#10:** python writer re-emits derived + region markers.
- **#11 / split-writer:** region markers keep python and agent bytes disjoint.
- **#14:** label↔prefix check built here; runs before reconcile.
- **#16:** pending-synthesis placeholders in agent regions/files.
- **#17:** tolerant delimiter, strict ID grammar.
- **r3:** Systems + Role Dictionary moved here as registry joins; ID checks are
  procedure-local for parallel-fill safety.
