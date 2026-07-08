# CONSULT MVP — Build Tickets

Shared architecture for the MVP rebuild. Every ticket (M0–M6) references the
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
content hash, and its state (`new` | `processed`); procedures cite `SRC-` ids in
their Source Materials. The **initial run** (M0) consumes everything in `new/`;
**later** a new file dropped in `new/` is what triggers reassessment (M6). Fill
and synthesis agents read from `_sources/` (both subfolders) + `sources.yaml` to
ground their drafting.

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
      new/                       dropped here; not yet consumed
      processed/                 moved here once ingested into procedures
    _reference/                  the noun database (human-confirmed)
      systems.yaml               canonical systems + aliases + description/limitations
      roles.yaml                 canonical functional roles + reports-to + responsibilities
      glossary.yaml              (optional) Appendix D terms
      sources.yaml               SRC- registry (source materials + hash + new|processed)
    00_document-profile.md       static (human-owned) — H2 sections
    04_process-overview.md       static (human-owned) — Purpose narrative
    10_<proc-slug>.md            procedure fragments (fill-agent/human-owned = SOURCE OF TRUTH)
    10_<proc-slug>.md            (band 10 = procedures; several share the band)
    ...
    70_procedure-index.md        derived, PYTHON-owned (In-Scope index; pure SELECT)
    80_role-dictionary.md        derived, PYTHON-owned (join from roles.yaml)
    81_systems.md                derived, PYTHON-owned (registry × usage; Quick-Ref slot)
    82_dependencies.md           derived, agent-owned  (judgment: reads A. Process Overview)
    84_raci.md                   derived, agent-owned  (judgment: RACI matrix)
    88_risk-observations.md      derived, PYTHON-owned (PP-/IO- observation rows)
    89_risk-judgment.md          derived, agent-owned  (impact/priority/recommendation)
    90_appendix-b-gaps.md        derived, PYTHON-owned (pure mechanical)
    91_appendix-c-screens.md     derived, PYTHON-owned (pure mechanical)
    manifest.json                order, grouping, roles, ownership, title/subtitle
    .hashes.json                 per-procedure content hashes (M5 change signal; git-ignored)
