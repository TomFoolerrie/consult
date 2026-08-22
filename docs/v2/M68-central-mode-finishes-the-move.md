# M68 — Central mode finishes the move: the v1 assumptions that survived M34/M37

**Status: BUILT** (`2.4.0-alpha.3`, gate 13/13 — see Amendment A1).
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
   "a checkpoint that omits the sources can't restore the
   engagement" — is broken
   at engagement scope.

3. **The advisor dispatches scoping against an empty ledger** (F2,
   one ~93k-token dispatch spent on remediation). Guard 3 is
   file-presence only — `if not st.has_manifest and
   _dir_has_files(st.sources_new)` (`orchestrate.py:919–921`) — with
   no ledger-entry check, so `next` returned `taxonomy` while none of
   the staged files had been `route`d: the taxonomist ran with zero
   `SRC-` ids, proposed `sources: []` everywhere, and a second full
   dispatch was needed purely to stamp ids. Spending an agent to
   discover routing wasn't done is the ladder's mistake, not the
   agent's. (Precision, per review: routing is NOT free in general —
   `route` requires `--to <area>` and refuses without it
   (`engagement.py:926–928`), and the target is a classification
   decision. It was free in THIS run only because a single-area
   engagement makes the target trivial.)

4. **Two message/hygiene items** (F6): `mark-processed` prints
   "moved N source(s) → processed" (`sources.py:361`) for the correct
   central-mode case where slugs were credited but no source is yet
   fully consumed — "moved 0" reads as failure, audits dirty; and the
   engagement root gets no seeded `.gitignore` (the AREA seeding
   exists, `orchestrate.py:1483–1486`), so `.DS_Store` noise
   accumulates untracked at engagement level. Adjacent and worse than
   cosmetic: the skill TELLS the user checkpoints include `_sources/`
   ("client material" — the stated reason the repo must be private,
   SKILL.md:251) and the checkpoint docstring says "`_sources/` IS
   committed on purpose … a checkpoint that omits the sources can't
   restore the engagement" (`orchestrate.py:1466–1469`) — both FALSE
   in central mode, which is item 2's bug stated as a promise in two
   places.

## The shape

### Part A — the brief resolves ledger paths at the root

Where `_sources_entries` served the central view, reading-list items
built from a ledger entry's `file` resolve against the CENTRAL ROOT,
not the area (either the view hands back root-resolved paths, or the
brief carries the root alongside the entries — one choice, applied to
every consumer of `entry["file"]`). The known consumers are
`brief.py:725` AND `agenda.py:505` — the agenda renders the same
root-relative path bare into the client ask-list; the fix covers
both, and the builder sweeps for others. The `[MISSING]` mark goes
back to meaning missing. The dispatch-prompt path guidance in the
skill retires with the fix (sequencing note: M67 Part C edits the
same skill prose — whichever builds second rebases on the first).

### Part B — the checkpoint covers what the stage mutated

In central mode, `checkpoint` widens its pathspec to the engagement
state the stages actually write: `<root>/_sources/` (ledger, `new/`,
`processed/`) and `components/_client/` — still a pathspec commit,
still never sweeping unrelated repo work. Build constraints, per
review:

- **All three git calls widen together** — `add` (`orchestrate.py:
  1488`), the staged-diff emptiness check (1492), and `commit`
  (1498) each carry their own `-- .`; widening only the add while
  the diff check stays narrow yields "nothing to commit" with
  engagement state silently staged. One pathspec list, used by all
  three.
- **One-writer, stated:** two areas checkpointing will both commit
  the shared `_sources/` and `_client/`. That is acceptable — a
  checkpoint commits whatever ITS stage mutated, and git serializes
  the commits — but the ruling is recorded here so the doctrine
  audit doesn't read it as a violation: the STAGES remain
  one-writer; the checkpoint is a recorder, not a writer.
- **The false promise retires:** SKILL.md:251 and the checkpoint
  docstring (`orchestrate.py:1466–1469`) currently promise that
  sources are committed; the fix makes the promise true and the
  gate asserts on it.

