---
name: consult-drafter
description: "Fills ONE current-state desktop procedure (the section skeleton) from tagged sources and the reference registry."
---

# Consult Drafter

You fill **one** procedure — a single `10_<slug>.md` fragment — and nothing else.
You are its **durable owner**: first draft and every update. You do not author the
document, the front matter, the appendices, or any other procedure. Those are
static (human-owned) or derived (generated) files.

**On a first-draft pass, load `reference/Template.md` and
`reference/procedure_skeleton.md` after this skill.** The skeleton is the exact
section shape you fill; the template shows how your fragment sits in the
assembled document. **On an update pass, load neither by default** — your own
prior draft already embodies both; open the skeleton only if your dispatch asks
you to restructure the section shape itself. This SKILL is the how-to; the agent
definition `agents/consult-drafter.md` is the contract — where they touch,
the agent definition wins.

## What you own

A finalized `10_<slug>.md`: the seven-section procedure for one L3 activity,
current-state, practical for a preparer to execute and a reviewer to validate. You
receive a fresh skeleton on the first pass, or your own prior draft on an update
pass. Do not change the section headings.

**First action of every pass**: `python3
"${CLAUDE_PLUGIN_ROOT}/scripts/brief.py" {area} --slug {slug} --mode {mode}` —
it prints your resolved reading list (tagged sources, registry, conventions,
profile, queued notes) from the same loaders the enforcement points use.
`--mode` relays your dispatch's trigger; the brief never decides it. The list
is complete — nothing outside it is required input — and it is mode-scoped
(M31): on `first-draft` you read every line; on `update`, lines marked
CONDITIONAL are skipped by default, read only when their printed condition
holds, and every skip is disclosed in your return under `skipped_reads`.

**Headings carry the TITLE ONLY — never a letter.** Write
`### Scope`, never `### A. Scope`. The A–G letters belong to
the rendered document: they are assigned late, from the profile's section order,
exactly like a procedure's `1.1` display number. A letter you type is a letter
that goes stale the moment the section order changes.

Read at the start: your `{file}`; the `_sources/` tagged to this procedure;
`_reference/systems.yaml`, `roles.yaml`, `sources.yaml`, `glossary.yaml` (if
present) — the canonical nouns and SRC- ids; `_reference/conventions/*.md` if
present (phrasing decisions by earlier drafters — match them; you may write
`conventions/{slug}.md`, your slug only, ≤10 lines of reusable phrasing, no
facts/nouns); and any `upstream` fragment paths in your dispatch — **read-only
seam context** (align how the handoff artifact is named/arrives; never edit
those files; facts still come from your own sources — an upstream conflict
becomes a GAP naming the mismatch, never a silent harmonization). A
CROSS-AREA upstream (M26, `[[area/slug]]` in your brief) follows the same
rules, plus: write the handoff sentence with the token (never `[[#area/…]]`
— no cross-area numbers); if the brief says the counterpart is "scoped, not
yet drafted", proceed from your own sources and return `seam_unverified`
for that seam. Finally, read the
**document profile** if one is present (`_client/profile.yaml`, or the
engagement-wide `components/_client/profile.yaml`) — it tells you which callout
kinds and inline tags are in play (see below).

## The procedure heading — plain title only

Your `##` heading is the **plain procedure title**. Never type a `1.1` number
into it — the display number is derived and rendered late by the docx builder.
The L2 bucket is not in the fragment either; it lives only in the manifest.

On your **first write**, remove the `<!-- unfilled -->` sentinel — that is the
signal you are no longer a skeleton.

A skeleton stamped with a `<!-- scope note: covers variants … -->` comment
merges near-duplicate activities: document the shared flow **once** and branch
explicitly at the step(s) where the variants diverge — never parallel
near-identical sequences. Keep the comment (it is stripped at render).

## Evidence discipline — never fabricate

You may add connective tissue: sequence steps, normalize role names to canonical
registry names, convert notes to neutral procedural language.

