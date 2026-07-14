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
(change-scoped). When the user asks "what will X cost", answer from this
boundary: count the drafter dispatches, everything else is zero.

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
| `.aggregate.json` | last aggregate basis + registry-warning list (top-up gate reads this) |
| `.hashes.json` | per-derived-kind procedure-hash baseline; ONLY `scope_delta.py commit` writes it — skip it after synthesize and guard 9 fires forever |
| `.reconcile.json` | `{basis, clean}` — render is gated on clean at the current basis |
| `.render.json` | `{basis, docx, awaiting_review}` — the review resting state |
| `_review/kits/` | derived send-outs; regenerate freely with kits.py |
| `_review/returned/` non-empty | un-ingested returns → `ingest_returns` outranks everything below confirm |
| `_review/*.notes.yaml` | judgment work queued for drafters (merge-appended; multiple sources) |
| `_review/_unassigned.notes.yaml` | items no procedure owns → human triage gate |
| `_review/.maps/*.json` | render provenance (apply anchors); never hand-edit |
| `_assets/screens/<slug>/SC-*.png` | captured evidence; final render embeds; hand-dropping a file here is first-class |
| `_client/org-chart.yaml`, `taxonomy.yaml` | optional client context: person→role grounding + L1 boundary authority (taxonomy agent reads; reconcile enforces names) |
| scope note comment in a skeleton | merged variant pair — drafter writes shared flow once, branches at divergence |

### Failure playbook

- **Advisor returns the same action twice with no progress** → the stage
  didn't write its signal file or didn't do its work; report the stage bug,
  don't loop.
- **aggregate exits non-zero** → a malformed callout in ONE fragment
  (fail-loud names it). Dispatch that procedure's drafter (update mode) with
  the error text; never hand-fix.
- **reconcile ERRORs** — route by class: ID grammar / dangling ID / bare gap
  tag → that fragment's drafter. Dangling `[[slug]]` → whoever wrote it
  (fragment drafter, or RACI/dependencies agent for 82/84). NAMED INDIVIDUAL
  → drafter for that fragment (role-only rule; roles.yaml `people` has the
  mapping). Derived-row pair unknown → re-run aggregate first (stale view)
  before suspecting a fragment. Manifest/order errors → scaffold-level;
  surface to the human.
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
  if action is a HUMAN GATE: stop, tell the user what to do, end turn
  if action == done: report and stop
  else: repeat
