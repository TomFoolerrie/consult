# M29 — Constitution coverage: enforce the contract-only rules

> **Status: CORE BUILT (v1.15.0) — sweep (Amendment A1, 54 rules) +
> checks 2–4 shipped; Part 2.1 (register checks) still pending, builds
> after M30 per the resequencing below.**
> **Resequenced (system review, 2026-07-30): Part 2.1 (the register
> checks) builds AFTER M30**, not before — it validates entry structure
> only M30's verb creates; building it first means validating freeform
> files. Chain: M28 → M29 (sweep + checks 2–4) → M30 → M29 Part 2.1.
> The system's standing pattern is moving rules from prompt to gate —
> everything it does reliably, it does because a script enforces what a
> contract instructs. This ticket closes the gap for the MUST-rules that
> are mechanically checkable but today live only in agent contracts.

## Part 1 — The rules sweep (do this first; it IS the spec)

Read every agent contract (`agents/*.md`) and skill, list every MUST-rule,
and classify each:

- **enforced** — a reconcile check / notes-bus validation / verb refusal
  already exists (cite it);
- **mechanically enforceable** — becomes a check in Part 2, with its
  ERROR-vs-WARNING call argued;
- **judgment-only** — stays contract-side, with one line on why (the
  gate-gaming rule below).

The sweep's output table goes in this ticket as an amendment, so coverage
is a decision on record rather than an accident of history.

**The gate-gaming rule (what stays OUT):** a check that needs judgment
(one-linking-sentence limits, tone, "did the handoff grow into
documentation") does not go in. A false-positive-prone gate is worse than
a contract rule: drafters write to satisfy the gate instead of the
reader. Reconcile's checks must be ones a drafter can satisfy only by
doing the right thing.

## Part 2 — Checks already agreed

1. **Register references (the engagement-level citation check).**
   Contract says "reference the register, never restate" — nothing
   validates either half. Add: (a) a prose reference naming a register
   that does not exist under `components/_client/registers/` (resolved
   through the M13 shadowing pattern reconcile already uses) is an ERROR
   naming the known registers; (b) a distinctive value that appears in a
   register entry restated in fragment prose is a WARNING naming the
   register ("reference, don't restate"). Restatement matching is
   deliberately conservative (exact distinctive strings — dollar
   thresholds, cutoff phrases — never fuzzy). See M30 for the open
   design question on a formal register reference form.
   **Builds AFTER M30** (see status note), and gains a third half then:
   (c) a prose reference naming a class-CONTEXT entry is an ERROR —
   context entries are never cited by name (the mechanical backstop for
   M30's align-never-evidence rule, moved from prompt to gate per the
   house doctrine).
2. **consult-meta presence** — a DRAFTED fragment (no `unfilled`
   sentinel) with no `consult-meta` block at all silently skips noun
   binding, so the Systems view / Role Dictionary / RACI just omit it —
   invisible today (only unknown slugs warn). ERROR.
3. **Hard-wrap ~80 columns** — the contract rule that anchor matching
   (M12) and the citation scrub's one-newline window (M4) depend on.
   WARNING on prose lines past ~100 cols (tables, code, URLs exempt).
4. **`[[#slug]]` outside a table row** — the number-only form is for Ref
   cells where the title is its own column; in prose it renders a
   cryptic bare number. WARNING with the fix ("use [[slug]]").

## Citation locality — settled here, discussion continuing in M30

`SRC-` citations remain AREA-LOCAL, validated against the area's own
ledger (M22.1 unchanged). The sanctioned crossings are `adopt` (M24 —
the evidence moves, as a hash-stamped local source) and the registers
(shared recurring facts, checked by Part 2.1). A raw cross-area citation
would silently bind to the wrong ledger today (ids collide by
construction: every area has an SRC-004) and would break retirement
accounting, the drafter reading list, and the render scrub. Any change
to this is M30's conversation, not a side effect here.

## Acceptance

- The sweep table exists as an amendment, every MUST-rule classified.
- Each Part-2 check: constructed-violation test + clean-pass test;
  messages carry file:line + the fix (house standard).
- Register checks resolve through client_config's M13 layering (area
  shadows engagement), and say which layer answered.
- No judgment-only rule got a gate (the gate-gaming rule is cited in
  the sweep table for each exclusion).

## Amendment A1 — the rules sweep table (built with the core checks)

Every MUST-rule extracted from `agents/*.md` and `skills/*/SKILL.md`
(2026-07-31 sweep, built alongside checks 2–4). Classifications:
**enforced** (the check/validator/verb refusal is cited), **mech-candidate**
(mechanically enforceable; listed, NOT built — this ticket builds only
checks 2–4), **judgment-only** (stays contract-side; the gate-gaming rule is
the cited reason unless another is named). "Built here (M29)" marks this
ticket's three checks.

