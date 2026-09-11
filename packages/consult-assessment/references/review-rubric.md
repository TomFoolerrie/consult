# Findings review rubric — for the human at the gate

Read the findings table as the partner would. Questions in the order they usually fail. Verdict is **proceed** or **rerun** (with what to change in `prompts/reader.md`).

| check | healthy | rerun signal |
|---|---|---|
| Count per interview | ~8–25 | <5 (it summarized) or >40 (it logged every sentence) |
| Specificity | any five findings, you know what was seen and where without opening the source | "controls are weak", "process is manual" — no what, no where |
| Citations | `lint.py cite` on five random findings: the lines say what the finding says | lines are adjacent-but-not-quite, or the finding overreaches them |
| Severity | spread across 1–3 | all 2 (scale unused) or all 3 (advocating) |
| Evidence basis | interviews mostly `stated`; `inferred` rows say so in their text | everything `observed`, or inferences presented as fact |
| Strengths | at least one per interview | zero — the story has nothing to validate the client with |
| Tagging | findings tagged to the specific area they belong to; catch-all values rare | catch-alls stacked on specific things (default taxonomy: Entity-Level / Pervasive / Governance on a cycle-specific gap) |
| Cross-document links | second interview's findings reference the first's where they overlap (`related`) | `related` empty everywhere — batching isn't paying off |
| Duplicates within group | none from the same document | same fact logged twice from one interview |
| One thing per finding | yes | "no JE approval and clawbacks unreconciled" in one row; "and"/semicolon joining two problems |
| Engagement vs client | "not discussed" / "PBC outstanding" logged as `open_item` | absence-of-discussion logged as a gap, especially with `evidence_basis: observed` |
| Coverage | `trace` shows every in-scope primary-axis category populated | UNCOVERED categories nobody decided to exclude |

A few bad rows with the pattern right → **proceed**; normalize and revise exist for that.
A wrong pattern → **rerun**; say which row of this table failed and the orchestrator rolls back and re-runs the same group after the prompt fix.
