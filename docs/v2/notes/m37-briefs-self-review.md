# M37 WP-S2 — agent briefs, self-review against the ticket

What this is: the orchestrator's review aid for the prose half of M37. For each
brief, the ticket's contract lines are quoted (from
[`../M37-surveyor-librarian.md`](../M37-surveyor-librarian.md) and
[`../M37-build-plan.md`](../M37-build-plan.md)) with the section of prose that
satisfies each; then every v1 path and verb removed or kept, with the reason.

Files in this work package:

| file | state |
|---|---|
| `agents/consult-surveyor.md` | new |
| `agents/consult-librarian.md` | new |
| `agents/consult-drafter.md` | edited (additive only) |
| `agents/consult-intake.md` | rewritten (central-mode operation) |
| `agents/consult-taxonomy.md` | STATUS banner only; body untouched |
| `agents/consult-placement.md` | STATUS banner only; body untouched |

---

## A. `agents/consult-surveyor.md` — Part C + Part D (node altitude)

### Ticket line → where it is satisfied

> "The surveyor is `consult-taxonomy`'s successor, dispatched at the same point
> in the flow, returning a strictly larger result"

Front matter (`description`, `model: opus` pin carried from consult-taxonomy)
and the opening two-jobs framing ("You do two jobs where v1 did one"). Every v1
return field survives in **What you return**, with the new fields added — the
result is strictly larger, field by field.

> "1. **Structure proposal** — node entities + registry, as today."

Two sections: **THE NODES — the taxonomy as entity files (M37 Part A)** (the
node entity files: live path `{area}/_taxonomy/<slug>.md`, staged at
`{area}/_reference/.proposed/_taxonomy/<slug>.md`, the `Scope`-only shape, the
`consult-meta` block, the one-callout-kind rule) and **What you write** (the v1
registry set kept as-is: `procedures.yaml`, `systems.yaml`, `roles.yaml`,
`glossary.yaml`, `area.yaml`, `new_buckets.yaml`, `notes.yaml`).

> "the L3 procedure set filed under L2 buckets" / "registry nouns as today"
> (WP-S2)

**The hierarchy you are building**, **One activity, one procedure**, the
variant-vs-separate test, **Ordering hints & seam declarations**, the gap
forecast field in `procedures.yaml` — all carried from the v1 brief with wording
intact where nothing changed.

> "2. **Sufficiency assessment** — per proposed node, from the coverage join
> plus judgment over the tagged sources: enough to draft / thin / nothing.
> Judgment is the agent's; the JOIN is handed to it precomputed (the brief
> carries the coverage map — the agent never re-derives mechanics)."

**SUFFICIENCY — enough / thin / nothing (M37 Part C)**: the four-row table
(`enough` / `thin` / `nothing` / `conflicted`), "the mechanics are handed to you,
the judgment is yours", the mechanical floor rule (`claimed` can never be
`enough`; map-`conflicted` is call-`conflicted`), and the explicit "**Never
recompute the map**". The `coverage` dispatch field is declared in **Your
assignment** with the same prohibition and the reason (pure function, no file,
`scripts/coverage_map.py`). Hard rule 8 repeats it and names the guardrail
("never write a coverage file… breaks the charter's one hard guardrail").

> "3. **Information requests** — for thin/empty nodes: what to ask the client,
> phrased as requests ("the AP aging process: who runs it, from which system — a
> walkthrough or the SOP if one exists")"
> … "written as the surveyor's structured return"

**INFORMATION REQUESTS — the client ask, written while scoping is cheap**: the
phrase-as-request rule with the ticket's own example, "name what would satisfy
it", one-per-node in the client's language, the conflict variant (both readings,
neutral attribution, "we have deliberately not guessed" — matching the shipped
`information-request.yaml` preamble), the no-pipeline-vocabulary rule, and the
never-ask-what-a-source-answers rule. They ride in the **structured return** as
`information_requests`, not as entities — stated in that section and in the
return contract.

> "The request list is fed from TWO altitudes (ruling, 2026-08-14): node-level
> coverage (thin / claimed / conflicted) and step-level GAP callouts — one list,
> two feeders."

Named in the same section ("rendered by the shipped `information-request`
deliverable definition (which reads the same coverage statuses plus the
step-level GAP callouts — two altitudes, one list)"). The step-level feeder is
the drafter's GAP, which is why the drafter's rule 6 is part of this package.

> "rendered before the human confirm gate so the client ask goes out while
> scoping is still cheap" / "The gate sequence gains nothing new"

Opening ("Nothing you write goes live … The gate does not move"), the
information-request section's first line, and the node-promotion line (the human
moves node files at that same gate).

