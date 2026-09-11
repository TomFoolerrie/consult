# Assessment integration — first consumer of the skill contract

Status: **INITIAL TEXT/CSV INTEGRATION COMPLETE — remaining product work explicit.** Current results and examples: `IMPLEMENTATION-STATUS.md`. Read `SKILL-CONTRACT.md` for the general boundary. The supplied ZIP is preserved; a tracked working copy now lives at `packages/consult-assessment/`. See its `INTEGRATION.md` for supported scope, archive identity, and verification results.

Implemented: `harness/assessment-evidence.ts` reads assessment-shaped versioned findings and checks engine-ID citations through `ledger.verifySource` / `sourceExcerpt`. It emits JSON or a human-readable Markdown review. Six adapter tests pass, including CLI behavior. See [`harness/ASSESSMENT-EVIDENCE.md`](harness/ASSESSMENT-EVIDENCE.md) for usage, limitations, and the distinction from full assessment validation. The tracked package's runner now has explicit CONSULT mode: source lookup and shim citations use the engine; validation combines the evidence adapter with local schema/layer checks. Standalone lower-case IDs are deliberately refused in this mode, not silently remapped. Six package tests pass (including standalone-data compatibility), alongside a separate full-demo test; these include a scripted fictional text assessment through revision, analytical layers, fresh-process resume and rendered bundle. CSV procedures now consume verified engine snapshots, use record locators, and publish immutable synthesis with all input hashes declared. Other table formats refuse. `synthetic/engagement-5/run.ts` adds a complete scripted mechanics demonstration with later evidence revising the local finding/theme/recommendation; it is not a live-model result.

## 1. What this integration should demonstrate

A consultant asks for a bounded assessment, reviews a small extraction sample, gives ordinary-language feedback, and receives an inspectable analytical pack. Later they return with new evidence and continue without rebuilding the engagement or operating the internals themselves.

The integration must improve this experience without converting CONSULT into an assessment pipeline. It must also leave a simple source-reading skill simple.

## 2. Ownership mapping

| Assessment concept today | Proposed integrated home | Important distinction |
|---|---|---|
| Registered sources, `src-NNN:Lnn` | Engine source ledger; adapter supplies method-compatible views/locators | One authoritative source identity; source normalization and line mapping need explicit treatment |
| Client profile and engagement objective | Engine `OBJECTIVE.md` for framing; cited capture/source material for client facts | Do not copy factual profile statements into the soft objective merely to satisfy a brief |
| Source groups, pre-reads, dependency waves | Assessment run configuration | Method execution choices, not engagement membership or engine workflow |
| Classification taxonomy and severity scales | Assessment package/run | Distinct from engine process taxonomy; freeze or version per run |
| Findings `F-NNN` | Assessment's local findings ledger | Includes observations, risks, strengths, gaps, open items; not identical to accepted engine judgments |
| Themes `T-NNN` | Assessment's local ledger | Diagnoses and their evidence relationships |
| Recommendations `R-NNN`, initiatives `I-NNN` | Assessment's local ledgers | Method-specific advice and planning, not new engine register types |
| Revision proposals `P-NNN` and author ownership | Assessment's local revision machinery | No need for a global engine proposal queue |
| Selected candidate judgment | Engine findings via consultant handoff | Human acceptance remains explicit; local method completion does not imply acceptance |
| Open items | Local method records, selectively handed to consultant as questions | Not every open item deserves a client ask; consultant curates against objective |
| Figures, tables, annotated narrative | Skill-owned work products, published through engine discovery | Preserve internal IDs and a path to their ledger; don't flatten all lineage into SRC citations |
| Method progress, resume information | Durable assessment run state | Keep out of the consultant's full-time context; surface a concise summary |
| Gates, budget, engagement checkpoint | Existing engine/host facilities where applicable | Local calibration and local revisions require explicit semantics, not duplicate authority |

## 3. The evidence bridge is the first technical seam

Detailed design and selected technical recommendations: [`EVIDENCE-BRIDGE.md`](EVIDENCE-BRIDGE.md). It records the inspected source-reader/validator/registration behavior, proposed shared API, failure contract, and test-first implementation sequence. The general read-only verification/excerpt slice is implemented in the engine, and the separate assessment adapter consumes it for evidence review. The tracked package runner is connected in explicit text/CSV CONSULT mode. Analysis registration uses the engine's `publishSynthesis` contract, not a second registry; CSV records and text lines use distinct locators.

The assessment currently expects line-addressed registered text. CONSULT registers arbitrary source files with uppercase `SRC-` IDs and does not supply an equivalent general line-locator contract. Renaming IDs is not the whole integration.

Questions to resolve:

- Does a reader cite the original document, a normalized text artifact, or both?
- When PDF or spreadsheet input is normalized, how is the mapping back to the original retained?
- How does the assessment validator read the authoritative engine hash and current file path?
- How are citations kept valid when the engine retires a source from `new/` to `processed/`?
- How does an assessment-local item retain its full analytical lineage when promoted to an engine judgment?

Initial recommendation: use a narrow adapter for source lookup and locator verification. Prefer engine IDs end to end if that is a small package change. If a compatibility registry is necessary, make it an explicitly regenerable projection with an unambiguous ID mapping, not a separately edited source registry. Inspect the actual scripts before choosing.

Do not use a summary as primary evidence simply because it is easier to line-number. Derived text needs declared provenance and a verifiable relationship to its original.

## 4. First end-to-end slice

