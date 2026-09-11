# Changelog

## CONSULT integration working copy — text and CSV

Imported from the supplied 0.6.1 archive; original ZIP preserved. Added explicit
CONSULT manifest mode, shared source lookup/citations, combined validation,
integrated shim/brief boundaries, and non-destructive rerun guidance. Standalone
mode remains available. CSV analysis now consumes verified snapshots, uses
record-level citations, and publishes immutable artifacts through the engine
with every input/hash declared. Added a scripted fictional demonstration with
review corrections, new evidence and revised conclusions. See `INTEGRATION.md`
for the archive hash, exact supported scope, all-green repository tests and
unavailable standalone companion dependencies.

## 0.6.1 — 2026-09-02 (pre-handover verification)

- `tests/loop.sh`: the orchestrator's exact path — a bare engagement dir with spaces in its name, driven only by `run.py next` from "no registry" to `[DONE]`, agents simulated, 24 assertions. Run this on the work machine first.
- All test scripts are now safe under skill and engagement paths containing spaces, and no longer hardcode any path. Verified from a fresh unzip into `/tmp/fresh install (x)/`, and again with cp1252 stdio + C locale.
- pyflakes clean on every script; syntax verified against Python 3.9; only third-party dependency is pyyaml (openpyxl optional, lazy).
- Brief: tabular kind now wins over size (a 6-line CSV is TABULAR, not "read fully"); drafter orders a group interviews → summary → artifacts → data so a reader hears the claim before it sees the artifact that tests it.
- `lint.py register --exclude NAME` for a context file kept among the sources (e.g. `profile.md`).

## 0.6 — 2026-09-02 (building on earlier groups)

**What the orchestrator must do differently**

- Groups may declare `builds_on: [G1, G4]` or `builds_on: all`. The reader's brief then carries a compact index of those groups' findings (id, type, severity, evidence basis, category, first line, sources), the open items earlier readers left, and the categories with nothing logged yet — placed **after** the sources. The reader prompt enforces two passes: extract blind from its own sources, then situate (set `related`, log corroborating evidence, name contradictions in the finding text, answer open questions). It never sees prior findings before its own extraction.
- `next` spawns in waves: a group waits until everything it builds on is complete. Set `builds_on` on artifact and data groups (the ones that test what interviews claimed), not on interview groups (anchoring risk). For the remaining groups of the current engagement, add `builds_on: all` to the data groups before spawning them.

## 0.5.1 — 2026-09-02 (grouping)

**What the orchestrator must do differently**

- Fewer, larger, coherent groups. A group is one question the assessment must answer, with every source that bears on it — interviews, the artifacts they mention, the data that tests what they claim, the transcript's summary — read by one reader. Split only when it would not fit (~35k source words). Overlap between groups is fine and cheap; a missed contradiction is not. Four to eight groups is typical; fourteen is splitting by size. Full rules in `references/manifest.md`.
- Ask the human to tag `topic:` on every source at annotation time (and `summary_of:` on transcript summaries). It is the single most useful field they fill: the drafter groups by topic across kinds, keeps summaries with their transcripts, and only falls back to by-interviewee / by-kind batching for untagged sources.

**Changes**

- `manifest.py draft`: topic-first grouping; `summary_of` pairing; `--budget-words` default 20000 → 35000; `--artifact-batch` 8 → 12; warns above `--max-groups` (8) with the merge advice. Group `note` now asks "what question should this reader answer?".
- `next` and the lint registry doc ask for `topic` and `summary_of`; the runbook tells the orchestrator to review the group count against the rules before spawning.

## 0.5 — 2026-09-02 (the reader as analyst)

**What the orchestrator must do differently**

1. Regenerate agents (`run.py agents …`): two new roles, `assess-retrospector` and (from 0.4) `assess-digester`. Restart the session after.
2. `next` now asks for a `retro` op after the fan-out completes and again after the story. One agent writes `<workdir>/retro-<phase>.md` in the format of the live orchestrator's own report (bugs / efficiency / findings quality / coverage / notes). Hand it to the human; forward the bugs section to the skill maintainer. Skip by creating the file empty.
3. Tabular sources are analyzed, not read. Readers now have `assess.py data profile <src>`, `data run <procedure> <src> …`, and `playbook`. Procedure outputs are written to `paths.analysis` (default `{out}/analysis` — deliverable side, keep it in git) and **auto-registered in the lint registry** as sources with `kind: analysis`, `derived_from: <src>`. Findings cite the source rows and the analysis together; `validate` accepts both. Do not edit or move analysis files after registration.
4. Digest: check whether your harness caches an identical prompt prefix across subagents before using it; if it does, skip the digest (create it empty). The runbook says so now.

**New**

