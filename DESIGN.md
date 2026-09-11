# DESIGN — the module map

Fourteen TypeScript engine files (src/), one bounded Python worker (py/), the consultant + three worker classes + a two-layer skill library, four kernel files. Under a third of
the oracle's surface after the A9 distillation: every deterministic verb either does bookkeeping an agent shouldn't hand-roll, enforces honesty, or expands context — no workflow lives in the engine. Every rule here is a charter consequence, not a preference.

## The one picture

```
                         THE HUMAN
              questions ↑↓ answers · relayed client info · spend/send calls
                        │
                   THE CONSULTANT  (agents/consultant.md + system.md — standing, strong model)
        reads everything · bookkeeping through verbs, capture directly (A14) · works directly or delegates, by cost
                        │
        ┌───────────────┼──────────────────────┐
        │ delegates (by cost) │ verbs (toolbox) │ consults
   worker classes ──────┤                      ├── desk.state()     (the one derived picture:
   (haiku·sonnet·opus   │   src/cli.ts         │    where are we · coverage · needs)
    — pin model + a   × │   one entry point    └── answers.ground() (what's the standing)
     fixed tool surface)│
   skills: shipped      │
   kernel/skills/ +     │
   authored _skills/    │
        ────────────────┴──────────────────────
                     THE FOLDER (the only state)
   engagement/
     STATE.md             the consultant, directly  the state pad: working memory, read first every sitting (A8)
     OBJECTIVE.md         the consultant, directly  the soft objective: relationship framing, no client facts (A11/A14)
     _sources/            ledger.ts owns           sources.yaml, new/, processed/, parked/, scans/ (A20)
     _registers/          asks.ts · findings.ts · record.ts  asks.yaml, findings.yaml, sessions/ (A15/A18)
     _skills/             brief.ts (saveSkill)     consultant-authored skills (variants logged, reusable) — `consult skill save`
     _definitions/        definitions.ts (pin)     the deliverable shapes this engagement pinned — `consult pin`
     _types/              the consultant, directly the engagement's vocabulary amendments (shadow the shipped type declarations)
     _synthesis/          render.ts + workers      work products + their cards (sidecar or head, A22); registrable as sources (A12)
     capture/             consultant+workers, directly  fragments + _taxonomy/ — flat, no manifest, no areas (A14)
```

## Data flow: the one cycle

(Four loops became two at the first reading; two became ONE at the A10
ruling — the "client cycle" was the brain cycle wearing a costume.)

**input → update → output.** Anything arriving — a fresh source, a
client's response, a relayed conversation — comes through the ONE intake
door (`route`, or `asks.respond` when it answers asks), is folded into
capture, and checked. Anything leaving — an answer with standing, an
analysis, a rendered document, a curated ask — is a pure read or a
demand-driven render over the updated record. The client is one of the
places inputs come from and outputs go to, not a separate loop:
`desk.needs` says what the pinned shapes lack, the consultant curates asks
(few, simple, artifact-shaped), the information request renders, the
response comes back through the same door. Analytical questions are the
same motion with a license attached (analyses are skills, A9).

What made the client path feel separate is not a cycle but a GATE:
anything client-facing crosses the human, as does any spend over the
sitting budget. Gates sit ON the cycle; they are not cycles.

## The stores — each answers one question, once (A11)

| Store | Question it answers | Writer | Machine-parsed? |
|---|---|---|---|
| `STATE.md` | what am I doing? | consultant, directly | never |
| `OBJECTIVE.md` | why are we here? | consultant, directly (A14) | never (quoted into briefs) |
| `capture/` | what do we know? | consultant/workers, directly (A14) | yes — the substrate |
| `_registers/` | where does each transaction stand? | asks.ts / findings.ts | yes — debts computed |
| `_registers/sessions/` | what did the machinery spend, and who said yes at a gate? | the machinery (record.ts) | append-only audit |
| `_sources/` | what came in, and is it accounted for? | ledger.ts | yes — the balance |
| `_synthesis/` | what have we made? | render.ts / workers | registrable as synthesis sources (A12) |
| `_skills/` | what work shapes have we authored? | brief.ts (saveSkill), via `consult skill save` | yes — resolved into briefs |
| `_definitions/` | which deliverable shapes are pinned? | definitions.ts (pin), via `consult pin` | yes — compiled at render; `needs` measures against them |
| `_types/` | which vocabulary has this engagement amended? | the consultant, directly (overlays that shadow the shipped declarations by name) | yes — the grammar parses through them |

