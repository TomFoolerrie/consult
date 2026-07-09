# M7 — `consult-orchestrate`: the one entry point (no manual Python)

**Depends on:** M0, M3, M4, M5 (it wraps them). **Blocks:** none.

## Goal

A single skill the user invokes to advance an area end to end, so they never run
a Python script by hand. It inspects folder state, performs the one next action
(run a deterministic script itself, or **dispatch a subagent**), moves consumed
sources `new/` → `processed/`, and pauses at the two human gates.

## Context-isolation is the point (not optional)

The orchestrator is a thin coordinator. Judgment work is **never run inline in
the orchestrator's context** — each piece runs as a **separate subagent** (a
tool-scoped `.claude/agents/` type per stage) that reads its own inputs and
returns a compact result. The orchestrator only runs deterministic Python, spawns
subagents and collects their small returns, moves files, and stops at gates. It
must not read transcripts, drafts, or source text into its own context — that is
what keeps its context flat regardless of engagement size and lets fill fan out
one subagent per procedure in parallel. See the README "Context-isolation
principle" + agent roster.

## Why

The user drives the engagement, not the toolchain. `consult-orchestrate` is the
human-facing playbook over `orchestrate.py` (the read-only state advisor) and the
stage scripts/agents — the MVP analogue of the original `consult-run`.

## Two pieces

**1. `orchestrate.py` — read-only state advisor (Python).** Given an area folder,
it derives the **single next action** from state and prints it (`--json`);
it never mutates. State signals:

