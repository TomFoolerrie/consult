# Evaluation — CONSULT × the Consulting Skill Chain

*2026-07-31. Evaluates the `skillchainhandoff` bundle (26 skills, 8 layers,
typed contracts, plus an orchestrator design note) against CONSULT as built
(v1.17.2, M0–M30), and recommends how to build on the consult idea with it.*

---

## What arrived

The handoff bundle contains:

- **The chain**: 26 prompt-only skills spanning the full engagement lifecycle
  — L1 Discovery → L2 Analysis → L3 Synthesis → L4 Deliverables → L5 Quality,
  plus governance, cross-cutting (client-researcher, proposal-framer), and two
  optional CFGI brand renderers. Skills interact only through 8 named contract
  types (`discovery-output`, `context-profile`, `analysis-output`,
  `assessment-output`, `research-output`, `synthesis-output`,
  `deliverable-content`, `quality-pass`).
- **`chain-graph.yaml`**: a first pass at the dependency graph as data.
  Explicitly unvalidated — the `consumes` edges were inferred from skill
  descriptions, not read out of the SKILL.md bodies.
- **`ORCHESTRATOR-DESIGN.md`**: a concept note for a chain orchestrator.
  Nothing built.

## The two systems, honestly compared

They are opposite postures applied to the same profession:

| | CONSULT | Skill chain |
|---|---|---|
| Shape | Deep and narrow — one deliverable class (governed desktop procedures), 30 milestones deep | Broad and shallow-per-node — the whole engagement lifecycle, one SKILL.md per stage |
| State | Durable, on disk, per area; git-historied; hash-signalled | Conversation-scoped; contracts are inline markdown blocks |
| Contracts | Machine-parsed, fail-loud (strict ID grammar, `consult-meta` slug binding, reconcile constitution) | Prose conventions with an HTML-comment header; "typed" by discipline, not enforcement |
| Failure posture | Fail loud, never guess, never drop | Graceful degradation — every skill accepts raw input when its contract input is missing |
| Traceability | Every claim cites an `SRC-` id; register citation gate (M29/M30); named-individual scan | "Source attribution" requested in output templates, unenforced |
| Orchestration | Built: read-only state advisor, isolated subagents, human gates, waves | A design note listing this as future work |
| Coverage | Current-state documentation of finance areas | Everything from intake to steering-committee deck to proposal |

Neither subsumes the other. The chain is a **coverage** asset; CONSULT is a
**governance** asset.

## Core finding 1 — the orchestrator the note asks for already exists here

`ORCHESTRATOR-DESIGN.md` lists five functions and three open questions. Every
one of them is something CONSULT has already built and hardened, usually after
learning the failure mode the hard way:

| Orchestrator note asks for | CONSULT already has |
|---|---|
| Backward resolution from a goal; "what do I have vs. need" | `orchestrate.py` — the read-only state advisor deriving the single next action from folder state (M7, M18 honesty invariant) |
| Gap detection before burning a synthesis pass | Stage gates (M17) — the draft-ready boundary exists precisely so the "am I happy with the verbs and nouns?" decision lands *before* the spend |
| Parallel fan-out with merge | One drafter per procedure, wave-ordered by `upstream:` hints (M11) |
| Enforcement of always-run passes ("trigger-based activation gets skipped") | The reconcile constitution (M22/M29): invariants are *policed at render*, not requested in prompts. This is exactly the fix for the chain's writing-scrubber problem |
| Context-profile propagation into every invocation | Engagement-level `_client/` config resolution (M13) + document profile (M14) |
| Open question: where does it live? "Probably not a skill" | Answered: a skill that is a *thin coordinator* over a deterministic advisor + isolated subagents — the skill only triggers; the advisor decides |
| Open question: context accumulation | Answered: disk-backed state, compact subagent returns, "never pull transcripts or draft text into your own context" |
| Open question: registry as data, prose generated from it | Answered in principle: "two databases, everything else is a view" — the chain's registry/graph dual-maintenance problem is the exact drift class CONSULT's thesis eliminates |
| "Don't let the orchestrator write content" | The context-isolation rule, load-bearing since M7 |

The v0 retrospective is also directly on point: CONSULT's first architecture —
a shared mutable state machine — is roughly what a naive chain orchestrator
would become, and it cost an entire hardening slice before being replaced.

**Conclusion: do not build the orchestrator described in the note as a second
system. CONSULT *is* that orchestrator, one abstraction level down.** The
question is not "how do we build the chain's orchestrator" but "how does
CONSULT's engagement model grow to cover chain stages."

## Core finding 2 — CONSULT ends exactly where the chain begins to add value

CONSULT's scope boundary is stated in its own docs: *"Cross-area
prioritization / effort×impact roadmap is a separate decision deliverable, out
of MVP scope."* The chain is precisely that decision deliverable pipeline:
findings-consolidator → tom/process/roadmap/change → exec-deck-builder /
memo-brief-writer → quality → CFGI renderers.

And CONSULT already produces, mechanically and with provenance, the exact
inputs those skills want:

| CONSULT artifact | Chain contract it maps to |
|---|---|
| Appendix A — PP/IO register (observation, impact, severity, `[[slug]]`) | The findings section of `discovery-output` / the seed of `analysis-output` |
| Appendix B — gap log (`GAP-`, nature, owner-to-confirm) | `discovery-output` "dark spots / contradictions / missing artifacts" |
| Systems view + registry (`systems.yaml` descriptions, limitations, aliases) | The system-landscape half of `discovery-output` |
| Role dictionary + RACI | Org/actor input to `analysis-output`, tom-designer, change-planner |
| Key Dependencies | Process-interaction input to process-designer and roadmap-builder |
| `_reference/sources.yaml` (SRC- ids, hashes, touches) | The evidence-tracing layer findings-consolidator asks for but cannot enforce |
| `_client/` engagement config (M13) | `context-profile` — same role: calibration injected everywhere, not a gate |
| Engagement registers (M30 citable/context classes, citation gate) | The enforced version of the chain's "Evidence base: … with source attribution" |

