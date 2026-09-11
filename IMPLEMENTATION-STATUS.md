# CONSULT + assessment — first integration complete

## Start here

The engine and assessment now work together for **registered text and CSV sources**. This is a completed first mechanical integration, not a declaration that the product is ready for unsupported non-developers.

For a consultant-facing look at the result:

- [Review before new evidence](synthetic/engagement-5/example/review-before-response.md)
- [Updated evidence review](synthetic/engagement-5/example/evidence-review.md)
- [Updated narrative draft](synthetic/engagement-5/example/story.md)

Everything in this example is invented. The analytical choices were scripted to exercise the software; no model was called, no private data used, and no actual approvals were recorded.

## What is now implemented

**Shared evidence:** one engine source identity; full-hash checks; verified text excerpts; CSV data-record citations that work with multiline fields.

**Assessment connection:** the tracked package's explicit CONSULT mode uses engine source lookup, combines local analytical checks with engine evidence checks, and generates the worker shim accordingly. The original ZIP remains unchanged.

**Analysis publication:** verified table snapshots, source IDs and hashes for every actual input, immutable versioned outputs, provenance-collision refusals, and an intake lock preventing concurrent source-ID allocation. Reconciliation includes both inputs and refuses ambiguous keys.

**Review and continuation:** Markdown packs retain evidence basis and display excerpts/errors. Local author revisions preserve earlier versions. A scripted demonstration covers a correction, analytical layers, separate-process resume, bundle rendering, rerun, new evidence, revised conclusions, and source retirement. The method reaches `DONE` using explicitly labelled scripted review decisions, and new evidence reopens review before the second completion.

No assessment-specific theme/recommendation/initiative schema was added to the engine. No new server, port, database, paid model session or client-facing send was introduced.

## Verification

- **163/163 repository tests pass**, including the existing DOCX tests.
- TypeScript checking passes, including the new runnable demonstration.
- All imported Python scripts compile.
- Imported alternate-taxonomy smoke test passes.
- Fictional demonstration runs successfully and leaves a clean, versioned engagement folder.
- Engine check on the demonstration: **zero errors, 30 card warnings** for method internals.

Python testing used an isolated temporary virtual environment, not a system package install. Dependencies are recorded in `requirements-test.txt`. The imported full standalone smoke/loop suites still require the unsupplied `consult-lint` companion; those suites are not claimed to pass. A direct standalone-data regression test is green.

## Reproduce

```sh
npm ci --ignore-scripts
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
PATH="$PWD/.venv/bin:$PATH" npm test
npm run typecheck
PATH="$PWD/.venv/bin:$PATH" npm run demo:assessment
```

The demo creates a new temporary engagement and prints paths to its review, story and results. An explicit output directory must not already exist. The environment commands above are POSIX development instructions, not the intended consultant onboarding experience.

## What the run taught us

### 1. The evidence connection is useful and reusable

Source checks, excerpts, CSV records and source-backed publication are generic engine capabilities. Assessment consumes them without taking ownership of the engagement or introducing another authoritative registry.

### 2. Semantic review is still essential

The demonstration deliberately starts with an overreaching finding (two export rows = two payments), then corrects it and later revises it again when a payment-register extract arrives. Structural checks pass on valid citations; they cannot decide whether the conclusion follows. The visible excerpts and retained revision trail make the professional correction inspectable.

### 3. Method discovery is the next concrete simplification target

The run exposes 30 missing-card warnings because the engine treats local ledgers, prompts, figure specs and intermediate tables as independent work products. This is now observed context noise, not a speculative concern.

Recommended next design: a generic method-run entry card with progressively disclosed internals. It must preserve the engine's discoverability and damage visibility, not hide files behind an unverified manifest. That needs an explicit bounded change; this pass does not silently weaken the current “nothing hidden” rule.

### 4. Input accounting still conflates two purposes

A method can legitimately use a source without needing a duplicate capture of everything it extracted. The integration retains genuine capture targets and does not fake consumption credit. A future source-purpose distinction should account separately for shared knowledge and method use.

## Remaining product work before a non-developer pilot

1. Method entry/discovery and a compact resume summary, reducing internal-file noise.
2. Supported installation/preflight and plain-language recovery; the package is currently repository-relative and agent-operated.
3. A clear human review experience for selecting the lens, correcting a sample, and approving outbound material.
4. A live-model fictional run, followed by a non-developer trial without developer coaching.

Also deliberately out of scope: automatic promotion into engine findings, automatic dependency invalidation, PDF/OCR/spreadsheet normalization, non-CSV table formats, complete legacy-ID migration, and retrospective changes to the engine's existing standing resolver. CSV snapshots are currently in-memory and verification is stateless; large-engagement performance has not been benchmarked.

The source bridge checks artifact integrity and locators. It does **not** prove semantic support, source completeness, currency, or recursive conflict propagation. The filesystem checks/intake lock are operational safeguards, not a sandbox against a hostile local process.

## Technical map

- General design: `SKILL-CONTRACT.md`
- Evidence design and chronological progress: `EVIDENCE-BRIDGE.md`
- Integration mapping: `ASSESSMENT-INTEGRATION.md`
- Package usage/current boundary: `packages/consult-assessment/INTEGRATION.md`
- Engine APIs: `src/ledger.ts`
- Assessment review adapter: `harness/assessment-evidence.ts`
- Generic publication adapter: `harness/publish-synthesis.ts`
- Repeatable demonstration: `synthetic/engagement-5/run.ts`

Deployment remains separate from this implementation: no client-facing sends or paid model runs were performed. Running the demonstration commits only inside its newly created fictional engagement, never the implementation repository.
