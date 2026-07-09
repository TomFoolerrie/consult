<!--
  procedure_skeleton.md — the per-procedure A–H skeleton.

  This is the single definition of procedure SHAPE. M0's scaffold.py stamps
  ONE copy of this block per procedure into `10_<slug>.md`, substituting the
  procedure title for `<Procedure Title>`. The consult-drafter fills it.

  Rules enforced by the shape:
  - The procedure heading is a bare `##` with the PLAIN TITLE only — never a
    `1.1` number (the display number is derived and rendered late by the docx
    builder) and never an L2 bucket marker (the L2 bucket lives only in the
    manifest).
  - A–H sub-sections are `###`; steps are `####`.
  - Callouts live in their HOME section (CONTROL→F, PAIN POINT/IMPROVEMENT→H,
    VALIDATION REQUIRED + SCREENSHOT PLACEHOLDER inline in E at their step).
  - The `consult-meta` fenced block is end matter; the docx builder skips it.
  - The `<!-- unfilled -->` sentinel marks an un-drafted skeleton; the drafter
    removes it on first write. It is the orchestrator's "needs fill" predicate.
-->

## <Procedure Title>

<!-- unfilled -->

### A. Process Overview

TBD — What this procedure accomplishes, when it occurs, who performs it, what
it excludes, and how it connects to upstream / downstream activities. (This
section is what the dependencies agent reads.)

### B. Quick Reference

- **Trigger:** TBD
- **Frequency:** TBD
- **Preparer:** TBD
- **Reviewer:** TBD
- **Primary systems / tools:** TBD
- **Key outputs:** TBD

### C. Pre-Requisites

- TBD — what must be true before the procedure begins.

### D. Inputs

- **Input 1:** TBD — source / owner.

### E. Step-by-Step Procedure

#### Step 1: TBD

TBD — Describe the step in neutral current-state procedural language. Add the
bolded inline tags below only where the detail helps execution, review, or
auditability — not mechanically on every step.

- **System / Tool:** TBD
- **Navigation Path:** TBD
- **Fields / Parameters:** TBD
- **Expected Result:** TBD
- **Evidence Required:** TBD

<!-- Inline callouts live at the step they attach to (E is their home): -->

> **VALIDATION REQUIRED — GAP-01:** TBD — a fact, owner, timing, path, or decision to confirm.
> - **Nature:** unknown | conflict | unsupported-assumption
> - **Owner to confirm:** TBD

> **SCREENSHOT PLACEHOLDER — SC-01:** TBD — what to capture and what it must validate.

### F. Key Controls

<!-- CONTROL callouts are the source for the Controls view — no table. -->

> **CONTROL — CTRL-001:** TBD — what is checked / reconciled / approved.
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** TBD
> - **Owner:** TBD

### G. Outputs

- **Output 1:** TBD
- **Evidence retained:** TBD

### H. Known Issues & Improvement Opportunities

<!-- PAIN POINT + IMPROVEMENT callouts here ARE the structured source for
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
