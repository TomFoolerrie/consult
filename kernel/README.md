# kernel — the declarative half (MOCK-OUT)

Four files ship, all ported from the oracle at build time with v1 residue
removed (no aliases, no activity type):

```
types/process-step.yaml          the capture substrate: scope / inputs /
                                 transformation / outputs / controls / issues.
                                 Callouts: the engine-required QUESTION record,
                                 plus shipped DEFAULT vocabulary (CONTROL with
                                 Performer/Comparison/Trigger/Evidence, PAIN
                                 POINT, IMPROVEMENT OPPORTUNITY) — amendable
                                 per engagement; skills bind to declared kinds.
                                 No SCREENSHOT PLACEHOLDER; no aliases.
types/taxonomy-node.yaml         one part (scope), the question record only
                                 (a question naming two sources IS the
                                 lens-conflict record)
deliverables/information-request.yaml   the ask loop's front door — curated
                                 asks lead, mechanical feeds as appendix
deliverables/findings-report.yaml       accepted findings by theme
```

A fourth directory joins at build time: `skills/` — the SHIPPED work
shapes (procedure-draft, source-read, assessment, data-analysis,
data-clean), each
declaring mission, write boundary, context contract, return contract,
rules, and a recommended worker class. Engagement-authored skills live
in `<root>/_skills/` and shadow shipped ones by name — the consultant
authors them ad-hoc (always saved before use, logged, reusable).

Analyses are skills, not engine verbs (A9): the four analysis lenses the
old engine hard-coded (pain-synthesis, control-coverage, conflict-support,
handoff-friction) live as lenses of the `assessment` skill; their feed
selection is plain retrieval through `answers.ground`. A new kind of
analysis is a new skill — never an engine change.

The definition language's rule set lives in `src/definitions.ts`.
Adding a deliverable = adding a YAML file here (plus at most one view
builder) — the charter property this directory exists to demonstrate.
