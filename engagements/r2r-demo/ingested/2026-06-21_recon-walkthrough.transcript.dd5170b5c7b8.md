---
source: fixtures/r2r/recon_walkthrough.txt
source_hash: sha256:dd5170b5c7b8adfbe98df6ec73e7aa4618720b5f223fa9764ef6e29c3312909c
doc_type: transcript
ingested_at: '2026-06-21T21:32:46Z'
ingester: ingest_normalize.py/transcript@1
title: Recon Walkthrough
provenance:
  pages: null
  slides: null
  sheets: null
hints:
  client: null
  systems: []
  people: []
immutable: true
---

# Recon Walkthrough

**Associate:** This session is about the account reconciliation and consolidation side of Record to Report. Walk me through what happens after the close locks.

**SeniorAccountant:** Once the trial balance is final, each entity submits its reconciliations into the consolidation system. We collect data from every ledger and load it centrally before we run eliminations.

**Associate:** How are the intercompany eliminations handled — manually or by the system?

**SeniorAccountant:** The consolidation tool runs the intercompany eliminations automatically based on matched IC accounts. It's a fairly mature, machine-driven step. Topside entries are still booked manually by corporate, though.

**Associate:** And reconciliations themselves — is that a strong process or a weak one in your view?

**SeniorAccountant:** Reconciliations are actually one of our stronger areas. The recon tool is standardized, every account has an owner, and aging items get escalated. I'd call it a real strength relative to the rest of the close.

**Associate:** Is consolidation centralized or does each region run their own?

**SeniorAccountant:** Consolidation is fully centralized at corporate. Regions feed data in, but the actual consolidation and corporate review happen in one central team. One unrelated thing while you're here — the company's annual charitable-giving match program for employees opens next month, and HR asked whether finance can publicize the donation portal to staff.

**Associate:** That charitable-giving match is outside what we're scoping here, but I'll capture it so it doesn't get lost. Thanks for the walkthrough.
