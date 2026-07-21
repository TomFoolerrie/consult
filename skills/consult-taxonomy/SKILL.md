---
name: consult-taxonomy
description: "How-to brief for the consult-taxonomy scoping subagent: scope one L1 finance function, stand up the noun registry, and stage proposals for a human confirm gate."
---

# consult-taxonomy — scoping + reference-registry stand-up

This is the working brief the `consult-taxonomy` agent preloads. The agent
definition (`agents/consult-taxonomy.md`) is the contract; this file is
the expanded method. Where they overlap, they must agree — if you change one,
change the other.

You scope **one area = one prescribed L1 finance function**. You run in your own
context: read the area's new sources and the reference taxonomy, then **propose**
(never apply) the procedure set, the canonical noun registry, and the source
registry. A human reviews and confirms before anything is scaffolded.

## Golden rules (read these first)

1. **Propose only — never go live.** Everything you write goes under
   `{area}/_reference/.proposed/`. You never touch the live `_reference/`, never
   write a `manifest.json`, never create a `10_<slug>.md`. Python does that at the
   confirm gate (`scaffold.py --confirm`).
2. **Best-guess freely, but mark confidence and never invent facts.** Aliases and
   names may be inferred from how sources talk; factual claims about the client's
   systems (`description`, `limitations`) must be transcript-sourced or left
   blank. A guessed limitation rendered as fact is the anti-anchoring defect the
   credibility guardrail forbids.
3. **Stay inside your L1.** Activities that belong to another L1 are reported in
   your return, not scoped.
4. **New L2 buckets need human approval.** Never fold an invented bucket into
   `procedures.yaml` as if it were known.
5. **Return compact.** No source text, no long prose — the orchestrator only needs
   the summary to drive the confirm gate.

## Inputs (from the dispatch prompt)

- `area` — the area folder, e.g. `components/fixed-assets`.
- `l1` — the prescribed L1 **taxonomy slug** you operate in (matches a `slug:` in
  the taxonomy). Stay inside it.
- `taxonomy` — the reference taxonomy
  (`skills/consult-taxonomy/reference/reference_taxonomy.yaml`, or a user override).
- `mode` — `initial` (fresh area) or `incremental` (new sources after scaffold).

## The hierarchy you build

- **L1 (given)** — the finance function. Fixed.
- **L2 buckets (known backbone)** — the sub-processes listed under your L1 in the
  taxonomy. Use each bucket's `slug` **verbatim** as an `l2` value; do not
  re-slugify. This is a mostly-closed set.
- **L3 activities (you discover)** — read from the sources. Each L3 becomes **one
  procedure**, filed under exactly one L2 bucket. This is the open set; the
  taxonomy never enumerates L3s.

File each discovered L3 under an L2 bucket. When work fits **no** existing bucket,
propose a new bucket (needs-approval) rather than forcing a bad fit or inventing a
bucket silently.

## Client context (optional inputs at `{area}/_client/`)

The human may drop client-supplied reference files at `{area}/_client/` — read
them when present, never write to that folder, never invent their contents.
Schema examples live beside this skill:
`reference/org_chart.example.yaml` and `reference/client_taxonomy.example.yaml`.

- **`org-chart.yaml`** (person → title): ground `roles.yaml` on it — the
  client's real titles become canonical role names, and each person is listed
  under their role's `people:` field. People named in sources but absent from
  the org chart still get mapped (best-guess role, `confidence: low`).
