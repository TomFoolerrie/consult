---
name: consult-review-comment-resolver
description: Triage SOP reviewer comments, propose edits, create a response log, and flag items requiring SME validation.
---

# Review Comment Resolver Skill

## Purpose

Triage and resolve reviewer comments on SOP / desktop procedure deliverables without silently merging changes or masking unresolved validation items.

## Use This Skill When

Use this skill when the user provides:

- A `.docx` with reviewer comments
- Extracted Word comments
- A reviewer comment log
- A revised SOP draft plus reviewer feedback

## Operating Rules

- Do not silently accept reviewer edits.
- Preserve a response-to-comments trail.
- Distinguish factual corrections from preferences.
- Flag items requiring SME validation.
- Do not invent missing evidence to satisfy a comment.
- If a comment changes the procedure materially, recommend evidence audit follow-up.

## Comment Categories

Classify each comment as one of:

- `FACTUAL CORRECTION`
- `CLARIFICATION`
- `STRUCTURE / FORMATTING`
- `EVIDENCE REQUEST`
- `CONTROL / COMPLIANCE`
- `SCOPE QUESTION`
- `SME VALIDATION REQUIRED`
- `CLIENT PREFERENCE`
- `DUPLICATE / NO ACTION`

## Workflow

1. Extract or summarize each comment.
2. Assign a comment ID: `RC-001`, `RC-002`, etc.
3. Classify the comment.
4. Determine whether the comment can be resolved from available source material.
5. Propose the exact document edit.
6. Identify validation items.
7. Produce a response-to-comments log.

## Output Format

```markdown
# SOP Reviewer Comment Resolution Log — [Process Name]

## Summary

- Comments Reviewed: [count]
- Proposed Edits: [count]
- SME Validation Required: [count]
- Evidence Follow-Up Required: [count]

## Response-to-Comments Table

| Comment ID | Location | Reviewer Comment | Category | Proposed Resolution | Source / Evidence Basis | SME Validation Needed? | Status |
|---|---|---|---|---|---|---|---|
| RC-001 | Section / Step | ... | CLARIFICATION | ... | SRC-001 | No | Proposed |
```

## Revised Text Blocks

For each material edit, provide replacement-ready Markdown:

```markdown
### Replace Section / Step [X] with:

[Revised text]
```

## Status Values

Use:

- `Proposed`
- `Accepted for Update`
- `Needs SME Validation`
- `Needs Evidence`
- `Deferred`
- `No Action`

## Engagement flow: extract → classify → map → emit actions → apply

Inside a `consult` engagement, reviewer comments are not resolved by hand-editing
documents. They are turned into **structured actions applied through the
state/register commands**, attributed and logged, and made **idempotent** by a
consumed marker. The driver is `scripts/review_ingest.py` (T31), which reuses
`scripts/docx_comments.py` (T30) for the OOXML work and calls `scripts/state_machine.py`
for every mutation. Never re-parse the `.docx` yourself and never edit `state.json`
or `register.json` directly — go through these commands.

### 1. Extract (helper, deterministic)

```
python3 scripts/review_ingest.py extract \
    --engagement E --docx PATH/reviewed.docx --round N --out review/bundle.json
```

This runs `docx_comments.py`, computes the docx content hash, and:

- **If that hash is already in `engagements/E/review/consumed.json` → it skips**
  (prints `{"skipped": true, ...}`, touches nothing). This is the crash-replay
  guard: re-running extract on an already-applied docx is a no-op.
- Otherwise it emits the comments bundle (JSON: `{engagement, docx, hash, round,
  comments[], tracked_changes[]}`) and appends one entry per comment to
  `engagements/E/deliverables/review_log.md`. It does **not** mark the docx
  consumed — `apply` does that.

Each comment in the bundle carries `{id, author, date, comment, anchored_text}`.
The `anchored_text` is the body span the reviewer commented on — use it to locate
the node/step the comment is about.

### 2. Classify each comment

