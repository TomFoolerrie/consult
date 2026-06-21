# Review Log

Appended every review round: extracted comments and applied before→after moves, reviewer-attributed.

## Round 1 — extract (2026-06-21T22:09:16+00:00)
- docx: `record-to-report.reviewed.docx` (hash `e91e323f0fb1…`) — 3 comment(s)
  - **[0] Controller** on “The accrual workflow is the primary identified pain point: all accruals are built manually in spreadsheets and re-keyed into the ERP each period. The controller identified this step as the primary close pain point and the most frequent source of late adjustments. The process is entirely manual with no automated upload or ERP-native accrual workflow.”: After our Q3 fix the accrual pain is medium now, not high — please downgrade.
  - **[1] Controller** on “A dual-reviewer control is operated in practice for reconciliations with balances above $50K: a second-level reviewer is required before sign-off. This control is not documented in any policy and is not enforced by system configuration — it exists in institutional memory only.”: This control IS documented — it's control RTR-04 in the SOX matrix. Update the evidence tier.
  - **[2] SME** on “Process Owner: TBD — confirm with process owner. The accrual workflow owner has not yet been identified in source materials.”: Accrual owner is the Assistant Controller, not TBD.

## Round 1 — apply (2026-06-21T22:09:58+00:00)
- docx: `record-to-report.reviewed.docx` (hash `e91e323f0fb1…`) — 3 action(s)
  - **[0] Controller** — `set-lens` on `record-to-report.close`
    - args: `{"node": "record-to-report.close", "lens": "process", "value": "pain_med"}`
    - before: `{"coverage": "partial", "lenses": {"current_state": "present", "process": null, "automation": "human", "capability": null, "operating_model": "local"}, "sop": {"status": "draft", "rev": 1}, "improvement": {"status": "draft", "rev": 1}, "counts": {"improvements": 3, "gaps": 6, "screenshots": 0}}`
    - after:  `{"coverage": "partial", "lenses": {"current_state": "present", "process": "pain_med", "automation": "human", "capability": null, "operating_model": "local"}, "sop": {"status": "draft", "rev": 1}, "improvement": {"status": "draft", "rev": 1}, "counts": {"improvements": 3, "gaps": 6, "screenshots": 0}}`
  - **[1] Controller** — `add-item` on `record-to-report.close`
    - args: `{"type": "improvement", "l1": "record-to-report", "l2": "close", "id": "IMP-0002", "field": {"review_status": "accepted", "requires_human_review": "false", "note_reviewer": "Reviewer (Controller): control RTR-04 documented in SOX matrix — evidence tier upgraded to documentary", "source": "review/RTR-04"}}`
    - before: `{"coverage": "partial", "lenses": {"current_state": "present", "process": "pain_med", "automation": "human", "capability": null, "operating_model": "local"}, "sop": {"status": "draft", "rev": 1}, "improvement": {"status": "draft", "rev": 1}, "counts": {"improvements": 3, "gaps": 6, "screenshots": 0}}`
    - after:  `{"coverage": "partial", "lenses": {"current_state": "present", "process": "pain_med", "automation": "human", "capability": null, "operating_model": "local"}, "sop": {"status": "draft", "rev": 1}, "improvement": {"status": "draft", "rev": 1}, "counts": {"improvements": 3, "gaps": 6, "screenshots": 0}}`
  - **[2] SME** — `add-item` on `record-to-report.close`
    - args: `{"type": "improvement", "l1": "record-to-report", "l2": "close", "id": "IMP-0001", "field": {"owner": "Assistant Controller", "review_status": "accepted", "note_reviewer": "Reviewer (SME): accrual owner confirmed as Assistant Controller"}}`
    - before: `{"coverage": "partial", "lenses": {"current_state": "present", "process": "pain_med", "automation": "human", "capability": null, "operating_model": "local"}, "sop": {"status": "draft", "rev": 1}, "improvement": {"status": "draft", "rev": 1}, "counts": {"improvements": 3, "gaps": 6, "screenshots": 0}}`
    - after:  `{"coverage": "partial", "lenses": {"current_state": "present", "process": "pain_med", "automation": "human", "capability": null, "operating_model": "local"}, "sop": {"status": "draft", "rev": 1}, "improvement": {"status": "draft", "rev": 1}, "counts": {"improvements": 3, "gaps": 6, "screenshots": 0}}`
