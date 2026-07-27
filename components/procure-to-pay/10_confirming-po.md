## Confirming (After-the-Fact) Purchase Order

### Scope

This procedure covers the creation of a purchase order after goods have already
been delivered or services already performed without a purchase order in place —
the "confirming PO" — from the point an unmatched supplier invoice is returned to
procurement through to the PO being available for receipt and invoice matching.
It covers the justification expected to support the after-the-fact commitment and
the handling of delivered material that could not be tied to a PO at the dock. It
excludes normal, in-advance requisitioning and PO issuance ([[requisition-and-approval]],
[[po-issuance-and-change-orders]]), the receipt transaction itself
([[goods-receipt]]) and the subsequent matching and entry of the supplier invoice
([[po-invoice-entry-and-three-way-match]]). Non-PO invoices that are deliberately
processed without a purchase order are handled under
[[non-po-invoice-entry-and-approval]] rather than converted to a confirming PO.

### At a Glance

| Field | Value |
|---|---|
| Trigger | A supplier invoice arrives for goods or services already delivered with no purchase order, and is returned to procurement by Accounts Payable |
| Frequency | Approximately 15–20 per month, concentrated at Plant 2 (SRC-002, SRC-005) |
| Preparer | Procurement Lead or Buyer, depending on plant |
| Reviewer | TBD — confirm with process owner (see GAP-01) |
| Systems | Coupa; NetSuite (receipt and matching downstream) |
| Key inputs | Unmatched supplier invoice; written justification for the after-the-fact commitment |
| Key outputs | Confirming purchase order in Coupa, synced to NetSuite and available for receipt and match |

### Before You Start

- **Unmatched supplier invoice** — [[invoice-intake-and-capture]]; received and
  returned to procurement by Accounts Payable because no purchase order could be
  identified.
- **Written justification for the commitment** — from the requesting plant or
  department; expected to be a written justification from the Plant Manager, though
  in practice an email from any requester is accepted (SRC-002).
- **Supplier record** — [[new-vendor-onboarding]]; the supplier must already exist
  and be active in Coupa and in the NetSuite vendor master, since a PO cannot be
  raised against a supplier that has not been onboarded.
- **Delivered material or completed service** — physical goods may be held
  unidentified in the segregated receiving area at Plant 2 ("the cage") pending
  identification of the PO they belong to (SRC-004).

### Procedure

#### Step 1: Receive the returned invoice and identify the unauthorized commitment

An invoice that cannot be matched to a purchase order is returned by Accounts
Payable to procurement. The supplier, the plant or department that placed the
order, and the goods or services delivered are identified from the invoice and,
where available, the supplier's supporting paperwork.

- **Evidence Required:** the returned supplier invoice.

#### Step 2: Obtain the justification for the after-the-fact commitment

A written justification for the commitment is obtained from the requesting plant.
The stated requirement is a written justification from the Plant Manager; the
practice described is that an email from any requester is accepted (SRC-002).

> **VALIDATION REQUIRED — GAP-02:** The justification standard for a confirming
> purchase order is not applied as stated.
> - **Note:** Obtain a written justification from the Plant Manager as the stated
>   requirement; the accepted practice is unconfirmed — see GAP-02.
> - **Detail:** The Procurement Lead states the confirming PO "is supposed to
>   require a written justification from the plant manager", but that "in practice
>   it requires an email from anyone" (SRC-002). It is unconfirmed whether the
>   Plant Manager requirement is documented policy, what form of justification is
>   actually accepted, and whether any exception to it is approved. Resolution sits
>   with the Procurement Lead.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

#### Step 3: Create the confirming purchase order

The purchase order is created after the fact in Coupa against the existing
supplier, for the goods or services already delivered, at the price invoiced. The
PO is then transmitted and syncs into NetSuite so that a receipt and an invoice
match can be performed.

> **VALIDATION REQUIRED — GAP-01:** The creation and approval path for a confirming
> purchase order is unconfirmed.
> - **Note:** Confirm the Coupa document type and approval routing before creating
>   the PO — do not assume the standard requisition chain applies. See GAP-01.
> - **Detail:** Sources establish that procurement "create[s] a PO after the fact"
>   (SRC-002) but describe no distinct Coupa transaction type, navigation path,
>   field flag or marker identifying the order as confirming, and no approval
>   routing. It is unconfirmed whether the standard requisition approval chain and
>   dollar thresholds re-apply to a commitment already incurred, who reviews or
>   approves the resulting PO, and whether confirming POs are distinguishable in
>   Coupa for reporting. Resolution requires the Coupa approval chain export and
>   confirmation from the Procurement Lead.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa purchase order creation screen for
> a confirming PO, showing any field or flag that identifies the order as
> after-the-fact.

#### Step 4: Release material held in the segregated receiving area against the new PO

