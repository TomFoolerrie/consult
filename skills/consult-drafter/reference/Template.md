# Finance Desktop Procedures

_Current-state desktop procedures._

<!--
  HEADING CONTRACT (docs/README.md):
  - Exactly ONE `#` in the assembled document — the title above. Its subtitle is
    the italic tagline on the next non-blank line. M2 lifts BOTH into the
    manifest (title + subtitle); the docx cover reads them. Component files on
    disk carry no `#`.
  - Every section is `##`. `##` is the ONLY thing that starts a new fragment, so
    the splitter yields exactly one fragment per section — no wrapper headings.
  - Inside a procedure: A–H are `###`, steps are `####`.
  - Static sections are human-owned. Procedure sections are the source of truth
    (fill agent / human). Derived sections are generated and carry a
    `<!-- derived: KIND; writer: W -->` marker — never hand-edit them.
  - The per-procedure A–H block is defined once in `procedure_skeleton.md` and
    reproduced below as the single procedure example.
-->

---

## Document Profile

<!-- static; human-owned -->

| Field | Value |
|---|---|
| Client / Organization | TBD |
| Process Name | TBD |
| L1 Business Cycle | TBD |
| L2 Process Area | TBD |
| Version | v0.1 |
| Date | TBD |
| Prepared By | TBD |
| Document Owner | TBD |
| Classification | Internal Use Only |
| Status | Draft |

---

## How to Use This Document

<!-- static; human-owned -->

This document provides current-state desktop procedures for **[Process Name]**,
written for preparers, reviewers, approvers, process owners, and audit /
compliance stakeholders.

Each procedure follows a consistent A–H structure:

- **A. Process Overview** — what the procedure accomplishes and where it fits.
- **B. Quick Reference** — trigger, cadence, owners, systems, key outputs.
- **C. Pre-Requisites** — what must be true before it begins.
- **D. Inputs** — reports, files, approvals, extracts, confirmations used.
- **E. Step-by-Step Procedure** — execution steps with judgment-placed system,
  navigation, field, expected-result, and evidence detail, plus inline
  validation-gap and screenshot callouts.
- **F. Key Controls** — control points embedded in the procedure.
- **G. Outputs** — what it produces and where outputs flow downstream.
- **H. Known Issues & Improvement Opportunities** — current-state friction and
  future-state opportunities (the source for Appendix A).

---

## Document Control

<!-- static; human-owned -->

This is a living document. The process owner keeps it current as systems, roles,
controls, and business requirements evolve.

**Review frequency:** TBD

| Version | Date | Author | Summary of Changes | Status |
|---|---|---|---|---|
| v0.1 | TBD | TBD | Initial draft. | Draft |

---

## Source Materials

<!-- static; human-owned. Canonical SRC- registry lives in _reference/sources.yaml. -->

| Source ID | Source | Type | Date | Owner / Provider | Used For |
|---|---|---|---|---|---|
| SRC-001 | TBD | TBD | TBD | TBD | TBD |

---

## Process Overview

<!-- static; human-owned narrative -->

TBD — Describe what the process accomplishes, why it is performed, and the
business outcome it supports.

<!--
  DEFERRED / DERIVED, not authored here:
  - The In-Scope Sub-Processes / L3 index is python-derived (M3) — no
    hand-edited copy lives in this template.
  - Process Flow Summary is dropped for the MVP (no clean owner; not needed for
    a working system).
-->

---

<!--
  PROCEDURES. One `## <Plain Title>` per L3 procedure. The block below is the
  canonical procedure shape, kept in sync with `procedure_skeleton.md` (what
  scaffold.py stamps). Repeat once per procedure; in the folder model each
  procedure is its own `10_<slug>.md` fragment.
-->

## Bank Reconciliation

<!-- unfilled -->

### A. Process Overview

TBD — What this procedure accomplishes, when it occurs, who performs it, what it
excludes, and how it connects to upstream / downstream activities. (This section
is what the dependencies agent reads.)

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

> **VALIDATION REQUIRED — GAP-01:** TBD — a fact, owner, timing, path, or decision to confirm.
> - **Nature:** unknown | conflict | unsupported-assumption
> - **Owner to confirm:** TBD

> **SCREENSHOT PLACEHOLDER — SC-01:** TBD — what to capture and what it must validate.

### F. Key Controls

> **CONTROL — CTRL-001:** TBD — what is checked / reconciled / approved.
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** TBD
> - **Owner:** TBD

### G. Outputs

- **Output 1:** TBD
- **Evidence retained:** TBD

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** TBD — observed current-state friction, source-grounded.
> - **Impact:** TBD
> - **Severity:** High | Medium | Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** TBD — the proposed improvement (this IS the recommendation).
> - **Addresses:** PP-001

```consult-meta
systems: []
roles:   []
```

---

<!--
  DERIVED SECTIONS. Each is generated by exactly one writer and carries a
  `<!-- derived: KIND; writer: W -->` marker; reconcile.py errors if a declared
  derived file is missing its marker. Do not hand-edit. Column shapes shown for
  reference only.
-->

## Role Dictionary

<!-- derived: roles; writer: python -->
> _Generated from `_reference/roles.yaml` + usage — do not hand-edit._

| Functional Role | Reports To | Standard Responsibilities | Appears In |
|---|---|---|---|
| _(generated)_ | | | |

---

## RACI Matrix

<!-- derived: raci; writer: agent -->
> _Generated by the RACI agent — do not hand-edit._

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| _(generated)_ | | | | |

---

## Systems & Data Inputs

<!-- derived: systems; writer: python -->
> _Generated from `_reference/systems.yaml` × procedure `consult-meta` usage — do not hand-edit._

| System / Tool | Role in Process | Known Limitations | Appears In |
|---|---|---|---|
| _(generated)_ | | | |

---

## Key Dependencies

<!-- derived: dependencies; writer: agent -->
> _Generated by the dependencies agent from each procedure's A. Process Overview — do not hand-edit._

| Upstream Dependency | Downstream Dependency |
|---|---|
| _(generated)_ | |

---

## Appendix A — Pain Points & Improvement Opportunities

<!-- derived: appendix-a; writer: python -->
> _Assembled mechanically from the PP-/IO- callouts in each procedure's H section — do not hand-edit. Rows are typed: Pain Points and Improvement Opportunities have different columns._

**Pain Points**

| ID | Observation | Impact | Severity | Source Procedure |
|---|---|---|---|---|
| _(generated)_ | | | | |

**Improvement Opportunities**

| ID | Recommendation | Addresses | Source Procedure |
|---|---|---|---|
| _(generated)_ | | | |

---

## Appendix B — Gap / Validation Log

<!-- derived: gap-log; writer: python -->
> _Assembled mechanically from VALIDATION REQUIRED callouts — do not hand-edit._

| Gap ID | Nature | Description | Owner to Confirm | Source Procedure |
|---|---|---|---|---|
| _(generated)_ | | | | |

---

## Appendix C — Screenshot / Evidence Index

<!-- derived: screenshot-index; writer: python -->
> _Assembled mechanically from SCREENSHOT PLACEHOLDER callouts — do not hand-edit._

| SC ID | Caption | Source Procedure | Status |
|---|---|---|---|
| _(generated)_ | | | |

---

## Appendix D — Glossary & Reference

<!-- derived: glossary; writer: python -->
> _Generated from `_reference/glossary.yaml` — do not hand-edit._

| Term | Definition |
|---|---|
| _(generated)_ | |
