# M42 WP-D1 self-review — the drafter contract vs Part A (intent diff)

Scope: `agents/consult-drafter.md` only. The normative text is
[`../M42-callout-doctrine.md`](../M42-callout-doctrine.md) Part A; this note
diffs INTENT, not wording, and reports the tensions I resolved rather than
smoothing them silently. Line refs are post-edit.

## Where the doctrine landed

| Part A | Landed | Intent check |
|---|---|---|
| A1 boundary vs CTRL | `**A boundary is not a record.**` — lines 510–523 | Full: heuristic-not-encoding, "the break never records the control", most controls cause no boundary, "never infer a control from a boundary", never omit because the heading shows it, approval step = both, always. The absence-detectability argument is kept but restated in reader terms (see friction 2). |
| A2 four-field CTRL bar | `**The CTRL bar…**` — lines 524–542; enumerated fields 528–534 | Full: performer / comparison ("against what") / trigger / evidence, all from sources; weak statement "does not mint"; prose in the controls part + **ONE** GAP; the manager-reviews-invoices example; key-ness/adequacy/coverage are the analyst's (M39). Added one non-spec clause: "never a callout per missing field" — an obvious mis-read of "ONE GAP" the spec leaves implicit. |
| A3 GAP bar | `**The GAP bar…**` — lines 543–553 | Full: a specific fact whose absence BLOCKS stating the step correctly; the four-item example list; "Unconfirmed" alone does not mint; fact / who can answer / what it blocks; the ask agenda is the surveyor's, the drafter's license is operation-blocking facts found mid-fill. |
| A4 PAIN | `**PAIN — the easy one…**` — lines 554–560 | Restated, not rewritten: the contract already carried voiced/attributed/SRC-evidenced correctly (callout grammar at 672–682, "observation, never adjudication" at 886). One tightening: the Severity sentence is re-pointed at the existing per-item rule so the restatement cannot read as a second, softer severity policy. |
| A5 sub-steps | `**Sub-steps carry no callouts.**` — lines 561–573 | Full: same owner/system by definition; "Callouts attach to the STEP … never to a sub-step"; a callout about a sub-step moment names it in the body; a CTRL whose `Performer` differs from the step's owner is a boundary signal → **split**; the self-consistency argument. Extended by one clause the spec states only in A5's prose ("or system") to keep it symmetric with the granularity rule. |
| A6 interaction | `**How the three interact…**` — lines 574–597 | Full: one fact one home cross-referenced by id; step prose names, never re-describes; PAIN-about-a-CTRL = record both, cite each other, never annotate or weaken, the JOIN is the analyst's; unknown vs painful, "mint both", "never merged"; a GAP about a control cites the controls part; gap-answer completes the CTRL through the existing note path (pointed at the `kind: source` / `category: gap-answer` routes already in the contract at lines 66–94). Population bullet is stated as *what is not yours* (surveyor before, librarian after, act on their notes) — the drafter-facing half of A6's last bullet. |
| B5 worked example | `#### The bars, worked` — lines 598–644 (fenced example 604–635, the three rulings 637–644) | Full: CTRL-001 with all four fields as sub-fields; the Purchasing Manager review refused → prose in Controls + GAP-002 naming exactly the missing fields; PP-001 ↔ CTRL-001 cross-referenced by id. Ids are exemplary in the contract's existing style (`CTRL-001`, `PP-001`; `GAP-002` rather than `GAP-01` — see friction 4). |

## v1 sections tightened, not duplicated

- **line 376** — the MAP OF HOMES row for `F. Key Controls` was literally
  "unchanged."; it now names the bar (one CONTROL callout per control that
  clears it, prose for one that does not, no adequacy judgment here). Tightened
  to the bar, not a second copy of the doctrine.
- **lines 393–396** — the "controls live in Key Controls" bullet gains one
  sentence pointing at the bars and repeating that a step break is never itself
  a control record.