Indexing covers four of these stores — `_sources`, `_synthesis`,
`capture`, `_skills`. The rest are not indexed and do not need to be:
the registers are read whole, the prose files are read every sitting,
and the two declaration stores are opened when a shape is touched.

No store answers another's question. Registers hold NO knowledge —
lifecycle bookkeeping only; a register holding synthesized prose is a
second capture, which is a bug. Standings are COMPUTED, never stored:
evidenced (cited to an artifact on file), claimed (no citable
provenance — the line is auditability, not truth), contested (a question
naming two sources), absent (a question no statement answers) — derived
at read time from the record's physical shape.

## Module inventory (each file carries its full contract)

| Module | Owns / writes | One line |
|---|---|---|
| `src/types.ts` | nothing | the shared vocabulary: lifecycles and standings as discriminated unions |
| `src/cli.ts` | nothing | one entry point, every verb, one parser |
| `src/kernel.ts` | nothing | the grammar: type declarations, parsing, entity/taxonomy enumeration (absorbed engagement.ts, A18) |
| `src/definitions.ts` | `_definitions/` | the deliverable definition language (load, validate, compile) + `pin` — the one writer of the pinned-shape store |
| `src/index.ts` | nothing — pure | progressive disclosure (A22): index → card → content; one card schema; indexes computed every call, never stored |
| `src/ledger.ts` | `_sources/` | one intake door: route, park, scan, status — consumption COMPUTED from capture citations (A18); the durable scan is a pointer to _sources/scans/ (A20) |
| `src/asks.ts` | `_registers/asks.yaml` | four stored states (proposed/accepted/sent/closed); answered + settled DERIVED from the record's shape (A18) |
| `src/findings.ts` | `_registers/findings.yaml` | the findings register (propose→accept/reject) |
| `src/answers.ts` | nothing (pure) | the question interface: grounded answers with standing |
| `src/check.ts` | nothing | the QC gate: seven mechanical checks, no signal files |
| `src/render.ts` | `_synthesis/` | any definition → .docx + its card, via the versioned job to the py seam (A23) + the BUILDERS registry (absorbed views.ts, A18); views never files (R1) |
| `src/desk.ts` | nothing (pure) | the ONE derived picture: state/report, coverage, needs, locate — writes nothing, ever (A18) |
| `src/record.ts` | git + `_registers/sessions/` | the machinery's hand: checkpoint, sessionAppend, budget, spend, gate — BOTH gates auditable (A18) |
| `src/brief.ts` | `_skills/` | the skill store + composer: resolve (local shadows shipped), saveSkill (the one writer, behind `consult skill save`), compose(name, class, params) |
| `src/returns.ts` | nothing (mints through findings.ts) | the RETURN door (A27): validate a skill's engine-shaped YAML return, mint its finding proposals, record the return in the session record, print the asks/statements/flags handed to the consultant — refuses malformed by name and mints nothing on refusal |
| `py/render_worker.py` | `_synthesis/` (via render.ts) | the one Python seam, built (A23): a bounded docx formatter that never thinks — job v1 in, {path, sections, warnings} out |

Outside the engine, in the harness: `harness/conformance.ts` — the DYNAMIC
half of the skill contract (A27). It snapshots an engagement, runs a skill
against it, and reports every wall the skill crossed, by path: a write under
`_sources/`, a register or prose pad touched, capture without a declared
`writes: capture-fragment` grant, synthesis outside `_synthesis/<skill>/`, an
uncarded artifact, a source hash that no longer verifies, a missing or
`[HUMAN]`-carrying return, a check error the run introduced. Fixture root:
`harness/fixtures/conformance/`.

