# DESIGN — the module map

Sixteen engine modules, four agent contracts, four kernel files. Roughly a third of
the oracle's surface. Every rule here is a charter consequence, not a preference.

## The one picture

```
                         THE HUMAN
              questions ↑↓ answers · relayed client info · spend/send calls
                        │
                   THE LIBRARIAN  (agents/librarian.md — standing, strong model)
        reads everything · writes only through verbs · delegates to cheap models
                        │
        ┌───────────────┼──────────────────────┐
        │ delegates     │ verbs (the toolbox)  │ consults
   agents/drafter  ─────┤                      ├── desk.state()      (where are we)
   agents/analyst  ─────┤   consult/cli.py     ├── coverage.map()    (what do we know)
   agents/reader   ─────┤   one entry point    ├── needs.standing()  (what's missing)
                        │                      └── answers.ground()  (what's the standing)
        ────────────────┴──────────────────────
                     THE FOLDER (the only state)
   engagement/
     _sources/            ledger.py owns          sources.yaml, new/, processed/, parked/
     _registers/          asks.py, findings.py    asks.yaml, findings.yaml
     _journal/            journal.py              flags.yaml, tenure.yaml, sessions/
     _client/             desk.py (hold verb)     understanding.md, consult.yaml, registers/
     _exports/            render.py               rendered .docx
     components/<area>/   engagement.py owns      manifest.json, fragments, _taxonomy/
```

## Data flow: the four loops

1. **The knowledge loop** — a source arrives (dropped by the human, or a client
   response put back in) → `ledger.register` → librarian routes it → a `reader`
   or `drafter` dispatch folds it into fragments → `views.aggregate` refreshes
   derived views → `check.run` gates quality. Coverage and answers are pure reads
   over the result; nothing is cached.
2. **The question loop** — the human asks → `answers.ground` assembles the
   grounded answer (evidenced / claimed / contested / absent) from capture +
   coverage + registers → an *absent* or *thin* answer proposes the ask or the
   cheap read that would close it.
3. **The engagement loop** — `needs.standing` says what the objective's shapes
   still lack → librarian curates asks (`asks.propose`) → human accepts → the
   information request renders on demand → answers come back as source drops →
   `asks.match` credits them. Continuous, not a phase.
4. **The analysis loop** — an analytical question → `analysis.feeds` computes
   candidates mechanically → `analyst` judges them (propose-only license) →
   `findings` register → human accepts/rejects in conversation → accepted
   findings are citable and renderable.

## Module inventory (each file carries its full contract)

| Module | Owns / writes | One line |
|---|---|---|
| `consult/cli.py` | nothing | one entry point, every verb, one parser, floor check |
| `consult/kernel.py` | nothing | type declarations + fragment→entity parsing |
| `consult/definitions.py` | nothing | the deliverable definition language (load, validate, compile) |
| `consult/engagement.py` | manifest, fragments (scaffold only) | folder truth: paths, manifest, entity load, scaffold |
| `consult/ledger.py` | `_sources/` | the source ledger: register, route, park, credit, answers |
| `consult/asks.py` | `_registers/asks.yaml` | the ask lifecycle + matching |
| `consult/findings.py` | `_registers/findings.yaml` | the findings register (propose→accept/reject) |
| `consult/journal.py` | `_journal/` | flags, tenure, session records — judgment's homes |
| `consult/coverage.py` | nothing (pure) | node status + lens conflicts, recomputed every call |
| `consult/needs.py` | nothing (pure) | what each pinned shape still lacks — standing state as a read |
| `consult/answers.py` | nothing (pure) | the question interface: grounded answers with standing |
| `consult/analysis.py` | nothing (pure) | mechanical candidate feeds for the analyst license |
| `consult/views.py` | derived view files | aggregate: rebuild every python-owned view |
| `consult/check.py` | signal file | the QC gate (the oracle's reconcile, distilled) |
| `consult/render.py` | `_exports/` | any definition → .docx, refuse-on-placeholder |
| `consult/desk.py` | `consult.yaml` hold block, git | the librarian's desk: state, checkpoint, hold, budget |
| `consult/brief.py` | nothing | deterministic work orders for every dispatch |

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
- A token spent on judgment lands in a file the machine reads.

## What is deliberately absent

v1 anything · a second capture type · per-area sources · the thirteen-guard
advisor as the seat of control · the thin-coordinator role · markup review
(kits/xlsx/tracked-changes) · synthesis agents · matrix/agenda/research-pass/
consolidator (return on run demand, ticket-first) · any store beyond the ones
named above.
