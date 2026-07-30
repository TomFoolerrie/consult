# Accounting-Date & Cutoff Matrix

<!-- ENGAGEMENT REGISTER — the one home of date/cutoff conclusions.
     Drop this file into components/_client/registers/ at your engagement
     root. Procedures REFERENCE this register; they never restate its rows.
     Seeded from the cross-L1 seam analysis (Seam D) — every row marked
     "pending" is a management conclusion still to be confirmed; a
     procedure needing that row keeps its GAP until the row is settled. -->

_Which event date governs accounting recognition, per transaction type.
"Date," "receipt," "delivery," "release," and "posting" are different
events — a procedure names the row it relies on rather than re-deriving
the rule._

| Transaction type | Physical event | Title transfer | Recognition date | Cutoff evidence | Late-document treatment | Owner of conclusion | Status |
|---|---|---|---|---|---|---|---|
| Customer sales | Delivery to customer | pending | Delivery date (POD) | Shipment Tracking w/ POD report | pending | Order to Cash | pending confirmation |
| Purchased materials | Physical arrival at dock | pending | pending — paperwork receipt vs physical arrival unresolved | GR posting + receiving paperwork | pending | Procure to Pay | pending confirmation |
| Drug substance | Shipment (title may transfer at ship) | At shipment (per analysis — confirm) | pending — title at ship vs SAP receipt later | pending | pending | pending | pending confirmation |
| Production completion | Batch release | n/a | pending — GR may wait on quality-release docs | Release docs + material document | pending | P2P → Inventory (see production handoff) | pending confirmation |
| PAP transfer / dispensing | Transfer vs dispense are DIFFERENT events | n/a | pending — see PAP population dictionary | PharmaCord reporting | pending | Inventory | pending confirmation |
| Physical checks (receipts) | pending — receipt vs mailing vs bank deposit | n/a | pending | pending | pending | Order to Cash | pending confirmation |
| Supplier invoices | Invoice receipt | n/a | pending | invoice entry record | pending | Procure to Pay | pending confirmation |
| Intercompany activity | pending | pending | pending | pending | Period reopening owned by FSC | Financial Statement Close | pending confirmation |

**Standing rules (confirmed as of seeding):**
- Period reopening for late entries is owned by Financial Statement Close.
- O2C revenue recognition is delivery-based; any extract pulled by shipment
  date must be bridged to delivery before use (the bridge lives in the
  Revenue Cut-Off procedure, not here).