- **Condition:** physical goods were delivered and are held unidentified in the
  segregated receiving area at the plant

Delivered material that could not be tied to a purchase order at the dock is held
in a fenced area of the receiving floor at Plant 2 until it is claimed. Once the
confirming PO exists, the held material is identified against it so that the
receipt can be entered (SRC-004).

- **System / Tool:** the receiving floor at the plant (physical inspection of held
  material)

#### Step 5: Hand the confirming PO back for receipt and invoice processing

The confirming PO is communicated back to Accounts Payable and to the receiving
function so that the receipt can be entered against it ([[goods-receipt]]) and the
returned invoice can be entered and matched
([[po-invoice-entry-and-three-way-match]]).

### Outputs & Evidence

- **Confirming purchase order** — raised in Coupa and synced to NetSuite; consumed
  downstream by [[goods-receipt]] and [[po-invoice-entry-and-three-way-match]].
- **Justification correspondence** — the email or written justification supporting
  the commitment. Its retention location and period were not established;
  TBD — confirm with process owner.
- **Not retained:** no formal metric, log or register of confirming purchase orders
  is maintained. The Procurement Lead keeps a personal spreadsheet, which is not a
  tracked measure (SRC-002).

### Key Controls

> **CONTROL — CTRL-001:** An invoice that cannot be matched to a purchase order is
> not processed; it is returned to procurement, which surfaces the unauthorized
> commitment and forces creation of a confirming purchase order.
> - **Type:** Detective
> - **Frequency:** Each occurrence
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-002:** A confirming purchase order is supported by a written
> justification for the after-the-fact commitment from the requesting plant.
> - **Type:** Preventive
> - **Frequency:** Each occurrence
> - **Owner:** Plant Manager

> **CONTROL — CTRL-003:** Delivered material that cannot be tied to a purchase
> order is segregated in a controlled area of the receiving floor and is not put
> away or consumed until it is claimed and matched to a purchase order.
> - **Type:** Preventive
> - **Frequency:** Each occurrence
> - **Owner:** Receiving Supervisor

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Commitments are made outside the procurement process at
> a rate of roughly 15–20 per month, concentrated at Plant 2, and the volume is not
> tracked as a metric.
> - **Note:** Confirming purchase orders run at 15–20 per month with no formal
>   measurement, so the leakage is neither visible nor managed.
> - **Detail:** The Procurement Lead describes the pattern as a plant going down,
>   maintenance calling a vendor direct, the vendor performing the work and
>   invoicing with no purchase order in place (SRC-002). Volume is estimated at
>   15–20 per month, concentrated at Plant 2 (SRC-002, SRC-005). Asked whether the
>   volume is tracked as a metric, the Procurement Lead confirmed it is not, noting
>   only a personal spreadsheet. The consequence named is loss of price leverage,
>   because the commitment is made before procurement is involved.
> - **Impact:** Spend is committed outside the process with no negotiated price and
>   no competitive leverage; the scale of the leakage is not measured.
> - **Severity:** High

> **PAIN POINT — PP-002:** The stated requirement for a Plant Manager written
> justification is not enforced; an email from any requester is accepted.
> - **Impact:** The only preventive control over after-the-fact commitments
>   operates as a formality, providing no accountability at the plant for
>   bypassing the process.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Delivered goods that cannot be tied to a purchase order
> accumulate in the segregated receiving area at Plant 2 and are not cleared.
> - **Note:** Roughly 30 pallets sit unidentified in the segregated area at Plant 2,
>   some since autumn 2025, largely from direct-to-vendor ordering.
> - **Detail:** The Receiving Supervisor describes a fenced area in the back corner
>   of the receiving floor holding anything that cannot be tied to a purchase order
>   until somebody claims it, estimating roughly 30 pallets at the time of the
>   walkthrough with some material held since the previous autumn (SRC-004,
>   SRC-005). The Receiving Supervisor attributes the contents to people calling a
>   vendor direct without a requisition. No clearing routine, ageing review or
>   owner for the held material was described by any source.
> - **Impact:** Material that has been delivered and will be invoiced is neither
>   received nor available for use; the associated liability is unrecorded until the
>   confirming purchase order is raised.
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Track confirming purchase orders as a
> reported metric — volume, value, plant and requesting department — from Coupa
> rather than a personal spreadsheet, and review the trend with plant leadership.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Enforce the justification requirement by
> routing every confirming purchase order for Plant Manager approval in Coupa, so
> the justification is captured on the transaction rather than in email.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Establish an owner and a periodic ageing
> review for material held in the segregated receiving area, so held items are
> claimed, converted to a confirming purchase order or returned rather than
> accumulating.
> - **Addresses:** PP-003

```consult-meta
systems: [coupa, netsuite]
roles:   [procurement-lead, buyer, plant-manager, receiving-supervisor, ap-manager, requester]
```
