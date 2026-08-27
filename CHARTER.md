# The v2 Charter — the engagement brain and its librarian

**Status: RULED — Amendment A1 recorded 2026-08-26; the build proceeds on the orphan branch `v2-rebuild`**

**Naming (ruled):** the fresh build is **v2** — the human's call: what we shipped as 2.0–2.5.1 never stopped being v1's body and is retroactively the v1 line's final form, frozen as the oracle. Earlier drafts of this document said "v3"; read every remaining "v3" below as the rebuild. The oracle keeps its version numbers; the rebuild's stream starts at `2.0.0-alpha` on the `v2` branch — the streams never mix.
**Origin:** the human's call after run 3 ("distill what we want and build fresh — code is cheap"), plus the vision statement: *"the user doesn't want to babysit this... the human should talk to the client and then come back and ask questions about the client, and the AI just needs to know the answer or how to get it."* Evidence base: run-derived tickets M65–M78, CHANGELOG 2.4.0–2.5.1, docs/retrospective-v0.md, three live Nordhaven runs.

---

## 1. What v3 is, in one paragraph

v2 was a document factory: a thirteen-guard pipeline, a thin coordinator babysitting it, and a human answering gates on the pipeline's schedule. v3 inverts the relationship. **v3 is an engagement brain with a standing steward — the librarian — and its primary interface is a question.** The human owns the client relationship: they talk to the client, understand them, and over that relationship the deliverable shapes emerge and evolve. Between conversations, the human comes back and asks questions about the client — and the brain either knows the answer, from capture, or knows exactly how to get it: re-read a source, dispatch a cheap reader, or put a curated ask to the client through the human. Documents still get produced — but a deliverable is something the brain can *render on demand*, not the thing the system exists to march toward.

## 2. Why the evidence supports this shape

Three live runs produced one governing observation: **the agents' error count is approximately zero; every defect lived in the harness** (M77). The failures were the guard that scoped against an empty ledger, the gate that destroyed what it was promoting, the readiness check that reported CLEAN over placeholders — the *script*, never the judgment. v2's own late doctrine was already walking here: "grow the tenancy, not the harness" (M77), briefs over guards, judgment lands in files the machine reads (M76), the standing taxonomist with its own precedent record. Meanwhile the costliest waste was ownership-shaped: a quarter of run 2's tokens spent confirming absences the taxonomist had already established, because the harness — not the agent — decided what ran (M74). And the human's stated experience of v2 was babysitting. The correction is not a better script; it is putting the standing agent in charge of the script.

The second observation: the declared objective of all three runs — a findings report — was never rendered, while five deliverable definitions, a review loop, two synthesis agents and more shipped untouched by any run. Breadth of pre-built capability bought nothing; the never-run parts are where every run bled. Hence: a general engine, validated deep on a narrow set, grown only on demand.

## 3. The operating model

**The librarian.** One standing agent (strong model) owns the engagement's knowledge: the taxonomy, coverage, the ask register, source routing, curation, and the engagement's running understanding of what the client wants. It is v2's taxonomist grown into the seat v2 gave the orchestrator. It keeps its precedent record (tenure) and its flags; its judgment persists in files, so a new sitting inherits case law instead of re-deriving it (~100k tokens per re-derivation, M77).

**The toolbox.** The deterministic verbs, unchanged in spirit from v2: one writer per file, every write through a verb, folder state the only state, the ledger, registers, coverage as a pure function, aggregate/reconcile/render. The difference is who holds it: the librarian invokes verbs and *delegates* — dispatching smaller, cheaper models for bounded work (drafting a fragment, reading a source for a specific answer, a hygiene sweep) with briefs, cost awareness, and the write boundaries v2 proved. Delegation of duties to smaller models is the librarian's economy, not the harness's schedule.

**The human.** Talks to the client. Brings back what they learned — freeform, conversational — and the librarian folds it into the record. Asks questions; gets answers with honesty about grounds (known / thin / contested / absent — the coverage map and GAP discipline, which v2 already built, surfaced as the answer layer instead of buried under the pipeline). Makes the calls that are genuinely human: what to send the client, what to spend real money on, how the deliverable shape should evolve. The human is never asked to type YAML, never asked to answer a gate the librarian could have answered, and never babysits a loop.

**Documents are demand-driven, and client engagement is continuous — first class.** A document is formulated when, and because, there are questions and needs whose answers the objective requires — never on a schedule, never because a pipeline reached a stage. The information request is the archetype, generalized: the brain generates client engagement *throughout* the engagement — each round of asks earns answers, answers sharpen the record, the sharpened record surfaces the next questions worth asking. The needs-behind-a-document ("what must be true for this deliverable, and what's missing") are therefore first-class state the librarian maintains continuously, not a pre-fill checkpoint. And the return path is deliberately plain: **no markup round-trip** — the client's response is simply put back in, dropped as a source, routed by intake, matched to the asks it answers. One door in, the same door every time.

