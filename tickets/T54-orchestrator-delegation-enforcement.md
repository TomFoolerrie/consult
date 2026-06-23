# T54 — Orchestrator delegation enforcement (stop inline self-execution)

**Slice 4 (Cost & Runtime Efficiency) · Follow-up · From field run (3 real artifacts, ~$10) ·
Depends: — · Touches: `skills/consult-run/SKILL.md`, and (runtime-dependent) the dispatch
contract docs.**

> **Field observation (load-bearing).** On a real 3-artifact run the orchestrator **did the
> fan-out work itself** — it classified / consolidated / drafted inline instead of dispatching
> to `consult-classifier` / `consult-consolidator` / `consult-drafter`. Cost was ~$10 for three
> artifacts. The suspected dominant cost driver is **this**, not the JSON-format friction (that
> is T55).

## Problem

`consult-run` is **prose** that *describes* a dispatch loop: "if `kind == llm_fanout`, spawn the
named sub-agent once per target; if `kind == deterministic`, run the script yourself." Nothing
**structurally** forces delegation. When the per-stage work is small (e.g. 3 docs) the model
"helpfully" performs the classify/consolidate/draft reasoning in its own context instead of
fanning out.

The cost consequence is severe and compounding:

1. **Context bloat, re-billed every turn.** Every stage's full inputs (ingested MD text, the
   taxonomy slice, all per-doc reasoning) accumulate in the **single** orchestrator context
   instead of living in isolated sub-agent contexts that return a one-line summary. Later stages
   (merge, consolidate, draft, synthesize) then re-read that bloated context. Token cost scales
   with accumulated context, not with work done.
2. **No isolation / no parallelism.** The whole point of the fan-out architecture (one sub-agent
   per doc/node/L1, each writing only its own artifact and returning a one-liner) is defeated.
3. **Silent correctness drift.** An inline classifier is not subject to the per-doc artifact
   schema + `validate_artifact.py` cross-field gate that a real `consult-classifier` sub-agent
   must pass before its artifact counts. Inlining can therefore skip the validation contract
   entirely.

## Decision needed (the fork — resolve as step 0 of Build)

**The fix depends on a runtime fact that must be confirmed first, not assumed:**

- **(A) The runtime CAN spawn sub-agents** (Claude Code / Agent SDK; the `Task`/`Agent`
  primitive is available). Then inlining is **instruction drift** and the fix is *enforcement* —
  harden the prose into a blocking contract + content-starvation (below). Strongest available
  enforcement in this runtime is moving the loop out of the model entirely (a deterministic
  driver / Workflow that reads `orchestrate.py next --json` and spawns sub-agents
  programmatically, so the loop-level model never sees document content and *cannot* inline).
- **(B) The runtime CANNOT spawn sub-agents** (Claude Desktop skills run in the **main
  conversation**; there may be no per-doc sub-agent primitive). Then inlining is **forced**, not
  drift — the fan-out architecture has no execution substrate here, and "harden the prose" will
  not fix it. The real options become: (i) treat the suite as **Claude Code / SDK-targeted** and
  use Desktop only for authoring single skills; or (ii) add an explicit **single-context
  sequential discipline** to `consult-run` — process one target at a time, emit its artifact,
  **drop its inputs from working context before the next** (an explicit "do not carry the
  previous doc's text forward" instruction), so a no-sub-agent runtime still bounds context
  growth. This is strictly weaker than true isolation but is the only lever Desktop offers.

**Do not write the fix until the runtime is confirmed.** The user's last reported run was in
**Claude Desktop** → branch (B) is the likely live path; verify whether Desktop exposes any
sub-agent/Task capability before committing to (i) vs (ii).

## Build

**Step 0 — confirm the runtime fork** (above). Record the finding at the top of the build report;
it selects everything below.

**If (A) — enforcement (sub-agents available):**
- Rewrite the dispatch section of `consult-run` from descriptive to **imperative + blocking**:
  for `kind == llm_fanout` the orchestrator **MUST** spawn the named sub-agent once per target;
  performing classify / consolidate / draft / synthesize reasoning itself is a **contract
  violation**, not a permitted shortcut for small batches. State the *reason* (context isolation
  / cost) so the model doesn't "optimize" it away.
- **Content-starvation:** explicitly forbid the orchestrator from reading `ingested/*.md`,
  taxonomy slices, or calling the input-gatherer scripts (`consolidate_inputs.py`,
  `draft_inputs.py`, `synthesis_inputs.py`) **itself** — those feed sub-agents. Starved of the
  content, it cannot inline the work. The orchestrator only ever handles `orchestrate.py next`
  output (`{action, kind, targets}`) + one-line sub-agent summaries.
- (Optional, strongest) note the deterministic-driver / Workflow option as the durable fix:
  `orchestrate.py next --json` already emits machine-readable actions — a code loop can spawn
  sub-agents structurally so delegation is not *remembered*. File as a follow-up if out of scope
  here.

**If (B) — single-context discipline (no sub-agents):**
- Add a **sequential, context-bounded** loop to `consult-run`: one target at a time; produce its
  artifact via the command/validate path; **explicitly drop that target's source text from
  working context** before the next target. Forbid carrying multiple docs' full text
  simultaneously.
- Document plainly at the top of `consult-run` that **true fan-out isolation requires the Claude
  Code / SDK runtime**; in a single-context runtime the suite runs sequentially and costs more,
  and that is expected. Don't let the prose imply isolation that the runtime can't deliver.

**In both branches:** keep `orchestrate.py` read-only and the action contract unchanged — this
ticket changes *how the orchestrator obeys the dispatch tags*, not the tags themselves.

## Tests

This is primarily a **prose/contract** change; assert what is mechanically assertable:
- `orchestrate.py next --json` still emits `kind` + `targets` for each stage (no regression to
  the dispatch contract the rewrite relies on) — exercise via the existing Slice-1 e2e fixture.
- A lint/grep check that `consult-run` no longer instructs (or now forbids) the orchestrator to
  read `ingested/*.md` or invoke the gatherer scripts directly (branch A).
- **Manual re-measure (the real acceptance):** re-run the 3-artifact engagement and record the
  per-stage behavior (did each `llm_fanout` stage dispatch?) and total cost vs the ~$10 baseline.
  Capture **counts and cost only — no client content** (ties into T56's instrumentation).

## DoD

- Runtime fork confirmed and recorded; the chosen branch (A enforcement / B sequential
  discipline) implemented in `consult-run`.
- The orchestrator no longer performs fan-out stage work in its own context (branch A), **or**
  the single-context path bounds context growth by dropping spent inputs (branch B).
- `orchestrate.py` action contract unchanged; Slice-1 e2e green.
- A re-run of the 3-artifact engagement shows the intended dispatch behavior and a recorded cost
  delta vs the ~$10 baseline (acceptance is the cost drop, measured via T56).
