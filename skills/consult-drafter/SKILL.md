---
name: consult-drafter
description: Draft canonical SOP Markdown from cleaned process sources, including procedures, gaps, controls, pain points, and screenshot placeholders.
---

# Drafter Skill

## Purpose

Draft a canonical Markdown SOP / desktop procedure deliverable from pre-processed source materials.

The output must follow `references/canonical_sop_deliverable_template.md` unless the user provides a more specific template.

## Use This Skill When

Use this skill when the user asks to:

- Draft an SOP or desktop procedure
- Convert cleaned walkthrough notes into a procedure
- Build current-state process documentation
- Populate the canonical SOP template
- Create a procedure with gaps, controls, outputs, pain points, and screenshot placeholders

Do not use this skill for raw transcript cleanup, standalone evidence audits, Word comment resolution, screenshot insertion, or Markdown-to-Word conversion.

## Required Inputs

Use available source files and infer non-blocking metadata where reasonable. If missing, use `TBD` and log the item in Appendix C.

Minimum useful inputs:

- Process name or process area
- At least one cleaned source Markdown file or prior SOP draft

Helpful optional inputs:

- Client / organization name
- Project / workstream name
- L1 / L2 / L3 taxonomy
- Control matrix
- RACI notes
- Screenshot inventory
- Prior SOP draft
- SOP version or revision label, if the user has provided one
- Style or branding configuration

## Scope Level Handling

Before drafting, determine whether the user is requesting an **L1-Level** or **L2-Level** SOP deliverable.

### L2-Level SOP Deliverable

Use this scope when the user requests one specific L2 process area, one process area, or one discrete process grouping.

Examples:

- "Draft an SOP for Local FS Preparation"
- "Create the SOP for Account Reconciliations"
- "Document the GTN process"
- "One doc per L2"

In L2-Level mode:

- The document covers one L2 process area.
- The L1 Business Cycle is shown as parent context.
- L3 sub-processes / procedures become the detailed procedures.
- Use the canonical template structure as-is.
- The Sub-Process Inventory lists L3s / procedures within the selected L2.
- The Process Flow Summary describes flow across the L3s within that L2.
- The Cross-Reference Matrix links procedure-level controls, pain points, gaps, screenshots/evidence, and outputs.

### L1-Level SOP Deliverable

Use this scope when the user requests one full L1 business cycle, multiple L2 process areas under the same L1, or explicitly asks for one document per L1.

Examples:

- "Create one SOP for Financial Statement Close"
- "I want one document covering all close processes"
- "Build one doc per L1"
- "Cover L1-L2-L3 in a single document"
- "Combine the L2 SOPs under the Financial Statement Close cycle"

In L1-Level mode:

- The document covers one L1 business cycle.
- Each L2 process area becomes a major section within the document.
- Each L3 sub-process / procedure is documented under its parent L2.
- Add an L2 Process Area Inventory before the Sub-Process Inventory.
- Group Detailed Procedures by L2 process area.
- Preserve L2-specific numbering prefixes for procedures, controls, pain points, opportunities, gaps, screenshots/evidence, and outputs.
- Aggregate roles, systems, dependencies, controls, pain points, gaps, evidence, and improvement opportunities across all included L2s.
- Add an L2 Process Area column to the Cross-Reference Matrix.
- If some L2s have insufficient detail, include them in the L2 Process Area Inventory and log missing procedure detail in Appendix C.

### Scope Ambiguity Rule

- If the user's request clearly names one L2 process area, default to L2-Level mode.
- If the user's request clearly names one L1 business cycle or multiple L2 process areas under the same L1, default to L1-Level mode.
- If scope is ambiguous, infer the likely scope from the taxonomy and source files where reasonable. If the output scope materially affects document structure and cannot be inferred, ask one clarification question before drafting.

### Scope Statement Requirement

In the drafting note and Document Profile, explicitly state the selected scope level:

- `Scope Level: L1-Level SOP Deliverable`
- `Scope Level: L2-Level SOP Deliverable`

Also state why that scope was selected based on the user's request.

## Evidence Standard: Balanced

Use balanced evidence discipline.

You may add obvious connective tissue for readability and sequencing, including:

