# DESIGN — the module map

Sixteen TypeScript engine files (src/), one bounded Python worker (py/), four agent contracts, four kernel files. Roughly a third of
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
   agents/drafter  ─────┤                      ├── desk.state()      (where are we)
   agents/analyst  ─────┤   src/cli.ts         ├── coverage.status() (what do we know)
   agents/reader   ─────┤   one entry point    ├── needs.standing()  (what's missing)
                        │                      └── answers.ground()  (what's the standing)
        ────────────────┴──────────────────────
                     THE FOLDER (the only state)
   engagement/
     _sources/            ledger.ts owns          sources.yaml, new/, processed/, parked/
     _registers/          asks.ts, findings.ts    asks.yaml, findings.yaml
     _journal/            journal.ts              flags.yaml, tenure.yaml, sessions/
     _client/             desk.ts (hold verb)     understanding.md, consult.yaml, registers/
     _exports/            render.ts               rendered .docx
     components/<area>/   engagement.ts owns      manifest.json, fragments, _taxonomy/
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
| `src/engagement.ts` | manifest, fragments (scaffold only) | folder truth: paths, manifest, entity load, scaffold |
| `src/ledger.ts` | `_sources/` | the source ledger: register, route, park, credit, answers |
| `src/asks.ts` | `_registers/asks.yaml` | the ask lifecycle + matching |
| `src/findings.ts` | `_registers/findings.yaml` | the findings register (propose→accept/reject) |
| `src/journal.ts` | `_journal/` | flags, tenure, session records — judgment's homes |
| `src/coverage.ts` | nothing (pure) | node status + lens conflicts, recomputed every call |
| `src/needs.ts` | nothing (pure) | what each pinned shape still lacks — standing state as a read |
| `src/answers.ts` | nothing (pure) | the question interface: grounded answers with standing |
| `src/analysis.ts` | nothing (pure) | mechanical candidate feeds for the analyst license |
| `src/views.ts` | nothing (pure) | the view-builder registry; views are computed at render time, never files (R1) |
| `src/check.ts` | signal file | the QC gate: eight capture-quality checks (R3) |
| `src/render.ts` | `_exports/` | any definition → .docx, refuse-on-placeholder |
| `src/desk.ts` | `consult.yaml` hold block, git | the librarian's desk: state, checkpoint, hold, budget |
| `src/brief.ts` | nothing | work orders for delegates only; the librarian's picture is desk.report (R2) |
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
- Asks are few, simple, and artifact-shaped: one good artifact request closes many gaps; clients do not answer question lists.
- The assessment license attaches to the activity, not an agent: candidates in, proposals out, whoever judges.

## What is deliberately absent

v1 anything · a second capture type · per-area sources · the thirteen-guard
advisor as the seat of control · the thin-coordinator role · markup review
(kits/xlsx/tracked-changes) · synthesis agents · matrix/agenda/research-pass/
consolidator (return on run demand, ticket-first) · any store beyond the ones
named above.
