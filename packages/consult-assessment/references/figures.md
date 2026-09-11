# Figure catalog

`render.py figures` emits one JSON spec per figure into the manifest's `paths.figures`. Specs are brand-agnostic; the brand renderer decides how each `type` becomes a slide. Every spec carries `sources` (the ids behind it) and a declared `unit`.

Two units exist: **themes** answer "how many problems" (a theme's footprint on an axis is the union of its findings' values, so a fact evidenced twice counts once); **findings** answer "how much evidence". A figure that shows both says which is the label and which is the support. Before themes exist, theme counts are zero; renderers fall back to the findings series and label it as evidence, and the story should not lead with theme-unit figures until the theme gate has passed.

## House figures — declared in the taxonomy's `figures:` block

| type | declared with | data |
|---|---|---|
| heatmap | `rows: <axis>, cols: <axis>` | per cell: theme count (label), finding count (evidence), max_severity, ids. Either axis may be multi-valued. Any finding with a value on both axes lands here, whatever its other tags |
| bar | `axis: <axis>` [, `by: <axis>`] | theme series and finding series per value; optional breakdown of the theme series by another axis |

The default taxonomy ships three: `fig-heatmap` (business cycle × assertion), `fig-process` (business cycle × process attribute), `fig-dimensions` (dimension, by business cycle).

## Method figures — always built

| id | type | unit | data | answers |
|---|---|---|---|---|
| fig-scorecard | table | themes + findings | per value of the primary axis: findings, strengths, max severity, highs, theme ids | How does each area stand? |
| fig-themes | cards | themes | theme, root cause, on_theme axes, impact, footprint on the primary axis, severity, rec ids | What are the patterns? |
| fig-priority | quadrant | initiatives | impact × effort | What first? |
| fig-roadmap | timeline | initiatives | dependencies and duration | In what order? |
| fig-trace | funnel | counts | F→T→R→I + orphans | How we got here |
| fig-coverage | bar | findings | per source; evidence-basis mix | What drove this? |
| fig-unthemed | list | findings | non-strength findings in no theme, with primary-axis value and severity | What did we see that didn't form a pattern? |
| fig-strengths | list | findings | strength findings by primary-axis value | What to keep doing |
| fig-open-items | list | findings | `open_item` findings with sources | What did we not get to? (appendix / workplan) |

"Evidence" everywhere above means findings of type gap, risk, or observation. Strengths and open items are never counted as problems.

A new heatmap or bar is a taxonomy edit. A new figure *type* is a `render.py` change; keep it a pure function of the ledgers — no judgment in the renderer. The story cites figures by id; if one it needs is missing, it leaves a `<!-- needs figure -->` comment for the orchestrator.
