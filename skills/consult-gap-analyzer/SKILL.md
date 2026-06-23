---
name: consult-gap-analyzer
description: >-
  Stage 4 substantive-gap sub-agent (the LLM sibling of the structural scan). For one
  CONSOLIDATED L2 node, reads the synthesis via `scripts/consolidate_inputs.py gather` and
  adds the gaps the mechanical scan can't see — internal contradictions, thin /
  single-source evidence, undocumented controls, conflicting lens signals, and especially
  any control- or procedure-critical claim resting on `evidence_tier:verbal` (the Evidence
  DoD: a verbal-only control is not "done"). Each gap is a `type:gap` register row added via
  `scripts/state_machine.py add-item` with a stable `dedup_key` (re-runs upsert, never
  duplicate), a tag from the controlled gap vocab, and the evidence ref in `source`. Runs
  AFTER consolidate and before drafting. Never invents evidence or flags; cites register IDs
  / evidence refs. Its ids come off the normal add-item path (`GAP-NNNN`) and never collide
  with the structural `GAP-STRUCT-*` namespace.
---

# Skill: Consult Gap Analyzer — Substantive Gaps on a Consolidated L2 Node

## Purpose

This is the **LLM layer of Stage 4** (`consolidate_contract.md` §7; spec §5 Stage 4).
`scripts/gap_report.py scan` already finds the *structural* gaps mechanically
(empty nodes, missing lenses, no evidence, SOP not started) and writes them as
`GAP-STRUCT-{l1}-{l2}-{kind}` rows. This skill is its **LLM sibling**: for one
**consolidated** L2 node it reads the synthesis and adds the **substantive** gaps
a mechanical scan cannot see:

- **Internal contradictions** — the node's evidence / findings disagree with each
  other (e.g. two docs assert incompatible owners, timings, or control designs).
- **Thin / single-source evidence** — a material claim or procedural step rests on
  one uncorroborated source.
- **Undocumented controls** — a control is referenced but never described /
  evidenced.
- **Verbal-only control or procedure-critical claims** — the Evidence DoD case
  below; this is the headline rule.
- **Conflicting lens signals** — the diagnosis lenses imply two different stories
  the consolidator left unreconciled.

Each becomes a `type:gap` register row on the **same confirm / add-item path** as
every other finding, with a stable `dedup_key`, a gap-vocab `tag`, and the
evidence ref in `source`.

## When to Use

Use **after consolidate** has run on the node — it needs the synthesis (the node
MD, the confirmed register rows, the resolved evidence). It runs **before
drafting**. Drive it per consolidated L2 node (or batch per L1 if cross-L2 context
matters, per `consolidate_contract.md` §8).

**Do NOT use it for:** the structural scan (`scripts/gap_report.py scan`, already
built — do not re-emit its findings); the consolidation itself
(`consult-consolidator`, T13, which confirms candidate_findings and authors the
MD); the merge-time contradiction gap (`GAP-CONFLICT-*`, written by
`classify_merge.py`); the disposition / final gate.

## Inputs — use the gatherer (read-only, do not forage)

Get your complete, deterministic input bundle from the **same** read-only helper
the consolidator uses:

```bash
python3 scripts/consolidate_inputs.py gather \
  --engagement {E} --node {KEY} --json --excerpts
```

The bundle gives you everything you need to spot substantive gaps:

- `node` — `coverage`, the 5 `lenses`, the `evidence` list with each entry's
  **`tier`** (`verbal` / `documentary` / `system_observed`), `source`, `loc`,
  `note`, plus the `node_md` path and the `last_evidence_at` / `consolidated_at`
  markers (so you can confirm the node really is consolidated).
- `register_rows` — the **existing active rows already on this node** (improvements
  and any existing gaps, **including `GAP-STRUCT-*`**). Read these so you do **not
  duplicate** a gap the structural scan or a prior run already recorded, and so you
  can cite their IDs.
- `candidate_findings` — the staged findings, each with its `evidence_tier` and
  `evidence_ref`.
- `evidence_excerpts` (with `--excerpts`) — the cited MD lines resolved from the
  immutable ingested docs, so you can read what a claim actually rests on and
  judge its tier / corroboration **without re-reading files or inventing text**.