> "**Drafting a node the human confirms despite thin evidence is allowed** — the
> system informs, the human decides (M17/M18 doctrine)."

Sufficiency section, last bullet: "**Thin is not a refusal.** … Your job is that
the human decides *knowing*."

> Part D: "The surveyor flags nodes whose tagged sources conflict on a material
> fact (owner, system, sequence) → coverage status `conflicted`, and the
> conflict is written as a GAP-style callout on the node entity, naming both SRC
> ids and both claims in their own framing (the PAIN discipline: observation,
> never adjudication)."

**THE LENS-CONFLICT RECORD (M37 Part D)**: the three-step contract (mark
`conflicted`; write the GAP on the node naming both ids and both claims, with a
worked example; raise the request), the four prohibitions (never pick a side,
never blend, never drop the weaker claim, conflict outranks volume), the
materiality test, and the reason both ids must be *in the callout body* — that
is what `coverage_map.py` reads as the conflict record.

> Part D: "Adjudication is human (at review) or analytical (M39) — never the
> drafter's, never the surveyor's."

Same section, and hard rule 7.

> Build plan: "the M34 A2 carry-in applies: **sources enter central engagements
> only through route/adopt — the surveyor refines TAGS (ledger.retag), it never
> mints registry entries**"

Three places, deliberately: **Central mode is the mode you run in** (the two
consequences), **`sources.yaml` — TAG REFINEMENTS ONLY (the M34 A2 line)** (the
`id` + `touches` shape, REPLACE semantics as the sanctioned M6 veto, the
explicit never-write list `hash`/`state`/`file`/`registered`/`consumed`, the
drop-with-a-warning behavior for an unmatched entry, area-slice-only), and hard
rule 4.

> Build plan: "enumerate ledger-staged sources via `ledger.assess`"

**Your assignment** (`sources` and `unassessed` dispatch fields, named as
derived from `ledger.assess` / `ledger.area_view` by the orchestrator) and
**Coverage is attested, never assumed** step 1 — the reconciliation is now
dispatch-lists-vs-folder, and a staged file in neither list is reported under
`unregistered`, never registered by the agent.

> "the attestation discipline v1 had" (WP-S2 assignment)

**Coverage is attested, never assumed**, kept as four numbered rules with v1's
teeth: Read-tool-only reads, `files_listed`/`files_read` must match, "a blocked
tool is a STOP, not a detour", "a loud dead-end costs one redispatch; silent
partial coverage costs a rebuild".

### v1 paths and verbs — removed or kept

| v1 item | disposition | why |
|---|---|---|
| `{area}/_sources/new/` as the enumeration target | **replaced** by `<root>/_sources/new/` + the ledger-derived dispatch lists | central mode: the area owns no `_sources/` tree (`sources.central_root` is the mode marker) |
| `*.route.md` intake sidecars | **removed** | central `route` folds the pointer into the ledger entry's `note:` (`_route_central` / `ledger.annotate`); `scaffold.stamp_sources` is a no-op centrally, so nothing folds a sidecar |
| `sources.yaml` SRC minting ("Continue `SRC-` ids from the existing max") | **removed** | one minter: `ledger.register`, via route/adopt. The brief forbids inventing an id |
| `hash`/`state` note ("stamped by the Python scaffold step, not you") | **removed** | hashed at registration; central `stamp_sources` is a documented no-op |
| `{area}/_reference/.proposed/` as the staging root | **kept** | still the sanctioned staging path; `scaffold.promote_reference` reads it, and centrally routes `sources.yaml` through `promote_tag_refinements` → `ledger.retag` |
| `procedures.yaml`, `systems.yaml`, `roles.yaml`, `glossary.yaml`, `area.yaml`, `new_buckets.yaml`, `notes.yaml` | **kept verbatim in shape** | `REGISTRY_FILES` / `REGISTRY_KEYS` and the confirm step still consume exactly these |
| `notes.yaml` kinds (`review | source | retirement | rename | consolidation`) + `src:` | **kept** | the M6 bus contract is unchanged; `kind` is load-bearing for retirement accounting |
| the reference taxonomy as ADVISORY (v1.6.1) | **kept** | ruling unchanged; `_client/taxonomy.yaml` survives as the reference tree (Part A) |
| client context (`org-chart.yaml`, `taxonomy.yaml`, M13 shadowing, M30 registers) | **kept** | none of it moved |
| sibling-manifest boundary + M26 seam declarations, `upstream:` two notations | **kept** | scaffold still validates and drops bad cross-area refs |
| retirement proposal flow (flags, `[[slug]]` grep, retirement notes, re-emit `touches`) | **kept, one step added** | `reconcile` still blocks on dangling `[[slug]]`; the added step names the orphaned node file, since a retired L3 leaves `{area}/_taxonomy/<slug>.md` behind |
| gap forecast (M26) | **kept** | still the early client ask-list, and now one of two feeders alongside the requests |
| `skills: consult-taxonomy` + `model: opus` | **kept** | the skill's reference files (`reference_taxonomy.yaml`, the example client files) are cited by the brief; the M26 pin rationale is unchanged |

