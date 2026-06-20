---
template_name: "{{template.name}}"
template_version: "{{template.version}}"
client_name: "{{client.name}}"
project_name: "{{project.name}}"
document_title: "{{document.title}}"
document_subtitle: "{{document.subtitle}}"
prepared_by: "{{document.prepared_by}}"
document_owner: "{{document.owner}}"
classification: "{{document.classification}}"
date: "{{document.date}}"

brand:
  font_family: "{{brand.font_family}}"
  color_primary: "{{brand.color.primary}}"
  color_secondary: "{{brand.color.secondary}}"
  color_tertiary: "{{brand.color.tertiary}}"
  color_accent: "{{brand.color.accent}}"
  color_warning: "{{brand.color.warning}}"
  color_success: "{{brand.color.success}}"
  color_neutral_dark: "{{brand.color.neutral_dark}}"
  color_neutral_light: "{{brand.color.neutral_light}}"

headings:
  h1_style: "{{heading.h1.style}}"
  h2_style: "{{heading.h2.style}}"
  h3_style: "{{heading.h3.style}}"
  h4_style: "{{heading.h4.style}}"
---

<!--
TEMPLATE NOTES
- Replace all {{variables}} before finalization.
- Use functional role names in the body.
- Individual names should appear only in the Roles & Responsibilities section unless client policy requires otherwise.
- Use callout blocks consistently:
  - VALIDATION REQUIRED
  - PAIN POINT
  - FUTURE-STATE OPPORTUNITY
  - CONTROL POINT
  - WARNING
  - DECISION REQUIRED
  - EVIDENCE REQUIRED
-->

# <span style="color: {{brand.color.primary}};">{{document.title}}</span>

_<span style="color: {{brand.color.secondary}};">{{document.subtitle}}</span>_

---

## <span style="color: {{brand.color.primary}};">Document Profile</span>

| Field | Value |
|---|---|
| **Client** | {{client.name}} |
| **Project / Workstream** | {{project.name}} |
| **L1 Business Cycle** | {{process.l1_business_cycle}} |
| **L2 Process Area** | {{process.l2_process_area}} |
| **Document Type** | {{document.type}} |
| **Version** | {{document.version}} |
| **Date** | {{document.date}} |
| **Prepared By** | {{document.prepared_by}} |
| **Document Owner** | {{document.owner}} |
| **Classification** | {{document.classification}} |
| **Status** | {{document.status}} |

---

# <span style="color: {{brand.color.primary}};">How to Use This Document</span>

This document provides {{document.purpose_summary}}.

It is designed for the following audiences:

- **Process preparers** who execute the procedure.
- **Reviewers and approvers** who validate completion and evidence.
- **Process owners** who maintain accountability for the process.
- **Leadership / sponsors** who need visibility into risks, dependencies, and improvement opportunities.
- **Auditors / compliance stakeholders** who require traceable evidence and control references.

Each detailed procedure follows the standard structure below:

| Block | Section | Purpose |
|---|---|---|
| A | Process Overview | Defines what the procedure accomplishes, what it excludes, and where it fits in the process. |
| B | Summary Card | Provides trigger, cadence, ownership, systems, and governing documents. |
| C | Pre-Requisites | Lists what must be true before the procedure begins. |
| D | Data Inputs | Lists reports, files, system extracts, approvals, and confirmations consumed by the procedure. |
| E | Step-by-Step Desktop Procedure | Provides numbered execution steps, system navigation, field-level instructions, warnings, and evidence requirements. |
| F | Key Controls | Identifies embedded controls and review points. |
| G | Outputs / Deliverables | Defines what the procedure produces and where outputs flow downstream. |
| H | Known Issues & Pain Points | Captures confirmed current-state friction, risks, and limitations. |

---

# <span style="color: {{brand.color.primary}};">Table of Contents</span>

