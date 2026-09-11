# Evidence bridge — concrete design

Status: **INITIAL TEXT/CSV IMPLEMENTATION COMPLETE.** Current summary: `IMPLEMENTATION-STATUS.md`. Earlier implementation records below are chronological; remaining design sections distinguish future work. Technical recommendations are selected below so the consultant does not have to adjudicate software details; they are not amendments silently applied to the charter.

### Completed initial integration record

- Added verified CSV snapshots and record locators (`sourceTable`, `sourceRecord`, CLI `source table|record`). CSV parsing uses `csv-parse`; one-based data records preserve multiline fields without claiming they are physical lines.
- Added `publishSynthesis` and a generic JSON-over-stdin publication adapter. Input versions are rechecked; all inputs become synthesis grounds; incompatible provenance/deduplication is refused. Source-ID allocation is serialized with a named-busy intake lock. Published outputs remain immutable.
- Assessment's integrated CSV procedures consume verified snapshots, register uniquely versioned outputs/cards, and declare both reconciliation inputs. Non-CSV tables, missing columns and ambiguous reconciliation keys are refused. Standalone behavior has a direct regression test.
- Added a repeatable fictional demonstration with real engine/package writers, review correction, local analytical layers, process restart, immutable rerun, new evidence/revised conclusions, and source retirement. No model or private data was used.
- Final verification: **163/163 tests pass**, typechecking passes, Python scripts compile, alternate-taxonomy smoke test passes. Python dependencies were installed only into an isolated temporary virtual environment; `requirements-test.txt` records them.
- The demo has zero engine check errors but 30 missing-card warnings for method internals. Discovery noise is documented as a concrete next design target, not silently hidden.

### First slice implementation record (historical)

- `src/ledger.ts`: `verifySource(root, id)` and `sourceExcerpt(root, id, { start, end })`; no new store or module.
- `src/cli.ts`: `source verify SRC-nnn` and `source excerpt SRC-nnn --lines START:END`, JSON output, classified read-only.
- `tests/evidence.test.ts`: six test groups written and observed failing before implementation; all now pass. Coverage includes retirement, duplicate/unknown IDs, missing hashes/files, changed bytes, line boundaries, UTF-8/CRLF, binary controls, traversal/symlink escapes, CLI refusals, and unchanged ledger bytes on reads.
- TypeScript checking passes. Full suite: 143/146 pass; three DOCX tests fail because Python `docx` is not installed in this environment. No system dependency installation was attempted. Project Node dependencies installed with `npm ci --ignore-scripts`.
- Artifact checks return `integrity: sha256-matched`, not a truth/standing verdict. Synthesis grounds are returned as metadata, not recursively verified by this operation.
- Path checks guard lexical and resolved paths. They are not a sandbox against hostile concurrent filesystem mutation.
- No assessment script was imported or changed. CSV locators, registration changes, source-purpose semantics, and changes to `answers.ground` remain unimplemented.

Parent documents: `SKILL-CONTRACT.md`, `ASSESSMENT-INTEGRATION.md`.

### Assessment adapter implementation record

`harness/assessment-evidence.ts` now consumes the assessment's versioned JSONL findings shape. Engine-ID citations resolve through the shared read-only bridge. It preserves evidence basis, rejects ambiguous row history and legacy IDs, reports per-citation failures, and emits JSON or a Markdown review pack. Details: `harness/ASSESSMENT-EVIDENCE.md`.

Six adapter tests were added test-first, including a real CLI subprocess check. Combined with the six engine-evidence tests, all 12 new tests pass. Typechecking passes. Latest full-suite result: 149/152 pass; the same three DOCX-render tests fail for missing Python `docx`. The original assessment runner, source registration, and taxonomy/layer validators are not wired to integrated mode yet.

### Tracked package runner integration record

The supplied ZIP is preserved; `packages/consult-assessment/` is now the tracked working copy. Explicit `mode: consult` connects source discovery, shim `cite`, and local validation to the engine bridge. Four package integration tests exercise actual Python scripts, including a scripted fictional assessment through author correction, analytical layers, process restart, and bundle generation. This is not a live-model result. Integrated data procedures refuse until versioned registration and tabular locators are implemented.

Latest full Node suite: 153/156 pass; the same three missing-`docx` failures remain. Typechecking and imported `smoke-house.sh` pass. Imported `smoke.sh` stops at the missing consult-lint data-registration dependency; `loop.sh` requires that unsupplied companion to start. See `packages/consult-assessment/INTEGRATION.md` for exact scope.

## 1. Decision summary

