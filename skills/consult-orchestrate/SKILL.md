---
name: consult-orchestrate
description: >-
  The one entry point for advancing a CONSULT engagement area end to end. Invoke it as
  "build / continue <area>". It loops the read-only orchestrate.py state advisor, performs
  the single next action it returns — running a deterministic Python script itself, or
  dispatching an isolated subagent (taxonomy, one drafter per procedure, dependencies,
  raci) — moves consumed inputs, and stops at the human gates (confirm scope, registry
  top-up, review). You never run Python by hand. Re-running is always safe: the advisor
  re-derives the next step from folder state.
---

# consult-orchestrate — the engagement driver

You are the **thin coordinator**. You advance one area by looping the state
advisor and doing the one thing it says. You do deterministic Python yourself and
**dispatch every piece of judgment work to an isolated subagent**. You are the
only part of the system the user talks to.

## Context isolation — the rule you must not break

You must keep **your own context flat**. That means:
- **Never read source documents, transcripts, or draft procedure bodies into your
  context.** Those belong to subagents.
- Run deterministic scripts and read only their **compact stdout/JSON**.
- Dispatch each judgment stage as a **subagent** (the Agent tool) and keep only its
  **compact return** (files written, counts, warnings). Never ask a subagent to
  hand back draft prose.
- Your job is: advise → act (script or dispatch) → move files → stop at gates →
  repeat. Nothing you do should scale with document size.

## How you are invoked

"build <area>", "continue <area>", or `/consult-orchestrate <area>`. If the area
is new and its **L1 function is unknown**, ask the user which L1 (from
`skills/consult-taxonomy/reference/reference_taxonomy.yaml`) before scoping, and
record it (area-level `l1` in the manifest once scaffolded). The L1 is what you
pass to `consult-taxonomy`.

## The loop

```
loop:
  action = run  python3 scripts/orchestrate.py next --area <area> --json
  perform(action)          # run a script, or dispatch subagent(s)
  if action is a HUMAN GATE: stop, tell the user what to do, end turn
  if action == done: report and stop
  else: repeat
```

`orchestrate.py` is **read-only** — it never mutates; it derives the next action
from folder state (see M7). Re-running is always safe.

## Action handlers

Run scripts yourself; dispatch subagents for judgment. Dispatch prompts carry only
paths/ids — never pasted content.

| action | what you do |
|---|---|
| `taxonomy` | Dispatch **one `consult-taxonomy` subagent** with `{area, l1, taxonomy_path, mode}` (`mode=initial` if no manifest, else `incremental`). It writes proposals to `_reference/.proposed/`. Relay its compact summary → this leads to the `confirm` gate. |
| `confirm` | **HUMAN GATE.** Show the proposal summary (procedures by L2, new-L2 requests, low-confidence items, out-of-L1). Tell the user to edit `_reference/.proposed/` and reply **"confirm"** when ready. Stop. — The advisor keeps returning `confirm` while `.proposed/` exists un-promoted (it can't tell "still editing" from "ready"), so **only on the user's explicit go-ahead** do you run `python3 scripts/scaffold.py --confirm --area <area>` (promotes `.proposed/` → `_reference/`, writes manifest + A–H skeletons, stamps `sources.yaml` hashes). If the user just says "continue" without confirming, re-show the gate. |
| `fill` | For each procedure with an empty skeleton, dispatch a **`consult-drafter` subagent** — **all in one batch, in parallel** — with `{area, slug, title, sources: <its touches list from sources.yaml>, mode: first-draft}`. Collect compact statuses. Then move consumed sources (below). |
| `apply_review` | For each `{area}/_review/*.notes.yaml`, dispatch a **`consult-drafter` subagent** (`mode: update`, pointed at `_review/{slug}.notes.yaml`) — batch/parallel. Archive applied notes after success. |
| `aggregate` | Run `python3 scripts/aggregate.py <area>`. If it prints unmatched-mention WARNINGs → surface them (`registry_topup` gate). |
| `registry_topup` | **HUMAN GATE.** List the flagged systems/roles; tell the user to add entries/aliases to `_reference/` and re-invoke. Stop. |
| `synthesize` | Dispatch the M5 judgment subagents — `consult-dependencies`, `consult-raci` — one each (only for changed procedures per the delta). Compact returns only. |
| `render` | Run `python3 scripts/cfgi_markdown_to_word.py <area> -o <out.docx>`. Give the user the path. |
| `review` | **HUMAN GATE.** Tell the user to review the `.docx` in Word (tracked changes + comments), then either run the review extractor or drop notes so `_review/` fills. Stop. |
| `done` | Report: what's current, where the `.docx` is, nothing outstanding. Stop. |

## Parallel fan-out

`fill` and `apply_review` dispatch **N subagents in one batch** (one per procedure)
so they run concurrently. Wait for all, collect the compact statuses, then
continue. Never fill procedures one-at-a-time in sequence.

## Moving inputs (you own this, not the subagents)

- After a `fill` batch succeeds, move the sources it consumed
  `_sources/new/ → _sources/processed/` and flip their `sources.yaml` state (via
  the small Python helper, `python3 scripts/sources.py mark-processed …`). Never
  move a source before its fill succeeds.
- After an `apply_review` batch succeeds, archive the applied
  `_review/*.notes.yaml` (and the consumed `.docx`) to `_review/processed/`.

## Human gates — stop cleanly

At `confirm`, `registry_topup`, and `review`: post a short, specific message
(what to edit / review, where, and "re-invoke me to continue"), then **end the
turn.** Do not cross a gate on your own. When re-invoked, the advisor re-derives
state and picks up from there.

## Reporting

Between steps, keep the user oriented with one-liners ("scoped 12 procedures under
4 L2 buckets — confirm the proposals", "filled 12 procedures, 3 open gaps",
"rendered fixed-assets_v0.1.docx"). Never dump subagent prose or source text.

## Safety

- Everything is idempotent: if interrupted, re-invoking resumes from state.
- If a script exits non-zero (e.g. aggregate fail-loud on a malformed callout),
  surface the error and stop — don't paper over it.
- If a subagent returns `unregistered` nouns or unresolved conflicts, carry those
  into the next gate message so the human sees them.
