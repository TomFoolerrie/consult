# Skill integration contract — design draft

Status: **DESIGN CONTRACT — proposals are not blanket charter rulings.** This document records the design discussion; it does not amend `CHARTER.md`. The initial text/CSV evidence and assessment connection has since been implemented; see `IMPLEMENTATION-STATUS.md` for exact supported behavior and verification.

## 1. Purpose and product target

CONSULT is a continuing engagement engine with many consulting methods attached. Assessment is the first substantial external method to meet it, not the workflow every future skill must follow. The engine and the supplied `consult-assessment.zip` were built separately with eventual integration in mind; differences between them are integration decisions, not evidence of a failed integration.

The user is a capable consultant, not an AI developer. They should frame an assignment, supply permitted material, inspect analysis, correct it in ordinary language, and decide what to send. They should not maintain manifests, repair registries, choose prompt files, or diagnose subagent installation.

A useful intermediate result is enough: sourced observations, candidate findings, themes, follow-up questions, and a defensible first draft. Finished executive presentation design is not the initial acceptance criterion.

Development must not depend on access to private client data. Use invented engagements and non-developer usability trials with fictional material. No private data crosses into development to validate this design.

### Design commitments from the discussion

- Many kinds of skill must attach through clear boundaries.
- Assessment is the first integration example.
- Prioritize practical usefulness to a non-developer before engine consolidation.
- Reduce context noise and procedural burden on the model as well as the human.
- Document proposals and unresolved decisions before implementation.

### Working hypotheses, still subject to decision

- CONSULT owns the continuing engagement and shared source identities.
- Skills own bounded methods and their internal analytical records.
- A small integration surface can coexist with rich skill internals.
- Contributions to shared engagement knowledge are explicit, not automatic duplication.

## 2. Current foundations and gaps

The implementation already supplies most of the conceptual attachment points:

| Concern | Existing surface | Limitation relevant to integration |
|---|---|---|
| Skill declaration | `src/brief.ts`: `Skill`, `skill`, `saveSkill` | YAML declarations, not installation of script/reference bundles |
| Invocation context | `brief.compose`, `consult brief` | One printable work brief; no general packaged-method lifecycle |
| Discovery | `src/index.ts`: index, cards, content paths | Must verify nested method work products and avoid indexing every internal row/file |
| Sources | `src/ledger.ts`: route, scan, status | Shared artifact identities; external source/line identifiers need translation |
| Grounding | `src/answers.ts`: ground, cite | Structural provenance, not verification that cited text supports a claim |
| Shared knowledge | `capture/`, declared grammar | Direct consultant or skill-licensed worker edits, not a generic promotion API |
| Engagement transactions | asks and findings modules | Specific shared lifecycles, not containers for all skill-internal records |
| Work products | `_synthesis/`, cards, synthesis registration | Artifacts can be discovered and registered; method run layout is not agreed |
| Machinery | `src/record.ts`, harness | Audit/budget/gates exist; dispatch and actual usage accounting depend on the host |

The existing YAML skill remains the starting point. Do not introduce an independent plugin framework simply to connect the first package.

Current write boundaries and approvals are largely contracts obeyed by the agent, not a filesystem sandbox or an independently authenticated authorization system. Documentation must not imply stronger enforcement than exists.

## 3. Five connection boundaries

### A. Context: supply enough to work, not everything installed

**Engine responsibility:** make objective, guidance, relevant sources/capture, open questions, and existing work products discoverable through stable references and cards.

**Skill responsibility:** declare the inputs it needs and open relevant content. A skill may inspect raw registered sources when its task requires independent extraction; capture is not a mandatory lossy funnel for every method.

**Proposed invocation brief:**

- assignment and intended outcome;
- objective and applicable human guidance;
- exact read/write scope;
- selected references and content paths;
- output location, if any;
- applicable approval and budget constraints;
- skill entry instructions and where to find deeper references;
- resume reference, only for an existing run.

Selection is not exclusion: the worker should have a bounded way to discover additional relevant material, or report that the brief is insufficient. Scope limits must be explicit, not inferred from a missing card.

**Context budget rule:** the standing consultant sees a short skill description and concise run summary. Only the active worker loads the task-specific method. Do not attach all installed skill manuals to every sitting.

**Current detail to revisit:** `brief.compose` scopes indexes by selected stores, not strictly by selected records. Naming one source can still include every source index entry. Measure this before claiming a small dispatch context at scale.

### B. Evidence: shared identities, distinct kinds of judgment

**Engine responsibility:** shared source identity, reference resolution, artifact integrity checks, declared synthesis grounds, and computed engagement standing.

**Skill responsibility:** source interpretation, extraction quality, domain-specific evidence distinctions, and internal analytical lineage.

Rules proposed for every integration:

