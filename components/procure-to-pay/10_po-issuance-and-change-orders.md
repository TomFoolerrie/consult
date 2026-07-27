## PO Issuance and Change Orders

<!-- scope note: covers variants — PO issuance and transmission (cXML or PDF); Change order (PO revision); Blanket PO (annual not-to-exceed). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers turning a fully approved Coupa requisition into a
purchase order in the Supplier's hands, change orders (purchase order
revisions), and blanket purchase orders carrying an annual not-to-exceed (NTE)
value for recurring spend (SRC-002). It begins where
[[requisition-and-approval]] ends — each requisition that completes approval.
Downstream, the purchase order is received against in [[goods-receipt]] and
matched in [[po-invoice-entry-and-three-way-match]]. Purchase orders raised
after the fact for goods or services a vendor has already supplied are
excluded — they follow [[confirming-po]] (SRC-002).

### At a Glance

| Field | Value |
|---|---|
| Trigger | Full approval of a requisition in Coupa (issuance); a required revision to an issued purchase order, including over-shipment blocks referred by receiving (change order); recurring annual spend (blanket purchase order) (SRC-002, SRC-004) |
| Frequency | Continuous — purchase orders issue as requisitions complete approval; change orders and blanket setup are ad hoc |
| Preparer | None at issuance — Coupa cuts the purchase order automatically (SRC-002). Change orders: Requester or Buyer (SRC-002). Blanket purchase order setup: TBD — confirm with process owner (see GAP-04) |
| Reviewer | None described at issuance; value-increasing change orders re-route to the requisition-chain approvers of [[requisition-and-approval]] (SRC-002) |
| Systems | Coupa (purchase order generation, transmission, revision, blanket NTE); NetSuite (receives the purchase order by sync) |
| Key inputs | Fully approved requisition; Supplier transmission details; change order request; blanket purchase order NTE terms (SRC-002, SRC-004) |
| Key outputs | Transmitted purchase order (NIG- sequential number); purchase order revisions with re-approval trail; blanket purchase orders with annual NTE; purchase order record in NetSuite (SRC-002) |

### Before You Start

- **Fully approved requisition** — [[requisition-and-approval]]; exists in Coupa with the Requester and the completed approval chain (SRC-002).
- **Coupa supplier record** — the Supplier is active in Coupa with a transmission path: cXML enablement, or an email address for the PDF copy (SRC-002).
- **Issued purchase order** (change orders only) — exists in Coupa (SRC-002).
- **Change order request** — the revised quantities or values, from the Requester or Buyer; includes over-shipment blocks referred by the Receiving Supervisor (SRC-002, SRC-004).
- **Blanket purchase order terms** — the annual not-to-exceed value for the recurring spend category; for a release against a blanket, cumulative releases must remain below the annual NTE — releases block once the ceiling is reached (SRC-002).

### Procedure

#### Step 1: Coupa generates the purchase order at final requisition approval

Once the requisition is fully approved, Coupa cuts the purchase order — no
manual preparation step sits between final approval and issuance (SRC-002).
The purchase order number is the NIG- prefix followed by a sequential number
(SRC-002).

> **SCREENSHOT PLACEHOLDER — SC-01:** An issued purchase order in Coupa showing the NIG- sequential number and issued status; validates automatic generation from an approved requisition and the numbering format.

#### Step 2: Transmit the purchase order to the Supplier

Coupa transmits the purchase order. Suppliers enabled for cXML — approximately
sixty of them — receive it electronically; all other suppliers receive a PDF
by email (SRC-002). How a failed or unconfirmed transmission (a cXML error or
a bounced email) is detected and remediated was not described by any source:
TBD — confirm with process owner [[GAP-01 — PO TRANSMISSION FAILURE HANDLING]].

- **Fields / Parameters:** Transmission method (cXML or email PDF), determined by the Supplier's enablement on the Coupa supplier record (SRC-002).

> **VALIDATION REQUIRED — GAP-01:** How a failed cXML transmission or a bounced PDF email is detected, who is alerted, and how the purchase order is re-sent were not described in the sources (SRC-002).
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 3: The purchase order syncs to NetSuite

The issued purchase order syncs from Coupa into NetSuite, giving receiving an
open purchase order to receive against and accounts payable a purchase order
to match invoices against — consumed downstream by [[goods-receipt]] and
[[po-invoice-entry-and-three-way-match]] (SRC-002). The sync cadence for
purchase orders and the failure-handling ownership were not established;
Coupa-to-NetSuite sync failures today are resolved ad hoc, at material effort
(see PP-002 in Known Issues) [[GAP-02 — PO SYNC CADENCE AND FAILURE OWNERSHIP]].

- **System / Tool:** Coupa → NetSuite interface