| Rule | Source contract | Classification | Enforcement point / reason |
|---|---|---|---|
| Never fabricate systems/paths/thresholds/etc. (evidence discipline) | drafter (agent §rule 1, skill) | judgment-only | needs the sources; a gate can't verify truth (gate-gaming rule) |
| Uncertainty in GAP callouts, never hedges in body prose | drafter (agent §rule 4) | enforced | `check_hedge_prose` (reconcile #15, WARNING) |
| Individuals NEVER named; roles only | drafter, dependencies, raci | enforced | `check_named_individuals` (#7; full name ERROR, token WARNING) |
| Populate the consult-meta slug block | drafter (agent §rule 2) | enforced — **built here (M29)** | `check_consult_meta_presence` (#14, ERROR); unknown slugs already `check_consult_meta` (#5, WARNING) |
| Hard-wrap fragments at ~80 columns | consolidator (anchor rule); drafter house style | enforced — **built here (M29)** | `check_hard_wrap` (#19, WARNING >100 cols; one warning per fragment) |
| `[[#slug]]` only in table Ref cells, never prose | drafter/derived-table convention | enforced — **built here (M29)** | `check_number_only_xref_in_prose` (#20, WARNING; `/`-tokens skipped — M26 already errors) |
| American English, always | drafter (agent §rule 3) | enforced | `check_british_spellings` (#16, WARNING, word list) |
| No pipeline vocabulary ("callout", "fragment", "manifest") in prose | drafter (agent §rule 3) | mech-candidate | word-list check, same shape as the British check; not built |
| Expand acronyms on first use per procedure | drafter (agent §rule 3) | judgment-only | acronym-vs-product-name is a judgment read (gate-gaming rule) |
| Step headings imperative and verb-first | drafter (agent §rule 3) | judgment-only | verb detection is NLP guesswork; drafters would write to the detector (gate-gaming rule) |
| No bare `\|` in table cells (escape as `\\\|`) | drafter (agent §rule 3) | enforced | `check_table_shape` (#17, SHEARED TABLE ROW WARNING) |
| Cross-reference with `[[slug]]`, never number or copied title | drafter (agent §rule 5), dependencies, raci | enforced | `check_baked_numbers` (#12, ERROR) + `check_xref_tokens` (#3, dangling ERROR) |
| Cite `SRC-` ids; never invent one; every procedure cites | drafter (agent §rule 5) | enforced | `check_src_citations` (#9, M22.1 ERROR; documented no-registry boundary) |
| Citations parenthetical-only, never woven into sentence meaning | drafter (agent §rule 5) | enforced-at-render + mech-candidate | final-mode scrub WARNs listing woven survivors; an earlier reconcile-side detector is a candidate |
| External doc sections cited as `§N.N`, never `section N.N` | drafter (agent §rule 5) | enforced | `check_baked_numbers` (#12) catches the bare pattern; `§` form passes |
| No H1 in a fragment (ATX or setext) | drafter, template | enforced | `check_heading_contract` (#11, M22.4 ERROR) |
| Section headings carry title only — never a letter (`### A. Scope`) | drafter (agent + skill) | mech-candidate | regex `^###\s+[A-H]\.\s` on fragment headings; not built |
| Remove the `unfilled` sentinel on first write | drafter | enforced | advisor guard 4 fill predicate + M19 substance check (`check_fragment_substance`, #8) |
| `Detail:` requires `Note:`; CONTROL/SC take `note` only | drafter (M16.3) | enforced | `check_note_detail` (in #2; ERROR / WARNING) |
| Never renumber existing callout IDs on update | drafter | judgment-only | needs prior-run state (git history); folder-snapshot gate has no authority to compare against |
| Update mode = targeted edits, never a full rewrite | drafter, dependencies, raci | judgment-only | "how much changed" vs "what the work order touched" is a judgment diff (gate-gaming rule) |
| Sibling/other-area work: one handoff sentence, never its steps | drafter (scope boundaries) | enforced (advisory) + judgment-only depth | `check_cross_area_ownership` (#18, WARNING); "grew into documentation" is the ticket's named gate-gaming exclusion |
| Never `[[#area/slug]]` (no cross-area numbers) | drafter (M26) | enforced | `check_xref_tokens` (#3, M26 ERROR) |
| Reference engagement registers, never restate their values | drafter (M24) | mech-enforceable — deferred | Part 2.1a/b (register existence ERROR + restatement WARNING), builds AFTER M30 |
| Class-CONTEXT register entries are aligned to, never cited as evidence | M30 §align-never-evidence | enforced-at-verb + contract-side (backstop = Part 2.1c, builds after M30) | the register verb refuses evidence-class use; the citation backstop is Part 2.1c |
| Write the reprofile heading even when the finding is "none" | drafter (termination contract) | enforced | advisor guard 4.5 re-fires on the missing heading — the drift signal IS the check |
| Author only profile-listed callout kinds / inline tags | drafter (M14) | enforced | render strips out-of-profile kinds and WARNs on dangling ids; scaffold bakes `sections:` |
| Body gap refs `[[GAP-NN — label]]` match a callout in the fragment | drafter | enforced | per-fragment dangling-ID check (#2, ERROR); bare `[[GAP — ]]` is BARE GAP TAG (ERROR) |
| Fill every PAIN POINT / IMPROVEMENT field; Severity enum only | drafter (register source) | mech-candidate | required-subfield + enum check per callout kind; not built |
| `Condition:` authored as first line of the step body | drafter | enforced-at-render (partial) + judgment | render hoists a misplaced tag; which steps are conditional is judgment |
| Taxonomy writes only under `_reference/.proposed/` | taxonomy (golden rule 1) | enforced | `scaffold.py --confirm` is the sole promoter; agent has no Bash |
| Registry `description`/`limitations` sourced or blank | taxonomy (hard rule 3) | judgment-only | truth-vs-source needs the transcripts (gate-gaming rule) |
| Slugs kebab-case, unique, set once | taxonomy (hard rule 5) | enforced | manifest v1 schema (`check_manifest_schema`, #1) + XREF grammar |
| New L2 buckets need human approval | taxonomy (hard rule 4) | enforced | confirm-gate mechanics: buckets take effect only via human-run scaffold |
| Tag every source (`touches` real manifest slugs) | taxonomy (hard rule 6) | enforced | `check_touches` (#10, M22.2 ERROR, dual with sources.py load); untouchable source rests at `unresolvable` |
| Never set `hash`/`state`/`consumed` on sources | taxonomy | enforced | scaffold + `sources.py mark-processed` are the sole writers of those fields |
| Every notes item carries `kind:` | taxonomy (notes bus) | enforced | confirm fails loudly on a kind-less item (notes-bus validation) |
| Stay inside the dispatched L1 | taxonomy (hard rule 1) | judgment-only | boundary calls need the sources + client taxonomy read (gate-gaming rule) |
| Consolidator writes no content file; notes only via `consolidate.py note` | consolidator | enforced | tool grant (no Write/Edit) + the note verb is the only writer |
| Every finding evidenced by 2+ procedures | consolidator | enforced | `consolidate.py note` refuses a finding with no `--peers` |
| Never resolve factual conflicts | consolidator | judgment-only | the agent has no sources; no gate can either (gate-gaming rule) |
| Anchors exact, short enough for one line | consolidator | mech-candidate | note-time literal-match validation against the target fragment; apply already degrades to a note |
| 10 findings per category cap, truncation reported | consolidator | mech-candidate | bus-side per-category count per pass; not built |
| Agent views never quote callout IDs outside table rows | dependencies, raci | enforced | `check_quoted_callout_ids` (#13, M22.6 ERROR) |
| Re-emit the `<!-- derived: KIND; writer: W -->` marker | dependencies, raci | enforced | `check_derived_markers` (#4, M22.3 ERROR on missing/mismatched) |
| Exactly one Accountable per activity | raci | mech-candidate | parse the 84 long-form table, count names in the Accountable column; not built |
| RACI long form only (five fixed columns), never role-per-column | raci | mech-candidate | header-shape check on `84_raci.md`; not built |
| RACI cells use canonical `roles.yaml` names only | raci | mech-candidate | cell-name ⊆ registry check; not built |
| Zero-routes forbidden: every intake file ends routed or parked | intake | enforced | folder state is the record; `engagement.py audit` reports unprocessed counts until empty |
| Never excerpt/summarize/merge/split intake documents | intake | judgment-only | reduction is invisible to a gate over copies (gate-gaming rule) |
| Classifier never uses `--new-area` | intake | enforced | `engagement.py route` refuses an unscoped area without the human-only flag |
| Orchestrator keeps context flat (never reads sources/drafts) | orchestrate | judgment-only | context contents are not folder state; nothing on disk to check |
| Stop at human gates; only named verbs cross them | orchestrate | enforced | `human_gate: true` + sole-writer verbs (`accept`, `accept-draft`); advisor re-returns the gate |
| Never pass update slugs as `--filled` | orchestrate (M6 bus contract) | judgment-only | the verb cannot know the dispatch's trigger; documented consequence + `--updated` evidence rule are the guard |
| Render only over a clean reconcile | orchestrate, docx-builder | enforced | advisor gates render on `.reconcile.json` `{basis, clean}` |
| One writer per file (fragments/registry/views/`_client/`) | orchestrate, all agents | enforced | detection: `check_derived_markers` (#4); prevention: dispatch shape + tool grants |

**Tally: 30 enforced (3 of them built here), 10 mech-candidates (not
built), 12 judgment-only, 1 deferred to Part 2.1 (+ the M30
align-never-evidence row, enforced-at-verb with its 2.1c backstop).**
Every mech-candidate above is a future-ticket list, not scope creep into
this one; every judgment-only row cites why a gate would be gamed or has
no authority on disk.