```

`orchestrate.py` is **read-only** — it never mutates; it derives the next action
from folder state (see M7). Re-running is always safe. Because it cannot run the
mutating stages itself, each deterministic stage leaves a small git-ignored
state file at the area root that the advisor reads next loop: `aggregate.py` →
`.aggregate.json` (`{proc_hashes, registry_hash, warnings}`); the synthesis pass
→ `.hashes.json` (procedure hashes, the M5 change signal); `reconcile.py` →
`.reconcile.json` (`{basis, clean}`); the renderer → `.render.json`
(`{basis, docx, awaiting_review}`). A stage that doesn't write its file reads as
"never ran", so its guard keeps firing — surface that as a stage bug, don't loop
blindly. The action JSON carries `{action, reason, human_gate, details}`.

## Action handlers

Run scripts yourself; dispatch subagents for judgment. Dispatch prompts carry only
paths/ids — never pasted content.

| action | what you do |
|---|---|
| `taxonomy` | Dispatch **one `consult-taxonomy` subagent** with `{area, l1, taxonomy_path, mode}` (`mode=initial` if no manifest, else `incremental`). If `{area}/_client/` exists (optional `org-chart.yaml` / `taxonomy.yaml`), say so in the dispatch prompt so the agent reads it. It writes proposals to `_reference/.proposed/`. Relay its compact summary → this leads to the `confirm` gate. |
| `confirm` | **HUMAN GATE.** Show the proposal summary (procedures by L2, merged variants + overlap flags, new-L2 requests, low-confidence items, unmapped people, out-of-L1). Tell the user to edit `_reference/.proposed/` and reply **"confirm"** when ready. Stop. — The advisor keeps returning `confirm` while `.proposed/` exists un-promoted (it can't tell "still editing" from "ready"), so **only on the user's explicit go-ahead** do you run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --confirm --area <area>` (promotes `.proposed/` → `_reference/`, writes manifest + A–H skeletons, stamps `sources.yaml` hashes). If the user just says "continue" without confirming, re-show the gate. |
| `fill` | For each procedure still carrying the `unfilled` sentinel, dispatch a **`consult-drafter` subagent** — **all in one batch, in parallel** — with `{area, slug, title, sources: <its touches list from sources.yaml>, mode: first-draft}`. Collect compact statuses. Then move **fully-consumed** sources (below) — pass the set of successfully-filled slugs to `sources.py mark-processed`; a source moves only when its whole `touches` set is filled. Partial-batch failure is fine: unfilled procedures keep their sentinel and re-dispatch next pass. |
| `ingest_returns` | Review-kit returns landed in `_review/returned/`. Run the deterministic ingest chain yourself, **in this order**: (1) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/screens_ingest.py" <area>` (pulls pasted screenshots → `_assets/screens/`, archives templates); (2) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gaps_ingest.py" <area>` (workbook answers → notes, archives workbooks); (3) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_apply.py" <area>` (tracked changes applied mechanically; failures become notes; does NOT archive); (4) `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_extract.py" <area>/_review/returned --comments-only --area <area>` (comments → notes, archives the docs). Report the applied/noted split. Zero tokens spent; the advisor then routes any notes to `apply_review`. |
| `apply_review` | For each `{area}/_review/*.notes.yaml` in `details.notes`, dispatch a **`consult-drafter` subagent** with **only** `{area, slug, mode: update, review_notes: _review/{slug}.notes.yaml}` (one trigger — no `sources` list; the drafter reads its own draft + registry + the notes). Batch/parallel. Archive applied notes to `_review/processed/` after success. If `details.unassigned` is set, also tell the user that `_review/_unassigned.notes.yaml` holds reviewer items that couldn't be attributed to a procedure and needs their triage. |
| `review_triage` | **HUMAN GATE.** Only unattributed reviewer items remain (`details.unassigned`). Tell the user to open `_review/_unassigned.notes.yaml` and either move each item into the right `_review/{slug}.notes.yaml` or delete/archive the file, then re-invoke. Stop. |
| `aggregate` | Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aggregate.py" <area>`. Non-zero exit (fail-loud on a malformed callout) → surface + stop. Unmatched-mention WARNINGs → `registry_topup` gate. |
| `registry_topup` | **HUMAN GATE.** List the flagged systems/roles (`details.warnings`); tell the user to add entries/aliases to `_reference/` and re-invoke. Stop. On re-invoke the registry edit changes `registry_hash`, so the advisor returns `aggregate` again — the top-up loop re-runs aggregate and clears (or re-flags) the warning. |
| `synthesize` | Dispatch the M5 judgment subagents — `consult-dependencies`, `consult-raci` — one each (they self-scope to changed procedures via the delta). Compact returns only. **Then, for each kind whose agent wrote successfully, rebaseline the change signal yourself:** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scope_delta.py" commit --folder <area> --kind dependencies` (and `--kind raci`). This is the ONLY writer of the `.hashes.json` baseline the advisor reads — skip it and guard 9 keeps returning `synthesize` forever. Commit a kind only after its agent succeeded (a failed agent keeps its stale baseline so it re-dispatches next pass). |
| `reconcile` | Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py" <area>` over the whole area (the hard gate). Any ERROR → surface + stop; don't render over it. |
| `render` | Run the renderer (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" <area> -o <out.docx>`) — only after `reconcile` is clean. Default is `--mode working` (everything visible + provenance anchors). Then emit the per-owner review kits: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kits.py" <area>`. Give the user the docx path + `_review/kits/index.md`. When the user asks for the **client-facing deliverable**, render `--mode final` instead (strips open gaps, embeds captured screenshots; report its stripped/embedded counts) — final mode emits no kits. |
| `review` | **HUMAN GATE.** The resting state after render. Give the `.docx` path (`details.docx`) and point at `_review/kits/index.md` — the user sends each kit folder to its owner. Returned files (reviewed docs, gap workbooks, screenshot templates) go into `_review/returned/` (→ `ingest_returns` next invoke). The user can also review the full draft directly, **or explicitly accept**. Stop. The advisor keeps returning `review` while `awaiting_review` is set — only on the user's explicit acceptance do you report `done`. |
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
- After an `apply_review` batch succeeds, archive the applied notes with
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sources.py" archive-review <area> --slugs <slugs…>`
  (add `--docx <path>` to also archive the consumed `.docx`); it moves them to
  `_review/processed/`.

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
