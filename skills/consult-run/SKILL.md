---
name: consult-run
description: >-
  Engagement orchestrator (the one entry an associate invokes to advance an engagement).
  Loops scripts/orchestrate.py next --engagement E --json, then performs the single returned
  action — runs the deterministic script itself, or fans out the named sub-agent skill once
  per target — walking the state-driven order ingest -> classify -> merge -> consolidate ->
  gap -> draft -> synthesize -> render, then through the review re-entry (a node re-marked
  diagnosis-dirty loops back to consolidate -> draft -> render) to the final gate. At the
  final gate it runs gates.py final-check: pass -> recommends the terminal `final` action
  (agent applies it, setting deliverable statuses final, then `next` reports `done`); fail
  -> `gate_blocked` naming the failing gates. Re-running is always safe — orchestrate.py is
  read-only and re-derives the next step from state.
---

# Skill: Consult Run — State-driven Orchestrator

## Purpose

This is the **one entry an engagement associate invokes** ("run / continue
engagement E"). It advances the engagement one step at a time and surfaces what
needs a human. It is the high-level playbook over the low-level command surface
(`state_machine.py`) and the stage scripts/skills.

This is the **state-driven** form of `orchestration_contract.md` (§3 loop, §5
dispatch, §6 gates): not a one-way pipeline. It walks the build order to the
render gate, then handles the **review re-entry** (after review edits dirty a
node, it loops back consolidate → redraft → re-render → re-review) and terminates
at a **`final` action gated by `gates.py final-check`**.

The brain is **read-only**: `scripts/orchestrate.py next` reads `status`
(`state_machine.py status`, the T04 signal) + the DoD gate (`gates.py
final-check`) and returns the **single next action**. This skill *executes* that
action — including applying the `final` action it merely *recommends*. All state
mutation is done by the named scripts / by the sub-agents' command-path
write-backs — **never by `orchestrate.py`** (it advises; it does not mutate).

## The order

```
ingest -> classify -> merge -> consolidate -> gap -> draft -> synthesize -> render
                          ^                                                    |
                          |  review re-entry (node re-marked diagnosis-dirty)  |
                          +----------------------------------------------------+
                                                                               |
                                                       final-check PASS -> final -> done
                                                       final-check FAIL -> gate_blocked
```

`orchestrate.py next` returns exactly **one** action, with its `targets` (the
docs / nodes / L1s / deliverables to act on) and its `kind` (`deterministic` or
`llm_fanout`). You execute that one action, then call `next` again. Readiness is
a first-match walk down the order, derived purely from state + on-disk classify
artifacts + deliverable MDs + the DoD gate — so the answer is stable until you
advance the state.

**`next --all`** lists **every** ready action on the frontier (not just the
first), so a multi-session run can see the whole picture (e.g. a stale re-render
owed alongside a still-draftable node). The single-action `next` follows the
same precedence; `--all` is for visibility, not a different decision.

## The loop you follow

```
loop:
    obj = run: python scripts/orchestrate.py next --engagement E --json
    if obj.action == "done":          -> STOP; engagement complete (all final, gates pass)
    if obj.action == "gate_blocked":  -> STOP; report the failing DoD gates (do NOT finalize)
    if obj.action == "final":         -> APPLY it (set statuses final, below), then loop
    if obj.action == "render":        -> run the render script, present the Word for review (gate)
    if obj.kind == "deterministic":   -> run obj.script yourself (subprocess)
    if obj.kind == "llm_fanout":      -> you MUST delegate. Invoke the named workflow
                                          `consult-fanout` (Tier 2 below) with args
                                          {engagement:E, stage:obj.action, targets:obj.targets}
                                          (for classify, also pass schema). Do NOT perform the
                                          stage's reasoning yourself. The workflow runs the
                                          classify merge itself — you do NOT run then_script.
    (state advances)                  -> loop again
```

Always re-run `next` after each action rather than assuming the order — new
evidence, review edits, or a half-done stage re-opens the right step.

## Deterministic vs LLM fan-out (the dispatch mapping)

`orchestrate.py` tags each action. **Deterministic** = you run the named Python
script directly. **LLM fan-out** = you spawn the named sub-agent skill **once
per target** (bounded concurrency; each sub-agent writes only its own artifact /
deliverable and returns a one-line summary; sub-agents never write state).

### llm_fanout is BLOCKING: you MUST delegate (not a suggestion)

When `obj.kind == "llm_fanout"` you **MUST** delegate the work to the named
sub-agent skill, **once per target**. **Performing the classify / consolidate /
draft / synthesize reasoning yourself — in this orchestrator context — is a
contract violation, not an allowed shortcut.**
This holds even for small batches of one or two targets:
"there are only a few, I'll just do it inline" is exactly the drift this rule
forbids. Do not do it.

The reason — so it is not "optimized" away:

- **Context isolation.** Each fan-out target's full inputs (ingested MD, taxonomy
  slice, per-doc reasoning) belong in an **isolated sub-agent context** that
  returns only a **one-line summary**. If you do the reasoning inline, every
  stage's full inputs pile into this single orchestrator context and are
  **re-billed on every later turn** — cost scales with accumulated context, not
  work done.
