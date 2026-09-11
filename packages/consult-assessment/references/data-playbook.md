# Data playbook — the reader as analyst

A tabular source is not read; it is tested. The reader profiles it, picks procedures for what kind of dataset it is, runs them, reads the outputs, and logs findings that cite both the source rows and the analysis. Analysis outputs are registered sources (kind: analysis, derived_from: the data), so a citation into them is as good as a citation into a transcript.

Commands (via the shim): `data profile <src>` · `data run <procedure> <src> [options]` · `data procedures`.

## Always, first
1. `data profile <src>` — learn the columns, their types, blanks, ranges, and what a row looks like. If the profile shows no rows, the header is not on line 1 or the format is odd; look at the first 20 lines with Read and decide.
2. Identify the dataset kind from the columns (below). If it's none of these, still run `group` on the obvious dimension and `outliers` on the amount.
3. Run three to five procedures, not fifteen. Each output is a registered source; noise costs the next reader.

## By dataset kind

**Journal entry listing** (je_no, date, user/preparer, memo, debit/credit or amount)
- `group --by user --amount amount` — who posts what; a preparer who is also the approver, or one person posting most of the volume, is a segregation finding
- `timing --date date --period-end <close> --cutoff <books-closed>` — weekend and post-close postings
- `outliers --amount amount --round 1000` — large and round-dollar entries (estimates, plugs)
- `duplicates --key je_no` and `gaps --seq je_no` — sequence integrity
- `filter --where memo~reclass` / `~adjust` / `~plug` / `~true-up` — manual adjustments

**Bank reconciliation / outstanding items** (date, ref, amount, status)
- `aging --date date --asof <rec date> --amount amount` — stale reconciling items
- `outliers --amount amount` — the big ones
- `recon --other <bank statement src> --key ref --amount amount` — if both sides are registered

**AP / AR aging** (vendor/customer, invoice, date, amount, bucket)
- `aging --date invoice_date --asof <period end> --amount amount` — recompute the buckets; compare to the client's
- `group --by vendor --amount amount` — concentration
- `blanks --cols vendor,invoice,date` — completeness of the record

**Trial balance / GL detail** (account, name, debit, credit, balance)
- `filter --where name~suspense` / `~clearing` / `~opening balance` / `~unapplied` — parking accounts; check whether balances move period to period
- `outliers --amount balance` — what dominates
- `recon --other <prior period TB> --key account --amount balance` — what changed

**Payroll register** (employee, dept, gross, taxes, net, date)
- `duplicates --key employee` within a period; `group --by dept --amount gross`; `timing --date pay_date`
- `blanks --cols employee,dept` — ghost or unclassified employees

**Commission schedule / agent splits** (agent, deal, gross commission, split %, payable, clawback)
- `group --by agent --amount payable`; `outliers --amount payable`; `filter --where clawback>0`
- `recon --other <GL commission expense src> --key deal --amount payable` — the schedule-to-GL tie the client says it does

**Fixed asset register, intercompany matrices, other**
- `group` on the classifying column, `outliers` on the amount, `blanks` on the keys, `aging` on acquisition/settlement dates.

## Writing the finding
- Quantify from the output: "130 of 400 JEs (33%) posted on weekends [src-014:L88 … , src-031:L9]" — source rows first, analysis second.
- One procedure output can yield several findings; one finding should not summarize a whole procedure ("timing analysis shows issues").
- If a procedure finds nothing, that can be a strength: "No duplicate JE numbers in 400 entries [src-032:L6]".
- For xlsx sources there are no physical lines; cite the analysis output only, or ask the orchestrator to export to csv.
- Nothing material after profiling and procedures is still a finding: `observation`, "Reviewed <src> in full via profile + <procedures>; nothing material to scope", citing L1 — that is what closes the source for coverage.

## What this is not
Not a substitute for reading the narrative around the data (the memo column, the notes in the rec). Not statistical assurance — these are analytics that direct attention; the finding says what the numbers show, not what they prove.
