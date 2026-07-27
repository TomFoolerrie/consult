## Purchase Order Issuance and Change Orders

<!-- scope note: covers variants — Initial PO issuance and transmission; Change order / PO revision. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers the conversion of a fully approved requisition into a
purchase order in Coupa, transmission of that purchase order to the supplier, its
synchronisation into NetSuite, and any subsequent amendment of an issued purchase
order by change order. Both variants are covered here: initial issuance and the
change order or revision of a purchase order already in the supplier's hands.
Creation and approval of the underlying requisition are excluded and are
documented in [[requisition-and-approval]]; releases against an annual
not-to-exceed agreement are documented in [[blanket-po-management]], and purchase
orders raised after the commitment was already made are documented in
[[confirming-po]]. Receipt against the issued purchase order is excluded and is
documented in [[goods-receipt]], as is the matching of the supplier invoice to it
in [[po-invoice-entry-and-three-way-match]]. (SRC-002, SRC-004, SRC-005)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A requisition reaches full approval in Coupa; or an issued purchase order must be amended in quantity, value or content |
| Frequency | Ad hoc, continuous |
| Preparer | Coupa (system-generated on full approval); Buyer or Requester for a change order |
| Reviewer | Approval chain approvers by value — Cost Center Owner, Functional Vice President, Chief Financial Officer — on a value-increasing change order only |
| Systems | Coupa (purchase order creation, transmission and change orders); NetSuite (receives the synchronised purchase order) |
| Key inputs | Fully approved Coupa requisition; supplier cXML enablement status or remit contact email |
| Key outputs | Issued purchase order numbered `NIG-<sequential>`, transmitted to the supplier and synchronised to NetSuite; revised purchase order versions where amended |

### Before You Start

- **Fully approved Coupa requisition** — [[requisition-and-approval]]; every
  approver in the chain must have approved before Coupa will cut the purchase
  order.
- **Active supplier record** — [[new-vendor-onboarding]]; must exist in Coupa and
  in NetSuite, since the purchase order is cut in Coupa and synchronised to the
  NetSuite vendor master.
- **Supplier transmission method** — held on the supplier record as either cXML
  enablement or an email contact; determines how the purchase order is sent.
- **Issued purchase order** — required only for the change order variant; must be
  an existing purchase order in Coupa, which the amendment supersedes with a new
  version.

### Procedure

#### Step 1: Cut the purchase order from the approved requisition

Once the requisition is fully approved, Coupa creates the purchase order from it.
Purchase order numbers are assigned sequentially in the format `NIG-` followed by
a sequential number. (SRC-002)

- **Fields / Parameters:** purchase order number, format `NIG-<sequential>`.

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa purchase order record as created from an approved requisition, showing the `NIG-` number and the source requisition.

#### Step 2: Transmit the purchase order to the supplier

Coupa transmits the purchase order to the supplier. Suppliers that are cXML
enabled — approximately 60 of them — receive it by cXML; all remaining suppliers
receive a PDF copy by email. (SRC-002)

- **Expected Result:** the purchase order leaves Coupa by the channel configured
  on the supplier record; no source describes a confirmation that the supplier
  received it.

> **VALIDATION REQUIRED — GAP-01:** No monitoring of purchase order transmission failure was described by any source.
> - **Note:** Do not assume a transmitted purchase order was delivered — confirm whether a failed cXML transmission or a bounced email is surfaced to anyone, and who acts on it.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 3: Synchronise the purchase order to NetSuite

The issued purchase order synchronises into NetSuite, where it becomes available
for receipt and for matching against the supplier invoice.

- **System / Tool:** NetSuite, which receives the purchase order from Coupa.
- **Expected Result:** an open purchase order exists in NetSuite against which a
  receipt and a bill can be recorded.

