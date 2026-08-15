# M42 build plan — the callout doctrine

> Foundation for [`M42-callout-doctrine.md`](M42-callout-doctrine.md).
> Gate: `tests/test_doctrine_m42.py` (skips until the drafter prose
> lands). THE NORMATIVE TEXT IS PART A OF THE SPEC — the prose packages
> encode it without paraphrase drift; where the contract's existing
> voice wants different wording, keep the spec's load-bearing anchors
> (the grep tests name them) and report the tension rather than
> smoothing it. Ground rules as ever.

## Work packages

### WP-D1 — the drafter contract (prose)
Owns `agents/consult-drafter.md` + `docs/v2/notes/m42-drafter-self-review.md`.
Encode A1 (boundary vs callout), A2 (the four-field CTRL bar + weak-CTRL
refusal), A3 (operation-blocking GAP bar; the agenda belongs upstream),
A4 (PAIN restated where it already lives), A5 (sub-steps carry no
callouts; cross-owner control = split signal), A6 (interaction contract,
one-fact-one-home, both-never-merged), and the worked example (Part B5:
a fully-minted CTRL, a refused CTRL that becomes prose + GAP, a
PAIN-about-a-CTRL pair, cross-referenced). Edit the existing callout
sections in place — this contract is long and v1-serving too; keep v1
activity guidance intact where it differs (the doctrine is
process-step-first but the bars apply to both).
Targets: TestDrafterDoctrine (8), TestWorkedExampleParses (1).

### WP-D2 — surveyor + librarian (prose)
Owns `agents/consult-surveyor.md`, `agents/consult-librarian.md`,
+ `docs/v2/notes/m42-population-self-review.md`.
Surveyor: explicit ownership of the ask agenda (its information
requests are THE confirm-with-client channel; downstream drafters mint
only operation-blocking GAPs — unrequested thinness is the surveyor's
miss). Librarian: the grooming trigger (duplicate GAPs across steps, a
GAP a tagged source likely answers, CTRLs missing the four fields) —
proposed via the notes bus, never edited directly.
Targets: TestPopulationOwnership (2).

### WP-D3 — the drafter brief block (code)
Owns `scripts/brief.py` (additive: `drafter_brief` appends the M41
objective block — reuse `objective_block(area)`; when unconfigured the
existing output must remain byte-stable except for the appended absence
line, and every existing section untouched).
Targets: TestDrafterBriefObjective (2).

## Sequencing
WP-D1 ∥ WP-D2 ∥ WP-D3 → close-out (2.1.0-alpha.5): ticket BUILT +
amendment, CHANGELOG entry, charter row, version bump.