**The brain's honesty contract.** Every answer carries its standing: *evidenced* (cited to sources), *claimed* (in the record, uncited), *contested* (a lens conflict — both readings shown, never adjudicated), or *absent* (and here is the ask that would close it). "I don't know, and here's how we find out" is a first-class answer — it becomes a curated ask or a cheap source-reading dispatch, at the librarian's proposal and the human's word when it costs something.

**Where the pipeline went.** The route→survey→confirm→fill→reconcile→render sequence still exists — as *the librarian's playbook*, not as the system's spine. Guards become the librarian's checklist; the advisor becomes a tool the librarian consults; gates shrink to the two kinds that are genuinely human: **spends** (a fill wave, an expensive pass) and **client-facing sends** (a document leaving the building). Everything else the librarian decides and records.

## 4. The objective, and why it stays soft

No required fields. The engagement's objective is the librarian's maintained understanding — prose, updated after every client conversation the human relays, versioned in the record like everything else. It is deliberately *not* a schema the user must satisfy on day zero: v2's two-field objective already hard-coded a deliverable name three runs never rendered. The only structured artifact is downstream of the relationship: when a deliverable shape emerges from client conversations, the librarian (with the human) pins it as a definition — and the needs view reads *that*. The objective narrows attention (M41's rule, kept); it never gates capability.

## 5. Deliverables — a general engine, validated deep

The kernel definition language is kept at full strength and is the whole answer to "create any client deliverable": a deliverable is a YAML definition — shape, bindings over declared vocabulary, skin — rendered by a general engine. **Charter property: adding a deliverable is a YAML-sized act.** A new document shape means a new definition and at most one view builder; if it ever requires touching the engine, that is a v3 bug by definition.

