# M39 WP-F3 — the consult-analyst brief, self-review against the ticket

What this is: the orchestrator's review aid for the prose half of M39, in the
M37 format. Every contract line from
[`../M39-analysis-verbs.md`](../M39-analysis-verbs.md) and
[`../M39-build-plan.md`](../M39-build-plan.md) is quoted with the section of
prose that satisfies it; then the license boundary is traced rule by rule; then
the friction (what the machinery does not yet have) is recorded rather than
invented.

Files in this work package:

| file | state |
|---|---|
| `agents/consult-analyst.md` | new |
| `docs/v2/notes/m39-analyst-self-review.md` | new (this file) |

No script, kernel, test or fixture change. Prose only.

---

## A. Ticket line → where it is satisfied

> Build plan WP-F3: "Owns `agents/consult-analyst.md` (new) + a self-review note
> (docs/v2/notes/m39-analyst-self-review.md)."

This package, exactly these two files.

> Build plan WP-F3: "The license: assess and PROPOSE findings (via the
> structured return; the deterministic layer writes through findings.propose at
> the human gate) — never write, never resolve, never adjudicate a conflict"

**## THE LICENSE — hard rule 1, before anything else**, stated as the brief's
first substantive section and repeated as hard rule 1. Its five clauses map
one-to-one onto the ticket's: never write a file (with the tool list named as the
enforcement — `tools: Read, Grep, Glob`, no writer), never edit an entity, never
resolve a conflict, never soften or rephrase what a person said, and "**Findings
you propose are written by the deterministic layer only after the human accepts
them in conversation**" naming `findings.propose` and the `proposed` status.

> M39 Part A: "the CLAIM (the analyst's assessment, in the system's voice — the
> first place the system is allowed one)"

**## THE RETURN CONTRACT**, the `claim` bullet: "the assessment, **in the
system's voice**. This is the one place in the entire system where the system
speaks" — with the writing rules that follow from that (declarative, specific, no
hedging, no pipeline vocabulary), and the opening paragraph of the brief which
frames the whole role as the licensed exception to every upstream agent's
observe-never-judge.

> M39 Part A: "**grounds** (the SRC ids, PAIN/GAP callout ids, entity slugs, and
> coverage facts it rests on — every finding traces or it does not exist)"

The `grounds` bullet of the return contract, carrying the ticket's sentence
verbatim ("Every claim traces or it does not exist"), the id classes
(`SRC-`/`PP-`/`GAP-`/`CTRL-`/slugs), the resolution requirement and the refusal
behaviour from `findings.resolve_grounds` (unresolvable ground refused **by
name**, nothing written), plus the rule that ids are cited *exactly as handed* —
never reconstructed, never invented. Hard rule 2 (**grounds or nothing**) repeats
it with the `ungroundable` escape hatch so an ungroundable belief has somewhere
honest to go instead of becoming a fabricated citation.

> M39 Part A: "severity/theme tags"

`theme` (short, stable, client-readable; reuse when the theme really is the same;
the verb refuses a blank one — matching `findings.propose`) and
`severity_suggestion` (`high|medium|low`, explicitly **a suggestion**, stated
with its basis, "never a number, never a matrix" — the human overrules).

> M39 Part A: "**The human gate is the M30 conversation, reused**: analysis
> proposes; the human accepts, edits, or rejects in chat; the register verb
> writes. A finding never reaches a rendered deliverable before acceptance."

License clause 5, and the return contract's framing ("ready for
`findings.propose` … at the human gate"). The brief states that only `accepted`
findings can reach a rendered deliverable and that the analyst never runs the
verb — matching `findings.renderable` (accepted only).

> M39 Part A: "**Findings never flow back into the capture layer.** No note, no
> edit, no callout is generated from a finding into any entity … One direction.
> (The one exception: a finding may propose an information request…)"

