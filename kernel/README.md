# kernel — the declarative half (MOCK-OUT)

Four files ship, all ported from the oracle at build time with v1 residue
removed (no aliases, no activity type):

```
types/process-step.yaml          the capture substrate: scope / inputs /
                                 transformation / outputs / controls / issues;
                                 the five callout kinds with their declared
                                 fields (CONTROL: Performer, Comparison,
                                 Trigger, Evidence; GAP: Grounds, Nature)
types/taxonomy-node.yaml         one part (scope), one callout kind (the
                                 lens-conflict record)
deliverables/information-request.yaml   the ask loop's front door — curated
                                 asks lead, mechanical feeds as appendix
deliverables/findings-report.yaml       accepted findings by theme
```

A fourth directory joins at build time: `templates/` — the SHIPPED work
shapes (procedure-draft, source-read, assessment, data-analysis), each
declaring mission, write boundary, context contract, return contract,
rules, and a recommended worker class. Engagement-authored templates live
in `<root>/_templates/` and shadow shipped ones by name — the librarian
authors them ad-hoc (always saved before use, logged, reusable).

The definition language's rule set lives in `src/definitions.ts`.
Adding a deliverable = adding a YAML file here (plus at most one view
builder) — the charter property this directory exists to demonstrate.
