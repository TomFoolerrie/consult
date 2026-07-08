---
name: consult-drafter
description: "Drafts formal consulting-style process documentation and desktop procedures."
---

# Consult Drafter

**ALWAYS LOAD `reference/Template.md` DIRECTLY AFTER READING THIS SKILL.** Read it in full before drafting anything — it is the canonical document structure for every deliverable this skill produces, and drafting without it will produce a non-conforming document.

## Purpose

Draft lean, client-ready finance process documentation and desktop procedures from cleaned source materials, including prior drafts, walkthrough notes, process inventories, controls, risks, gaps, and screenshot plans.

This skill produces a **complete, DOCX-friendly Markdown deliverable** that can be converted downstream into Word. The output should read like a practical desktop procedure, not a database export or audit matrix.

The system uses a single document architecture:

- **L1 | Overall Finance / Business Cycle** — broad finance cycle or parent context.
- **L2 | Process Area** — the process area covered by the document.
- **L3 | Step-by-Step Procedures** — recurring activities or sub-processes documented in detail.

Template guidance lives in two places:

- **This skill** explains the drafting workflow, evidence discipline, structure rules, and quality checks.
- **`reference/Template.md`** is the lean, DOCX-friendly Markdown shell and the canonical document structure. Load it directly after reading this skill and use it as the default structure unless the user provides a more specific template.

Supporting scripts in `scripts/`, used on demand:

- **`reconcile.py`** — ID-integrity validator; runs on a single assembled file or a split project.
- **`split_doc.py` / `assemble_doc.py`** — break a large draft into editable component files and reassemble them with all content preserved — inter-section whitespace is normalized (see "Build Scripts, Don't Retype").

---

## Required Inputs

Use available source files and infer non-blocking metadata where reasonable. If information is missing, use **TBD — confirm with process owner** and log material unknowns inline with **Step-by-Step Procedures** AND in **Appendix B | Gap / Validation Log**.

---

## Core Evidence Standard

Use balanced evidence discipline.

You may add obvious connective tissue for readability and sequencing, including:

- Combining repeated statements.
- Normalizing role names.
- Sequencing steps when order is clearly implied.
- Converting conversational notes into neutral procedural language.
- Writing transitions that add no new procedural facts.

Do **not** fabricate procedural facts. Never invent:

- Systems or tools.
- System navigation paths.
- Field names or parameter values.
- Approval thresholds.
- Review owners or approvers.
- Control evidence.
- Timing or frequency.
- Archive locations.
- Report names.
- Downstream recipients.
- Exception handling.
- Screenshot availability.

When source support is unclear, incomplete, contradictory, or missing, use the following formal gap tag:

- Example:`[[GAP-01 — SYSTEM PATH UNKNOWN]]`

If sources conflict, do not choose silently. State the conflict and log a gap. For routine cases where a prior draft conflicts with fresher dated walkthrough notes, prefer the most recent dated source only when there is no true contradiction; note the basis in the drafting note if needed.

---

## Drafting Emphasis

Default to **current-state desktop procedure documentation**.

The deliverable should be practical for:

- A preparer executing the task.
- A reviewer validating completion.
- A process owner maintaining the process.
- An audit or compliance stakeholder understanding evidence and controls.

If source materials are sparse, unstable, or heavily improvement-oriented:

- Keep the step-level detail lighter.
- Document only confirmed current-state activities.
- Route material unknowns to **Appendix B | Gap / Validation Log**.
- Capture friction and future-state ideas in **Appendix A | Risks, Pain Points & Improvement Opportunities**.

---

## Canonical Structure

`reference/Template.md` is the authoritative section order — follow it. In brief:

- **Front matter:** Document Profile, How to Use This Document, Document Control, Source Materials.
- **Current-State Process Documentation:** Process Overview (Purpose; In-Scope Sub-Processes / L3 Procedures); Process Flow Summary.
- **Step-by-Step Procedures:** one module per L3 procedure, each using the A–H structure below.
- **Governance:** Roles & Responsibilities; Systems & Data Inputs; Key Dependencies.
- **Appendices:** A — Risks, Pain Points & Improvement Opportunities; B — Gap / Validation Log; C — Screenshot / Evidence Index; D — Glossary & Reference.

