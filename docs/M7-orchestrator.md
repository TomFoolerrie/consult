# M7 — `consult-orchestrate`: the one entry point (no manual Python)

**Depends on:** M0, M3, M4, M5 (it wraps them). **Blocks:** none.

> **Revised by M18, M17 and M6 — the ladder below is the current one.** This
> ticket shipped a 12-row precedence table; three later tickets changed it, and
> the rows are renumbered rather than replaced so the original design is still
> legible:
>
> - **M18 (advisor honesty)** added guard **0** (`error` — a nonexistent area
>   folder used to read as `done`), split guard 2 into applicable-vs-orphaned
>   notes (**2b** `review_triage` now also catches an orphan, not just the
>   `_unassigned` bucket), added the **`unresolvable`** resting gate at **5b** and
>   inside guard **8**, changed `.aggregate.json`'s `proc_hashes` to
>   `{slug: {file: sha}}`, and gave `.reconcile.json` an optional `failing_files`.
> - **M17 (stage gates)** inserted guard **8.5** `draft_ready` and its
>   `.draft_ready.json` signal, written only by the new `accept-draft`
>   subcommand. (Sticky holds, this ticket's item 3, are still unbuilt.)
> - **M6 (reassessment)** narrowed guard 5 to *unassessed* sources and added
>   **5a** `unresolvable` for the stranded remainder.
> - Guard **1.5** (`ingest_returns`) arrived with M9/M10 and was never in this
>   table.
>
> `scripts/orchestrate.py`'s module docstring is the authority; the table below is
> kept in step with it.

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
| 0 | the area folder does not exist | `error` — **not a gate**; `next` exits **2** so the driver stops. A typo'd `--area` used to read as `done` (audit F3) |
| 1 | `_reference/.proposed/` exists | `confirm` (HUMAN GATE) — highest, so a pending proposal is never re-scoped |
| 1.5 | `_review/returned/` holds un-ingested kit returns | `ingest_returns` (M9/M10) — the deterministic chain first, so drafters only see what needs judgment |
| 2 | a `_review/<slug>.notes.yaml` whose basename names a **live manifest procedure slug** (excluding `_unassigned.notes.yaml`) | `apply_review` — one `consult-drafter` (update) per slug, **skip taxonomy** (M8). Coexisting orphans ride along in `details.orphan_notes`; `_unassigned.notes.yaml` rides along too, so the human is told about both. With **no manifest at all** this guard steps aside for guard 3 — nothing is applicable to an unscoped area (M18/F1) |
| 2b | notes naming no live slug, or only `_review/_unassigned.notes.yaml` | `review_triage` (HUMAN GATE) — a drafter has no procedure to update and a note archives only on a successful dispatch, so no stage can clear it; the two resolutions (restore the procedure / archive the note) are named in `details.resolutions` |
| 3 | no `manifest.json` **and** `_sources/new/` non-empty | `taxonomy` (initial) |
| 4 | `manifest.json` exists **and** any procedure still carries the `unfilled` sentinel | `fill` (fan out one drafter per unfilled procedure; M11 waves via `details.unfilled`/`deferred`) |
| 5 | `manifest.json` exists **and** `_sources/new/` holds files that are **UNASSESSED** — unregistered in `_reference/sources.yaml`, or registered at a different `hash` | `taxonomy` (incremental). M6 narrowed this from "non-empty": a source registered at its current bytes has already been read and proposed against |
| 5a | every file in `_sources/new/` is assessed, and nothing can consume them (guard 2 ruled out a pending note, guard 4 an `unfilled` skeleton) | `unresolvable` (HUMAN GATE) — naming the stranded `SRC-` ids. Re-dispatching taxonomy would propose nothing new and spend a dispatch per lap (audit F7 / M6) |
| 5b | a manifest procedure whose fragment file is absent | `unresolvable` (HUMAN GATE) — no stage writes a fragment from nothing, and guard 6 used to fire forever with the wrong cause (audit F4) |
| 6 | procedure or registry content changed vs `.aggregate.json` | `aggregate` |
| 7 | aggregate emitted unmatched-mention WARNINGs | `registry_topup` (HUMAN: add entry/alias, re-run) |
| 8 | derived views not verified clean at the current basis | `reconcile` (area-wide hard gate) — **unless** `.reconcile.json` recorded `failing_files` at this exact basis, in which case the failures are partitioned by owner (M18/F8): drafter-owned fragments → `unresolvable`; agent-owned views the change signal already marks stale → `synthesize` first, then reconcile re-verifies; agent-owned views with **nothing** stale → `unresolvable`; anything else (manifest, a python-derived view, `_reference/sources.yaml`) → plain `reconcile` |
| 8.5 | a spend is outstanding (`synthesize` or `render`) and this draft is not accepted | `draft_ready` (HUMAN GATE, M17) — the last free stop; cleared only by `accept-draft` |
| 9 | procedures changed but judgment views stale, or a pending placeholder remains | `synthesize` |
| 10 | all views current and reconciled, no fresh `.docx` | `render` |
| 11 | rendered; awaiting human review | `review` (HUMAN GATE) |
| 12 | nothing outstanding | `done` |

**The resolvable-action invariant (M18).** An action is returnable only if running
it can change the state that selected it. `unresolvable` is the result for the
states where nothing satisfies that: `human_gate: true`, exit **0** — a *resting*
gate like `review`, not an error, because the folder is consistent and the ladder
is merely out of moves. It carries three named fields — `details.state` (what was
detected), `details.why_no_stage` (why no stage clears it), `details.human_action`
(the specific fix) — plus the evidence (`stranded_ids`/`stranded_sources`,
`missing_procedures`, `failing_files`, `dangling_refs`). `error` is the one
non-gate: there is nothing to rest on, so `next` exits nonzero.

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

**State the advisor reads (the mutating stages write it).** `orchestrate.py`
is read-only, so it cannot itself run `aggregate`/`reconcile` to learn their
result — it must read a small persisted signal each stage leaves. These files
are **git-ignored, at the area root**, and are the M7 orchestration contract:

| File | Written by | Shape | Guards it drives |
|---|---|---|---|
| `.aggregate.json` | `aggregate.py` | `{proc_hashes:{slug:{file:sha}}, registry_hash:sha, warnings:[…]}` — per-**file** inside each slug (M18/F5), so a duplicate slug cannot drop one file's hash out of the change signal. A pre-existing signal in the old `{slug:sha}` shape simply compares unequal, and one harmless aggregate pass rewrites it | 6 (stale if proc/registry hash differs), 7 (topup if `warnings`) |
| `.hashes.json` | `scope_delta.py commit` (the orchestrator runs it per kind, after each M5 agent succeeds — the sole writer) | `{derived_kind:{slug:sha}}` — per-kind procedure-hash baseline as of that kind's last successful write (the "M5 change signal") | 9 (synthesize if current proc hashes differ from a kind's baseline) |
| `.reconcile.json` | `reconcile.py` | `{basis:sha, clean:bool}`, plus **optional** `failing_files:[rel,…]` (M18/F8) — the area-relative files the run's errors named. The key is OMITTED when the caller does not track it, and guard 8 then behaves exactly as it did pre-M18 | 8 (reconcile if basis stale or not clean; the owner partition above when `failing_files` is recorded at the current basis) |
| `.draft_ready.json` | `orchestrate.py accept-draft` **only** (M17) | `{draft_basis:sha, accepted:true}` — `draft_basis` is `sha256(json.dumps([proc_hashes, registry_hash], sort_keys=True))`: the **two databases only**, deliberately not `basis`. `synthesize` rewriting the derived views must not re-open a gate the human just cleared; any fragment or registry edit must | 8.5 (draft_ready unless the recorded value equals the current one) |
| `.render.json` | the **working-mode** renderer (M4); `awaiting_review` cleared by `orchestrate.py accept` | `{basis:sha, docx:path, awaiting_review:bool}`. `--mode final` and `--slugs` renders are exports and never write it (M21), so the signal is unambiguously about the working document | 10 (render if basis stale), 11 (review if awaiting) |

