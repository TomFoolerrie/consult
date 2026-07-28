## Material Disposition Adjustments (Damage, Spoilage, Scrap)

### Scope

This procedure covers the recording, approval, and posting of inventory adjustments for damaged, spoiled, or scrapped material identified outside the cycle count, using the Material Disposition Form. It excludes adjustments arising from cycle count variances, which are counted under [[cycle-count-execution]] and approved and posted under [[count-adjustment-review-and-posting]]. Damage identified during receiving inspection, before putaway, is handled under the Procure to Pay receiving process and is likewise excluded. Bin placement of material after receipt is covered by [[putaway-and-bin-confirmation]].

### At a Glance

| Field | Value |
|---|---|
| Trigger | Discovery of damaged, spoiled, or scrap material in the warehouse |
| Frequency | Event-driven (as dispositions occur) |
| Preparer | The employee who identifies the disposition; posted by the Inventory Control Analyst |
| Reviewer | Area Supervisor; Plant Controller for dispositions over $5,000 book value |
| Systems | NetSuite (posting); paper Material Disposition Form |
| Key inputs | Completed Material Disposition Form; photographs for damage claims |
| Key outputs | Posted inventory adjustment in NetSuite; signed Material Disposition Form |

### Before You Start

- **Material Disposition Form** — blank paper form; available to the employee documenting the disposition.
- **Photographs of the damaged material** — taken at the point of discovery; required as supporting evidence for damage claims.

### Procedure

#### Step 1: Complete the Material Disposition Form

The employee who finds the damaged, spoiled, or scrap material completes the Material Disposition Form, recording the affected material and the nature of the disposition (SRC-001). The form is paper; there is no system-based entry at this stage.

#### Step 2: Attach photographs of the damaged material

- **Condition:** the disposition supports a damage claim

Photographs of the damaged material are attached to the form to support the claim (SRC-001).

- **Evidence Required:** photographs attached to the Material Disposition Form

#### Step 3: Obtain the Area Supervisor's sign-off

The preparer's Area Supervisor reviews and signs the completed form (SRC-001).

#### Step 4: Obtain Plant Controller approval for high-value dispositions

- **Condition:** the book value of the disposition exceeds $5,000

The signed form is routed to the Plant Controller, whose approval is required before the adjustment may be posted (SRC-001).

#### Step 5: Post the adjustment in NetSuite

The approved form is delivered to the Inventory Control Analyst, who posts the inventory adjustment in NetSuite (SRC-001).

> **VALIDATION REQUIRED — GAP-01:** The NetSuite transaction type and navigation path used to post a disposition adjustment, and the expected timing between form approval and posting, are unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

> **VALIDATION REQUIRED — GAP-02:** Where the signed Material Disposition Forms are filed after posting, and for how long they are retained, is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

> **SCREENSHOT PLACEHOLDER — SC-01:** A completed and signed Material Disposition Form (values redacted as needed), validating the form's fields and the supervisor and Plant Controller signature blocks.

> **SCREENSHOT PLACEHOLDER — SC-02:** The posted disposition adjustment in NetSuite, validating the transaction type and the quantity and value adjusted.

### Outputs & Evidence

- **Posted inventory adjustment** — the on-hand quantity and value in NetSuite reflect the disposition.
- **Evidence retained:** the signed Material Disposition Form, carrying the Area Supervisor sign-off and, where applicable, the Plant Controller approval.
- **Not retained:** photographs of damaged material are frequently absent from damage-claim forms, leaving those claims without supporting visual evidence.

### Key Controls

> **CONTROL — CTRL-001:** Every Material Disposition Form is signed by the preparer's Area Supervisor before it is submitted for posting.
> - **Type:** Preventive
> - **Frequency:** each disposition
> - **Owner:** Area Supervisor

> **CONTROL — CTRL-002:** Dispositions over $5,000 book value require Plant Controller approval before the adjustment is posted.
> - **Type:** Preventive
> - **Frequency:** each disposition over $5,000 book value
> - **Owner:** Plant Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Photographs are supposed to be attached to damage-claim forms but usually are not (SRC-001).
> - **Impact:** Damage claims lack supporting visual evidence at the time the adjustment is posted.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** The Material Disposition Form is entirely paper-based, from preparation through sign-off to delivery for posting (SRC-001).
> - **Impact:** Approvals and routing occur outside the system, leaving no system audit trail before the posting itself and making forms and their evidence easy to lose.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Replace the paper Material Disposition Form with an electronic form or workflow that enforces supervisor and Plant Controller approvals and requires photograph attachment for damage claims before the adjustment can be posted.
> - **Addresses:** PP-001, PP-002

```consult-meta
systems: [netsuite]
roles:   [area-supervisor, plant-controller, inventory-control-analyst]
```
