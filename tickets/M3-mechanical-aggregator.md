# M3 — Mechanical aggregator (zero-token views)

**Depends on:** M1, M2. **Blocks:** M5.

## Goal

A deterministic Python engine that reads all procedure fragments in a folder and
(a) regenerates the **pure-mechanical** derived files in full, and (b) emits an
**extract bundle** of pre-extracted facts for the agent-owned derived files (M5).

## Why

Most of what looks like "the appendixes" is a `SELECT`, not synthesis. Doing it
in Python costs zero tokens, is idempotent, and is correct on delete/rename
(full rebuild each run). Reserve agents (M5) for genuine judgment cells only.

## Changes

New `skills/consult-drafter/scripts/aggregate.py` (name TBD):

**Reads:** the folder's `manifest.json` + every `role: procedure` fragment,
using the extraction contract in `tickets/README.md`.

**Writes (writer: python files) — full rebuild each run:**
- `90_appendix-b-gaps.md` — one row per `GAP-` (id, location = source proc
  display number + step, description from the tag/callout text, owner/priority/
  status left as TBD if not inline).
- `91_appendix-c-screens.md` — one row per `SC-` (id, caption, procedure/step,
  source, status).

**Emits (scratch, not committed) — extract bundle `*.extract.json`:**
- Canonical entity lists: distinct systems, distinct roles (deduped, with the
  procedures each appears in) — the shared vocabulary for M5 agents.
- Per-derived-kind mechanical rows the agent will copy through verbatim:
  - `risks` (Appendix A): one row per `PP-`/`IO-` with observation + source
    procedure; judgment cells (impact/priority/recommendation) blank.
  - `systems`: system → list of procedures it appears in; judgment cells blank.
  - `roles`: role → list of procedures/steps; judgment cells blank.
  - `dependencies`: raw upstream/downstream phrases pulled from each procedure's
    `A. Process Overview`, tagged by source procedure (candidate list; the agent
    decides).
- The In-Scope Procedures index + Process Flow candidate rows (procedure display
  number, title, group).

**Fail-loud:** any extraction violating the contract (bare gap tag, undefined-but-
referenced ID, prefix/label mismatch, conflicting duplicate) → stderr diagnostic
+ nonzero exit; **never** silently drop a row. Reuses `reconcile.py`'s ID logic
(factor shared bits into a small module rather than duplicating).

**Idempotent:** running twice with no procedure changes yields byte-identical
mechanical files and bundle.

## Acceptance

- On a folder with seeded procedures, `90_`/`91_` are regenerated with exactly
  the IDs present in the procedures; deleting a procedure removes its IDs on the
  next run.
- Extract bundle contains deduped systems/roles with correct back-references.
- A malformed tag (e.g. `[[GAP — no id]]`) causes nonzero exit with a clear
  message; nothing is dropped silently.
- Two consecutive runs are byte-identical (idempotence).
- No committed scratch files (bundle is git-ignored or written to a scratch
  path).

## Out of scope

Filling judgment cells; git-delta scoping; agent orchestration — all M5.