1. **One identity:** use CONSULT's `SRC-nnn` IDs in integrated skills. No lower-case shadow IDs and no second authoritative registry.
2. **Identity plus location:** represent a citation as source identity plus an optional typed locator. Preserve compatibility with existing bare source citations in capture.
3. **Check evidence at use:** resolve the current ledger path and verify the full registered SHA-256 before supplying excerpts or accepting a citation as structurally valid. Do not rely on a separate check having run earlier.
4. **Version outputs:** a rerun writes a new artifact; never overwrite a registered analysis in place. Exact-byte duplicates may resolve to an existing source, with provenance compatibility checked.
5. **Keep two evidence dimensions:** reference validity and engagement standing do not replace stated/observed/inferred or professional judgment about support.
6. **Register all actual inputs:** multi-source analysis declares all sources it used, not only its first input.
7. **Keep metadata local when it is local:** assessment grouping, topic labels, reader assignments, and classification axes do not become source-ledger fields by default.
8. **Ship a narrow supported slice first:** UTF-8 text excerpts and CSV record references. PDF/OCR, spreadsheet-cell maps, and Parquet locators need explicit later adapters; do not pretend a filename plus a page-like string has been verified.

## 2. What inspection established

### Engine

`src/ledger.ts` stores full SHA-256, root-relative file paths, source ID, intent, provenance, grounds, and scan pointer. `retire` changes the path from `new/` to `processed/` without changing identity. `route` deduplicates by content hash and requires nonempty intent. It does not presently validate every synthesis ground at routing time.

`src/kernel.ts` accepts only bare `SRC-<digits>` in statement `cites`. It does not accept line-qualified citation strings. `src/answers.ts` derives primary standing from the ledger entry without verifying bytes in that call. `src/check.ts` separately checks source integrity.

Consumption in `ledger.status` is derived from capture citations against declared fragment intent. Use by a skill ledger currently earns no capture consumption credit.

### Assessment package

- `scripts/common.py` defaults to lower-case three-digit `src-` citation syntax; other call sites also hard-code that convention.
- `scripts/validate.py` expects a consult-lint registry with `sources`, active status, relative file path, truncated hash (`sha`, first 16 hex characters), and cached line count.
- The validator checks active file hashes, but its line bound check uses registry metadata. The current pattern/check does not comprehensively enforce positive, ordered, actual line bounds.
- `scripts/data.py::register_output` writes the source registry, mints IDs, and supersedes previous entries sharing an output path.
- `cmd_run` writes a predictable analysis filename before registration, so rerunning can replace the bytes behind an earlier citation.
- `register_output` records one `derived_from` source; reconciliation also reads `--other`. That second dependency needs explicit representation in integrated provenance.
- CSV reading uses `csv.reader.line_num`, which identifies the physical end line of the parsed record. Quoted multiline cells mean a record is not necessarily one physical line.
- Assessment citation validation verifies reference structure/integrity; it does not decide whether cited text supports the observation.

These are code-inspection findings, not test-run results.

## 3. The small general engine surface

Extend the existing ledger/library and CLI style rather than adding an evidence microservice or assessment-specific engine module. Names below are sketches to finalize with executable tests.

### Source lookup

```
sourceInfo(root, sourceId)
  -> { id, currentPath, registeredHash, provenance, grounds }
```

Read authoritative metadata on demand. Paths are locations, not identity. No stored `active` mirror or cached path in a skill may override the ledger.

### Citation verification and excerpt

```
verifyCitation(root, reference)
  -> checked identity + locator + integrity result

sourceExcerpt(root, reference)
  -> checked reference + excerpt + format/locator description
```

Both use the same validation core. Excerpt retrieval must not accidentally bypass integrity checks. Open/read bytes once per request and hash the same bytes used for the excerpt, rather than hashing one read and displaying another. Missing hash is an explicit inability to verify, not success.

Batch support can be a thin convenience: read/hash each unique source once per call. Do not add a persistent verification cache in the first slice.

The shared operation establishes:

- the ID resolves uniquely;
- the current path is an allowed engagement file (including symlink escape checks);
- the bytes match the registered full hash;
- the locator is supported, well formed, and within the actual content;
- the returned excerpt comes from those bytes.

It does **not** establish truth, semantic support, completeness, absence of counterevidence, or currency for a particular engagement question. The result must say what was checked, not simply return `valid: true` with no meaning.

### Derived output registration

Reuse `route` for identity allocation. A generic wrapper, if needed, should:

1. verify declared input identities and compatible evidence references;
2. require nonempty, resolvable synthesis grounds;
3. require a new output path for changed bytes;
4. ensure the output is under the declared work-product boundary;
5. route with `provenance: synthesis`;
6. return the authoritative ID and registration result.