---

## Procedure Module Rules

Each L3 procedure should use the A–H structure.

### A. Process Overview

Briefly describe:

- What the procedure accomplishes.
- When it occurs.
- Who performs it.
- What it excludes.
- How it connects to upstream and downstream activities.

### B. Quick Reference

- **Trigger:** TBD
- **Frequency:** TBD
- **Preparer:** TBD
- **Reviewer:** TBD
- **Primary systems / tools:** TBD
- **Key outputs:** TBD
- **Related control references:** TBD
- **Related risk / gap references:** TBD

### C. Pre-Requisites

Use bullets. Document what must be true before the procedure begins.

### D. Inputs

Use bullets. Include the source, owner, location, or format only when supported and useful.

### E. Step-by-Step Procedure

Write steps as clear numbered or titled procedural steps.

Use supplemental step metadata selectively. Include details such as system/tool, navigation path, fields/parameters, expected result, and evidence only when the detail helps the preparer execute the step, helps the reviewer validate completion, or supports auditability.

Preferred pattern:

```md
##### Step X: Action Title

Describe the action in concise current-state procedural language.

- **System:** TBD 
- **Key field / parameter:** TBD
- **Expected result:** TBD 

> **CONTROL — CTRL-001:** Describe the embedded review, reconciliation, approval, or system check.

> **Evidence:** Describe retained evidence, if applicable.
```

### F. Key Controls

Use a table when controls are identified or implied by the source materials.

### G. Outputs

Use bullets. Include outputs, downstream recipients, systems of record, archive locations, and evidence retained only where supported.

### H. Known Issues / Improvement Notes

Use bullets. Include issue, impact, recommendation, owner, and status where known.

Recommended pattern:

```md
- **Known issue / pain point:** TBD  
  **Impact:** TBD  
  **Recommendation:** TBD  
  **Owner:** TBD  
  **Status:** Open / In progress / Resolved
```

---

## Inline Callout Rules

Callouts should appear inline within the relevant procedure step.

Approved callout labels:

```md
> **CONTROL — CTRL-001:** ...
> **VALIDATION REQUIRED — GAP-01:** ...
> **PAIN POINT — PP-001:** ...
> **IMPROVEMENT OPPORTUNITY — IO-001:** ...
> **SCREENSHOT PLACEHOLDER — SC-01:** ...
```

Use callouts only where they help the reader understand execution risk, judgment, evidence, open items, or improvement opportunities at the point in the process where those items matter.

---

## Exceptions and Escalations

Document exceptions, escalation paths, rejection handling, rework, or fallback procedures inline within the relevant step when those details are supported by source materials.

---

## Screenshot / Evidence Placeholder Rules

Do not insert screenshots.

Use screenshot / evidence IDs such as **SC-01**, **SC-02**, etc.

In the procedure body, insert placeholders as inline callouts:

```md
> **SCREENSHOT PLACEHOLDER — SC-01:** User to insert screenshot showing the specific screen, report, approval, output, or control evidence. Caption should describe what the user must validate.
```

Populate **Appendix C | Screenshot / Evidence Index** with:

- SC ID
- Caption
- Procedure / Step
- Source
- Status

Only request screenshots or evidence that:

- Reduce execution risk.
- Clarify navigation.
- Evidence a control.
- Document a key output.
- Resolve a material uncertainty.

---

## Gap / Validation Rules

Every material uncertainty must appear in **Appendix B | Gap / Validation Log**.

Use body gap tags where the uncertainty appears:

```md
[[GAP-01 — SYSTEM PATH UNKNOWN]]
[[GAP-02 — OWNER TO CONFIRM]]
[[GAP-03 — EVIDENCE RETENTION UNKNOWN]]
```

Rules:

