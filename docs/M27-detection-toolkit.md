# M27 — Detection as a toolkit (layer 1 serves layer 2, on demand)

> **Status: PROPOSED — user-directed, not yet designed in detail, NOT
> built.** Captured 2026-07-30 from the user's direction: "think of
> [mechanical detection] more like a tool that the placement pass uses to
> do its job. Perhaps we can reduce the tokens layer two takes by giving
> it a really nice tool kit." Companions: M24 (the placement pass this
> re-instruments), M26 (the spine — already the first "tool-shaped"
> detection output), M12 (whose brief/note pattern is the precedent for
> script-computes / agent-judges).

## The observation

Today the engagement layer is a PIPELINE: `audit` computes every
mechanical finding up front, `brief` dumps ALL of it — findings, the full
gap register, area digests (or, with `--full`, every fragment whole) —
into one placement agent's context, and the agent works the pile top to
bottom. That shape pays for everything whether or not the agent needs it:

- The `--full` read is ~150–250k tokens at 4 L1s and grows linearly with
  the corpus, even when only a handful of findings need step-body depth.
- The digest mode under-recalled precisely BECAUSE it pre-decided what the
  agent would need to see (Scope sections only) — the fix so far was
  "show it everything" (`--full`), which is the opposite over-correction.
- The agent cannot ask a follow-up question. Its only moves are "work with
  what the brief gave me" or "name a fragment in `needs_full_read` and
  wait for a human to re-dispatch."

The reframe: mechanical detection is not a REPORT the agent reads — it is
a TOOLKIT the agent queries. The brief shrinks to the work order + the
finding INDEX; the evidence is pulled on demand, per finding, at the
granularity the finding actually needs.

## Sketch (to be designed properly before building)

A `query` surface on `engagement.py` (names illustrative):

- `engagement.py show <area>/<slug> [--section steps|scope|...]` — one
  fragment, or one section of one fragment, instead of the whole corpus.
- `engagement.py gaps [--area X] [--grep "..."]` — the gap register,
  filtered, instead of all ~100 gaps every time.
- `engagement.py matches <area>/<slug>` — the shingle/mention/twin
  findings TOUCHING one procedure (detection inverted: by-procedure view
  of the same computed facts).
- `engagement.py answers "<gap text or id>"` — candidate answering
  passages ranked by the existing shingle/title machinery: the script
  proposes WHERE to look, the agent reads only those spans and judges.
- `engagement.py spine [--area X]` — the M26 derived view, filtered.
- `engagement.py registers [--grep]` — register contents, so
  "is this already registered?" costs one query, not a standing listing.

The placement agent's flow becomes: read the compact index (counts + one
line per mechanical finding) → for each finding, pull exactly the
evidence it needs → route to a move or report. Tokens scale with the
FINDING COUNT, not the corpus size — which also un-blocks the size guard:
an engagement too big for `--full` is fine when nothing is read whole
unless a finding demands it.

## Constraints already settled (carry them into the design)

- The verbs stay read-only queries + the existing two writers (`note`,
  `adopt` command named in a note). The toolkit adds NO new writers.
- Deterministic extraction only: every query returns script-computed
  text/facts, never model output — same discipline as the M12 digest.
- The anti-silent-loss rule applies to queries: a filtered view must say
  what it filtered ("12 of 104 gaps shown") so the agent can't mistake a
  slice for the whole.
- The one gap parser (`callouts.open_gaps`), the one section parser, the
  one token grammar are the ONLY parsers behind the queries — no new
  parallel implementations.
- `--full` and digest mode remain as-is until the toolkit proves itself
  on a live run (the migration instrument is not gambled on this).
- Bounded-read contract for the agent, like the consolidator's cross
  pass: queries are the sanctioned way to widen a read; opening arbitrary
  files stays out of contract.

## Open questions for the design pass

1. Which queries earn their keep? Start from a transcript of a real
   placement run: every place the agent needed something the brief
   didn't have (or had 50x more than needed) names a query.
2. Does `answers` (candidate ranking) reintroduce the anchoring risk the
   rejected planner had — the script pre-deciding relevance? Mitigation
   sketch: it RANKS, never filters; the index still lists every gap.
3. Does the audit keep its human-facing report shape unchanged (yes,
   presumably — the toolkit is the agent-facing view of the same facts)?
4. Interaction with M12: should the consolidator's cross pass get the
   same toolkit instead of its baked digest? (Same shape, smaller scope.)
5. Token accounting: instrument a run with and without the toolkit before
   declaring victory — the digest-mode lesson is that pre-deciding what
   the agent needs can silently cost recall, and recall is the metric
   that matters here, not tokens alone.

## Explicitly not the goal

- Not a general RAG layer, not embeddings, not search infrastructure —
  deterministic filters and extractions over facts the scripts already
  compute.
- Not a reduction in what the HUMAN sees: `audit`'s report stays a
  complete, loud, no-silent-caps document.