- **`taxonomy.yaml`** (the client's own L1→L2→L3 map): the **boundary
  authority**. An activity it places under a different L1 than yours goes to
  `out_of_l1`, not into scope — one process is never documented in two L1s.
  Its L3 names are a naming/filing prior. It supplements the reference
  backbone: `l2` slugs still come from the reference taxonomy (map client L2
  names onto backbone buckets; a client L2 with no home is a new-bucket
  request, same needs-approval flow).

## Method

### 1. Read
- Everything in `{area}/_sources/new/` (the unconsumed inputs).
- The `taxonomy`: find your L1 by `slug`, read its L2 buckets and their slugs.
- `{area}/_client/` if present (org chart + client taxonomy — see above).
- **incremental only:** also read the live `_reference/` (systems/roles/sources)
  and the existing procedure slugs from `{area}/manifest.json`, so you propose a
  *delta* against what already exists.

### 2. Propose the procedure set → `.proposed/procedures.yaml`
One entry per L3 activity:
```yaml
procedures:
  - slug: bank-reconciliation      # stable identity, kebab-case, set ONCE here
    title: Bank Reconciliation
    l2: close                      # a known bucket slug, or an approved new one
    confidence: high | medium | low
    sources: [SRC-001, SRC-003]    # which sources describe this L3
    variants: []                   # only on a merged near-duplicate pair, e.g.
                                   #   ["New vendor setup", "Vendor banking change"]
    upstream: []                   # optional ordering hint: slugs whose output
                                   #   this procedure consumes (drafted first)
```
Slugs are identity: unique, kebab-case, never colliding. Scaffold builds the
manifest from this file; `procedures.yaml` itself is **not** a live registry file
and is never promoted.

**Merge near-duplicate L3s.** Before finalizing the set, compare candidates
pairwise: two L3s sharing the same core flow (actors, systems, step sequence)
that differ only by a small delta are **one procedure with `variants:`**, not
two — twin documents are bloat the client maintains twice. Scaffold stamps the
variants into the skeleton so the drafter writes the shared flow once and
branches at the divergence. Genuinely unsure → keep them separate and report
the pair in `overlap_flags` for the human. Distinct activities that merely
share a phase stay separate.

**Variant vs separate — the test.** One procedure (variant pair): same
trigger, same preparer role, same core system, same output; divergence is a
conditional branch at a few steps — *a diamond inside one box*. Separate
procedures: different trigger, different preparer role, a real handoff between
them (one's output feeds the other), or distinct control points — *an arrow
between two boxes*. When the handoff arm decides it, also stamp the downstream
procedure with `upstream: [<producer slug>]` — the orchestrator drafts
producers first and passes their fragments to downstream drafters read-only,
so the seam is described consistently. Hint only on clearly evidenced
handoffs; when in doubt, omit (absent = "no opinion", drafting just runs in
parallel as always).

### 3. Stand up the noun registry → `.proposed/systems.yaml`, `.proposed/roles.yaml`
```yaml
systems:
  - slug: sap
    name: SAP S/4HANA
    aliases: ["SAP", "S/4", "the ERP"]   # how sources refer to it
    description: ""      # ONLY if a source states it; else blank
    limitations: ""      # ONLY if a source states it; else blank
    confidence: high | medium | low
roles:
  - slug: ap-clerk
    name: AP Clerk
    aliases: ["the AP lady", "accounts payable clerk"]
    people: ["Luis Ortega"]        # individuals holding the role (org chart /
                                   #   sources) — prose names ROLES, never people
    reports_to: controller
    confidence: high | medium | low
```
The registry's primary purpose is **intake grounding**: it is the lookup a drafter
uses to normalize a messy mention ("the AP lady", "our system") into a canonical
name. Rich, honest aliases are the highest-value thing you produce here.
`description`/`limitations` follow the credibility guardrail — sourced or blank.

**`people:` is the person → role mapping.** Every individual named in the
sources or the org chart belongs under some role's `people:` list. Drafters use
it to resolve "Sarah sends the file…" into the role name, and `reconcile.py`
enforces it (a listed person's full name in procedure/derived prose is an
ERROR). A person you can't confidently place: best-guess a role at
`confidence: low` and report them in `unmapped_people` — never drop them.

### 4. Register + tag the sources → `.proposed/sources.yaml`
```yaml
sources:
  - id: SRC-001
    file: _sources/new/2026-06-close-walkthrough.md
    touches: [bank-reconciliation, pre-close-checklist]   # procedure slugs it informs
```
- Assign `SRC-` ids (initial: from `SRC-001`; incremental: continue from the
  existing max in the live `sources.yaml`).
- **`touches` is load-bearing:** it is how the orchestrator hands each parallel
  `consult-drafter` only its relevant sources instead of every drafter re-reading
  every transcript. A source may touch many procedures; a procedure may draw on
  many sources. Tag every source.
- **Do NOT set `hash` or `state`.** Those are deterministic byte-work stamped by
  `scaffold.py` at confirm, not by you.

### 5. New buckets (only if needed) → `.proposed/new_buckets.yaml`
```yaml
new_buckets:
  - slug: <proposed-l2-slug>
    name: <proposed L2 name>
    rationale: <why the sources need a bucket the taxonomy lacks>
    status: needs-approval
```
Surface every new bucket in your return. The human decides at the gate — you
cannot round-trip approval mid-run, so the gate is the permission point. If the
human approves, scaffold appends the bucket to the manifest's `l2_order` (giving
it a display-number ordinal); the immutable taxonomy is never mutated.

## Modes

**`initial`** — scope from scratch: propose the full L3 set, the registry, and
source tags for everything in `_sources/new/`.

**`incremental`** (M6 reassessment path — designed, build deferred) — new sources
landed after the area was scaffolded. Propose only the **delta**:
- new L3 procedures (new slugs only);
- new registry entries + new aliases for existing ones;
- new/updated `touches` tags naming which **existing** procedures the new source
  affects — this drives which drafters re-run in update mode;
- new-bucket requests (same needs-approval flow).

Incremental **never** renames or deletes an existing slug and never rewrites the
whole set. If a new source implies an existing procedure should **split or merge**,
do not do it — **flag it** for the human in `split_merge_flags`. On promotion,
scaffold MERGEs your delta into the live registry (adds new, updates re-emitted,
leaves untouched entries intact) — so you only need to emit what changed.

## What you return (compact)

- `mode`, `l1`; counts: procedures (new vs existing), L2 buckets, systems, roles,
  sources.
- `by_bucket`: each L2 → the L3 slugs filed under it.
- `new_buckets`: proposed buckets needing approval (slug + one-line rationale).
- `merged_variants`: near-duplicate L3s merged into one procedure (slug + variants).
- `overlap_flags`: heavily-overlapping pairs you did NOT merge (human decides).
- `unmapped_people`: individuals you could not confidently map to a role.
- `low_confidence`: procedures/entries the human should scrutinize first.
- `out_of_l1`: activities in the sources belonging to a different L1 (not scoped).
- `unresolved`: sources you couldn't place, or material ambiguity for the human.
- **incremental only:** `new_procedures`, `touched` (existing slugs a new source
  affects), `split_merge_flags` (proposals for the human, never auto-applied).

Do not return source contents. The proposals live in `.proposed/`; the summary
just drives the confirm gate.

## The confirm gate (what happens after you)

The human edits the files in `.proposed/` directly (add/remove/merge procedures,
split a merged variant pair back into two, fix a role or person mapping, add an
alias, blank a guessed limitation, approve a new bucket). Confirm = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --confirm --area {area} --l1 {l1}`,
which promotes `.proposed/` → live `_reference/` (a MERGE), builds `manifest.json`,
and writes one A–H skeleton per procedure. Nothing you wrote reaches the live
folder until that runs.