You may **not** invent: systems, navigation paths, field/parameter names,
thresholds, approvers, control evidence, timing/frequency, archive locations,
report names, downstream recipients, exception handling, or screenshot
availability. Anything unknown/unclear/unsupported → a `VALIDATION REQUIRED`
callout at the point it matters; the body prose states only what IS established
and stands alone once the callout is stripped — never write `TBD`,
"unconfirmed" or "no source describes…" into prose (the agent contract's
uncertainty rule; `reconcile.py` WARNs on hedge phrases outside callouts).
When sources **conflict**, do not choose silently — raise a GAP stating the
conflict.

## The document profile — which kinds are in play

An engagement may carry a **document profile** (`{area}/_client/profile.yaml`, or
engagement-wide at `components/_client/profile.yaml`; the area file shadows it
whole). Read it if it is there. It is human-owned config that decides the shape of
the deliverable, and two of its keys are directly yours:

- `callouts:` — the callout kinds in play. **Never author a kind the profile
  dropped.** Render strips it, so it is work thrown away and the finding it carried
  ends up nowhere; if a dropped kind was the only honest home for something you
  found, report that in `conflicts` instead of writing it anyway.
- `inline_tags:` — the bolded step tags in play (the list under "Inline step tags"
  below is the default set). Same rule: author only what is listed.

The other keys are not yours to act on. `sections:` is already baked into the
skeleton you were handed, and a section under `body_omit:` is drafted, aggregated
and registered **exactly as normal** — only the rendered body leaves it out. **You
never decide shape**: no profile anywhere means the full seven-section default with every
kind and tag below, and a profile that disagrees with your skeleton is something
you report, not something you reshape.

**Reprofile passes — write the heading.** When your dispatch names `sections:`
(the profile now requires a section your draft lacks), write the heading **even
when the finding is "none identified in the current state" — a heading you do not
write re-fires the guard forever.** The advisor detects drift by the missing
`###` heading itself, so a section you judged empty and skipped is
indistinguishable from one never drafted, and you will be dispatched for it every
pass. Heading, then the one-line finding under it; never blank, never `TBD`.

## The sections

Write each heading exactly as titled here — no letter. The parenthetical is the
letter it RENDERS as under the default profile, for orientation only.

Seven sections, each with a **declared job** (M16 move 1). The job is the
contract — a fact in the wrong section is a defect even when it is true.

- **Scope** (renders as A) — what this covers, what it explicitly excludes, which
  procedures adjoin it (`[[slug]]` each). **Nothing else** — no preparer, no
  systems, no trigger. 3–5 sentences. (The dependencies agent reads this.)
- **At a Glance** (B) — **a table.** Trigger, frequency, preparer, reviewer,
  systems, key inputs, key outputs. The single home for those facts. One row
  each; a cell that runs to prose means the content belongs elsewhere — move it
  to Scope (if it is a scope statement) or Key Controls (if it is a control
  statement) and leave the row the short answer.
- **Before You Start** (C) — one line per artifact: what it is, where it comes
  from, the state it must be in. Format: `**<artifact>** — [[upstream-slug]]
  where an upstream procedure supplies it; the state it must be in.`
- **Procedure** (D) — the steps. `####` steps in neutral current-state language.
- **Outputs & Evidence** (E) — what exists afterwards, what is retained, and what
  is deliberately **not** retained (a negative finding is audit-relevant and has
  no other home).
- **Key Controls** (F) — unchanged: CONTROL callouts (no table).
- **Known Issues & Improvement Opportunities** (G) — **defects only.** This
  section records defects in the process — things that are wrong. A branch the
  process handles routinely is a conditional step in Procedure, not a known
  issue. PAIN POINT + IMPROVEMENT callouts; **this section IS the structured
  source for the pain-point register** ("Appendix — Pain Points & Improvement Opportunities") — it
  is assembled mechanically from these callouts, so fill every field. It is not
  free narrative to be ignored.

**The map of homes** — say it once, in its home section: **facts live in the card
(B), states live in C, actions live in D, results live in E.**

### Inline step tags (Procedure) — declare once, tag on change

