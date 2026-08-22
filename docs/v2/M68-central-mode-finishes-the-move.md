# M68 — Central mode finishes the move: the v1 assumptions that survived M34/M37

**Status: RECORDED** (2026-08-22).
Origin: the Nordhaven build-run audit (2026-08-22), findings F2, F4,
F5, F6 — four places where central mode still behaves as if the area
owned its sources. Grouped because the root cause is one: the M34
detection seam was wired into the loaders, and these consumers never
got the memo.

## Why

1. **The brief flags every tagged source MISSING** (F4, systemic —
   worked around ×14 in one run). `_sources_entries` correctly asks
   the central seam (`brief.py:105–113`) and gets engagement-root-
   relative `file` paths back — and then the reading list joins them
   to the AREA folder (`_reading_item`, `brief.py:129–133`, called at
   `brief.py:725`): `components/procure-to-pay/_sources/new/…` does
   not exist, so every source prints `[MISSING — report it, do not
   guess]`. All 13 drafters and the taxonomist recovered only because
   the dispatch prompts carried the correct path — a workaround
   living in prompts, not in the tool.

2. **Checkpoints never commit the engagement's ledger** (F5, open
   data-loss window). `orchestrate.py checkpoint` stages and commits
   the AREA pathspec only (`orchestrate.py:1488–1498`) — deliberately,
   so unrelated repo work is never swept in. But in central mode the
   run's most valuable state is OUTSIDE the area: `_sources/
   sources.yaml` (every registration and consumption credit), the
   `new/ → processed/` moves, and `components/_client/`. A full run's
   worth of engagement state sat uncommitted in the working tree
   while six area checkpoints landed; the docstring's own promise —
   "a checkpoint that omits the sources can't [revert]" — is broken
   at engagement scope.

3. **The advisor dispatches scoping against an empty ledger** (F2,
   one ~93k-token dispatch spent on remediation). `next` returned
   `taxonomy` because `_sources/new/` was non-empty and no manifest
   existed — but none of the staged files had been `route`d, so the
   taxonomist ran with zero `SRC-` ids, proposed `sources: []`
   everywhere, and a second full dispatch was needed purely to stamp
   ids. Routing is deterministic and free; spending an agent to
   discover it wasn't done is the ladder's mistake, not the agent's.

4. **Two cosmetic honesty items** (F6): `mark-processed` prints
   "moved 0 source(s)" for the correct central-mode case where slugs
   were credited but no source is yet fully consumed — reads as
   failure, audits dirty; and the engagement root gets no seeded
   `.gitignore` (the AREA seeding exists, `orchestrate.py:1439`), so
   `.DS_Store` noise accumulates untracked at engagement level.

## The shape

### Part A — the brief resolves ledger paths at the root

Where `_sources_entries` served the central view, reading-list items
built from a ledger entry's `file` resolve against the CENTRAL ROOT,
not the area (either the view hands back root-resolved paths, or the
brief carries the root alongside the entries — one choice, applied to
every consumer of `entry["file"]` in the file). The `[MISSING]` mark
goes back to meaning missing. The dispatch-prompt path guidance in
the skill retires with the fix.

### Part B — the checkpoint covers what the stage mutated

In central mode, `checkpoint` widens its pathspec to the engagement
state the stages actually write: `<root>/_sources/` (ledger, `new/`,
`processed/`) and `components/_client/` — still a pathspec commit,
still never sweeping unrelated repo work. The engagement root gets
the same seeded `.gitignore` treatment the area gets (covering
`.DS_Store` and friends). v1 areas see zero change.

### Part C — the ladder routes before it scopes

The advisor's `taxonomy` guard checks the central ledger: staged
files in `<root>/_sources/new/` with no ledger entry → the action
tells the orchestrator to run `engagement.py route` for the
enumerated files FIRST (deterministic, zero agents), then dispatch.
Whether that is a distinct `route` action or a precondition folded
into `taxonomy`'s details is the builder's call; the invariant is
that a scoping dispatch never again runs against an empty ledger
while sources sit staged.

### Part D — the messages audit clean

`mark-processed` reports what happened: "credited N slug(s) across M
source(s); K fully consumed and moved" — zero moved stops reading as
failure.

## The gate

- Central-mode brief fixture: every tagged source resolves to an
  existing path; a genuinely absent file still gets `[MISSING]`.
- Central-mode checkpoint test: a stage that registers a source and
  credits a consumption commits the ledger delta; a v1-area
  checkpoint's committed set is byte-identical to today's.
- Advisor fixture: staged-but-unrouted sources → the route-first
  instruction, no taxonomist dispatch; routed sources → `taxonomy`
  as today.
- `mark-processed` message asserted in the credited-but-not-consumed
  case.
- Full suite + compat gate untouched.