What ships pre-written is a different question, and the evidence is blunt: every v2 definition that no run rendered was broken or unserviceable in ways tests didn't catch. A definition that has never met a live engagement is a liability wearing a capability's name. So v3.0 ships **two live-proven-or-provable definitions** — the information request (the ask loop's front door, proven in run 3) and the findings report (the thing three runs declared and never delivered) — and the third deliverable is written the week a client relationship produces its shape, which is exactly when it gets exercised. Deliverable shapes are expected to *evolve*: the definition language must make amending a shape as cheap as pinning one.

## 6. What carries over from v2 (proven live)

The kernel language and four-stage loading · process-step capture ("capture is the brain; every document is a render over it") · folder state as the only state · one writer per file; every write a verb · the engagement ledger (central, SRC minting, consumption credit) · the ask loop end to end · coverage as a pure function + the lens-conflict rule (v0's "single most valuable thing to port back") · flags, tenure, standing tenancy · the drafter contract and minting bars · briefs-first dispatch · cost gates that COST, never SCOPE · humans never type YAML · `done` (now: any "all quiet" claim) unreachable by damage · git checkpoints as the recovery substrate, covering the whole engagement from day one · session records written by the machinery, not by virtue.

## 7. What dies

v1 wholesale (activity type, aliases, per-area sources, compat gate, the v1 taxonomy agent) · the thirteen-guard advisor as the seat of control (demoted to a librarian's tool) · the thin-coordinator orchestrator role itself · `desktop-procedure` as shipped ("honestly unserviceable", M66) · the synthesis agents consult-dependencies/consult-raci (structurally unreachable, M71; their content is in the IPO edges) · the review-kit loop, permanently (~3,300 never-exercised lines; ruled D4 — client responses are put back in as source drops, no markup round-trip) · matrix, agenda, research pass, consolidator as shipped (return on run demand, ticket-first) · migrate_sections, split_doc, dead re-exports, milestone archaeology in comments · hand-rolled CLI inconsistency (one `consult <verb>` entry point).

## 8. The build method — run-first, permanently

1. **v3.0 is the librarian + toolbox + the two definitions, and nothing else.** Done is ruled by D8: several synthetic engagements (Nordhaven may be one), each driven librarian-first with the human interacting only as §3 describes — questions, relayed client answers, spend/send calls — each exercising the question interface, a generated round of client engagement with responses put back in, and a demand-driven render; results analyzed across runs; zero hand-edits to engagement state; session records written by the machinery.
2. **Nothing is built ahead of a run's need.** Features enter as tickets whose Origin is a run finding or a human call — the M65–M78 pattern made the default.
3. **The v2 repo freezes at 2.5.1 as the oracle.** Behavior questions defer to it until the human rules otherwise; deferred subsystems are ported from it against its tests when demanded.
4. **Question-answering is exercised from day one:** part of run 4's definition of done is the human asking real questions about Nordhaven and getting grounded answers — because that, not the render, is now the product.

## 9. The decisions that are yours

Provisionally ruled by the vision statement (say so if I've over-read):
- **The seat of control**: the librarian owns the engagement; the guard table demotes to its playbook; gates shrink to spends and client-facing sends. *(Your words; this is now the charter's spine.)*
- **The objective**: soft, prose, librarian-maintained; no required fields. *(§4.)*
- **D3 restated**: general engine as a charter property ("YAML-sized act"), two shipped definitions as the validation set, shapes evolve with the relationship. *(Per our exchange.)*

Still open, with recommendations:
- **D1 — central mode only.** *Recommend: yes.*
- **D2 — one capture substrate.** `process-step` (+ `taxonomy-node`) is the brain's only storage shape; `activity` dies with no compat gate. The human's "librarian's choice based on the objective" instinct is honored one level up: the *substrate* is fixed because coverage, conflicts, IPO edges and the question interface all join over it — what the librarian chooses per objective is the deliverable *shapes rendered over it*. *Recommend: yes, with that clarification.*
- **D4 — RULED (2026-08-26): the markup review loop is dead, not deferred.** "It wouldn't be markup — you just put the response back." Client responses re-enter as ordinary source drops: intake routes them, ask-matching credits them. Kits, xlsx round-trip, tracked-changes extract/apply do not exist in v3; the oracle keeps them if a future ruling ever wants them back.
- **D5 — synthesis agents die; any future dependencies/RACI view is a python render over IPO edges.** *Recommend: kill.*
- **D6 — RULED in spirit (2026-08-26): the analyst is core, reframed as the analysis service behind the question interface.** Not a pipeline stage: the human asks an analytical question → the librarian runs the mechanical candidate feeds and dispatches the analyst license over them → proposals land in the findings register → the human accepts/rejects in conversation → accepted findings become citable answers and, when a shape calls for it, a rendered document. Same license and candidate-feed honesty as M39/M49; the trigger is a question, not a milestone.
- **D7 — v3 gets a new repository; consult freezes as the oracle.** *Recommend: new repo.*
- **D8 — RULED (2026-08-26): done means synthetic engagements, plural, analyzed.** Not one Nordhaven pass. v3.0 is exercised against several synthetic engagements (cheap to fabricate: seed sources, an objective, scripted client responses — Nordhaven can be one of them), each driven librarian-first with the human interacting only as §3 describes, and the results analyzed across runs before v3.0 is called done. Each synthetic run must exercise: the question interface with grounded answers, at least one generated round of client engagement with responses put back in, and at least one demand-driven render.
- **D9 (new) — the librarian's autonomy boundary.** With gates reduced to spends and sends, how big may a spend be before it needs your word? *Recommend:* the librarian proposes any dispatch with a cost estimate and proceeds without asking below a per-sitting token budget you set; above it, or for anything client-facing, it waits. Simple, tunable, and keeps "no babysitting" honest without making the first bad day expensive.

---

## Amendment A1 — the rulings (2026-08-26)

- **Naming:** the rebuild is v2; the 2.0–2.5.1 line is retroactively v1's final form, frozen as the oracle.
- **Seat of control:** RULED — the librarian owns the engagement; gates shrink to spends and client-facing sends.
- **Objective:** RULED — soft prose, librarian-maintained, no required fields.
- **D1:** RULED yes — central mode only.
- **D2:** RULED yes — one capture substrate (`process-step` + `taxonomy-node`); shapes rendered over it are the librarian's choice per objective.
- **D3:** RULED as restated — general engine as a charter property ("a new deliverable is a YAML-sized act"); two shipped definitions as the validation set; shapes evolve with the relationship.
- **D4:** RULED — the markup review loop is dead. Client responses are put back in as ordinary source drops.
- **D5:** RULED kill — the synthesis agents die; any future dependencies/RACI view is a python render over IPO edges.
- **D6:** RULED — the analyst is core, reframed as the analysis service behind the question interface.
- **D7:** RULED (overriding the draft's recommendation) — **a fresh orphan branch `v2` in this repository**, not a new repo. Clean tree, same history host; the oracle lives on the existing branches.
- **D8:** RULED — done means several synthetic engagements, driven librarian-first, results analyzed across runs.
- **D9:** RULED as recommended — the librarian proposes every dispatch with a cost estimate and proceeds without asking below a per-sitting token budget the human sets; above it, or for anything client-facing, it waits.
- **Method:** RULED — mock the system out in modules first (stub contracts, no implementations) so the human understands and approves the shape before any implementation is written.


## Amendment A2 — the language ruling and the artifact-comment rulings (2026-08-26)

- **Language:** TypeScript. The engine is TS end to end; lifecycles and
  standings are discriminated unions (illegal states unrepresentable). Python
  remains in exactly one bounded seam: py/render_worker, a docx formatter fed
  a compiled JSON job — it formats, it never thinks. Document output is a
  declining priority; the hot path is YAML in, grounded answers out.
- **Delegation is economic, not structural** (comment on the knowledge loop):
  the librarian may touch capture files directly under the same minting bars;
  a delegate is dispatched when the task's cost — judged from the objective
  and the deliverable shape — warrants it. Briefs are issued for every unit
  of work, delegated or not.
- **The four loops are two cycles** (comment on the question loop): the brain
  cycle (input → update → output) and the client cycle (the one loop crossing
  the client boundary). Analysis is the brain cycle with a license attached.
- **The assessment license attaches to the activity, not an agent** (comment
  on the analysis loop): analysis.feeds stays a module; the librarian may
  judge feeds itself; the analyst is an optional cost-based delegate. License
  rules bind whoever judges.
- **Ask economy** (comment on the engagement loop): asks are tailored to the
  client relationship; FEW, SIMPLE, ARTIFACT-SHAPED requests (data, policies,
  org chart) are prioritized — one good artifact closes many gaps; clients do
  not answer question lists.


## Amendment A3 — the reassessment (applied 2026-08-26)

- **R1:** derived views are never files. Builders run in-memory at render
  time; the aggregate stage, derived markers, and pending stubs do not
  exist. The run-3 placeholder bug is structurally impossible, and capture
  areas hold only captured knowledge.
- **R2:** the librarian's sitting brief is desk.report — the printable form
  of desk.state. brief.* issues work orders for delegates only.
- **R3:** check.ts is eight capture-quality checks (markers and
  placeholders died with R1; substance folded into grammar).
- **R4:** the CLI loses aggregate; render is one self-contained verb.
- **R5:** library first — every verb wraps an exported function; tests and
  the synthetic harness drive the library in-process, asserting on typed
  results.
- Capture stays markdown; registers/ledger/journal stay YAML (assessed, not
  changed).


## Amendment A4 — the agent-roster rulings (2026-08-26, artifact comments round 2)

- **One delegate, many templates:** drafter/reader/analyst collapse into one
  WORKER agent parameterized by a template (kernel/templates/: mission,
  model tier, write boundary, context contract, return contract, rules).
  The librarian assigns templates from the objective and deliverable shape;
  starter set: procedure-draft, source-read, assessment, data-analysis.
  Adding a work shape is adding a template file. The assessment license
  survives intact as template content.
- **Every contract answers the round of questions:** mission · what it
  needs · context provided · what it returns — now the uniform shape of
  librarian.md, worker.md, and every template.
- **Token asymmetry is a design input:** input is cheap on strong models,
  output is dear. Review-with-edits over regeneration where it wins; the
  boundary is toed deliberately and recorded per spend.
- **Ask economy is a guiding principle, not a rule:** if the objective
  needs something, it needs something.


## Amendment A5 — agents vs templates (2026-08-26, artifact comments round 3)

- **Agents pin model; templates are skills with agency.** The worker
  becomes three CLASSES — worker-haiku, worker-sonnet, worker-opus — thin
  shells pinning only their model. All behavior, boundary, and license come
  from the loaded template. Class and template are chosen independently per
  dispatch; a template carries a recommended class, advisory only.
- **The librarian authors templates.** Ad-hoc, from scratch or as a variant
  of an existing one — always SAVED to <root>/_templates/ before use (never
  run from a prompt), logged in the session record, reusable by later
  sittings. Engagement-authored templates shadow shipped ones by name, the
  same rule deliverable definitions use. brief.ts owns the store.


## Amendment A6 — the naming ruling (2026-08-26): templates are SKILLS

What A4/A5 called templates are renamed skills throughout — they are skills
in the Claude Code sense, with agency: mission, write boundary, context
contract, return contract, rules, recommended worker class. Shipped skills
live in kernel/skills/; librarian-authored skills in <root>/_skills/
(saved before use, logged, reusable; local shadows shipped). brief.ts is
the skill store + composer (skill/skills/saveSkill/compose).


## Amendment A7 — the exorcism (2026-08-26): pick the pieces, drop the fossils

The rot hunt found seven fossils of two dead premises (the folder is the
document; the human is the trust boundary). All removed:

- **ROT-1:** no confirm ceremony, no .proposed/ — the librarian writes
  live; the gates are spends and sends. engagement.scaffold shrinks to
  newFragment.
- **ROT-2:** no manifest.json — membership is the files on disk; ordering
  comes from the taxonomy or the definition at render time. (The manifest
  was cached derived state, and runs 1–2 bled at exactly that boundary.)
- **ROT-3:** no area directory layer — one flat capture/ per engagement;
  partitioning is the taxonomy's job (L1s). Area parameters leave every
  signature.
- **ROT-4:** no holds machinery — "ask first" is a journal commitment the
  librarian records and obeys; consult.yaml, editHold, and the hold verbs
  do not exist.
- **ROT-5:** no signal files — checks return Defects; the session record
  logs that they ran.
- **ROT-6 + the callout ruling:** the engine hard-codes ONE callout kind,
  the QUESTION record (the registers join on it). All other capture
  vocabulary (CONTROL, PAIN POINT, IMPROVEMENT OPPORTUNITY, …) is a
  shipped, engagement-amendable default declared on the type; skills bind
  to declared kinds and carry the minting discipline; they never define
  schema. SCREENSHOT PLACEHOLDER is gone.
- **ROT-7:** display numbering and [[slug]] token resolution move to the
  render seam; capture cross-references are plain slugs, checked as
  mentions (warning).

**The start (the picked pieces):** Phase 1 = types, kernel, engagement
(flat), ledger, asks, journal, coverage, answers, minimal desk+cli —
ending at synthetic engagement #1 (drop, route, capture, ask, respond,
answer with standings). Phase 2 = definitions, views, check, render(+py),
needs, analysis, findings, skills store — ending at the two shipped
definitions rendering and synthetics #2–#3.

## Amendment A8 — the state pad (2026-08-26): the librarian gets a workspace

The ruling: the librarian keeps `<root>/STATE.md` — a scratch pad, a
workspace, a working memory. Free prose, written by the librarian
DIRECTLY (its one direct-write file; everything else still goes through
verbs), never parsed by any machinery, read FIRST at every sitting,
committed by every checkpoint like everything else in the folder.

Why it is first-class: most of the battle is letting the librarian's and
the human's input LIVE ON across sittings. The structured stores each
persist one kind of judgment — tenure holds precedent, flags hold
out-of-lane observations, the session record holds the machinery's audit —
but none of them holds "where I am, what I'm in the middle of, what the
human said last, what I intend next." That is what dies between sittings
and gets expensively re-derived. STATE.md is where it lives.

The division of memory, so the stores don't blur:
- `STATE.md` — the mind's own notes: in-flight work, intentions, the
  human's standing guidance, open threads. Prose, mutable, librarian-only.
- `_journal/tenure.yaml` — settled precedent (rulings, doubts). Verb-written.
- `_journal/flags.yaml` — out-of-lane observations. Verb-written.
- `_journal/sessions/` — the machinery's own audit. Machinery-written.
- `desk.state()` / `report()` — the DERIVED picture, recomputed from the
  folder every call. The engine describes; STATE.md is what the librarian
  thinks about the description.

This names the shape the system has been converging on: one central agent
with a persistent workspace, using tools to expand context and to show it
how we want the work done — and it manages the rest.

## Amendment A9 — the deterministic-workflow distillation (2026-08-26)

The concern: the scripts are prescriptive. The audit ran every
deterministic function through one test — a verb earns its place only as
(1) bookkeeping an agent shouldn't hand-roll, (2) honesty enforcement, or
(3) context expansion. Anything that encodes HOW to work is a script in a
tool's costume: that belongs to skills and the librarian's judgment. v1
scripted because the script was the trust boundary; v2 trusts the
librarian and the engine only guards invariants. The rulings:

- **analysis.ts is DELETED.** The engine no longer pre-declares what kinds
  of thinking exist: the four named analysis verbs (pain-synthesis,
  control-coverage, conflict-support, handoff-friction) become lenses of
  the shipped `assessment` skill; the deterministic residue — select
  records to feed a judgment — is retrieval, which `answers.ground`
  already is. The librarian authors new analyses as skills, never as code.
- **One event, one verb.** A client response no longer takes four verbs
  (route → match → credit → settle): `asks.respond(file, askIds)` does the
  whole motion atomically. Intake's two doors (register/route) merge into
  `route` per D4. `retire`/`unask` merge into `close(reason)`.
- **One derived picture.** coverage.ts and needs.ts fold into desk.ts:
  three modules computing slices of "where are we" was a v1 org chart.
  `state()` carries coverage and needs as sections; the pure reads remain
  exported from the desk.
- **check drops hedges** — word-list policing of prose style is a skill
  rule, not an invariant. Six mechanical checks remain.
- **newFragment is gone** — the fragment format lives in the type
  declaration and the grammar check catches malformed files; a scaffolding
  verb for a trusted agent is ceremony.
- **Flags and tenure FOLD INTO THE STATE PAD** (extends A8). The engine
  never computed on them — they were agent memory in YAML. STATE.md holds
  precedent and out-of-lane observations as sections, under pad
  discipline (close an observation by noting what actioned it). Workers
  return observations to the librarian, who logs them. journal.ts shrinks
  to the machinery-written session record.

Net: 18 modules → 13, the verb count roughly halved, zero workflows in
the engine. Every surviving verb guards an invariant or expands context.

## Amendment A10 — one cycle (2026-08-26)

The ruling: the two documented cycles are the same cycle. The "client
cycle" was the brain cycle wearing a costume — an ask is just an OUTPUT
whose audience is the client (a demand-driven render like any other), and
a response is just an INPUT arriving through the same one intake door as
any source. Needs is a read; respond() is routing. Four loops became two
at the first reading; two become ONE at this one:

    input → update → output

Everything the system does is a turn of that motion. What made the client
path feel separate is not a cycle — it is a GATE: anything client-facing
crosses the human. Gates sit ON the cycle; they are not cycles. The
documentation now shows one cycle with two gates (spends, sends) and the
client as one of the places inputs come from and outputs go to.

## Amendment A11 — the codifications (2026-08-27)

The state-inventory discussion, written down so none of it drifts:

- **The evidenced/claimed line, codified:** EVIDENCED means a skeptical
  reader can follow the citation to an artifact ON FILE in _sources/.
  CLAIMED means asserted with no citable provenance. The line is
  auditability, not truth — a claimed statement is often correct.
  Corollary: a relayed conversation is written up as a note, ROUTED as a
  source (provenance: client), and cited — evidenced by the note, with the
  trail saying exactly that. Claimed is the residue for what has no
  artifact at all.
- **Standings are computed, never stored.** No field says "evidenced".
  Standing is derived at read time from the record's physical shape:
  cited statement → evidenced; uncited → claimed; question naming two
  sources → contested; question with no answering statement → absent.
  The honesty contract is structural, not disciplinary.
- **The three-primitive capture grammar.** The engine prescribes exactly
  three things, each because honesty must be computable: addressable
  units (slugs, local ids), statements that carry machine-readable
  citations, and the question record. EVERYTHING above the grammar — the
  parts, the vocabulary, the atoms, the taxonomy's meaning — is the
  librarian's choice via the engagement-amendable type declarations,
  shaped from the objective. YAML is the shipped default surface, not a
  law: the parse lives in kernel.ts alone, and an alternative surface
  satisfying the grammar is a kernel amendment, not a redesign.
- **understanding.md is renamed OBJECTIVE.md.** The old name sounded
  like a knowledge store and collided with capture. It is the soft
  objective's home: who the client is, what the relationship is
  producing, the framing asks and deliverables are judged against.
  Durable where STATE.md is volatile; about the relationship where
  STATE.md is about the work. It holds NO client facts — those go to
  capture, evidenced.
- **Registers hold no knowledge** (confirmed): v1's fact-register idea
  is dead; a register is lifecycle bookkeeping only (asks, findings).
  The moment a register holds synthesized prose it is a second capture.
- **The analyst split: considered and DECLINED.** A standing analyst's
  benefits — separation of duties, fresh context, skeptical tuning — are
  already delivered per-dispatch by the assessment skill on a worker
  class (fresh context is structural: a worker sees only what the brief
  resolves). Its costs are the org-chart disease. Kept instead as a
  discipline: when the librarian judges its own record directly,
  consequential conclusions get a fresh-context verification dispatch
  before landing as proposed findings.

## Amendment A12 — synthesis sources and the consultant (2026-08-27)

Two rulings:

**1. The steward may register its own work as a source.** What was
_exports/ is renamed **_synthesis/** — the word says what the directory
is: work products the brain has synthesized (rendered deliverables
included), which are now registrable through the same one intake door
and citable like any other source. The guard that keeps this honest:
provenance gains a third class, `synthesis`, and a synthesis source MUST
declare the grounds it was built from — and it NEVER upgrades standing.
A statement citing a synthesis source inherits the standing of the
synthesis's own grounds, resolved through the chain; check verifies
every synthesis source declares resolvable grounds. Self-derived
knowledge becomes first-class; laundering claimed into evidenced by
citing your own summary is structurally impossible. Client-facing
sends still gate exactly as before — synthesis is where work products
live, not a bypass.

**2. The librarian is renamed THE CONSULTANT.** The seat, contract, and
economy are unchanged — the name now matches the job: one standing agent
that stewards the engagement and serves the human's client relationship.
Historical amendment text above stands as written; all living documents,
contracts, and code speak of the consultant.

## Amendment A13 — the pre-build pass (2026-08-27): edge prescriptions out

A final bloat/prescription hunt before the build. The core held; five
edge findings, all applied:

- **P-1: respond() was over-atomic — and dishonest.** Settle means "the
  answer is folded into capture", and folding is work that happens after
  arrival. The one-verb event is ARRIVAL: respond(file, askIds) routes
  and stamps answered (no `filled` param — arrival cannot know what got
  filled); settle(id) returns as the post-fold-in verb; the
  answered-but-unsettled debt does its job in between.
- **P-2: "thin" leaves CoverageStatus.** Thinness is a threshold judgment
  against the objective — the consultant's call, never a constant in
  coverage code. The engine reports what is computable: evidenced,
  claimed, conflicted, outstanding.
- **P-3: audience/artifact are optional on propose().** The ask economy
  is a guiding principle; required schema made it a rule. A pointed
  question the objective demands has no artifact.
- **P-4: theme is optional on findings.propose().** Organization belongs
  to the deliverable definition, not the register.
- **P-5: sent(ids?) can be selective.** The all-accepted sweep assumed
  one big information request — a v1 render-then-mark-all fossil. Sweep
  by default; piecemeal when the relationship's cadence calls for it.
- **P-6 (recorded intention, post-Phase-1):** module docstrings become
  the living truth once code lands; DESIGN shrinks to picture + laws;
  the blueprint artifact is regenerated from the tree, never hand-synced.

## Amendment A14 — the cold-read corrections (2026-08-27)

A fresh-context agent reconstructed the system from the docs alone. It
got the system, actors, stores, walkthroughs, and laws right at high
confidence — and surfaced one real contradiction plus a batch of spec
gaps. All resolved:

- **THE CAPTURE-WRITE RULING (F1, the human, verbatim intent): the
  consultant directly edits capture. Period. Full stop.** Forcing every
  capture edit through a verb means another pass must re-read the source
  and reconstruct the thought process — what is gained in auditability
  is lost in cost and coherence. The one-writer law is REDRAWN by store
  kind: machine-parsed bookkeeping (_sources/, _registers/, _journal/,
  _skills/ via saveSkill) is verb-only; capture/, STATE.md, and
  OBJECTIVE.md are DIRECT writes — the consultant anywhere, workers
  within their skill's write boundary — disciplined by check.run, the
  three-primitive grammar, and checkpoint diffs. Auditability moves from
  the write path to the record's shape, where A11 already put it.
- OBJECTIVE.md is a direct write (same ruling; its gate is the human
  relationship, not machinery).
- route() gains opts {provenance?, grounds?}; grounds required when
  provenance is "synthesis" (F6).
- settle joins the CLI inventory (F5).
- credit()'s semantics defined: filled = slugs whose open content this
  source filled; updated = slugs it corroborated or revised. credit
  (per-source) and settle (per-ask) are INDEPENDENT debts — both
  visible, no ordering imposed (F12).
- Ask.answeredBy becomes a list — one ask may be answered across
  responses (F17).
- CoverageStatus "conflicted" renamed "contested" — one concept, one
  name (F11).
- open-validations deleted from views — a v1 ghost; three shipped
  builders remain (F9).
- The budget's home named: budgetSet appends the budget line to the
  session record; remaining is derived (F13).
- Contradiction repair: EngagementHealth.repair NAMES the repairing
  verb; the CLI refuses all other state-changing verbs while it stands (F14).
- Worker classes pin model + a fixed tool surface (F15); counts and
  labels corrected everywhere (fifteen src files; two root prose files);
  _skills/ added to the stores table; the status line names the real
  branch, v2-rebuild (F3/F7/F16).

## Amendment A15 — _journal/ collapses into _registers/ (2026-08-27)

The ruling: _journal/ was a husk — A9 emptied it of flags and tenure,
leaving one subfolder in a top-level directory. Collapsed: sessions/
moves under _registers/, which now holds ALL the verb-only bookkeeping —
transaction state (asks.yaml, findings.yaml) and the machinery's own
append-only audit (sessions/). The live-state vs audit distinction
lives at the file level, where one-writer-per-file already enforces it.
journal.ts (one function) folds into desk.ts: the desk owns git, the
budget line, and now sessionAppend — the machinery's audit lives at the
desk. Fourteen engine files.

## Amendment A16 — the artifact comment round (2026-08-27)

- **Core laws distilled.** ~20 laws were constraining to read and diluted
  what is actually load-bearing. SEVEN CORE LAWS now lead; everything
  else demotes to corollaries beneath them (nothing deleted — re-ranked):
  1. The folder is the only state; everything derived is recomputed,
     never stored.
  2. Honesty is structural: standings computed from the record's shape;
     the audit trail terminates in _sources/; synthesis never upgrades
     standing.
  3. One writer per file: bookkeeping through verbs; capture and the
     prose files directly.
  4. No workflow lives in the engine — a verb exists only for
     bookkeeping, honesty, or context; how-to-work lives in skills.
  5. Agents pin model; skills carry the agency; delegation is economic.
  6. Two gates only: spends over budget, client-facing sends.
  7. Fail loud: named refusals, contradiction is a state, conflicts are
     recorded — never adjudicated.
- **The shipped skill library grows on the human's direction** ("a good
  library here is going to go a long way — data cleaning, data analysis,
  capture templates"): `data-clean` joins the roster (normalize one
  messy artifact into a clean referenced working file in _synthesis/).
  Capture templates need no new machinery — a capture shape IS a skill
  (procedure-draft variants), authored per engagement.
- Artifact prose simplified per comments (the one-picture notes, the
  dispatch doctrine, the deliberately-absent list, the gates card's
  negative confirmation cut). Full detail stays in the tree: system.md,
  worker.md, DESIGN.md.

## Amendment A17 — intake scan + who-runs-the-verbs (2026-08-27)

- **The intake scanner (the human's proposal, artifact comment):** every
  routed source can carry SCAN METADATA — a summary and key items —
  produced by a cheap model at intake, so the consultant's inventory
  reads scan lines instead of re-opening sources. Mechanism: a shipped
  `intake-scan` skill (recommended class: haiku), dispatched at route
  time as the consultant's standing playbook — NOT engine automation (no
  workflow in the engine). The scan lands on the ledger entry
  (LedgerEntry.scan). The consultant configures it the way it configures
  everything: author a local variant in _skills/ (e.g. a metadata
  template fitted to the objective) and it shadows the shipped skill.
  Deliberately minimal now; grows by skill authorship, never by engine
  change.
- **Who runs the verbs, stated loudly:** the CONSULTANT runs every verb.
  The human never touches the CLI; the human's part is the yes at the
  two gates and the conversation. Park, respond, route, credit — all the
  consultant's hands.

## Amendment A18 — the alignment (2026-08-27): the shape carries the audit, everywhere

An adversarial review judged the surface against the concept and found
the concept ahead of three verbs. Its verdict, accepted in full: three
of our own rulings (A14's shape-not-write-path, A16's one question per
store, law 6's two gates) were stated but not yet applied to the verbs
standing nearest to them.

- **credit() is DELETED (M1).** Consumption is computed, never declared:
  a source is consumed at slug S exactly when a statement in S cites its
  SRC id — corroboration included (adding the SRC to a citation list IS
  corroboration). ledger.status() derives consumed/outstanding from
  capture citations; a fully-cited source auto-retires at checkpoint.
  `touches` is renamed INTENT — the debt declared at route time,
  balanced by derivation, retired by the record's own shape.
- **settle() is DELETED; the ask lifecycle stores four states (M2):**
  proposed | accepted | sent | closed — the events the folder cannot
  show. `answered` and `settled` are computed properties (answeredBy
  non-empty; answering sources cited where the ask's questions live).
  Settlement becomes un-fakeable: you cannot stamp what the capture
  does not show. A13 was right that arrival ≠ fold-in, wrong that
  fold-in needed a verb — it needed a derivation.
- **The desk splits along the store line (M3):** desk.ts is now PURE
  (state, report, coverage, needs; locate/health lives in the snapshot)
  — the module matches its own doctrine. A new record.ts is the
  machinery's hand: checkpoint, sessionAppend, budget, spend.
- **The sends gate gets its mechanism (M4):** record.gate({kind:
  "send"|"spend", what, ruling}) — the human's yes and the crossing,
  in the session record. asks.accept/sent become its ask-shaped
  callers; a render leaving the building is gated the same way. Law 6
  is now auditable, not behavioral.
- **engagement.ts and views.ts dissolve (M5):** capture's joints are
  the grammar and the standing, not v1's three read modules — kernel.ts
  absorbs entities/taxonomy; render.ts absorbs the BUILDERS registry
  (the export stays public so "YAML-sized act" stays honest).
- **Judgment leaks sealed (M6):** absent standings carry the open
  QUESTION's address, not phrased ask text — phrasing is the
  consultant's; findings.byTheme deleted (organization belongs to the
  definition's view builder); no stored status duplicates a field.
- check's touches check widens to the CONSUMPTION check: intent slugs
  exist, synthesis grounds resolve, a retired source is actually fully
  cited — citations are now load-bearing for three modules, and this
  is the check that polices them.

Thirteen engine files. After a fold-in the consultant edits capture,
checks, checkpoints — and state() already shows which sources retired
and which asks settled, because the capture diff IS the credit.