- Combining repeated statements
- Normalizing role names
- Sequencing steps when order is clearly implied
- Converting conversational notes into neutral procedural language
- Writing transitions that do not add procedural facts

Do not fabricate procedural facts. Flag uncertainty when source support is unclear, incomplete, contradictory, or missing.

Never invent:

- Systems
- Navigation paths
- Field names
- Approval thresholds
- Review owners
- Control evidence
- Timing or frequency
- Archive locations
- Report names
- Downstream recipients
- Exception handling
- Screenshot availability

## Version / File Naming Standard

When creating a file, include the SOP version in the filename.

- If the user provides a version or revision label, use that value exactly after light filename-safe normalization.
- If no version is provided, use `v0.1` and log the version assumption in the drafting note.
- Normalize the process name for filenames by using lowercase words separated by hyphens and removing characters that are not filename-safe.
- For L2-Level mode, use the L2 process area name as the process name where available.
- For L1-Level mode, use the L1 business cycle name as the process name where available.
- Save Markdown deliverables using this pattern:
  - `[process-name]_sop_draft_[version].md`
- Examples:
  - `accounts-payable_sop_draft_v1.0.md`
  - `month-end-close_sop_draft_v0.1.md`
  - `financial-statement-close_sop_draft_v0.1.md`
- If generating downstream Word, PDF, or PowerPoint files from the SOP, preserve the same base filename and append the appropriate extension.

## Gap Tags

Use the generalized gap tags in `references/gap_tags.md`.

Every material gap tag used in the body must be logged in Appendix C | Gap / Validation Log.

## Output Modes

Classify the deliverable into one of three modes:

1. **Procedure Mode** — Stable enough for repeatable desktop procedure documentation.
2. **Improvement Narrative Mode** — Current state is unstable, manual, broken, temporary, or under redesign.
3. **Discovery / Triage Mode** — Insufficient information to determine procedure vs. improvement narrative.

If unclear, use Discovery / Triage Mode.

## Drafting Workflow

### Step 1 — Intake Scan

Identify:

- Scope level: L1-Level or L2-Level
- Scope selection rationale
- Known taxonomy
- L1 business cycle
- L2 process area(s)
- L3 sub-processes / procedures
- Sources
- Roles
- Systems
- Inputs
- Outputs
- Controls
- Pain points
- Improvement opportunities
- Gaps
- Screenshot candidates

Assign source IDs: `SRC-001`, `SRC-002`, etc.

If L1-Level mode is selected, map all available L2s under the L1 before drafting detailed procedures. If an L2 is known but source detail is incomplete, include the L2 in the inventory and log the missing documentation in Appendix C.

### Step 2 — Select Output Mode

State the selected output mode and briefly explain why.

### Step 3 — Build Canonical Markdown

Follow the canonical template section order. Produce completed Markdown, not a variable catalog or shell template.

Use placeholders only where information is actually unknown:

- `TBD — confirm with process owner`
- `Not documented in source materials`
- `Pending SME validation`

### Step 4 — Draft Current-State Process Documentation

Populate:

- Process Overview
- Process Purpose
- Process Boundaries
- L2 Process Area Inventory, if L1-Level mode
- Sub-Process Inventory
- Process Flow Summary

Use functional role names where possible.

For L2-Level mode:

- Describe the selected L2 process area.
- Use the Sub-Process Inventory to list L3 sub-processes / procedures within that L2.
- Use the Process Flow Summary to show sequencing across the L3s within that L2.

For L1-Level mode:

- Describe the full L1 business cycle.
- Add an L2 Process Area Inventory showing each L2 included in the document.
- For each L2, include its purpose, owner, key systems, major outputs, and documentation status where supported.
- Then list L3 sub-processes / procedures under the appropriate L2.
- Use the Process Flow Summary to show how L2s connect across the overall L1 cycle.

### Step 5 — Draft Detailed Procedures

For each procedure or L3 sub-process, use:

- Procedure Header
- A. Process Overview
- B. Summary Card
- C. Pre-Requisites
- D. Data Inputs
- E. Step-by-Step Desktop Procedure
- Exceptions / Escalations
- Evidence Retention Requirements
- F. Key Controls
- G. Outputs / Deliverables
- H. Known Issues & Pain Points
- Procedure Callouts, if useful

