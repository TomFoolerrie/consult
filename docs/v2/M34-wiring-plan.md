# M34 consumer-wiring build plan — central mode behind one seam

> Second build of [`M34-centralized-sources.md`](M34-centralized-sources.md).
> Gate: `tests/test_central_mode_m34.py` (skips until `ledger.assess`
> exists). Ground rules as ever ([`M33-build-plan.md`](M33-build-plan.md)):
> branch `v2`, full suite green to finish, one writer per file, frozen
> fixtures read-only, escalate friction verbatim, NEVER edit existing
> tests.
>
> Grounding: the consumer map produced by reconnaissance (2026-08-15) —
> every per-area source read/write site in the engine, its tests, and
> its central-mode judgment. Key findings honored here: guard 5 asks a
> third question the ledger didn't answer (added as `ledger.assess`);
> four v1 entry points lack direct tests (characterized FIRST, WP-W0);
> reconcile needs NO change (central citations are plain engagement-
> global `SRC-nnn`; prefixed ids exist only in the read-only adapter).

## The design rule

**One detection seam.** `sources.central_root(folder) -> root|None` walks
up from an area looking for `_sources/sources.yaml`. Everything else asks
that seam and branches once: v1 path (byte-identical behavior — the 844
tests are the proof) or ledger delegation. No consumer may test file
positions to decide mode, and no consumer other than `sources.py` and
`engagement.py` may import `ledger` directly — orchestrate/brief/scaffold
stay downstream of the v1 signatures they already call.

## Deferred out of this build (recorded)

- **Skill/agent prose** (consult-orchestrate SKILL.md ~15 sites,
  consult-taxonomy + consult-intake + consult-drafter briefs): the
  taxonomy and intake briefs are REPLACED WHOLESALE by M37 (surveyor/
  librarian), so rewriting them for central mode now is double work.
  Until M37, central mode is engine-complete but not agent-driven —
  acceptable because no live engagement is central yet.
- Register-provenance remap consumption (`registers.py` prose strings).
- The two parked WP-B decisions (touches-shrink pruning; nested staging
  paths) — unchanged this build.

## Work packages

### WP-W0 — characterization tests (parallel with W1; owns NEW test files only)
`tests/test_v1_source_characterization.py`: pin CURRENT v1 behavior of
the four untested entry points — `sources.assess_new_sources` (hash
partition, ambiguous-basename fallback, no-hash=unassessed),
`sources.registered_ids` (absent/unreadable -> set()),
`scaffold.write_promoted_notes` (processed-skip, consumed dedupe,
skeleton classification), `engagement.intake_status` (+
`reconcile.check_src_citations` skip-when-empty posture). Must pass
against v1 AS IT IS — these are tripwires for W1-W3, not targets.

### WP-W1 — ledger.assess + area_view + the sources.py seam
Owns `scripts/ledger.py` + `scripts/sources.py`.
- `ledger.assess(root)` — the guard-5 question at engagement scope:
  partition `_sources/new/` files into (unassessed names, assessed
  entries) by the v1 rules (no hash recorded -> unassessed; hash
  mismatch -> unassessed; match -> assessed). Sorted, sidecar/dotfile
  exclusions as in `_new_file_names`.
- `ledger.area_view(root, area)` — the v1-shaped slice: entries touching
  the area with FLAT area-local `touches`/`consumed` lists (plus id,
  file, note, hash, state derived). This is what re-pointed consumers
  format — brief's listing stays byte-shaped.
- `sources.central_root(folder)`; central branches inside
  `registered_ids`, `assess_new_sources`, `mark_processed` (delegates to
  `ledger.credit` with the same filled/updated sets, returns 0/1 in the
  CLI posture). v1 branches byte-identical.
Targets: gate classes TestDetection, TestAssess, TestAreaView,
TestSourcesModule (+ WP-W0 tripwires + full suite).

### WP-W2 — orchestrate + brief (after W1; owns those two files)
- `orchestrate.py`: `State.sources_new` and the `_dir_has_files`
  pre-checks become central-aware (the ROOT `_sources/new/` is the
  staging dir in central mode); guard 5/5a and guard 3 then flow through
  `sources.assess_new_sources` unchanged. Guard-5a human_action text
  gains the central-mode phrasing only when in central mode.
- `brief.py`: `_sources_entries` asks the seam -> `ledger.area_view`;
  `REGISTRY_FILES` drops `sources.yaml` only in central mode (v1 tuple
  untouched).
Targets: TestBrief + full suite (the m6/orchestrate suites are the v1
regression proof).

### WP-W3 — engagement + scaffold (after W1; owns those two files; parallel with W2)
- `engagement.py`: in central mode `route` = `ledger.register` with
  area-level tags (`{area: []}`) + pointers folded into the entry note —
  no copies, no sidecars, file stays in root `_sources/new/`; `park` =
  `ledger.park`; `_intake_context` accepts the root `_sources/new/` as
  the drop point; `adopt` mints through `ledger.register` (one minter).
  v1 `intake/` flow untouched.
- `scaffold.py`: central mode — `stamp_sources` becomes a no-op with a
  stated reason (hashes stamped at registration); the sources half of
  the promote map skipped (taxonomy refines TAGS via a ledger touches
  update, not a registry merge — implement the minimal
  `ledger.retag(root, id, area, slugs)` if the promote path needs it,
  document it); `write_promoted_notes` + `known_src_ids` read
  `ledger.area_view`. v1 branches byte-identical. Author NEW tests for
  your central-mode scaffold behavior (test_central_scaffold_m34.py) —
  WP-W0 pins the v1 side.
Targets: TestIntakeVerbs + your own scaffold tests + full suite.

## Sequencing

WP-W0 ∥ WP-W1 → {WP-W2 ∥ WP-W3} → orchestrator integration (suite,
close-out, alpha.4). Every package ends with `python3 -m pytest -q`
fully green except gate classes owned by a LATER package (report their
exact failures).
