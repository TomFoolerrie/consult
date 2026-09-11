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
