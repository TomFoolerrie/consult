# Runbook — for the orchestrator

You drive this with one loop:

```
python3 $SK/scripts/run.py next --root <engagement dir>      # before a manifest exists
python3 $SK/scripts/run.py next --manifest <manifest>        # once it does (next finds it by itself if there is only one)
```

Before a manifest exists, `next` inspects the engagement dir and walks you through registration, registry annotation (human), the client profile (human), and drafting the manifest. After that it reads the ledgers, the manifest, and the recorded gates and prints exactly one line: `[RUN] <what to do>`, `[HUMAN] <what to hand over and how to record the answer>`, or `[DONE]`. Do the thing, then call `next` again. You never decide sequencing; you never fill a prompt placeholder by hand.

## The spawn boundary

Two ways to start an agent; pick one per harness.

**Claude Code subagents (preferred in Claude Code).** Once per install, `run.py agents --out <plugin>/agents/` (or `.claude/agents/`) writes six subagent definitions — `assess-reader`, `assess-normalizer`, `assess-themer`, `assess-recommender`, `assess-planner`, `assess-storyteller` — each with frontmatter (name, description, tools, model) and the static system prompt. Per op, `run.py render --op <op> [--group G] --format brief` writes `<paths.prompts>/<agent>.brief.md`: the per-run half — author identity, paths, sources, commands, the taxonomy-generated example, open proposals. Spawn with the Agent tool (formerly Task), passing the brief's *text* as the prompt:

```
Agent(subagent_type="assess-reader", description="extract G1",
      prompt=<contents of reader-G1.brief.md>, run_in_background=true)
```

One call per group in the same turn for the fan-out; wait for all to finish before `run.py check`. Ops map to subagents: extract/revise → reader, normalize → normalizer, themes → themer, recommend → recommender, plan → planner, story → storyteller.

If you are yourself a subagent rather than the main session, make sure your definition lists `Agent(assess-reader, assess-normalizer, assess-themer, assess-recommender, assess-planner, assess-storyteller)` in `tools` and test one spawn before relying on it — nested spawning has open issues. `run.py agents --with-orchestrator` writes an `assess-orchestrator` subagent with that allowlist and this runbook as its body, for running an engagement from a bare Claude Code session: *"Use the assess-orchestrator subagent on manifest …"*.

**Any other harness.** `run.py render` without `--format` writes a complete, self-contained file (static body + brief). Start an agent whose instructions are that file.

Every brief starts with an environment block that names the engagement root and a command shim (`<workdir>/assess.py`, written by `render` with all long paths baked in). Agents see one absolute path — the root — and run short root-relative commands like `python assessment/work/assess.py ledger append findings ...`. This matters on Windows/OneDrive layouts where skill and ledger paths run to 150+ characters with spaces; agents should never have to reproduce those.

Either way the agent's *author identity* comes from the brief (`reader-G1`, from the manifest's `agents:` block and each group's `agent`), not from the subagent definition name. `revise` is the same reader as `extract`, in edit mode; ownership survives because the author name is the same.

Regenerate the subagent files whenever `prompts/*.md` changes; briefs are regenerated every op anyway. **Claude Code loads `.claude/agents/` at session start** — after writing them, restart the session (or run `/agents`) before the first spawn, or the spawn will fail with an unknown subagent type.

## What `next` will walk you through

**Before the loop can start** — things only a human can supply. Ask for them if missing (and, in Claude Code, run `run.py agents` once):
- the engagement dir is a git repo;
- `registry.yaml` in the sources dir has `kind` filled on every source, `people` on interviews, `pre_read_candidate` on context documents, and — the most valuable one — `topic` on each source (the question it bears on: "close", "commissions", "cash & escrow"…) plus `summary_of` on transcript summaries. Run `lint.py register`, hand the human `lint.py status`, wait. Then `lint.py verify` and commit;
- a client profile at the manifest's `context` path (one page: business, size, finance team, systems, why the engagement exists, what the client thinks the problem is);
- a manifest: `manifest.py draft` then edit `run`, the `paths:` and `agents:` blocks to match the engagement layout, each group's `note` (the question that group answers), and add `engagement_objective`/`notes` to `pre_read`. **Review the group count against the grouping rules in `references/manifest.md`**: fewer, larger, coherent groups — one per question, related interviews + artifacts + data together, ~35k source words each, overlap allowed. If the draft produced more than eight, that is splitting by size; merge. The drafter puts the first group under `groups:` and the rest under `deferred_groups:`; `next` tells you when to restore them.