A CONSULT area is, in chain terms, **the most evidence-governed
`discovery-output` + partial `analysis-output` producer available** — every
finding traceable to a source line, mechanically aggregated, human-gated.
Feeding the chain from anything less (raw transcripts straight into
interview-synthesizer) throws that governance away for finance-process
engagements.

## The seam, and the rule for it

The two failure postures must not blend. CONSULT's value is fail-loud;
the chain's value is forgiving coverage. The clean boundary is a **contract
instance as a file**: inside CONSULT everything stays policed by reconcile;
what crosses the seam is a rendered contract document (the chain's own
`<!-- type: … -->` block format), derived — never hand-written — from the two
databases. It is a view, so the existing thesis covers it: regenerate, never
patch.

What should *not* cross the seam inward: the chain's "accepts raw input when
contract input is missing" philosophy. Nothing inside CONSULT should ever
degrade gracefully; degradation is for the conversation layer outside.

## Options considered

**A. Extend CONSULT to swallow the chain** — re-implement chain stages as
CONSULT agents/milestones. Rejected for now: the chain's judgment-heavy
synthesis skills (pyramid arguments, TOM patterns, CRAFT narrative) are
genuinely conversation-shaped; forcing them into one-writer-per-file
governance before the seam is proven would be M-numbered scope explosion.

**B. Build the note's standalone orchestrator over the chain** — rejected:
duplicates CONSULT, and would re-learn the v0 lessons (shared state, prose
scraping, trigger reliability) from scratch.

**C. Bridge first, converge later** — CONSULT exports contract instances; the
chain consumes them; governance patterns migrate into the chain incrementally.
**Recommended.** Cheapest step is deterministic Python over data CONSULT
already aggregates, and it is immediately useful even if nothing else is ever
built.

## Recommended build order

1. **`scripts/export_contracts.py` — the bridge (small, deterministic, no new
   agent).** Given an area at/past the draft-ready gate, emit
   `_deliverables/contracts/discovery-output_<area>.md` (and an
   `analysis-output` seed) in the chain's block format, projected from the
   PP/IO register, gap log, systems/roles views, dependencies, and
   `sources.yaml`. Every finding row carries its `(slug, id)` and `SRC-`
   citations. It is a derived view with `writer: python` and a derived marker,
   so reconcile governs it for free. This makes any installed chain skill
   usable against a CONSULT area *today* by pasting or referencing the file.

2. **Validate `chain-graph.yaml` before anything routes on it.** The handoff
   itself flags the `consumes` edges as the load-bearing risk. Mechanical
   check: parse each SKILL.md's `Contracts:` section (they are consistently
   formatted) and diff against the graph. Fits in a small script; the two
   chain-adjacent excluded skills (enterprise-ai-advisor, ai-use-case-assessor)
   get an explicit in-or-out decision at the same time.

3. **Apply the CONSULT thesis to the chain's governance.** Make the validated
   graph the database and *generate* the registry prose and MASTER-INDEX from
   it — retiring the "registry must stay current" dual-maintenance rule the
   manifest itself worries about. This is the same move as manifest→views and
   costs little once step 2's parser exists.

4. **Inbound calibration: `context-profile` → `_client/`.** Accept a
   company-profiler output as a human-confirmed file under the engagement
   `_client/` config (M13 already resolves engagement-level context across
   areas). Human-dropped, never agent-written — consistent with the existing
   `_client/` ownership rule.

5. **Only then, orchestrated chain stages.** Wrap the highest-value downstream
   path (findings-consolidator → roadmap-builder → exec-deck-builder) as
   dispatched subagents consuming contract files and writing contract files,
   with the writing-scrubber pass enforced as a render gate rather than a
   trigger. This is where the chain's "always-run passes get skipped" problem
   gets the reconcile treatment. Do not start here; steps 1–2 de-risk it.

## Risks and cautions

- **Contract blocks are still prose.** Downstream chain skills will not
  fail-loud on a malformed contract; the bridge must therefore be the only
  producer on the CONSULT side (never hand-edited), and the export format
  pinned by a golden fixture like every other view.
- **Severity/impact vocabularies differ** (CONSULT PP severity enum
  High/Medium/Low vs. the chain's per-skill scales). Map explicitly in the
  exporter; don't let two vocabularies coexist in one document.
- **CFGI branding exists in both stacks** (docx builder here; pptx
  style/html-bridge there). Keep both as render-layer-only — the chain already
  isolates branding to folder 07, matching CONSULT's render-time-only rule.
  Deck rendering should stay downstream of `deliverable-content`, not become a
  CONSULT view.
- **Don't regress the intake path.** For finance-process engagements, raw
  sources should keep entering through `_sources/new/` and taxonomy — not
  through the chain's L1 skills — or the citation gate and touches-tagging are
  bypassed. The chain's L1 remains the right front door only for engagement
  types CONSULT doesn't model.

## Bottom line

The handoff doesn't compete with CONSULT — it maps the territory around it.
CONSULT already is the orchestrator the handoff's design note wishes for, and
the chain already is the downstream engagement coverage CONSULT declared out
of scope. Building on the consult idea means joining them at one seam: a
deterministic contract exporter (step 1) plus a validated graph (step 2),
after which every further step is optional and independently valuable.
