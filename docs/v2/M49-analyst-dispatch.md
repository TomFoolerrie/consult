# M49 — The analyst dispatch path: the last unreachable agent gets reached

**Status: SPEC** — the standing follow-up recorded at M39's close and
carried through every backlog since ("an `analysis.py brief` CLI + analyst
dispatch hint + conflict-records extractor"), plus the per-area findings
filter. Scheduled by the human 2026-08-17 after the review campaign
(M44–M48) closed.

## Why

The analyst (M39) is the only agent with an assessment license — and it is
UNREACHABLE: `scripts/analysis.py` has no CLI, no skill passage dispatches
`consult-analyst`, and nothing assembles its work order. Its verbs exist
(three candidate generators, the findings lifecycle with the human
accept/reject gate); the road to them does not. M39 also named FOUR verbs;
only three generators shipped — the conflict-support extractor (the feeder
for resolution QUESTIONs) is the missing fourth.

## The shape

### Part A — the brief (`analysis.py brief`)

`analysis.py` gains `main(argv)` with a `brief` subcommand:
`python3 scripts/analysis.py brief <area>` prints the analyst's work order
in the brief.py idiom — deterministic, READ-ONLY, deciding nothing:

- the license line (assessment only; propose via `findings.propose`, never
  write an area file, never resolve/rephrase capture content — the M39
  one-direction rule restated as the header);
- the candidate feeds, computed inline: counts + entries from
  `control_gap_candidates`, `handoff_candidates`, `pain_inventory` and the
  new `conflict_records` (Part B);
- the findings register state (proposed / accepted / rejected counts, ids);
- the engagement objective block (`brief.objective_block` — the analyst
  aims at what the engagement was hired to produce);
- the finish contract (propose findings with resolvable grounds; the human
  gate does the accepting).

Refusals: unknown area exit 2; a `brief` over an area outside an
engagement tree refuses by name (the `_root_of` idiom).

### Part B — the fourth generator: `conflict_records(area)`

One record per GAP-kind callout that is a CONFLICT on its face: its body
cites **two or more distinct SRC ids** (the two-mint doctrine's conflict
shape — both readings, both citations), or carries an explicit
`Nature: conflict` field (the v1 grammar). Emits
`{"kind": "conflict-record", "step", "id", "srcs", "text"}` — display ids
via the document-global map, prefixes resolved through the type
declaration, deterministic order, read-only. A GAP citing fewer than two
sources and carrying no conflict field is an absence, not a conflict — not
a record. These records are the raw material for resolution QUESTIONs (the
analyst proposes a finding or drafts the ask; it never resolves).

### Part C — the per-area findings filter: `findings.for_area(root, area)`

`entries()` is engagement-wide; consumers keep re-filtering by hand. New
read-only verb: the entries whose grounds resolve into the named area
(callout ids in the area's corpus, or the area's own step slugs) —
`area` accepted as a name or a path. Findings grounded only in SRC ids or
other areas are excluded. Status filter passes through.

### Part D — the dispatch surface

- `skills/consult-orchestrate/SKILL.md`: an analyst passage — when to
  dispatch (drafted corpus, on the human's request or at a review
  milestone; never in the drafting loop), the brief command, the return
  shape (proposed finding ids), and the human gate (accept/reject stays
  the human's — nothing renders until accepted, which the register
  already enforces structurally).
- `agents/consult-analyst.md`: the contract names the brief as its first
  action (the drafter-contract pattern).

## Test impact

New gate: `tests/test_analyst_m49.py` (committed with this spec; four
skip gates, one per part). **No existing test changes.**

## Acceptance gate

`tests/test_analyst_m49.py` — written before the build: the brief prints
license + feeds + register state + objective and refuses bad areas; the
conflict extractor catches the fixture's two-source GAPs and excludes
single-source ones, both grammars (v2 two-citation, v1 `Nature: conflict`);
`for_area` partitions a proposed finding by its grounds' home; the skill
and the contract carry the dispatch passages; everything read-only and
deterministic.