- `scripts/data.py`: `profile` (format sniffing for csv/tsv/xlsx/markdown-table/jsonl; columns, types, blanks, ranges, samples, exact physical line numbers) and procedures `outliers`, `timing`, `group`, `duplicates`, `gaps`, `aging`, `blanks`, `filter`, `recon`. Every output has a `line` column mapping back to the source file.
- `references/data-playbook.md`: dataset kinds (JE listing, bank rec, AP/AR aging, TB/GL, payroll, commissions, other) → which procedures, and how to write a data finding.
- Reader prompt: the TABULAR strategy is now "profile, playbook, three to five procedures, cite rows + analysis"; a source with nothing material still gets one `observation` row ("reviewed in full; nothing material to scope") so coverage is proven rather than assumed — this also closes the per-source-completion hole where an empty source would look partial forever.
- `retro` op and prompt; `paths.retro`, `paths.analysis`; `assess.py playbook`.

**Sizes**: scripts ~2,100 lines Python; 8 agents; 9 references. Feature freeze from here until the layer prompts (themes → story) have run on real data.

## 0.4 — 2026-09-02 (from the first live run: 14 groups, 138 findings)

**What the orchestrator must do differently**

1. **Group completion is now per source.** A group is `complete` only when every declared source has a finding by its reader; otherwise `partial` or `not started`. `run.py status` shows `done/declared` per group and `next` refuses to move on while any group is partial — it re-issues extract for that group and the rendered brief is a **resume brief** (done sources marked `[DONE]`, remaining listed, same agent name so ownership holds). Check `status` now: any group whose reader was killed mid-run will show as partial and needs finishing.
2. **Deferred groups are a manifest field.** `deferred_groups:` holds groups that are not spawnable yet; `manifest.py draft` puts the first interview group in `groups:` and the rest there (`--all-groups` to disable). After the findings gate passes, `next` tells you to move them into `groups:`. If you stashed groups in a side file, put them under `deferred_groups:` instead.
3. **Digest before the fan-out.** If the shared pre-reads exceed ~250 lines, `next` asks for the new `digest` op once: `assess-digester` writes `<workdir>/context-digest.md` (120–200 lines), and every subsequent brief gives readers the digest instead of the raw pre-reads (raw files move to a *reference* list). Regenerate agents (`run.py agents`) so `assess-digester` exists. To skip, create the digest file empty.
4. **Restart the session after `run.py agents`.** Claude Code loads `.claude/agents/` at session start; the first spawn fails otherwise.
5. `run.py check` is fixed (0.3.2). Stop calling validate/trace directly; `check` and the shim's `trace` now also print coverage by primary-axis category with **UNCOVERED** and **THIN** lists.

**Reader behaviour changes (re-render briefs; regenerate agents)**

- Briefs mark a reading strategy per source from the registry's kind and size: *read fully* / *LARGE: structure + grep* / *TABULAR: header + sample + grep*. The static prompt says never to read a large document linearly.
- Summary + transcript in one group: read the summary as an index, then the transcript, log once with both citations — instead of logging from the summary and editing every row afterwards.
- New finding type `open_item` for "not discussed" / "PBC outstanding" / "follow up". Kept in the ledger, excluded from evidence, themes, and heat maps, rendered as `fig-open-items`. Validator warns when an open_item claims `evidence_basis: observed`. Normalizer proposes the retype.
- Compound-finding test sharpened ("and" / semicolon joining two problems = two findings). Cross-linking asked for explicitly.
- Observation-length warning moved from 400 to 600 chars, and the prompt says fix-or-move-on rather than explain.
- Context file is no longer duplicated into `pre_read`; a group may list `reference:` files that readers consult only if relevant.

**Fixes**

- `manifest.py draft` warns when `--out` is outside the engagement root (../ chains) and no longer injects `context` into `pre_read`.
- Displayed paths are normpath'd (`_client\..\..\x` no more).

**Coverage reporting**

- `trace --taxonomy` (and `check`, and the shim) print evidence findings per primary-axis category, with UNCOVERED (0) and THIN (≤2). The review rubric gains a coverage row; the runbook asks for a scope decision on every uncovered category before themes.

## 0.3.2 — 2026-09-02

**Fixes**

- `run.py check` built a `shell=True` command from an unquoted string and broke on any path with spaces (OneDrive / "Client (2026)"). It now runs validate and trace as argument lists; no `shell=True` remains in either skill.
- Every command line `run.py next` prints, and the environment block in briefs, now quotes paths that contain spaces or parentheses, so the orchestrator can paste them as-is.
- Smoke test runs check, next, render, and the shim from a root named `Client (2026) - OneDrive`.

## 0.3.1 — 2026-09-02 (Windows fixes)

**What the orchestrator must know**