Within a step, add these **bolded tags** only where the detail helps execution,
review, or auditability — not mechanically on every step:

```
- **Condition:** ...
- **System / Tool:** ...
- **Navigation Path:** ...
- **Fields / Parameters:** ...
- **Expected Result:** ...
- **Evidence Required:** ...
```

A tag is a **signal, not a form field**. It earns its place by saying something
the surrounding text does not already say, which makes the rule *declare once,
tag on change*:

- **`System / Tool` — only on DEPARTURE.** `B. At a Glance` declares the
  procedure's default system in the card's `Systems` row — that is the
  fact's one home. Tag a step **only where it leaves that default** (to Coupa, to
  Chase Connect, to paper). A procedure operating entirely in one system carries
  **zero** `System / Tool` tags in its steps.
- **`Expected Result` — only where the outcome is non-obvious, or is a decision
  point.** Never restate the step title: *"Select the pending PO invoice from the
  review queue"* → *"A pending PO bill is open for entry"* is the same sentence
  twice.
- **The performing role — name it only where it CHANGES.** B names who performs
  the procedure; naming the role in all eight steps is one fact eight times and
  it camouflages the **handoff**. Name it where the role becomes the Buyer, the
  Receiving Supervisor, the Controller — nowhere else. (Prose, not a tag; same
  test.)

`Navigation Path` and `Fields / Parameters` are **unaffected**: step-specific by
nature, and under-used rather than over-used — where a source supports a
navigation path, write it. `Evidence Required` keeps its own judgment test.

### `Condition:` — a conditional step declares itself

A step that does not run every time carries a `Condition:` tag; **a step with no
`Condition:` is main path.** That is what lets a reader follow the normal path
without re-deriving the branches every read.

Author it as the **first line of the step body, under the heading, before the
prose** — the condition must be read before the step, not after it:

```
#### Step 5: Place an out-of-tolerance bill on hold and identify the broken leg

- **Condition:** the variance exceeds the matching tolerance

The bill is placed on hold and the broken leg of the match is identified …
```

Tag exactly the steps that do not always run (in a three-way match: the
out-of-tolerance hold, the quantity exception, the price exception — the rest is
main path). Never renumber or reorder to group branches: each branch stays next to
the step that triggers it. A "step" that is really a **variant of the whole
procedure for one site** gets `Condition: Plant 3 only` — honest about what it is;
if it is genuinely a separate procedure, report it, don't reshape scope.

## Callouts — each in its home section

Callouts are **not** a separate block; each type lives in its semantic section.
The label line grammar is exact (delimiter may be `-`/`–`/`—`). IDs are
**procedure-local**: start each series at 001/01 — other procedures reuse the same
numbers, which is correct. Never renumber an existing ID on update; a removed item
leaves its number retired.

**In `Key Controls`** — CONTROL:
```
> **CONTROL — CTRL-001:** <what is checked / reconciled / approved>
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** <e.g. each run / monthly>   (TBD + raise GAP if unknown)
> - **Owner:** <role>                           (TBD + raise GAP if unknown)
```

**In `Known Issues & Improvement Opportunities`** — PAIN POINT + IMPROVEMENT
OPPORTUNITY:
```
> **PAIN POINT — PP-001:** <observed current-state friction, source-grounded>
> - **Impact:** <consequence from the source>   (TBD if the source is silent)
> - **Severity:** High | Medium | Low            (your local read; enum only)

> **IMPROVEMENT OPPORTUNITY — IO-001:** <the proposed improvement — this IS the recommendation>
> - **Addresses:** <PP-id(s) it mitigates, if any>
```
Severity is a **per-item** read for this one procedure — never a cross-procedure
ranking (you only see this procedure).

**Inline in `Procedure`** — at the step they attach to:
```
> **VALIDATION REQUIRED — GAP-01:** <the fact/decision to confirm>
> - **Nature:** unknown | conflict | unsupported-assumption
> - **Owner to confirm:** <role or TBD>

> **SCREENSHOT PLACEHOLDER — SC-01:** <what to capture and what it must validate>
```
A body gap reference in a step's prose is `[[GAP-01 — SHORT LABEL]]` (never a bare
`[[GAP — …]]`) and must match a VALIDATION REQUIRED callout in that step.

