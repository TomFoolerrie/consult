# Assessment evidence review

Reference checks: passed. 2 active findings.

This checks registered bytes and citation locations. It does not establish that a claim is true, supported by its excerpt, complete, or free of counterevidence. Taxonomy and analytical-layer checks are separate.

Review each observation against its excerpt. Distinguish what someone reports from what was independently observed. Flag overreach, missing context, and conflicting evidence.

## F-001 — version 1

The controller reports checking invoices for duplicates before payment.

Evidence basis: stated. Type: observation.

### SRC-001:L2-L3

> The controller reports that invoices are checked for duplicates before payment.
> No completed review evidence was supplied with this interview.

Source file: \_sources/new/interview.md
Registered SHA-256: fba05d8e5de2ada8cc3eb2a3df3bb4f5629dd3b77841a81d07c7c5c549c6a221

## F-002 — version 2

Two exported records share invoice identifier INV-001 and amount 125; whether these represent duplicate payments is unresolved.

Evidence basis: observed. Type: risk.

### SRC-002:R1

> invoice\_id: "INV-001"
> vendor: "Example Supplies"
> amount: "125"

Source file: \_sources/new/payments.csv
Registered SHA-256: e7fb2ba4a8839b12605e01dddd611abcc1982ace150aa787e52e337843259d6a

### SRC-002:R2

> invoice\_id: "INV-001"
> vendor: "Example Supplies"
> amount: "125"

Source file: \_sources/new/payments.csv
Registered SHA-256: e7fb2ba4a8839b12605e01dddd611abcc1982ace150aa787e52e337843259d6a

### SRC-003:L5-L12

> stats: duplicate\_groups=1, rows\_involved=2
>
> \#\# Duplicate keys invoice\_id \(2\)
>
> \| source record \| invoice\_id \| vendor \| amount \| note \|
> \|---\|---\|---\|---\|---\|
> \| SRC-002:R1 \| INV-001 \| Example Supplies \| 125 \| ×2 \|
> \| SRC-002:R2 \| INV-001 \| Example Supplies \| 125 \| ×2 \|

Source file: \_synthesis/assessment/demo/out/analysis/SRC-002-duplicates-91019e3103e04042b1d578f1d0ccffb5.md
Registered SHA-256: 1b07e6d35825650e7e722cbfc26fa9d83965fa465a9786badf84e50f8045d192