- **Isolation / parallelism / correctness.** Inlining defeats the entire point of
  the fan-out architecture (no isolation, no parallelism) and **skips the
  per-target artifact schema + `validate_artifact.py` gate** the real sub-agent
  must pass — a silent correctness drift.

**Honest scope of this rule.** This prose is a **rule / contract**; on its own a
Markdown skill cannot *mechanically* stop the model reading a file or reasoning
inline. The **structural** guarantee — where the loop-level model never receives
the content, so it *cannot* inline — is **Tier 2: the `consult-fanout`
workflow**, which has now landed (below). You delegate each `llm_fanout` action
to that workflow by name; the per-target content goes to the workers inside it,
never to this loop. The rule above still governs the rare path where you can't
invoke the workflow — but the workflow is the default, and it is what holds the
line.

### CONTENT PROHIBITION: the orchestrator stays content-starved

For an `llm_fanout` action you handle **only** the `orchestrate.py next` output
(`{action, kind, targets}`) and the workers' returned **one-line summaries**. You
do **NOT**, in this orchestrator context:

- read `ingested/*.md` (the normalized source documents),
- read the taxonomy slices or any per-node / per-doc content,
- run the input-gatherers yourself — `scripts/consolidate_inputs.py`,
  `scripts/draft_inputs.py`, `scripts/synthesis_inputs.py` (nor any other
  per-target content gather).

Those gatherers and that content **feed the delegated workers** — each sub-agent
runs its own gatherer inside its own isolated context. They are **not** inputs to
the orchestrator. (Again: a *rule*, not a physical gate — Tier 2 is what makes it
structural, by never handing the content to the loop-level model at all.)

### Tier 2: delegate via the `consult-fanout` workflow (the structural enforcement)

For every `llm_fanout` action, **invoke the `consult-fanout` workflow** (Workflow
tool) rather than hand-spawning sub-agents. It is the deterministic per-stage
fan-out: one worker per target, via the custom agent types in `.claude/agents/`,
at a conservative concurrency. You call it with:

```
workflow "consult-fanout" with args {
    engagement: E,
    stage:      obj.action,        # classify | consolidate | draft | synthesize
    targets:    obj.targets,       # docs / nodes / l1s / scope, verbatim from `next`
    schema:     <classify only>    # see below
}
```

- **Invocation surface — by name, with a scriptPath fallback.** When CONSULT is
  installed as a **plugin**, the workflow registers and resolves **by name**
  (`consult-fanout`) — use that. If your runtime has the repo open as a plain
  folder (no plugin install), the name may **not** be in the Workflow registry;
  then invoke it by **`scriptPath: .claude/workflows/consult-fanout.mjs`** instead.
  Same args either way. (Confirmed on first live run: name resolution is
  environment-dependent; the workflow itself is identical.)
- **Args may be marshalled as a JSON string** by some runtimes; the workflow
  parses either an object or a JSON string, so just pass the object above.

- **Schema (classify only) — T55 Phase 2.** When `obj.action == "classify"`, read
  `schemas/classify_artifact.schema.json` and pass it as `args.schema`. The
  workflow forwards it to each classifier as a StructuredOutput schema, so the
  per-doc artifact is **valid by construction** (no author→validate→rewrite loop).
  Read the schema file **once** here and pass it in — the workers don't re-read it;
  this is the *one* file the orchestrator reads, and it is a schema, not engagement
  content, so it does not breach the content prohibition.
- **Merge ownership.** The workflow runs the classify `merge` itself as its
  post-step. **You do NOT run `classify_merge.py merge`** for a classify fan-out —
  doing so would double-merge. (The standalone deterministic `merge` *action* from
  `next` is unaffected; that is a separate, non-fan-out step.)
- **Consolidate / draft / synthesize** have no post-step — their workers apply /
  write inline. Just invoke the workflow and re-run `next`.
- **Cost map — T56.** The workflow returns a `cost` object
  (`{stage, targets, outputTokensDelta}`). Append it to
  `engagements/E/cost_map.json` (a content-free per-stage list: stage, #targets,
  Δoutput-tokens — **no document content**). This is the measured per-phase cost
  the acceptance check reads; the workflow can't write files, so you persist it.
- **Human gate unchanged.** The workflow runs **one stage and returns** — it never
  advances, renders, or finalizes. You stay the gate-respecting loop: after it
  returns, re-run `next` and handle render / `needs_human` / `final` as before.