> **VALIDATION REQUIRED — GAP-02:** The Coupa-to-NetSuite integration has no named owner and no described monitoring or alerting.
> - **Note:** A purchase order that fails to reach NetSuite is not signalled by any process described in the sources; confirm the owner and the failure-detection mechanism before relying on synchronisation.
> - **Detail:** The nightly supplier synchronisation from Coupa to NetSuite is known to fail intermittently, leaving records incomplete and corrected by hand, and no interviewee could name an owner or any monitoring or alerting over the integration (SRC-005). The same working notes record that each failure consumes roughly three people for about an hour. No source described whether purchase order synchronisation shares that integration, that failure mode or that absence of monitoring. Resolution sits with the IT Manager jointly with the Procurement Lead.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

#### Step 4: Raise a change order against an issued purchase order

- **Condition:** an issued purchase order must be amended

The purchase order is edited in Coupa by the Requester or the Buyer. The edit
creates a new version of the purchase order — the first amendment produces
version 2 — which supersedes the prior version. (SRC-002)

> **SCREENSHOT PLACEHOLDER — SC-02:** The Coupa purchase order in an amended state, showing the version indicator and the approval chain assigned to the revision.

#### Step 5: Raise a change order to clear a blocked over-receipt

- **Condition:** a delivered quantity exceeds the purchase order quantity by more
  than the configured receiving tolerance

Where a shipment exceeds the ordered quantity by more than the tolerance
configured in NetSuite, the receipt is blocked at the dock and the Receiving
Supervisor asks the Buyer to raise a change order increasing the purchase order
quantity. Quantities within the tolerance are received without a change order,
and a short shipment requires none — the purchase order remains open for the
balance. (SRC-004)

- **System / Tool:** NetSuite, where the over-receipt is blocked, before the
  change order is raised in Coupa.

> **VALIDATION REQUIRED — GAP-03:** The over-receipt tolerance that forces a change order is unconfirmed.
> - **Note:** The tolerance is unconfirmed — do not operate to a figure; obtain the configured NetSuite value before applying it.
> - **Detail:** The Receiving Supervisor recalled a percentage tolerance of approximately 10% and believed there is also a dollar cap of perhaps $500, while stating he did not know the numbers exactly and deferring to the Buyer or to whoever configured it (SRC-004). The working notes record the over-receipt tolerance as insufficiently supported to document, note that it does not appear in the prior SOP excerpt, and flag that the Receiving Supervisor may be conflating it with the three-way match tolerance, which is itself disputed (SRC-005). The NetSuite configuration has not been pulled. Resolution sits with the Buyer.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

#### Step 6: Re-route a value-increasing revision for approval

- **Condition:** the change order increases the value of the purchase order

A revision that increases the purchase order value re-enters the Coupa approval
chain before it is issued. The approvers required are those the revised value
attracts under the requisition approval ladder described in
[[requisition-and-approval]]. See [[GAP-04 — CHANGE ORDER RE-APPROVAL RULE]].

> **VALIDATION REQUIRED — GAP-04:** The rule determining which approvers a value-increasing change order re-routes to is in conflict between sources.
> - **Note:** The re-approval rule is unconfirmed — do not describe a grace band or a reduced approver set to a preparer until the Coupa configuration has been read.
> - **Detail:** The Procurement Lead initially stated that an increase of less than approximately 10% returns only to the Cost Center Manager rather than the full chain (SRC-002). The Buyer contradicted this in the same interview, stating that the revision re-routes to whoever the new dollar value attracts — so a purchase order moving from $24,000 to either $26,000 or $28,000 requires Chief Financial Officer approval — and the Procurement Lead then accepted that there is no 10% grace band. The Buyer qualified his own answer as approximately 80% certain and stated he had never read the configuration. No party has consulted the Coupa approval chain export (SRC-005). Resolution sits with the Procurement Lead, who owns the Coupa approval chains.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

#### Step 7: Issue a value-decreasing revision without re-approval

- **Condition:** the change order decreases the value of the purchase order

