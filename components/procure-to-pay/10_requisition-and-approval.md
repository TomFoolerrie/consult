## Requisition and Approval

<!-- scope note: covers variants — Catalog / punchout requisition; Non-catalog free-text requisition; Services requisition (statement of work required). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Process Overview

Requisition and Approval is the entry point for all purchase-order-backed
spend: a Requester raises a requisition in Coupa, and the requisition routes
through Coupa's tiered approval chains until it is fully approved (SRC-002).
The procedure runs ad hoc, whenever goods or services are needed from a
supplier that is already active in Coupa and NetSuite; a supplier not yet on
file must first complete [[new-vendor-onboarding]]. Three request paths are
covered as variants of one flow: catalog / punchout requisitions, non-catalog
free-text requisitions, and services requisitions, which require a statement of
work (SRC-002). Purchases made outside this procedure — vendor call-outs
invoiced without a purchase order — are regularized after the fact under
[[confirming-po]], and non-PO invoice spend follows a separate approval ladder
under [[non-po-invoice-entry-and-approval]]. Downstream, the fully approved
requisition triggers [[po-issuance-and-change-orders]], where Coupa generates
and transmits the purchase order.

### Quick Reference

- **Trigger:** A Requester needs goods or services from a supplier that is active in Coupa (SRC-002).
- **Frequency:** Ad hoc — continuous, on demand.
- **Preparer:** Requester.
- **Reviewer:** Cost Center Owner (every requisition); Functional Vice President and Chief Financial Officer added by dollar threshold (SRC-002).
- **Primary systems / tools:** Coupa.
- **Key outputs:** Fully approved requisition in Coupa, ready for purchase order generation.

### Pre-Requisites

- The supplier exists and is active in Coupa and NetSuite; a supplier not on file must first complete [[new-vendor-onboarding]] (SRC-002).
- The Requester has access to Coupa to raise the requisition.
- For a services requisition: a statement of work is prepared and available to attach (SRC-002).
- For a capital requisition: an approved AFE (Authorization for Expenditure) number has been issued (SRC-002).

### Inputs

- **Requirement details:** description, quantity, and supplier for the goods or services needed — from the Requester.
- **Hosted catalog / punchout content:** supplier-maintained catalog items and pricing, used on the catalog path (SRC-002).
- **Statement of work:** services requisitions only; attached by the Requester (SRC-002).
- **Approved AFE number:** capital requisitions only (SRC-002). AFE issuance itself sits outside this procedure and was not described in the sources.

### Step-by-Step Procedure

#### Step 1: Initiate the requisition and select the request path

The requisition is raised in Coupa through one of three paths — Requesters
range from plant maintenance planners and engineers to marketing staff
(SRC-002):

- **Catalog / punchout:** hosted catalogs and punchout sites are available for
  MRO items through the industrial distributor, and for IT purchases. The
  hosted catalog is shopped, or a punchout to the Supplier's own site returns
  to Coupa with a cart, which becomes the requisition.
- **Non-catalog:** a free-text request — a description of what is needed is
  typed and the Supplier selected.
- **Services:** a separate services request form, used because a statement of
  work must be attached.

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa requisition entry screen showing the three request paths (hosted catalog / punchout, non-catalog free text, services request form); validates that all three intake paths exist as described.

#### Step 2: Complete variant-specific requirements

- **Condition:** the requisition is a services requisition (statement of work required) or a capital purchase (AFE number required)

For a services requisition, the statement of work is attached — the
services form exists specifically because this attachment is required
(SRC-002). For any capital purchase, regardless of path, the approved AFE
number is entered in the dedicated Coupa custom field; a capital
requisition will not route for approval at all until the field is populated —
the AFE gate described at CTRL-002 in F (SRC-002). How the gate is
administered is unconfirmed [[GAP-01 — AFE GATE ADMINISTRATION]].

- **Fields / Parameters:** AFE number (custom field, capital requisitions); statement of work attachment (services requisitions).

> **VALIDATION REQUIRED — GAP-01:** Whether the Coupa AFE custom field validates the entered number against approved AFEs or only requires that the field be populated, and which role administers the gate, were not established (SRC-002).
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-02:** A capital requisition in Coupa showing the AFE custom field populated; validates that the field exists and blocks routing when empty.

#### Step 3: Submit the requisition for approval routing