### Verbs NOT invented (the friction, recorded)

- **Node-file promotion.** Nothing promotes `{area}/_reference/.proposed/
  _taxonomy/*.md` into `{area}/_taxonomy/`: `scaffold.promote_reference` merges
  only `REGISTRY_FILES`, and it ignores extra subdirectories. The brief
  therefore stages the files, names them in the return, and states plainly that
  promotion is the human's move at the gate. No verb was invented.
- **`ledger.retag` is not callable by an agent.** `scripts/ledger.py` has no
  `__main__` / CLI. The brief routes the refinement the only way that exists:
  `.proposed/sources.yaml` → `scaffold.promote_tag_refinements` →
  `ledger.retag` at confirm. The brief names `ledger.retag` as the mechanism, not
  as a command for the agent to run.

---

## B. `agents/consult-librarian.md` — Part E

### Ticket line → where it is satisfied

> "The librarian unifies M6's scoping reassessment and M24's placement pass into
> one recurring curation dispatch over the brain"

Opening ("The surveyor sets the structure up front, once. You keep it honest
afterwards"), the front-matter description, and the two halves of the body: the
structural moves (M6) and **One fact, one home — the M24 triage you carry**.

> "**Triggers** (advisor-sequenced, as today): new sources registered after
> confirm; a drafter GAP naming an unscoped activity; consolidator/
> placement-style findings that a fact or step sits in the wrong node."

**Your triggers — what brings you back**, as a numbered list: the ticket's three
plus two the ticket's own machinery implies (a consolidator finding, and a
coverage/sufficiency signal that reads as structural). Each says what to propose.

> "**Proposes, never executes**: split this node / add an L3 / move this step /
> merge these — each as a note on the M6 bus targeted at the scope gate, with
> evidence."

**What you propose — five moves, each as a note with evidence** (the table names
split / add / move / merge, plus `retag` — the central-mode move the ledger
makes possible), the three-part proposal requirement (move, evidence, what the
human must do), and **How a proposal is filed — the M6 bus, targeted at the
scope gate**: the real command (`engagement.py note <area> --slug --note`),
`kind: review` as the vetoable kind, and the `SCOPE PROPOSAL (<move>):` opening
convention so a structural proposal is findable on a bus with five producers.

> "Structural change still flows human-confirm → scaffold/manifest edits by the
> deterministic layer (rename propagation per M20)."

Opening paragraph and hard rule 1 (no manifest edit, no scaffold, no rename, no
node file, no ledger write, no register write, no adopt run).

> "M24's one-fact-one-home judgment continues inside the librarian's brief
> (placement was always curation)"

**One fact, one home — the M24 triage you carry (unchanged)**: the rule, the two
diseases, the three moves with their execution boundaries
(reduce-to-handoff / promote-to-register / adopt-as-source), and the brief-first
work order (`engagement.py brief`, SIZE GUARD obeyed) carried from
consult-placement.

> "never writes entities" (WP-S2 assignment) / "no file mutated by the agent"
> (acceptance sketch)

Hard rules 1–3, and the return contract carrying everything that is not a note.

> Part D, at the node altitude

Hard rule 6: a conflict is reported with both accounts and both `SRC-` ids,
never harmonized — explicitly the same lens-conflict rule the surveyor and
drafter carry.

### v1 paths and verbs — removed or kept

