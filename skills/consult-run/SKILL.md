---
name: consult-run
description: Slice-1 engagement orchestrator (the one entry an associate invokes to advance an engagement). Loops scripts/orchestrate.py next --engagement E --json, then performs the single returned action — runs the deterministic script itself, or fans out the named sub-agent skill once per target — walking the fixed linear order ingest -> classify -> merge -> consolidate -> gap -> draft -> synthesize -> render -> done. Stops at the render gate (renders deliverables to Word, then reports; never auto-finalizes, never ingests review). Re-running is always safe — orchestrate.py is read-only and re-derives the next step from state.
---

# Skill: Consult Run — Slice-1 Linear Orchestrator

## Purpose

This is the **one entry an engagement associate invokes** ("run / continue
engagement E"). It advances the engagement one step at a time and surfaces what
needs a human. It is the high-level playbook over the low-level command surface
(`state_machine.py`) and the stage scripts/skills.

This is the **Slice-1 LINEAR** form of `orchestration_contract.md` (§3 loop, §5
dispatch, §6 gates): a **one-way walk** in a fixed order that **stops at the
render gate**. The state-driven readiness loop, review ingestion, and the DoD
`final` gates are S2 (T37+) and explicitly out of scope here.

The brain is **read-only**: `scripts/orchestrate.py next` reads `status`
(`state_machine.py status`, the T04 signal) and returns the **single next
action**. This skill *executes* that action. All state mutation is done by the
named scripts / by the sub-agents' command-path write-backs — never by
`orchestrate.py`.

## The linear order

```
ingest -> classify -> merge -> consolidate -> gap -> draft -> synthesize -> render -> done
```

`orchestrate.py next` returns exactly **one** of these as `action`, with its
`targets` (the docs / nodes / L1s / deliverables to act on) and its `kind`
(`deterministic` or `llm_fanout`). You execute that one action, then call `next`
again. Readiness is a first-match walk down the order, derived purely from state
+ on-disk classify artifacts + deliverable MDs — so the answer is stable until
you advance the state.

## The loop you follow

```
loop:
    obj = run: python scripts/orchestrate.py next --engagement E --json
    if obj.action == "done":            -> STOP; report the render gate (below)
    if obj.action == "render":          -> run the render script, then STOP at the gate (below)
    if obj.kind == "deterministic":     -> run obj.script yourself (subprocess)
    if obj.kind == "llm_fanout":        -> spawn obj.skill once per target, bounded
                                            concurrency; for classify, run obj.then_script after
    (state advances)                    -> loop again
```

Always re-run `next` after each action rather than assuming the order — new
evidence or a half-done stage re-opens the right step.

## Deterministic vs LLM fan-out (the dispatch mapping)

`orchestrate.py` tags each action. **Deterministic** = you run the named Python
script directly. **LLM fan-out** = you spawn the named sub-agent skill **once
per target** (bounded concurrency; each sub-agent writes only its own artifact /
deliverable and returns a one-line summary; sub-agents never write state).

| action | kind | what you run |
|---|---|---|
| `ingest` | deterministic | `scripts/ingest_normalize.py ingest --engagement E --source PATH...` |
| `classify` | **llm_fanout** | `consult-classifier` once per `targets.docs` doc → **then** run `scripts/classify_merge.py merge --engagement E` (`then_script`) |
| `merge` | deterministic | `scripts/classify_merge.py merge --engagement E` |
| `consolidate` | **llm_fanout** | `consult-consolidator` once per `targets.nodes` dirty node |
| `gap` | deterministic | `scripts/gap_report.py scan --engagement E` |
| `draft` | **llm_fanout** | `consult-drafter` **and** `consult-improvement-drafter` once per L1 bundle in `targets.l1s` |
| `synthesize` | **llm_fanout** | `consult-synthesizer` (engagement-level; authors `deliverables/synthesis.md`) |
| `render` | deterministic | `scripts/render_deliverables.py render --engagement E --what all` → then **GATE** |
| `done` | — | render gate reached; stop and report |

Notes on the fan-out stages (each fronted by a read-only input gatherer the
sub-agent consumes, so it does not forage):

- **classify** — `consult-classifier` per ingested MD writes
  `classify/{hash}.artifact.json`; the deterministic `classify_merge.py` runs
  **after** the whole fan-out (it applies evidence + lenses; candidate findings
  stay staged).
- **consolidate** — `consult-consolidator` per diagnosis-dirty node; inputs from
  `scripts/consolidate_inputs.py gather --engagement E --node KEY`. Writes the
  node MD and confirms findings via the command path; the loop re-derives
  dirtiness from `mark-consolidated`.
- **draft** — per L1: `consult-drafter` (SOP, Stream A) + `consult-improvement-drafter`
  (improvements, Stream B); inputs from `scripts/draft_inputs.py gather
  --engagement E --l1 L1`.
- **synthesize** — `consult-synthesizer`; inputs from
  `scripts/synthesis_inputs.py gather --engagement E`. Authors the lead
  `deliverables/synthesis.md` and lifts `type:theme` rows.

## The render gate (the hard stop in Slice 1)

When `next` returns `action: render` it carries `gate: "render"`. Run
`render_deliverables.py` to produce the `.docx` deliverables, then **STOP and
report** — present the rendered Word for human review. The agent **does not
self-finalize**: there is no review ingestion, no `final` assembly in Slice 1
(those are S2). When the next call returns `action: done` (also `gate: render`),
all built deliverables are rendered; report the gate and stop.

The only other reasons to stop and report mid-loop are the human-input signals
in `status.needs_human` (conflict gaps, unmapped rows pending an owner,
`requires_human_review`) — surface them; do not push past them.

## Idempotency & re-running is safe

- **`orchestrate.py next` is READ-ONLY** — it writes nothing (not `state.json`,
  not `register.json`, not deliverables). Calling it on every loop iteration
  leaves the engagement byte-identical.
- **Every action is re-runnable.** Readiness is re-derived from state each loop,
  so a new session, a crash, or new documents arriving just continues:
  ingest dedups by source hash; classify counts a doc done only once its
  artifact exists; merge re-resolves from the full artifact set; consolidate is
  gated by `consolidated_at` vs `last_evidence_at`; gap scan upserts/self-heals;
  render skips missing MDs and re-renders present ones.
- New documents mid-engagement re-open the relevant steps (those docs become
  un-classified; affected nodes become diagnosis-dirty) without disturbing
  settled work — so a second `consult-run` session is always correct.

## Scripts & skills this names (all real, all committed)

- Scripts: `scripts/orchestrate.py`, `scripts/state_machine.py`,
  `scripts/ingest_normalize.py`, `scripts/classify_merge.py`,
  `scripts/consolidate_inputs.py`, `scripts/gap_report.py`,
  `scripts/draft_inputs.py`, `scripts/synthesis_inputs.py`,
  `scripts/render_deliverables.py`.
- Skills: `consult-classifier`, `consult-consolidator`, `consult-gap-analyzer`,
  `consult-drafter`, `consult-improvement-drafter`, `consult-synthesizer`.

(`consult-gap-analyzer` is the substantive gap-analysis sub-agent that runs over
the same nodes; the Slice-1 deterministic `gap` action is the structural scan
`gap_report.py scan`.)