- Body gap tags must carry the same ID used in Appendix B.
- Do not write bare `[[GAP — ...]]` tags without an ID.
- Each body tag should map to one Appendix B row.
- Check Appendix B for current gap ID's, do not repeat already used ID's.
- Use gaps for material unknowns, contradictions, unsupported assumptions, missing owners, missing system paths, unresolved timing, unclear controls, and uncertain evidence retention.
- Do not overuse gap tags for minor wording placeholders that do not affect execution, control, ownership, or evidence.

---

## Risks, Pain Points, and Improvement Opportunities

Capture confirmed current-state friction and improvement ideas in two places:

1. Inline within the relevant procedure step or procedure H section.
2. **Appendix A | Risks, Pain Points & Improvement Opportunities**.

Use these ID prefixes:

- **PP-###** for pain points.
- **IO-###** for improvement opportunities.

---

## Numbering Convention

Use two-level procedure numbering by default, such as:

- 1.1
- 1.2
- 1.3

Use consistent ID prefixes:

- **CTRL-###** for controls unless source materials provide client-specific control IDs.
- **PP-###** for pain points.
- **IO-###** for improvement opportunities.
- **GAP-##** for validation gaps.
- **SC-##** for screenshots or evidence placeholders.
- **SRC-###** for source materials.

---

## Drafting Workflow

### Step 1 — Intake Scan

Identify:

- Process name.
- Client / organization.
- L1 business cycle.
- L2 process area.
- L3 sub-processes.
- Source materials.
- Roles.
- Systems.
- Inputs.
- Outputs.
- Controls.
- Pain points.
- Improvement opportunities.
- Gaps.
- Screenshot / evidence candidates.

Assign source IDs such as **SRC-001**, **SRC-002**, etc.

### Step 2 — Build the Lean Markdown Shell

Follow the canonical structure and the user's provided template.

### Step 3 — Draft Current-State Process Documentation

Populate:

- Process Overview.
- Purpose.
- In-Scope Sub-Processes / L3 Procedures.
- Process Flow Summary.

Use functional role names where possible.

### Step 4 — Draft Step-by-Step Procedures

For each L3 procedure:

- Use the A–H module.
- Write current-state steps in practical execution language.
- Add system, navigation, field, expected-result, and evidence details selectively.
- Place callouts inline.
- Do not invent unsupported facts.

### Step 5 — Draft Controls, Outputs, and Dependencies

Capture supported controls, outputs, upstream dependencies, and downstream dependencies.

Where a control is unclear, log a validation gap rather than inventing the control.

### Step 6 — Draft Risks, Pain Points, and Improvement Opportunities

Capture confirmed pain points and future-state opportunities inline and in Appendix A.

### Step 7 — Draft Screenshot / Evidence Placeholders

Insert screenshot placeholders only where materially useful and index them in Appendix C.

### Step 8 — Draft Gap / Validation Log

Route material unknowns to Appendix B and reconcile body gap tags to Appendix B rows.

### Step 9 — Cleanup and Reconciliation

Before finalizing:

- Remove unused placeholder rows.
- Remove generic TBD rows that do not represent real unknowns.
- Confirm body gap tags reconcile to Appendix B.
- Confirm screenshot placeholders reconcile to Appendix C.
- Confirm pain points and opportunities reconcile to Appendix A.
- Confirm controls are defined where referenced.
- Confirm numbering is consistent.

For larger or ID-heavy deliverables, run `scripts/reconcile.py` — either on the split project directory (it walks `manifest.json`, no assembly needed) or on the assembled file.

---

## Build Scripts, Don't Retype

For any task larger than a single short procedure — especially consolidations or repackaging large prior drafts — read source drafts from disk, transform them with scripts, and assemble the pieces rather than re-emitting long procedure text manually.

Retyping large tables or long procedures is slow and introduces transcription drift. Use model judgment for structure, scope, overlap, evidence gaps, and drafting quality; use scripts for repetitive assembly and ID reconciliation where practical.

### Iterating on a large draft

For large or ID-heavy documents, iterate on components instead of re-emitting the whole file:

