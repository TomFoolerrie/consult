# CONSULT v2 — the engagement brain and its consultant

**Current integration work:** [implementation status and consultant-facing examples](IMPLEMENTATION-STATUS.md).

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

## Verified source access (first skill-integration slice)

Skills can now check a registered artifact or retrieve a precise UTF-8 text excerpt:

```sh
consult source verify SRC-001
consult source excerpt SRC-001 --lines 2:5
consult source record SRC-002 --record 7
consult source table SRC-002
```

These return JSON and are read-only. They resolve the source's current ledger
path and verify its full registered SHA-256. Excerpts use positive, inclusive
line ranges; CRLF is normalized for display, and a terminal newline adds no
extra line. Missing/changed files, unsupported text, unsafe paths, and invalid
ranges are named refusals. Binary artifacts can be verified but are not
necessarily line-addressable.

Library entry points: `ledger.verifySource(root, id)` and
`ledger.sourceExcerpt(root, id, { start, end })`. `integrity: sha256-matched`
means byte identity only—not truth, semantic support, computed standing, or
recursive verification of synthesis grounds. Existing `answer` behavior is
unchanged. CSV records are one-based data records after the header, not physical
lines; parsing is strict comma-delimited UTF-8. Assessment has explicit text/CSV
integration in `packages/consult-assessment/`, including immutable analysis
publication with declared input versions. See its
[INTEGRATION.md](packages/consult-assessment/INTEGRATION.md) for supported scope.
Run `npm run demo:assessment` for a scripted fictional example; Python test/demo
dependencies and isolated-environment setup are documented in
[IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md).

Design and progress: [skill contract](SKILL-CONTRACT.md),
[assessment integration](ASSESSMENT-INTEGRATION.md), and
[evidence bridge](EVIDENCE-BRIDGE.md).

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