License clause 2 (with the mechanical audit named: "a full analysis pass must
leave every entity, view and note file byte-identical … a pass that changed one
byte failed however good the analysis was") and **hard rule 3**, which names the
forbidden trees (`components/`, `_sources/`) and carries the single exception —
the information request, "which asks for evidence rather than asserting a
conclusion". The request appears in the return contract as the optional
`information_request` field on the M37 request path.

> Build plan WP-F3: "model-pinned like the other workers"

Front matter: `model: opus`, with the inline pin comment in the workers'
convention and the standalone `<!-- model pin rationale (M26 convention,
carried) -->` block under the front matter — the surveyor's shape exactly.
**Opus, not sonnet**: the surveyor pins opus because it is "the engagement's
single point of judgment"; the analyst is the engagement's only *assessment*
license, its claims are cited in a client deliverable, and the pass is bounded
(one verb, one area), so the premium is bounded. The drafter/consolidator sonnet
tier is the *proven worker* tier for bounded content work; assessment is not
that.

> Acceptance sketch: "`consult-analyst` is model-pinned and brief-fed like the
> other workers; its contract carries the assessment license and its boundary
> (proposes findings; resolves nothing; writes nothing)."

Front matter pin + **## Your assignment (from the dispatch prompt)** (the
brief-fed dispatch fields: `area`, `root`, `verb`, and the candidate material) +
the license section. "Resolves nothing" is verb 3's boundary and hard rule 4;
"writes nothing" is license clause 1 and the tool list.

> Build plan WP-F3: "candidates handed in precomputed (never re-derive mechanics
> — the coverage-map discipline)"

**## Your inputs are HANDED TO YOU, precomputed — never re-derived**, opening
with the discipline and its *reason* in the coverage-map's own terms ("a
hand-recount that disagrees with the generator laundres a wrong answer into a
confident one"), the four handed inputs each with its real fields, and the
instruction to report a disagreement rather than substitute arithmetic
(`disagreements` in the return). **Hard rule 7** repeats it and forbids writing a
coverage or candidate file — the charter's one hard guardrail, in the surveyor's
wording.

> Build plan design pins: "Generators produce CANDIDATES with mechanical grounds;
> judgment (materiality, clustering) is the analyst agent's."

The verb sections, each opening with "**The work:**" and naming what the generator
already did versus what the judgment adds. Verbs 2 and 4 are explicitly
materiality passes over a set the analyst may not extend (hard rule 5); verb 1 is
the clustering pass.

> M39 Part B verb 1: "**Pain synthesis** — cluster PAIN callouts across the
> engagement (same friction voiced in three areas is one theme, evidenced
> thrice); propose themed findings with all voices cited."

**### 1. `pain-synthesis`** — "the same friction voiced in N places is **one theme
evidenced N times**, not N findings"; "**Every voice is cited**" (every pain id in
the cluster plus the `SRC-` ids those pains name; "a cluster that quietly drops
the two weakest members has misrepresented its own weight of evidence"); the
verbatim-framing boundary; and the anti-inflation rule (one pain alone is a
single-voice finding stated as such, never padded with adjacent non-matching
pains).

> M39 Part B verb 2: "**Control coverage** — mechanical candidate generation …
> agent judgment on which candidates matter; propose gap findings."

**### 2. `control-coverage`** — materiality on the two axes the evidence supports
(**what the output feeds**; **what the pains say**), the explained-absence rule
("an **explained absence can still be a finding** … *but say so honestly*", and
the two symmetric prohibitions: never present an explained absence as
undiscovered, never present an undocumented absence as a design decision), and
the no-design boundary.

> M39 Part B verb 3: "for M37 `conflicted` facts: lay out both claims, their
> sources, and what each would imply — proposing a RESOLUTION QUESTION, not a
> resolution (the human or the client resolves; the licensed-exception boundary
> stops here)."