**Then the loop.** In order, `next` will hand you: init → (digest, if the shared pre-reads are large) → extract first group → `[HUMAN]` findings gate → restore deferred groups → fan out → normalize → revise per author until `check --gate themes` is clean → `[HUMAN]` second look → themes (surface orphans) → recommend → plan → render figures/tables → `[HUMAN]` fill `story_note` if still TODO → story → bundle → `[DONE]`.

**Group completion is per source, not per author.** A group counts as extracted only when every source it declares has at least one finding by its reader. A reader that dies halfway leaves the group `partial`; `next` insists on finishing it before anything else, and the re-rendered brief is a resume brief (done sources marked, remaining listed) for the same agent name, so ownership holds. `run.py status` shows `done/declared` per group. Never trust "the author has findings" as completion — that is how seven policy documents nearly vanished from an assessment.

**Deferred groups.** `manifest.py draft` puts the first interview group under `groups:` and the rest under `deferred_groups:`. After the findings gate passes, `next` tells you to move them into `groups:`; readers can't be spawned for deferred groups, and `status` lists them so nothing is forgotten.

**Waves.** Groups with `builds_on:` wait until those groups are complete; `next` prints each spawnable wave. Typical: interviews blind and in parallel first, then artifact/data groups that build on them. A reader with `builds_on` gets the prior-findings index in its brief and follows the two-pass rule (blind, then situate); the index is never shown before the reader's own extraction.

**Data sources are analyzed, not read.** Readers get `data profile` / `data run` through the shim and a playbook (`playbook`) that maps dataset kinds (JE listing, bank rec, aging, TB, payroll, commissions) to procedures. Procedure outputs land in `paths.analysis` (deliverable side) and are auto-registered as sources with `kind: analysis`, `derived_from: <src>`, so findings cite source rows and the analysis together and `validate` accepts both. Never move or edit an analysis file after it is registered; re-run the procedure instead. Export xlsx to csv before registering if you want row-level citations.

**Retro.** After the fan-out completes, and again after the story, `next` asks for the `retro` op: one agent writes `<workdir>/retro-<phase>.md` — bugs, efficiency, findings quality, coverage, notes — in the format that the first live run's orchestrator wrote unprompted and that produced version 0.4. Hand it to the human alongside the findings; forward the bugs section to whoever maintains the skill. Skip by creating the file empty.

**Digest.** Check first whether your harness caches an identical prompt prefix across subagents — if it does, the duplicated pre-reads cost little and lose nothing, and you should skip the digest. If it doesn't: when the shared pre-reads (profile, objective, org chart, notes) run past ~250 lines, `next` asks for the `digest` op before the first reader: one agent writes `<workdir>/context-digest.md` (120–200 lines) and every reader loads that instead of the raw files, which are moved to *reference*. On a 14-group engagement this saves on the order of a hundred thousand tokens. To skip it, create the digest file empty.

After every op that wrote to the ledger: `run.py check --manifest M [--gate <layer>]` must exit 0, then `ledger.py checkpoint --ledger-dir <ledger_dir> -m "<op>"`. `next` reminds you, but the rule is yours.

## Gates

Record human decisions with `run.py gate --manifest M --name <gate> --status <status> [--note "..."]`. `next` won't advance past a gate that isn't recorded.

| gate | who | statuses |
|---|---|---|
| findings | human, after the first group | `passed` / `rerun` (note = which rubric row failed and the prompt change) |
| (coverage) | you, at the end of fan-out | not a gate but a check: `trace` prints UNCOVERED and THIN primary-axis categories; each is either a scope decision to record in the story note or a group to add |
| normalized | you, after the normalizer finishes | `done` |
| revise | human, after all readers have revised | `passed` |

Give the human the review pack for the findings gate: `ledger.py show findings --md` plus `lint.py cite` output for five random findings, and point them at `references/review-rubric.md`.

On `rerun`: `git checkout -- <ledger_dir> && rm -rf <workdir>`, apply the prompt change from the gate note, set the gate back to `pending`, and `next` will re-issue the same group. Never fix rows to satisfy the rubric — a wrong pattern is wrong everywhere.

## Watch the reader

While a reader runs, fail the run and treat it as `rerun` if it: writes to a `.jsonl` in the ledger dir directly; loops on `REFUSED`; skips a source; emits all findings at the end instead of per document. These are prompt problems and the gate note is where they get fixed.

## Rollback rules

- Ledgers roll back with git to the last checkpoint. Never by deleting rows.
- A source edited after registration fails validation on every citation into it. Re-register (new id), and the citing author re-cites. Don't paper over it.
- Work dirs are disposable; ledger dirs are the deliverable.
