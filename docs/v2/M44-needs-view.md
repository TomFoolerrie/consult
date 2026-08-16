# M44 — The Needs View: per-deliverable gaps as a render, and the two-mint GAP

**Status: BUILT** (`2.2.0-alpha.1`, gate 21/21, suite 1144) — from the
2026-08-16 architecture review (decisions D1 + D2, ruled by the human).
Ticket map: this is the first of the review's five (M44–M48). See
Amendment A1 for build friction and open follow-ups.

## Why (the ruling, verbatim in spirit)

The review's engagement lens found the gap machinery NOISY: "too many gaps...
we need to know what gaps matter. The shape of what we need changes on
deliverables — a real gap for a desktop procedure is different than a gap for
an audit readiness assessment." The human's reframing, ratified: gaps should
not live with the drafters — **"it's almost a render step."** An engagement
that starts as audit readiness and later sells other services must be able to
**re-render** its needs when the objective changes.

The follow-on question ("what value does drafter-voiced absence add?") was
settled in chat: a render over the brain can see that something is
*undocumented*, but it cannot see that something was *confirmed not to
exist* — an empty Controls part looks identical in both cases. So the drafter
keeps exactly the absence FACTS a render cannot reconstruct, and loses the
ranking/asking job entirely.

**The two rulings this ticket encodes:**

- **D1 — the needs view.** A per-deliverable gap render over the brain:
  deterministic, read-only, objective-driven, recomputed on demand. Every
  need names the deliverable it blocks. Serviceability is its structural
  feed, deepened; the objective (M41) selects the targets; changing the
  objective changes the render and nothing in the capture layer.
