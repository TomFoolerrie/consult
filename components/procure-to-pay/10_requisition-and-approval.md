## Requisition and Approval

<!-- scope note: covers variants — Catalog / punchout requisition; Non-catalog free-text requisition; Services requisition (SOW required). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers how a Requester raises a purchase requisition in Coupa and how
that requisition is routed through the Coupa approval chain to fully approved status.
It runs on demand, whenever a department, plant or function needs goods or services,
and it applies to three requisition paths that share one flow and one approval chain:
catalog and punchout requisitions, non-catalog free-text requisitions, and services
requisitions that require a statement of work. The Requester prepares the requisition;
approval is performed by the Cost Center Owner and, above dollar thresholds, by the
Functional Vice President and the Chief Financial Officer. The supplier must already
be transactable, which is established upstream by [[new-vendor-onboarding]]. This
procedure ends at full approval; cutting and transmitting the purchase order, and any
subsequent change order, are covered by [[po-issuance-and-change-orders]], and
purchases made without a requisition are covered by [[confirming-po]]. (SRC-002,
SRC-005)

### B. Quick Reference

- **Trigger:** A Requester needs goods or services and raises a requisition in Coupa.
- **Frequency:** On demand.
- **Preparer:** Requester.
- **Reviewer:** Cost Center Owner in all cases; Functional Vice President and Chief Financial Officer above the dollar thresholds in F.
- **Primary systems / tools:** Coupa (hosted catalogs, punchout catalogs, non-catalog request form, services request form, approval chains).
- **Key outputs:** A fully approved requisition in Coupa, released for purchase order issuance.

### C. Pre-Requisites

- The supplier exists and is transactable in both Coupa and NetSuite (see [[new-vendor-onboarding]]).
- The Requester has Coupa access and a cost center against which the requisition can be charged.
- For a capital purchase, an approved authorization for expenditure (AFE) number is available to enter on the requisition.
- For a services requisition, a statement of work is available to attach.

### D. Inputs

- **Requirement to purchase:** Requester — the goods or services needed, the quantity, and the cost center to be charged.
- **Hosted and punchout catalog content:** Coupa — supplier-provided catalog items and pricing for maintenance, repair and operations (MRO) items from the industrial distributor and for IT items.
- **Supplier selection:** Requester — for a non-catalog free-text requisition, the supplier chosen from the Coupa supplier list.
- **Statement of work:** Requester — required for a services requisition.
- **AFE number:** Requester — required for a capital requisition.

### E. Step-by-Step Procedure

#### Step 1: Determine the requisition path

The Requester determines which of the three requisition paths applies: a catalog or
punchout requisition where the item is available on a hosted or punchout catalog, a
non-catalog free-text requisition where it is not, or a services requisition where the
purchase is for services. The path determines how the line detail is created in Step 2;
the approval routing in Steps 4 and 5 is the same for all three.

- **System / Tool:** Coupa

#### Step 2: Create the requisition

The Requester creates the requisition in Coupa. The line detail is built according to
the path selected in Step 1:

- **Catalog / punchout:** the Requester selects hosted catalog items, or punches out
  to the supplier site, shops, and returns the cart to Coupa, which becomes the
  requisition lines.
- **Non-catalog free-text:** the Requester types a free-text description of what is
  required and selects the supplier.
- **Services:** the Requester uses the separate services request form, which requires a
  statement of work to be attached.

- **System / Tool:** Coupa
- **Fields / Parameters:** Requisition lines (catalog selection, punchout cart return, or free-text description); supplier (non-catalog); statement of work attachment (services).
- **Expected Result:** A requisition exists in Coupa with priced or described lines and an identified supplier.

> **VALIDATION REQUIRED — GAP-01:** The Coupa navigation paths and the mandatory fields for each of the three requisition paths — catalog/punchout, non-catalog free-text, and the services request form — including which cost accounting fields the Requester must complete. Sources describe the three paths but not the screens or field sets.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa requisition entry screen for each of the three paths, to validate the distinct forms and the fields the Requester must complete.

#### Step 3: Record the AFE number for a capital requisition

Where the requisition is for capital expenditure, the Requester enters an approved
authorization for expenditure (AFE) number in the designated custom field. A capital
requisition will not route for approval until this field carries an approved AFE
number.

- **System / Tool:** Coupa
- **Fields / Parameters:** AFE number (custom field, capital requisitions).
- **Expected Result:** The capital requisition is eligible to enter the approval chain.

> **VALIDATION REQUIRED — GAP-02:** How a requisition is identified as capital in Coupa (for example by commodity, account, or a Requester-set flag), and whether the AFE number is validated against an approved AFE register or accepted as free text.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 4: Submit the requisition into the Coupa approval chain

The Requester submits the requisition. Coupa routes it through the configured approval
chain, which is driven by the requisition value. The Cost Center Owner approves every
requisition regardless of value. Above the first threshold the Functional Vice
President is added to the chain, and above the upper threshold the requisition routes
to the Chief Financial Officer. The stated ladder is: under $2,000, Cost Center Owner
only; $2,000 to $25,000, Cost Center Owner and Functional Vice President; above the
upper threshold, the Chief Financial Officer in addition — see
[[GAP-03 — CFO APPROVAL THRESHOLD]]. The requisition approval ladder is described as
deliberately distinct from the ladder applied to non-PO invoices, which is documented
in [[non-po-invoice-entry-and-approval]] and is not applied here.

- **System / Tool:** Coupa
- **Fields / Parameters:** Requisition total value; cost center.
- **Expected Result:** The requisition is pending with the approvers determined by its value.
- **Evidence Required:** The Coupa approval chain record on the requisition.

