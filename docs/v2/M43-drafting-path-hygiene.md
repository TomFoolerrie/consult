# M43 — The process-step drafting path + the hygiene feeder

> **Status: SPEC** — the two follow-ups M42 A1 recorded: (2) the drafter
> contract has no v2 process-step drafting path (its body is the v1
> seven-section document — the largest recorded gap between the kernel
> and its capture agent), and (7) the librarian's callout-grooming
> trigger has no mechanical feeder. Companions: M33 (the type whose
> drafting instructions finally exist), M42 (the doctrine this path
> operationalizes; the four CTRL field names gain their declared home
> here), M39 (analysis.py, the generator pattern the feeder matches),
> M34 (ledger.outstanding, the tagged-but-unconsumed primitive).
> Charter: [`README.md`](README.md).

## Part A — The process-step drafting path (prose, drafter contract)

A new top-level section in `agents/consult-drafter.md` — the v2 sibling
of "What you produce — structure" — teaching a drafter to fill a
process-step fragment. Its content is the IPO fixture's conventions
written down as rules, split honestly into LAW vs HOUSE STYLE:

**LAW (kernel-enforced; a violation refuses at parse):** callout labels
from the declaration only; id grammar `PREFIX-ALNUM`; prefix↔label
agreement; no duplicate ids in one entity; well-formed consult-meta.

**HOUSE STYLE (reconcile/review-enforced; the path states it):**

- `## <Heading>` = the step (matches the manifest); parts as
  `### <Title>` in declaration order (Scope, Inputs, Transformation,
  Outputs, Controls, Issues) — title only, no letters, no numbers.
- **Scope** (prose): what the step does end-to-end; `Owner: <Role>.`;
  `System(s): <...>.`; cadence; handoffs as `[[slug]]` tokens; one
  explicit out-of-scope sentence.
