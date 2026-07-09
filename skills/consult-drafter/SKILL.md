---
name: consult-drafter
description: "Fills ONE current-state desktop procedure (the A–H skeleton) from tagged sources and the reference registry."
---

# Consult Drafter

You fill **one** procedure — a single `10_<slug>.md` fragment — and nothing else.
You are its **durable owner**: first draft and every update. You do not author the
document, the front matter, the appendices, or any other procedure. Those are
static (human-owned) or derived (generated) files.

**Load `reference/Template.md` and `reference/procedure_skeleton.md` after this
skill.** The skeleton is the exact A–H shape you fill; the template shows how your
fragment sits in the assembled document. This SKILL is the how-to; the agent
definition `.claude/agents/consult-drafter.md` is the contract — where they touch,
the agent definition wins.

## What you own

A finalized `10_<slug>.md`: the A–H procedure for one L3 activity, current-state,
practical for a preparer to execute and a reviewer to validate. You receive a
fresh A–H skeleton on the first pass, or your own prior draft on an update pass.
Do not change the A–H headings.

Read at the start: your `{file}`; the `_sources/` tagged to this procedure; and
`_reference/systems.yaml`, `roles.yaml`, `sources.yaml`, `glossary.yaml` (if
present) — the canonical nouns and SRC- ids.

## The procedure heading — plain title only

Your `##` heading is the **plain procedure title**. Never type a `1.1` number
into it — the display number is derived and rendered late by the docx builder.
The L2 bucket is not in the fragment either; it lives only in the manifest.

On your **first write**, remove the `<!-- unfilled -->` sentinel — that is the
signal you are no longer a skeleton.

## Evidence discipline — never fabricate

You may add connective tissue: sequence steps, normalize role names to canonical
registry names, convert notes to neutral procedural language.

You may **not** invent: systems, navigation paths, field/parameter names,
thresholds, approvers, control evidence, timing/frequency, archive locations,
report names, downstream recipients, exception handling, or screenshot
availability. Anything unknown/unclear/unsupported → `TBD — confirm with process
owner` plus a `VALIDATION REQUIRED` callout at the point it matters. When sources
**conflict**, do not choose silently — raise a GAP stating the conflict.

## The A–H sections

- **A. Process Overview** — what it accomplishes, when, who, what it excludes, and
  its upstream/downstream connections. (The dependencies agent reads this.)
- **B. Quick Reference** — Trigger, Frequency, Preparer, Reviewer, primary
  systems/tools, key outputs.
- **C. Pre-Requisites** — bullets: what must be true before it begins.
- **D. Inputs** — bullets: source/owner where supported.
- **E. Step-by-Step Procedure** — `####` steps in neutral current-state language.
- **F. Key Controls** — CONTROL callouts (no table).
- **G. Outputs** — bullets: outputs, downstream recipients, evidence retained,
  where supported.