> **VALIDATION REQUIRED — GAP-03:** The requisition value above which the Chief Financial Officer must approve. Sources conflict: the Procurement Lead states $25,000 and confirmed it when asked directly, while the Corporate Controller indicated $50,000. The lower breakpoints ($2,000 and the $2,000–$25,000 Functional Vice President band) come from a single source and are also unverified. The live Coupa approval chain export should be pulled and the full ladder confirmed against it.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead, with the Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The Coupa approval chain configuration showing the requisition value breakpoints and the approver assigned at each, to validate the ladder.

#### Step 5: Obtain approvals

Each approver reviews and approves the requisition in Coupa in sequence. The
requisition reaches fully approved status only when every approver in the chain has
approved.

- **System / Tool:** Coupa
- **Expected Result:** The requisition reaches fully approved status and is released for purchase order issuance.
- **Evidence Required:** The Coupa approval record showing each approver and the approval date.

> **VALIDATION REQUIRED — GAP-04:** Whether an approval escalation or reminder is configured in Coupa for requisitions that sit unapproved, and what the escalation interval and recipient are. The prior SOP specifies escalation after three business days, but approvals are reported to sit without escalation; whether this applies to the Coupa requisition chain was not established.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

> **VALIDATION REQUIRED — GAP-05:** How a rejected or returned requisition is handled — whether it is returned to the Requester for amendment and resubmitted through the full chain, or cancelled. No rejection path was described in the sources.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 6: Release the approved requisition

The fully approved requisition passes to purchase order issuance in Coupa. That
activity, including transmission to the supplier and any subsequent change order, is
covered by [[po-issuance-and-change-orders]].

- **System / Tool:** Coupa
- **Expected Result:** The approved requisition is available for purchase order creation.

### F. Key Controls

> **CONTROL — CTRL-001:** Cost centre approval — every requisition is approved in Coupa by the Cost Center Owner for the cost center being charged, regardless of value, before it can proceed to purchase order issuance.
> - **Type:** Preventive
> - **Frequency:** Each requisition
> - **Owner:** Cost Center Owner

> **CONTROL — CTRL-002:** Threshold-based approval escalation — the Coupa approval chain adds the Functional Vice President and then the Chief Financial Officer as the requisition value crosses the configured breakpoints, so higher-value commitments receive higher-level approval. The breakpoints are in dispute; see Step 4.
> - **Type:** Preventive
> - **Frequency:** Each requisition
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** Capital authorization — a capital requisition cannot enter the approval chain in Coupa until an approved authorization for expenditure (AFE) number is recorded in the designated custom field.
> - **Type:** Preventive
> - **Frequency:** Each capital requisition
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-004:** Statement of work requirement — a services requisition is raised on a separate Coupa form that requires a statement of work to be attached, so services commitments are supported by defined scope before approval.
> - **Type:** Preventive
> - **Frequency:** Each services requisition
> - **Owner:** Procurement Lead

### G. Outputs

- **Fully approved Coupa requisition:** Released to purchase order issuance in [[po-issuance-and-change-orders]].
- **Approval record:** The Coupa approval chain history showing each approver and approval date, retained on the requisition.
- **Evidence retained:** Statement of work attached to the requisition for services purchases; AFE number recorded on capital requisitions.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Requisition-to-purchase-order cycle time is long and is dominated by approval waiting time. The Procurement Lead measured a median of approximately 6.5 days from requisition to purchase order, of which about five days is time spent waiting in approval queues. The measurement comes from the Procurement Lead's own spreadsheet rather than a system report and should be treated as indicative.
> - **Impact:** Requesters wait roughly a week for a purchase order, which encourages purchasing outside the process, and no system-generated cycle-time measure exists to manage against.
> - **Severity:** High

> **PAIN POINT — PP-002:** Hosted and punchout catalog pricing is stale and does not always reflect negotiated contract pricing.
> - **Impact:** Requesters buy off-contract without knowing, eroding the value of negotiated agreements.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The approval ladders in use across the Procure to Pay cycle are not consistently understood. The requisition ladder is described as deliberately different from the non-PO invoice ladder, but the difference is not understood consistently across Finance and Procurement, and the requisition breakpoints themselves are stated differently by different owners.
> - **Impact:** Approval requirements cannot be stated with confidence, and neither ladder has been verified against the live system configuration.
> - **Severity:** High

> **PAIN POINT — PP-004:** Approvals sit in queues without effective escalation. Escalation after three business days is specified in the prior SOP, but approvals are reported to remain outstanding for around two weeks, indicating the escalation is either not configured or not working.
> - **Impact:** Requisitions stall with no automated prompt, extending cycle time and requiring manual chasing.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Introduce auto-approval for low-value catalog requisitions — the Procurement Lead proposes automatically approving catalog requisitions under approximately $1,000 placed against a contracted price, estimated to remove around a third of requisition volume from the approval chain.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish a scheduled catalog refresh so hosted and punchout pricing is reconciled to current negotiated contract pricing, with an owner accountable for the refresh.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Pull the Coupa approval chain export and the NetSuite non-PO approval workflow configuration, document both ladders against the live configuration, and confirm with Finance and Procurement leadership whether the difference between them is intended.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Confirm and enable approval escalation and reminder notifications on the Coupa requisition chain, and report on requisitions ageing in approval queues.
> - **Addresses:** PP-001, PP-004

```consult-meta
systems: [coupa, netsuite]
roles:   [requester, cost-center-owner, functional-vp, cfo, procurement-lead, buyer, corporate-controller, supplier]
```
