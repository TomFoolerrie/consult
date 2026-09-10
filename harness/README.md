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

Environment the worker classes assume: Python 3.11 with python-docx (render)
and duckdb + pyarrow (data-wrangle / data-analysis over Parquet).

## The pulse (A19, resolved into existing verbs)
There is no `consult pulse`. Unattended maintenance is two existing verbs
on a timer, from outside the engine — e.g. hourly:

```
0 * * * *  cd /path/to/engagement && export PATH=/path/to/consult/bin:$PATH && consult check && consult checkpoint pulse
```

`checkpoint` on a clean tree is a no-op commit attempt; on a dirty tree it
is autosave with an audit trail, labelled `pulse` so it never reads as a
judged checkpoint. `consult state` carries the clock (ages); the
consultant's prompt carries the mirror. Nothing here ranks, proposes, or
gates.