| v1 item | disposition | why |
|---|---|---|
| `engagement.py brief <components-dir> [--full]` as first action | **kept** | it is still the only work order; the SIZE GUARD line still overrides |
| `engagement.py note <area> --slug --note` | **kept, sole writer** | the only note verb that exists (`add_note`, `kind: review`) |
| the three placement moves + triage questions | **kept** | unchanged doctrine; register writes stay with `engagement.py register` |
| `<register>#<entry-id>` proposal form, class + provenance | **kept** | M30 shape, still what the human approves |
| adopt-as-source: "the exact command, inside the note" | **kept** | `engagement.py adopt` is still executed by the orchestrator on the human's word |
| policy / control-design / configuration → unresolved | **kept** | absolute, carried verbatim in spirit |
| "never paste digests, fragment text, or gap bodies back" | **kept** | context discipline |
| `sonnet` model pin | **kept** | the placement pass ran on the worker tier; nothing about curation argues for a premium |
| M6's separate reassessment dispatch (taxonomy `mode: incremental` as the *only* structural path) | **folded in** | the librarian now proposes structure continuously; the surveyor's incremental mode remains for source-driven delta at the gate. Both retire nothing mechanical — the advisor's action names are WP-S3's business |
| **added** reads: `components/*/_taxonomy/*.md`, `manifest.json`, `<root>/_sources/sources.yaml` | new | the brain's index, the membership authority, and the tag evidence — the three things structural proposals are actually about |

### Verbs NOT invented (the friction, recorded)

- **The notes bus has no structural `kind:`.** `engagement.py note` writes
  `kind: review` only (no `--kind` flag), and the M6 bus contract fixes the kind
  set at `review | source | retirement | rename | consolidation`. The brief uses
  `kind: review` plus a `SCOPE PROPOSAL (<move>):` text convention rather than
  asking for a kind that does not exist.
- **A note requires an existing procedure slug.** There is no bus for a
  procedure that does not exist yet, so an `add` proposal has no home: the brief
  files it on the nearest affected existing procedure and reports it in the
  return (`RETURN ONLY`), and forbids inventing a slug — a note on a slug the
  manifest does not carry is a blocking reconcile error. **If M37 wants
  structural proposals to be first-class, this is the gap to close** (a
  scope-gate bus, or a `--kind` on `note`); it was not invented here.

---

## C. `agents/consult-drafter.md` — Part D (step altitude) + central-mode reads

Surgical, additive only. Four edits; every v1 instruction stands.

### Ticket line → where it is satisfied

> "Drafters inherit the same rule per step: conflicting sources on a fact →
> state neither, raise the GAP naming both. The drafter contract gets this block
> verbatim; the M29-style rules sweep classifies it."

