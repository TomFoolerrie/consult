# Assessment evidence adapter

Implemented first attachment point between the separately authored assessment
package and CONSULT. `assessment-evidence.ts` reads assessment's existing
versioned `findings.jsonl` format; it delegates source integrity and excerpts to
the engine. It does not write either ledger, mint source IDs, or run assessment.

## Invocation (for the consultant agent)

From the CONSULT checkout:

```sh
node --experimental-strip-types harness/assessment-evidence.ts \
  --root /path/to/engagement \
  --findings _synthesis/assessment/run-1/ledger/findings.jsonl \
  --format markdown
```

Omit `--format markdown` for machine-readable JSON. Findings paths are relative
to the engagement unless absolute. Output goes to stdout. Exit 0 means these
checks passed; exit 2 means broken references, invalid input, or no active
findings. On per-finding errors, the pack is still emitted so the consultant can
see and explain failures. Do not mistake an output file's existence for success.

The human receives the Markdown review, not instructions to operate this CLI.
The caller may publish it as an ordinary work product with the usual card and
send discipline. Never redirect output over the findings ledger or a registered
artifact; version published review files. This adapter itself writes no files.

## Input contract

The assessment's append-only row schema is retained. Relevant fields:

```json
{"id":"F-001","version":1,"status":"active","type":"observation","evidence_basis":"stated","observation":"Controller reports monthly review","sources":["SRC-001:L1-L2"]}
```

- Highest version wins; retired current rows are omitted.
- Duplicate versions are refused as ambiguous history.
- Invalid JSON or id/version/status refuses the file rather than silently
  discarding rows. Other current-row errors are reported in the review.
- Integrated citations use uppercase engine IDs, with optional inclusive line
  pinpoint: `SRC-001`, `SRC-001:L2`, `SRC-001:L2-L5` (also `L2-5`), or CSV data
  record pinpoint `SRC-002:R7` (one-based after header, not a physical line).
- Bare IDs verify artifact bytes and produce a no-pinpoint warning, no excerpt.
- `stated`, `observed`, and `inferred` remain distinct. No evidence standing is
  invented or inferred from an assessment row's classification.

**No implicit migration:** `src-001` from consult-lint is not assumed to mean
engine `SRC-001`. Register actual source artifacts and retain an explicit mapping
before converting old citations. This adapter refuses legacy IDs deliberately;
the archive's standalone runner still uses its original registry conventions.

## What the human can review

Each active finding carries its observation, evidence basis, version, exact
source excerpts when available, and any failed reference checks. Paths and
registered hashes remain available for audit. Warnings and errors are visible,
not dropped alongside failed citations. Source-authored Markdown/HTML is escaped
in the review rendering.

This helps the consultant answer: **does this excerpt support this observation,
and does the observation distinguish a reported assertion from verified
operation?** The adapter does not answer that professional question for them.

## Boundaries

This adapter checks citation integrity and extracts text. It does NOT replace:

- assessment's taxonomy, severity, proposal or cross-layer validators;
- semantic review, conflict discovery, source coverage or analytical quality;
- source registration or normalized-document provenance (CSV record lookup is
  delegated to the engine; publication uses a separate adapter);
- assessment package installation, runner/shim changes, or standalone migration;
- promotion of local findings into engine findings/capture;
- shared approval or budget accounting.

In particular, passing this adapter is not equivalent to passing the full
assessment. It does not check whether every expected source was examined. It
also does not recursively validate synthesis grounds or label findings with
engine standing.

Source bytes are reverified on each citation request. This is intentionally
simple and stateless, but repeated citations may reread the same file. Add a
per-operation batch facility if real run sizes justify it; do not cache
successful verification persistently or silently assume a whole review is an
atomic snapshot of concurrent work.

## Tests and next attachment

`tests/assessment-evidence.test.ts` exercises version selection, retirement,
legacy/malformed references, changed bytes, missing/empty/broken ledgers,
classification preservation, CLI exit behavior, and human-readable excerpts.
The fixtures are fictional; no private client data is needed.

The tracked package at `packages/consult-assessment/` now invokes this bridge
from `validate.py` in explicit CONSULT mode, retaining local schema/layering
checks. Its runner/shim uses engine sources and citations; CSV procedures use
verified snapshots and the separate `publish-synthesis.ts` adapter for immutable
publication. See the package's `INTEGRATION.md`
for usage, fictional scripted execution results, and remaining boundaries.