- If an agent patched `common.py` in the installed skill to work around the `fcntl` failure, this drop **overwrites that patch**. Replace the whole skill folder; do not merge.
- The `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` wrapper is no longer needed anywhere; every script sets UTF-8 on its own stdio and opens every file with an explicit encoding.

**Fixes**

- Ledger lock: `fcntl` is POSIX-only, so every ledger write failed on Windows. `locked()` now uses `msvcrt.locking` on Windows (non-blocking acquire with retry, 120 s ceiling) and `fcntl.flock` elsewhere.
- Encoding: 30+ `open()` / `read_text` / `write_text` calls used the platform default (cp1252 on Windows), which would crash on the first em-dash or arrow in a finding. All now pass `encoding="utf-8"`; stdin/stdout/stderr are reconfigured to UTF-8 at import. Same fix in `consult-lint/lint.py`. Smoke test now round-trips non-ASCII under a simulated cp1252 console.

## 0.3 — 2026-09-02

**What the orchestrator must do differently**

1. Re-render every brief before spawning. Briefs and the shim are generated per op; any brief rendered before this drop contains long absolute paths and is stale.
2. Spawned agents run commands through a shim, not the skill scripts. `run.py render` now writes `<workdir>/assess.py` (path: `paths.shim`, default `{workdir}/assess.py`). The brief's environment block names the engagement root once and every command is root-relative: `python _workspace/assessment/assess.py ledger append findings ...`. Do not wrap commands with `PYTHONUTF8=1` or quote skill paths for agents any more; the shim sets encoding and `chdir`s to the root itself.
3. The loop can start before a manifest exists: `run.py next --root <engagement dir>`. It walks registration → registry annotation (HUMAN) → client profile (HUMAN) → draft manifest, then finds the manifest on its own. Use this as the entry point instead of checking for prerequisites yourself.
4. `manifest.py draft` now writes paths relative to the manifest file's directory (the documented contract). If you edited a drafted manifest by hand to fix doubled paths, re-draft.
5. `ledger.py` accepts `--ledger-dir` / `--taxonomy` before or after the subcommand. Both `ledger.py init --ledger-dir D` and `ledger.py --ledger-dir D init` work.

**Behavior changes**

- Shim commands: `ledger`, `validate`, `trace`, `check`, `cite`, `render`, `next`, `taxonomy` (prints the taxonomy so agents never need its path).
- Brief placeholders added: `{{sh}}`, `{{root}}`; `{{taxonomy}}` now renders as the shim command rather than a path. Paths shown to agents are root-relative; anything outside the root (rare) is shown whole.
- SKILL.md opens with a "When invoked — do this" section: run `run.py next --root .`, do the one line it prints, repeat.
- Every ledger write takes an exclusive file lock (`<ledger_dir>/.lock`); `append` reads and validates its whole batch before locking. Parallel readers no longer collide on ids (reproduced without the lock: five readers, one id).
- `run.py agents --with-orchestrator` also writes `assess-orchestrator` with `tools: Agent(assess-reader, ...)` and the runbook as its body.
- `render.py bundle` writes a client story variant (`<story>-client.md`, bracket ids and comments stripped) and includes both in the bundle.

**Fixes**

- Draft put the context file into `pre_read` without relativizing it (doubled path).
- Reader prompt claimed the ledger refuses findings without a line pinpoint; it refuses findings with no source, the validator warns on no line.
- Stale references to `--sources-dir`, `src-NNN.md`, triage, and hard-coded axis names removed from prompts and references.

## 0.2 — 2026-09-02

- Taxonomy declares the knowledge model (`axes`, `scales`, `figures`); no axis names in scripts or prompts. ITGC example taxonomy and `tests/smoke-house.sh`.
- Manifest `paths:` and `agents:` blocks; every location and agent name is the orchestrator's. `render.py --manifest`.
- Prompts split into static system prompt (`prompts/<op>.md`) and per-run brief (`prompts/<op>.brief.md`); `run.py render --format brief|full`; `run.py agents` writes Claude Code subagent files.
- `run.py` entry point: `next`, `render`, `check`, `gate`, `status`. Runbook rewritten around the loop; review rubric added.
- Ledger dir must be `init`ed inside git; `checkpoint` commits with layer counts; writes refuse unmarked dirs.
- Themes carry the `on_theme` axis (diagnosis); figures declare units (themes vs findings); process map, unthemed, and strengths figures; merge refused across evidence bases, `link` proposal kind.
- Validator resolves citations through the consult-lint registry: active id, unchanged hash, line within file.

## 0.1 — 2026-09-01

- Initial: findings → themes → recommendations → initiatives → story ledgers; ownership; layer-below rule; gates; nine figures; smoke test.