You never read or write `state.json` / `register.json` directly. The bundle is
your only input; `add-item` is your only write.

## The Evidence DoD rule (the headline — read this carefully)

From spec §3 / §"Definition of Done":

> **Evidence DoD** = every control claim and procedure-critical step is ≥
> `documentary` tier or carries an open validation gap. A control attested only
> verbally must not look identical to one backed by a policy/system — a
> verbal-only control is **not "done."**

So: **whenever the node asserts a control or a procedure-critical step whose
backing evidence is `evidence_tier:verbal` (and no `documentary` /
`system_observed` source corroborates it), you MUST emit a substantive gap.**
Read the tier straight off the bundle's `node.evidence[*].tier` /
`candidate_findings[*].evidence_tier` — **do not invent or upgrade a tier**. If
the bundle says `verbal` and the claim is control- or procedure-critical, the gap
is mandatory. Tag it `control_not_evidenced` (or `approval_not_evidenced` for an
approval step) and cite the verbal evidence ref in `source`.

This is the one gap the mechanical scan structurally cannot produce: `gap_report.py`
sees coverage / lenses / evidence-presence, not evidence **tier vs. claim
criticality**. That judgment is this skill's job.

## How to find the substantive gaps

For the one node, working only from the bundle:

1. **Verbal control / procedure-critical claims** (mandatory, above). For each
   control claim or procedure-critical step, check the tier of its backing
   evidence. If it is only `verbal` and nothing `documentary`/`system_observed`
   corroborates it → emit a gap (`control_not_evidenced` / `approval_not_evidenced`).
2. **Internal contradictions.** Two evidence refs / findings on this node that
   assert incompatible facts (owner, timing, frequency, control design). Emit one
   gap (`unconfirmed`) naming **both** conflicting refs in `source`. (If the
   conflict is a *lens* disagreement already written as `GAP-CONFLICT-*` by the
   merge, do not duplicate it — cite that row instead.)
3. **Thin / single-source evidence.** A material claim or procedural step backed by
   exactly one uncorroborated source where corroboration should exist. Emit a gap
   (`unconfirmed`), citing the lone ref.
4. **Undocumented controls.** A control referenced in the narrative / evidence but
   never described or evidenced. Emit a gap (`control_not_evidenced`).
5. **Conflicting lens signals.** The 5-lens diagnosis tells two stories (e.g.
   `automation:machine` while the evidence describes a manual workaround). Emit a
   gap (`unconfirmed`) citing the evidence that conflicts with the asserted lens.

For each, **before emitting**, scan `register_rows`: if an existing row (a
`GAP-STRUCT-*` structural row, a `GAP-CONFLICT-*` merge row, or a prior
`GAP-NNNN`) already captures it, **do not duplicate** — the structural row stands.
You add only what the mechanical scan and the merge could not see.

## Emitting a gap — the add-item path (one row per gap)

Substantive gaps go in via **the normal `add-item` path**, exactly like confirmed
findings (`consolidate_contract.md` §4). Per gap:

```bash
python3 scripts/state_machine.py add-item --engagement {E} \
  --type gap --l1 {l1} --l2 {l2} \
  --field dedup_key='{node}|gap|{normalized-observation}' \
  --field tag={gap-vocab-tag} \
  --field source='{evidence_ref}' \
  --field evidence_tier={verbal|documentary|system_observed} \
  --field observation_pain_point='{what is missing / contradictory, and why}' \
  --field requires_human_review=true
```

Concrete worked example — a verbal-only PO-release approval control (the Evidence
DoD case):

```bash
python3 scripts/state_machine.py add-item --engagement {E} \
  --type gap --l1 procure-to-pay --l2 sourcing \
  --field dedup_key='procure-to-pay.sourcing|gap|verbal-only approval control on po release' \
  --field tag=control_not_evidenced \
  --field source='ingested/kickoff.md#L42-58' \
  --field evidence_tier=verbal \
  --field observation_pain_point='PO release approval control attested only verbally (no policy/system evidence); control claim is verbal-tier per Evidence DoD.' \
  --field requires_human_review=true
```

Field rules:

