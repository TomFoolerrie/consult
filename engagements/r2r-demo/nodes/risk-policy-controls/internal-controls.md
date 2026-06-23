---
node: risk-policy-controls.internal-controls
l1: risk-policy-controls
l1_name: Risk, Policy & Controls
l2: internal-controls
l2_name: Internal Controls
coverage: partial
lenses:
  current_state: present
  process: pain_med
  automation: null
  capability: null
  operating_model: null
---

# Risk, Policy & Controls — Internal Controls

## What we learned

The client operates a dual-review control requiring a second-level approver for every reconciliation above $50,000 before the account is closed. This control is asserted to run consistently each close cycle. However, no documentary or system evidence supports this assertion: the control is not written into any policy document, not configured in the reconciliation tool, and is not enforced at the system level. It exists entirely as tribal knowledge held by the controller and team members who have internalized the practice over time.

This creates material control fragility. If key personnel turn over, if reviewers are under close-deadline pressure, or if a new team member is unaware of the undocumented threshold, the control can fail silently with no audit trail or system guardrail to catch the lapse. From an audit and SOX-readiness perspective, a control that cannot be evidenced is treated as a control that does not exist.

Coverage is assessed as **partial**: a control intent is present and reportedly operating, but it is not documented, not system-enforced, and not independently verifiable.

## Evidence digest

All evidence for this node comes from the close walkthrough transcript (verbally attested, not documentary):

- **L31** — Controller states: *"we require a second-level reviewer to approve every reconciliation above fifty thousand dollars before the account is closed. That dual-review control is enforced every single close."*  
  Source: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L31`

- **L33–35** — When asked whether the control is documented in policy or system configuration, the controller confirms it is not: *"Honestly, no. It's how we've always done it but it isn't written into any policy or system config. It lives in people's heads."*  
  Source: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L33-35`

Both evidence items are **verbal attestation only** (`evidence_tier: verbal`). No policy document, workflow configuration, approval log, or system-enforced rule has been produced to corroborate that the dual-review control operates as described.

## Diagnosis (5 lenses)

**Current state: `present`**  
A dual-review control intent is present and verbally attested by the controller as operating each close. The process step exists in practice but is not formalized.

**Process: `pain_med`**  
The team has self-medicated against the risk of under-reviewed reconciliations by establishing an informal second-review norm. This is a workaround — not a designed, documented, or enforced control — and is therefore fragile by nature. Without a written policy or system guardrail, enforcement depends entirely on individual awareness and discipline.

**Automation: `null`**  
No data. The reconciliation tool is mentioned in passing as a potential control-enforcement point, but no evidence was gathered on its configuration or capabilities. This lens is not asserted.

**Capability: `null`**  
No data. Not asserted.

**Operating model: `null`**  
No data. Not asserted.

## Open items

**GAP — `control_not_evidenced` (pending register ID)**  
The dual-review control for reconciliations above $50K is supported by verbal attestation only. It is not documented in any policy, not enforced in the reconciliation tool, and cannot be independently evidenced. A verbally-attested-only control does not satisfy documentation or audit standards and must be treated as unevidenced until formal controls policy and system configuration are produced.

- Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L33-35`
- Evidence tier: `verbal`
- Recommended action: Document the dual-review threshold and approval requirement in a formal controls policy; configure the reconciliation tool to enforce the $50K threshold systematically so the control is system-observed and independently verifiable.
