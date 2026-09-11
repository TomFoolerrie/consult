# CONSULT integration — text and CSV

Status: **initial mechanical integration complete; not a live-model or non-developer usability result.** The original `consult-assessment.zip` is preserved unchanged at repository root. This directory is the tracked working copy.

Archive SHA-256: `239e5dfe3b61f26c7c76914f74a6e445127ea00bce99efe7617123340dc3e1f3`

The method's Python scripts stay outside engine `src/` and `py/`. A small Python-to-Node adapter calls shared engine rules rather than duplicating them. The package currently assumes this repository layout; standalone mode remains available, but relocating the integrated package requires additional packaging work.

## What works

- Explicit `mode: consult` manifest, with authoritative engine source IDs.
- Verified source lookup and excerpts through the generated worker shim.
- Engine citation-integrity checks combined with local taxonomy, schema, proposal and analytical-layer validation.
- Versioned assessment findings and author-owned revisions.
- Existing themes, recommendations, initiatives, tables, figures, and narrative bundling.
- CSV profiling/analysis against verified snapshots, with record-level citations.
- Immutable generated-analysis publication through the engine, declaring every actual input and its expected hash.
- Human-readable evidence packs preserving stated/observed/inferred distinctions.
- Fresh-process resume and revisions after new evidence, exercised in a fictional scripted demonstration.

## Manifest (the consultant agent prepares it)

Place the manifest at the engagement root for this example. Paths resolve relative to the manifest; writable method paths must remain under engagement `_synthesis/`.

```yaml
mode: consult
consult_root: .
run: payment-review
context: OBJECTIVE.md
# Select a suitable assessment taxonomy; this remains method-owned.
taxonomy: _synthesis/assessment/payment-review/taxonomy.yaml
# Required for generated analysis publication. These are genuine engine capture
# targets, not tags to invent merely to clear the source-consumption ledger.
capture_intent: [payment-review]
paths:
  ledger_dir: _synthesis/assessment/payment-review/ledger
  workdir: _synthesis/assessment/payment-review/work
  out: _synthesis/assessment/payment-review/out
source_notes:
  SRC-001: {kind: interview}
  SRC-002: {kind: data}
groups:
  - id: G1
    agent: reader-G1
    sources: [SRC-001, SRC-002]
    note: Distinguish reported review practice from evidence of operation.
story_note: Explain what is established, what remains unverified, and the next useful evidence request.
```

Do not specify `registry` in integrated mode; conflicting legacy configuration is refused. `source_notes` is local discovery metadata, not a second source authority. Client facts should be cited source/capture material in pre-reads, not inserted into the soft objective just to satisfy a profile convention.

`next --root` recognizes an unconfigured CONSULT engagement and directs the agent to prepare an integrated manifest instead of creating a consult-lint registry. Use explicit `--manifest` thereafter. Automatic integrated manifest drafting is not implemented.

## Commands

The existing method entry points remain:

```sh
python3 /path/to/consult/packages/consult-assessment/scripts/run.py next --manifest /engagement/assessment.yaml
python3 /path/to/consult/packages/consult-assessment/scripts/run.py render --manifest /engagement/assessment.yaml --op extract --group G1 --format brief
python3 /path/to/consult/packages/consult-assessment/scripts/run.py check --manifest /engagement/assessment.yaml
```

`render` creates the per-run shim, which workers use:

```sh
python3 /engagement/_synthesis/assessment/payment-review/work/assess.py cite SRC-001:L2-L4
python3 /engagement/_synthesis/assessment/payment-review/work/assess.py cite SRC-002:R7
python3 /engagement/_synthesis/assessment/payment-review/work/assess.py data profile SRC-002
python3 /engagement/_synthesis/assessment/payment-review/work/assess.py data run duplicates SRC-002 --key invoice_id
python3 /engagement/_synthesis/assessment/payment-review/work/assess.py validate
```

`cite` returns JSON with verified content and metadata. Bare source references verify bytes but supply no excerpt. Lower-case `src-001` is not automatically converted: it might mean a different source. Legacy migration needs an explicit mapping backed by actual artifacts.

The human receives a review pack, not commands:

```sh
node --experimental-strip-types /path/to/consult/harness/assessment-evidence.ts \
  --root /engagement \
  --findings _synthesis/assessment/payment-review/ledger/findings.jsonl \
  --format markdown
```

## Evidence and CSV contract

