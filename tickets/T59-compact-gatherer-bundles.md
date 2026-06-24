# T59 — Compact gatherer bundle serialization (input-token trim)

**Slice 4 (Cost & Runtime Efficiency) · Small optimization · Depends: — · Sequence with T56
(same files) · Touches: `scripts/consolidate_inputs.py`, `scripts/draft_inputs.py`,
`scripts/synthesis_inputs.py` (and optionally `scripts/orchestrate.py`), `tests/`.**

> **Origin.** Follow-up to the JSONL-vs-input-tokens question: JSONL does **not** save input
> tokens (its value is fault-isolation / emission reliability, not transport size). The real,
> near-free input-token lever is **compactness** — the gatherer bundles are pretty-printed and the
> indentation is pure overhead on every fan-out call.

## Problem

The read-only input gatherers emit their bundles with `json.dumps(bundle, ensure_ascii=False,
indent=2)` — `consolidate_inputs.py:290`, `draft_inputs.py:262`, `synthesis_inputs.py:296`. That
bundle **is the fan-out worker's input** (consumed by `consult-consolidator` / `consult-drafter` /
`consult-improvement-drafter` / `consult-synthesizer`). The `indent=2` whitespace (leading spaces +
newlines on every line) tokenizes as input on **every** worker invocation — paid per node / per L1
/ per engagement, across every run. It buys nothing for a machine consumer.

This is a modest, **compounding** trim — not a headline win like T55's `quote`-drop (which removes a
whole duplicated field). But it is genuinely near-free and independent of everything else.

## Build

- Switch the **`--json` bundle emit** in the three gatherers to **compact**: `json.dumps(bundle,
  ensure_ascii=False, separators=(",", ":"))` (drop `indent`). Keep `ensure_ascii=False` (don't
  re-introduce `\uXXXX` escaping, which would *cost* tokens on non-ASCII client text).
- **Optional, smaller lever:** `orchestrate.py next --json` (consumed by `consult-run`) — compact
  it too; it's a tiny single object, so the saving is marginal. Leave the human-readable
  `print_human` paths alone.
- **Do NOT touch on-disk state/artifacts.** `state.json`, `register.json`, `classify/*.json`,
  deliverable files stay readable/diffable (they're system-of-record, not transport, and
  diff-friendliness matters for review + git). Scope is **transport bundles only**.

## Reconciliation (so the set stays coherent)

- **vs T56:** T56's "measurement is side-channel; the bundle is unchanged" means *measurement does
  not pollute the bundle* — still true. T59 separately makes the bundle **compact**; T56's size
  figures then simply reflect the smaller bundle. No contradiction, but T56's wording is annotated
  to point here.
- **vs T58:** T58 creates its golden **after** T59, so the baseline already reflects compact
  bundles. If T58 ships first, refresh the bundle-related fixtures when T59 lands.

## Tests

- **Round-trip identity:** the compact bundle parses to the **same Python object** as the old
  pretty bundle (`json.loads(compact) == json.loads(pretty)`) — functionally identical input.
- **Size drop:** assert the compact bundle is strictly smaller (byte/char count) than the pretty
  one on a fixture — the whole point.
- **Consumer unaffected:** the fan-out workers still parse + use the bundle (exercise via the
  existing gather → worker path on the r2r fixture).
- **No state reformatting:** `state.json` / `register.json` / `classify/*.json` serialization is
  unchanged (still readable) — assert one on-disk file is byte-identical to pre-ticket.
- Any test that snapshots gatherer bundle **text** is updated to the compact form.

## DoD

- The three gatherer `--json` bundles emit compact JSON; the parsed object is identical; a
  measurable input-size reduction is asserted on a fixture.
- On-disk state/artifacts are untouched (still pretty/diffable).
- T56 wording annotated; T58 baseline accounts for compact bundles; no scratch left.
