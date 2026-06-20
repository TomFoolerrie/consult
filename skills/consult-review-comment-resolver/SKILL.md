---
name: consult-review-comment-resolver
description: Triage SOP reviewer comments, propose edits, create a response log, and flag items requiring SME validation.
---

# Review Comment Resolver Skill

## Purpose

Triage and resolve reviewer comments on SOP / desktop procedure deliverables without silently merging changes or masking unresolved validation items.

## Use This Skill When

Use this skill when the user provides:

- A `.docx` with reviewer comments
- Extracted Word comments
- A reviewer comment log
- A revised SOP draft plus reviewer feedback

## Operating Rules

- Do not silently accept reviewer edits.
- Preserve a response-to-comments trail.
- Distinguish factual corrections from preferences.
- Flag items requiring SME validation.
- Do not invent missing evidence to satisfy a comment.
- If a comment changes the procedure materially, recommend evidence audit follow-up.

## Comment Categories

Classify each comment as one of:

- `FACTUAL CORRECTION`
- `CLARIFICATION`
- `STRUCTURE / FORMATTING`
- `EVIDENCE REQUEST`
- `CONTROL / COMPLIANCE`
- `SCOPE QUESTION`
- `SME VALIDATION REQUIRED`
- `CLIENT PREFERENCE`
- `DUPLICATE / NO ACTION`

## Workflow

1. Extract or summarize each comment.
2. Assign a comment ID: `RC-001`, `RC-002`, etc.
3. Classify the comment.
4. Determine whether the comment can be resolved from available source material.
5. Propose the exact document edit.
6. Identify validation items.
7. Produce a response-to-comments log.

## Output Format

```markdown
# SOP Reviewer Comment Resolution Log — [Process Name]

## Summary

- Comments Reviewed: [count]
- Proposed Edits: [count]
- SME Validation Required: [count]
- Evidence Follow-Up Required: [count]

## Response-to-Comments Table

| Comment ID | Location | Reviewer Comment | Category | Proposed Resolution | Source / Evidence Basis | SME Validation Needed? | Status |
|---|---|---|---|---|---|---|---|
| RC-001 | Section / Step | ... | CLARIFICATION | ... | SRC-001 | No | Proposed |
```

## Revised Text Blocks

For each material edit, provide replacement-ready Markdown:

```markdown
### Replace Section / Step [X] with:

[Revised text]
```

## Status Values

Use:

- `Proposed`
- `Accepted for Update`
- `Needs SME Validation`
- `Needs Evidence`
- `Deferred`
- `No Action`
