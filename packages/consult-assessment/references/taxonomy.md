# Taxonomy — the house's knowledge model

The skill fixes the **method**: findings are sourced evidence; themes are diagnoses that cite findings; recommendations cite themes; initiatives cite recommendations; the story cites everything; only authors edit; figures are queries over the ledgers. The taxonomy defines the **knowledge**: what a finding is classified by, which axis carries the root cause, what gets plotted against what. Change the engagement type by changing this file, not the scripts.

```yaml
name: pre-audit-readiness

axes:                      # classification fields on every finding; order = display order
  <axis_name>:
    label: Business cycle  # column header / figure label
    role: where            # free text shown to readers ("where", "what is at risk", "why")
    values: [...]          # allowed values, in sort order
    required: true         # always required on a finding
    required_when: {other_axis: value}   # required only under a condition; optional otherwise
    multi: true            # list-valued (a finding may sit on several values)
    primary: true          # exactly one axis: the scorecard groups by it; tables sort by it
    on_theme: true         # themes carry this axis as their diagnosis; the finding's value is provisional
    secondary: true        # permits secondary_<axis> on findings and themes

scales:
  severity: {1: "...", 2: "...", 3: "..."}     # findings; the top value counts as "high" in the scorecard
  impact:   {1: Low, 2: Medium, 3: High}        # initiatives
  effort:   {1: Low, 2: Medium, 3: High}        # initiatives

figures:                   # house figures; method figures are always built
  - {id: fig-x, type: heatmap, rows: <axis>, cols: <axis>, title: "...", question: "..."}
  - {id: fig-y, type: bar, axis: <axis>, by: <axis>, title: "...", question: "..."}

rules: |                   # tagging discipline; readers load it verbatim
  ...
```

## What the method adds to every finding regardless of house
`type` (gap | risk | strength | observation), `evidence_basis` (stated | observed | inferred), `severity`, `observation`, `sources`, `related`. Strengths feed the validation beat of the story; evidence basis governs the merge rule; the rest is the citation chain.

## What a theme carries
`theme`, `root_cause`, `impact`, `findings[]`, plus **every axis marked `on_theme`** as a required field. The validator warns when a theme's value on that axis matches none of its findings' provisional values.

## Figures
- `heatmap` — `rows` × `cols`, either may be multi-valued. Cells carry a theme count (label), a finding count (evidence), max severity, and ids.
- `bar` — one axis; theme series (via footprint, or the theme's own value when the axis is `on_theme`) plus a finding series; optional `by` breaks the theme series down by another axis.
- Method figures always built: `fig-scorecard` (by the primary axis), `fig-themes`, `fig-priority`, `fig-roadmap`, `fig-trace`, `fig-coverage`, `fig-unthemed`, `fig-strengths`.

A theme has no coordinates of its own. Its footprint on any axis is the union of its findings' values, so a fact evidenced twice counts as one problem and no schema change is needed to plot themes anywhere findings can be plotted.

## Two examples in the box
`assets/taxonomy.yaml` — pre-audit readiness (business cycle × assertion / process attribute, dimension on themes).
`tests/fixture/taxonomy-itgc.yaml` — ITGC assessment (domain × control objective, systems, maturity gap on themes). `tests/smoke-house.sh` runs the same scripts against it.

## Swapping taxonomies mid-engagement
Don't. Axes are read at validate and render time, so an old ledger validated against a new taxonomy will fail on every renamed axis. Pick the model before extract; if it must change, treat it as a new run with a rollback point.