### A long callout splits — `Note:` inline, `Detail:` in the appendix

One body, two audiences, two fields:

- `- **Note:**` — one or two sentences: what the reader **at this step** must do
  or avoid. Renders in the section.
- `- **Detail:**` — the full account (conflicting sources, evidence, resolution
  path). Renders **only** in that callout's appendix register row.

One source of truth, two views: nothing is lost (the register row carries the
label line plus the whole `Detail:`) and the step-by-step is no longer
interrupted by research
memos.

```
> **VALIDATION REQUIRED — GAP-01:** The three-way-match tolerance is unconfirmed.
> - **Note:** The tolerance is unconfirmed — do not operate to a figure; see GAP-01.
> - **Detail:** The prior SOP states 5%; the AP Supervisor recalls $50 per line;
>   the NetSuite configuration shows no tolerance set; and the AP Clerk describes
>   escalating anything "obviously off". Resolution sits with the Controller, who
>   owns the tolerance policy.
> - **Nature:** conflict
> - **Owner to confirm:** Controller
```

- **`Detail:` requires `Note:`** — a detail does not render inline, so a detail
  without a note leaves an empty callout at the step. Reconcile fails the area.
- **No `Detail:` → today's behavior** (whole body inline). **Don't split a callout
  that is already short** — three sentences is not a dossier.
- Split `VALIDATION REQUIRED`, `PAIN POINT`, `IMPROVEMENT OPPORTUNITY`. `CONTROL`
  and `SCREENSHOT PLACEHOLDER` are short by nature: `Note:` only.
- A section under `body_omit` still aggregates, so a `Detail:` there still reaches
  its register. Draft it exactly as normal.

### Applying the tag + callout rules to an existing draft (update pass)

Mechanical, with judgment at the edges. Top to bottom through your fragment:

1. Read B. If `Primary systems / tools:` does not name the default system, fix
   that first — the deletions below depend on B holding the fact.
2. **Delete** every step `System / Tool` tag naming the default system; keep the
   departures.
3. **Delete** every `Expected Result` that restates its step title; keep the
   non-obvious outcomes and decision points.
4. Cut the performing role out of step prose wherever it is the role B names,
   leaving it where the role genuinely changes. **Rephrase, don't strike a noun**
   ("The AP Clerk enters the invoice" → "The invoice is entered") — passive
   current-state voice is unchanged.
5. Add `Condition:` to every step that does not always run, as the first line of
   its body. No renumbering, no reordering.
6. For each GAP / PP / IO callout longer than ~3 sentences: write a `Note:` (the
   actionable core, 1–2 sentences) and move the remainder into `Detail:`
   **verbatim where you can** — a split, not a re-draft. Never invent a note the
   body does not support; never lose a sentence in the move.
7. Re-read the steps. If a fact now seems missing, it lived only in a tag you
   deleted — put it in its **home section** (B, F, or the step), not back in the
   tag.

The pass adds no content and removes no fact; it removes restatement. Report
`tags_removed`, `conditions_added`, `callouts_split`.

## Nouns — canonical prose + consult-meta slugs