- **H. Known Issues & Improvement Opportunities** — PAIN POINT + IMPROVEMENT
  callouts. **This section IS the structured source for Appendix A** ("Pain
  Points & Improvement Opportunities") — it is assembled mechanically from these
  callouts, so fill every field. It is not free narrative to be ignored.

### Inline step tags (E) — by judgment

Within a step, add these **bolded tags** only where the detail helps execution,
review, or auditability — not mechanically on every step:

```
- **System / Tool:** ...
- **Navigation Path:** ...
- **Fields / Parameters:** ...
- **Expected Result:** ...
- **Evidence Required:** ...
```

## Callouts — each in its home section

Callouts are **not** a separate block; each type lives in its semantic section.
The label line grammar is exact (delimiter may be `-`/`–`/`—`). IDs are
**procedure-local**: start each series at 001/01 — other procedures reuse the same
numbers, which is correct. Never renumber an existing ID on update; a removed item
leaves its number retired.

**In `F. Key Controls`** — CONTROL:
```
> **CONTROL — CTRL-001:** <what is checked / reconciled / approved>
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** <e.g. each run / monthly>   (TBD + raise GAP if unknown)
> - **Owner:** <role>                           (TBD + raise GAP if unknown)
```

**In `H`** — PAIN POINT + IMPROVEMENT OPPORTUNITY:
```
> **PAIN POINT — PP-001:** <observed current-state friction, source-grounded>
> - **Impact:** <consequence from the source>   (TBD if the source is silent)
> - **Severity:** High | Medium | Low            (your local read; enum only)

> **IMPROVEMENT OPPORTUNITY — IO-001:** <the proposed improvement — this IS the recommendation>
> - **Addresses:** <PP-id(s) it mitigates, if any>
```
Severity is a **per-item** read for this one procedure — never a cross-procedure
ranking (you only see this procedure).

**Inline in `E`** — at the step they attach to:
```
> **VALIDATION REQUIRED — GAP-01:** <the fact/decision to confirm>
> - **Nature:** unknown | conflict | unsupported-assumption
> - **Owner to confirm:** <role or TBD>

> **SCREENSHOT PLACEHOLDER — SC-01:** <what to capture and what it must validate>
```
A body gap reference in a step's prose is `[[GAP-01 — SHORT LABEL]]` (never a bare
`[[GAP — …]]`) and must match a VALIDATION REQUIRED callout in that step.

## Nouns — canonical prose + consult-meta slugs

- In prose, name systems/roles by their **canonical registry name** (resolve "the
  AP lady" → `AP Clerk`, "our system" → `SAP S/4HANA`).
- Populate the **`consult-meta` end-matter block** with the registry **slugs** you
  used — this is the machine binding, not the prose:
  ```consult-meta
  systems: [sap, blackline]
  roles:   [ap-clerk, controller]
  ```
- A system/role with **no registry entry**: use the clearest label in prose, add a
  best-guess slug to `consult-meta`, and **report it**. Never invent a registry
  entry (an unregistered slug is a WARNING resolved by the human top-up loop).

## Cross-references and sources

- Refer to another procedure with the `[[slug]]` token — never a number or copied
  title. Systems/roles are **plain canonical text**, not tokens.
- Cite the `SRC-` id(s) you drew from; never invent SRC ids (use `sources.yaml`).

## Updates — leave no iteration artifacts

On an `update` pass, revise your prior draft so it reads as a single finished
product with no breadcrumbs:

- When a source **answers a prior GAP**, work the fact into the body and **delete
  the GAP entirely** — no "resolved"/"answered" markers.
- When a source **contradicts** existing text, update it (or raise a fresh GAP if
  unresolved); don't stack old and new.
- Remove any `TBD` the source now fills.
- Never renumber existing IDs.

## Before you finish

Run `python3 scripts/reconcile.py {file}` if available and fix any **ERRORS** in
your own file (dangling ID, bare gap tag, prefix/label mismatch). An unregistered
`consult-meta` slug is a **WARNING, not an ERROR** — leave your best-guess slug and
report it. ORPHAN warnings on unpopulated skeleton rows are fine.

## Style

Professional consulting language; current-state wording; functional roles; active
voice; concise steps; neutral descriptions. Avoid unsupported assumptions, blame
language, excessive caveats, named individuals in steps, and overuse of tables in
procedure bodies.

## What you return (COMPACT — no draft text)

- `slug`, `mode` (first-draft | update), `file` written
- counts: steps, controls (CTRL), open gaps (GAP), screenshots (SC), pain points
  (PP), improvements (IO)
- `consult_meta`: the systems/roles slugs you wrote
- `unregistered`: any system/role you used with no registry entry
- `conflicts`: source conflicts logged as GAPs (id + one line each)
- on update: `gaps_closed`, `tbds_filled`, `revised` (one line)
- `reconcile`: pass / the ERRORS you couldn't resolve

Do not return the procedure prose. The file is the deliverable.
