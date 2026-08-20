# M64 — Guardrails that guard: the suite and CI stop lying by omission

**Status: RECORDED** (not scheduled).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-16, F-26, F-27, F-29, F-28.

## Why

The suite is real — 1,261 tests, zero failures — but four mechanisms
that are supposed to keep it honest can each go quiet without anything
failing:

1. **Feature-detect skip gates guard sole coverage**
   (`test_research_m47.py:23–33`, `test_table_routing_m54.py:62`,
   `test_analyst_m49.py:47`, `test_wants_m55.py:28`, ~15 modules).
   Whole classes are gated behind conditions that feature-detect the
   code under test — `_has(module, attr)` or an exact substring match
   against a source/skill file. Rename `scaffold.promote_client` (live
   code, sole coverage in ONE gated class) and its tests silently skip;
   `pytest.ini` has no skip budget and nothing FAILS on a skip — the
   count prints in the summary, but no gate guards it and no `-rs`
   surfaces the reasons — so green stays green while coverage
   evaporates.

2. **Unpinned dependencies, no lockfile** (`requirements.txt:1`,
   `tests.yml:16`). CI resolves latest-on-PyPI every run. The suite
   already emits `PytestRemovedIn10Warning` for class-scoped
   instance-method fixtures — the next pytest major will start failing
   collection with no change in the repo.

3. **Assert-nothing tests** (`test_matrix_m38.py:141`).
   `test_controlless_step_renders_without_crash_and_empty_cell`
   asserts only that the rendered string is non-empty — it never
   locates the controlless step or checks the cell. The name documents
   coverage that does not exist.

4. **CI's push trigger names a branch that doesn't exist**
   (`.github/workflows/tests.yml:5`). `branches: [main, mvp]` — no
   `mvp` exists; the active `v2` and `v1.20-stable` are absent. Direct
   pushes to dev branches run no tests (PRs still do).

5. **Stale headline claims** (`README.md:14, 16, 191, 216`).
   "1,199 passing tests" (three places) and "803 v1 tests" — the suite
   is 1,261. A governance-pitched repo quoting wrong evidence counts
   undercuts its own pitch.

## The shape

### Part A — the skip budget

A meta-test (`tests/test_suite_honesty.py`) runs collection-level
accounting: the number of tests deselected by the feature-detect gates
is pinned (expected: ZERO on a healthy tree, since every gated feature
is BUILT). Any gate that starts skipping fails the meta-test naming the
gate — a rename now breaks loudly instead of un-testing a feature.
Where a gate's feature is permanently landed (M47/M49/M54/M55 all
shipped), the gate itself is deleted and the class runs
unconditionally — the simpler fix, preferred wherever the tree allows.

### Part B — pinned resolution

A `constraints.txt` (or full pins in `requirements.txt`) records the
known-good resolution; CI installs with `-c constraints.txt`. The
pytest-10 deprecation (class-scoped instance-method fixtures) is fixed
at the source per the warning's own instruction — `@classmethod`,
attributes on `cls` — so the pin is safety, not life support.

### Part C — the named assertions

The matrix render tests assert what their names promise: locate the
controlless step's row, assert the control cell is empty (and the
sibling assertions the class name implies). One pass over
`TestMatrixRender` for other name/assertion gaps.

### Part D — CI triggers and the README

`tests.yml` push triggers: `[main, v2, v1.20-stable]` (drop `mvp`).
README counts corrected to the collected number — or better, the
brittle literals replaced with "the full suite" plus one authoritative
count in the v2 README that the release checklist owns.

## The gate

- Meta-test: rename any gated symbol on a scratch branch → the
  honesty test fails naming the gate (demonstrated once in the ticket
  close-out, not kept).
- CI run on the pinned resolution is green; `pip check` clean.
- `TestMatrixRender` asserts cell-level facts; mutating the fixture's
  controlless step to carry a control fails the test.
- Workflow triggers match live branches; README counts match
  `pytest --collect-only`.
