# CONSULT v2 — the engagement brain and its consultant

**Status: BUILT — the executable spec is green; see `npm test` for the count.**
Every module carries its contract as a docstring and its behavior in tests/
(written first, per the method). The suite count moves with every amendment, so
it is not repeated here — CHARTER.md records the count at each amendment, and
`npm test` is the live answer.
The docx seam is built (A23): `render` compiles, validates, builds views, assembles
a versioned job, and hands it to py/render_worker.py — the one Python file — which
formats the .docx and nothing else; the card lands beside it.

The ruled charter is `CHARTER.md`. The module map and data flow are `DESIGN.md`.
The old engine (shipped as 2.0–2.5.1, retroactively the v1 line's final form) lives on
the other branches of this repository and serves as the oracle: when a behavior
question comes up, its behavior is the spec until the human rules otherwise.

## The idea in three sentences

The brain captures what is known about a client's processes as typed, evidenced
records, and always knows the standing of every statement: evidenced, claimed,
contested, or absent. A standing agent — the consultant — stewards that record: routes
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
SKILL-CONTRACT.md     the skill contract (A27): three ports, one return door, the v1 manifest, conformance
src/                  the engine — TypeScript, one entry point (`consult <verb>`)
py/                   the one Python seam: the bounded docx render worker
agents/               consultant + worker contracts, and system.md — the mental model the consultant loads every sitting
kernel/               the declarative half: 2 types, 2 deliverable definitions, 8 shipped skills
synthetic/            the synthetic engagements (the definition of done); #4 is the live-model run — see its RUNBOOK
harness/              the layer between the engine and the models: install.ts (the consultant seat + worker classes into a folder), client.ts (the scripted client)
bin/consult           the engine on PATH
tests/                the executable spec — written BEFORE the build (red until each module lands); the fixtures pin the on-disk grammar
```

An ENGAGEMENT folder — what `harness/install.ts` creates and the engine
reads — is a different tree:

```
STATE.md        OBJECTIVE.md        the two prose files, written directly
_sources/       route · park · scan · retirement at checkpoint   (new/ processed/ parked/ scans/)
_registers/     ask · finding · the machinery (asks.yaml, findings.yaml, sessions/)
capture/        the consultant and skill-licensed workers, directly (+ _taxonomy/)
_synthesis/     render and workers — work products and their cards
_skills/        consult skill save
_definitions/   consult pin
_types/         the consultant, directly — vocabulary amendments
```

## The start (picked pieces, build order)

Nothing below is excavated from v1 — this is the picked list, and the picked
list is the whole system.

**Phase 1 — the brain minimum** (ends with synthetic engagement #1):
`types` → `kernel` (grammar + enumeration) → `ledger` → `asks` →
`answers` → `desk` (pure derived picture) + `record` (checkpoint,
budget, gates) + `cli`.
At the end of phase 1 you can: drop sources, route them, capture, ask,
put responses back, and ask the brain questions with honest standings.

**Phase 2 — shapes and analysis**: `definitions` → `check` →
`render` (+ py worker) → `findings` → skills store (analyses ship as
skills — the engine has no analysis verbs, A9).
At the end of phase 2 the two shipped definitions render on demand and the
analysis license runs. Then synthetics #2 and #3, and the D8 analysis.
