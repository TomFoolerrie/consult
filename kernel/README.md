# kernel — the declarative half

Three directories ship, all ported from the oracle at build time with v1
residue removed (no aliases, no activity type): `types/`, `deliverables/`,
`skills/`.

## types/ — the capture grammar, as the YAML actually declares it

`types/process-step.yaml` — the capture substrate.

```
parts     body — "What happens", kind: prose        (ONE part)
callouts  question  QUESTION       prefix Q   → questions
          control   CONTROL        prefix C   → callouts
          pain      PAIN POINT     prefix P   → callouts
          io        INPUT/OUTPUT   prefix IO  → callouts, fields: direction, artifact
channels  statements · questions
```

`types/taxonomy-node.yaml` — one part (`scope`, prose), the QUESTION
callout only, the same two channels. A question naming two sources IS
the lens-conflict record, so the node needs no separate conflict shape.

The engine hard-codes exactly ONE callout kind: `question` — the
registers join on it. Everything else above is SHIPPED DEFAULT
vocabulary, declared here and amendable per engagement: a
`<root>/_types/<name>.yaml` shadows the shipped declaration by name.
Skills bind to declared kinds; they never define schema. There is no
SCREENSHOT PLACEHOLDER and there are no aliases.

## deliverables/ — the two shipped shapes

```
information-request.yaml   the ask loop's front door — curated asks lead,
                           mechanical feeds as appendix
findings-report.yaml       accepted findings by theme
```

Neither is auto-pinned. An engagement pins the shapes it wants with
`consult pin <name>`, which writes `<root>/_definitions/<name>.yaml`; a
local definition of the same name shadows the shipped one.

## skills/ — the eight shipped work shapes

| skill | writes | recommended class |
|---|---|---|
| `intake-scan` | nothing — the report is returned and landed by `consult scan` | haiku |
| `source-read` | nothing | haiku |
| `procedure-draft` | its one capture fragment | sonnet |
| `data-wrangle` | `_synthesis/` — one canonical dataset + its lineage note | sonnet |
| `data-analysis` | nothing | sonnet |
| `interview-guide` | `_synthesis/` — one markdown agenda | sonnet |
| `narrative-draft` | `_synthesis/` — one markdown document | sonnet |
| `assessment` | nothing — proposals are returned | opus |

Each declares mission, write boundary (`writes`), context contract,
return contract, rules, and a RECOMMENDED class — advisory: the
consultant may override with a recorded reason, because class and skill
are two independent dials.

Engagement-authored skills live in `<root>/_skills/` and shadow shipped
ones by name. The consultant authors them ad-hoc and saves them with
`consult skill save <file>` before use — always saved, logged, reusable.
A capture template is not new machinery: a capture shape IS a skill, a
`procedure-draft` variant authored per engagement.

## Why analyses are not verbs

Analyses are skills, not engine verbs (A9): the four analysis lenses the
old engine hard-coded (pain-synthesis, control-coverage, conflict-support,
handoff-friction) live as lenses of the `assessment` skill; their feed
selection is plain retrieval through `answers.ground`. A new kind of
analysis is a new skill — never an engine change.

The definition language's rule set lives in `src/definitions.ts`.
Adding a deliverable = adding a YAML file here (plus at most one view
builder) — the charter property this directory exists to demonstrate.