`basis` = combined hash of all procedure files + all derived files + the
manifest — the unit reconcile and render gate on. A **missing** state file means
"stage never ran", so its guard fires. An absent `doc_model.load_manifest`
(pre-M2) degrades to a plain `manifest.json` read; the contract is still to
import `load_manifest` from `doc_model`.

**Why `.aggregate.json` also records `registry_hash`.** Row 7 (`registry_topup`)
is a human gate: the human adds a registry entry/alias, then re-invokes. That
edit changes `registry_hash` but **not** the procedure hashes — so row 6
(`aggregate`) re-fires on the registry change alone, re-runs aggregate, and the
top-up loop clears the warning (or re-flags a still-missing one). Without the
registry hash the gate would never re-evaluate.

**`review` is the resting gate; `done` needs explicit human acceptance.** The
working-mode renderer stamps `awaiting_review:true`; the advisor returns `review`
until either new `_review/*.notes.yaml` appear (→ row 2, the revision loop) or the
human accepts. `decide()` is read-only and cannot know "accepted", so acceptance
is a **human signal**, not a state the advisor computes — but it is recorded by a
named verb rather than left to the driver's memory: `orchestrate.py accept` is the
SOLE writer that clears the flag (the renderer always sets it true), and the
driver runs it only on the user's explicit acceptance. Absent that, `done` (row
12) is only reached when the render basis is current and `awaiting_review` is
already false. Guard 8.5's `accept-draft` is the same shape one gate earlier: sole
writer of `.draft_ready.json`, and a no-op **with a stated reason** when the area
is not actually at its gate (it asks `decide()` rather than re-deriving the
conditions, so the flag can never be written for a state the gate does not
describe).

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
- **Stops and hands back to the human** at every result carrying
  `human_gate: true` — `confirm`, `review_triage`, `registry_topup`,
  `draft_ready` (M17), `unresolvable` (M18) and `review` — with a clear message of
  what to do; it never auto-crosses a gate. It also stops, without checkpointing,
  on `error` (M18), which is not a gate.
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
- `orchestrate.py next` is read-only (re-running it never changes state). The
  later-added `checkpoint` subcommand commits the area folder (and seeds its
  `.gitignore`) — the deliberate exception, never run by `next`/`decide`.
- Editing a procedure post-review and re-invoking resumes at `aggregate` and
  spends tokens only on the changed procedure (delegates to M5's delta).
- Interrupting mid-pass and re-invoking resumes correctly from state.

## Out of scope

Automated reassessment of the procedure set / registry on new sources (M6) — the
orchestrator will *route* to it once built, but M6 itself is deferred. *(M6 has
since been BUILT; guards 5 and 5a above are its ladder half.)*

## Design note

`orchestrate.py` advises; it does not mutate (mirrors the original system's
split). All state changes happen in the stage scripts and the agents' writes, so
the advisor stays a pure function of folder state and re-running is idempotent.
