---
name: consult-evidence-auditor
description: Audit drafted SOPs against source materials to identify unsupported claims, weak evidence, contradictions, and validation gaps.
---

# Evidence Auditor Skill

## Purpose

Review a drafted SOP against source materials and determine whether key procedural statements are supported, weakly supported, inferred, contradicted, or unsupported.

## Use This Skill When

Use this skill when the user provides:

- A drafted SOP or desktop procedure
- Source Markdown files, notes, transcripts, control narratives, or prior SOPs
- A request to audit support, validate evidence, identify gaps, or QC a draft

Do not rewrite the full SOP unless asked. Focus on evidence and validation quality.

## Audit Standard

Apply balanced evidence discipline:

- Obvious connective tissue is acceptable.
- Procedural facts require support.
- Unsupported procedural claims must be flagged.
- Contradictions must be escalated.

## Procedure

1. Identify source files and assign or use source IDs.
2. Break the SOP into auditable units:
   - Process overview claims
   - Procedure steps
   - Roles
   - Systems
   - Inputs / outputs
   - Controls
   - Exceptions
   - Evidence retention requirements
   - Pain points and improvement opportunities
3. Classify each auditable unit.
4. Recommend remediation.

## Evidence Classification

Use these classifications:

- `SUPPORTED` — Directly supported by source.
- `WEAK SUPPORT` — Directionally supported, but detail is incomplete.
- `CONNECTIVE TISSUE` — Acceptable drafting bridge, not a procedural fact.
- `UNSUPPORTED` — No source support located.
- `CONTRADICTED` — Source materials conflict with the SOP.
- `NEEDS SME VALIDATION` — Plausible but requires confirmation.

## Output Format

Return an audit summary followed by a detailed table.

```markdown
# SOP Evidence Audit — [Process Name]

## Audit Summary

- Overall Result: PASS / PASS WITH OPEN ITEMS / FAIL
- Source Files Reviewed: [count/list]
- Unsupported Items: [count]
- Contradicted Items: [count]
- SME Validation Items: [count]
- Recommended Next Step: [summary]

## Evidence Audit Table

| ID | SOP Location | SOP Statement / Step | Classification | Source Support / Quote | Issue | Recommended Action |
|---|---|---|---|---|---|---|
| EA-001 | Section / Step | ... | SUPPORTED | SRC-001: "..." | None | No action |
```

## Pass / Fail Rules

- `PASS`: No unsupported or contradicted material procedural facts.
- `PASS WITH OPEN ITEMS`: Open validation items exist but are clearly tagged and logged.
- `FAIL`: Unsupported or contradicted material procedural facts appear as if final.

## Remediation Guidance

For each issue, recommend one of:

- Add source citation / quote
- Convert to gap tag
- Move to Appendix C
- Rewrite as current-state observation
- Remove unsupported detail
- Request SME validation
- Resolve source conflict
