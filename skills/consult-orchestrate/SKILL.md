---
name: consult-orchestrate
description: >-
  The one entry point for advancing a CONSULT engagement area end to end. Invoke it as
  "build / continue {area}". It loops the read-only orchestrate.py state advisor, performs
  the single next action it returns — running a deterministic Python script itself, or
  dispatching an isolated subagent (taxonomy, one drafter per procedure, dependencies,
  raci) — moves consumed inputs, and stops at the human gates (confirm scope, registry
  top-up, draft-ready, review). You never run Python by hand. Re-running is always safe:
  the advisor re-derives the next step from folder state.
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

## The system model — read once, reason from it everywhere

The action table below covers the happy path; THIS is what lets you handle
everything else without reverse-engineering the scripts.

**Two databases, everything else is a view.**
1. Procedure fragments (`10_<slug>.md`) — the verbs; source of truth.
2. `_reference/` registry — the nouns (systems, roles + `people:` person→role
   map, SRC- sources with `touches:` tags, glossary).
Every other section (index, role dictionary, systems, appendices, RACI,
dependencies) is a **projection** — regenerated, never hand-fixed. Corollary:
when something is wrong in a derived section, the fix is ALWAYS upstream (a
fragment or the registry), then regenerate. Never patch a view.

**Identity and numbering.**
- `slug` = permanent identity, minted once at scoping. Display numbers
  ("2.3") derive from manifest order + `l2_order` at render; `[[slug]]`
  tokens resolve to them late. So reordering is always safe and numbers are
  never stored anywhere.
- Callout IDs are **procedure-local** (every drafter starts at 01; collisions
  across procedures are correct). Global 2-digit display IDs ("GAP-07") are a
  render-time transform. Corollary: an ID quoted in chat/Word is a DISPLAY id;
  on disk it's local. The maps in `doc_model.callout_display_ids` translate.
  Agent-owned sections (RACI, dependencies) never quote callout IDs at all.

**Folder state is the ONLY state.** There is no database, no memory: the
advisor re-derives everything from what's on disk, which is why re-invoking
after any interruption is safe and why every stage is idempotent. Deterministic
stages leave git-ignored signal files; if a stage "keeps firing", its signal
file wasn't written — that's a stage bug to surface, not a loop to ride.

**One writer per file.** Fragments ← drafters. Registry ← human (agent
proposes into `.proposed/`). Python-derived views ← aggregate. 82/84 ← their
agents. `_client/` ← human only. You yourself write NOTHING except by running
scripts. If you're ever tempted to edit a fragment directly — don't; dispatch
the drafter that owns it.

**Judgment vs mechanics — the token boundary.** Everything deterministic is
free: scaffold, aggregate, reconcile, render (both modes), kits, the whole
review return-trip (screenshot extraction, workbook answers, tracked-changes
apply, comment extraction). Tokens are spent ONLY on: taxonomy (once per
scope), drafters (first-fill, and updates consuming notes), dependencies+RACI
(change-scoped). When the user asks "what will X cost", answer from the cost
topology below: **taxonomy** spends 1 agent per scope pass, the **drafters**
spend N (one per procedure — usually the bulk of it), and **synthesize** spends
2; `consolidate` will spend 1 more once M12 lands. Everything else on the ladder
is free Python or a human's time — but `render` is the expensive kind of free,
because it starts a human review cycle, which is the scarcer resource.

| Guard | Action | Cost |
|---|---|---|
| 0 | `error` | — (abort; nothing was read) |
| 1 | `confirm` | human gate |
| 1.5 | `ingest_returns` | free (Python) |
| 2 | `apply_review` | **N drafter agents** |
| 2b | `review_triage` | human gate |
| 3 | `taxonomy` (initial) | **1 agent** |
| 4 | `fill` | **N drafter agents** |
| 5 | `taxonomy` (incremental) | **1 agent** |
| 5a/5b | `unresolvable` | human gate (resting) |
| 6 | `aggregate` | free (Python) |
| 7 | `registry_topup` | human gate |
| 8 | `reconcile` | free (Python) |
| **8.5** | **`draft_ready`** | human gate — the last free stop |
| 9 | `synthesize` | **2 agents** |
| 10 | `render` | free (Python) — but opens the human review round |
| 11 | `review` | human gate |
| 12 | `done` | — |

