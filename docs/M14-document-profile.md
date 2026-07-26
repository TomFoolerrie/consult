# M14 — Document profile (which sections exist, changeable mid-engagement)

> **Status: DESIGNED.**

## Goal

Make the document's **shape** configurable per engagement — not every engagement
wants `F. Key Controls`, a pain-point register, or a RACI — and make changing
that decision mid-engagement safe, with the expensive direction **quoted before
it is spent**.

## Why

Today the A–H shape and the derived back matter are fixed. Real engagements
differ: a pure desktop-procedure job has no controls scope; a controls-focused
one wants F and Appendix A but not improvement opportunities. Hard-coding one
shape means hand-deleting sections at the end, which is exactly the kind of
manual finishing this system exists to remove.

## Design

### The profile

`_client/profile.yaml` (resolved via M13, so it is engagement-wide by default):

```yaml
profile:
  sections: [A, B, C, D, E, F, G, H]     # A/B/E are mandatory; others optional
  body_omit: [F, H]                      # authored + aggregated, not shown in the procedure
  callouts: [CONTROL, VALIDATION REQUIRED, PAIN POINT,
             IMPROVEMENT OPPORTUNITY, SCREENSHOT PLACEHOLDER]
  derived: [index, roles, systems, dependencies, raci,
            appendix-a, appendix-b, appendix-c, appendix-controls]
  inline_tags: [System / Tool, Navigation Path, Fields / Parameters,
                Expected Result, Evidence Required]
```

Absent file → today's full set, and `body_omit` empty (no behavior change).

### Enforced in exactly two places

1. **Scaffold** — the skeleton contains only the profile's sections; the
   manifest lists only the profile's derived components.
2. **Render** — sections and callout kinds not in the profile are **stripped**,
   reusing the final-mode strip machinery.

The drafter reads the profile only to know which callout kinds and inline tags
are in play; it never decides shape.

### The asymmetry that makes this safe

- **Removing** a section is free and reversible: render strips it, fragments
  keep their content harmlessly, and turning it back on restores the text that
  was always there.
- **Adding** a section after drafting is the expensive direction: fragments
  scaffolded under the old profile genuinely have no such content, so each needs
  a drafter update pass.

### `body_omit` — authored, aggregated, not in the procedure body

`sections:` answers "does this content exist at all?" It cannot answer "exists,
but belongs in the appendix rather than in the procedure" — because it drives
**both** enforcement points at once. Drop `H` and the skeleton has no `H`, so the
drafter never authors a pain point, so **Appendix A renders empty**. The register's
own generated header states the dependency: *"aggregated mechanically from the `H`
section callouts."* Same for `F` and controls.

`body_omit` separates the two jobs. A listed section is scaffolded, drafted and
aggregated exactly as now, and omitted only from the **rendered procedure body**.
It must be a subset of `sections:` — omitting something that does not exist is a
profile error, and fails loud.

The motivating shape: procedures that read as clean operational text, with
controls and pain points collected into auditor-facing registers instead of
interrupting the steps.

Two properties worth stating, because they differ from `sections:`:

- **Free and reversible in both directions.** Unlike removing a section from
  `sections:` (free out, expensive back in), `body_omit` never loses content and
  never needs a drafter pass either way. The fragment is untouched; only the
  render changes.
- **Never trips `reprofile`.** The headings are present, so the drift detector
  below has nothing to detect. `body_omit` and the migration guard do not interact.

Reconcile is likewise unaffected: it validates `[[slug]]` and callout references
against fragment sources, not against the rendered output, so a cross-reference
from an omitted section still resolves.

### `appendix-controls` — the destination F never had

Pain points already have a register (Appendix A, Python-owned, built from the `H`
callouts). **Controls have none** — `F. Key Controls` is a section, and the derived
set is index, roles, systems, dependencies, RACI, and appendices A/B/C. So
`body_omit: [F]` without a destination would simply hide the controls.

Add `appendix-controls`: a Python-owned register built from the `F` callouts
(`CTRL-` ids, with the control statement and its owning procedure), the same
mechanical aggregation Appendix A already performs on `H`. No new machinery — the
callout parser, the ID scheme and the grouping all exist.

### The trade-off to make deliberately

Controls read in the context of the step they govern, and they cross-reference it —
live example, `CTRL-003` ends *"see the ACH second-approver gap at Step 4a."* A
matrix loses that adjacency, and a preparer reading only the procedure body no
longer sees the control that constrains what they are doing.

That is the right shape for an audit deliverable and the wrong shape for a
training document. Hence `body_omit` is a per-engagement choice with an **empty
default** — never inferred, and not something a profile should acquire quietly.

### Drift detection — no new state file

**The signal is already on disk: a fragment missing a heading the profile
requires.** Scaffold always writes headings, so a missing one means exactly one
thing — that fragment predates the profile change. This is preferred over a
`profile_hash` in the manifest: nothing to keep in sync, it survives hand edits,
and it is per-procedure rather than all-or-nothing.

New advisor guard, immediately after `fill` (same family — both are "fragments
aren't in their target shape yet"):

```
reprofile   profile requires section(s) absent from N fragment(s)
            details: {missing: {slug: [sections]}, dispatches: N}
```

Handler: report the count **first** ("12 drafter dispatches to add F. Key
Controls — proceed?"), and only on the user's go-ahead dispatch drafters in
update mode with the section list. Partial acceptance is fine: the guard is
per-procedure, so an area can sit half-migrated indefinitely without wedging the
loop.

Termination: a drafter writes the heading even when the answer is "no controls
identified in the current state" (a legitimate finding, and better recorded than
blank) — so the guard clears and cannot re-fire forever.

Removals need no action at all: the next render simply omits them.

### Interaction with existing gates

`reprofile` sits below `fill` (skeletons first) and above `aggregate` (don't
build views from a shape that's about to change). Since it is a cost gate, it
sets `human_gate: true`.

## Acceptance

- No `profile.yaml`: manifest, skeletons, and render byte-identical to today.
- Profile without F: skeletons have no F, render shows no F, reconcile clean.
- Add F to the profile after drafting: advisor returns `reprofile` naming every
  procedure and the dispatch count; after the drafters run it clears.
- Remove F from the profile after drafting: no `reprofile`, render omits F,
  fragments untouched; re-adding it does not re-dispatch (the headings are still
  there).
- `derived` without `raci`: no RACI component in the manifest, `synthesize`
  never dispatches the RACI agent.
- `body_omit: [H]`: the rendered procedure has no `H` section, **Appendix A is
  unchanged and non-empty**, fragments still carry their pain-point callouts, and
  no drafter is dispatched. Removing the entry restores `H` with no re-draft.
- `body_omit: [F]` with `appendix-controls` in `derived`: no `F` in the procedure
  body, every `CTRL-` id present exactly once in the controls register, and each
  row naming its owning procedure.
- `body_omit: [F]` **without** `appendix-controls`: profile error, named — the
  controls would otherwise vanish from the document.
- `body_omit` naming a section absent from `sections`: profile error, named.
- `body_omit` never causes `reprofile` to fire.
- A `[[slug]]` reference inside an omitted section still passes reconcile.
- Empty/absent `body_omit`: render byte-identical to today.

## Out of scope

- Per-procedure profiles (engagement/area granularity only).
- Reordering or renaming sections (A–H identity is the heading contract).
- A profile editor/wizard — it's a small hand-edited YAML file.
