# M3 — Mechanical aggregator (zero-token views)

**Depends on:** M0 (scaffolded folder + `_reference/`), M1, M2 (`doc_model.py`).
**Blocks:** M5.

## Goal

A deterministic Python engine that reads all procedure fragments + the
`_reference/` registry and (a) regenerates every python-owned derived view in
full, (b) writes a `> _Pending synthesis (M5)._` placeholder into the agent-owned
files, and (c) emits an extract bundle for the M5 agents.

## Why

Strict-syntax IDs and registry-backed nouns are `SELECT`s, not synthesis — do
them in Python for zero tokens, idempotently, correct on delete/rename. The
reference registry lets Systems and the Role Dictionary become joins too, which
is why they moved here from M5. Reserve agents for genuine prose judgment.

## Changes

New `scripts/aggregate.py`. Imports `doc_model.py`
(manifest + `display_numbers`) and the shared ID logic factored out of
`reconcile.py` (do not duplicate). Reads `manifest.json`, every `role:
procedure` fragment, and `_reference/*.yaml`.

**Python-owned files (one writer each) — full rebuild each run, marker re-emitted:**
- `70_procedure-index.md` (`procedure-index`) — In-Scope index: one row per
  procedure `{[[slug]] token, title, l2 bucket, Direction/Frequency/Owner from
  B. Quick Reference}`, grouped by L2 bucket in taxonomy order.
- `80_role-dictionary.md` (`role-dictionary`) — join from `roles.yaml`
  (role, reports-to, responsibilities) + "Appears In" `[[slug]]` list from each
  procedure's `consult-meta` `roles:` list.
- `81_systems.md` (`systems`) — **registry × usage join**: one row per
  `systems.yaml` entry (canonical name, description, limitations) + a "Related
  Procedures" cell = the `[[slug]]` tokens of procedures whose **`consult-meta`
  `systems:` list** contains that entry's slug. No prose scraping, no alias
  guessing — the slug list is the binding (see README noun-binding contract).
- `88_appendix-a.md` (`appendix-a`) — the Pain Points & Improvement Opportunities
  register, **fully mechanical**: one row per `PP-`/`IO-` callout with
  `{(slug, id), type, observation, impact, severity, Source Procedure [[slug]]}` —
  all fields read straight from the drafter's callout (impact + severity are
  authored there). No judgment agent, no render-join.
- `90_appendix-b-gaps.md` (`gap-log`) / `91_appendix-c-screens.md`
  (`screenshot-index`) — one row per `GAP-` / `SC-`, Source Procedure `[[slug]]`
  column (IDs procedure-local, so the column disambiguates).

**Agent-owned files — placeholder now, M5 fills them:**
- `82_dependencies.md`, `84_raci.md` → heading + marker + `> _Pending synthesis
  (M5)._`. (Each a clean single-writer file. M3 writes only the placeholder.)

**Extract bundle `<area>.extract.json` (scratch, git-ignored)** for M5. Both M5
agents do prose judgment, so the bundle carries the **relevant procedure prose**
(M3 extracts it so the *agents* read the bundle, not the procedure files — and the
orchestrator never touches it):
- `raw_dependencies`: each procedure's `A. Process Overview` text, tagged by slug.
- `raci_inputs`: per procedure, the `B. Quick Reference` **Preparer / Reviewer**
  lines + the `consult-meta` `roles:` slugs + the `E. Step-by-Step` text (owner
  mentions live here). This is **prose + the role slug list**, NOT a
  capacity-classified grid — capacity (who prepares vs reviews vs is informed) is
  the RACI agent's judgment from this prose. (There is no per-step role binding in
  the data; do not pretend one exists.)

**Registry binding (nouns) — read slugs, flag unknowns:** read each procedure's
`consult-meta` `systems:` / `roles:` slug lists and join them to `systems.yaml` /
`roles.yaml`. No prose scraping, no alias matching. A slug not present in the
registry → **WARNING** naming the slug + procedure ("add an entry"); never
dropped, never guessed into a new entry.

