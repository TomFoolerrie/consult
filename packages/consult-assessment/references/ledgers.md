# Ledger reference

All ledgers are JSONL under `ledger_dir`. Each line is a full row version; the current row for an id is its highest `version`. `ledger.py` is the only writer.

Meta fields on every row: `id`, `version`, `author`, `group`, `status` (active|retired), `created_at`, `edited_at`, `edit_reason`, `absorbed`.

## findings.jsonl  (F-NNN)
Method fields (every house):

| field | req | notes |
|---|---|---|
| type | y | gap / risk / strength / observation / open_item — open_item is a fact about the engagement (not discussed, PBC outstanding); kept for the workplan, excluded from evidence, themes, and figures |
| severity | y | `scales.severity` |
| evidence_basis | y | stated / observed / inferred |
| observation | y | one specific sentence or two |
| sources | y | `src-NNN:Lnn-Lnn`; pinpoint required by convention, warned if missing |
| related | n | other finding ids (corroborates / contradicts) |

Plus **one field per axis in the taxonomy** (`references/taxonomy.md`): single-valued or list per `multi`, required per `required` / `required_when`, `secondary_<axis>` where `secondary: true`. Values on `on_theme` axes are provisional on a finding.

## themes.jsonl  (T-NNN)
theme, root_cause, impact, findings[] — cites F ids only — plus **every `on_theme` axis** from the taxonomy as a required field (the diagnosis). Validator warns when the theme's value matches none of its findings' provisional values.

A theme has no axis values of its own except the `on_theme` ones. Its **footprint** on any other axis is the union of its findings' values there; figures count theme footprints for "how many problems" and findings for "how much evidence".

## recommendations.jsonl  (R-NNN)
solution, principle, what_changes, what_stops, themes[] (required), findings[] (optional direct).

## initiatives.jsonl  (I-NNN)
initiative, owner, impact (1–3), effort (1–3), time_required, dependencies[] (I ids), success_measure, recommendations[] (required).

## proposals.jsonl  (P-NNN)
proposer, target, target_author, kind (edit|retire|merge|link), reason, set{}, absorb[], status (open|accepted|rejected), resolution.

## Version control
`ledger.py init --ledger-dir D --git-init [ROOT]` creates the dir, writes `.assessment-ledger` (the marker every other command checks), and `git init`s ROOT (default: D's parent) if it isn't already in a repo. It also drops a `.gitattributes` with `*.jsonl merge=union` so two branches appending rows merge cleanly. `ledger.py checkpoint -m "..."` stages and commits the ledger dir with layer counts in the message. Append-only protects against bad edits; git protects against a bad `rm` or a write to the wrong path.

## Invariants (enforced by validate.py)
1. Findings need a source; every source matches the citation pattern and (with `--registry`) is an active registry entry whose file hash still matches and whose cited lines exist.
2. Axis values come from the taxonomy; `required` / `required_when` axes are present; multi/single cardinality holds; themes carry every `on_theme` axis.
3. Each layer cites only the layer below by id; never a raw source above findings.
4. Cited ids are active (not retired).
5. `--gate LAYER`: no open proposals on any lower layer.

## Ownership
`edit`, `retire`, `merge` refuse unless `--author` equals the row's author — for `merge`, the author of the survivor *and* every absorbed row. Everyone else uses `propose`. Author is the agent name from the manifest, so a re-spawned reader keeps its rights.

## Merge vs link
`merge` unions sources into the survivor but keeps the survivor's `evidence_basis`. Merging a `stated` interview claim with an `observed` artifact would produce a row that cites a signed document while reporting `stated`, and the coverage figure would miscount the evidence base. So the ledger refuses merges across evidence bases, and cross-author merges are already refused. The right move for cross-group duplicates is a **link**: each author adds the other id to `related`, both rows survive, and the theme layer binds them. Reserve `merge` for one author's own redundancy from the same evidence basis. Proposal kinds: `edit | retire | merge | link`.
