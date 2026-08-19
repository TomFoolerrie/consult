# M53 — Engine housekeeping: the debts the campaign wrote down

**Status: BUILT** (`2.3.0-alpha.4`, gate 8/8, suite 1253 green at
multiple random-order seeds — see Amendment A1). Scheduled by the human
2026-08-18 ("all, in order").
A paired-small-items ticket (the M43 precedent): four recorded debts, each
too small to carry a ticket alone, none licensed to change behavior.

## The items

### Part A — a shared public home for the kind resolvers (M43 A1 item 4)

`analysis.py`'s private resolver helpers (callout-prefix-through-the-type-
declaration, the step-type constant, the callout walk) now have FOUR
consumers: analysis, hygiene, needs, agenda — three of them importing
private `_`-named functions across module lines. They move to one public
home (working name `scripts/kinds.py`; final name at build) with the
consumers repointed. Pure relocation: same functions, same behavior, the
old names surviving as private aliases only if a gate pins an import path.

### Part B — analysis.py's module docstring (M49 A1 item 5)

The docstring predates the `brief` CLI and the fourth generator
(`conflict_records`). Refresh it to the shipped surface — and it shrinks
naturally once Part A moves the resolver prose to the new module's
docstring. Documentation only.

### Part C — the `expand_coverage_statuses` owner and the root helper (M40 A1)

The thin alias expansion (`plan_views._selected_statuses` is the one
expander today) gets a named owner next to Part A's resolvers, and the
area→engagement-root resolution idiom (`_root_of`, reimplemented
module-by-module) is published once from the same home. Consumers
repoint; behavior identical.

### Part D — the pytest-randomly flake

The recorded ordering flake gets root-caused and pinned: either the
offending shared state is fixed, or the dependent tests are marked with
an explicit ordering constraint and a comment naming the coupling.
"Re-run it" stops being the fix.

## Amendment A1 — build friction (recorded at close-out, 2026-08-18)

1. **The flake's real root cause was NOT the m38/m40 tmp collisions**
   (15 dedicated seeds proved those files innocent; M50 A1 item 7's
   attribution was wrong and is corrected there). It was
   `test_shape_audit_m36.py`'s `importlib.reload(client_config)`:
   the reload mints NEW exception classes, and two test modules
   from-import them at collection time, so `pytest.raises` stopped
   matching under any seed ordering the reload first. Fixed by
   snapshotting and restoring the module's original bindings —
   behavior-free, deterministic repro before/after. Seeds 2/3/4
   (previously red) now green.
2. **An `_err` seam preserves each owner's exception class:**
   `kinds.gap_prefix(tdecl, area, _err=...)` lets analysis/hygiene keep
   raising AnalysisError/HygieneError so no catch site changes meaning.
   The refusal wording is now one shared sentence (no test pinned the
   old variants).
3. **kinds.py's import discipline:** matrix_views at module level (no
   loader edge), kernel/definitions lazy inside functions — the
   plan_views cycle note, applied at the new home.
4. **pytest-randomly is not in the environment by default** (it was
   installed to reproduce); the flake was only ever visible with it.
   Recorded: the dev environment should pin it if seeded runs are to
   stay part of verification.
5. hygiene.py dropped six unused private re-imports from analysis that
   the relocation exposed as dead.

## Test impact

New gate: `tests/test_housekeeping_m53.py` — mechanical anchors only (the
public home exists; no consumer imports a private `_` resolver across
modules; the docstring names the CLI and all four generators). Licensed
edits: import-path repoints in existing gates where they grep module
internals, enumerated in the build plan. **Zero v1 tests change; zero
behavior changes** — every part is pinned by the existing suite running
green before and after, plus (for Part D) N seeded-order runs green.

## Acceptance gate

`tests/test_housekeeping_m53.py` green; full suite green under at least
three distinct `-p randomly` seeds recorded in the build plan; grep proves
no cross-module private-resolver imports remain.