1. Reuse engine source IDs; do not create a competing authoritative source registry.
2. A local source index may be an adapter projection, not a second authority. Specify how it is regenerated and checked.
3. Preserve source locators such as lines, rows, or pages where available. A locator must identify a particular artifact version. Do not claim the engine validates every locator today.
4. Generated analysis is declared synthesis with its grounds; it is never silently registered as primary client evidence.
5. An output reference does not prove its factual support. Semantic review remains part of the method.
6. Unresolved conflict and evidence limitations must remain visible in outputs that depend on them.

**Two independent dimensions:** engine standing answers whether material is cited, claimed, contested, or absent. Assessment's `stated / observed / inferred` describes the nature of the evidence or interpretation. A cited interview assertion can be structurally evidenced and still only stated by an interviewee. Neither dimension replaces the other.

**Known implementation boundaries to resolve or disclose:** primary-source standing resolution does not itself verify file hashes; synthesis resolution does not propagate a grounding fragment's open conflicts; rendered findings do not automatically display computed standing. These are observations from code inspection, not reproduction-tested defects or new rulings.

### C. Work products: one discovery boundary, many internal methods

**Engine responsibility:** durable work-product location, discoverability, cards, and optional registration as a synthesis source.

**Skill responsibility:** internal schemas, domain taxonomy, scripts, intermediate records, local validation, and analytical sequence.

Proposed layout to test, not an implemented directory contract:

```
_synthesis/
  <skill-name>/
    <run-id>/
      ... skill-owned records and outputs ...
      ... one concise entry summary/card ...
```

Before adopting this layout, exercise `index`, cards, scans, source registration, checkpointing, and the missing-card check against it. A nested method package must not flood the engagement index with scratch files or require a card for every internal ledger fragment. If the current implementation cannot distinguish these, make the smallest generic distinction between published entry artifacts and internal method files.

A skill's durable records are not necessarily redundant derived state: human judgments, revisions, and method decisions may live there. Recomputable summaries should not become independently editable sources of truth.

Do not require method-specific intermediate records to fit engine findings or capture schemas. Do not copy the entire method ledger into capture.

### D. Engagement contributions: explicit handoffs

A skill can produce valuable output without changing shared engagement knowledge.

When it does contribute, use existing lanes:

| Contribution | Proposed handoff |
|---|---|
| New external material | Consultant routes through the existing intake door |
| Factual capture changes | Consultant edits, or a worker edits its explicitly licensed fragment |
| Candidate engagement judgment | Consultant proposes through the findings interface; human acceptance remains distinct |
| Unresolved question | Consultant records the question, then curates an ask if appropriate |
| Work product | Skill writes within its boundary, supplies a card, and declares grounds if registered |
| Client-facing artifact | Consultant obtains and records send approval before it leaves |

A method's completed stage is not human approval. A human's approval of an extraction sample is not blanket acceptance of every later finding or permission to send a report.

The handoff should describe what is new, the supporting references, limitations, and the intended destination. For the first integration this may be a structured result file or returned brief; do not build a new global proposal queue by default.

Avoid repeated promotion on resume. A promoted item needs a recoverable mapping to its skill-run item and engine destination. Whether that mapping lives in the method's record or existing audit detail is an open implementation decision.

### E. Execution: portable obligations, host-specific mechanisms

**Engine/host responsibility:** common accounting and approval facilities, clear execution environment, and capability information.

**Skill responsibility:** its local workflow, prerequisites, progress record, resumability, and recovery instructions.

A one-shot reader needs no run state. A multi-stage assessment may use its own `next` loop. The engine does not become an assessment scheduler.

A small proposed result envelope, with optional fields omitted when unnecessary:

```
summary: what was learned or produced
outputs: paths/references to reviewable artifacts
limitations: gaps, caveats, or failed checks
contributions: proposed shared-engagement updates
resume: where and how to continue, if unfinished
needs-human: a specific professional decision, if needed
```

This is an interface sketch, not a new schema all skills must immediately implement. A short reader response can satisfy it in prose.

For durable methods, report a small state such as working, needs review, blocked, or complete, plus a reason and next action. Do not mirror all local phase state into a second engine scheduler.

A skill should declare required capabilities before expensive execution: executable/runtime dependencies, writable locations, delegation needs, and supported input forms. The Claude Code host adapter should detect missing prerequisites before launch where practical. The current installer and briefs do not provide that complete preflight.

The initial supported host should be named explicitly: **Claude Code**. Do not imply identical execution support in Claude web, Desktop, or other hosts. The consultant may execute directly where the method permits; nested delegation must be tested rather than assumed.

## 4. Minimal obligations versus optional capabilities

All skills:

- have a discoverable mission and bounded authority;
- preserve references and do not invent evidence;
- return usable results or a named limitation;
- obey shared spend/send constraints;
- do not overwrite another store's authority.