**### 3. `conflict-support`**, as a numbered three-part contract: (1) both claims
with attribution, neither softened, dropped or blended; (2) what each would
imply, worked through with a concrete example, "both implications … with equal
seriousness"; (3) the `resolution_question` with its three required parts (**who
to ask**, **what would settle it**, the question itself). Then "**NEVER a
verdict**", enumerating the disguises a verdict wears (recency, presumed
accuracy, a probability, a lean, a recommendation dressed as a summary) with the
operational tell: "If you find yourself writing 'likely', stop — that word is the
boundary being crossed." Plus the grounds rule that a conflict finding cites
**both** `SRC-` ids, because "citing one side's source only is how a verdict
smuggles itself in through the grounds".

> M39 Part B verb 4: "**Handoff friction** — IPO-edge analysis: outputs nobody
> consumes, inputs nobody produces, steps whose owner changes mid-artifact —
> mechanical detection, agent-judged materiality."

**### 4. `handoff-friction`** — the ticket's own materiality line as the two
poles ("**A retained log is not friction**" / "**An unconsumed work product
someone spends hours on IS friction**"), the paraphrase pre-test with its
`discarded`-on-paraphrase reporting duty (so the matcher's known blind spot stays
visible), and the `shared-input` judgment. The owner-change shape is named as **a
recorded generator miss, not a licence to detect it by hand** — see the friction
section below.

> M39 Part B: "an analysis agent (one new agent definition, `consult-analyst`,
> mode-scoped like the drafter) judges"

The `verb` dispatch field ("**One verb per dispatch**, like the drafter's mode")
and **hard rule 8** (material belonging to another verb is reported, not judged;
"a redispatch, not an initiative").

> M39 complexity accounting: "The review risk to police: **assessment leaking
> upstream** — an analyst note that 'fixes' a drafter's framing, a finding that
> edits a pain's wording at citation time, any path by which the system's opinion
> contaminates the record of what was said."

Three places, deliberately: license clause 4 (never soften or rephrase, naming
this exact risk), verb 1's verbatim boundary with a worked negative example ("you
may not smooth 'the AP lady just fixes it in the spreadsheet' into 'manual
intervention occurs downstream'"), and **hard rule 6** (pain wording verbatim;
"Your claim is your voice; the evidence inside it is theirs"). Hard rule 3 closes
the note/callout path.

> M39 Deferred: "**Future-state / recommendation deliverables** — findings say
> what is wrong; recommendations say what to build."

**Hard rule 9** (no recommendations), plus the no-design boundary inside verbs 2
and 4.

> M37 carry-in (the discipline this ticket is the licensed exception to):
> "Adjudication is human (at review) or analytical (M39) — never the drafter's,
> never the surveyor's."

The brief's opening paragraph enumerates the upstream prohibitions and claims the
vacancy they leave; verb 3 then states where the licensed exception itself stops.
The drafter's rule 6 and the surveyor's lens-conflict record are the producers of
the `conflicts` input, described in the inputs section in their own terms (a GAP
callout on a node naming ≥2 distinct `SRC-` ids — the record `coverage_map` reads).

> Build plan design pins: "Grounds are MANDATORY and must resolve against the
> engagement (SRC ids in the ledger; PP/GAP callout ids in the area corpus; entity
> slugs in manifests) — refusal names the unresolvable ground."

The `grounds` bullet, matching `findings.resolve_grounds`'s three-part universe
and its refusal message shape. The brief does not restate the resolution
algorithm — it states the consequence for the author (cite handed ids exactly;
an unresolvable ground means nothing is written).

### Real field names, checked against the modules

Every field the brief names exists in `scripts/analysis.py`:

| brief input | source function | fields named in the brief |
|---|---|---|
| `pains` | `analysis.pain_inventory` | `id`, `slug`, `heading`, `home`, `text`, `fields`, `srcs` — all seven, with the empty-`srcs` case called out as the generator documents it |
| `control_candidates` | `analysis.control_gap_candidates` | `slug`, `heading`, `produced`, `control_prose`, `srcs`, `grounds` — all six |
| `handoff_candidates` | `analysis.handoff_candidates` | `kind` (`orphan-output` / `shared-input`, the module's `KIND_*` values), `slug`, `slugs`, `artifact`, `item`, `grounds` — all six |
| `coverage` | `coverage_map.coverage` | the four statuses `evidenced | sourced | claimed | conflicted` |
| `conflicts` | node GAP callouts (`coverage_map._is_conflicted`'s record) | node slug, GAP id, both `SRC-` ids, both claims |

The return contract's names (`claim`, `grounds`, `theme`) are exactly
`findings.propose`'s keyword arguments; `severity_suggestion`,
`resolution_question` and `information_request` are agent-return fields for the
human gate, not `propose` arguments (see the friction below).

---

## B. The license boundary, traced rule by rule

| boundary | where stated | how the prose enforces it |
|---|---|---|
| never write a file | license clause 1; hard rule 1 | the front-matter tool list has **no writer** (`Read, Grep, Glob`) and the brief says so explicitly ("that is the contract, not an oversight"); no command anywhere in the brief is a write |
| never edit an entity | license clause 2; hard rule 3 | the one-direction rule with the byte-identical audit named as the consequence; the read set forbids even *reading* sources and `_review/`, so there is no path to a "correction" |
| never resolve a conflict | verb 3; hard rule 4 | the three-part contract makes the *deliverable* a question; the verdict prohibition enumerates the disguises; the grounds rule forces both `SRC-` ids so a one-sided citation cannot pass |
| never rephrase a person | license clause 4; verb 1; hard rule 6 | verbatim-with-attribution, a worked negative example, and the split of voices ("your claim is your voice; the evidence inside it is theirs") |
| the deterministic layer writes | license clause 5; return contract | the return is *proposal-shaped*, matching `propose`'s signature; the brief states the analyst never runs the verb and that a proposal is not a finding until a person says so |
| the human gate | license clause 5 | accept/edit/reject in chat; `renderable` = accepted only, so nothing proposed can render |
| candidates precomputed | inputs section; hard rule 7 | never recompute, never write a cache file, report disagreements in `disagreements` |
| no invented candidates | hard rule 5; verb 4 | `generator_gaps` is the only outlet, with the reason (no mechanical grounds, not reproducible, turns a bounded pass unbounded) |
| everything accounted for | attestation; hard rule 10 | `candidates_received` must equal `candidates_assessed`; every candidate is grounds or a named `discarded` line |
| no recommendations | hard rule 9; verbs 2 and 4 | the assessment stops at what is wrong; the deferral is named as the ticket's, not a stylistic preference |

House-style conformance (sibling test against `consult-surveyor.md` /
`consult-consolidator.md`): YAML front matter with `name` / `model` / folded
`description` / `tools`; an HTML-comment model-pin rationale; `# <name> — <one
line>` H1; `## Your assignment (from the dispatch prompt)`; an inputs section with
the never-re-derive prohibition; a numbered `## Hard rules`; a `## What you return
(COMPACT — …)` closing with the "do not return source text" discipline; and an
attestation block whose counts must match (the surveyor's
`files_listed`/`files_read` pattern, applied to candidates).

---

## C. Friction — what the machinery does not have (recorded, never invented)

These are honest gaps between the brief's needs and the shipped deterministic
layer. Nothing was invented to paper over them; the brief is written to the
machinery that exists.

- **There is no analyst brief command, and no dispatch assembler.**
  `scripts/analysis.py` and `scripts/findings.py` are both **library modules with
  no `__main__` and no argparse** — unlike `consolidate.py brief` or `brief.py`,
  which the consolidator and drafter briefs open with as their first action. So
  the analyst brief cannot say "run your brief"; it says the candidate material
  **arrives in the dispatch prompt, precomputed**, and describes the dict shapes
  the caller will have obtained from `analysis.control_gap_candidates`,
  `analysis.handoff_candidates`, `analysis.pain_inventory` and
  `coverage_map.coverage`. **If M39 wants the analyst dispatched like the other
  workers, this is the gap to close** (an `analysis.py brief <area> --verb` that
  assembles exactly these four inputs). It was not invented here.
- **No orchestrator action dispatches `consult-analyst`.** Nothing in
  `skills/consult-orchestrate/` names the analyst or the findings register; the
  advisor's action names are out of this package's scope (the M37 precedent: "the
  advisor's action names are WP-S3's business"). The brief states who dispatches
  it (`consult-orchestrate`, after the drafters land) as the intended flow, not as
  an implemented one. Concretely: `scripts/orchestrate.py` carries a brief map
  (`_CENTRAL_TAXONOMY_BRIEFS`, line ~200) pointing dispatch hints at
  `agents/consult-surveyor.md` / `agents/consult-librarian.md`, and
  `tests/test_dispatch_hints_m37.py` pins those two strings. There is **no analyst
  entry and no analysis action**, so no dispatch hint can name this brief yet;
  adding one is a script change and therefore outside WP-F3 (prose only).
- **There is no conflict-record extractor.** `coverage_map._is_conflicted` returns
  a **boolean** — it decides that a node is `conflicted` but returns neither the
  GAP id, the two `SRC-` ids, nor the two claims. Verb 3 needs all four. The
  brief therefore describes `conflicts` as records the *dispatcher* assembles from
  the node GAP callouts (which is where the data provably is — that callout body
  is what `_is_conflicted` reads), and specifies exactly which four facts each
  record must carry. **A `coverage_map.conflict_records(root)` (or an
  `analysis.conflict_candidates`) returning `{node, gap_id, srcs, claims}` is the
  missing generator** — the fourth verb's material is the only one of the four
  with no function of its own. Recorded, not built (WP-F2 owns the generators and
  is closed).
- **`findings.propose` has no slot for severity, the resolution question, or the
  information request.** Its signature is `propose(root, claim, grounds, theme)`
  and the entry it writes carries `id`/`status`/`theme`/`claim`/`grounds` (plus
  `reason` on a transition). So `severity_suggestion`, `resolution_question` and
  `information_request` ride in the **agent return** for the human at the gate,
  and the brief says so rather than implying the register stores them. Where the
  human wants a resolution question preserved in the record, it has to be written
  into the `claim` text. **If findings should carry severity as a field, that is
  an additive change to `findings.py` and a follow-up ticket** — WP-F1 is closed
  and this package changes no script.
- **Owner-change-mid-artifact is not generated.** `analysis.handoff_candidates`
  records the miss in its own docstring, with the reason (role bindings exist, but
  which bound role owns an artifact at a given moment is authored in prose, so a
  mechanical claim would be "an inference wearing mechanical clothing"). The brief
  keeps it a miss: verb 4 names it as not generated, and hard rule 5 routes any
  instance the analyst notices to `generator_gaps` — the ticket's third handoff
  shape stays visible without the analyst hand-detecting it and producing a
  finding with no mechanical grounds.
- **`analysis.py` is per-area; pain synthesis is described as engagement-wide.**
  M39 Part B verb 1 says "cluster PAIN callouts **across the engagement**" and
  "the same friction voiced in three **areas**", but `pain_inventory(area)` takes
  one area. The brief scopes the dispatch to one area (`area` + `root`) and
  clusters within it, which is what the generator supports; the cross-area
  synthesis would need either a multi-area dispatch or a union of inventories at
  the caller. Recorded as a scope narrowing, deliberately not smuggled in as a
  read-more-areas instruction — that would violate the bounded read set.

---

## Standing rule

`python3 -m pytest --tb=no -p no:warnings 2>&1 | tail -1` → `1056 passed, 1
xfailed` (0 failed) with the brief in place. Two tests do reference agent brief
FILENAMES — `tests/test_dispatch_hints_m37.py` asserts the surveyor and librarian
paths in `orchestrate.py`'s dispatch hints — but no test reads any brief's body,
and nothing references `consult-analyst` (there is no analysis action to hint at;
see the friction above). So this package is green by construction; the deterministic
gate for M39 is `tests/test_findings_m39.py`, owned by WP-F1 and WP-F2.
