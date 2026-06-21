---
name: consult-run
description: Engagement orchestrator (the one entry an associate invokes to advance an engagement). Loops scripts/orchestrate.py next --engagement E --json, then performs the single returned action — runs the deterministic script itself, or fans out the named sub-agent skill once per target — walking the state-driven order ingest -> classify -> merge -> consolidate -> gap -> draft -> synthesize -> render, then through the review re-entry (a node re-marked diagnosis-dirty loops back to consolidate -> draft -> render) to the final gate. At the final gate it runs gates.py final-check: pass -> recommends the terminal `final` action (agent applies it, setting deliverable statuses final, then `next` reports `done`); fail -> `gate_blocked` naming the failing gates. Re-running is always safe — orchestrate.py is read-only and re-derives the next step from state.
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
    if obj.kind == "llm_fanout":      -> spawn obj.skill once per target, bounded
                                          concurrency; for classify, run obj.then_script after
    (state advances)                  -> loop again
```

Always re-run `next` after each action rather than assuming the order — new
evidence, review edits, or a half-done stage re-opens the right step.

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
