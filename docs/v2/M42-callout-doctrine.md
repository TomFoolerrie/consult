# M42 — The callout doctrine: CTRL, GAP, PAIN — differentiation, sub-steps, interaction

> **Status: SPEC** — origin: user rulings 2026-08-15. The worry: drafter
> judgment on controls/gaps "will be surface level and a lot of noise."
> The resolution reached in discussion, ratified: the WRITE stays with
> the drafter; the judgment about the callout POPULATION moves up
> (surveyor sets the gap agenda before drafting; librarian grooms
> across steps after); the drafter's license narrows to what it can
> judge locally, enforced by minting bars. And the doctrine itself —
> boundary rule vs CTRL, sub-step interplay, the three-way interaction
> contract — must be "clear and understood" in the agent prompts.
> Companions: M33 (the process-step type these callouts live on), M37
> (the surveyor/librarian who gain population-level responsibility),
> M39 (the analyst, where all adequacy judgment already lives), M41
> (the objective block, which this ticket extends to the drafter
> dispatch). Charter: [`README.md`](README.md).

## Part A — The doctrine (normative; the prompts encode THIS text)

### A1. The boundary rule and the CTRL callout are different instruments

The step-granularity rule — a step breaks where **owner, system, or
control changes** — is a SPLITTING HEURISTIC: it tells the drafter where
to cut. It is not an encoding: a boundary does not say WHICH signal
caused it, and reading semantics off structure is prose-scraping, which
this architecture bans. Therefore:

- A control change may CAUSE a step break; the break never RECORDS the
  control. The CTRL callout does — content (who, what against what,
  when, evidence) plus SRC citation.
- Most controls cause no boundary at all (embedded checks inside a
  transformation: same owner, same system). They exist ONLY as callouts.
- Absence must be detectable: "a step with material outputs and no
  CTRL" is the most valuable query in the control landscape (the
  analyst's gap candidates, the matrix's empty cells). It is computable
  only because CTRL is explicit and sometimes absent. Never infer a
  control from a boundary; never omit one because the boundary "already
  shows it." On a pure approval step, the heading names the step; the
  CTRL states the control. Both, always.

### A2. The CTRL minting bar (what earns the prefix)

A CTRL callout is a RECORDED CONTROL STATEMENT, not a controls opinion.
It must carry, from sources, the four fields:

1. **Performer** — who executes the check/approval (role slug),
2. **Comparison** — what is checked/reconciled/approved against what,
3. **Trigger** — when/how often (per invoice, per run, monthly, on
   exception),
4. **Evidence** — where performance is recorded (sign-off, system flag,
   filed worksheet).

A source statement that cannot support the four fields does NOT mint a
weak CTRL: the statement stays as prose in the controls part, plus ONE
GAP asking for the missing control detail. ("The manager reviews
invoices" is prose + a GAP; it is not a control record yet.)
Key-ness, adequacy, and coverage judgments are NEVER the drafter's —
they are the analyst's, behind the human gate (M39).

### A3. The GAP minting bar (what earns the prefix)

A GAP (VALIDATION REQUIRED) names a specific fact whose absence BLOCKS
stating this step correctly — a number, a threshold, an owner, a control
field. "Unconfirmed" alone does not mint. Each GAP carries: the fact,
who can answer it, and what it blocks. The engagement-level "what should
we ask the client" agenda belongs to the SURVEYOR (its information
requests, issued before drafting spends tokens); the drafter's GAP
license is operation-blocking facts found mid-fill, nothing broader.

### A4. PAIN (the easy one, stated for completeness)

PAIN is a voiced observation — friction, worry, risk — captured in the
speaker's framing, attributed, SRC-evidenced. The drafter neither
infers pains nor assesses them. A pain requires someone to have SAID it.

### A5. Sub-steps carry no callouts

Sub-steps are the ordered "how" inside one step — same owner, same
system throughout, by definition. Two consequences, both hard rules:

