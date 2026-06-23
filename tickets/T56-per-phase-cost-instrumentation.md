# T56 — Per-phase cost / size instrumentation (measure the real hotspot)

**Slice 4 (Cost & Runtime Efficiency) · Follow-up · From field run (3 real artifacts, ~$10) ·
Depends: feeds T54 + T55 acceptance · Touches: `scripts/orchestrate.py`,
`scripts/consolidate_inputs.py`, `scripts/draft_inputs.py`, `scripts/synthesis_inputs.py`,
optionally `scripts/cost_report.py` (new), `tests/`.**

> **Field observation.** Total cost was ~$10 for three artifacts; quality "good, TBD." We are
> currently **guessing** which phase dominates (strong prior: T54's orchestrator inlining). This
> ticket replaces the guess with a per-phase **size/structure** map so T54 and T55 are optimized
> against data, not intuition. **No client content is ever emitted — only sizes, counts, and
> phase labels.**

## Problem

There is no per-phase visibility into where tokens/cost go. The input-gatherer scripts already
assemble and print the exact JSON **bundles** that get fed to each sub-agent
(`consolidate_inputs.py:290`, `draft_inputs.py:262`, `synthesis_inputs.py:296`) — i.e. the
per-phase *input size* is already computable, we just don't surface it. Likewise the classify
artifacts and deliverable MDs have measurable output sizes. Without this, T54 ("did inlining
actually cost the most?") and T55 ("did the trim help?") have no acceptance signal beyond a raw
dollar total.

**Runtime constraint (Desktop).** In Claude Desktop there is **no programmatic per-phase token
meter** — the skill cannot read its own token usage. So this ticket instruments the **content
size** that drives tokens (a faithful proxy), plus a place to **hand-annotate** the dollar figure
from the run, rather than pretending to auto-capture token counts the runtime won't expose.

## Build

1. **Bundle size reporting (proxy for input tokens).** In each input gatherer
   (`consolidate_inputs.py`, `draft_inputs.py`, `synthesis_inputs.py`), when `--json` is emitted,
   also expose a compact size summary (to **stderr** or a sibling `--measure` flag so it never
   pollutes the bundle the sub-agent consumes): total chars, an approximate token estimate
   (chars/4 — label it an estimate, do not imply exactness), and a per-section breakdown
   (e.g. taxonomy slice vs evidence vs prior MD). **Sizes and section names only — no content.**
2. **Phase rollup in `orchestrate.py`.** Add a read-only `orchestrate.py measure --engagement E`
   (or extend `next --all`) that walks the engagement and reports, per phase: number of targets,
   input-bundle size estimate per target (from #1), and output artifact/MD sizes already on disk.
   Read-only, like `next` — writes nothing.
3. **Optional `cost_report.py` (new).** A small reporter that aggregates #1/#2 into a one-screen
   table (phase, #targets, est. input tokens, output bytes) and provides a field to **paste the
   measured $ total** for the run so the team can correlate size→cost across runs. Keep it
   dependency-free and content-free.
4. **Acceptance hook for T54/T55.** Document the one command an operator runs after a 3-artifact
   engagement to capture the per-phase size map; that output is the acceptance artifact T54 and
   T55 reference (e.g. "classify input dropped N% after T55's `quote` trim";
   "orchestrator-context size bounded after T54").

## Tests

- `orchestrate.py measure` / the gatherer `--measure` path is **read-only** — running it leaves
  `state.json` / `register.json` / artifacts byte-identical (assert on the Slice-1 fixture).
- The size summary contains **no document content** — assert the output is purely
  numeric/structural (grep the measure output for a known content token from the fixture and
  assert **absent**).
- Size estimates are deterministic for a fixed corpus (same fixture → same numbers).
- No regression: the gatherers' normal `--json` bundle output is **unchanged** (the measure
  output is separate — stderr or a distinct flag), so sub-agents consume exactly what they did
  before. Slice-1 e2e green.

## DoD

- A single read-only command produces a per-phase size/structure map (targets, est. input tokens,
  output sizes) with **zero client content** in the output.
- The gatherers' consumed bundles are unchanged; measurement is side-channel only.
- T54 and T55 can cite a before/after from this map as their acceptance signal.
- A place exists to record the run's measured $ total alongside the size map for size→cost
  correlation over time.
