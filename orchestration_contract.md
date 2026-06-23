# CONSULT — Orchestration Contract

> Status: **BUILT** (implemented by `scripts/orchestrate.py`). Resolves the open "orchestration form" decision
> (`spec.md` §10). Sits above the stage contracts (`ingest_contract.md`,
> `classify_contract.md`) and the command surface (`consult-state-machine`).

## 1. The decision: agent-driven, state-driven

**Form:** a **`consult-run` skill the agent follows**, backed by Python helpers for the
deterministic glue. Not a pure-Python driver (Python can't spawn the Claude sub-agents the
LLM stages need), not CLAUDE.md-as-orchestrator (always-on context bloat; orchestration is
*invoked*, not ambient).

**Control model: state-driven, not a linear pipeline.** The orchestrator does **not** run
"stage 1 → 2 → 3." It asks *"what does the engagement state need next?"*, does that, and
repeats. This is what makes a long-running, multi-session engagement **resumable and
idempotent** — pick up any time, derive the next action from state, never replay from the top.

Why it matters: an engagement spans days and many sessions; documents arrive in waves; a stage
may be half-done. A linear script would be wrong on the second session. A state-driven
controller is always correct: it reads where things are and advances them.

## 2. Persona & invocation

- **Persona:** an engagement associate or lead — not a developer. They drop files in and ask
  the system to advance the engagement and surface what needs human input.
- **Invocation:** one entry — `consult-run` (e.g. "run/continue engagement {id}"). The agent
  then loops the control model until it reaches a **human gate** or there is nothing left to
  do, and reports a concise status + what it needs from a human.
- `consult-state-machine` remains the low-level command surface `consult-run` calls; this skill
  is the high-level playbook.

## 3. The control loop

```
load status(engagement)         # one read: what's where (see §4)
while an automatable step exists and no gate blocks:
    pick the highest-priority ready step (§5)
    execute it (deterministic script, or spawn LLM sub-agents)
    (state advances; re-derive)
report: progress + the next human action (review / decision / missing input)
```

The loop is **declarative**: each step's readiness is a predicate over state. Re-running
`consult-run` after a crash, a new session, or new documents simply re-derives readiness.

## 4. The `status` / `next` command (what the agent polls)

A read-only reporting command (extends `state_machine.py`, reads state + register + the ingest
manifest + the `classify/` artifacts) that returns, per engagement, the actionable picture —
so the agent decides what's next from **one compact read**, never by scanning everything:

- ingested docs in the manifest **not yet classified** (no artifact for their hash)
- **diagnosis-dirty** nodes (`node.last_evidence_at > node.consolidated_at`) — new *evidence*
  since the last synthesis (NOT generic `updated`, which any edit bumps)
- nodes needing **gap scan** / with open structural or conflict gaps
- nodes ready to **draft** (covered enough, per DoD); per-stream progress markers:
  `sop.status` (Stream A) and `improvement.status` (Stream B) — both carry `rendered_rev` /
  `reviewed_rev` so the loop can tell "drafted" vs "rendered, awaiting review" vs "review
  ingested, needs redraft"
- **gate status**: evidence-auditor pass? open `requires_human_review` / SME items? unmapped
  rows not **dispositioned** (not merely owned)?
- **what needs a human**: contradictions (conflict gaps), review rounds pending, unmapped triage

## 5. Stage dispatch (readiness → action)

| When state shows… | Action | Kind |
|---|---|---|
| new files dropped, not in manifest | `ingest_normalize.py` (immutable, hashed) | Python |
| ingested docs without a classify artifact | fan out **classify** sub-agents (one per doc, bounded) → artifacts | LLM |
| classify artifacts present, unmerged | `classify_merge.py` (evidence + lenses; stage findings) | Python |
| nodes with new evidence, stale MD | **consolidate** sub-agent per L2 (write node MD; confirm findings → `add-item`) | LLM |
| any time after consolidation | `gap_report.py scan` (structural + unmapped triage) | Python |
| nodes covered per DoD, `sop` not final | **draft** 5A/5B per L1 bundle | LLM |
| drafts ready | render Word (per L1), present for **human review** → **GATE** | Python + human |
| reviewed Word returned | **review-comment-resolver** ingest → apply via commands | LLM |
| gates satisfied | assemble **final output** | Python |

## 6. Fan-out & gates

- **Fan-out discipline:** classify spawns one sub-agent per un-classified doc, **bounded
  concurrency**; each writes its artifact and returns a one-line summary; the deterministic
  merge runs after. Consolidate similarly fans per dirty L2. Sub-agents never write state.
- **Human gates (the loop stops and reports):** (1) after drafts are rendered to Word — the
  agent does not self-finalize; (2) when a contradiction/conflict gap needs human lens
  resolution; (3) unmapped rows needing an owner; (4) before `final`, the DoD gates
  (evidence-auditor pass, zero open SME/`requires_human_review`). The agent surfaces these;
  it never pushes past them.

## 7. Idempotency & resumability

Every step is safe to re-run; readiness is re-derived from state each loop, so a new session
or a crash just continues. New documents arriving mid-engagement re-open the relevant steps
(those docs become "un-classified"; affected nodes become "dirty") without disturbing settled
work. Machine records use stable ids; ingested artifacts are immutable — so re-derivation
never duplicates or rots references.

## 8. Bookkeeping this requires (small additions)

- **`node.last_evidence_at`** + **`node.consolidated_at`** (state) — the evidence-specific
  diagnosis-dirty signal (`last_evidence_at > consolidated_at`). Set by `add-evidence` and
  consolidate respectively. (Both added to `engagement_state.schema.json`.)
- **Per-stream progress** — `sop.{rendered_rev,reviewed_rev}` (exists partly via `sop.rev`) and
  a parallel **`improvement.{status,rendered_rev,reviewed_rev}`** for Stream B (Stream B has no
  node status today — a build prerequisite for a resumable multi-round loop).
- **classified set** — derivable from `classify/{hash}.artifact.json` existing vs the manifest's
  active set (no new field needed).
- The **`status`/`next`** reporting command itself.

## 9. To validate during the vertical slice

- Does state carry enough signal to derive "what's next" unambiguously, or do we need more
  per-node progress markers beyond `consolidated_at`?
- Right gate set? Is "stop after drafts for human review" the only hard gate, or also after
  classify (to sanity-check the diagnosis before drafting)?
- Bounded-concurrency number for classify fan-out on a realistic doc count.
- Does the associate-facing status report read clearly enough to act on without internals?