Do not let the assessment adapter allocate IDs or write `_sources/sources.yaml` itself. Check duplicate registration semantics before wrapping: content-hash deduplication currently ignores provenance differences. A requested registration that conflicts with an existing entry's provenance must be explained/refused rather than silently relabeled or presented as a newly grounded synthesis.

No global multi-writer source service is needed for the first integration. Serialize source registration through the consultant/adapter; workers can write disjoint outputs and return registration requests. Parallel source routing needs separate atomicity work before it is promised safe.

## 4. Reference shape

Proposed internal representation:

```json
{
  "source": "SRC-012",
  "locator": { "kind": "lines", "start": 18, "end": 23 }
}
```

For tabular material:

```json
{
  "source": "SRC-013",
  "locator": { "kind": "csv-record", "record": 7 }
}
```

For the first CSV adapter, define record numbering as one-based data records following the header, excluding blank records according to one documented parser rule. Record dialect/encoding assumptions in the analysis run; detect/refuse ambiguous unsupported inputs rather than silently inventing a header. Return column names and values plus physical line span where available. A multiline record must still be one record.

Bare `{ "source": "SRC-012" }` remains useful for artifact-level references. A method may require more precise locators for a particular task; the engine should not demand line ranges for every type of work.

A human-readable form such as `SRC-012:L18-L23` is an adapter presentation, not a reason to inject that string into existing capture `cites`. Initially:

- capture keeps `cites: [SRC-012]`;
- method records preserve the structured locator;
- review packs show excerpts and the precise locator;
- contribution mappings preserve the method record reference.

Do not claim precise locations survive engine promotion unless the mapping is actually retained. A later capture grammar extension can be separately justified; it is not necessary to connect the first assessment.

### Line rules

- Strict UTF-8 for the supported text slice; reject unsupported/binary content.
- One-based, inclusive ranges, positive integers, end >= start.
- Count lines from the actual decoded bytes; do not trust a stored count.
- Define CRLF/LF handling consistently without changing the bytes being hashed.
- A final newline does not invent an extra content line; an empty file has no addressable content lines.
- Never silently truncate a requested out-of-bounds range.

The same rules feed verification, excerpts, and tests.

## 5. Provenance and evidence quality

Example:

```
SRC-010 interview transcript
  -> assessment F-008: "Controller reports reconciliations are reviewed monthly"
     evidence_basis: stated
     precise source excerpt retained
  -> T-002: a diagnosis citing F-008 and other records
  -> selected candidate engine finding
```

A registered transcript makes the observation auditable; it does not verify that the reviews occur. A theme is a method judgment, not a primary artifact. A registered narrative must declare its synthesis grounds.

For an aggregate or reconciliation:

```
SRC-020 ledger extract + SRC-021 reconciliation listing
  -> versioned analysis artifact SRC-022
     provenance: synthesis
     grounds: [SRC-020, SRC-021]
     method record: procedure, parameters, tool version, input hashes
```

Analysis outputs should carry enough procedure detail to reproduce the computation. IDs and hashes belong in provenance; domain claims remain in the analytical record.

Conflicts require an explicit review-pack field/section. The bridge must not advertise general conflict propagation as solved merely because all underlying IDs resolve. The current standing resolver's treatment of synthesis conflicts is a separate engine change to test.

## 6. Source lifecycle and change behavior

### Retirement

A source moved to `processed/` is still citable. Resolve ID -> current ledger path for every operation. No rerun or re-registration is required for a pure move.

### Changed bytes

A registered file edited in place fails verification with the source ID and offending path. Never refresh its hash automatically to make citations pass. A legitimate replacement is a new source artifact and identity; preserve earlier evidence if it is still available.

The engine currently has no full semantic supersession model. Do not translate `processed/` to assessment's `superseded` or assume newest means authoritative. A newer policy can coexist with an older policy relevant to an earlier period.

### Repeated analysis

Use versioned output paths within the method's run boundary. Keep previous bytes and item references. A new analysis does not overwrite a previously accepted conclusion. The consultant receives a delta and decides what needs review.

### Inputs changed during a run

Persist input IDs and hashes in the method run. Before publishing the result, recheck those inputs; report divergence. Recording a new result against new hashes without reconsidering the analysis is not a valid recovery.

## 7. Avoiding a new capture ceremony

The current engine requires source routing intent to name capture fragments; only citations in those fragments satisfy consumption. A rich skill may read a source and produce useful analysis without needing to duplicate its extraction into process-step capture.

**Recommended distinction:** skill input accounting and capture consumption answer different questions.

