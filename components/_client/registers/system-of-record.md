# System-of-Record Matrix

<!-- ENGAGEMENT REGISTER — the one home of "which system is authoritative
     for this business object." Drop into components/_client/registers/.
     Procedures reference the row; a procedure treating a different system
     as authoritative for an object is a finding. Seeded from the seam
     analysis (Root Cause 1 + Section 1). -->

_One row per business object. "Also present in" names the overlapping
representations that are NOT authoritative — the analysis's root cause was
each procedure picking its own apparent source._

| Business object | System of record | Also present in (not authoritative) | Owning L1 | Status |
|---|---|---|---|---|
| Contract (current agreement) | pending — LinkSquares vs Cobblestone transition unresolved (analysis finding) | Cobblestone (legacy), SharePoint, Ariba links | Procure to Pay | open issue |
| Vendor master | SAP S/4HANA | Ariba (synced) | Procure to Pay | pending confirmation |
| Vendor banking | SAP S/4HANA | pending — entry point unresolved | Procure to Pay | open issue |
| Approval authority | DoA policy (principle) + Approval Matrix register (implementation) | System configs, DocuSign, email | Procure to Pay (policy custody) | pending |
| Purchase order | pending — Ariba vs S/4HANA by PO type | both | Procure to Pay | open issue |
| Goods receipt | SAP S/4HANA (material document) | Receiving paperwork, batch records | Procure to Pay | pending confirmation |
| Inventory quantity | SAP S/4HANA | Cardinal 3PL portal, PharmaCord reports, Excel rollforwards | Inventory | pending confirmation |
| Inventory value | SAP S/4HANA (actual costing) | Excel workbooks, Anaplan | Inventory | pending confirmation |
| Customer shipment / delivery date | Cardinal (shipment) + POD report (delivery) | courier tracking | Order to Cash | pending confirmation |
| Customer invoice | SAP S/4HANA | Cardinal | Order to Cash | pending confirmation |
| Cash receipt | SAP S/4HANA (incoming payments) | Citi portal, Cardinal Cash Receipt Journal | Order to Cash | pending confirmation |
| Supplier payment | SAP S/4HANA (payment documents) | Citizens Bank | Procure to Pay | pending confirmation |
| Journal entry | BlackLine (manual JEs) / SAP (see posting-method taxonomy) | Excel upload templates, Gapify | Financial Statement Close | pending |
| Account reconciliation | BlackLine | Excel | Financial Statement Close | pending confirmation |
| Final reporting package | SharePoint (HQ package files) | Anaplan, Excel | Financial Statement Close | pending confirmation |
| PAP unit populations | pending — see PAP population dictionary (future register) | SAP storage locations, PharmaCord | Inventory (quantity+cost) | open issue |
| Commercial delivered-unit population | O2C Revenue Cut-Off controlled output (analysis Seam E) | Inventory rollforward re-derivation (to be retired) | Order to Cash | pending confirmation |