```

Filename prefixes are **coarse bands** (00–09 static, 10–69 procedures, 70–99
derived) for human browsing only. **`manifest.json` `order` is the sole
authority** for assembly/numbering; a reorder edits `order`, never filenames (so
per-file git history survives). **`order` values are sparse** (assigned in gaps
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
  `display_numbers(manifest) -> {slug: "g.s"}` is the *only* implementation of
  group.sequence. At render time (M4) the docx builder prefixes procedure
  headings and resolves `[[slug]]` tokens via that map. Numbers live in exactly
  one place and cannot drift.
- Callout IDs are **scoped to their procedure** (see below), independent of the
  number, so reordering never cascades.

### Callout ID scoping (parallel-authoring safe)

Fill agents run in parallel, so globally-sequential IDs would collide. IDs are
**local to their procedure**: `CTRL-001` in `bank-reconciliation` and `CTRL-001`
in `asset-disposal` are distinct. Global identity is the tuple `(slug, local-id)`.
Derived tables (Appendix A/B/C, Controls) always carry a **Source Procedure**
column (a `[[slug]]` token), so the pair is unambiguous. IDs are stable for the
life of the procedure — never renumbered — which keeps them audit-friendly under
add/remove/reorder.

---

## `manifest.json` schema (v1)

```jsonc
{
  "schema": "consult-mvp-manifest/v1",
  "area": "fixed-assets",
  "title": "Fixed Assets — Desktop Procedures",
  "subtitle": "Current-state desktop procedures",   // optional; drives docx cover subtitle
  "components": [
    { "file": "00_document-profile.md", "role": "static",
      "heading": "Document Profile", "order": 0 },

    { "file": "10_bank-reconciliation.md", "role": "procedure",
      "slug": "bank-reconciliation", "heading": "Bank Reconciliation",
      "group": 1, "order": 10 },

    { "file": "81_systems.md", "role": "derived", "derived_kind": "systems",
      "writer": "python", "heading": "Systems & Data Inputs", "order": 81 },

    { "file": "82_dependencies.md", "role": "derived", "derived_kind": "dependencies",
      "writer": "agent", "heading": "Key Dependencies", "order": 82 }
  ]
}
```

- `role` ∈ `static` | `procedure` | `derived`.
  - `static` = human-owned, non-procedure, not generated.
  - `procedure` = source of truth; carries `slug` + `group` (int, default 1).
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
| `00–04_*` static | human | Document Profile, How to Use, Control, Sources, Process Overview |
| `10_<slug>` procedure | fill agent / human | the source of truth |
| `70_procedure-index` | Python | In-Scope index (pure SELECT) |
| `80_role-dictionary` | Python | join from `roles.yaml` + "Appears In" usage |
| `81_systems` | Python | registry × Quick-Ref usage join |
| `82_dependencies` | agent | reads each procedure's A. Process Overview |
| `84_raci` | agent | RACI matrix (seeded by M3's role×procedure grid) |
| `88_risk-observations` | Python | one row per `PP-`/`IO-` callout (id, observation, `[[slug]]`) |
| `89_risk-judgment` | agent | impact / priority / recommendation, keyed `(slug, id)` |
| `90_appendix-b-gaps`, `91_appendix-c-screens` | Python | pure mechanical |

**Appendix A render-join:** the Risks appendix the reader sees is one table. M4
joins `88_risk-observations` (Python) and `89_risk-judgment` (agent) on the
`(source-procedure slug, PP-/IO- id)` key at render time — so each side stays a
clean single-writer file while the output is one merged table. The join key is
stable (IDs are procedure-local and never renumbered), so the merge is
deterministic.

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

- **Body gap tags** `[[GAP-NN — TEXT]]` (bare `[[GAP — …]]` = ERROR).
- **Table-defined IDs** — `F. Key Controls` rows, etc.

All ID checks are **per-fragment** (a fragment is one procedure). IDs are
procedure-local, so extraction parses each procedure file independently and keys
every ID on the `(slug, local-id)` pair; there is **no** global ID namespace. A
reference is only reconciled within its own fragment; derived tables carry the
`(slug, id)` pair via their Source-Procedure column. (This is why `reconcile.py`
needs a real rewrite — see M2 — not just "keep the ID checks.")

Errors (nonzero exit, nothing dropped): bare gap tag; referenced-but-undefined ID
**within a procedure**; ID prefix not matching its label; conflicting duplicate ID
**within a procedure**. The label↔prefix check is **new code owned by M3**.

**Noun matching → registry-backed, flag-don't-drop:**
- **Systems**: the sole authoritative slot is `B. Quick Reference` → "Primary
  systems / tools". Fill agents **copy the registry `name` verbatim** into that
  slot (they have the registry in context), so Python matching against
  `systems.yaml` names + aliases is near-exact; aliases absorb human-written
  variants. **Step prose is NOT scanned** — a system used only in step narrative
  and never listed in Quick Reference is out of scope by design (documented, not a
  silent miss). A Quick-Ref mention matching no entry/alias → **WARNING** (human
  adds an entry/alias), never dropped, never guessed.
- **Roles**: same, from `B. Quick Reference` Preparer / Reviewer.

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
| risk judgment | `consult-risk-judgment` | `89_risk-judgment.md` |

Deterministic stages (`scaffold`, `aggregate`, `render`, `reconcile`,
`scope_delta`) are plain Python the orchestrator runs directly — no agent.

## Build order (a real DAG)

`doc_model.py` (M2's foundation deliverable) is imported by M0, M3, M4, M5, so it
is built **first**. The legacy import splitter (also M2) is optional and can come
last. `consult-orchestrate` (M7) wraps the finished phases and is built last.

```
M1 (template = A–H skeleton source) ┐
M2·doc_model.py (shared spine)      ┴─▶ M0 (taxonomy + registry + confirm + scaffold)
                                          │
                                          ▼  fill agents (parallel)
                                        M3 (mechanical views) ──▶ M5 (RACI · deps · risk-judgment)
                                          │                          │
                                        M4 (docx builder) ◀──────────┘
M2·import-splitter = legacy single-file .md → folder (optional, last)
M6 (taxonomy/registry REASSESSMENT on new sources) — DEFERRED
```

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

## Definition of done (every ticket)

Code + prescribed tests written and passing; `manifest.json` and `_reference/*`
still validate; no scratch artifacts committed; a one-paragraph report of what was
built, the test output, and any contract deviation.