- **D2 — the drafter records absences, never ranks them.** The GAP callout
  shrinks to two mints: a **conflict** (two sources disagree) and an
  **evidenced absence** (a specific fact the held sources do not state, or a
  source affirmatively says does not exist). The GAP's *ask half* dies: it no
  longer carries "who can answer it" or "what it blocks" — blocking is the
  needs view's computation, the ask agenda is a render over it, and priority
  words never appear at capture. "Unconfirmed" alone still does not mint
  (M42's bar stands).

## Part A — the two-mint GAP (normative doctrine amendment)

Amends M42 Part A's GAP bar. Everything not restated stands.

1. **What a GAP is now:** a *recorded fact about the evidence*, never an ask.
   Two mints, exactly:
   - **Conflict** — two held sources disagree on a specific fact. Body: the
     fact, both readings, both `SRC-` citations.
   - **Evidenced absence** — a specific, named fact that the tagged sources
     do not state (source-silence after the read), or that a source
     affirmatively confirms does not exist ("the AP manager confirmed nothing
     checks this"). Body: the fact, and the grounds (the sources read, or the
     confirming citation).
2. **What no longer belongs in a GAP body:** who can answer it, what
   deliverable or operation it blocks, any urgency or priority wording.
   Those are computed downstream (the needs view) or owned elsewhere (the
   surveyor's agenda is now a render — see Part C). A GAP that arrives with
   an ask half is not invalid at parse (grammar unchanged) — the doctrine
   simply stops asking for it, and the librarian's grooming may propose the
   trim.
3. **The generic-thinness rule stands:** "unconfirmed" alone, a general sense
   of thinness, or a fact you could state less precisely — none of these
   mint. The needs view reports undocumented territory structurally; a GAP
   for "we don't know much here" is exactly the noise this ticket deletes.
4. **The CTRL-bar interplay stands** (a weak control statement = prose + one
   GAP for the missing fields): that GAP is an evidenced absence — the
   named missing fields ARE specific facts the sources do not state.
5. **Grammar unchanged.** The `VALIDATION REQUIRED — GAP-` label, id grammar,
   home sections, sub-step rules, PAIN/CTRL interaction contract (M42): all
   stand. This is a minting-bar amendment, not a kernel change.

## Part B — the needs view (machinery)

New module `scripts/needs.py`, in the hygiene.py idiom: engagement-scoped,
read-only, deterministic, candidates-not-verdicts.

### The API

```python
needs(area, deliverable=None) -> list[dict]
```

- **Target selection:** `deliverable` names one installed definition;
  omitted, the targets are the objective's `deliverables:` list
  (`client_config.objective`). No objective configured and no name passed →
  `[]` (the CLI prints the accessor's own "no engagement objective" line —
  a report, never a crash).
- **Entry shape** (every key always present):
  `{"deliverable": str, "kind": str, "need": str, "where": str,
  "grounds": list[str]}` — `need` is one sentence; `where` names the
  binding, node slug, or step slug; `grounds` carries the mechanical basis
  (binding name, coverage status, callout display id, SRC ids).
- **Three feeds, three kinds:**
  1. `binding-unserved` — `definitions.serviceability(defn, area)`, one
     entry per gap string, attributed to its deliverable. The structural
     floor: nothing here is new judgment.
  2. `coverage` — for a target with a `coverage:` binding: every taxonomy
     node the coverage map reports at one of the binding's selected statuses
     (reuse `plan_views._selected_statuses` and `plan_views.node_steps` —
     the `thin` alias expands there and only there). Skipped entirely for a
     deliverable with no coverage binding — the SHAPE of need follows the
     deliverable, which is the point.
  3. `recorded-gap` — every open GAP-kind callout on the area's entity
     fragments (prefixes resolved through the type declaration, never
     typed), attributed to each target deliverable whose bindings bind that
     entity type. These are the two mints surfacing: a conflict or evidenced
     absence blocks any deliverable that renders the entity carrying it.
- **Determinism & discipline:** stable order (deliverable, then kind, then
  document order); two calls byte-equal; zero writes (fingerprint-stable);
  no coverage/status word typed in the module that a binding did not supply
  (the M36 shape-audit rule).

### The CLI and the view

- `python3 scripts/needs.py <area> [--deliverable NAME]` prints the render:
  a heading per deliverable, entries grouped by kind, the unconfigured-
  objective line when that is the state. Exit 0 on a printed report
  (including the empty one), 2 on bad usage/unknown area or deliverable.
- One derived-view builder, `engagement-needs`, registered through
  `aggregate.PY_BUILDERS` (one import + one entry, the plan_views/matrix_views
  pattern), emitting the same render in aggregate's derived-view idiom — so a
  future definition (D4's interview agenda is next) can bind it. No shipped
  definition changes in this ticket.

## Part C — the prose (three contracts + the brief)

- **Drafter** (`agents/consult-drafter.md`): the GAP bar rewritten to Part A —
  the two mints, the deleted ask half, the standing generic-thinness rule.
  The worked example's GAP bodies updated to carry grounds instead of
  "confirm with the process owner" phrasing.
- **Surveyor** (`agents/consult-surveyor.md`): the ask agenda is now
  *rendered from the needs view*, not authored — the surveyor runs
  `scripts/needs.py` and shapes asks from its entries; its own judgment
  stays (what to ask FIRST, how to phrase a client-facing ask), the
  inventory of what is missing is no longer its to compile by hand.
- **Librarian** (`agents/consult-librarian.md`): grooming vocabulary
  unchanged; one line admits the ask-half trim as a proposable groom.
- **Brief** (`scripts/brief.py` `objective_block`): the per-deliverable
  section's lead-in points at the needs view as the deeper render
  (serviceability lines stay — they are the structural floor and cheap).

## Wants (recorded, not gates)

- The information-request definition rebinding onto `engagement-needs`
  (today it renders coverage + step callouts directly) — after D4 lands.
- A conflict/absence discriminator on GAP callouts (a `fields:`-style
  semantic marker, M43 A1's candidate) so `recorded-gap` entries can say
  which mint they are.

## Acceptance gate

`tests/test_needs_m44.py` — written before the build, skip-gated per work
package. Suite green at every commit; zero v1 tests edited.

## Amendment A1 — build friction (recorded at close-out, 2026-08-16)

From WP-G2, three grammar collisions the doctrine rewrite exposed —
none fixed in this ticket because spec Part A item 5 says "grammar
unchanged"; each needs a human ruling before anyone touches the grammar:

1. **`Owner to confirm:` is the ask half in field form.** The inline GAP
   grammar declares `- **Owner to confirm:** <role or TBD>` — exactly the
   "who can answer it" the doctrine deleted from prose. The contract is
   mildly self-contradictory at that one field until it is retired, made
   optional, or kept as a legacy slot the doctrine no longer asks to fill.
2. **`Grounds:` is example-only.** The worked example now shows a
   `- **Grounds:**` sub-field (mirroring the needs view's `grounds` key),
   but the grammar declares no such field. Minting it canonically is the
   natural pair to ruling #1.
3. **The `Nature:` enum predates the two mints.** It reads
   `unknown | conflict | unsupported-assumption`; the worked example now
   says `evidenced absence`, outside the enum. The obvious alignment is
   `conflict | evidenced-absence` — a grammar change, so deferred with
   the others.

Also noted: M42's standing anchors ("blocks",
"'unconfirmed' alone does not mint") survive truthfully — "what it
blocks" now appears only as the thing the drafter must NOT write.

## Amendment A2 — WP-G1 build friction (recorded at close-out, 2026-08-16)

1. **`where` for `binding-unserved` is not derivable from the return
   value** — `definitions.serviceability` hands back flat sentences, so
   the builder calls it once per binding on a single-binding copy of the
   definition to get exact attribution. If serviceability ever returns
   structured gaps, switch to it (follow-up: a structured serviceability
   return is now wanted by two consumers — brief.py renders the
   sentences, needs.py re-derives their attribution).
2. **The CLI prints the objective's own report line** on objective-driven
   runs and suppresses it under `--deliverable` (the objective plays no
   part then). A rule the spec did not state.
3. **Multiple `coverage:` bindings on one definition** would emit
   duplicate node entries; no shipped definition does this — a de-dupe
   rule waits until one exists.
4. **Broken-area posture:** an area outside an engagement tree, or with an
   unreadable manifest, renders empty coverage/recorded feeds ("thin is
   not a defect") rather than refusing — so a genuinely broken area reads
   as "no needs". The one mandated refusal (unknown deliverable, by name)
   propagates as `DefinitionError`. Worth revisiting when the taxonomist
   (M45) becomes the render's main consumer.
5. The recorded-gap mint discriminator and the first `engagement-needs`
   consumer stay on the Wants list (the latter is M46 by design).

## Work packages

| WP | Owns | Delivers |
|---|---|---|
| WP-G1 | `scripts/needs.py`, `scripts/aggregate.py` (registration lines only) | Part B: the module, the CLI, the `engagement-needs` builder |
| WP-G2 | `agents/consult-drafter.md`, `agents/consult-surveyor.md`, `agents/consult-librarian.md`, `scripts/brief.py` | Parts A + C: the doctrine amendment and the prose |