The boundary at 8.5 is precise: everything at or before it is either free or
already spent; everything after commits **agents** (`synthesize`) or **people**
(`render` → kits → review). That is why `draft_ready` is the gate to explain
properly rather than rush past.

**The review loop in one breath.** Working render stamps provenance
(bookmarks + `_review/.maps/` sidecars) → kits go out per owner → returns
land in `_review/returned/` → `ingest_returns` applies/ingests everything
mechanical → only notes (comments, gap answers, failed applies) reach
drafters → final render strips gap scaffolding and embeds captured
screenshots. Precision of the mechanical apply is structural (verify-or-
revert); its failures degrade to notes, never to corrupted fragments.

### Signals dictionary (what the folder is telling you)

| On disk | Meaning |
|---|---|
| `_reference/.proposed/` exists | scope proposals awaiting the human confirm gate; consumed (deleted) by scaffold --confirm |
| `<!-- unfilled -->` in a fragment | skeleton not yet drafted → `fill` |
| `_sources/new/` non-empty | unconsumed inputs → taxonomy (initial or incremental) |
| `sources.yaml` `touches:` | which drafters each source feeds — the fan-out routing |
| `sources.yaml` `hash:` / `state:` / `consumed:` | the retirement ledger, written advisor-side and **never by an agent**: `hash` is stamped by `scaffold --confirm` (it is what makes a source "already assessed" at guard 5), `state` + `consumed` by `sources.py mark-processed`. `consumed:` is the durable per-slug credit record, never reset — it is what lets a source spanning a new and an existing procedure retire across two batches |
| `.aggregate.json` | last aggregate basis + registry-warning list (top-up gate reads this); `proc_hashes` is per-file inside each slug |
| `.hashes.json` | per-derived-kind procedure-hash baseline; ONLY `scope_delta.py commit` writes it — skip it after synthesize and guard 9 fires forever |
| `.reconcile.json` | `{basis, clean}` — render is gated on clean at the current basis. May also carry `failing_files` (the area-relative files the last run's errors named): that is what lets guard 8 send a fixable failure to `synthesize` first and an unfixable one to `unresolvable`, instead of re-running the verifier forever |
| `.draft_ready.json` | `{draft_basis, accepted}` — the M17 draft-ready accept flag, keyed to the **two databases only** (procedures + registry), so `synthesize` rewriting 82/84 cannot re-open a gate the human just cleared, while any fragment or registry edit does. ONLY `orchestrate.py accept-draft` writes it |
| `.render.json` | `{basis, docx, awaiting_review}` — the review resting state. Only `--mode working` writes it; `--mode final` and `--slugs` renders are exports and leave it untouched |
| `*.extract.json` | per-doc extraction sidecar written by aggregate (derived; git-ignored) |
| `_review/kits/` | derived send-outs; regenerate freely with kits.py |
| `_review/returned/` non-empty | un-ingested returns → `ingest_returns` outranks everything below confirm |
| `_review/*.notes.yaml` | judgment work queued for drafters (merge-appended; multiple producers). Every item carries `kind:` (`review` \| `source` \| `retirement` \| `rename` \| `consolidation`), and a `kind: source` item also carries `src: SRC-<id>`. You never read these files — but the `kind` is what makes retirement accounting honest, so it is why `mark-processed` distinguishes `--filled` from `--updated` |
| `_review/_unassigned.notes.yaml` | items no procedure owns → human triage gate |
| `_review/.maps/*.json` | render provenance (apply anchors); never hand-edit |
| `_assets/screens/<slug>/SC-*.png` | captured evidence; final render embeds; hand-dropping a file here is first-class |
| `_client/org-chart.yaml`, `taxonomy.yaml` | optional client context: person→role grounding + L1 boundary authority (taxonomy agent reads; reconcile enforces names) |
| scope note comment in a skeleton | merged variant pair — drafter writes shared flow once, branches at divergence |

### Failure playbook

- **Advisor returns the same action twice with no progress** → the stage
  didn't write its signal file or didn't do its work; report the stage bug,
  don't loop. Exception: a **gate** returned twice is correct, not a loop —
  `unresolvable` in particular is a resting state the advisor will keep
  returning until a human changes something. Never re-run the action that
  produced an `unresolvable`.
- **aggregate exits non-zero** → a malformed callout in ONE fragment
  (fail-loud names it). Dispatch that procedure's drafter (update mode) with
  the error text; never hand-fix.
- **reconcile ERRORs** — route by class: ID grammar / dangling ID / bare gap
  tag → that fragment's drafter. Dangling `[[slug]]` → whoever wrote it
  (fragment drafter, or RACI/dependencies agent for 82/84). NAMED INDIVIDUAL
  → drafter for that fragment (role-only rule; roles.yaml `people` has the
  mapping). Empty / heading-only fragment, unregistered or missing `SRC-`
  citation, an H1 in a fragment, a baked display number (`see 1.2`), a callout
  ID quoted in 82/84 → the owning writer's agent (fragment drafter, or the
  82/84 agent), same as the grammar classes. `touches` naming a non-manifest
  slug → the human: it is a registry edit (`_reference/sources.yaml`), and
  until it is fixed the source can never retire. Derived-row pair unknown →
  re-run aggregate first (stale view) before suspecting a fragment.
  Manifest/order errors → scaffold-level; surface to the human.