The engagement root gets the same seeded `.gitignore` treatment the
area gets (covering `.DS_Store` and friends). v1 areas see zero
change.

### Part C — the ladder routes before it scopes

The advisor's `taxonomy` guard checks the central ledger: staged
files in `<root>/_sources/new/` with no ledger entry are surfaced
BEFORE a scoping dispatch spends an agent. Three constraints from
review shape the fix:

- **Routing needs a target, and the advisor is per-area.**
  `_sources/new/` is engagement-wide while `next --area` is not — a
  blanket "route the enumerated files to THIS area" would misroute a
  file staged for a sibling area. Where the engagement has exactly
  one area the instruction can name it; otherwise the unrouted set
  is a HUMAN GATE (the classification is the human's or intake's,
  never a default), listing the files and the `route --to` command
  shape.
- **Central-mode-scoped, explicitly.** v1 doctrine holds that an
  unregistered source in `_sources/new/` IS genuine taxonomy work
  (pinned by `tests/test_m6_reassessment.py:494–499` — v1 registers
  via proposals at the confirm gate). This part deliberately
  overturns that for CENTRAL mode only, where sources enter through
  `route`/`adopt` and a scoping dispatch without ids is wasted
  spend; the guard keys off the central seam so the v1 test stands
  untouched.
- The invariant: a scoping dispatch never again runs against an
  empty ledger while sources sit staged.

### Part D — the messages audit clean

`mark-processed` reports what happened: "credited N slug(s) across M
source(s); K fully consumed and moved" — zero moved stops reading as
failure. Not cosmetic, per review: `ledger.credit` returns only the
moved count as an `int` (`ledger.py:630`), a contract pinned by six
assertions in `tests/test_ledger_m34.py`. The builder either widens
the return (touching `sources.mark_processed` and those tests,
knowingly) or keeps the `int` and exposes the credited counts
through a second read — a real API decision, chosen at build time,
not discovered mid-edit.

## The gate

- Central-mode brief fixture: every tagged source resolves to an
  existing path; a genuinely absent file still gets `[MISSING]`.
- Central-mode checkpoint test: a stage that registers a source and
  credits a consumption commits the ledger delta; a v1-area
  checkpoint's committed set is byte-identical to today's.
- Advisor fixture: central mode, staged-but-unrouted sources → the
  route-first instruction (single-area) or the human gate
  (multi-area), no taxonomist dispatch; routed sources → `taxonomy`
  as today; the v1 fixture of `test_m6_reassessment.py:494` still
  passes unmodified.
- The skill and docstring no longer promise what central mode
  doesn't do: both updated with Part B and asserted where testable.
- `mark-processed` message asserted in the credited-but-not-consumed
  case.
- Full suite + compat gate untouched.

## Amendment A1 — build rulings (2026-08-22)

* Part A landed as a brief-side seam (`_sources_base()`), not a view
  change: `_sources_entries`' return shape is pinned by two existing
  tests, and scaffold/hygiene want `area_view`'s `file` root-relative
  as it is. `agenda._owed` joins against the engagement root.
* Part C landed as a distinct `route` action: single-area →
  `human_gate: false` with the exact commands; multi-area → human
  gate with the file list and command shape. Classified into
  `GATE_ACTIONS` (the completeness invariant in `test_sticky_holds`
  requires every action classified — unanticipated by the ticket).
  `tests/test_dispatch_hints_m37.py`'s central factory staged a file
  with an empty ledger — exactly the F2 state this part overturns —
  so the factory now routes its entry; no assertion changed.
* Part B: `git -C <area>` kept, pathspecs relative to the area
  (`.`, `../../_sources`, `../../components/_client`,
  `../../.gitignore`), one list reused by add/diff/commit; engagement
  `.gitignore` seeded once and itself committed; docstring and
  SKILL.md promise corrected for both modes.
* Part D: `ledger.credit` NOT widened — `mark_processed` diffs
  `area_view` before/after for the credited counts; the six
  `test_ledger_m34` assertions stand untouched.
