# M43 WP-H3 — self-review of the process-step drafting path

Scope: `agents/consult-drafter.md`, new top-level section
`## What you produce — a process step`, placed immediately after the v1
`## What you produce — structure` block (after its two v1-specific `###`
rules) and immediately before `### What earns a callout — the minting bars
(M42 doctrine)`, so the bars visibly govern both paths. One bullet added to
the dispatch-input list in "Your assignment" (the `YOUR UNIT` line). No v1
content deleted, moved, or reworded.

## Intent diff vs spec Part A

| Part A requirement | Written | Note |
|---|---|---|
| Path selected by the dispatch's `YOUR UNIT` line; absent → v1 default | yes | stated in the opening sentence and again in the dispatch-input bullet |
| LAW = parse_entity refusals (labels from declaration, `PREFIX-ALNUM`, prefix↔label agreement, no duplicate ids, well-formed consult-meta) | yes | the five labels are named explicitly, from `kernel/types/process-step.yaml` |
| HOUSE STYLE = everything else, review/reconcile-enforced, still binding | yes | stated with those words, including "the parser will accept a violation, review and reconcile will not" |
| `## <Heading>` matches the manifest | yes | |
| Parts as `### <Title>`, declaration order, title only, no letters/numbers | yes | order copied from the type declaration |
| Scope shape: end-to-end sentence, `Owner:`, `System(s):`, cadence, `[[slug]]` handoffs, one explicit out-of-scope sentence | yes | examples quoted from the fixtures |
| Inputs/Outputs line grammar with real examples; `[[slug]]` for in-area steps, named role/actor otherwise; parenthetical = system/record; prose tail for non-step terminals; lines ARE the dependency arrows | yes | two verbatim example lines, three verbatim prose tails |
| Transformation: one narrative paragraph then `1.`-numbered imperative sub-steps, same owner/system, performer change = split signal citing the M42 bars, no callouts in the list | yes | "Sub-steps carry no callouts" cross-references the callout doctrine rather than restating it |
| Controls/Issues as callout homes; four declared CTRL fields carried as `> - **<Field>:** <value>` sub-fields when sources support them | yes | field names taken from spec Part C (`Performer, Comparison, Trigger, Evidence`) |
| Honest absence is content, cited; approve-exceptions pattern quoted | yes | quoted verbatim, and the phrase "not found" appears |
| `consult-meta` last, `systems:`/`roles:` registry-slug lists | yes | |
| Pointer to the M42 minting bars, bars left in place | yes | two pointers ("see the minting bars below, M42 A5"; "The minting bars below govern") |
| Tight working contract, no tutorial | judged met | ~60 lines for six parts plus the law/style split |

Deliberate additions beyond the literal spec text, both one line each: a
closing paragraph naming which of the contract's global rules still apply on
this path (evidence discipline, nouns, tone, uncertainty-in-callouts,
conflicting sources, final read-through) and which v1-only rules do not (the
seven sections, the inline step tags, `Condition:`). Without it a drafter on
the v2 path has no stated relationship to the rest of the document.

## Fixture conformance

Does the written grammar describe all five
`tests/fixtures/ipo-engagement/components/purchasing/10_*.md` fragments as-is?
**Yes for all five** — heading, six parts in declaration order, Scope shape,
Inputs/Outputs line grammar, Transformation paragraph + `1.` list, callout
homes, `consult-meta` last. Details checked and matched:

- `10_approve-exceptions.md` — the honest-absence Controls part is the pattern
  the path now quotes. Also the only fragment whose Scope names a second
  working role ("Owner: AP Manager, working with the Senior AP Specialist");
  the written rule (`Owner: <Role>.`) accommodates it, as `<Role>` is a role
  statement, not a single slug.
- `10_schedule-payment.md` — Owner line names three roles by responsibility
  ("AP Manager for the proposal, Treasury Analyst for the file, Corporate
  Controller for approval"), and sub-steps 5 attributes two performers
  parenthetically. Same accommodation; see the finding below.
- `10_reconcile-statements.md` — its single Output has no downstream step and
  carries the prose tail plus an explicit "no downstream process in this area
  consumes it" clause; covered by the prose-tail rule. Its out-of-scope
  sentence is phrased as a downstream-silence sentence ("Nothing downstream in
  this area consumes its product") rather than an exclusion — the loosest
  reading of "one explicit out-of-scope sentence" in the corpus.
- `10_match-po.md`, `10_receive-invoice.md` — conform without qualification.
- All five CTRLs are prose-only, zero `> - **<Field>:**` sub-fields. This is
  the spec's stated expectation ("the whole frozen fixture corpus" appears as
  thin-ctrl candidates by design), so it is not a violation of the written
  style — the path says sub-fields are carried "where the sources support
  them", and it says silence about the four facts is the defect, not prose.

### Findings to REPORT, not accommodate

1. **`10_schedule-payment.md` sits at the edge of the same-owner-throughout
   sub-step rule.** Step 5 reads "Upload the file in Chase Connect (Treasury
   Analyst) and release it (Corporate Controller)" — two performers inside one
   sub-step, which the path calls a split signal. The Scope is honest about
   the three owners, and the parenthetical attribution is the mitigation, but
   under the rule as written this step is a candidate for splitting (upload /
   release) or for splitting the step itself. Recorded for the owner of the
   fixture corpus; I did not edit the fixture and did not soften the rule.
2. **The out-of-scope sentence is universal in the corpus but not uniform in
   form** (see `10_reconcile-statements.md` above). The path states the rule
   as an explicit out-of-scope sentence; three fragments say "out of scope"
   literally, two express the boundary otherwise. Left as stated — the rule is
   about the boundary being stated, not about the phrase.

## Verification

- `tests/test_hygiene_m43.py::TestDraftingPath` — 5 passed.
- `tests/test_doctrine_m42.py tests/test_objective_m41.py` — 33 passed (both
  grep this file; anchors intact).
- Full `tests/` — green.