On submission, Coupa builds the approval chain — the tiered requisition
approval control described at CTRL-001 in F. The Cost Center Owner approves
every requisition. Below $2,000, the Cost Center Owner is the only approver;
from $2,000 to $25,000 the chain adds the Functional Vice President; above
$25,000 it extends to the Chief Financial Officer (SRC-002). The upper
threshold is contested across the sources
[[GAP-02 — CFO ROUTING THRESHOLD]]. This requisition ladder is distinct from
the non-PO invoice approval ladder used in
[[non-po-invoice-entry-and-approval]]; whether that divergence is deliberate
is itself contested [[GAP-03 — REQUISITION VS NON-PO LADDER]].

> **VALIDATION REQUIRED — GAP-02:** The dollar threshold at which a requisition routes to the Chief Financial Officer is contested: the Procurement Lead states $25,000 (SRC-002), the Corporate Controller implied $50,000 in passing, and the Accounts Payable Manager could not say (SRC-005). No one has verified the live approval chain configuration in Coupa — pull the Coupa approval chain export to confirm the full ladder.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

> **VALIDATION REQUIRED — GAP-03:** The Procurement Lead describes the requisition approval ladder as deliberately different from the non-PO invoice approval ladder; the Corporate Controller did not appear aware that the two ladders differ (SRC-002, SRC-005). Confirm whether the divergence is intended design and document one authoritative pair of ladders.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-03:** The approval chain panel on a submitted high-value requisition in Coupa; validates the live approver sequence by threshold and supports resolution of GAP-02.

#### Step 4: Approvers action the requisition

Each approver in the chain reviews and approves the requisition within Coupa.
Approvals frequently dwell in approver queues — the dominant share of the
requisition-to-PO cycle time, detailed in H. Handling of a rejected or
returned requisition — whether it is edited and resubmitted, and whether
a resubmission re-routes the full chain — was not described in the sources:
TBD — confirm with process owner [[GAP-04 — REJECTED REQUISITION HANDLING]].

> **VALIDATION REQUIRED — GAP-04:** How a rejected or returned requisition is handled (edit and resubmit path, and whether resubmission re-routes the full approval chain) was not described by any source.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 5: Hand off the fully approved requisition to purchase order issuance

Once the final approver has actioned the requisition, it is fully approved in
Coupa, and Coupa generates and transmits the purchase order. Purchase order
generation, transmission, and subsequent change orders are documented under
[[po-issuance-and-change-orders]] (SRC-002).

### Key Controls

> **CONTROL — CTRL-001:** Tiered requisition approval chain in Coupa: every requisition requires Cost Center Owner approval, with the Functional Vice President added from $2,000 and the Chief Financial Officer above $25,000 (upper threshold contested — see GAP-02 in E) (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each requisition
> - **Owner:** Cost Center Owner / Functional Vice President / Chief Financial Officer, by threshold

> **CONTROL — CTRL-002:** AFE gate on capital requisitions: Coupa will not route a capital requisition for approval unless an approved AFE number is present in the dedicated custom field (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each capital requisition
> - **Owner:** System-enforced in Coupa; administering role TBD — confirm with process owner (see GAP-01 in E)

### Outputs

- **Fully approved requisition (Coupa):** consumed by [[po-issuance-and-change-orders]], where Coupa generates and transmits the purchase order (SRC-002).
- **Evidence retained:** the requisition record and its approval history in Coupa, where all approvals are executed (SRC-002); no separate archive location was described in the sources.

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Requisition-to-PO cycle time runs at a median of 6.5 days, of which roughly five days is requisitions sitting in approver queues (SRC-002). The figure comes from the Procurement Lead's own spreadsheet rather than a system report and should be treated as indicative (SRC-005).
> - **Impact:** Slow fulfillment of operational needs; approval queue dwell dominates the requisition-to-PO cycle.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** Punchout catalog pricing is stale — roughly half of it does not reflect negotiated contract pricing — so Requesters buy off-contract without knowing (SRC-002, SRC-005).
> - **Impact:** Off-contract buying and loss of negotiated pricing on catalog-path spend.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Auto-approve low-dollar catalog requisitions (below approximately $1,000) placed against a contracted price, removing an estimated one-third of requisition volume from the approval chain (SRC-002, SRC-005).
> - **Addresses:** PP-001

```consult-meta
systems: [coupa, netsuite]
roles:   [requester, cost-center-owner, functional-vp, cfo, procurement-lead, corporate-controller, ap-manager, supplier]
```