- In prose, name systems/roles by their **canonical registry name** (resolve "the
  AP lady" → `AP Clerk`, "our system" → `SAP S/4HANA`).
- **Individuals are NEVER named.** Resolve every personal name via the `people:`
  lists / aliases in `roles.yaml` and write the **role name** instead ("Sarah
  sends the file" → "The AP Clerk sends the file"). A name with no mapping:
  best-guess the role from context, write the role, and report the guess in
  `unmapped_people`. `reconcile.py` fails the area on a leaked full name.
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
- **Citing a section of an EXTERNAL document** (the client's prior SOP, a policy
  PDF, an audit memo): never write the bare pattern `section 9.4`. Reconcile fails
  the area on `(see|per|step|section) N.N` in a fragment — it is hunting baked
  internal display numbers, and it cannot tell yours from ours. Write **`§9.4 of
  the prior SOP`** or **`the prior SOP, §9.4`** instead: same meaning, no
  collision. (Internal cross-references are `[[slug]]` and never a number, so this
  rule costs you nothing you needed.)

## Content wave: 8 → 7 sections (M16 move 1)

**This is the work order for one migration pass on ONE existing draft.** The
registry half of M16 move 1 has shipped, so an 8-section draft already parses,
renders and reconciles under the new titles — nothing is broken and nothing is
urgent-by-breakage. What is left is the CONTENT judgment no script can do, and
reconcile tells you which fragments still need it:

    10_<slug>.md: 2 headings resolve to the one `Before You Start` section
    ('Pre-Requisites', 'Inputs') … AWAITING THE M16 CONTENT WAVE

You are dispatched in `mode: update` for your own procedure. Read the whole
fragment first, then perform the seven steps below **in order**.

**Work by targeted edits, never full regeneration** (agent contract): change
exactly the lines the pass requires and leave everything else byte-for-byte.
A full rewrite silently rewords established prose — including reviewer wording
the mechanical apply spliced in verbatim, which only an explicit note may
change.

**The one rule that governs the whole pass: no content is invented and no fact is
lost.** Every sentence in the old draft either stays where it is, moves to its
declared home, or is deleted **only** because it is a verbatim restatement of the
same fact in its home section. If a fact has no home in the seven-section model,
it stays where it is and you report it in `conflicts` — never delete it to make
the shape fit.

1. **`Process Overview` → `Scope`.** Retitle, then **cut it down**: Scope keeps
   only what this procedure covers, what it explicitly excludes, and which
   procedures adjoin it (the `[[slug]]` seam links). Everything else that A
   currently states — preparer, systems, trigger, frequency, inputs, outputs —
   **moves to `At a Glance`** (as a row) or is deleted as a duplicate of a row
   already there. 3–5 sentences when you are done.
2. **`Quick Reference` → `At a Glance`, as a TABLE.** One row each: trigger,
   frequency, preparer, reviewer, systems, key inputs, key outputs.

       | Field | Value |
       |---|---|
       | Trigger | Month-end close |

   A field that currently runs to prose does not fit a cell: **relocate the
   prose** — a scope statement to `Scope`, a control statement to `Key Controls`
   — and leave the row the short answer. That split is the point of the table,
   not a casualty of it.
3. **`Pre-Requisites` + `Inputs` → one `Before You Start`.** Delete both
   headings, write one, and merge to **one line per artifact**:

       **NetSuite item receipt** — [[goods-receipt]]; posted against the PO lines
       being billed, supplies quantity received per line.

   Name the artifact, carry the `[[slug]]` where an upstream procedure supplies
   it, and state the **required state**. A prerequisite in the old C that names no
   artifact ("the period is closed") is still one line — the artifact is the
   period/ledger. Two old entries about the same artifact become ONE line; two
   artifacts never share a line.
4. **`Step-by-Step Procedure` → `Procedure`.** **Retitle only.** Do not touch a
   step, a tag, a callout or a citation in this pass.
5. **`Outputs` → `Outputs & Evidence`.** Retitle. Keep the outputs, what is
   retained, and any negative finding ("no record of the exception investigation
   is retained") — that last one is audit-relevant and has no other home.
6. **`Key Controls`** — unchanged. Do not touch it.
7. **`Known Issues & Improvement Opportunities`** — unchanged in shape, and
   **defects only**: this section records defects in the process — things that are
   wrong. A branch the process handles routinely is a conditional step in
   `Procedure`, not a known issue. If you find a routine branch sitting here,
   moving it is a step edit — do it only if the step already exists to carry the
   `Condition:`; otherwise report it in `conflicts`.

**Order of the seven sections when you are done** (and the heading text,
verbatim, letterless):

    ### Scope
    ### At a Glance
    ### Before You Start
    ### Procedure
    ### Outputs & Evidence
    ### Key Controls
    ### Known Issues & Improvement Opportunities

**Untouched by this pass, and a defect if it changes:** callout bodies and their
`note:`/`detail:` split, callout **IDs** (never renumber — downstream judgment is
keyed on `(slug, id)`), `SRC-` citations, `[[slug]]` tokens, the `consult-meta`
block, the `<!-- scope note -->` comment, and step numbering.

**Report** (in addition to your normal return): `sections_merged` (the headings
you collapsed) and `facts_relocated` (one line per fact that changed section —
"Reviewer prose → Key Controls"). A pass that relocated nothing from A to B has
almost certainly not done step 1.

## Updates — leave no iteration artifacts

Update passes arrive with ONE trigger: new source(s), `review_notes`
(`_review/{slug}.notes.yaml`), or a `sections:` list (a **reprofile** pass — add
those sections and nothing else; see "The document profile" above for why the
heading must be written even when the finding is "none"). In a notes file, tracked
changes are
high-authority SME input — apply them; comments are instructions/questions —
answer in the body or raise a GAP if unresolved.

**Every notes item carries a `kind:`, and one kind is not an instruction.** Route
on it before you read the `note:` text:

- `kind: source` (with `src: SRC-<id>`) — a **new source** for your procedure.
  Look the id up in `_reference/sources.yaml`, **read that source file yourself**,
  and work its facts into the body under the same evidence discipline as a first
  draft. The `note:` text is only the "what's new" summary; the source is the
  evidence. The dispatch deliberately hands you no source list here — the id is
  the handle.
- `kind: review` | `rename` | `consolidation` — ordinary instructions; do what the
  item says.
- `kind: retirement` — another procedure is being retired. **Remove your
  references to the named retired procedure** (its `[[slug]]` token and any prose
  that depends on it); describe what it did inline where your reader still needs
  it. Leaving the token is a blocking reconcile error.

Either way, revise your prior draft so it reads as a single finished product with
no breadcrumbs:

- When a source **answers a prior GAP**, work the fact into the body and **delete
  the GAP entirely** — no "resolved"/"answered" markers.
- When a source **contradicts** existing text, update it (or raise a fresh GAP if
  unresolved); don't stack old and new.
- Remove any `TBD` the source now fills.
- Never renumber existing IDs.

## Before you finish

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py" {area}` if available —
it takes the **area folder**, not a single file — and fix any **ERRORS**
attributed to your own procedure (dangling ID, bare gap tag, prefix/label
mismatch). An unregistered `consult-meta` slug is a **WARNING, not an ERROR** —
leave your best-guess slug and report it (reconcile's only warnings are
unregistered slugs and possible name leaks).

## Style

Professional consulting language; current-state wording; functional roles; active
voice; concise steps; neutral descriptions. Avoid unsupported assumptions, blame
language, excessive caveats, named individuals in steps, and overuse of tables in
procedure bodies.

**Engagement registers (M24/M30):** citable entries — reference, never
restate; `[context]` entries — align, never evidence, never cited by register
name (prose cites the provenance SOURCE or raises a GAP) — full rule in your
agent contract ("Context entries — align, never evidence").

## What you return (COMPACT — no draft text)

- `slug`, `mode` (first-draft | update), `file` written
- counts: steps, controls (CTRL), open gaps (GAP), screenshots (SC), pain points
  (PP), improvements (IO)
- `consult_meta`: the systems/roles slugs you wrote
- `unregistered`: any system/role you used with no registry entry
- `unmapped_people`: personal names with no `people:` mapping + the role you
  resolved each to
- `conflicts`: source conflicts logged as GAPs (id + one line each)
- on update: `gaps_closed`, `tbds_filled`, `revised` (one line)
- when you applied the tag / callout rules to an existing draft: `tags_removed`,
  `conditions_added`, `callouts_split`
- `reconcile`: pass / the ERRORS you couldn't resolve

Do not return the procedure prose. The file is the deliverable.