Text citations use positive inclusive physical line ranges (`:L2-L4`). CSV citations use one-based **data records after the header** (`:R7`), not physical lines. Quoted multiline cells remain one record; blank physical lines are skipped; empty cells and nonblank empty-valued records are preserved. Header names must be nonempty and unique after trimming, quoting valid, and column counts consistent.

Supported tabular input is a registered `.csv` file, comma-delimited UTF-8. XLSX, TSV, Parquet, markdown tables and normalized-document mappings are not supported by integrated data mode. It refuses instead of falling back to the permissive standalone parser. Unknown requested columns and ambiguous reconciliation keys are also refused.

`data profile` consumes a verified table and returns orientation to stdout; it does not publish a citable source. `data run`:

1. obtains verified input table snapshots from the engine;
2. performs the method's calculation;
3. records source IDs/hashes, procedure, parameters, a run ID and implementation hash;
4. writes a new uniquely named analysis artifact and its card;
5. asks the engine to publish it as synthesis against those exact input versions.

Reconciliation records both sources as grounds. It refuses blank/duplicate keys rather than quietly omitting or collapsing records. Output rows identify which source a record came from.

Publication rechecks every input before registration. Changed input bytes, unknown versions or incompatible content/provenance collisions are refused. A rerun does not overwrite prior evidence. On publication failure, the unregistered artifact remains at the named path for inspection/retry; never assume it is citable merely because a file exists. The authoritative ID is returned only after successful publication.

Input source metadata is not a second registry. Registration is serialized by the engine intake lock; concurrent intake receives a named busy refusal. Do not delete another writer's lock. The standing consultant should avoid other source-ledger edits while intake is running; this is not a general transactional database or hostile-process sandbox.

## Professional review and continuation

Human feedback is ordinary consulting feedback. The agent applies it through author-owned revisions and shows the changed sample. In the current ledger CLI, list-valued `--set` uses **semicolon-separated values**, not JSON array text.

Method review does not authorize client sends or accept engine findings. New evidence is routed through CONSULT, included in the method's scope, and used to reconsider relevant local findings/themes/recommendations. That reconsideration is deliberate work, not an implemented automatic invalidation service.

The fictional demo preserves a before-response pack and later narrows the follow-up after a payment-register extract arrives. It never treats a repeated export row as proof of a duplicate payment.

## Remaining boundaries

- Byte/locator verification is not semantic support, truth, complete source coverage, or recursive propagation of synthesis conflicts.
- Automatic promotion of assessment conclusions into engine findings/capture is not implemented. The consultant uses existing supported lanes.
- All method internals currently appear in engine artifact discovery. The demo produces 30 missing-card warnings for these internals, despite zero check errors. Directory-level method discovery needs a separate, run-backed design; do not hide files or fabricate cards to disguise the issue.
- Method use does not itself satisfy engine capture-consumption debt. Keep genuine capture intent; do not duplicate facts purely for retirement.
- The package is not automatically installed as a discoverable engine YAML skill or Claude plugin. Host installation, preflight UX and non-developer onboarding remain product work.
- Standalone static prompts may use lower-case examples/legacy registry instructions. In integrated mode the package's host-mode notice and generated boundary instructions take precedence; only supplied engine IDs and the integrated shim are authoritative.
- No live model, paid session, client data or actual human approvals were used in the mechanical demonstration.

## Verification

Latest results: **163/163 repository tests pass**, TypeScript checking passes, Python scripts compile, and imported `smoke-house.sh` passes. Tests use an isolated Python environment with the dependencies in `requirements-test.txt`; no system Python packages were installed.

The package tests exercise actual scripts, not just an adapter mock: local validation alongside engine failures, source retirement, author revisions, fresh-process resume, text/record review, two-input analysis, immutable reruns, changed-input refusal, standalone registry compatibility, and a full scripted demonstration through bundle rendering and method `DONE`. Review decisions are explicitly labelled as synthetic; new evidence reopens review before the updated run completes.

The imported full `smoke.sh` stops at the unsupplied sibling consult-lint dependency; `loop.sh` requires that companion to start. Those suites are not claimed green. A direct standalone-data regression test and the alternate-taxonomy smoke suite provide narrower compatibility evidence.

Reproduce the integrated demonstration with `npm run demo:assessment`. See `synthetic/engagement-5/README.md` and the checked-in illustrative review/story snapshots.
