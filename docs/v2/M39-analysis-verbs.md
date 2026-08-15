# M39 — Analysis verbs: findings over the brain

> **Status: BUILT (2.0.0-alpha.9)** — `scripts/findings.py` (the lifecycle
> M30 A1 deferred: FIND- ids, grounds-or-refused with engagement-wide
> resolution, terminal reject, accepted-only renderability, the
> one-direction rule structural and fingerprint-pinned),
> `scripts/analysis.py` (three declaration-driven read-only candidate
> generators), `kernel/deliverables/findings-report.yaml` (the findings
> verb, accepted-only enforced at load), `agents/consult-analyst.md`
> (the one assessment license). Gates: `tests/test_findings_m39.py`
> 11/11; suite 1056 passed, 1 pinned xfail. Build records:
> [`M39-build-plan.md`](M39-build-plan.md),
> [`notes/m39-analyst-self-review.md`](notes/m39-analyst-self-review.md).
>
> **Amendment A1 (build notes, 2026-08-15):** (1) findings live at the
> engagement-root `_registers/findings.yaml` — the one-direction rule
> overrode M30's register home (which is under `components/`);
> (2) grounds resolve against ledger ∪ declaration-parsed corpus ∪
> manifests, assembled per call, no labels typed; (3) the pain kind is
> derived by subtraction across shipped definitions — honest but
> indirect; a semantic marker on callout declarations is the recorded
> clean fix; (4) rendering the findings report end-to-end waits on the
> M38-recorded definition-views-to-manifest gap; (5) follow-ups
> recorded: an `analysis.py brief` CLI, the analyst dispatch hint, a
> `conflict_records` extractor (verb 3's material), severity/resolution
> slots on propose, owner-change detection, engagement-wide pain
> clustering; (6) findings serviceability is engagement-uniform — the
> per-area observations appendix needs an area filter on the verb. Companions: M33 (the graph
> these verbs read; PAIN callouts are their named raw material), M30 (the
> register machinery findings land in), M37 (whose conflicts and coverage
> feed the analysis substrate; whose observe-never-adjudicate line this
> ticket is the licensed exception to), M35 (findings reports are
> deliverable definitions). Charter: [`README.md`](README.md).

## The problem this solves

By this point in the spine the brain is full of deliberately unassessed
material: PAIN callouts captured in the interviewee's framing, GAP
callouts, `conflicted` coverage, control assignments, IPO edges. Every
agent upstream is contractually forbidden from judging it — the drafter
observes, the surveyor flags, the librarian proposes structure. That
discipline is what keeps the capture layer trustworthy, and it leaves the
actual consulting question — *what does this all mean, and what should the
client do?* — with no home.

v2's answer (charter): **analysis is a distinct consumer class.** Analysis
verbs read the graph and emit **findings** — a new register-class citizen
— never touching entities, never editing views, never rendering. Findings
then feed findings-shaped deliverables through the ordinary M35 path.

## Part A — The finding: what it is and where it lives

A finding is a register entry (M30 machinery, third entry class alongside
citable/context): stable id, the CLAIM (the analyst's assessment, in the
system's voice — the first place the system is allowed one), **grounds**
(the SRC ids, PAIN/GAP callout ids, entity slugs, and coverage facts it
rests on — every finding traces or it does not exist), severity/theme
tags, and status (`proposed` → human-confirmed → `accepted`/`rejected`).

- **The human gate is the M30 conversation, reused**: analysis proposes;
  the human accepts, edits, or rejects in chat; the register verb writes.
  A finding never reaches a rendered deliverable before acceptance.
  (M30 A1 deferred the entry lifecycle — `proposed`/`confirmed` status —
  as "build only if noise materializes." Findings are that
  materialization: **this ticket builds the deferred lifecycle**, for the
  findings class at minimum; extending it to citable entries stays
  M30-deferred.)
- Findings live in an engagement `findings` register. The register verb
  refuses a finding without grounds — the M30 A1 provenance discipline,
  verbatim.
- **Findings never flow back into the capture layer.** No note, no edit,
  no callout is generated from a finding into any entity — the brain
  records what IS; findings record what the system THINKS. One direction.
  (The one exception: a finding may propose an information request, which
  follows the M37 request path — asking for more evidence is not
  assessment.)

## Part B — The verbs (shipped set, bounded)

Each verb is one dispatch pattern: deterministic Python assembles the
relevant subgraph into a brief; an analysis agent (one new agent
definition, `consult-analyst`, mode-scoped like the drafter) judges;
proposals land as `proposed` findings. The shipped set is exactly what the
captured material supports:

1. **Pain synthesis** — cluster PAIN callouts across the engagement
   (same friction voiced in three areas is one theme, evidenced thrice);
   propose themed findings with all voices cited.
2. **Control coverage** — mechanical candidate generation (steps with
   material outputs and no CTRL; taxonomy nodes whose steps are
   control-thin — a Python pass over the graph), agent judgment on which
   candidates matter; propose gap findings.
3. **Conflict adjudication support** — for M37 `conflicted` facts: lay
   out both claims, their sources, and what each would imply — proposing
   a RESOLUTION QUESTION, not a resolution (the human or the client
   resolves; the licensed-exception boundary stops here).
4. **Handoff friction** — IPO-edge analysis: outputs nobody consumes,
   inputs nobody produces, steps whose owner changes mid-artifact —
   mechanical detection, agent-judged materiality.

Verbs 2 and 4 are mostly Python with a judgment pass on top — the
house pattern (mechanical candidates, bounded judgment). New verbs beyond
these four are future tickets, not configuration; the analysis surface
grows deliberately.

## Part C — Findings-shaped deliverables

Shipped with this ticket: `kernel/deliverables/findings-report.yaml` — an
M35 definition binding accepted findings, grouped by theme, each with its
grounds rendered as citations back through the SRC chain. The charter's
"multiple forms of analysis" lands as: capture once, analyze into
findings, render findings through any definition. (An observations
appendix for the desktop procedure — accepted findings relevant to one
area — is a three-line binding away and ships as a worked example of
definition composition.)

## Acceptance sketch (firm up at build time)

- The findings register class round-trips through the M30 verb: propose →
  list → accept/reject; groundless finding refused; `proposed` findings
  excluded from every render binding (the lifecycle M30 A1 deferred,
  built here).
- Each shipped verb, over the M38 IPO fixture (seeded with clusterable
  pains, a control-thin step, one conflict, one orphan output): produces
  `proposed` findings whose grounds resolve — every cited id exists (a
  reconcile-grade check).
- One-direction audit: a full analysis pass leaves every entity, view,
  and note file byte-identical (asserted mechanically).
- The findings report renders from accepted findings only; a rejected
  finding appears nowhere.
- `consult-analyst` is model-pinned and brief-fed like the other workers;
  its contract carries the assessment license and its boundary (proposes
  findings; resolves nothing; writes nothing).
- v1 suite green.

## Complexity accounting (the standing test)

New state files: zero (findings ride the existing register machinery).
New gates: zero (the M30 conversation gate is reused). New agent judgment:
one agent with ONE license — assess, propose, never write, never resolve
— which is the whole point of the ticket and is fenced by the register
verb's refusals plus the one-direction audit. The review risk to police:
**assessment leaking upstream** — an analyst note that "fixes" a drafter's
framing, a finding that edits a pain's wording at citation time, any path
by which the system's opinion contaminates the record of what was said.
The one-direction audit exists to catch exactly this.

## Deferred (recorded, not built)

- **Future-state / recommendation deliverables** — findings say what is
  wrong; recommendations say what to build. A distinct consulting product
  with its own discipline questions; a future ticket cluster, not a verb.
- **Benchmark-informed analysis** (findings graded against external
  practice libraries) — needs a licensing/provenance story for the
  external material first.
- **User-defined verbs** — same posture as M35's user-authored agent
  views: powerful, sharp, needs the shipped experience first.
