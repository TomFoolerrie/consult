# rubric — done for synthetic #4 (the LIVE-MODEL run)

This is the first synthetic where a model sits in the consultant seat and
runs the verbs itself. The human (you) relays, answers the two gates, and
runs the client driver between sittings. Everything below is checked on the
folder after the run — none of it is asserted by hand.

- [ ] every seed source routed, with intent declared, and a scan landed
      (`_sources/scans/SRC-00n.yaml` for each; the CSV's scan is kind
      system-export with a schema section; the thread's is correspondence)
- [ ] a taxonomy shaped from the objective, not the sources
- [ ] the Q2 export wrangled to a canonical (`_synthesis/*.parquet` or CSV if
      DuckDB is unavailable) with `row_id` + `source_ref`, a lineage note, a
      sidecar card — and REGISTERED as a synthesis source with grounds
- [ ] every capture statement cited; the Doyle/policy disagreement recorded
      as a question naming both sources, never adjudicated
- [ ] one full ask round: asks proposed → the human's yes recorded as gates →
      sent → the driver delivers → responses routed via `ask respond` →
      folded in; settlement DERIVED (the receipts ask stays unsettled
      because the answer is a non-answer)
- [ ] at least one worker dispatch, with `consult spend` recorded from the
      reported usage; no spend over budget without a recorded gate
- [ ] `consult render information-request` produced a docx with its card;
      the send gate for it recorded
- [ ] `consult check` clean (no errors; no cards warnings) at the final checkpoint
- [ ] questions.md: 6/6 standings as expected via `consult answer`
- [ ] the session record shows every gate and spend; STATE.md is current
- [ ] the consultant never asked the human anything that was not a spend or a send