New **### 6. Conflicting sources — state neither, raise the GAP naming both**,
appended to the numbered non-negotiable rules (rules 1–5 unchanged) immediately
before **## Before you finish** — the house position for a contract block, in the
house form (a numbered rule, bulleted contract, a worked callout example). It
carries: state neither (no blend, no hedge — cross-referencing rule 4), the GAP
naming both ids and both claims in their own framing with `Nature: conflict`,
never pick a side (adjudication is human at review or analytical per M39), the
long-callout split pointer, the `conflicts` return field, the materiality test,
and the note that the surveyor raises the identical GAP one altitude up. Rule 1's
existing line ("Sources conflict → raise a GAP stating the conflict; never
silently choose") is left untouched and is now the one-line form of rule 6.

> WP-S2: "drafter briefs get their central-mode path updates" / "sources arrive
> as ledger-tagged lists in the brief; the `_reference/sources.yaml` path line
> gains its central-mode sibling"

Three additive edits:
1. **Your assignment**, the `sources` field — a central-mode paragraph: tags live
   in `<root>/_sources/sources.yaml` (written by `route`/`adopt`, refined by
   `consult-surveyor`), files at `<root>/_sources/new/`, **the brief resolves the
   paths either way**, the entry `note:` carries the intake pointer, and
   "nothing else about your job changes".
2. **The fallback reading list**, item 2 — the tagged sources are under
   `{area}/_sources/` *or* `<root>/_sources/new/` centrally.
3. **The fallback reading list**, item 3 — the `_reference/sources.yaml` line
   gains its sibling: centrally the `SRC-` ids resolve in the engagement ledger,
   read-only, never edited; `systems.yaml`/`roles.yaml`/`glossary.yaml` stay
   per-area (which is true: `promote_reference` still merges them, and only
   `sources.yaml` is diverted centrally).
4. **The `kind: source` note item** — resolving `src:` gains the same sibling
   path, because that is the other place the brief names a sources registry.

### v1 paths and verbs — removed or kept

| item | disposition | why |
|---|---|---|
| every v1 line in the brief | **kept, byte-for-byte** except at the four insertion points | the brief is live for v1 engagements |
| `brief.py {area} --slug --mode` as first action | **kept, unchanged** | `_sources_entries` already asks `sources.central_root` and hands back the v1 entry shape, so the brief's reading list needs no drafter-side change — the prose says exactly that |
| `{area}/_reference/sources.yaml` | **kept, sibling added** | still correct for v1; centrally the area owns no such file |
| `{area}/_sources/` | **kept, sibling added** | same reason |
| `consult-taxonomy` named as the tagger | **kept, `consult-surveyor` named alongside** | v1 areas still dispatch consult-taxonomy; deleting the name would make the v1 sentence wrong |

---

## D. `agents/consult-intake.md` — the M34 A2 rewrite

### Ticket line → where it is satisfied

> Build plan: "intake … briefs get their central-mode path updates"; the A2
> carry-in: "route = tagging"

- **Classification judgment: unchanged.** Read every area's manifest as the
  target vocabulary; read each document whole ("relevance often lives in the last
  third"); one verb per file; `--note-for` pointers written by the agent that
  just read the document, describing where relevance lives and never summarizing.
  All five original contract rules survive with their original teeth
  (zero-routes forbidden; bias to over-route with the asymmetric-cost argument;
  describe-never-reduce; never `--new-area`; relay a refusing verb).
- **Operationally:** **The flow** step 2 names the drop point as
  `<root>/_sources/new/` TOP LEVEL (v1: `<root>/intake/`), with the mode marker
  (`<root>/_sources/sources.yaml`) named so the agent can see which it is, and
  the note that a file with a ledger entry is registered work-in-progress, not a
  to-do (`ledger.status`'s `unregistered` list is the to-do).
- **What `route` does in a central-mode engagement — TAGGING, not copying**: one
  ledger entry per document (not one per area), `--to` becomes AREA-LEVEL tags
  with procedure slugs named later by the surveyor at the confirm gate, **nothing
  copied and nothing moved**, **no `.route.md` sidecars** (pointers fold into the
  entry's `note:`), idempotent by content hash with re-route = merge.
- **Park unchanged in spirit**: same section, last bullet — the reason is
  recorded against the file in the ledger (loud until dealt with) instead of
  moved to `parked/`; a parked file still ends the pass accounted for.
- Contract rule 5 is the rewritten one: "You register and tag; you do nothing
  else" — replacing v1's "Route writes file copies only", and adding no
  `touches` refinement, no hashes, no ledger hand-edits.
- **House structure kept**: front matter with the `sonnet` pin, `## Your
  assignment (from the dispatch prompt)`, `## The flow`, `## Contract rules (the
  anti-silent-loss core)`, `## What you return (COMPACT — no document text)`.

### v1 paths and verbs — removed or kept

| v1 item | disposition | why |
|---|---|---|
| `intake/` as the drop point | **kept as the v1 branch**, central branch added | `_intake_context` supports both; the verbs detect the mode themselves |
| `routed/` folder as the success state | **removed in the central branch** | central `route` moves nothing; the ledger entry IS the success state |
| `.route.md` pointer sidecars | **removed in the central branch** | `_route_central` writes the pointer into the entry `note:` via `ledger.annotate` |
| "Route writes file copies only — no sources.yaml entries, no hashes" | **rewritten** | centrally route DOES register (that is the A2 point); the agent still writes no slugs, no hashes, nothing else |
| `engagement.py route` / `park` command forms, `--to`, `--note-for`, `--reason`, `--new-area` | **kept verbatim** | the real flag set, unchanged in both modes |
| the five contract rules | **kept**, rule 5 rewritten as above | anti-silent-loss core |
| "You are taxonomy's little sibling" | **reworded** to "the surveyor's little sibling" | same relationship, current name |
| **added** return fields: `SRC-` id per routed line, `already_registered` | new | the verb prints both; they are the only new facts the pass produces |

---

## E. Retirement banners (F)

`consult-taxonomy.md` and `consult-placement.md` each gained a short blockquote
STATUS banner directly under the H1, and **nothing else changed in either file**
(no front-matter edit, no body edit). Each says: succeeded by
`consult-surveyor` / `consult-librarian` for central-mode engagements; retained
verbatim for v1 areas; the body below is the live contract for those areas. The
taxonomy banner additionally warns against porting central-mode rules into the
v1 body (its per-area enumeration and `sources.yaml` minting are correct there).

Rationale: v1 engagements still dispatch both briefs — the advisor's action
names are WP-S3's business, and the build plan prefers the surveyor riding the
existing `taxonomy` action name where tests pin it. A banner is the only
retirement signal that cannot break a v1 dispatch.

---

## Standing rule

`python3 -m pytest --tb=no -p no:warnings 2>&1 | tail -1` → `1013 passed` (0
failed) with these briefs in place. No test reads any of the five agent briefs
(prose is orchestrator-reviewed, not gated), so this package is green by
construction; the deterministic gate for M37 is `tests/test_surveyor_m37.py`,
owned by WP-S1.
