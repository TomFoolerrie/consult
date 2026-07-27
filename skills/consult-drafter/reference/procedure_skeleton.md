<!--
  procedure_skeleton.md — the per-procedure section skeleton.

  This is the single definition of procedure SHAPE. M0's scaffold.py stamps
  ONE copy of this block per procedure into `10_<slug>.md`, substituting the
  procedure title for `<Procedure Title>`. The consult-drafter fills it.

  SEVEN sections with declared jobs (M16 move 1) — Scope, At a Glance, Before
  You Start, Procedure, Outputs & Evidence, Key Controls, Known Issues &
  Improvement Opportunities. The jobs are the contract; see
  `skills/consult-drafter/SKILL.md` ("The sections").

  Rules enforced by the shape:
  - The procedure heading is a bare `##` with the PLAIN TITLE only — never a
    `1.1` number (the display number is derived and rendered late by the docx
    builder) and never an L2 bucket marker (the L2 bucket lives only in the
    manifest).
  - Sub-sections are `###` and carry the TITLE ONLY — never a letter prefix
    (M23: the A–G letter is display, stamped at render from the profile's
    section order, exactly like a procedure's `1.1` display number).
  - Callouts live in their HOME section (CONTROL→Key Controls, PAIN POINT /
    IMPROVEMENT OPPORTUNITY→Known Issues, VALIDATION REQUIRED + SCREENSHOT
    PLACEHOLDER inline in Procedure at their step).
  - Steps are `####`.
  - The `consult-meta` fenced block is end matter; the docx builder skips it.
  - The `<!-- unfilled -->` sentinel marks an un-drafted skeleton; the drafter
    removes it on first write. It is the orchestrator's "needs fill" predicate.
-->

## <Procedure Title>

<!-- unfilled -->

### Scope

TBD — what this procedure covers, what it explicitly EXCLUDES, and which
procedures adjoin it (`[[slug]]` for each). **Nothing else** — no preparer, no
systems, no trigger, no frequency: those live in At a Glance. 3–5 sentences.
(This section is what the dependencies agent reads.)

### At a Glance

<!-- A TABLE — one row per fact, and the single home for these facts. A cell
     that runs to prose means the content belongs in another section. -->

| Field | Value |
|---|---|
| Trigger | TBD |
| Frequency | TBD |
| Preparer | TBD |
| Reviewer | TBD |
| Systems | TBD |
| Key inputs | TBD |
| Key outputs | TBD |

### Before You Start

<!-- ONE LINE PER ARTIFACT: what it is — where it comes from — the state it
     must be in. Upstream artifacts carry the `[[slug]]` that supplies them. -->

- **<Artifact>** — TBD (`[[upstream-slug]]` where an upstream procedure supplies
  it); TBD — the state it must be in.

### Procedure

#### Step 1: TBD

TBD — Describe the step in neutral current-state procedural language. Add the
bolded inline tags below only where the detail helps execution, review, or
auditability — not mechanically on every step.

- **Condition:** TBD — only on a conditional step; no condition = main path.
- **System / Tool:** TBD — only where it DEPARTS from the card's default.
- **Navigation Path:** TBD
- **Fields / Parameters:** TBD
- **Expected Result:** TBD
- **Evidence Required:** TBD

<!-- Inline callouts live at the step they attach to (Procedure is home): -->

> **VALIDATION REQUIRED — GAP-01:** TBD — a fact, owner, timing, path, or decision to confirm.
> - **Nature:** unknown | conflict | unsupported-assumption
> - **Owner to confirm:** TBD

> **SCREENSHOT PLACEHOLDER — SC-01:** TBD — what to capture and what it must validate.

### Outputs & Evidence

- **Output 1:** TBD — downstream recipient where supported.
- **Evidence retained:** TBD — where, and for how long.
- **Not retained:** TBD — what is deliberately NOT kept (a negative finding is
  audit-relevant and has no other home).

### Key Controls

<!-- CONTROL callouts are the source for the Controls view — no table. -->

> **CONTROL — CTRL-001:** TBD — what is checked / reconciled / approved.
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** TBD
> - **Owner:** TBD

### Known Issues & Improvement Opportunities

<!-- DEFECTS ONLY — things that are WRONG. A branch the process handles
     routinely is a conditional step in Procedure, not a known issue.
     PAIN POINT + IMPROVEMENT callouts here ARE the structured source for
     Appendix A (assembled mechanically) — fill every field. -->

> **PAIN POINT — PP-001:** TBD — observed current-state friction, source-grounded.
> - **Impact:** TBD
> - **Severity:** High | Medium | Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** TBD — the proposed improvement (this IS the recommendation).
> - **Addresses:** PP-001

```consult-meta
systems: []
roles:   []
```