For L2-Level mode:

- Draft each L3 sub-process / procedure directly under Detailed Procedures.

For L1-Level mode:

- Group detailed procedures by L2 process area.
- Use L2 headings before the related L3 sub-processes / procedures.
- Repeat the standard procedure structure for each L3 / procedure under the applicable L2.

Use this step pattern when supported:

```markdown
#### Step X: [Action Title]

[Concise procedural instruction.]

- **System / Tool:** [System or TBD]
- **Navigation Path:** [Path or [[GAP — NOT DOCUMENTED]]]
- **Fields / Parameters:** [Fields or [[GAP — NOT DOCUMENTED]]]
- **Expected Result:** [Expected result]
- **Evidence Required:** [Evidence or [[GAP — EVIDENCE RETENTION UNKNOWN]]]
```

### Step 6 — Controls, Outputs, and Dependencies

Capture only supported controls. If a control appears implied but not evidenced, use placeholder control IDs such as `CTRL-TBD-01` and log the validation need.

For L1-Level mode, aggregate controls, outputs, and dependencies across all included L2s while preserving L2-specific references.

### Step 7 — Pain Points and Improvement Opportunities

Pain points go in:

- Procedure-level H. Known Issues & Pain Points
- Appendix A | Risks & Pain Points Log

Improvement opportunities go in:

- Appendix B | Process Improvement Opportunities

Do not blend future-state recommendations into current-state execution steps.

For L1-Level mode, aggregate pain points and improvement opportunities across all included L2s while preserving the source procedure or L2 reference.

### Step 8 — Screenshot Placeholders

Do not insert screenshots.

Use screenshot IDs: `SC-01`, `SC-02`, etc.

In the procedure body, insert:

```markdown
> **SCREENSHOT PLACEHOLDER — SC-01:** [Caption]. User to insert screenshot showing [specific screen/report/action].
```

Populate Appendix D with status `Pending user input`.

Only request screenshots that reduce execution risk, clarify navigation, evidence a control, or document a key system output.

### Step 9 — Gap / Validation Log

Every material uncertainty must appear in Appendix C using `GAP-01`, `GAP-02`, etc.

For L1-Level mode, include gaps for any known L2s that are in scope but lack enough detail to draft procedure-level documentation.

### Step 10 — Cross-Reference Matrix

For L2-Level mode, populate each procedure row with linked controls, pain points, gaps, screenshots/evidence, and outputs.

For L1-Level mode:

- Add an L2 Process Area column.
- Populate each row at the procedure level, grouped or sortable by L2.
- Link each procedure row to its controls, pain points, gaps, screenshots/evidence, and outputs.
- If an L2 is included in scope but lacks procedure detail, include a row identifying the L2 and log the missing detail in Appendix C.

## Style

Use professional consulting language, current-state wording, functional roles, active voice, concise steps, and neutral descriptions.

Avoid unsupported assumptions, blame language, excessive caveats, and named individuals in process steps unless required.

## Final Response

Return:

1. Drafting note with scope level, output mode, assumptions, major gaps, and screenshot placeholder count.
2. Complete SOP Markdown deliverable.

If creating a file, save as `[process-name]_sop_draft_[version].md`, using the Version / File Naming Standard above.

## Quality Checklist

Before finalizing, verify:

- Scope level is stated as L1-Level or L2-Level.
- Scope selection rationale is stated.
- Canonical section order is preserved.
- Source Materials table is populated.
- For L1-Level mode, L2 Process Area Inventory is populated.
- For L1-Level mode, Detailed Procedures are grouped by L2.
- For L1-Level mode, Cross-Reference Matrix includes an L2 Process Area column.
- Each procedure has A–H sections where applicable.
- Procedure steps do not invent unsupported facts.
- Body gap tags are reflected in Appendix C.
- Pain points are reflected in Appendix A.
- Improvement items are reflected in Appendix B.
- Screenshot placeholders are reflected in Appendix D.
- Cross-Reference Matrix is populated.
- No screenshots are inserted.
- File name includes the SOP version when a file is created.
- Output is ready for downstream Markdown-to-docx conversion.