1. `python3 scripts/split_doc.py ASSEMBLED.md OUT_DIR` — break the document into one component file per major section, with each procedure and each appendix on its own, plus a `manifest.json` that records their order.
2. Edit only the component file(s) you need. This keeps each turn small and avoids transcription drift in untouched sections.
3. QC as you go — no assembly required. `reconcile.py` walks the manifest and checks IDs across all fragments together, so you can validate the split project directly between edits.
4. `python3 scripts/assemble_doc.py OUT_DIR REBUILT.md` — only when you want the final single file. Stitches the components back together in manifest order, preserving all content (inter-section whitespace is normalized).

IDs reconcile across the whole document, not within a single fragment, so run the QC gate one of two ways — on the split project (no assembly needed) or on an assembled file — but never on a single component:

```text
python3 scripts/reconcile.py OUT_DIR      # split project: walks manifest.json; reports <component>:<line>
python3 scripts/reconcile.py REBUILT.md   # single assembled file: reports <line>
```

Expect ORPHAN warnings for any template placeholder rows you have not yet populated or pruned (for example `CTRL-002` or `SC-02`) — these are not errors and clear once Step 9 removes unused rows. Only ERRORS — bare tags, dangling references, missing components — return a non-zero exit and must be resolved.

Reconciling the split project directly is the cheaper loop: edit a component, reconcile the directory, repeat — and assemble only at the end. To add a section mid-project, create the component file and insert it into `manifest.json` at the right position; assembly and reconciliation both follow manifest order.

---

## Formatting Rules for DOCX-Friendly Markdown

Use:

- Standard heading levels.
- Pipe-style Markdown tables where possible.
- Bullets and numbered lists.
- Blockquotes for inline callouts.
- Plain-text placeholders such as **TBD — confirm with process owner**.
- Short paragraphs.
- Functional role names instead of individual names unless names are specifically required.

Avoid:

- Raw HTML in final user-facing Markdown.
- Nested tables.
- Mermaid diagrams.
- Footnotes unless required.
- Complex Markdown extensions.
- Raw Word field codes.
- Variable syntax such as `{{variable.name}}`.
- A Markdown Table of Contents.

---

## File Naming Standard

When creating a file, include the version in the filename.

If the user provides a version or revision label, use that value exactly after light filename-safe normalization. If no version is provided, use **v0.1** and log the version assumption in the drafting note if relevant.

Normalize the process name with lowercase hyphenated words, removing characters that are not filename-safe.

Use this pattern:

```text
[process-name]_process-doc_[version].md
```

Examples:

- `accounts-payable_process-doc_v1.0.md`
- `month-end-close_process-doc_v0.1.md`
- `financial-statement-close_process-doc_v0.1.md`

---

## Style

Use:

- Professional consulting language.
- Current-state wording.
- Functional roles.
- Active voice.
- Concise steps.
- Neutral descriptions.
- Clear distinction between current-state procedure and future-state recommendations.

Avoid:

- Unsupported assumptions.
- Blame language.
- Excessive caveats.
- Named individuals in process steps unless required.
- Overly academic process taxonomy language.
- Overuse of tables in procedure bodies.

---

## Final Response

When returning a drafted document, provide:

- A concise drafting note.
- Key assumptions.
- Major gaps or validation items.
- Screenshot / evidence placeholder count, if applicable.
- A link to the saved Markdown file, if file output was requested.

---

## Quality Checklist

Before finalizing, verify:

- The single L1 → L2 → L3 hierarchy is clear.
- Canonical section order is preserved.
- Document Control is updated to reflect any changes
- Source Materials are populated or marked TBD.
- In-Scope Sub-Processes / L3 Procedures are listed.
- Process Flow Summary is populated where sources support it.
- Each procedure uses the A–H structure.
- Procedure steps do not invent unsupported facts.
- Callouts appear inline, not in a standalone callout section.
- Controls are supported by source materials or logged as validation gaps.
- Pain points and opportunities are reflected in Appendix A.
- Body gap tags carry IDs and reconcile to Appendix B.
- Screenshot / evidence placeholders are blockquotes and reconcile to Appendix C.
- Numbering and ID prefixes are consistent.
- Unused default placeholder rows are removed.
- File name includes the version when a file is created.
- Output is ready for downstream Markdown-to-DOCX conversion.