> **VALIDATION REQUIRED — GAP-02:** The cadence of the Coupa-to-NetSuite purchase order sync, and the owner and resolution path when a record fails to sync, were not established — the related supplier-record sync is described as having no monitoring, alerting, or named owner (SRC-002, SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

#### Step 4: Change order — initiate a purchase order revision

- **Condition:** an issued purchase order must change

Common
triggers are revised quantities or values from the business, and over-shipment
blocks: when a delivery exceeds what receiving is permitted to accept against
the purchase order, the receipt blocks and the Receiving Supervisor asks the
Buyer to raise a change order (the receiving tolerance itself is documented in
[[goods-receipt]]) (SRC-004). The purchase order is edited
in Coupa, which creates a new version of the purchase order (SRC-002).

> **SCREENSHOT PLACEHOLDER — SC-02:** The version history of a revised purchase order in Coupa showing the original and revised versions and the associated approval routing; validates that revisions are versioned rather than overwritten.

#### Step 5: Change order — re-approval routing by value change

- **Condition:** a purchase order revision changes the purchase order value

A revision that increases the purchase order value re-routes for approval; a
revision that decreases the value does not re-route (SRC-002). Per the Buyer's
account, an increase re-routes to whichever approval level the new total value
reaches under the requisition approval chain of [[requisition-and-approval]],
with no grace band for small increases; the Procurement Lead initially
described increases under ten percent as returning only to the Cost Center
Owner, then withdrew that account in the same interview. Neither account has
been verified against the Coupa configuration
[[GAP-03 — CHANGE-ORDER RE-APPROVAL ROUTING]].

> **VALIDATION REQUIRED — GAP-03:** The re-approval routing for value-increasing change orders is contested.
> - **Note:** Do not document a grace band for small increases — the routing rule for value-increasing revisions is contested; see GAP-03.
> - **Detail:** The Buyer states the revision re-routes to whichever approvers the new total value requires, with no grace band — at roughly eighty percent confidence, never having read the configuration — while the Procurement Lead initially described a sub-ten-percent grace band routing only to the Cost Center Owner before deferring to the Buyer (SRC-002, SRC-005). Pull the Coupa approval chain configuration to confirm the live routing rule.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

#### Step 6: Blanket purchase order — establish and release against an annual NTE

- **Condition:** recurring spend covered by a blanket purchase order

Recurring spend categories — janitorial,
the gas supplier, tooling consignment — are covered by blanket purchase orders
carrying an annual not-to-exceed value and released against by receipt
(SRC-002). When cumulative releases reach the NTE, further releases block
(SRC-002). A Coupa burn-down report exists for monitoring NTE consumption, but
no one runs it on a schedule and no owner or cadence is defined — releases
routinely block mid-year with no warning (see PP-001 in Known Issues) (SRC-002, SRC-005).
Who establishes a blanket purchase order, and how a blocked blanket is
unblocked — the NTE increase path and the approval it requires — were not
described: TBD — confirm with process owner
[[GAP-04 — BLANKET PO ADMINISTRATION]].

> **VALIDATION REQUIRED — GAP-04:** Who sets up a blanket purchase order, who approves the annual NTE, and the procedure for increasing the NTE when releases block at the ceiling were not described by any source (SRC-002, SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

> **SCREENSHOT PLACEHOLDER — SC-03:** The Coupa blanket purchase order burn-down report for an active blanket; validates that the report exists and shows cumulative releases against the annual NTE.

### Outputs & Evidence

- **Issued purchase order:** transmitted to the Supplier by cXML (approximately sixty enabled suppliers) or PDF email (SRC-002).
- **Purchase order record in NetSuite:** the open purchase order that [[goods-receipt]] receives against and [[po-invoice-entry-and-three-way-match]] matches against (SRC-002).
- **Purchase order revisions:** new versions with their re-approval history, held in Coupa (SRC-002).
- **Blanket purchase orders:** annual NTE instruments released against by receipt, with a Coupa burn-down report available on demand (SRC-002).
- **Evidence retained:** the purchase order's version and approval history on the Coupa record (SRC-002); no separate archive location was described in the sources.

### Key Controls

> **CONTROL — CTRL-001:** A purchase order is generated only from a fully approved requisition — Coupa does not cut the purchase order until the approval chain of [[requisition-and-approval]] completes (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each purchase order
> - **Owner:** System-enforced in Coupa; Procurement Lead owns the process

> **CONTROL — CTRL-002:** Change-order re-approval — a revision that increases the purchase order value re-routes for approval before taking effect; decreases do not re-route (routing detail contested — GAP-03 in the Procedure section) (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each value-increasing change order
> - **Owner:** Requisition-chain approvers per [[requisition-and-approval]]

> **CONTROL — CTRL-003:** Blanket purchase order NTE ceiling — Coupa blocks further releases once cumulative releases reach the annual not-to-exceed value (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each release against a blanket purchase order
> - **Owner:** System-enforced in Coupa; monitoring owner undefined (GAP-04 in the Procedure section)

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Blanket purchase order NTE burn-down is unmonitored: the Coupa report exists, but no one runs it on a schedule and no owner is defined, so blankets hit the annual ceiling mid-year — described as month nine — and all releases block without warning, producing urgent escalations to the Buyer (SRC-002, SRC-005).
> - **Impact:** Supply interruption for recurring services and materials until the block is cleared; unplanned firefighting for the Buyer.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** Coupa-to-NetSuite sync failures are resolved ad hoc — per the Procurement Lead, roughly three people spend an hour each time something fails to sync, and no monitoring, alerting, or named owner for the interface could be identified (SRC-002, SRC-005).
> - **Impact:** Recurring multi-person rework; downstream receiving and invoice matching wait on the purchase order reaching NetSuite.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a named owner and a scheduled cadence for the Coupa NTE burn-down report, so blanket purchase orders are replenished before the ceiling blocks releases (SRC-002).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish monitoring and alerting on the Coupa-to-NetSuite interface with a named owner for failure resolution, replacing today's ad hoc multi-person triage (SRC-005).
> - **Addresses:** PP-002

```consult-meta
systems: [coupa, netsuite]
roles:   [requester, buyer, procurement-lead, receiving-supervisor, cost-center-owner, supplier]
```
