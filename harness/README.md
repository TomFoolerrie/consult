# harness — the layer between the engine and the models

Not engine. The engine is `consult <verb>` (bin/consult on PATH). The harness
is how the abstractions land on the Claude Code substrate:

| abstraction | on the substrate |
|---|---|
| the consultant seat | `<root>/CLAUDE.md` — whoever opens the folder with `claude` IS the consultant; the file is agents/consultant.md + agents/system.md + substrate notes |
| the three worker classes | `<root>/.claude/agents/worker-{haiku,sonnet,opus}.md` — model pinned, tool surface fixed, ~20 lines each |
| dispatch | the Agent tool with `subagent_type: worker-<class>` and `prompt` = the output of `consult brief …` — the brief IS the skill delivery |
| spend accounting | the Agent result reports usage; the consultant runs `consult spend` right after |
| the two gates | a question to the human in the chat, recorded with `consult gate` / `ask accept` |
| the client | not in the chat — files arrive in `_sources/new/`, the human relays; for synthetics, `harness/client.ts` plays the client from a script.yaml |

`install.ts <root> [--objective file]` puts all of it into an engagement folder
(skeleton, pads, seat, classes, permissions, first commit). Idempotent on the
prose files. Tests: tests/harness.test.ts. Run a live engagement:
synthetic/engagement-4/RUNBOOK.md.

The ENVIRONMENT must provide Python 3.11 with python-docx (render) and
duckdb + pyarrow (data-wrangle / data-analysis over Parquet); the worker
classes ASSUME it is there and nothing checks at dispatch time. Install
it before the first live run — a missing library surfaces as a worker
failing mid-dispatch, not as a named refusal.

## Assessment evidence adapter (partial integration)

`assessment-evidence.ts` reads assessment's versioned findings ledger using
engine source IDs and produces checked citations/excerpts as JSON or a Markdown
review pack. It is read-only and does not replace the assessment runner or its
schema/layer validators. Usage and boundaries:
[ASSESSMENT-EVIDENCE.md](ASSESSMENT-EVIDENCE.md).

## The conformance kit (A27) — the dynamic half of the skill contract

`consult skill check <name>` is the STATIC half (manifest valid, ports
declared, runtime entry present, no `[HUMAN]`/gate vocabulary in a level-2
runner). `harness/conformance.ts` is the DYNAMIC half: it RUNS a skill against
a known engagement and proves from the filesystem that it stayed inside its
walls. It writes nothing and repairs nothing — it reports.

```
conform(root, { skill, run, expectReturn? }) → { ok, findings }
```

`run(root)` is whatever exercises the skill: a scripted stub in the suite, a
real dispatch in life, a shell command from the CLI. `conform` snapshots every
file path + sha256 under `_sources/`, `_registers/`, `capture/`, `_synthesis/`
plus `STATE.md` and `OBJECTIVE.md`, runs it, snapshots again, and reports each
of these as a finding NAMING the offending path:

- any change under `_sources/` — only `_sources/sources.yaml` GAINING entries
  is allowed (publication); an edited, deleted or re-hashed existing entry is not;
- any change under `_registers/`, `STATE.md`, `OBJECTIVE.md` — a skill writes
  none of these: it returns, and the CONSULTANT lands the return;
- any change under `capture/`, unless the skill's manifest declares
  `writes: capture-fragment` (the `procedure-draft` grant). The manifest is read
  as plain YAML from `<root>/_skills/` then `kernel/skills/` (level 1
  `<name>.yaml` or level 2 `<name>/skill.yaml`). The grant is honoured coarsely
  in this first kit: WHICH fragment the brief named is not checked here — the
  checkpoint diff still audits that;
- any new file under `_synthesis/` outside `_synthesis/<skill>/`, and any
  modification or deletion of a work product already published (immutable);
- any new synthesis artifact without a card (A22);
- any source registered before the run whose bytes no longer verify;
- with `expectReturn`: a missing return file, one that does not parse as YAML,
  one lacking `skill:` or `run:`, one written INSIDE a store, or one carrying
  `[HUMAN]` text — a skill never stops for a human;
- any `consult check` ERROR the run introduced (pre-existing errors are not the
  skill's).

How a skill author runs it:

```
node --experimental-strip-types harness/conformance.ts <root> <skill> \
    [--return <return-file>] -- <command…>
```

The command runs with the engagement root as its cwd and stands in for the
dispatch. Exit 0 means it conforms; exit 2 prints one `finding:` line per
violation. Build the known root with
`harness/fixtures/conformance/engagement.ts` (`conformanceFixture()`): the
skeleton, two routed sources (markdown + CSV), one fragment carrying a question
record, and one accepted ask, all landed through the library's own doors.
Tests: tests/conformance.test.ts.

## The pulse (A19, resolved into existing verbs)
There is no `consult pulse`. Unattended maintenance is two existing verbs
on a timer, from outside the engine — e.g. hourly:

```
0 * * * *  cd /path/to/engagement && export PATH=/path/to/consult/bin:$PATH && consult check; consult checkpoint pulse
```

The separator is `;`, NOT `&&`, deliberately: `consult check` exits 2
whenever the record carries an error, and an unattended autosave must
not be blocked by a defect the consultant has not fixed yet. The check
still runs, and its output still lands in the cron log — it just does
not gate the save. Note that a declared INTENT for a fragment not yet
written is a WARNING, not an error, so an in-flight fold-in does not
make the cron line noisy.

`checkpoint` on a clean tree is a no-op commit attempt; on a dirty tree it
is autosave with an audit trail, labelled `pulse` so it never reads as a
judged checkpoint. `consult state` carries the clock (ages); the
consultant's prompt carries the mirror. Nothing here ranks, proposes, or
gates.
