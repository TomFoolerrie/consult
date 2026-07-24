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
  callouts: [CONTROL, VALIDATION REQUIRED, PAIN POINT,
             IMPROVEMENT OPPORTUNITY, SCREENSHOT PLACEHOLDER]
  derived: [index, roles, systems, dependencies, raci,
            appendix-a, appendix-b, appendix-c]
  inline_tags: [System / Tool, Navigation Path, Fields / Parameters,
                Expected Result, Evidence Required]
```

Absent file → today's full set (no behavior change).

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

## Out of scope

- Per-procedure profiles (engagement/area granularity only).
- Reordering or renaming sections (A–H identity is the heading contract).
- A profile editor/wizard — it's a small hand-edited YAML file.