Routing is **by folder** (deterministic — the advisor never guesses content).
The guards **overlap in raw state**, so precedence is explicit: evaluate top to
bottom, **first match wins.** This is what stops the advisor from re-running
`taxonomy` over human-edited `.proposed/` or looping (r3 review #2).

| # | Guard (first match wins) | Next action |
|---|---|---|
| 1 | `_reference/.proposed/` exists | `confirm` (HUMAN GATE) — highest, so a pending proposal is never re-scoped |
| 2 | `_review/*.notes.yaml` present | `apply_review` — one `consult-drafter` (update) per slug, **skip taxonomy** (M8) |
| 3 | no `manifest.json` **and** `_sources/new/` non-empty | `taxonomy` (initial) |
| 4 | `manifest.json` exists **and** any procedure still carries the `unfilled` sentinel | `fill` (fan out one drafter per unfilled procedure) |
| 5 | `manifest.json` exists **and** `_sources/new/` non-empty (no unfilled, no `.proposed/`) | `taxonomy` (incremental) |
| 6 | any procedure hash changed vs `.hashes.json` | `aggregate` |
| 7 | aggregate emitted unmatched-mention WARNINGs | `registry_topup` (HUMAN: add entry/alias, re-run) |
| 8 | derived views built but `reconcile` not yet clean this pass | `reconcile` (area-wide hard gate) |
| 9 | procedures changed but judgment views stale | `synthesize` |
| 10 | all views current and reconciled, no fresh `.docx` | `render` |
| 11 | rendered; awaiting human review | `review` (HUMAN GATE) |
| 12 | nothing outstanding | `done` |

**Why the order matters:** after scaffold, `_sources/new/` is still full (sources
move only after fill) — but row 4 (`fill`) precedes row 5 (`taxonomy
incremental`), so a freshly-scaffolded area fills rather than re-scoping. Row 1
outranks everything, so an edited `.proposed/` always surfaces the confirm gate.
The two "new input" folders route differently by design: `_sources/new/` → the
scope-aware path (taxonomy reads it, tags `touches`); `_review/` → straight to the
drafter (notes are already procedure-anchored by `review_extract.py`, M8).

**The `unfilled` sentinel (fill predicate).** `scaffold.py` stamps each new
procedure skeleton with an explicit `unfilled` marker (a `<!-- unfilled -->` line,
or `status: unfilled` in its `consult-meta`); the drafter **removes it on its
first successful write.** Row 4 keys off the sentinel's presence — a deterministic
"is this a skeleton?" predicate, not a fragile heuristic (file size / TBD count).

**`reconcile` is in the loop (row 8), not opportunistic.** After `aggregate`
(and `synthesize`), the orchestrator runs `python3 scripts/reconcile.py <area>`
over the whole area — the hard gate for order uniqueness, `[[slug]]` resolution,
derived `(slug,id)` pairs, and derived-marker presence. It **gates `render`**; a
manifest-only reorder still passes through it. (Agents may self-reconcile their
one file, but the area-wide gate is the orchestrator's, always run.)

**2. `skills/consult-orchestrate/SKILL.md` — the driver the user talks to.**
Loops `orchestrate.py next`, and for each returned action either runs the
deterministic script itself (`scaffold.py`, `aggregate.py`,
`cfgi_markdown_to_word.py`, `scope_delta.py`, `reconcile.py`) **or dispatches the
matching subagent** — `consult-taxonomy`, one `consult-drafter` per procedure (in
parallel), or the M5 judgment agents (`consult-dependencies`, `consult-raci`).
Each subagent runs in its **own context** and returns a
compact status (files written, warnings, done) — the orchestrator never ingests
the drafts or sources itself. It:
- **Moves sources** `_sources/new/` → `processed/` (and flips `sources.yaml`
  state) only after the fill that consumed them succeeds.
- **Stops and hands back to the human** at `confirm`, `registry_topup`, and
  `review`, with a clear message of what to do; it never auto-crosses a gate.
- Re-running is always safe — `orchestrate.py` re-derives the next step from
  state, so the user can invoke the skill repeatedly ("continue fixed-assets").

## Changes

- New `scripts/orchestrate.py` (read-only advisor; imports `doc_model.py`).
- New `skills/consult-orchestrate/SKILL.md` (the driver; dispatches subagents by
  type, runs the deterministic scripts, never drafts inline).
- New `.claude/agents/` defs for the judgment stages so the orchestrator can
  dispatch them as isolated subagents: `consult-taxonomy`, `consult-drafter`,
  `consult-dependencies`, `consult-raci` (each preloads its skill brief,
  tool-scoped to just its input reads + its one output file + reconcile/aggregate).
  (The M5 agent defs may already exist from M5 — reuse.)
- Source/review move logic (new → processed + `sources.yaml` state; applied
  review notes → `_review/processed/`) lives in a small Python helper
  (`scripts/sources.py`) the orchestrator calls (not hand-done, not in M0).
- **A source is "consumed" per-source, not per-batch (r3 review #10).** A source's
  `touches` list may span several procedures; a fill batch may partially fail
  (drafter A succeeds, B fails). `sources.py mark-processed` takes the set of
  **successfully-filled** slugs and moves a source to `processed/` **only when its
  entire `touches` set is filled.** A source touching an unfilled/failed procedure
  stays in `new/` (still "outstanding"), and its still-unfilled procedures keep
  their `unfilled` sentinel → the next pass re-dispatches only those (row 4).
- On a **new** area whose `l1` is unknown, the skill asks the user which L1 (from
  the reference taxonomy) and records it area-level in the manifest; that `l1` is
  passed to `consult-taxonomy`. See `skills/consult-orchestrate/SKILL.md` for the
  full action-by-action driver contract.

## Acceptance

- From an area containing only `_sources/new/*`, invoking the skill walks:
  taxonomy → (stop: confirm) → fill → aggregate → (stop: topup if any) →
  synthesize → render → (stop: review) → done, running all Python itself.
- The user runs **zero** Python commands directly in a full pass.
- Each judgment stage runs as a **subagent**, not inline: after a full pass the
  orchestrator's own context holds only compact statuses, not any draft/source
  text (verify the drafts don't appear in the orchestrator transcript).
- Fill dispatches procedures **in parallel** (N subagents for N procedures).
- Consumed sources end in `_sources/processed/` with `sources.yaml` state
  `processed`; nothing is moved before its fill succeeds.
- `orchestrate.py` is read-only (re-running `next` never changes state).
- Editing a procedure post-review and re-invoking resumes at `aggregate` and
  spends tokens only on the changed procedure (delegates to M5's delta).
- Interrupting mid-pass and re-invoking resumes correctly from state.

## Out of scope

Automated reassessment of the procedure set / registry on new sources (M6) — the
orchestrator will *route* to it once built, but M6 itself is deferred.

## Design note

`orchestrate.py` advises; it does not mutate (mirrors the original system's
split). All state changes happen in the stage scripts and the agents' writes, so
the advisor stays a pure function of folder state and re-running is idempotent.
