# CONSULT MVP — Build Tickets

Shared architecture for the MVP rebuild. Every ticket (M0–M17) references the
contracts defined here so the individual tickets don't restate them. Read this
first.

> **Revision history.**
> - *r1 → r2* (adversarial review): numbers never baked into content
>   (`[[slug]]` tokens + one render-time helper); `split` is a one-shot bootstrap;
>   role `frontmatter`→`static`; In-Scope index python-owned; content-hash change
>   signal.
> - *r2 → r3* (this revision): the system is **folder-native from birth**. A new
>   **M0 (`consult-taxonomy`)** determines the procedure set *and* stands up a
>   **reference registry** (the two-database model below), gated by a human
>   confirm step, then Python scaffolds A–H skeletons that fill agents populate in
>   parallel. `split` (M2) demotes to a legacy **import** tool. Systems & Role
>   Dictionary move to Python-owned joins (M3); M5 shrinks to RACI + dependencies
>   + Appendix-A judgment.
> - *r3 refinements*: nouns bound via an explicit per-procedure `consult-meta`
>   slug block (no prose scraping); callouts moved to home sections (CONTROL→F,
>   PP/IO→H, GAP/SC inline in E); **Appendix A is now fully mechanical** (drafter
>   authors impact + severity in the PP/IO callouts) — the Appendix-A judgment
>   agent is dropped, so **M5 = RACI + dependencies only**.

---

## The thesis — two databases, everything else is a view

1. **Procedures = the verbs.** One `##` fragment per L3 procedure; the source of
   truth for what happens, in what order, with what controls/gaps/screenshots.
2. **Reference registry = the nouns.** Canonical systems, canonical functional
   roles, glossary terms, source materials — a human-confirmed dictionary per
   area (`_reference/`).

Every other section — Roles & Responsibilities, Systems & Data Inputs, Key
Dependencies, the Appendices, the In-Scope index — is a **projection** of those
two, regenerated rather than hand-maintained.

Humans edit the procedure fragments and the registry. Reviewers read the rendered
Word document. The assembled single `.md` is **not** an artifact — it exists only
transiently inside the docx build.

### Sources lifecycle

Raw inputs (transcripts, prior SOPs, notes) live **per area** under `_sources/`,
split into two subfolders:

- **`new/`** — you drop raw files here. Anything in `new/` is unconsumed work.
- **`processed/`** — once a source has been ingested into the procedures, it is
  **moved** here (by the orchestrator, never by hand), so `new/` always shows
  exactly what's outstanding.

Each source is registered in `_reference/sources.yaml` with an `SRC-` id, a
content hash, its state (`new` | `processed`), and a **`touches:` list of the
procedure slugs it informs** (tagged by `consult-taxonomy`). Procedures cite
`SRC-` ids in their Source Materials. The `touches` tags are what let the
orchestrator dispatch each parallel `consult-drafter` **only its relevant
sources** — no drafter re-reads every transcript. The **initial run** (M0)
consumes everything in `new/`; **later** a new file dropped in `new/` is what
triggers reassessment (M6) and re-dispatch of the drafters it touches.

> Real client data: `_sources/` and the engagement folder can be gitignored (or
> the whole thing kept in a private repo) — same rule as the original system.

### What the reference registry is for (and isn't)

- **Primary purpose: intake grounding.** Messy transcripts don't say "AP Clerk"
  and "SAP S/4HANA" — they say "the AP lady" and "our system." The registry is
  the lookup a fill agent consults to **normalize ambiguous input into canonical
  names**, which it then writes as **plain text**.
