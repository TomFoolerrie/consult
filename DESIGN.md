# DESIGN — the module map

Sixteen TypeScript engine files (src/), one bounded Python worker (py/), the librarian + three worker classes + a two-layer skill library, four kernel files. Roughly a third of
the oracle's surface. Every rule here is a charter consequence, not a preference.

## The one picture

```
                         THE HUMAN
              questions ↑↓ answers · relayed client info · spend/send calls
                        │
                   THE LIBRARIAN  (agents/librarian.md — standing, strong model)
        reads everything · writes only through verbs · works directly or delegates, by cost
                        │
        ┌───────────────┼──────────────────────┐
        │ delegates (by cost) │ verbs (toolbox) │ consults
   worker classes ──────┤                      ├── desk.state()      (where are we)
   (haiku·sonnet·opus   │   src/cli.ts         ├── coverage.status() (what do we know)
    — pin model only) × │   one entry point    ├── needs.standing()  (what's missing)
   skills: shipped      │                      └── answers.ground()  (what's the standing)
   kernel/skills/ +     │
   authored _skills/    │
        ────────────────┴──────────────────────
                     THE FOLDER (the only state)
   engagement/
     STATE.md             the librarian, directly  the state pad: working memory, read first every sitting (A8)
     _sources/            ledger.ts owns           sources.yaml, new/, processed/, parked/
     _registers/          asks.ts, findings.ts     asks.yaml, findings.yaml
     _journal/            journal.ts               flags.yaml, tenure.yaml, sessions/
     _skills/             brief.ts (saveSkill)     librarian-authored skills (variants logged, reusable)
     _exports/            render.ts                rendered .docx
     capture/             engagement.ts owns       fragments + _taxonomy/ — flat, no manifest, no areas
```

## Data flow: the two cycles

(Reduced from four loops per the human's reading: knowledge-in and
answers-out are one motion.)

1. **The brain cycle — input → update → output.** Anything arriving (a
   fresh source, a client's response put back in, a relayed conversation)
   is registered and routed, folded into capture, and checked. Anything leaving (an answer with standing, an
   analysis, a rendered document) is a pure read or a demand-driven render
   over the updated record. Analytical questions are the same motion with
   a license attached: `analysis.feeds` computes candidates, whoever holds
   the license judges them, proposals land in `findings`, the human rules.
2. **The client cycle — the one loop that crosses the client boundary.**
   `needs.standing` says what the pinned shapes lack → the librarian
   curates asks (few, simple, artifact-shaped — see asks.ts's ask economy)
   → human accepts → information request renders → `asks.markSent` →
   responses come back through the same intake door → `asks.match` credits
   them → settle. Continuous through the engagement, not a phase.

## Module inventory (each file carries its full contract)

| Module | Owns / writes | One line |
|---|---|---|
| `src/types.ts` | nothing | the shared vocabulary: lifecycles and standings as discriminated unions |
| `src/cli.ts` | nothing | one entry point, every verb, one parser |
| `src/kernel.ts` | nothing | type declarations + fragment→entity parsing |
| `src/definitions.ts` | nothing | the deliverable definition language (load, validate, compile) |
| `src/engagement.ts` | capture/ skeletons (newFragment) | folder truth, flat: locate, entities, taxonomy — no manifest, no areas, no confirm ceremony |
| `src/ledger.ts` | `_sources/` | the source ledger: register, route, park, credit, answers |
| `src/asks.ts` | `_registers/asks.yaml` | the ask lifecycle + matching |
| `src/findings.ts` | `_registers/findings.yaml` | the findings register (propose→accept/reject) |
| `src/journal.ts` | `_journal/` | flags, tenure, session records — judgment's homes |
| `src/coverage.ts` | nothing (pure) | node status + lens conflicts, recomputed every call |
| `src/needs.ts` | nothing (pure) | what each pinned shape still lacks — standing state as a read |
| `src/answers.ts` | nothing (pure) | the question interface: grounded answers with standing |
| `src/analysis.ts` | nothing (pure) | mechanical candidate feeds for the analyst license |
| `src/views.ts` | nothing (pure) | the view-builder registry; views are computed at render time, never files (R1) |
| `src/check.ts` | nothing | the QC gate: seven capture-quality checks, no signal files |
| `src/render.ts` | `_exports/` | any definition → .docx, refuse-on-placeholder |
| `src/desk.ts` | git + the session budget line | the librarian's desk: state/report, checkpoint, budget — holds are journal commitments, not machinery |
| `src/brief.ts` | `_skills/` | the skill store + composer: resolve (local shadows shipped), saveSkill, compose(name, class, params) |
| `py/render_worker` | `_exports/` (via render.ts) | the one Python seam: a bounded docx formatter that never thinks |

## Laws (ported, all live-proven)

- Folder state is the only state; every "where are we" is derived on demand.
- One writer per file; every write is a verb; agents never touch state directly.
- Pure reads stay pure: coverage, needs, answers, analysis write nothing, cache nothing.
- Fail loud: malformed input is a named refusal, never a default.
- No "all quiet" claim reachable by damage: `desk.state` requires positive
  evidence of completeness, and a self-contradictory folder is its own state.
- Humans never type YAML; every gate answer is a verb.
- Cost gates cost, never scope (a thin node waits; it is never silently dropped).
- Adding a deliverable is a YAML-sized act; if it needs an engine change, that is a bug.
- Derived views are never files: computed at render time, in-memory (R1) — a placeholder cannot ship because it cannot be stored.
- Library first: every CLI verb wraps an exported function; the harness drives the library in-process (R5).
- A token spent on judgment lands in a file the machine reads.
- Delegation is economic, not structural: the librarian may do the work itself; a delegate is dispatched when the task's cost warrants it (judged from the objective and the deliverable shape).
- Ask economy is a guiding principle, not a rule: prefer few, simple, artifact-shaped asks — but if the objective needs something, it needs something.
- The engine hard-codes ONE callout kind: the question record (registers join on it). All other capture vocabulary is a shipped, engagement-amendable default; skills bind to declared kinds, never define them.
- No manifest, no areas, no .proposed/, no holds machinery, no signal files: the folder-as-document and human-as-trust-boundary fossils are out (ROT-1..7).
- The assessment license attaches to the activity, not an agent: candidates in, proposals out, whoever judges.
- Agents pin model; skills carry the agency. Worker classes (haiku/sonnet/opus) pin only the model; class and skill are independent dials. Adding a work shape is adding a skill file — shipped (kernel/skills/) or librarian-authored (_skills/, saved before use, logged, reusable).
- Token asymmetry is a design input: input is cheap on strong models, output is dear — review-with-edits over regeneration where it wins.
- The librarian has a workspace: `STATE.md`, its one direct-write file — free prose, never machine-parsed, read first at every sitting, checkpointed with everything else. Working memory persists; only settled judgments go to the journal stores (A8).

## What is deliberately absent

v1 anything · a second capture type · per-area sources · the thirteen-guard
advisor as the seat of control · the thin-coordinator role · markup review
(kits/xlsx/tracked-changes) · synthesis agents · matrix/agenda/research-pass/
consolidator (return on run demand, ticket-first) · any store beyond the ones
named above.
