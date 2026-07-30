# Approval Matrix

<!-- ENGAGEMENT REGISTER — the one home of approval routing.
     Drop into components/_client/registers/. The DoA POLICY defines
     principle and threshold; THIS register defines implementation;
     procedures reference a row and describe only transaction-specific
     exceptions. Seeded from the seam analysis (Seam B) — rows marked
     "pending" are approval-authority questions for management, not
     documentation gaps. -->

_One row per transaction type and amount band: who prepares, who approves,
in what order, whether the system enforces it, and where the evidence
lands. A procedure writes "per the engagement approval matrix (contracts,
mid-tier band)" — never a local copy of the threshold._

| Transaction type | System | Amount band | Preparer | Approver sequence | System-enforced? | Evidence location | Amendment rule | Status |
|---|---|---|---|---|---|---|---|---|
| Contract execution | LinkSquares | low band (define) | pending | pending | Partially (stages) | LinkSquares + DocuSign | pending — incremental vs revised-total unresolved | pending |
| Contract execution | LinkSquares | mid-tier band | pending | **pending — routing for this band is MISSING (analysis finding)** | pending | pending | pending | open issue |
| Contract execution | LinkSquares | high band (define) | pending | pending | pending | pending | pending | pending |
| Purchase order — Ariba | SAP Ariba | per Ariba authority matrix | Requester | Per configured chain | Yes | Ariba workflow log | Re-approval on change order: pending | pending |
| Purchase order — Supply Chain direct | SAP S/4HANA | **thresholds unidentified (analysis finding)** | Supply Chain | pending | pending | pending — off-system approvals not attached to SAP records | pending | open issue |
| RFA | DocuSign | tiers: pending | pending | pending | No (off-system) | DocuSign envelope | pending | open issue |
| Goods receipt | SAP S/4HANA (MIGO) | n/a | Receiver | Reviewer: pending (analysis finding) | No | Material document | n/a | pending |
| Supplier invoice | SAP S/4HANA | per DoA | AP | pending | pending | SAP + attachments | n/a | pending |
| Journal entry — BlackLine | BlackLine | per JE policy | Preparer (see posting-method taxonomy) | Independent reviewer | Yes | BlackLine | n/a | pending |
| Journal entry — direct SAP upload | SAP GUI | pending | pending | **reviewer for direct uploads: pending (analysis finding)** | No | pending | n/a | open issue |
| Payment proposal / run | S/4HANA + Citizens | pending — second-approver threshold for ACH unresolved | AP | pending | Partially | Payment-run package | n/a | open issue |
| Close package | Excel/SharePoint | n/a | FSC assembler | Final approver: pending | No | HQ package files | n/a | pending |

**Governance row (Root Cause: no owner for config-after-policy-change):**
| Question | Owner | Status |
|---|---|---|
| Who updates system matrices (Ariba, LinkSquares stages, SAP workflow) after a DoA policy change? | pending | open issue |
| Where is historical policy-approval evidence retained? | pending | open issue |
