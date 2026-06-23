# T50 — Resolve the CSV-transport contradiction (decision required)

**Slice 3 · Wave 3 · Depends: T47 (touches `gap_report.py`), T48 (touches the prose) ·
Touches: `skills/consult-improvement-log/scripts/improvement_log.py`, `scripts/gap_report.py`,
`spec.md`, `README.md`**

## Problem (from review)
The docs say the CSV/Excel transport is **dropped** (spec.md:31-33, :260-262; README:34), but
the register write path still depends on it:
- `improvement_log.py:38` hard-imports `pandas` (this is *why* the e2e fails with no deps);
- `gap_report.py:228` writes a temp CSV to feed the register;
- spec.md:515-517 / :668-669 honestly admit it's not done.

So the spec contradicts itself; §8/§10 is the truth.

## Decision required (pick one — ask the user before building)
- **(A) Make the code match the docs** — remove the pandas/CSV transport: convert
  `improvement_log.py` to JSON-native upsert (no pandas import) and have `gap_report.py` feed
  rows in-process instead of via temp CSV. Drops `pandas` from `requirements.txt`. More work,
  but realizes the documented design and de-flakes the no-deps path.
- **(B) Make the docs match the code** — keep CSV transport; correct spec §1/§4 to state the
  register engine uses an internal CSV/pandas staging step, and remove the "dropped" claim.
  Cheap, honest, but leaves pandas as a hard dependency.

Recommend **(A)** if `pandas` isn't otherwise needed; **(B)** if xlsx rendering already pins
pandas/openpyxl anyway.

## Tests
- Option A: `improvement_log.py` imports without pandas; e2e register assertions pass with
  pandas uninstalled; temp-CSV artifacts no longer created.
- Option B: docs grep clean of the "CSV dropped" claim; e2e unchanged.

## DoD
Code and prose agree; e2e green; decision recorded in the ticket.