- **`--type gap`** — always. (`--l1` / `--l2` are required for `--type gap`.)
- **`dedup_key`** — a **stable** key, shape `{node}|gap|{normalized-observation}`
  (mirrors `consolidate_inputs.proposed_dedup_key`: `{node}|{type}|{tail}`). Keep
  it deterministic so a **re-run upserts the same row** instead of minting a fresh
  `GAP-NNNN`. `add-item` matches on `dedup_key` first, id second, so a second pass
  on the same node updates the existing row in place — **without a stable
  `dedup_key`, a re-run duplicates every gap.**
- **`tag`** — a value from the **controlled gap vocab** (see
  `skills/consult-improvement-log/SKILL.md`): `not_documented`, `unconfirmed`,
  `confirm`, `owner_unknown`, `reviewer_unknown`, `approver_unknown`,
  `system_unknown`, `timing_unknown`, `frequency_unknown`, `input_unknown`,
  `output_unknown`, `navigation_unknown`, `field_unknown`,
  **`control_not_evidenced`**, **`approval_not_evidenced`**,
  `evidence_retention_unknown`, `archive_location_unknown`,
  `exception_handling_unknown`, `downstream_dependency_unknown`,
  `upstream_dependency_unknown`. Verbal-only / undocumented controls →
  `control_not_evidenced` (approvals → `approval_not_evidenced`); contradictions,
  thin evidence, conflicting lenses → `unconfirmed`.
- **`source`** — the **evidence ref** (`path#Lstart-Lend`) the gap rests on, taken
  straight from the bundle. For a contradiction, cite **both** conflicting refs.
  Never invent a ref; never cite a file you did not see in the bundle.
- **`evidence_tier`** — carry the tier **through from the bundle**; do not
  fabricate or upgrade it. The verbal tier is the whole point of the DoD gap.
- **`observation_pain_point`** — what is missing / contradictory and why it
  matters. Cite the conflicting register IDs / evidence refs; **do not restate
  structured data**.
- **`requires_human_review=true`** — a substantive gap is a judgment that wants a
  reviewer's eyes; flag it.

**Do not pass `--id`** for a substantive gap. Let `add-item` auto-assign the next
`GAP-NNNN` (`state_machine.TYPE_TO_PREFIX`). That is exactly why these **never
collide with `GAP-STRUCT-*`**: structural ids are minted by `gap_report.py` in the
`GAP-STRUCT-` namespace; substantive ids come off the auto-`GAP-NNNN` sequence.
Re-identification on re-runs is by `dedup_key`, not by a hand-set id, so you never
need to reach into the structural namespace.

## Re-runs upsert, never duplicate

Because every gap carries a stable `dedup_key`, running this skill again on the
node (e.g. after a 2nd evidence wave re-consolidates it) **upserts** each gap onto
its existing `GAP-NNNN` row rather than minting a duplicate. This is the
LLM-finding analogue of the structural scan's stable `GAP-STRUCT-*` ids and of the
consolidator's confirmed-finding `dedup_key`. A gap that is no longer warranted is
left to the human-review / disposition path — this skill adds and upserts; it does
not archive.

## Non-negotiables

1. **Runs after consolidate.** It needs the synthesis; confirm the node is
   consolidated (bundle's `consolidated_at`) before analyzing.
2. **Evidence DoD is mandatory.** Any control- or procedure-critical claim resting
   on `evidence_tier:verbal` (uncorroborated) **must** produce a gap.
3. **Never invent evidence, refs, tiers, or flags.** Cite register IDs / evidence
   refs from the bundle only; every command and `--field` shown here exists in
   `state_machine.py add-item` — invent none.
4. **Stable `dedup_key`** on every gap (`{node}|gap|{normalized-observation}`), so
   re-runs upsert one row, never duplicate.
5. **`tag` from the controlled gap vocab**, evidence ref in `source`,
   `evidence_tier` carried through from the bundle.
6. **Do not collide with `GAP-STRUCT-*`.** Use the auto-assigned `GAP-NNNN` id
   (no `--id`); do not re-emit structural gaps already in `register_rows`.
7. **Only writes via `add-item`.** Never touches `state.json` / `register.json`
   directly.