- Capture consumption: did the intended shared knowledge get recorded?
- Skill accounting: did this method examine its assigned material, and what did it use or omit?

A skill's "read" or "done" flag must not pretend it settled capture debt. Conversely, the consultant must not generate filler statements to retire a source.

For the first thin slice, use genuine capture intent and let unfulfilled capture debt remain visible; the method reports source use separately. Do not fake completion. Before wide rollout, evaluate a generic declaration of source purpose (capture targets and/or method use) with honest separate completion rules. This may change a charter-level assumption, so specify and test it separately rather than quietly making `intent: []` legal everywhere.

This is not a request for the user to choose a schema. The recommended product behavior is: **every input is accounted for, without requiring every useful analysis to become duplicate capture.**

## 8. Assessment adapter changes

1. Add an explicit integrated mode; standalone consult-lint behavior remains separate until deliberately retired.
2. Replace ID-specific regexes and source lookups in integrated mode with shared references/bridge calls.
3. Keep grouping annotations and reader metadata in the method run. A discovery projection can be generated for the existing manifest drafter, but cannot be edited as a source authority.
4. Delegate citation integrity and excerpts to the bridge; keep taxonomy, layering, revision, and evidence-basis checks local.
5. Replace `register_output`'s mint/supersede/write logic in integrated mode with versioned output plus engine registration.
6. Collect all referenced inputs (including reconciliation's `other`) into provenance.
7. Translate review excerpts into user-facing findings packs, not instructions for the human to run `lint.py cite`.
8. Make source accounting and outstanding capture intent visible separately.

Use a small JSON-over-CLI boundary for Python -> TypeScript integration on Claude Code. It respects the existing library-first/CLI architecture and avoids maintaining a second implementation of engine rules in Python. Batch requests can minimize subprocess overhead. No daemon, database, network port, or additional service is required.

Implementation should reside in the repository with tests, not only in a modified ZIP. Keep the supplied archive unchanged as the input snapshot. The package import location and runtime ruling should be settled with the package-attachment work before copying its entire codebase into engine source.

## 9. Failure contract

Named failures should distinguish:

- unknown or duplicate source ID;
- missing/unreadable file;
- missing or malformed registered hash;
- changed content;
- path outside allowed source/work-product scope;
- unsupported encoding/format/locator;
- invalid or out-of-bounds locator;
- unresolved synthesis ground;
- registration/provenance collision;
- unsupported input state (for example ambiguous CSV structure).

The consultant sees a useful translation: "I cannot verify this finding because its cited file changed. The earlier citation needs review." Diagnostics retain the ID/path for the maintainer. Do not hide failures behind an empty excerpt, claimed certainty, or automatic source replacement.

## 10. Executable acceptance plan

Start with tests before implementation, consistent with the existing repository method.

| Test | Required outcome |
|---|---|
| Registered text plus line range | Exact excerpt and full-hash verification |
| Bare artifact citation | Checked source identity/integrity; no invented pinpoint |
| Source retirement | Same ID/reference resolves at new path |
| Missing or edited source | Named failure, not an evidenced excerpt |
| Zero/reversed/oversized line range | Refused before any output is published |
| Empty file, trailing newline, CRLF, Unicode | Documented deterministic line behavior |
| Binary passed as line-addressable text | Named unsupported-format failure |
| CSV with a multiline quoted field | One correct record, not a misleading single-line citation |
| New analysis of two inputs | Both declared as grounds |
| Analysis rerun | Prior registered bytes intact; new version available |
| Same bytes with incompatible provenance | No silent provenance laundering through deduplication |
| Concurrent registration requests | Serialized in first adapter; unsupported concurrency not promised |
| Derived artifact with unknown ground | Refused before ledger mutation |
| Registration followed by consumer failure | Source remains recorded; retry does not mint a duplicate |
| Standalone assessment mode | Existing behavior/tests kept separate from integrated mode |
| Source reader using the same bridge | No assessment taxonomy or local ledger required |

Then exercise the fictional assessment scenario in `ASSESSMENT-INTEGRATION.md` and measure the human's correction work, not only mechanical success.

## 11. Next implementation slice

Build **read-only verified source lookup and text excerpts first**, with temporary engagement fixtures. This supplies immediate review value without changing source lifecycle, capture grammar, or package execution.

Then connect one assessment validation/excerpt path and one simple source reader. Add derived-output registration only after the read path and provenance-collision behavior are tested. CSV locators follow the initial text slice, before claims of tabular integration.

No user decision is needed to proceed with the read-only slice. Source-purpose semantics and method review behavior will be presented as concrete product choices once an example makes their consequences visible.
