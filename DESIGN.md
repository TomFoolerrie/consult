# DESIGN — the module map

Fourteen TypeScript engine files (src/), one bounded Python worker (py/), the consultant + three worker classes + a two-layer skill library, four kernel files. Under a third of
the oracle's surface after the A9 distillation: every deterministic verb either does bookkeeping an agent shouldn't hand-roll, enforces honesty, or expands context — no workflow lives in the engine. Every rule here is a charter consequence, not a preference.

## The one picture

```
                         THE HUMAN
              questions ↑↓ answers · relayed client info · spend/send calls
                        │
                   THE CONSULTANT  (agents/consultant.md — standing, strong model)
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
     _sources/            ledger.ts owns           sources.yaml, new/, processed/, parked/
     _registers/          asks.ts · findings.ts · desk.ts   asks.yaml, findings.yaml, sessions/ (A15)
     _skills/             brief.ts (saveSkill)     consultant-authored skills (variants logged, reusable)
     _synthesis/          render.ts + workers      work products; registrable as sources (A12)
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
| `_registers/sessions/` | what did the machinery spend? | the machinery (desk.ts) | append-only audit |
| `_sources/` | what came in, and is it accounted for? | ledger.ts | yes — the balance |
| `_synthesis/` | what have we made? | render.ts / workers | registrable as synthesis sources (A12) |
| `_skills/` | what work shapes have we authored? | brief.ts (saveSkill) | yes — resolved into briefs |

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
| `src/kernel.ts` | nothing | type declarations + fragment→entity parsing |
| `src/definitions.ts` | nothing | the deliverable definition language (load, validate, compile) |
| `src/engagement.ts` | nothing | folder truth, flat: locate, entities, taxonomy — capture itself is a direct write (A14) |
| `src/ledger.ts` | `_sources/` | the source ledger, one intake door: route, park, credit, status |
| `src/asks.ts` | `_registers/asks.yaml` | the ask lifecycle; respond() is the one-verb ARRIVAL motion; settle() closes after fold-in (A13) |
| `src/findings.ts` | `_registers/findings.yaml` | the findings register (propose→accept/reject) |
| `src/answers.ts` | nothing (pure) | the question interface: grounded answers with standing |
| `src/views.ts` | nothing (pure) | the view-builder registry; views are computed at render time, never files (R1) |
| `src/check.ts` | nothing | the QC gate: six mechanical checks, no signal files |
| `src/render.ts` | `_synthesis/` | any definition → .docx, refuse-on-placeholder |
| `src/desk.ts` | git + `_registers/sessions/` | the ONE derived picture: state/report, checkpoint, budget, sessionAppend (A15) |
| `src/brief.ts` | `_skills/` | the skill store + composer: resolve (local shadows shipped), saveSkill, compose(name, class, params) |
| `py/render_worker` | `_synthesis/` (via render.ts) | the one Python seam: a bounded docx formatter that never thinks |

## Laws (ported, all live-proven)

- Folder state is the only state; every "where are we" is derived on demand.
- One writer per file. The write boundary is drawn by STORE KIND (A14): machine-parsed bookkeeping (_sources/, _registers/, _skills/) is verb-only; capture/, STATE.md, and OBJECTIVE.md are DIRECT writes — the consultant anywhere, workers within their skill's write boundary — disciplined by check.run, the grammar, and checkpoint diffs.
- Pure reads stay pure: the desk's derived picture and answers write nothing, cache nothing.
- Fail loud: malformed input is a named refusal, never a default.
- No "all quiet" claim reachable by damage: `desk.state` requires positive
  evidence of completeness, and a self-contradictory folder is its own state.
- Humans never type YAML; every gate answer is a verb.
- Cost gates cost, never scope (a thin node waits; it is never silently dropped).
- Adding a deliverable is a YAML-sized act; if it needs an engine change, that is a bug.
- Derived views are never files: computed at render time, in-memory (R1) — a placeholder cannot ship because it cannot be stored.
- Library first: every CLI verb wraps an exported function; the harness drives the library in-process (R5).
- A token spent on judgment lands in a file the machine reads.
- Delegation is economic, not structural: the consultant may do the work itself; a delegate is dispatched when the task's cost warrants it (judged from the objective and the deliverable shape).
- Ask economy is a guiding principle, not a rule: prefer few, simple, artifact-shaped asks — but if the objective needs something, it needs something.
- The engine hard-codes ONE callout kind: the question record (registers join on it). All other capture vocabulary is a shipped, engagement-amendable default; skills bind to declared kinds, never define them.
- No manifest, no areas, no .proposed/, no holds machinery, no signal files: the folder-as-document and human-as-trust-boundary fossils are out (ROT-1..7).
- The assessment license attaches to the activity, not an agent: candidates in, proposals out, whoever judges.
- No workflow lives in the engine (A9): a verb survives only as bookkeeping, honesty enforcement, or context expansion — how-to-work lives in skills. One event, one verb — the event is ARRIVAL (A13): `asks.respond` routes and stamps; settle() closes only after fold-in. Analyses are skills, never engine verbs.
- Agents pin model (+ a fixed tool surface); skills carry the agency. Worker classes (haiku/sonnet/opus) pin nothing else; class and skill are independent dials. Adding a work shape is adding a skill file — shipped (kernel/skills/) or consultant-authored (_skills/, saved before use, logged, reusable).
- Synthesis is citable, never standing-upgrading (A12): a synthesis source declares the grounds it was built from, and statements citing it inherit those grounds' standing — self-derived knowledge is first-class, laundering is structurally impossible.
- Token asymmetry is a design input: input is cheap on strong models, output is dear — review-with-edits over regeneration where it wins.
- The consultant has a workspace: `STATE.md`, its one direct-write file — free prose, never machine-parsed, read first at every sitting, checkpointed with everything else. Working memory persists — and after A9 the pad IS judgment's home (precedent, doubts, observations); the machinery keeps only the session record.

## What is deliberately absent

v1 anything · a second capture type · per-area sources · the thirteen-guard
advisor as the seat of control · the thin-coordinator role · markup review
(kits/xlsx/tracked-changes) · synthesis agents · matrix/agenda/research-pass/
consolidator (return on run demand, ticket-first) · any store beyond the ones
named above.