- **Callouts attach to the STEP** (their declared homes), never to a
  sub-step. A callout ABOUT a moment inside the transformation names
  the sub-step in its body ("at sub-step 3, the clerk matches the PO
  number…"). One home per fact; the sub-step list stays a clean
  procedure.
- **A control with a different performer or system than the step's is
  not an embedded control — it is a boundary signal.** If a CTRL's
  performer field would differ from the step's owner, the granularity
  rule fires: split the step. The doctrine is self-consistent: sub-steps
  cannot host cross-owner facts because cross-owner IS the definition
  of a new step.

### A6. The interaction contract (how the three compose)

- **One fact, one home, cross-referenced by id.** Control content lives
  in the CTRL body; step prose NAMES a control it triggers, never
  re-describes it. A pain about a control ("we always miss the
  tolerance check") does not annotate or weaken the CTRL: record the
  CTRL (what the control is) AND the PAIN (what the speaker said about
  living with it), each citing the other's id. The JOIN is the
  analyst's job — a pain-about-a-control is precisely a finding
  candidate, and pre-joining it at capture would be assessment.
- **Unknown vs painful:** a fact nobody can state is a GAP; a fact
  everybody states and suffers is a PAIN. When a speaker voices worry
  about an unknown, mint both — the question (GAP) and the voiced worry
  (PAIN) — cross-referenced, never merged.
- **A GAP about a control** (missing field per A2) cites the controls
  part it would complete. When the answer arrives (gap-answer note),
  the drafter completes the CTRL and resolves the GAP through the
  existing note path.
- **Population-level responsibilities:** the surveyor owns the
  before-drafting ask agenda (A3); the librarian owns after-drafting
  grooming — duplicate GAPs across steps, a GAP a tagged source likely
  answers, CTRLs missing fields — proposed through the notes bus,
  executed by the owning drafter or the human. The drafter owns only
  its own step's record.

## Part B — Where the doctrine lands

1. **`agents/consult-drafter.md`**: the minting bars (A2, A3), the
   boundary-vs-callout differentiation (A1), the sub-step rules (A5),
   the interaction contract (A6) — written into the existing callout
   sections, in the contract's voice, replacing softer language. The
   drafter dispatch gains the M41 objective block (which deliverables
   make which callouts load-bearing).
2. **`agents/consult-surveyor.md`**: owns the ask agenda explicitly —
   its information requests are THE channel for confirm-with-client
   items; a note that drafters downstream mint only operation-blocking
   GAPs, so the surveyor must not leave known thinness unrequested.
3. **`agents/consult-librarian.md`**: the grooming trigger — callout
   population hygiene (duplicates, likely-answered GAPs, field-less
   CTRLs) proposed via notes, never edited directly.
4. **`scripts/brief.py`**: `drafter_brief` carries the objective block
   (one call to the existing `objective_block`; deterministic, tested).
5. **A worked example** in the drafter contract: one fully-minted CTRL
   (four fields), one refused CTRL (prose + GAP instead), one
   PAIN-about-a-CTRL pair with cross-references — doctrine shown, not
   just stated.

## Acceptance sketch (tests/test_doctrine_m42.py, written first)

- Mechanical prose greps: drafter contract carries the four CTRL
  fields, the "prose + GAP, not a weak CTRL" rule, the
  boundary-vs-callout line, the sub-steps-carry-no-callouts rule, the
  both-never-merged GAP/PAIN rule; surveyor carries the ask-agenda
  ownership; librarian carries the grooming trigger.
- `drafter_brief` output contains the objective block when configured
  (and its absence line when not); v1 drafter-brief bytes unchanged
  when no objective is configured — the block appends, never reshapes.
- The worked example's CTRL callout parses under the process-step
  declaration (kernel.parse_entity over a fixture built from it).
- v1 suite green; zero v1 tests edited.

## Complexity accounting

New state: zero. New gates: zero. New agents: zero. New judgment: zero —
this ticket REMOVES judgment from the drafter (narrower license) and
relocates population judgment to agents that already hold curation
licenses. The bill is prose precision plus one brief block. The review
risk: **doctrine drift between the three prompts** — the normative text
lives HERE (Part A), and the prompts must encode it without paraphrase
drift; the self-review note must diff intent, not wording.

## Deferred (recorded, not built)

- The mechanical hygiene REPORT (deterministic duplicate/field checks
  feeding the librarian candidates, analysis.py-style) — M43 candidate;
  the librarian trigger lands now, its mechanical feeder later.
- CTRL-CANDIDATE two-tier promotion — rejected for now (a lifecycle for
  a recorded fact); revisit only if the minting bar proves insufficient
  on a real engagement.