- **Inputs/Outputs** (list): `- <artifact> — from <origin> (<system>)`
  / `- <artifact> — to <destination> (<system>)`. Origin/destination is
  a `[[slug]]` token when it is a step of this area, a named role/actor
  otherwise; the parenthetical names the system or record; a non-step
  terminal gets a prose tail ("retained …", "sent to the supplier by
  email"). These lines ARE the dependency arrows — write them as facts.
- **Transformation**: one narrative paragraph (who works what, what the
  system does, what stops the line), then a `1.`-numbered sub-step list
  of imperative steps — same owner and system throughout (a performer
  change is a split signal, per M42 A5), no callouts in the list.
- **Controls / Issues**: the callout homes. The M42 minting bars govern
  (the contract already carries them for both unit types); the CTRL's
  four fields are now DECLARED (Part C) — carry them as
  `> - **<Field>:** <value>` sub-fields when the sources support them.
  Honest absence is content: a Controls part with no CTRL states what
  was looked for and not found, cited.
- **consult-meta** last: `systems:` and `roles:` registry-slug lists.

**The unit line (Part B) tells you which path you are on** — absent it,
the v1 seven-section path is the default, exactly as today.

## Part B — The unit line (deterministic, brief)

`brief.drafter_brief` gains a `YOUR UNIT` line derived from the area's
RESOLVED deliverable definition: the entity type its entity-part
binding names (`process-step` → the Part A path; `activity` → the v1
path). Unresolvable/undefined → the v1 default, stated ("unit:
activity (default — no definition resolved)"). No new config, no new
dispatch key minted by hand: the definition layer already knows what
the area is made of. The drafter contract's dispatch-input list admits
the line.

## Part C — The four CTRL fields, declared

`kernel/types/process-step.yaml`'s CONTROL callout gains
`fields: [Performer, Comparison, Trigger, Evidence]` — optional
declaration metadata (kernel's callout-key allowlist extends by this
one key; parse behavior unchanged: `fields` on a declaration is
DOCUMENTATION + vocabulary for consumers, never a parse gate). This is
the M42 doctrine's field vocabulary getting its one declared home, so
the hygiene feeder (and any future consumer) reads names from the
declaration instead of typing prose constants.

## Part D — The hygiene feeder (`scripts/hygiene.py`)

Engagement-scoped (takes `root`; walks areas the way engagement.py
does), read-only, cache-free, analysis.py's conventions exactly
(candidates with `grounds` in the corpus's own words; deterministic
order; refusals only for declaration failures, never thin corpora):

1. `duplicate_gap_candidates(root)` — gap-kind callouts across all
   areas/steps whose normalized bodies (lowercased, whitespace
   collapsed, `[[slug]]` flattened, SRC citations stripped) share
   token overlap at or above a fixed, documented threshold. Pairs, each
   naming both ids, both steps, both texts. A candidate, not a verdict.
2. `answered_gap_candidates(root)` — per area, `ledger.outstanding` ×
   open gap callouts: a step's GAP paired with every source tagged to
   that step and not yet consumed by this area. Grounds: the SRC id,
   its file, its ledger note, the GAP text verbatim.
3. `thin_ctrl_candidates(root)` — control-kind callouts whose
   `fields` lack one or more of the DECLARED field names (Part C).
   Prose-only CTRLs (the whole frozen fixture corpus) appear here by
   design — whether the prose carries the facts is the librarian's
   judgment, which is the point of a candidate.

Kind vocabulary = the librarian contract's existing return values
(`duplicate-gaps`, `gap-likely-answered`, `ctrl-missing-field`).
Gap/control kinds resolved through definition bindings + declaration
(analysis.py's discipline; zero shape-audit entries).

## Part E — The librarian wiring

`engagement.placement_brief` gains a `CALLOUT HYGIENE` section
(immediately after the open-gap register — the adjacent
callout-population content), listing the three generators' candidates
with grounds; the brief's return contract adds `callout_grooming`
(syncing it with the librarian contract, which already declares that
key); the librarian contract's "the mechanical feeder does not exist
yet (M43)" sentence is replaced with the feeder's name.

## Acceptance sketch (tests/test_hygiene_m43.py, written first)

- The drafter contract carries the Part A path (grep anchors: the part
  order, the `— from` / `— to` grammar, the LAW-vs-style split, the
  unit line admission); the SKILL/agent split is respected (no v1
  section deleted).
- `drafter_brief` over the IPO area prints `process-step` in its unit
  line; over the v1 p2p fixture prints `activity`; both paths' existing
  output otherwise byte-stable.
- Declaration: process-step's control callout carries the four field
  names; kernel loads it (allowlist extended); a declaration WITHOUT
  fields still loads (optional).
- Generators over tmp IPO copies: an injected near-duplicate GAP pair
  is found (and the distinct fixture GAPs are NOT paired); an injected
  touched-not-consumed source pairs with its step's GAP; fixture CTRLs
  (prose-only) all appear as thin-ctrl candidates with the missing
  names listed; all three read-only (fingerprint); deterministic order.
- `placement_brief` carries the CALLOUT HYGIENE section with candidates
  when they exist and an explicit none-line when not.
- v1 suite green; zero v1 tests edited.

## Complexity accounting

New state: zero. New gates: zero. New agents: zero. New judgment: zero
— the feeder is mechanical candidates for judgment that already has a
license (the librarian's grooming trigger). The bill: one prose path
(conventions that already exist in the fixture, written down), one
brief line read off existing data, one declaration key, one read-only
module. Review risks: **the path drifting from the fixture** (the
exemplar corpus and the instructions must describe the same grammar —
the tests pin both sides), and **candidate flooding** (thin-ctrl flags
every prose CTRL by design; the brief section must present counts +
samples, not walls, and the librarian judges — if real engagements
drown, the threshold/presentation is the knob, never the honesty).

## Deferred (recorded, not built)

- Field-presence as a parse or reconcile GATE — deliberately not: the
  declaration documents, the feeder surfaces, the librarian judges.
- Cross-area duplicate-gap detection variance (different-area pairs
  are included from day one; a same-fact-different-cycle heuristic
  beyond token overlap waits for real-engagement evidence).
- The v1 activity path gaining sub-fields — v1 CTRLs keep their
  Owner/Frequency template; no retrofit.
