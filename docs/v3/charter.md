# The v3 Charter — the engagement brain and its librarian

**Status: DRAFT v2 — reframed around the human's vision statement of 2026-08-26; rulings D1–D9 pending**
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

*Amendment A1 (rulings) — pending.*