**Registry top-up loop (part of the "useful" milestone DoD, not M6):** the
WARNINGs are the human's worklist — add the missing system/role (or an alias) to
`_reference/`, re-run aggregate, until Systems/Roles are complete. This closes the
"registry frozen at confirm" gap in-band (review r3 #7) rather than waiting for
the deferred M6.

**Fail-loud IDs (nonzero exit, nothing dropped):** bare gap tag;
referenced-but-undefined ID; ID prefix not matching its callout label (**new code
owned here**); conflicting duplicate ID **within a procedure** (IDs are
procedure-local — the check is per-procedure, review-scoping-safe). Delimiter
tolerant (`-`/`–`/`—`); ID grammar strict.

**Idempotent:** two runs, no procedure/registry change → byte-identical outputs.

## Implementation notes (as built)

- **Invocation:** `python3 scripts/aggregate.py components/<area>` (accepts the
  area folder or its `manifest.json`). Exit `0` = views rebuilt (WARNINGs
  allowed), `1` = a fail-loud fragment ERROR (nothing written — the run aborts
  *before* any file is emitted so a bad fragment never leaves half-regenerated
  views), `2` = bad usage / unreadable input.
- **Manifest-driven output:** the writer set is read from the manifest's
  `derived` components, not hard-coded — `writer: python` dispatches by
  `derived_kind` to a builder; `writer: agent` gets the pending placeholder. Each
  file is written as `## <heading>` + `<!-- derived: KIND; writer: W -->` + body,
  so it drops straight into `doc_model.assemble` alongside the fragments.
- **Shared ID grammar lives in `aggregate.py`** (`LABEL_TO_PREFIX`,
  `CALLOUT_LINE_RE`, `SUBFIELD_RE`, the strict-ID / tolerant-delimiter regexes,
  `parse_callouts`). Per the README script-layout rule and the M2 ticket,
  **`reconcile.py` should import these** rather than re-implement them (this
  ticket may not edit `reconcile.py`, so the helpers carry an in-code note).
- **Registry loader** tolerates either a `{slug: {...}}` mapping or a
  `[{slug, …}]` list (and an optional top-level `systems:` / `roles:` key), so it
  survives either shape M0 emits.
- **Severity enum** (`High|Medium|Low`) is validated as a **WARNING**, never a
  fail-loud error — only ID-grammar defects abort (per the README's "missing
  optional field parses as blank; only ID-grammar defects fail loud").
- **Idempotency** is guaranteed by deterministic ordering (registry entries
  sorted by slug; back-reference `[[slug]]` lists sorted by manifest `order`;
  procedures grouped by `l2_order` and ordered by `display_numbers`) and a fixed
  JSON serialization (`sort_keys`, trailing newline) for the extract bundle.

## Acceptance

- `70/80/81/88/90/91` are rebuilt (single-writer each) from procedures + registry;
  deleting a procedure removes its rows/usages next run.
- `81_systems.md` shows every `systems.yaml` entry with "Related Procedures"
  back-references derived from `consult-meta` slug lists; a `consult-meta` slug
  absent from the registry raises a WARNING (not dropped). No prose is scraped.
- `80_role-dictionary.md` comes from `roles.yaml`; `84_raci.md` and
  `82_dependencies.md` hold pending placeholders.
- `88_appendix-a.md` rows come only from the `H` section's PP/IO callouts, with
  impact + severity read from the callout (no judgment agent involved).
- Re-running aggregate after a human adds a registry entry clears that entry's
  WARNING (top-up loop works).
- Two procedures each defining a local `CTRL-001` do **not** collide; the
  per-procedure duplicate check still catches a real intra-procedure dup.
- `[[GAP — no id]]` and a `PAIN POINT — CTRL-9` mismatch each cause nonzero exit.
- En-dash vs em-dash delimiter difference does not error.
- Two consecutive runs are byte-identical; no committed scratch files.

## Out of scope

RACI, dependency prose, Appendix-A judgment cells — M5.

> **Contract gap flagged (not fixed here):** the scratch extract bundle
> `<area>.extract.json` is written into the area folder and is meant to be
> **git-ignored** (README ownership table + "scratch, git-ignored"). The
> repo-root `.gitignore` does not yet cover `*.extract.json`; that ignore rule
> belongs to whichever ticket owns `.gitignore` (M0/M2), since this ticket is
> scoped to touch only `aggregate.py` and this file.

## Adversarial review resolutions

- **#5:** In-Scope index python-owned.
- **#2:** derived cross-refs use `[[slug]]` tokens.
- **#8:** systems/roles are registry joins (canonical), not fake-mechanized free
  text; dependencies stay agent prose.
- **#9:** Appendix A observation from callouts only; H not parsed.
- **#10:** python writer re-emits derived + region markers.
- **#14:** label↔prefix check built here; runs before reconcile.
- **#16:** pending-synthesis placeholders in agent files.
- **#17:** tolerant delimiter, strict ID grammar.
- **r3 #1:** ID checks are per-procedure `(slug, local-id)`.
- **r3 #3 / robustness:** nouns bound via the explicit `consult-meta` slug list —
  no prose scraping, no alias matching (kills the fuzziest parser).
- **r3 #5:** split-writer files replaced by one-writer-per-file.
- **r3 refinement:** Appendix A is fully mechanical (drafter authors impact +
  severity in the callouts); no judgment agent, no render-join.
- **r3 #7:** in-band registry top-up loop, not deferred to M6.
- **r3:** Systems + Role Dictionary are registry joins owned here.
