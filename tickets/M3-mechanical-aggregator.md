# M3 — Mechanical aggregator (zero-token views)

**Depends on:** M1, M2. **Blocks:** M5.

## Goal

A deterministic Python engine that reads all procedure fragments in a folder and
(a) regenerates the **pure-mechanical** derived files in full, (b) writes a
**"pending synthesis" placeholder** into agent-owned derived files, and (c) emits
an **extract bundle** of pre-extracted facts for the agents (M5).

## Why

What has strict syntax (IDs in callouts, gap/screenshot tags) is a `SELECT`, not
synthesis — do it in Python for zero tokens, idempotently, correct on
delete/rename. Reserve agents (M5) for genuine judgment cells only. See the
extraction contract in `tickets/README.md` for the strict-vs-not boundary.

## Changes

New `skills/consult-drafter/scripts/aggregate.py` (name TBD). Imports
`doc_model.py` (M2) for the manifest + `display_numbers` helper; imports the
shared ID logic factored out of `reconcile.py` (do not duplicate).

**Reads:** the folder's `manifest.json` + every `role: procedure` fragment.

**Writes — python-owned files, full rebuild each run, marker re-emitted:**
- `70_procedure-index.md` (`derived_kind: procedure-index`) — the In-Scope
  index: one row per procedure `{display number, title, group}` plus
  Direction/Frequency/Owner pulled from `B. Quick Reference` where present. Pure
  SELECT. Owner of the table that used to be hand-edited (review #5).
- `90_appendix-b-gaps.md` (`gap-log`) — one row per `GAP-` (id, location = source
  procedure `[[slug]]` token + step, description, owner/priority/status TBD if not
  inline).
- `91_appendix-c-screens.md` (`screenshot-index`) — one row per `SC-`.

  Cross-references in these files use `[[slug]]` tokens (resolved at render), not
  baked numbers (review #2).

**Writes — agent-owned files, placeholder only (M3 does not synthesize):**
- Into `80_roles.md`, `81_systems.md`, `82_dependencies.md`,
  `88_appendix-a-risks.md`: the section heading, the `<!-- derived -->` marker,
  and a `> _Pending synthesis (M5)._` note, so the interim Word doc shows an
  explicit pending state rather than raw `TBD` rows (review #16). M5 overwrites
  these in full.

**Emits — extract bundle `<area>.extract.json` (scratch, git-ignored):**
- **Systems:** a **raw, un-deduped mention list** — each literal string from
  `B. Quick Reference` "Primary systems / tools" and step `**System:**` fields,
  tagged with its source procedure slug. **No dedup/canonicalization** (that's the
  systems agent's job — review #8).
- **Roles:** raw Preparer/Reviewer strings, tagged by procedure slug.
- **Appendix A rows:** one per `PP-`/`IO-` callout with observation + source
  procedure slug; judgment cells (impact/priority/recommendation) blank. The
  callout is the **sole** source; `H. Known Issues` is not read (review #9).
- **Dependencies:** the raw `A. Process Overview` text per procedure, tagged by
  slug — handed to the agent to read. Python does **not** attempt phrase
  extraction (review #8).
- Procedure-index rows (same data written to `70_`).

**Fail-loud (nonzero exit, nothing dropped):** bare gap tag; referenced-but-
undefined ID; ID prefix not matching its callout label (this label↔prefix check
is **new code owned here** — `reconcile.py` doesn't do it today, review #14);
conflicting duplicate ID. Delimiter parsed tolerantly (`-`/`–`/`—`); ID grammar
strict (review #17).

**Idempotent:** two runs with no procedure changes → byte-identical outputs.

## Acceptance

- On a seeded folder, `70_`/`90_`/`91_` contain exactly the procedures/IDs
  present; deleting a procedure removes its rows next run.
- Agent-owned files contain the pending-synthesis placeholder + marker.
- Extract bundle: systems/roles are raw mention lists with source slugs (no
  dedup); Appendix A rows only from callouts; dependencies are raw A-section text.
- `[[GAP — no id]]` → nonzero exit, clear message, nothing dropped.
- A callout `> **PAIN POINT — GAP-9:** …` (prefix/label mismatch) → error.
- A single en-dash vs em-dash delimiter difference does **not** error.
- Two consecutive runs are byte-identical.
- No committed scratch files.

## Out of scope

Filling judgment cells; change-scoping; agent orchestration — all M5.

## Adversarial review resolutions

- **#5:** In-Scope index is a python-owned file with a real owner.
- **#2:** derived cross-refs use `[[slug]]` tokens, not baked numbers.
- **#8:** systems = raw mentions (agent canonicalizes); dependencies = raw prose
  for the agent; Python does not fake-mechanize them.
- **#9:** Appendix A sourced only from callouts; H not parsed.
- **#10:** python writer re-emits the derived marker.
- **#14:** label↔prefix check built here explicitly.
- **#16:** pending-synthesis placeholder into agent files.
- **#17:** tolerant delimiter, strict ID grammar.