## The verbs the stores' writers expose

Every verb wraps one exported function (R5). Beyond the inventory the
CLI docstring lists, four verbs exist specifically because a store needs
exactly one writer, or a damaged tree needs exactly one repair:

| verb | why it exists |
|---|---|
| `consult pin <definition>` | the ONE writer of `_definitions/` — pins a shipped or local shape into the engagement; refuses an unknown name; never overwrites a file already there |
| `consult skill save <file>` | the ONE writer of `_skills/` — validates the skill's shape and logs the save, so a skill is never run from raw prompt text |
| `consult brief <skill> [--class c] [--cards a,b] [--param k=v]…` | dispatch's composer; `--param` is repeatable and carries the skill's own parameters from the CLI |
| `consult return <file>` | the ONE door for what a skill produces (A27) — validates the return, mints its finding proposals, records it in the session record, and HANDS the consultant the asks, statements and flags (it mints no ask and writes no capture) |
| `consult skill check <name>` | the STATIC half of conformance (A27) — manifest valid, ports declared, runtime entry present, no `[HUMAN]`/gate vocabulary in a level-2 runner; the dynamic half is `harness/conformance.ts` |
| `consult init` | the repair verb for an engagement-shaped tree with no `_sources/` marker — creates the skeleton without touching what is already there. Without the marker the engine refuses every verb, reads included, so this is the one way back |

## The skill contract (A27)

A skill sits ON TOP of the engine when it reads through it, writes through
it, and returns through it; a skill that keeps its own knowledge ledger, its
own gates, or its own next-action loop inside the folder sits BESIDE it and
is a second brain. Three ports — READ (index/card/answer + the four `source`
verbs, everything locatable), WRITE (`publishSynthesis` under
`_synthesis/<skill>/<run>/`, with cards; capture fragments only under a
declared grant), RETURN (`consult return <file>`) — and a manifest that
declares them (`contract: v1`, `reads`, `writes`, `returns`, `runtime`).
Conformance is proof, not hope: `consult skill check` statically,
`harness/conformance.ts` dynamically. Deliberately absent: any skill
orchestrator in the engine, and any skill-declared gate — when to run a
skill and what to do with its return is the consultant's judgment, and the
two gates stay the only stops. The full spec is `SKILL-CONTRACT.md`.

## The seven core laws (A16)

1. **The folder is the only state** — everything derived is recomputed, never stored.
2. **Honesty is structural** — standings computed from the record's shape; the audit trail terminates in _sources/; synthesis never upgrades standing.
3. **One writer per file** — bookkeeping through verbs; capture and the prose files directly.
4. **No workflow lives in the engine** — a verb exists only for bookkeeping, honesty, or context expansion; how-to-work lives in skills.
5. **Agents pin model; skills carry the agency** — delegation is economic, not structural.
6. **Two gates only** — spends over the sitting budget, and client-facing sends.
7. **Fail loud** — named refusals; a contradiction is a state; conflicts are recorded, never adjudicated.

Corollaries (all live-proven, none deleted — ranked beneath): derived
views are never files (R1) · library first, every CLI verb wraps an
exported function (R5) · humans never type YAML · cost gates cost,
never scope · adding a deliverable is a YAML-sized act · a token spent
on judgment lands in a file the machine reads · ask economy is a
guiding principle, not a rule · one engine callout kind, the question
record; all other vocabulary is amendable · token asymmetry is a design
input: review-with-edits over regeneration · one event, one verb — the
event is arrival · the state pad persists working memory (A8); the pad
is judgment's home (A9) · no "all quiet" reachable by damage · no
manifest, areas, .proposed/, holds, or signal files (ROT-1..7).

## What is deliberately absent

v1 anything · a second capture type · per-area sources · the thirteen-guard
advisor as the seat of control · the thin-coordinator role · markup review
(kits/xlsx/tracked-changes) · synthesis agents · matrix/agenda/research-pass/
consolidator (return on run demand, ticket-first) · any store beyond the ones
named above.
