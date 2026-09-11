# Synthetic #5 — first integrated assessment (scripted)

**Result: PASS for connected mechanics. Not a live-model result.**

This example uses invented payment-review material to exercise the actual CONSULT
engine and imported assessment writers/runner/renderers together. Analytical
judgments and the narrative are scripted; no paid model, private data, client
send, or real approval is involved.

## Look at the output

- [`example/review-before-response.md`](example/review-before-response.md)
- [`example/evidence-review.md`](example/evidence-review.md)
- [`example/story.md`](example/story.md)

These are illustrative snapshots from a successful run. Their source IDs/paths
belong to that generated engagement, not to this repository's own files. Run the
demo to obtain a complete new engagement, its source artifacts and git history.

## Reproduce

With Node dependencies and Python/PyYAML installed (see root
`IMPLEMENTATION-STATUS.md`):

```sh
npm run demo:assessment
# Or name a directory that does NOT yet exist:
npm run demo:assessment -- /tmp/my-new-fictional-assessment
```

It prints paths to the generated engagement, evidence review, updated narrative,
and results. It never overwrites an existing engagement directory. It creates
and commits only the new fictional engagement's repository, using per-command
synthetic git identity; it does not alter global git configuration.

## Scenario

1. A controller says invoices are checked for duplicates; no operating review
   evidence accompanies the interview.
2. An export repeats an invoice identifier and amount. The integrated analysis
   identifies repeated keys and publishes a versioned, source-backed artifact.
3. A deliberately overreaching draft finding says the invoice was paid twice.
   A scripted review corrects it: repeated export rows are not proof of two
   payments. The old row remains in history.
4. Findings feed a theme, recommendation, initiative, evidence pack and draft
   narrative using the method's own records and scripts.
5. A fresh process resumes from durable state. No agent memory is required.
6. Repeating the analysis creates another immutable artifact, preserving the
   first source ID and bytes.
7. A later payment-register extract lists one payment for the invoice. The
   finding, theme and recommendation are revised explicitly; the before-response
   pack remains available. Register completeness is still an open limitation.
8. Raw sources move to `processed/`; all citations still resolve by identity.

## Mechanical checks

- Shared source IDs and verified source bytes.
- Actual local schema/layer validation combined with engine evidence checking.
- CSV data-record locators distinct from physical text lines.
- Versioned publication with expected input hashes and synthesis grounds.
- Author-owned edits and preserved finding versions.
- Fresh-process resume, tables/figures/bundle rendering and clean final git.
- Zero engine check errors after retirement.

The same run currently produces **30 missing-card warnings** for method-local
ledgers, prompts, intermediate tables and figure files. This is an observed
integration issue, not a failed calculation or something this demo conceals.
It motivates a future generic method-run discovery boundary.

The automated `tests/assessment-demo.test.ts` checks this run in the repository
suite. Separate tests cover changed-source refusal, multiline CSV, two-input
reconciliation, ambiguous keys, provenance collisions and standalone behavior.

## What this does not prove

It does not prove model extraction quality, independent semantic review,
automatic dependency invalidation, professional adequacy of recommendations,
or usability by a non-developer. It reaches the method's `DONE` using explicitly labelled scripted review
decisions, not a real human review or autonomous model. New evidence reopens
review before the updated run completes. Live-model and usability evaluations
remain distinct next steps, not claims hidden inside a synthetic PASS.