Use fictional close-process material: two interviews, a short policy, and a small transaction export. Plant a disagreement, an unsupported interview claim, a genuine strength, and an unanswered question. Keep expected conclusions separate from the agent's inputs.

### Step 1 — assignment

Human: "Assess audit readiness of the close process. Focus on ownership and reconciliation support. Give me findings and a first narrative, not a finished deck."

Consultant selects the assessment method, confirms professional scope where necessary, uses the sitting budget, checks environment prerequisites, and creates or resumes a method run.

### Step 2 — inputs and sample

Sources enter through CONSULT. The assessment reads them through the evidence adapter. The method selects a coherent first group and produces a small findings review pack containing source excerpts, not commands for the human to run.

Human sees specificity, evidence basis, omissions, and representative classifications. They do not see registry annotation chores or manifest edits.

### Step 3 — correction

Human: "The interview only establishes what they say happens. Also, combine the three ownership observations into a clearer issue."

Consultant records guidance, the method revises through its own writer/ownership rules, and presents a bounded before/after sample. An actual method defect is distinguished from a disagreement about interpretation. Never silently modify prompts and rerun everything just because a validator failed.

### Step 4 — analytical output

Method completes extraction and its local analytical sequence, validates lineage, and produces tables and an annotated narrative. It returns a concise summary, limitations, artifact references, candidate engagement contributions, and a resume reference if needed.

The consultant proposes selected engagement judgments; it does not copy every `F-NNN` into the engine findings register. The pack remains useful even before those proposals are ruled on. Client-facing sends still cross the human boundary.

### Step 5 — fresh sitting and changed evidence

Restart in a fresh context. The human supplies an amended policy that conflicts with a previously used source. The consultant resumes from files, routes the new source, and asks the method to reconsider the relevant material.

Expected result: a visible conflict, an explicit assessment of affected conclusions, and a change summary. No silent overwrite of accepted judgments, no duplicate findings caused by replay, and no claim that the entire assessment is current merely because one artifact was regenerated.

## 5. Review-pack definition

The initial output should be easy to challenge rather than visually elaborate:

1. Assignment, scope, source coverage, and exclusions.
2. A short list of consequential findings with excerpts and evidence basis.
3. Themes with linked supporting observations and counterevidence.
4. Recommendations/initiatives with rationale and unresolved dependencies.
5. Open questions and proposed client follow-up, separated from client deficiencies.
6. Annotated narrative suitable for consultant editing.
7. Changes since the previous review and exact decisions requested.

The archive already supplies many ingredients. Integration work should connect and expose them, not replace them reflexively with new engine schemas.

## 6. Work packages

| Package | Deliverable | Done when |
|---|---|---|
| WP1: Boundary decisions | Agreed ownership table and charter-sensitive rulings | Source authority, taxonomy distinction, review authority, and runtime scope are unambiguous |
| WP2: Evidence adapter | Shared source lookup plus supported locator handling | References survive retirement; changed source content is detected; derived material cannot masquerade as primary |
| WP3: Package/run attachment | Small discovery entry, invocation brief, work location, concise resume summary | Fresh consultant context can find and continue the run without the full method manual |
| WP4: Review and handoff | Review pack plus explicit selected contributions | Human feedback produces traceable revisions; repeating the handoff does not duplicate engine items |
| WP5: Fictional integration trial | Recorded end-to-end run with correction and new evidence | User-facing work is useful; limitations and procedural failures are recorded rather than hidden |
| WP6: Simplification pass | Run-backed changes to redundant ceremony | Removed steps have a demonstrated replacement; one-shot skills do not inherit assessment overhead |

Do not implement all packages before exercising a thin WP2–WP4 path. Keep the first case small enough to inspect every important claim.

## 7. Unresolved tensions to handle deliberately

- **Review gates:** the method has mandatory findings/revision reviews; the engine has two global gates. Decide whether these are optional calibration under consultant control or an explicitly approved method requirement.
- **Runtime:** the external method includes Python analysis/orchestration scripts. Clarify the charter's one-Python-seam scope before importing anything into engine source.
- **Workflow:** assessment's `next` is useful local sequencing, but must not become the engagement's seat of control.
- **Author identity:** local revision ownership survives respawn; engine worker classes identify model tiers. Preserve method author identity in briefs without requiring new engine agent roles for every phase.
- **State and manifests:** durable local method configuration is different from a cached engagement manifest, but that distinction must be ruled rather than assumed.
- **Checkpointing:** avoid nested git repositories and redundant commits. Inspect local checkpoint behavior and choose how it participates in the engagement repository.
- **Dependencies:** archive expects a discovery/registration companion (`consult-lint`) and specific data inputs. Inventory these before describing the ZIP as independently runnable.

## 8. Evidence and inspection status

Reviewed for this draft: engine README/design, relevant skill-composition and grounding/check/render code, consultant instructions, synthetic results; archive skill entry point, runbook, ledger/taxonomy references, human review rubric, and story prompt.

Follow-up inspection covered assessment citation validation, data-source lookup/registration and CSV parsing locations, and engine routing/retirement/consumption. Findings are recorded in `EVIDENCE-BRIDGE.md`. Subsequent work inspected and adapted runner source lookup, validation, shim creation, brief source paths and rerun guidance; bundle generation and local author revisions were exercised with fictional scripted data. Data registration and CSV record locators have since been connected and tested. Remaining product work includes nested artifact discovery, package installation, non-CSV format support, and complete standalone compatibility (some suites require the unsupplied consult-lint companion). Imported documentation is not treated as independent evidence of runtime success.