- **reconcile WARNINGs** (unregistered slugs, possible name tokens) → carry
  them to the next gate message; they never block render.
- **review_apply falls back a lot** → normal for reviewers who disabled
  tracked changes or restructured heavily; the notes carry everything, the
  drafters absorb it. Only report a defect if it applied something WRONG
  (it structurally shouldn't be able to).
- **Kit lands in `role-*` / `unassigned/`** → roles.yaml `people:` or the org
  chart is missing/thin; tell the user which role has no person mapped.
- **User asks for the client deliverable while gaps are open** → that's
  allowed by design: `--mode final` strips and reports counts; relay the
  counts so the acceptance is informed.

## How you are invoked

"build <area>", "continue <area>", or `/consult-orchestrate <area>`. If the area
is new and its **L1 function is unknown**, ask the user which L1 (from
`skills/consult-taxonomy/reference/reference_taxonomy.yaml`) before scoping, and
record it (area-level `l1` in the manifest once scaffolded). The L1 is what you
pass to `consult-taxonomy`.

## The loop

```
loop:
  action = run  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/orchestrate.py" next --area <area> --json
  perform(action)          # run a script, or dispatch subagent(s)
  if perform mutated the area:   # every action except a gate you stopped at / done
      run  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/orchestrate.py" checkpoint --area <area> --stage <action>
  if action == error: `next` exited 2 — the --area path is wrong. Report and STOP.
  if action is a HUMAN GATE: stop, tell the user what to do, end turn
  if action == done: report and stop
  else: repeat
```

`human_gate: true` is the machine-readable stop signal — it covers `confirm`,
`review_triage`, `registry_topup`, `draft_ready`, `unresolvable` and `review`.
Trust the flag, not your memory of the list. `error` is deliberately **not** a
gate (a gate rests; there is nothing here to rest on) — it is the one action
where `next` exits nonzero, so treat a nonzero exit as "stop", never as
"progress".

**Git checkpoints are part of the loop, not a courtesy.** Folder state is the
only state, so an uncommitted area is an engagement one bad `rm` from gone.
After every action that changed the folder — including the human-triggered
`scaffold --confirm` at the confirm gate — run the `checkpoint` subcommand
above. It is deterministic and safe to over-call: it stages and commits ONLY
the area pathspec (message `consult(<area>): <stage>`), no-ops when nothing
changed or the area isn't in a git repo, and never pushes. Don't hand-craft
`git add`/`git commit` yourself; the subcommand is the one writer.

`orchestrate.py next` is **read-only** — it never mutates; it derives the next
action from folder state (see M7). Re-running is always safe. (The `checkpoint`
subcommand above is the one deliberate exception: it commits the area folder —
and seeds an area `.gitignore` on first use — but never touches folder content
the stages produced.) Because `next` cannot run the
mutating stages itself, each deterministic stage leaves a small git-ignored
state file at the area root that the advisor reads next loop: `aggregate.py` →
`.aggregate.json` (`{proc_hashes: {slug: {file: sha}}, registry_hash, warnings}`);
the synthesis pass → `.hashes.json` (procedure hashes, the M5 change signal);
`reconcile.py` → `.reconcile.json` (`{basis, clean}` + optional `failing_files`);
the working-mode renderer → `.render.json` (`{basis, docx, awaiting_review}`).
Two of them are written by a human's decision rather than a stage:
`accept` → `.render.json`'s `awaiting_review`, and `accept-draft` →
`.draft_ready.json` (`{draft_basis, accepted}`); each subcommand is the SOLE
writer of its flag. A stage that doesn't write its file reads as
"never ran", so its guard keeps firing — surface that as a stage bug, don't loop
blindly. The action JSON carries `{action, reason, human_gate, details}`.

## Action handlers

Run scripts yourself; dispatch subagents for judgment. Dispatch prompts carry only
paths/ids — never pasted content.

| action | what you do |
|---|---|
| `taxonomy` | Dispatch **one `consult-taxonomy` subagent** with `{area, l1, taxonomy_path, mode}` (`mode=initial` if no manifest, else `incremental`). If `{area}/_client/` exists (optional `org-chart.yaml` / `taxonomy.yaml`), say so in the dispatch prompt so the agent reads it. It writes proposals to `_reference/.proposed/`. Relay its compact summary → this leads to the `confirm` gate. |
| `confirm` | **HUMAN GATE.** Show the proposal summary (procedures by L2, merged variants + overlap flags, new-L2 requests, low-confidence items, unmapped people, out-of-L1). Tell the user to edit `_reference/.proposed/` and reply **"confirm"** when ready. Stop. — The advisor keeps returning `confirm` while `.proposed/` exists un-promoted (it can't tell "still editing" from "ready"), so **only on the user's explicit go-ahead** do you run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --confirm --area <area>` (promotes `.proposed/` → `_reference/`, writes manifest + A–H skeletons, stamps `sources.yaml` hashes). If the user just says "continue" without confirming, re-show the gate. |
| `fill` | Dispatch a **`consult-drafter` subagent** for each slug in `details.unfilled` — **all in one batch, in parallel** — with `{area, slug, title, sources: <its touches list from sources.yaml>, mode: first-draft}`. **M11 waves:** `details.unfilled` is the *current wave only* — slugs whose `upstream` hints (manifest) are already drafted; `details.deferred` lists what waits for a later wave (dispatch nothing for those — the advisor surfaces them next pass, once this wave clears their sentinels). When `details.upstream_files` has an entry for a slug, add `upstream: [<those paths>]` to that drafter's dispatch (read-only seam context). Collect compact statuses. Then move **fully-consumed** sources (below) — pass the set of successfully-filled slugs to `sources.py mark-processed` as **`--filled`** (never `--updated`; see "Moving inputs"); a source moves only when its whole `touches` set is filled. Partial-batch failure is fine: unfilled procedures keep their sentinel and re-dispatch next pass. |
| `ingest_returns` | Review-kit returns landed in `_review/returned/`. Run the deterministic ingest chain yourself, **in this order**: (1) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/screens_ingest.py" <area>` (pulls pasted screenshots → `_assets/screens/`, archives templates); (2) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gaps_ingest.py" <area>` (workbook answers → notes, archives workbooks); (3) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_apply.py" <area>` (tracked changes applied mechanically; failures become notes; does NOT archive); (4) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_extract.py" <area>/_review/returned --comments-only --area <area>` (comments → notes, archives the docs). Report the applied/noted split. Zero tokens spent; the advisor then routes any notes to `apply_review`. |
| `apply_review` | For each `{area}/_review/*.notes.yaml` in `details.notes`, dispatch a **`consult-drafter` subagent** with **only** `{area, slug, mode: update, review_notes: _review/{slug}.notes.yaml}` (one trigger — no `sources` list; the drafter reads its own draft + registry + the notes). Batch/parallel. **The dispatch shape does not change when a note carries new source material**: an item may be `kind: source` with `src: SRC-<id>`, and the drafter resolves that id through `_reference/sources.yaml` itself — you still paste no source paths and no source text. Then, after the batch succeeds: (1) archive the applied notes to `_review/processed/` (the `archive-review` command below), and (2) credit the retirement ledger — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sources.py" mark-processed <area> --updated <slugs that succeeded>`. **Never pass update slugs as `--filled`** — that credits every source whose `touches` names the slug regardless of kind, so a plain reviewer comment would retire a source no drafter ever read (silent loss of client material). If `details.unassigned` is set, also tell the user that `_review/_unassigned.notes.yaml` holds reviewer items that couldn't be attributed to a procedure and needs their triage. Orphaned notes may ride along in `details.orphan_notes` — mention them, and expect a `review_triage` gate once the applicable notes are archived. |
| `review_triage` | **HUMAN GATE.** Reviewer material no drafter can consume. Two shapes, told apart by which key is set (M18/F1): (a) `details.unassigned` — items `review_extract.py` couldn't attribute to a procedure; tell the user to open `_review/_unassigned.notes.yaml` and either move each item into the right `_review/{slug}.notes.yaml` or delete/archive the file. (b) `details.orphan_notes` + `details.orphan_slugs` — notes whose basename names **no live manifest procedure**, so a drafter has nothing to update and the note can never archive; relay `details.resolutions` verbatim (restore the procedure, or archive the note to `_review/processed/`). Then re-invoke. Stop. |
| `aggregate` | Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aggregate.py" <area folder path>` (this script does NOT resolve bare names under components/). Non-zero exit (fail-loud on a malformed callout) → surface + stop. Unmatched-mention WARNINGs → `registry_topup` gate. |
| `registry_topup` | **HUMAN GATE.** List the flagged systems/roles (`details.warnings`); tell the user to add entries/aliases to `_reference/` and re-invoke. Stop. On re-invoke the registry edit changes `registry_hash`, so the advisor returns `aggregate` again — the top-up loop re-runs aggregate and clears (or re-flags) the warning. |
| `draft_ready` | **HUMAN GATE (guard 8.5) — a resting gate, not a failure.** The area is fully drafted and reconciled clean, and the next move is the first one that costs something: `details.would_spend` says which (`synthesize` = 2 agents, or `render` = a human review round). Put `details.question` to the user ("am I happy with the verbs and the nouns before anything else is paid for?") and present the three options in `details.answers` — the list is the gate's stable shape, so read them from the JSON rather than reciting them: **read** (free) — the `command` field carries the real `--slugs` list for a procedures-only render; **consolidate** — `command: null` because the M12 consolidator is not built yet, so say that plainly and do not improvise a substitute; **accept** (free) — `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/orchestrate.py" accept-draft --area <area>`. Note the advisor prints repo-relative script paths in `answers[].command` (it has no `CLAUDE_PLUGIN_ROOT`), so prefix `python3 "${CLAUDE_PLUGIN_ROOT}/"` as you do everywhere else. Stop. Only on the user's explicit acceptance do you run `accept-draft` (the sole writer of `.draft_ready.json`), then re-loop. A `--slugs` read-render never writes `.render.json`, so showing the user the draft does not advance the machine and does not need a checkpoint. |
| `unresolvable` | **STOP — a resting gate (guards 5a/5b/8), `human_gate: true`, exit 0.** The folder is consistent and the ladder is simply out of moves: **no action can change the state that selected it.** So do NOT retry the action that led here, do not re-run the stage the state mentions, and do not invent a workaround. Report, verbatim and in this order: `details.state` (what was detected), `details.why_no_stage` (why no stage clears it), `details.human_action` (the specific fix — it is written to be actionable, including the exact command where one exists). Then add whatever evidence keys are present: `details.stranded_ids` (the `SRC-` ids stranded in `_sources/new/`, with `stranded_sources` carrying each one's `touches`/`consumed`), `details.missing_procedures` (manifest slugs whose fragment file is gone), `details.failing_files` + `details.dangling_refs` (reconcile failures no producer can regenerate). End the turn. |
| `error` | **ABORT the run.** `next` exited **2** and read no state at all: the area folder does not exist (`details.missing_folder`). This is a wrong `--area` — a typo, or a bare name that resolves to `components/<name>` and was never scoped. It is deliberately not a gate, so do not checkpoint and do not re-loop. Show the path it tried, ask the user for the right area name, and stop. |
| `synthesize` | Dispatch the M5 judgment subagents — `consult-dependencies`, `consult-raci` — one each (they self-scope to changed procedures via the delta). Compact returns only. **Then, for each kind whose agent wrote successfully, rebaseline the change signal yourself:** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scope_delta.py" commit --folder <area> --kind dependencies` (and `--kind raci`). This is the ONLY writer of the `.hashes.json` baseline the advisor reads — skip it and guard 9 keeps returning `synthesize` forever. Commit a kind only after its agent succeeded (a failed agent keeps its stale baseline so it re-dispatches next pass). |
| `reconcile` | Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py" <area folder path>` over the whole area (the hard gate; folder path, not a bare name). Any ERROR → surface + stop; don't render over it. |
| `render` | Run the renderer (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" <area> -o <out.docx>`) — only after `reconcile` is clean. Default is `--mode working` (everything visible + provenance anchors). Then emit the per-owner review kits: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kits.py" <area>`. Give the user the docx path + `_review/kits/index.md`. When the user asks for the **client-facing deliverable**, render `--mode final` instead (strips open gaps, embeds captured screenshots; report its stripped/embedded counts) — final mode emits no kits. Note (M21): a final render is an **export, not a pipeline state** — it never writes `.render.json`, so it cannot re-open the `review` gate or discard an `accept` that already happened. The advisor's answer is unchanged by it; hand over the file path and carry on from whatever the state actually is. |
| `review` | **HUMAN GATE.** The resting state after render. Give the `.docx` path (`details.docx`) and point at `_review/kits/index.md` — the user sends each kit folder to its owner. Returned files (reviewed docs, gap workbooks, screenshot templates) go into `_review/returned/` (→ `ingest_returns` next invoke). The user can also review the full draft directly, **or explicitly accept**. Stop. The advisor keeps returning `review` while `awaiting_review` is set — only on the user's explicit acceptance do you run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/orchestrate.py" accept --area <area>` (the only writer that clears the flag), then report `done`. |
| `done` | Report: what's current, where the `.docx` is, nothing outstanding. Stop. |

## Parallel fan-out

`fill` and `apply_review` dispatch **N subagents in one batch** (one per procedure)
so they run concurrently. Wait for all, collect the compact statuses, then
continue. Never fill procedures one-at-a-time in sequence.

## Moving inputs (you own this, not the subagents)

- After a `fill` batch, call `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sources.py" mark-processed <area>
  --filled <slugs…>` with the slugs that **succeeded**. A source moves
  `_sources/new/ → processed/` (and flips `sources.yaml` state) **only when its
  whole `touches` set is filled** — so a source spanning a failed procedure stays
  in `new/`. Never move a source before its procedures fill.
- After an `apply_review` batch succeeds, do **both** of these:
  1. archive the applied notes —
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sources.py" archive-review <area> --slugs <slugs…>`
     (add `--docx <path>` to also archive the consumed `.docx`); it moves them to
     `_review/processed/`.
  2. credit the ledger —
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sources.py" mark-processed <area> --updated <slugs…>`,
     again only the slugs that **succeeded**. Skip this and a source whose notes
     were applied is never retired: it sits in `_sources/new/` already assessed,
     nothing can consume it, and the next pass rests at the `unresolvable` gate
     naming its `SRC-` id.
- **Why the two flags differ — this is the whole of M6's bus contract.**
  `--filled` is a FIRST-DRAFT fill, and the fill dispatch hands the drafter the
  slug's *entire* tagged source list, so a successful fill provably consumed every
  source that `touches` it: credit is unconditional. `--updated` is an UPDATE
  batch, where the notes decide what the drafter actually read — so credit
  requires **evidence**: a `kind: source` item in that slug's notes naming the
  source's id. A reviewer comment, a rename note or a consolidation finding on the
  same procedure credits nothing. Pass update slugs as `--filled` and you destroy
  exactly that distinction: every source touching the slug is retired on the
  strength of a note that never mentioned it, and the client material it carried
  is silently lost. The two flags are cumulative and cross-batch — `consumed:` on
  each source entry accumulates and is never reset, so a source spanning one new
  and one existing procedure retires when the union of the two batches covers its
  `touches`, in either order and any number of passes apart. Both flags accept
  several slugs (`--filled a b c`), and you may pass both in one call.

## Human gates — stop cleanly

At `confirm`, `review_triage`, `registry_topup`, `draft_ready`, `unresolvable`
and `review` — anything carrying `human_gate: true`: post a short, specific
message (what to edit / review, where, and "re-invoke me to continue"), then
**end the turn.** Do not cross a gate on your own. When re-invoked, the advisor
re-derives state and picks up from there.

Two of them have a **named writer for their crossing** and nothing else may
cross them: `review` clears only via `orchestrate.py accept`, and `draft_ready`
only via `orchestrate.py accept-draft`. `unresolvable` has no such verb by
design — it is the one gate whose crossing is a human editing the folder.

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
