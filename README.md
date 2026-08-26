# CONSULT v2 — the engagement brain and its librarian

**Status: MOCK-OUT.** Every module exists as a contract — a docstring that says what it
owns, what it writes, and what it refuses — with signatures and no implementations.
Nothing here runs yet. The point of this stage is that a human can read this tree in
one sitting and know how the code works before any of it is written.

The ruled charter is `CHARTER.md`. The module map and data flow are `DESIGN.md`.
The old engine (shipped as 2.0–2.5.1, retroactively the v1 line's final form) lives on
the other branches of this repository and serves as the oracle: when a behavior
question comes up, its behavior is the spec until the human rules otherwise.

## The idea in three sentences

The brain captures what is known about a client's processes as typed, evidenced
records, and always knows the standing of every statement: evidenced, claimed,
contested, or absent. A standing agent — the librarian — stewards that record: routes
sources, curates the taxonomy, generates client engagement (asks) throughout the
engagement, keeps its own working memory in a state pad (`STATE.md`) so nothing
mid-flight dies between sittings, and does the work itself or delegates it to
cheaper models — a cost decision, not a structural one. The human talks to the
client, relays what they learned, asks the brain questions, and makes exactly two
kinds of calls: what to spend and what to send.

## Layout

```
CHARTER.md            the ruled charter (Amendment A1)
DESIGN.md             module map, data flow, who-writes-what
src/                  the engine — TypeScript, one entry point (`consult <verb>`)
py/                   the one Python seam: the bounded docx render worker
agents/               two contracts: librarian + worker classes (skills in kernel/skills/)
kernel/               the declarative half: 2 types, 2 deliverable definitions
synthetic/            the synthetic-engagement harness (the definition of done)
tests/                (arrives with implementation — tests-first, per module)

## The start (picked pieces, build order)

Nothing below is excavated from v1 — this is the picked list, and the picked
list is the whole system.

**Phase 1 — the brain minimum** (ends with synthetic engagement #1):
`types` → `kernel` (parse) → `engagement` (flat capture) → `ledger` →
`asks` → `journal` → `coverage` → `answers` → minimal `desk` + `cli`.
At the end of phase 1 you can: drop sources, route them, capture, ask,
put responses back, and ask the brain questions with honest standings.

**Phase 2 — shapes and analysis**: `definitions` → `views` → `check` →
`render` (+ py worker) → `needs` → `analysis` → `findings` → skills store.
At the end of phase 2 the two shipped definitions render on demand and the
analysis license runs. Then synthetics #2 and #3, and the D8 analysis.

```