Only when relevant:

- a durable run and resume handle;
- internal ledgers or taxonomy;
- authored scripts or multiple agents;
- capture edits or proposed findings;
- document rendering;
- human calibration of the method.

A source reader should remain cheap to author. A multi-stage method should not be artificially reduced to a single prompt. Neither should dictate the other's ceremony.

## 5. Consultant experience and review

The human reviews professional substance, not runtime configuration.

Example interaction:

> Assess the close process for audit readiness. Focus on ownership and supporting evidence.

The consultant confirms scope, selects the method, performs preflight, and presents a small sample with source excerpts. The human can say:

> Too granular. Combine related observations, and stop presenting interview statements as verified operation.

The consultant translates that into a bounded revision, shows representative before/after results, and only then applies the adjustment more widely. Human feedback is recorded as guidance and method-specific decisions, not instructions to hand-edit rows until validation passes.

Review pack target:

- what was assessed and what was not;
- important findings with source excerpts and evidence distinctions;
- themes and recommendations with inspectable lineage;
- contradictions, open questions, and assumptions;
- what changed since the previous review;
- precise decisions requested from the human.

Do not create new mandatory global approval gates for every skill phase. A method may seek calibration; distinguish useful professional interaction from compulsory engine authorization. The assessment's existing review gates need an explicit ruling against the engine's two-gate doctrine before integration.

## 6. Change and continuation

A later source may affect prior work. Do not silently regenerate accepted conclusions or claim universal automatic invalidation is already solved.

First-integration behavior:

1. Route the new source normally.
2. Consultant identifies potentially affected runs using their declared scope and inputs.
3. Skill compares against its prior record and reports affected items and limitations.
4. Consultant decides which shared conclusions need revision or fresh human consideration.
5. Publish a change summary; preserve the previous review trail.

A run should record enough input identity/version information to explain what it used. Start with explicit input references and a checkpoint/version reference, not a global dependency-graph service. Source changes, capture edits, and changes to the method/taxonomy are separate reasons to reconsider results.

## 7. Contract pressure tests

| Example | Uses | Must not be forced to acquire |
|---|---|---|
| Source reader | Brief, source refs, returned material | Run directory, ledger, phase controller |
| Interview preparation | Capture/questions, guide artifact, optional ask suggestions | Assessment taxonomy, accepted findings, analytical pipeline |
| Assessment | Sources/capture, local records, review, resumability, contributions | Ownership of the engine's source registry or engagement schedule |

Acceptance: all three fit without assessment-specific engine verbs, duplicated authoritative sources, or loading all methods into the consultant's permanent context.

## 8. Decisions to resolve next

| ID | Decision | Initial recommendation |
|---|---|---|
| D1 | Packaged scripts/references alongside YAML skills | Keep the current skill declaration as the entry point; determine minimal bundle-resolution support |
| D2 | Method run layout and discovery | Test namespaced `_synthesis/` runs with one published entry point before adopting |
| D3 | Source identifiers and locators | Engine IDs authoritative; preserve method locators through an explicit adapter |
| D4 | Observation versus engagement finding | Keep separate; promote selected judgments explicitly |
| D5 | Method review versus engine gates | No additional global gates; rule the assessment calibration behavior explicitly |
| D6 | Local Python scripts versus the one-Python-seam ruling | Clarify whether the existing ruling binds engine implementation only; do not silently exempt packages |
| D7 | Durable local method state versus no-workflow/no-manifest laws | Permit only if ruled as skill-owned method state, not a new engine workflow or cached engagement authority |
| D8 | Version identity and promotion replay | Record method/input versions and item mappings locally first |
| D9 | Package installation and trust | Define maintainer-installed code and dependency preflight; declarations alone are not a security boundary |

## 9. Implementation order and evidence

1. Resolve ownership and charter-sensitive decisions in this document.
2. Map the assessment's actual schemas and scripts onto these boundaries (see `ASSESSMENT-INTEGRATION.md`).
3. Build a thin adapter for one invented assessment case, not a universal plugin runtime.
4. Exercise a one-shot reader and interview-preparation example against the same contract.
5. Test correction, new evidence, fresh-session resume, and duplicate handoff prevention.
6. Run a non-developer usability session without developer coaching of normal operation.
7. Consolidate only the ceremony those runs show to be redundant.

Measure human correction time, technical interruptions, model procedural mistakes, irrelevant brief context, traceability of important conclusions, and successful resume. Token counts and passing unit tests are supporting evidence, not substitutes for useful consulting work.

This draft is not itself a runtime specification for every proposal. Subsequent implementation is tracked in `IMPLEMENTATION-STATUS.md`: a working package copy is integrated outside engine source, its scripts were exercised on fictional data, and the original ZIP remains unchanged. Discovery grouping, promotion automation and onboarding remain future work.