- **Not a variable/token layer.** Procedures write canonical names directly;
  there are **no** `[[sys:…]]` / `[[role:…]]` tokens. (Procedure-to-procedure
  refs still use `[[slug]]` tokens — that's a separate, cheaper concern.)
- **Bonus: it drives the mechanical views.** Because names are canonical and the
  registry carries **aliases**, Python can match inline mentions back to registry
  entries (name + alias) to build the Systems and Role-Dictionary views. Mentions
  that match no entry/alias are **flagged, never silently dropped** — the human
  keeps the canonical list honest.

---

## Folder model (the primary artifact)

```
components/
  <l1-area>/                     one area = one "document" = its own git history
    _sources/                    raw input documents (see "Sources lifecycle")
      new/                       dropped here; not yet consumed → taxonomy reads these
      processed/                 moved here once ingested into procedures
    _review/                     procedure-anchored review notes (M8) → drafter, NOT taxonomy
      kits/                      per-owner review kits (M9, derived — regenerate at will)
      returned/                  drop kit returns here → advisor `ingest_returns` (M9/M10)
      .maps/                     render-time provenance sidecars (M10 apply anchors)
      processed/                 consumed reviewed .docx + applied notes, archived
    _assets/screens/<slug>/      captured screenshots (SC-id keyed) → final-mode embeds;
                                   hand-dropping a PNG here is as valid as the ingest script
    _reference/                  the noun database (human-confirmed)
      systems.yaml               canonical systems + aliases + description/limitations
      roles.yaml                 canonical functional roles + reports-to + people (person→role map)
      glossary.yaml              (optional) Appendix D terms
      sources.yaml               SRC- registry (source materials + hash + new|processed)
    _client/                     OPTIONAL human-dropped client context (never agent-written)
      org-chart.yaml             person → title map → roles.yaml `people` + reconcile name check
      taxonomy.yaml              client's own L1→L2→L3 map → L1 boundary authority at scoping
    00_document-profile.md       static (human-owned) — H2 sections
    04_process-overview.md       static (human-owned) — Purpose narrative
    10_<proc-slug>.md            procedure fragments (fill-agent/human-owned = SOURCE OF TRUTH)
    10_<proc-slug>.md            (band 10 = procedures; several share the band)
    ...
    06_procedure-index.md        derived, PYTHON-owned (In-Scope index; pure SELECT)
    07_role-dictionary.md        derived, PYTHON-owned (join from roles.yaml)
    08_systems.md                derived, PYTHON-owned (registry × consult-meta usage)
    82_dependencies.md           derived, agent-owned  (judgment: reads A. Process Overview)
    84_raci.md                   derived, agent-owned  (judgment: RACI matrix)
    88_appendix-a.md             derived, PYTHON-owned (PP + IO register: obs/impact/severity)
    90_appendix-b-gaps.md        derived, PYTHON-owned (pure mechanical)
    91_appendix-c-screens.md     derived, PYTHON-owned (pure mechanical)
    manifest.json                order, grouping, roles, ownership, title/subtitle
    .hashes.json                 per-derived-kind procedure-hash baseline (M5 change signal;
                                    {derived_kind: {slug: sha}}; written by scope_delta.py commit,
                                    the orchestrator's sole writer; git-ignored)
```

Filename prefixes are **coarse bands** (00–09 front matter — static sections
plus the reader-orientation views (index / roles / systems) that precede the
procedures; 10 procedures; 82+ derived back matter) for human browsing only.
**`manifest.json` `order` is the sole authority** for assembly/numbering; a
reorder edits `order`, never filenames (so per-file git history survives). In
`order` space the front-matter views sit at 6–8 and the derived back-matter at
prefix × 100 (8200+), far above the sparse procedure orders, so any realistic
procedure count fits below it. **`order` values are sparse** (assigned in gaps
of 10 — 10, 20, 30…) so a mid-sequence insert gets a value *between* its
neighbours and renumbers nothing else; only if a gap is exhausted does a local
renormalize happen (and it touches only the manifest, never filenames).

---

## Heading contract (the one rule)

- Exactly **one `#`** per *assembled* document — the title (held in the manifest,
  not in any fragment). Component files carry no `#`.
- **Every section is `##`.** `##` is the *only* thing that starts a new fragment.
- Inside a procedure fragment: A–H sub-sections are `###`, steps are `####`.
- Fenced code blocks are ignored for splitting — both ```` ``` ```` and `~~~`
  fences. Constraint (documented): ATX headings only; setext (`---` underline)
  headings are not recognized.

No numbered-module regex, no appendix regex, no "shallowest level" computation.

### Procedure identity, cross-references, and display number

- **Identity = a stable `slug`**, assigned **once at creation** (by M0 scaffold,
  or by M2 import) and stored in the manifest. Tooling never re-derives it;
  renaming a heading does not change it.
- **Procedure→procedure cross-references use `[[<slug>]]` tokens.** Never a number,
  never a copied title. (Nouns — systems/roles — are plain canonical text, not
  tokens.)
- **Display number (`1.1`) = derived, rendered late.** One shared helper
  `display_numbers(manifest) -> {slug: "L2.seq"}` is the *only* implementation of
  the number. It is `{L2-ordinal}.{activity-seq}`: the L2 bucket's ordinal is its
  1-based position in the manifest's **`l2_order`** list; the activity seq is the
  procedure's 1-based position within that bucket (by `order`). So Close's
  activities are 1.1, 1.2; Consolidation's are 2.1, 2.2. `l2_order` (not the
  immutable taxonomy) is the ordering authority, so **approved new L2 buckets get
  an ordinal** by being appended to it at scaffold. At render time (M4) the docx
  builder prefixes procedure headings and resolves `[[slug]]` tokens via this map.
  Numbers live in exactly one place and cannot drift.
- Callout IDs are **scoped to their procedure** (see below), independent of the
  number, so reordering never cascades.

### Callout ID scoping (parallel-authoring safe)

Fill agents run in parallel, so globally-sequential IDs would collide. IDs are
**local to their procedure**: drafters always number from 01 (`CTRL-01` in
`bank-reconciliation` and `CTRL-01` in `asset-disposal` are distinct) — they
never need to know their place in the document. Global identity is the tuple
`(slug, local-id)`, and the files on disk are stable for the life of the
procedure — never renumbered — which keeps review anchors, diffs, and change
hashes audit-friendly under add/remove/reorder.

**What the reader sees is different**: global sequential numbering is a
**display transform**, derived at generation time by
`doc_model.callout_display_ids(folder)` (the single numbering authority,
mirroring `display_numbers`): walk procedures in manifest order, hand out one
2-digit counter per prefix across the document (`GAP-01…`, `PP-01…`; naturally
3 digits past 99). `render.py` rewrites IDs inside each procedure section
(context makes locals unambiguous) and `aggregate.py` consumes the same map
when writing derived rows — body and appendices always agree, and no reader
ever sees a duplicate ID. Appendix rows are grouped by **L2 sub-process**
(`#### <L2 title>`), each row carrying its `[[slug]]` token in the last
(Procedure) column — reconcile pairs `(slug, display-id)` from those two
positions. Agent-owned sections must NOT quote callout IDs (they are not
rewritten there); they reference `[[slug]]` and describe the item in words.

---

## `manifest.json` schema (v1)

```jsonc
{
  "schema": "consult-mvp-manifest/v1",
  "area": "fixed-assets",
  "l1": "record-to-report",                         // prescribed L1 function (slug from the taxonomy)
  "l2_order": ["pre-close-set-up","close","consolidation"],  // the area's L2 buckets IN ORDER
                                                    //   (taxonomy order + any approved new buckets
                                                    //    appended). display_numbers reads THIS, not
                                                    //    the immutable taxonomy.
  "title": "Fixed Assets — Desktop Procedures",
  "subtitle": "Current-state desktop procedures",   // optional; drives docx cover subtitle
  "components": [
    { "file": "00_document-profile.md", "role": "static",
      "heading": "Document Profile", "order": 0 },

    { "file": "10_bank-reconciliation.md", "role": "procedure",
      "slug": "bank-reconciliation", "heading": "Bank Reconciliation",
      "l2": "close", "order": 10,
      "upstream": ["cash-application"] },              // optional M11 ordering hint
                                                       //   (taxonomy-decided, scaffold-
                                                       //    validated): drafted after these

    { "file": "08_systems.md", "role": "derived", "derived_kind": "systems",
      "writer": "python", "heading": "Systems & Data Inputs", "order": 81 },

    { "file": "82_dependencies.md", "role": "derived", "derived_kind": "dependencies",
      "writer": "agent", "heading": "Key Dependencies", "order": 82 }
  ]
}
```

- `role` ∈ `static` | `procedure` | `derived`.
  - `static` = human-owned, non-procedure, not generated.
  - `procedure` = source of truth; carries `slug` + `l2` (the L2 sub-process
    bucket slug it files under — from the reference taxonomy, or an approved new
    bucket). An L3 activity = one procedure; the L2 bucket is its group.
  - `derived` = generated; carries `derived_kind` and **exactly one** `writer`
    ∈ `python` | `agent`. There are no split-writer files (see below).
- `role` is authoritative — read from the manifest, never re-inferred at steady
  state.

---

## Ownership rule (ONE writer per file — no exceptions)

Every file has exactly one writer. Where a section mixes mechanical and judgment
content, it is **two files**, joined at render (M4) — never one file with two
writers. This is the first review's rule, restored; region markers are gone.

| File | Writer | Contents |
|---|---|---|
| `_reference/*.yaml` | human (seeded by M0 agent, confirmed at gate) | the noun database |
| `_client/*.yaml` | human only (optional) | client context: org chart, client taxonomy — read by M0 agent + reconcile |
| `00–04_*` static | human | Document Profile, How to Use, Control, Sources, Process Overview |
| `10_<slug>` procedure | fill agent / human | the source of truth |
| `06_procedure-index` | Python | In-Scope index (pure SELECT) |
| `07_role-dictionary` | Python | join from `roles.yaml` + "Appears In" usage |
| `08_systems` | Python | registry × `consult-meta` usage join |
| `82_dependencies` | agent | reads each procedure's A. Process Overview |
| `84_raci` | agent | RACI matrix (seeded by M3's role×procedure grid) |
| `88_appendix-a` | Python | PP + IO register: id, type, observation, impact, severity, `[[slug]]` |
| `90_appendix-b-gaps`, `91_appendix-c-screens` | Python | pure mechanical |

**Appendix A is fully mechanical.** The drafter authors complete PP/IO callouts
(observation + impact + per-item severity) in each procedure's `H` section; M3
aggregates them into `88_appendix-a` like the gap log / screenshot index. There is
**no** Appendix-A judgment agent and no render-join — the register needs no
cross-procedure synthesis. (Cross-area prioritization / effort×impact roadmap is a
separate *decision deliverable*, out of MVP scope.)

Every derived writer re-emits the section's `<!-- derived: KIND; writer: W -->`
marker; `reconcile.py` errors if a declared derived file is missing it.

For agent-owned derived files, Python produces an **extract bundle** (scratch
JSON, git-ignored) plus the agent's **prior file** so the agent preserves judgment
for unaffected rows without a synthetic key.

---

## Extraction / matching contract (what Python reads from procedures)

**Strict IDs → Python owns them (fail-loud on malformed grammar):**
- **Inline callout IDs** — `> **<LABEL> — <ID>:** <text>`. Delimiter parsed
  tolerantly (`-`/`–`/`—`); ID grammar strict; IDs are procedure-local. LABEL→prefix:

  | Label | ID prefix |
  |---|---|
  | CONTROL | `CTRL-` |
  | VALIDATION REQUIRED | `GAP-` |
  | PAIN POINT | `PP-` |
  | IMPROVEMENT OPPORTUNITY | `IO-` |
  | SCREENSHOT PLACEHOLDER | `SC-` |

- **Body gap tags** `[[GAP-NN — TEXT]]` (bare `[[GAP — …]]` = ERROR). `doc_model.resolve_tokens`
  deliberately skips them (they aren't procedure cross-refs); `render.py` flags any that reach
  the docx as a bold `[GAP-NN — TEXT]` marker so an unresolved gap is never silently invisible.
- **Callout sub-fields** — a callout's structured fields are blockquote bullet
  lines directly under its label line, grammar `> - **<Field>:** <value>` (bold
  label, colon inside the bold, value after). M3 parses these deterministically.
  Fields by callout type (a **missing optional field parses as blank, not an
  error**; only ID-grammar defects fail loud):
  - CONTROL: `Type` (Preventive|Detective|Corrective), `Frequency`, `Owner`
  - PAIN POINT: `Impact`, `Severity` (**enum: High|Medium|Low**)
  - IMPROVEMENT OPPORTUNITY: `Addresses` (PP ids)
  - VALIDATION REQUIRED: `Nature` (unknown|conflict|unsupported-assumption), `Owner to confirm`

**Appendix A rows are typed** (PP and IO have different columns — do not force one
shape): a PP row = `{id, observation, impact, severity, [[slug]]}`; an IO row =
`{id, recommendation, addresses, [[slug]]}`. M3 renders them as two sub-tables (or
one table with type-appropriate blank cells) — never demands impact/severity on an
IO row.

All ID checks are **per-fragment** (a fragment is one procedure). IDs are
procedure-local, so extraction parses each procedure file independently and keys
every ID on the `(slug, local-id)` pair; there is **no** global ID namespace. A
reference is only reconciled within its own fragment; derived tables carry the
`(slug, id)` pair via their Source-Procedure column. (This is why `reconcile.py`
needs a real rewrite — see M2 — not just "keep the ID checks.")

Errors (nonzero exit, nothing dropped): bare gap tag; referenced-but-undefined ID
**within a procedure**; ID prefix not matching its label; conflicting duplicate ID
**within a procedure**. The label↔prefix check is **new code owned by M3**.

**Noun binding → explicit slug list, no prose-scraping (robustness fix).**
Python does **not** fuzzy-match free-text system/role names out of prose. Each
procedure fragment carries a machine-readable **`consult-meta` block** (see below)
in which the fill agent lists the **registry slugs** it used. Python reads that
slug list directly — no regex over prose, no alias guessing. The canonical names
still appear in the human-readable prose (Quick Reference etc.) for the reader,
but they are *not* the machine binding; the slug list is.
- A slug in `consult-meta` that isn't in `_reference/*.yaml` → **WARNING** (human
  adds the entry/alias), never dropped, never guessed.
- Prose is never scanned for systems/roles — so no brittle scraper and no silent
  miss; the agent's explicit list is the single source.

### The `consult-meta` block (per procedure)

A fenced block with info-string `consult-meta` (YAML body), placed as **end
matter** at the bottom of each procedure fragment:

````md
```consult-meta
systems: [sap, blackline]     # registry slugs this procedure uses
roles:   [ap-clerk, controller]
```
````

- The splitter **already** ignores fenced blocks, so it needs no special-casing.
- The docx builder (M4) **skips** any `consult-meta` fence — it never renders.
- `reconcile.py` checks every slug against `_reference/`; an **unresolved slug is a
  WARNING, not an ERROR** (it names a real noun the registry doesn't have yet —
  the human top-up loop resolves it; it must not block the area). ERRORs are
  reserved for ID-grammar defects, dangling `[[slug]]`, duplicate `order`,
  missing derived markers, and named individuals (below).
- **Individuals are referred to by role, never by name.** `roles.yaml` entries
  carry a `people:` list (seeded from `_client/org-chart.yaml` when provided);
  `reconcile.py` scans procedure + derived prose for those names — a full name
  is an **ERROR**, a standalone first/last name a **WARNING** (could be a
  coincidence; the human judges). Static front matter is exempt (the Document
  Profile legitimately credits interviewees).
- This is the ONLY structured emission the fill agent produces beyond the prose
  (decision (a) — minimal). IDs stay as strict-grammar callouts in prose.

**Prose → agent (not mechanical):**
- **Dependencies** — the agent reads each procedure's `A. Process Overview`.
  Python does not extract these.

**Appendix A single-source rule:** the inline `PP-`/`IO-` callout is the **sole
structured source** for Appendix A. `H. Known Issues` is free narrative, **not
parsed** (no double-write with the agent judgment cells).

---

## The one entry point: `consult-orchestrate`

You never run Python by hand. **`consult-orchestrate`** (M7) is the single skill
you invoke ("build / continue fixed-assets"). It inspects folder state, runs the
right script or **dispatches the right subagent** for the next phase, moves
consumed sources `new/` → `processed/`, and **pauses at the two human gates** (the
scaffold confirm gate, and the Word-review re-entry). Everything below is what it
drives under the hood.

### Context-isolation principle (load-bearing)

The orchestrator is a **thin coordinator**. Every unit of judgment work runs as a
**separate subagent in its own context** (a tool-scoped agent type under
`.claude/agents/`, one per stage), returning only a compact result. The
orchestrator does **not** run a skill's drafting inline — it never pulls
transcripts, drafts, or source text into its own context. It only: runs
deterministic Python, spawns subagents and collects their small returns, moves
files, and stops at gates. This is what keeps the orchestrator's context flat no
matter how large the engagement gets, and it's why fan-out (one fill subagent per
procedure) is cheap and parallel.

**Agent roster** (each a `.claude/agents/` def that preloads its skill brief,
tool-scoped, run by the orchestrator — never inline):

| Stage | Subagent | Writes |
|---|---|---|
| scope + registry | `consult-taxonomy` | `_reference/.proposed/*` |
| fill (one per procedure, parallel) | `consult-drafter` | `10_<slug>.md` |
| dependencies | `consult-dependencies` | `82_dependencies.md` |
| RACI | `consult-raci` | `84_raci.md` |

Deterministic stages (`scaffold`, `aggregate`, `render`, `reconcile`,
`scope_delta`, `kits`, and the whole review return-trip — `screens_ingest`,
`gaps_ingest`, `review_apply`, `review_extract`) are plain Python the
orchestrator runs directly — no agent.

### The review loop is person-shaped and mostly deterministic (M9/M10)

A working-mode render also emits **per-owner review kits**
(`_review/kits/<person>/`): the per-L3 docs that person owns (tracked changes
on by default), a gap workbook, and a screenshot template — ownership resolved
Preparer role → `roles.yaml people:` → lowest org-chart rank. Returned files
drop into `_review/returned/`; the advisor's `ingest_returns` action then runs,
zero-token: screenshots → `_assets/screens/`, workbook answers → notes,
**tracked changes applied mechanically** (render-time provenance anchors +
verify-or-revert; anything unverifiable becomes a note), comments → notes.
Only the notes — the judgment layer — reach drafters. `render.py --mode final`
produces the client deliverable: open gaps stripped (count reported), captured
screenshots embedded with italic captions.

### Drafting order is hint-driven and optional (M11)

Taxonomy may stamp a procedure with `upstream: [slugs]` when the sources
clearly show it consuming another procedure's output. Scaffold validates the
hints into the manifest; the advisor's `fill` then returns **waves** — only
slugs whose upstreams are already drafted, the rest `deferred` — and lists
`upstream_files` so downstream drafters get their upstream fragments as
**read-only seam context** (never edited; conflicts become GAPs). No hints →
one wave, exactly the pre-M11 behavior. Wave progress is carried by the
existing `unfilled` sentinels — no new state. Drafters also share a cheap
terminology digest under `_reference/conventions/` (one file per slug,
advisory, not hashed into any signal).

### Tests

`python3 -m pytest tests/` (CI runs it on every push/PR — see
`.github/workflows/tests.yml`). Tests build synthetic areas under pytest
`tmp_path` and pin the observable contracts: advisor precedence + M11 waves,
scaffold manifest rules, aggregate/reconcile checks, render modes + numbering
+ provenance, kits/ingest round-trips, and the M10 verified-or-fallback apply.

## Build order (a real DAG)

`doc_model.py` (M2's foundation deliverable) is imported by M0, M3, M4, M5, so it
is built **first**. The legacy import splitter (also M2) is optional and can come
last. `consult-orchestrate` (M7) wraps the finished phases and is built last.

```
M1 (template = A–H skeleton source) ┐
M2·doc_model.py (shared spine)      ┴─▶ M0 (taxonomy + registry + confirm + scaffold)
                                          │
                                          ▼  fill agents (parallel)
                                        M3 (mechanical views) ──▶ M5 (RACI · dependencies)
                                          │                          │
                                        M4 (docx builder) ◀──────────┘
M2·import-splitter = legacy single-file .md → folder (optional, last)
M8 (review loop: Word tracked-changes + comments → drafter) — after M4
M6 (taxonomy/registry REASSESSMENT on new sources) — DEFERRED
M9/M10 (per-owner review kits + deterministic tracked-changes apply) — BUILT
M11 (dependency-ordered drafting waves + upstream context) — BUILT, off unless hinted
```

### Designed, not yet built (in build order)

| Ticket | What | Why it's in this order |
|---|---|---|
| M12 | **Consolidator** — whole-area consistency pass, notes only | the real answer to cross-procedure drift; open questions now settled (propose-only on provenance grounds, mechanical `naming` majority, per-bucket cap). Build **last** (it needs the whole pipeline in place) but **run early** — at M17's draft-ready gate, before `synthesize`, so its note churn precedes the tail instead of forcing a second pass |
| M13 | Engagement-level `_client/` config resolution | small; unblocks sharing client context across areas (and M14's profile) |
| M14 | Document profile — which sections/callouts/derived views exist, changeable mid-engagement | depends on M13 for where the profile lives |
| ~~M15~~ | ~~Verbosity measured, not capped~~ | **RETIRED into M16** — measurement proved low-signal; its field caps and the no-length-checks-in-reconcile decision are carried there |
| M16 | **Section model — one home per fact** (7 sections, tag-on-change, callout `note`/`detail`, step `Condition:`) | a repetition fix, not a length fix; four independently shippable moves, cheapest first — M14 supplies the migration guard |
| M17 | **Stage gates** — draft-ready boundary (guard 8.5) + sticky `hold:` list | the ladder never stops between `fill` and `review`, so the "am I happy with the verbs and nouns?" decision lands after the spend. Gate ships alone; holds need M13 |

**Two "new input" folders, routed by folder (deterministic):** `_sources/new/`
(raw docs) → `consult-taxonomy` (it reads them to tag `touches` + detect scope
deltas). `_review/` (procedure-anchored notes from `review_extract.py`, M8) →
straight to `consult-drafter` update mode, **skipping taxonomy**. The router never
guesses content — the folder decides.

- **After M1 + M2·doc_model + M0 + fill + M3 + M4**: a full document renders —
  procedures, In-Scope index, Systems, Role Dictionary, Appendix B/C are real.
  Dependencies, RACI, and Appendix-A judgment show `> _Pending synthesis (M5)._`.
- **Registry top-up is part of this milestone's DoD, not deferred:** M3's
  unmatched-mention WARNINGs drive a human loop — add the entry/alias to
  `_reference/`, re-run aggregate — so Systems/Roles are complete before sign-off.
  M6 only automates the *incremental* reassessment when new sources arrive later.
- **M5** fills the remaining judgment. **M6** is deferred.

## Credibility guardrail (carried over from the original system)

Registry `description` / `limitations` and any lens-like assertion about the
client's real systems must be **sourced from the transcript or left blank/TBD —
never invented.** The M0 agent cites the source line or emits nothing. Rendering
a guessed "known limitation" as fact is the same anchoring defect the original
taxonomy-baselines guardrail prohibits.

## Robustness posture

The brittleness in a Python-heavy pipeline concentrates in one place: parsing
loosely-structured, agent-written Markdown. The design contains it by (1) binding
nouns via the explicit `consult-meta` slug list instead of scraping prose; (2)
keeping callout IDs to a strict line grammar (tolerant only on the delimiter);
(3) **failing loud** — never silently dropping or guessing; (4) pinning behavior
with **golden-fixture tests** (below). The remaining Python is deterministic
work over structured data (JSON/YAML/hashes), which is low-risk. Escape hatch: if
any single parse stage proves brittle in practice, it can be replaced by a
subagent read (trade a few tokens for robustness) without touching the rest — the
orchestrator already dispatches subagents.

**Script layout.** All engine scripts the orchestrator/agents invoke live under a
**top-level `scripts/`** (`doc_model.py`, `reconcile.py`, `scaffold.py`,
`aggregate.py`, `scope_delta.py`, `orchestrate.py`, `sources.py`,
`review_extract.py`, and the renderer). Agents/skill run them from the repo root
as `python3 scripts/<name>.py …` (matching the agent Bash allow-patterns). The
legacy `reconcile.py`/`split_doc.py` under `skills/consult-drafter/scripts/` move
here. (They may instead be one `consult` CLI with subcommands — implementer's
choice — but the invocation prefix `scripts/` stays stable so tool patterns hold.)

The **legacy import splitter is deferred out of the MVP** — folders are born via
M0 scaffold, so it's not on the critical path; build it only if importing an
existing single-file SOP is actually needed.

## Definition of done (every ticket)

Code + prescribed tests written and passing; **a golden-fixture check** (a
committed sample area + expected outputs, re-run to catch regressions loudly);
`manifest.json` and `_reference/*` still validate; no scratch artifacts committed;
a one-paragraph report of what was built, the test output, and any contract
deviation.