- **lines 659–667** — after the v1 `CONTROL` callout template, a paragraph maps
  the v1 field names onto the bar (`Owner` = performer, `Frequency` = trigger,
  label line = what against what, evidence stated in the body) and rules that
  `TBD` is for an open field on a real control record, never a way to mint one
  that has not cleared the bar. No v1 guidance was deleted anywhere in the
  file; the template, the `Type/Frequency/Owner` fields, the long-callout split,
  the seven-section map and every rule under "The non-negotiable rules" stand
  as they were.

## Frictions (reported, not smoothed)

1. **Doctrine before grammar.** The acceptance test extracts the FIRST
   `> **CONTROL — CTRL-` block in the file and parses a fragment around it, so
   the worked example must precede the v1 callout *template* — which is
   otherwise where a reader would learn the label grammar. I therefore placed
   the whole minting-bars section (and its example) BEFORE
   "### Callouts — formalized, each in its home section" and opened it with an
   explicit forward pointer ("the exact label grammar … follow immediately
   below"). Order is now bars → grammar; the contract's own instinct would have
   been grammar → bars. Flagging because it is a test-shaped ordering choice,
   not an editorial one.
2. **A1's "most valuable query in the control landscape".** Part A argues from
   the downstream query (the analyst's gap candidates, the matrix's empty
   cells). The contract bans pipeline vocabulary in *prose the client sees*, and
   its voice elsewhere addresses the drafter about its own file, so I kept the
   argument but phrased it as "the most valuable question anyone asks of this
   material" and dropped the matrix/analyst mechanics. Intent preserved; the
   spec's two concrete consumers are no longer named at that point (they are
   named in the A2 and A6 paragraphs instead).
3. **"the controls part" vs the seven sections.** Part A is process-step-first
   ("the controls part"); this contract serves v1 activity drafting too, where
   the home is `F. Key Controls`. I wrote both homes wherever the phrase
   appears, and opened the section with an explicit both-types scope sentence
   (lines 505–509). The spec's phrase is kept verbatim as one of the two.
4. **Example id widths.** The contract's v1 templates use `CTRL-001`/`PP-001`
   but `GAP-01`/`SC-01`. My refused-control GAP is `GAP-002`, matching the
   example's own three-digit series rather than the v1 GAP template — the ids
   are exemplary and procedure-local either way, but this is a visible
   inconsistency with the template ten lines further down. Left as is (the
   example reads as one coherent set); worth a decision if the widths are ever
   normalized.
5. **Cross-reference mechanics.** A6 requires the CTRL and the PAIN to "cite
   each other's id", but the contract's citation rule (lines 849–862) restricts
   in-prose parentheticals to `SRC-`/`GAP-` ids so final render can scrub them —
   a bare `(PP-001)` in a CTRL body would survive into a client export. I
   therefore carried the cross-references as sub-fields (`- **Reported pain:**
   PP-001` on the CTRL, `- **Control:** CTRL-001` on the PAIN). This is a
   mechanism the spec does not name and no other part of the contract declares;
   if these two field names are meant to be canonical (and therefore
   register-visible), that is a ruling M42 has not made.
6. **Sub-steps have no home in this contract yet.** A5 is written for the v2
   process step's Transformation list; `agents/consult-drafter.md` contains no
   other mention of sub-steps and no process-step sections at all (its body is
   the v1 seven-section document). The rule is therefore stated in the abstract
   here and will need a home when the v2 drafting path is written into this
   contract; until then a v1 drafter reads A5 as a rule about a structure it
   does not produce. Recorded, not resolved.

## Verification

- `python -m pytest tests/test_doctrine_m42.py -q` → `13 passed` (TestDrafterDoctrine 8/8, TestWorkedExampleParses 1/1).
- `python -m pytest tests/test_objective_m41.py -q` → passed.
- Full suite `python -m pytest -q` → green (1 xfail, pre-existing).