| action | kind | what you run |
|---|---|---|
| `ingest` | deterministic | `scripts/ingest_normalize.py ingest --engagement E --source PATH...` |
| `classify` | **llm_fanout** | via `consult-fanout` (stage=classify): one `consult-classifier` per `targets.docs` doc; the **workflow** runs `classify_merge.py merge` as its post-step (you do **not**) |
| `merge` | deterministic | `scripts/classify_merge.py merge --engagement E` |
| `consolidate` | **llm_fanout** | `consult-consolidator` once per `targets.nodes` dirty node |
| `gap` | deterministic | `scripts/gap_report.py scan --engagement E` |
| `draft` | **llm_fanout** | `consult-drafter` **and** `consult-improvement-drafter` once per L1 bundle in `targets.l1s` |
| `synthesize` | **llm_fanout** | `consult-synthesizer` (engagement-level; authors `deliverables/synthesis.md`) |
| `render` | deterministic | `scripts/render_deliverables.py render --engagement E --what all` → present Word for review (**human gate**) |
| `final` | deterministic | **you apply it**: `state_machine.py set-sop/set-improvement --node KEY --status final` per `targets.deliverables` (DoD gate already passed) |
| `gate_blocked` | — | DoD `final-check` failed; stop and report the failing gates in `targets.failing_gates` (do **not** finalize) |
| `done` | — | engagement complete: all deliverables final and DoD gates pass; stop and report |

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

## The render gate (the human hand-off)

When `next` returns `action: render` it carries `gate: "render"`. Run
`render_deliverables.py` to produce the `.docx` deliverables, then **present the
rendered Word for human review**. The agent does not self-finalize from a fresh
render: review happens against the Word. The render action fires both for a first
render (MD present, no `.docx`) **and** for a re-render owed after a redraft (a
per-L1 stream whose content `rev` is ahead of its `rendered_rev` — the review
re-entry path below).

The other reasons to stop and report mid-loop are the human-input signals in
`status.needs_human` (conflict gaps, unmapped rows pending an owner,
`requires_human_review`) — surface them; do not push past them.

## The review re-entry (looping back after review)

Review edits are ingested (T31, out of scope here) and applied via the command
path. When a review correction changes a node's substance, the ingest path
`mark-dirty`s that node (stamps `last_evidence_at = now`), so it becomes
**diagnosis-dirty** again (`last_evidence_at > consolidated_at`). On the next
`next`, even though deliverables are already rendered, the loop **does not report
done** — it returns `consolidate` for that node, re-entering the build:

```
review marks node dirty  ->  consolidate (re-write node MD, mark-consolidated)
                         ->  draft (the affected L1 streams redraft; rev bumps)
                         ->  render (rev > rendered_rev -> re-render that stream)
                         ->  back to the final gate
```

This is the same machinery as a new document arriving mid-engagement: dirtiness
and rev/rendered_rev drive the right re-work without disturbing settled streams.

## The final gate (`gates.py final-check` — the terminal step)

Once everything is rendered and no stream is stale (no node diagnosis-dirty,
nothing left to draft/render), `next` consults **`gates.py final-check`** (the
DoD gates: unmapped rows dispositioned, zero open `requires_human_review`,
evidence refs resolve, final artifacts have paths):

- **final-check PASSES** → `next` returns `action: final` (`kind: deterministic`,
  `gate: final`). **You apply it**: for each `{node, block}` in
  `targets.deliverables`, run `state_machine.py set-sop` / `set-improvement
  --node KEY --status final`. Then call `next` again — it returns `done`.
  `orchestrate.py` itself never sets `final`; it only recommends it.
- **final-check FAILS** → `next` returns `action: gate_blocked` (`gate: final`)
  with the failing gate names in `targets.failing_gates`. **Stop and report**
  them; do **not** advance to `final`. Run `gates.py final-check --engagement E`
  for the per-failure detail, clear the gate(s), then re-run.
- **`done`** → all started deliverable blocks are `final` and the gates pass; the
  engagement is complete. Stop and report.

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
- New documents **or review edits** mid-engagement re-open the relevant steps
  (new docs become un-classified; affected nodes become diagnosis-dirty;
  redrafted streams go stale vs `rendered_rev`) without disturbing settled work
  — so a second `consult-run` session is always correct.
- **The terminal gate is re-derived, not latched.** `final` is recommended only
  while the gates pass and deliverables are not yet final; `gate_blocked` only
  while a gate fails. Re-running after clearing a gate flips `gate_blocked` →
  `final` deterministically. Applying `final` (statuses → final) flips `final` →
  `done`. There is no point at which re-running is unsafe.

## Scripts & skills this names (all real, all committed)

- Scripts: `scripts/orchestrate.py`, `scripts/state_machine.py`,
  `scripts/gates.py` (the `final-check` DoD gate), `scripts/ingest_normalize.py`,
  `scripts/classify_merge.py`, `scripts/consolidate_inputs.py`,
  `scripts/gap_report.py`, `scripts/draft_inputs.py`,
  `scripts/synthesis_inputs.py`, `scripts/render_deliverables.py`.
- Skills: `consult-classifier`, `consult-consolidator`, `consult-gap-analyzer`,
  `consult-drafter`, `consult-improvement-drafter`, `consult-synthesizer`.

(`consult-gap-analyzer` is the substantive gap-analysis sub-agent that runs over
the same nodes; the Slice-1 deterministic `gap` action is the structural scan
`gap_report.py scan`.)