A revision that decreases the purchase order value does not re-enter the approval
chain and is issued on the approvals already recorded against the prior version.
(SRC-002)

#### Step 8: Transmit and synchronise the revised purchase order

- **Condition:** a change order has been raised

The revised purchase order version is transmitted to the supplier and
synchronised to NetSuite by the same channels as the initial issuance.

### Outputs & Evidence

- **Issued purchase order** — numbered `NIG-<sequential>` in Coupa; transmitted
  to the supplier and synchronised to NetSuite, where it is the input to
  [[goods-receipt]] and to [[po-invoice-entry-and-three-way-match]].
- **Revised purchase order version** — supersedes the prior version in Coupa and
  re-synchronises to NetSuite.
- **Evidence retained:** the purchase order record, its version history and the
  approval chain recorded against each version are retained in Coupa.
- **Not retained:** no record of a failed purchase order transmission or a failed
  Coupa-to-NetSuite synchronisation is retained, and no source described one being
  produced; no measurement of change order volume, of re-approval turnaround, or
  of the frequency of over-receipt-driven change orders is retained.

### Key Controls

> **CONTROL — CTRL-001:** A purchase order is created only from a fully approved requisition; Coupa cuts and transmits the purchase order on full approval and not before.
> - **Type:** Preventive
> - **Frequency:** each purchase order
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-002:** A change order that increases the value of an issued purchase order re-enters the Coupa approval chain before the revised version is issued; a decrease does not re-route.
> - **Type:** Preventive
> - **Frequency:** each value-increasing change order
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** A delivered quantity above the configured receiving tolerance is blocked in NetSuite and cannot be received until the Buyer raises a change order increasing the ordered quantity.
> - **Type:** Preventive
> - **Frequency:** each receipt exceeding the tolerance
> - **Owner:** Buyer

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Failures of the Coupa-to-NetSuite integration are detected by their downstream symptoms rather than by monitoring, and have no owner.
> - **Note:** Each failure is worked out reactively and consumes roughly three people for about an hour; no alerting exists and no interviewee could name an owner.
> - **Detail:** The Procurement Lead named Coupa-to-NetSuite synchronisation as one of his four pain points, stating that every time something does not sync, three people spend an hour on it (SRC-002). The working notes record that the nightly synchronisation breaks intermittently, that records land incomplete and are corrected by hand, and that nobody could name an owner or any monitoring or alerting over it (SRC-005).
> - **Impact:** A purchase order that does not reach NetSuite blocks receipt and invoice matching until somebody notices downstream, and the remediation effort is unplanned and undirected.
> - **Severity:** High

> **PAIN POINT — PP-002:** The change order re-approval rule is not documented and the Coupa configuration governing it has never been read.
> - **Note:** The Procurement Lead and the Buyer gave contradictory accounts of which approvers a value-increasing revision re-routes to, and neither had consulted the configuration.
> - **Detail:** The Procurement Lead stated there was a grace band below approximately 10% that returns the revision only to the Cost Center Manager, then accepted the Buyer's contrary account that routing follows the new dollar value; the Buyer put his own confidence at approximately 80% and stated he had never read the configuration (SRC-002). The Coupa approval chain export remains outstanding (SRC-005). The conflict is logged as GAP-04.
> - **Impact:** Buyers cannot predict what a revision will require, and no party can assert that value-increasing amendments are approved at the correct level.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a named owner to the Coupa-to-NetSuite integration and implement failure alerting, so that a purchase order or supplier record that does not synchronise is detected at the integration rather than by the receiving dock or Accounts Payable.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Extract the Coupa approval chain configuration and document the change order re-approval rule, including the receiving tolerance that forces a change order, so that both are stated from the system of record rather than from recollection.
> - **Addresses:** PP-002

```consult-meta
systems: [coupa, netsuite]
roles:   [procurement-lead, buyer, requester, receiving-supervisor, cost-center-owner, functional-vp, cfo, it-manager]
```
