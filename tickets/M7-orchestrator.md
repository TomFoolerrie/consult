# M7 — `consult-orchestrate`: the one entry point (no manual Python)

**Depends on:** M0, M3, M4, M5 (it wraps them). **Blocks:** none.

## Goal

A single skill the user invokes to advance an area end to end, so they never run
a Python script by hand. It inspects folder state, performs the one next action
(run a deterministic script itself, or fan out the right agent), moves consumed
sources `new/` → `processed/`, and pauses at the two human gates.

## Why

The user drives the engagement, not the toolchain. `consult-orchestrate` is the
human-facing playbook over `orchestrate.py` (the read-only state advisor) and the
stage scripts/agents — the MVP analogue of the original `consult-run`.

## Two pieces

**1. `orchestrate.py` — read-only state advisor (Python).** Given an area folder,
it derives the **single next action** from state and prints it (`--json`);
it never mutates. State signals:

| Folder state | Next action |
|---|---|
| no `manifest.json`, `_sources/new/` non-empty | `taxonomy` (scope + stage proposals) |
| `_reference/.proposed/` exists, not yet confirmed | `confirm` (HUMAN GATE) |
| manifest exists, procedure skeletons empty | `fill` (fan out one agent per procedure) |
| procedures changed vs `.hashes.json` | `aggregate` then `synthesize` |
| aggregate emitted unmatched-mention WARNINGs | `registry_topup` (HUMAN: add entry/alias, re-run) |
| all views current | `render` |
| rendered; awaiting review | `review` (HUMAN GATE) |
| review edits dirtied procedures | back to `aggregate` |
| nothing outstanding | `done` |

**2. `skills/consult-orchestrate/SKILL.md` — the driver the user talks to.**
Loops `orchestrate.py next`, and for each returned action either runs the script
(`scaffold.py`, `aggregate.py`, `cfgi_markdown_to_word.py`, `scope_delta.py`) or
fans out the named agent (`consult-taxonomy`, the per-procedure fillers, the M5
judgment agents). It:
- **Moves sources** `_sources/new/` → `processed/` (and flips `sources.yaml`
  state) only after the fill that consumed them succeeds.
- **Stops and hands back to the human** at `confirm`, `registry_topup`, and
  `review`, with a clear message of what to do; it never auto-crosses a gate.
- Re-running is always safe — `orchestrate.py` re-derives the next step from
  state, so the user can invoke the skill repeatedly ("continue fixed-assets").

## Changes

- New `scripts/orchestrate.py` (read-only advisor; imports `doc_model.py`).
- New `skills/consult-orchestrate/SKILL.md` (the driver; references the stage
  scripts + agent skills by name).
- Source move logic (new → processed + `sources.yaml` state) lives in a small
  Python helper the orchestrator calls (not hand-done, not in M0).

## Acceptance

- From an area containing only `_sources/new/*`, invoking the skill walks:
  taxonomy → (stop: confirm) → fill → aggregate → (stop: topup if any) →
  synthesize → render → (stop: review) → done, running all Python itself.
- The user runs **zero** Python commands directly in a full pass.
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