Assign a `comment_id` (the bundle's `id`) and one of the categories above
(`FACTUAL CORRECTION`, `CLARIFICATION`, `STRUCTURE / FORMATTING`, `EVIDENCE REQUEST`,
`CONTROL / COMPLIANCE`, `SCOPE QUESTION`, `SME VALIDATION REQUIRED`,
`CLIENT PREFERENCE`, `DUPLICATE / NO ACTION`). The category drives the command map.

### 3. Map each comment to a command

Map to the real `state_machine.py` subcommands only (`set-lens`, `add-item`,
`set-sop`, `set-improvement`):

| Comment intent | Category (typical) | Command |
|---|---|---|
| Diagnosis/lens change (e.g. "this is mostly manual, not mixed") | FACTUAL CORRECTION, SCOPE QUESTION | `set-lens --node L1.L2 --lens automation --value human` |
| New finding / corrected finding | FACTUAL CORRECTION, CONTROL / COMPLIANCE | `add-item --type improvement --l1 L1 --l2 L2 --field title=... --field description=...` |
| SOP scope/status change (e.g. mark a draft `revised`) | STRUCTURE / FORMATTING, SCOPE QUESTION | `set-sop --node L1.L2 --status revised` |
| Improvement deliverable status/scope change | SCOPE QUESTION | `set-improvement --node L1.L2 --status revised` |
| `SME VALIDATION REQUIRED` | SME VALIDATION REQUIRED | `add-item --type improvement ... --field requires_human_review=true` (routes + **blocks `final`** until closed) |
| Prose-only edit (wording, no state change) | CLARIFICATION, CLIENT PREFERENCE | Edit the node MD (`engagements/E/nodes/L1/L2.md`) directly; no state command |
| Duplicate / no action | DUPLICATE / NO ACTION | none — record in the log only |

### Review-override conflict: applied but audited (T33)

The reviewer is **authoritative** (human > machine), so a review `set-lens`
**always applies** — even when it contradicts an existing, evidence-backed lens
value. But an override of a non-null value is **not silent**: `apply` records it so
the disagreement is visible. For every `set-lens` action, `apply` checks the node's
current lens value *before* applying and then:

| Current lens value | New (reviewer) value | Behaviour |
|---|---|---|
| `null` | anything | Apply normally (first assertion — no conflict). |
| non-null, **equals** new | same | Apply (idempotent no-op-ish — no conflict). |
| non-null, **differs** from new | different | **Apply the reviewer's value** AND upsert a `GAP-CONFLICT` audit row. |

The audit row is a normal register row (added through `add-item`, never by hand):

- `type:gap`, `tag:unconfirmed`, `source:review`
- stable `dedup_key` = `conflict|{node}|{lens}|review` — so **re-applying the same
  override in a later round upserts the one row**, never a duplicate. (This key is
  deliberately distinct from the classify-side `GAP-CONFLICT-{l1}-{l2}-{lens}`, which
  is a *different* conflict — signals disagreeing across documents, lens left null.)
- `observation_pain_point` records the `{node, lens, prior_value, reviewer_value,
  reviewer, comment_id}` so the override is fully attributed.

The override is noted in `review_log.md` (an `OVERRIDE AUDITED` line under the
action). The conflict row surfaces in `state_machine.py status` as an open gap for a
human to confirm later; `apply` does **not** auto-resolve it — the human reviewer
already made the call, this row only audits that they overrode evidence. You do
**not** need to hand-build this row or pre-flag the action: emit the `set-lens`
action normally and `apply` handles the detection, the override, and the audit.

### 4. Emit the actions JSON

A JSON **list** of action objects. Each is `{command, args, reviewer, comment_id}`,
where `args` are the command's flags (dashes→underscores), and `--field` /
`--field-json` may be given as an object:

```json
[
  {
    "command": "set-sop",
    "args": {"node": "procure-to-pay.invoice-processing", "status": "revised"},
    "reviewer": "Jane Reviewer",
    "comment_id": "0"
  },
  {
    "command": "add-item",
    "args": {
      "type": "improvement",
      "l1": "procure-to-pay", "l2": "invoice-processing",
      "field": {"title": "AP manager approves invoices",
                "description": "Reviewer correction from round 1"}
    },
    "reviewer": "Jane Reviewer",
    "comment_id": "0"
  },
  {
    "command": "set-lens",
    "args": {"node": "procure-to-pay.invoice-processing",
             "lens": "automation", "value": "human"},
    "reviewer": "Jane Reviewer",
    "comment_id": "0"
  }
]
```

Only `set-lens`, `add-item`, `set-sop`, `set-improvement` are allowed in actions
JSON; any other command is rejected.

### 5. Apply

```
python3 scripts/review_ingest.py apply \
    --engagement E --docx PATH/reviewed.docx --actions review/actions.json --round N
```

For each action `apply` runs the command (attributed to `reviewer`), captures the
touched node's **before→after** and appends it to `review_log.md`, then **marks the
docx hash consumed** in `engagements/E/review/consumed.json`. If any action fails,
the docx is **not** marked consumed (fix the actions and re-run). A re-run on an
already-consumed docx is a no-op (no double-apply).

Lens/finding changes bump node state, leaving the node **diagnosis-dirty** — the
next `consult-run` re-consolidates and redraws it. That is how review folds back in
without a CSV round-trip; `review_log.md` is the canonical human-readable trail.

## Disposing of `unmapped` content (T34)

A `type:unmapped` row is content the pipeline captured but could **not** auto-place
on the taxonomy (the pipeline never auto-buckets). Every active `unmapped` row must
be **dispositioned** by a human before the engagement is done — an owner is not
enough; the row must carry a `disposition` other than `pending`. Set it through the
existing `add-item` upsert-by-id (no new state command exists — re-adding the same
`--id` updates the row in place):

| `disposition` | Meaning | Flow |
|---|---|---|
| `reclassified` | The content does belong on the taxonomy after all; a human supplies the target `{l1}.{l2}`. | See the two-step flow below. |
| `converted` | The content became a real register item (improvement/gap/screenshot); the unmapped row is now redundant. | `add-item --type unmapped --id UNM-NNNN --field disposition=converted --field note=...` (and add the real item separately). |
| `out_of_scope` | The content is genuinely outside this engagement's scope. | `add-item --type unmapped --id UNM-NNNN --field disposition=out_of_scope --field note=...` |

**Reclassify flow** (two commands — disposition + archive, then mark the target
dirty so it is re-diagnosed; the pipeline never auto-buckets, so the human names the
target):

```
# 1. set disposition=reclassified AND archive the now-redundant unmapped row
python3 scripts/state_machine.py add-item --engagement E \
    --type unmapped --id UNM-NNNN \
    --field disposition=reclassified \
    --field record_status=archived \
    --field note="reclassified to {l1}.{l2} by <human>"

# 2. mark the target node diagnosis-dirty so the next consult-run re-consolidates it
python3 scripts/state_machine.py mark-dirty --engagement E --node {l1}.{l2}
```

Archiving the row removes it from the active set (so it no longer fails the gate),
and `mark-dirty` makes the target node show up in `state_machine.py status`
(`diagnosis_dirty_nodes`) → the orchestrator re-consolidates it.

## Gate before `final`: `gates.py final-check` must pass

Before any deliverable on a node is set `final` (`set-sop`/`set-improvement
--status final`), the engagement must pass the read-only Definition-of-Done gates:

```
python3 scripts/gates.py final-check --engagement E [--json]
```

It exits **0 only when every gate passes** (nonzero otherwise), so wire it in front
of any `final` step and **do not bless `final` while it FAILs**. The gates:

- **unmapped_dispositioned** — every active `type:unmapped` row has
  `disposition != pending` (use the dispositions above).
- **no_open_human_review** — zero active rows with `requires_human_review` true
  (archived rows excluded). This is why an open `SME VALIDATION REQUIRED` /
  `requires_human_review=true` item **blocks `final`** until closed.
- **evidence_refs_resolve** — (best-effort) every node-evidence `source` ref
  resolves to a readable file under the engagement dir.
- **final_artifacts_have_path** — no node whose `sop.status` / `improvement.status`
  is `final` lacks a `path`.

`gates.py` is strictly read-only (it never writes `state.json` / `register.json`);
it only reports. Fix the failing items via the normal `state_machine.py` commands,
then re-run.