- [Document Control](#document-control)
- [Source Materials](#source-materials)
- [Process Taxonomy & Numbering Convention](#process-taxonomy--numbering-convention)
- [Current-State Process Documentation](#current-state-process-documentation)
  - [Process Overview](#process-overview)
  - [Process Flow Summary](#process-flow-summary)
  - [Detailed Procedures](#detailed-procedures)
  - [Roles & Responsibilities](#roles--responsibilities)
  - [Systems & Data Inputs](#systems--data-inputs)
  - [Key Dependencies](#key-dependencies)
- [Appendix A | Risks & Pain Points Log](#appendix-a--risks--pain-points-log)
- [Appendix B | Process Improvement Opportunities](#appendix-b--process-improvement-opportunities)
- [Appendix C | Gap / Validation Log](#appendix-c--gap--validation-log)
- [Appendix D | Screenshot / Evidence Index](#appendix-d--screenshot--evidence-index)
- [Appendix E | Glossary & Reference](#appendix-e--glossary--reference)

---

# <span style="color: {{brand.color.primary}};">Document Control</span>

This document is a living document. The process owner is responsible for keeping it current as systems, roles, controls, and business requirements evolve.

Review frequency: **{{document.review_frequency}}**

| Version | Date | Author | Reviewer | Summary of Changes | Status |
|---|---:|---|---|---|---|
| {{version.1.number}} | {{version.1.date}} | {{version.1.author}} | {{version.1.reviewer}} | {{version.1.summary}} | {{version.1.status}} |
| {{version.2.number}} | {{version.2.date}} | {{version.2.author}} | {{version.2.reviewer}} | {{version.2.summary}} | {{version.2.status}} |

---

# <span style="color: {{brand.color.primary}};">Source Materials</span>

| Source ID | Source Material | Date | Owner / Provider | Used For | Location |
|---|---|---:|---|---|---|
| SRC-001 | {{source.1.name}} | {{source.1.date}} | {{source.1.owner}} | {{source.1.used_for}} | {{source.1.location}} |
| SRC-002 | {{source.2.name}} | {{source.2.date}} | {{source.2.owner}} | {{source.2.used_for}} | {{source.2.location}} |
| SRC-003 | {{source.3.name}} | {{source.3.date}} | {{source.3.owner}} | {{source.3.used_for}} | {{source.3.location}} |

---

# <span style="color: {{brand.color.primary}};">Process Taxonomy & Numbering Convention</span>

| Level / ID Type | Definition | Template Convention | Client-Specific Example |
|---|---|---|---|
| L1 Business Cycle | Highest-level business cycle | {{taxonomy.l1_format}} | {{taxonomy.l1_example}} |
| L2 Process Area | Major process grouping | {{taxonomy.l2_format}} | {{taxonomy.l2_example}} |
| L3 Sub-Process | Specific recurring activity | {{taxonomy.l3_format}} | {{taxonomy.l3_example}} |
| Procedure ID | Unique procedure reference | {{taxonomy.procedure_id_format}} | {{taxonomy.procedure_id_example}} |
| Control ID | Unique control reference | {{taxonomy.control_id_format}} | {{taxonomy.control_id_example}} |
| Pain Point ID | Current-state issue reference | PP-### | PP-001 |
| Opportunity ID | Future-state opportunity reference | OI-### | OI-001 |
| Gap ID | Validation / open item reference | GAP-## | GAP-01 |
| Screenshot / Evidence ID | Screenshot or evidence reference | SC-## | SC-01 |

---

# <span style="color: {{brand.color.primary}};">Current-State Process Documentation</span>

## <span style="color: {{brand.color.secondary}};">Process Overview</span>

{{process.overview_narrative}}

### Process Purpose

{{process.purpose}}

### Process Boundaries

| Boundary Element | Description |
|---|---|
| **Start Event** | {{process.start_event}} |
| **End Event** | {{process.end_event}} |
| **In Scope** | {{process.in_scope}} |
| **Out of Scope** | {{process.out_of_scope}} |
| **Primary Business Owner** | {{process.primary_owner}} |
| **Primary Systems** | {{process.primary_systems}} |
| **Primary Outputs** | {{process.primary_outputs}} |

---

## <span style="color: {{brand.color.secondary}};">Sub-Process Inventory</span>

| Ref | Sub-Process | Direction / Type | Frequency | Primary Owner | Procedure Status |
|---|---|---|---|---|---|
| {{procedure.1.ref}} | {{procedure.1.name}} | {{procedure.1.direction}} | {{procedure.1.frequency}} | {{procedure.1.owner}} | {{procedure.1.status}} |
| {{procedure.2.ref}} | {{procedure.2.name}} | {{procedure.2.direction}} | {{procedure.2.frequency}} | {{procedure.2.owner}} | {{procedure.2.status}} |
| {{procedure.3.ref}} | {{procedure.3.name}} | {{procedure.3.direction}} | {{procedure.3.frequency}} | {{procedure.3.owner}} | {{procedure.3.status}} |

---

## <span style="color: {{brand.color.secondary}};">Process Flow Summary</span>

| When | What Happens | Who | Inputs | Outputs | Ref |
|---|---|---|---|---|---|
| {{flow.1.when}} | {{flow.1.what}} | {{flow.1.who}} | {{flow.1.inputs}} | {{flow.1.outputs}} | {{flow.1.ref}} |
| {{flow.2.when}} | {{flow.2.what}} | {{flow.2.who}} | {{flow.2.inputs}} | {{flow.2.outputs}} | {{flow.2.ref}} |
| {{flow.3.when}} | {{flow.3.what}} | {{flow.3.who}} | {{flow.3.inputs}} | {{flow.3.outputs}} | {{flow.3.ref}} |

---

# <span style="color: {{brand.color.primary}};">Detailed Procedures</span>

<!--
COPY THE PROCEDURE MODULE BELOW FOR EACH L3 SUB-PROCESS.
-->

---

## <span style="color: {{brand.color.secondary}};">{{procedure.ref}} | {{procedure.name}}</span>

### <span style="color: {{brand.color.tertiary}};">Procedure Header</span>

| Field | Value |
|---|---|
| **Procedure ID** | {{procedure.id}} |
| **Procedure Name** | {{procedure.name}} |
| **L1 Business Cycle** | {{process.l1_business_cycle}} |
| **L2 Process Area** | {{process.l2_process_area}} |
| **L3 Sub-Process** | {{procedure.l3_subprocess}} |
| **Legacy / Crosswalk ID** | {{procedure.legacy_id}} |
| **Procedure Type** | {{procedure.type}} |
| **Status** | {{procedure.status}} |
| **Last Updated** | {{procedure.last_updated}} |
| **SME Validated By** | {{procedure.sme_validated_by}} |

---

### <span style="color: {{brand.color.tertiary}};">A. Process Overview</span>

{{procedure.process_overview}}

#### Purpose

{{procedure.purpose}}

#### Scope

| Scope Element | Description |
|---|---|
| **In Scope** | {{procedure.in_scope}} |
| **Out of Scope** | {{procedure.out_of_scope}} |
| **Start Event** | {{procedure.start_event}} |
| **End Event** | {{procedure.end_event}} |

---

### <span style="color: {{brand.color.tertiary}};">B. Summary Card</span>

| Field | Value |
|---|---|
| **Trigger** | {{procedure.trigger}} |
| **Cadence / Frequency** | {{procedure.frequency}} |
| **Business Owner** | {{procedure.business_owner}} |
| **Preparer** | {{procedure.preparer}} |
| **Reviewer** | {{procedure.reviewer}} |
| **Approver** | {{procedure.approver}} |
| **Primary Systems** | {{procedure.primary_systems}} |
| **Source Inputs** | {{procedure.source_inputs}} |
| **Governing Documents** | {{procedure.governing_documents}} |
| **Key Outputs** | {{procedure.key_outputs}} |
| **Downstream Process / Recipient** | {{procedure.downstream_process}} |
| **Control References** | {{procedure.control_refs}} |
| **Risk / Gap References** | {{procedure.risk_gap_refs}} |

---

### <span style="color: {{brand.color.tertiary}};">C. Pre-Requisites</span>

Before beginning this procedure, confirm the following:

| # | Pre-Requisite | Owner | Evidence / Confirmation | Status |
|---:|---|---|---|---|
| 1 | {{prereq.1.description}} | {{prereq.1.owner}} | {{prereq.1.evidence}} | {{prereq.1.status}} |
| 2 | {{prereq.2.description}} | {{prereq.2.owner}} | {{prereq.2.evidence}} | {{prereq.2.status}} |
| 3 | {{prereq.3.description}} | {{prereq.3.owner}} | {{prereq.3.evidence}} | {{prereq.3.status}} |

---

### <span style="color: {{brand.color.tertiary}};">D. Data Inputs</span>

| Input ID | Data Input | Source System / Location | Owner | Required Format | Notes |
|---|---|---|---|---|---|
| IN-001 | {{input.1.name}} | {{input.1.source}} | {{input.1.owner}} | {{input.1.format}} | {{input.1.notes}} |
| IN-002 | {{input.2.name}} | {{input.2.source}} | {{input.2.owner}} | {{input.2.format}} | {{input.2.notes}} |
| IN-003 | {{input.3.name}} | {{input.3.source}} | {{input.3.owner}} | {{input.3.format}} | {{input.3.notes}} |

---

### <span style="color: {{brand.color.tertiary}};">E. Step-by-Step Desktop Procedure</span>

#### Step 1: {{step.1.title}}

{{step.1.description}}

- **System / Tool:** {{step.1.system}}
- **Navigation Path:** {{step.1.navigation_path}}
- **Fields / Parameters:** {{step.1.fields}}
- **Expected Result:** {{step.1.expected_result}}
- **Evidence Required:** {{step.1.evidence_required}}

> <span style="color: {{brand.color.warning}};">**WARNING:** {{step.1.warning}}</span>

#### Step 2: {{step.2.title}}

{{step.2.description}}

- **System / Tool:** {{step.2.system}}
- **Navigation Path:** {{step.2.navigation_path}}
- **Fields / Parameters:** {{step.2.fields}}
- **Expected Result:** {{step.2.expected_result}}
- **Evidence Required:** {{step.2.evidence_required}}

#### Step 3: {{step.3.title}}

{{step.3.description}}

- **System / Tool:** {{step.3.system}}
- **Navigation Path:** {{step.3.navigation_path}}
- **Fields / Parameters:** {{step.3.fields}}
- **Expected Result:** {{step.3.expected_result}}
- **Evidence Required:** {{step.3.evidence_required}}

---

#### Exceptions / Escalations

| Exception ID | Exception Scenario | Required Action | Escalation Owner | SLA / Timing |
|---|---|---|---|---|
| EX-001 | {{exception.1.scenario}} | {{exception.1.action}} | {{exception.1.owner}} | {{exception.1.sla}} |
| EX-002 | {{exception.2.scenario}} | {{exception.2.action}} | {{exception.2.owner}} | {{exception.2.sla}} |

---

#### Evidence Retention Requirements

| Evidence Type | Description | Required? | Archive Location | Retention Owner |
|---|---|---|---|---|
| Source Document | {{evidence.source_document}} | {{evidence.source_required}} | {{evidence.source_location}} | {{evidence.source_owner}} |
| System Screenshot | {{evidence.screenshot}} | {{evidence.screenshot_required}} | {{evidence.screenshot_location}} | {{evidence.screenshot_owner}} |
| Approval Evidence | {{evidence.approval}} | {{evidence.approval_required}} | {{evidence.approval_location}} | {{evidence.approval_owner}} |
| Transaction Reference | {{evidence.transaction_ref}} | {{evidence.transaction_required}} | {{evidence.transaction_location}} | {{evidence.transaction_owner}} |
| Final Output | {{evidence.final_output}} | {{evidence.final_output_required}} | {{evidence.final_output_location}} | {{evidence.final_output_owner}} |

---

### <span style="color: {{brand.color.tertiary}};">F. Key Controls</span>

| Control ID | Control Objective | Control Activity | Control Type | Nature | Frequency | Preparer | Reviewer | Evidence | Related Risk ID |
|---|---|---|---|---|---|---|---|---|---|
| {{control.1.id}} | {{control.1.objective}} | {{control.1.activity}} | {{control.1.type}} | {{control.1.nature}} | {{control.1.frequency}} | {{control.1.preparer}} | {{control.1.reviewer}} | {{control.1.evidence}} | {{control.1.related_risk}} |
| {{control.2.id}} | {{control.2.objective}} | {{control.2.activity}} | {{control.2.type}} | {{control.2.nature}} | {{control.2.frequency}} | {{control.2.preparer}} | {{control.2.reviewer}} | {{control.2.evidence}} | {{control.2.related_risk}} |

---

### <span style="color: {{brand.color.tertiary}};">G. Outputs / Deliverables</span>

| Output ID | Output / Deliverable | Description | Downstream Recipient | System of Record | Archive Location |
|---|---|---|---|---|---|
| OUT-001 | {{output.1.name}} | {{output.1.description}} | {{output.1.recipient}} | {{output.1.system_of_record}} | {{output.1.archive_location}} |
| OUT-002 | {{output.2.name}} | {{output.2.description}} | {{output.2.recipient}} | {{output.2.system_of_record}} | {{output.2.archive_location}} |

---

### <span style="color: {{brand.color.tertiary}};">H. Known Issues & Pain Points</span>

| Pain Point ID | Known Issue / Pain Point | Impact | Priority | Owner | Recommendation |
|---|---|---|---|---|---|
| {{painpoint.1.id}} | {{painpoint.1.issue}} | {{painpoint.1.impact}} | {{painpoint.1.priority}} | {{painpoint.1.owner}} | {{painpoint.1.recommendation}} |
| {{painpoint.2.id}} | {{painpoint.2.issue}} | {{painpoint.2.impact}} | {{painpoint.2.priority}} | {{painpoint.2.owner}} | {{painpoint.2.recommendation}} |

---

### <span style="color: {{brand.color.tertiary}};">Procedure Callouts</span>

> <span style="color: {{brand.color.warning}};">**PAIN POINT:** {{callout.pain_point}}</span>

> <span style="color: {{brand.color.accent}};">**VALIDATION REQUIRED:** {{callout.validation_required}}</span>

> <span style="color: {{brand.color.success}};">**FUTURE-STATE OPPORTUNITY:** {{callout.future_state}}</span>

> <span style="color: {{brand.color.primary}};">**CONTROL POINT:** {{callout.control_point}}</span>

> <span style="color: {{brand.color.warning}};">**DECISION REQUIRED:** {{callout.decision_required}}</span>

---

# <span style="color: {{brand.color.primary}};">Roles & Responsibilities</span>

## <span style="color: {{brand.color.secondary}};">Role Dictionary</span>

| Role ID | Functional Role | Description | Standard Responsibilities |
|---|---|---|---|
| ROLE-001 | {{role.1.functional_role}} | {{role.1.description}} | {{role.1.standard_responsibilities}} |
| ROLE-002 | {{role.2.functional_role}} | {{role.2.description}} | {{role.2.standard_responsibilities}} |
| ROLE-003 | {{role.3.functional_role}} | {{role.3.description}} | {{role.3.standard_responsibilities}} |

## <span style="color: {{brand.color.secondary}};">Client Role Mapping</span>

| Functional Role | Name | Reports To | Key Responsibilities | Related Procedures |
|---|---|---|---|---|
| {{client_role.1.functional_role}} | {{client_role.1.name}} | {{client_role.1.reports_to}} | {{client_role.1.responsibilities}} | {{client_role.1.related_procedures}} |
| {{client_role.2.functional_role}} | {{client_role.2.name}} | {{client_role.2.reports_to}} | {{client_role.2.responsibilities}} | {{client_role.2.related_procedures}} |
| {{client_role.3.functional_role}} | {{client_role.3.name}} | {{client_role.3.reports_to}} | {{client_role.3.responsibilities}} | {{client_role.3.related_procedures}} |

---

## <span style="color: {{brand.color.secondary}};">RACI Matrix</span>

| Activity | Ref | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|---|
| {{raci.1.activity}} | {{raci.1.ref}} | {{raci.1.responsible}} | {{raci.1.accountable}} | {{raci.1.consulted}} | {{raci.1.informed}} |
| {{raci.2.activity}} | {{raci.2.ref}} | {{raci.2.responsible}} | {{raci.2.accountable}} | {{raci.2.consulted}} | {{raci.2.informed}} |
| {{raci.3.activity}} | {{raci.3.ref}} | {{raci.3.responsible}} | {{raci.3.accountable}} | {{raci.3.consulted}} | {{raci.3.informed}} |

---

## <span style="color: {{brand.color.secondary}};">Segregation of Duties Note</span>

{{sod.note}}

---

# <span style="color: {{brand.color.primary}};">Systems & Data Inputs</span>

| System / Tool | Role in Process | Related Procedures | Key Inputs / Outputs | Known Limitations | Owner |
|---|---|---|---|---|---|
| {{system.1.name}} | {{system.1.role}} | {{system.1.related_procedures}} | {{system.1.inputs_outputs}} | {{system.1.limitations}} | {{system.1.owner}} |
| {{system.2.name}} | {{system.2.role}} | {{system.2.related_procedures}} | {{system.2.inputs_outputs}} | {{system.2.limitations}} | {{system.2.owner}} |
| {{system.3.name}} | {{system.3.role}} | {{system.3.related_procedures}} | {{system.3.inputs_outputs}} | {{system.3.limitations}} | {{system.3.owner}} |

---

# <span style="color: {{brand.color.primary}};">Key Dependencies</span>

| Upstream Dependency | Feeds Into | Dependency Owner | Risk if Delayed / Incomplete | Mitigation |
|---|---|---|---|---|
| {{dependency.upstream.1.name}} | {{dependency.upstream.1.feeds_into}} | {{dependency.upstream.1.owner}} | {{dependency.upstream.1.risk}} | {{dependency.upstream.1.mitigation}} |
| {{dependency.upstream.2.name}} | {{dependency.upstream.2.feeds_into}} | {{dependency.upstream.2.owner}} | {{dependency.upstream.2.risk}} | {{dependency.upstream.2.mitigation}} |

| Downstream Dependency | Fed By | Dependency Owner | Required Timing | Notes |
|---|---|---|---|---|
| {{dependency.downstream.1.name}} | {{dependency.downstream.1.fed_by}} | {{dependency.downstream.1.owner}} | {{dependency.downstream.1.timing}} | {{dependency.downstream.1.notes}} |
| {{dependency.downstream.2.name}} | {{dependency.downstream.2.fed_by}} | {{dependency.downstream.2.owner}} | {{dependency.downstream.2.timing}} | {{dependency.downstream.2.notes}} |

---

# <span style="color: {{brand.color.primary}};">Cross-Reference Matrix</span>

| Procedure Ref | Procedure Name | Controls | Risks / Pain Points | Gaps | Screenshots / Evidence | Outputs |
|---|---|---|---|---|---|---|
| {{xref.1.ref}} | {{xref.1.name}} | {{xref.1.controls}} | {{xref.1.risks}} | {{xref.1.gaps}} | {{xref.1.screenshots}} | {{xref.1.outputs}} |
| {{xref.2.ref}} | {{xref.2.name}} | {{xref.2.controls}} | {{xref.2.risks}} | {{xref.2.gaps}} | {{xref.2.screenshots}} | {{xref.2.outputs}} |

---

# <span style="color: {{brand.color.primary}};">Appendix A | Risks & Pain Points Log</span>

| PP ID | Observation | Source Procedure | Impact | Priority | Owner | Recommendation | Status |
|---|---|---|---|---|---|---|---|
| PP-001 | {{pp.1.observation}} | {{pp.1.source}} | {{pp.1.impact}} | {{pp.1.priority}} | {{pp.1.owner}} | {{pp.1.recommendation}} | {{pp.1.status}} |
| PP-002 | {{pp.2.observation}} | {{pp.2.source}} | {{pp.2.impact}} | {{pp.2.priority}} | {{pp.2.owner}} | {{pp.2.recommendation}} | {{pp.2.status}} |

---

# <span style="color: {{brand.color.primary}};">Appendix B | Process Improvement Opportunities</span>

| OI ID | Observation | Root Cause | Recommended Action | Expected Impact | Priority | Owner | Status |
|---|---|---|---|---|---|---|---|
| OI-001 | {{oi.1.observation}} | {{oi.1.root_cause}} | {{oi.1.recommended_action}} | {{oi.1.expected_impact}} | {{oi.1.priority}} | {{oi.1.owner}} | {{oi.1.status}} |
| OI-002 | {{oi.2.observation}} | {{oi.2.root_cause}} | {{oi.2.recommended_action}} | {{oi.2.expected_impact}} | {{oi.2.priority}} | {{oi.2.owner}} | {{oi.2.status}} |

---

# <span style="color: {{brand.color.primary}};">Appendix C | Gap / Validation Log</span>

| Gap ID | Type | Location | Description | Owner | Priority | Due Date | Resolution / Decision | Status |
|---|---|---|---|---|---|---|---|---|
| GAP-01 | {{gap.1.type}} | {{gap.1.location}} | {{gap.1.description}} | {{gap.1.owner}} | {{gap.1.priority}} | {{gap.1.due_date}} | {{gap.1.resolution}} | {{gap.1.status}} |
| GAP-02 | {{gap.2.type}} | {{gap.2.location}} | {{gap.2.description}} | {{gap.2.owner}} | {{gap.2.priority}} | {{gap.2.due_date}} | {{gap.2.resolution}} | {{gap.2.status}} |

---

# <span style="color: {{brand.color.primary}};">Appendix D | Screenshot / Evidence Index</span>

| SC ID | Caption | Procedure / Step | Source | Why Needed | Status | Owner | Archive Location |
|---|---|---|---|---|---|---|---|
| SC-01 | {{screenshot.1.caption}} | {{screenshot.1.procedure_step}} | {{screenshot.1.source}} | {{screenshot.1.why_needed}} | {{screenshot.1.status}} | {{screenshot.1.owner}} | {{screenshot.1.archive_location}} |
| SC-02 | {{screenshot.2.caption}} | {{screenshot.2.procedure_step}} | {{screenshot.2.source}} | {{screenshot.2.why_needed}} | {{screenshot.2.status}} | {{screenshot.2.owner}} | {{screenshot.2.archive_location}} |

---

# <span style="color: {{brand.color.primary}};">Appendix E | Glossary & Reference</span>

| Term | Definition | Related Procedure / Section |
|---|---|---|
| {{glossary.1.term}} | {{glossary.1.definition}} | {{glossary.1.related_section}} |
| {{glossary.2.term}} | {{glossary.2.definition}} | {{glossary.2.related_section}} |
| {{glossary.3.term}} | {{glossary.3.definition}} | {{glossary.3.related_section}} |

---

# <span style="color: {{brand.color.primary}};">Appendix F | Template Variable Catalog</span>

Use the following variables to configure the template.

## Brand Variables

- `{{brand.font_family}}`
- `{{brand.color.primary}}`
- `{{brand.color.secondary}}`
- `{{brand.color.tertiary}}`
- `{{brand.color.accent}}`
- `{{brand.color.warning}}`
- `{{brand.color.success}}`
- `{{brand.color.neutral_dark}}`
- `{{brand.color.neutral_light}}`

## Document Variables

- `{{document.title}}`
- `{{document.subtitle}}`
- `{{document.type}}`
- `{{document.version}}`
- `{{document.date}}`
- `{{document.prepared_by}}`
- `{{document.owner}}`
- `{{document.classification}}`
- `{{document.status}}`
- `{{document.review_frequency}}`

## Client / Project Variables

- `{{client.name}}`
- `{{project.name}}`
- `{{process.l1_business_cycle}}`
- `{{process.l2_process_area}}`
- `{{process.primary_owner}}`
- `{{process.primary_systems}}`
- `{{process.primary_outputs}}`

## Procedure Variables

- `{{procedure.id}}`
- `{{procedure.ref}}`
- `{{procedure.name}}`
- `{{procedure.type}}`
- `{{procedure.status}}`
- `{{procedure.trigger}}`
- `{{procedure.frequency}}`
- `{{procedure.business_owner}}`
- `{{procedure.preparer}}`
- `{{procedure.reviewer}}`
- `{{procedure.approver}}`
- `{{procedure.primary_systems}}`
- `{{procedure.governing_documents}}`
- `{{procedure.control_refs}}`
- `{{procedure.risk_gap_refs}}`

## Control Variables

- `{{control.#.id}}`
- `{{control.#.objective}}`
- `{{control.#.activity}}`
- `{{control.#.type}}`
- `{{control.#.nature}}`
- `{{control.#.frequency}}`
- `{{control.#.preparer}}`
- `{{control.#.reviewer}}`
- `{{control.#.evidence}}`
- `{{control.#.related_risk}}`

## Log Variables

- `{{pp.#.*}}` for pain points
- `{{oi.#.*}}` for opportunities
- `{{gap.#.*}}` for validation items
- `{{screenshot.#.*}}` for screenshot / evidence index items
- `{{glossary.#.*}}` for glossary terms