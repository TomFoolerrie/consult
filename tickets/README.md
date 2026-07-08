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
    _reference/                  the noun database (human-confirmed)
      systems.yaml               canonical systems + aliases + description/limitations
      roles.yaml                 canonical functional roles + reports-to + responsibilities
      glossary.yaml              (optional) Appendix D terms
      sources.yaml               SRC- registry (source materials)
    00_document-profile.md       static (human-owned) — H2 sections
    04_process-overview.md       static (human-owned) — Purpose narrative
    10_<proc-slug>.md            procedure fragments (fill-agent/human-owned = SOURCE OF TRUTH)
    10_<proc-slug>.md            (band 10 = procedures; several share the band)
    ...
    70_procedure-index.md        derived, PYTHON-owned (In-Scope index; pure SELECT)
    80_roles.md                  derived: Role Dictionary = PYTHON join; RACI = agent
    81_systems.md                derived, PYTHON-owned (registry × alias-matched usage)
    82_dependencies.md           derived, agent-owned  (judgment: reads A. Process Overview)
    88_appendix-a-risks.md       derived: mechanical rows (Python) + judgment cells (agent)
    90_appendix-b-gaps.md        derived, PYTHON-owned (pure mechanical)
    91_appendix-c-screens.md     derived, PYTHON-owned (pure mechanical)
    manifest.json                order, grouping, roles, ownership, title/subtitle
    .hashes.json                 per-procedure content hashes (M5 change signal; git-ignored)
```

Filename prefixes are **coarse bands** (00–09 static, 10–69 procedures, 70–79
python index, 80–89 mixed derived, 90–99 python appendices) for human browsing
only. **`manifest.json` `order` is the sole authority** for assembly/numbering; a
reorder edits `order`, never filenames (so per-file git history survives).

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
  - `derived` = generated; carries `derived_kind` and `writer` ∈ `python` | `agent`.
- The `roles` file (`80_`) is a **split-writer exception handled by a marker**,
  see below — Role Dictionary block is python, RACI block is agent.
- `role` is authoritative — read from the manifest, never re-inferred at steady
  state.

---

## Ownership rule (one writer per writable region)

| Fragment kind | Writer | Contents |
|---|---|---|
| `_reference/*.yaml` | human (seeded by M0 agent, confirmed at gate) | the noun database |
| static | human | Document Profile, How to Use, Control, Sources, Process Overview |
| procedure | fill agent / human | the source of truth |
| derived `procedure-index` | Python | In-Scope index (pure SELECT) |
| derived `systems` | Python | registry × alias-matched procedure usage |
| derived `gap-log`, `screenshot-index` | Python | full rebuild each run |
| derived `dependencies` | agent | reads each procedure's A. Process Overview |
| derived `risks` (Appendix A) | Python rows + agent judgment cells | observation = Python; impact/priority/recommendation = agent |
| derived `roles` (`80_`) | **split by marker** | Role Dictionary = Python join from `roles.yaml`; RACI = agent |

**Split-writer files** (`risks`, `roles`) use explicit region markers so python
and agent never touch the same bytes:

```md
<!-- region: mechanical; writer: python -->
… python-owned table (rebuilt each run) …
<!-- /region -->
<!-- region: judgment; writer: agent -->
… agent-owned table (RACI / impact cells) …
<!-- /region -->
```

Python rewrites only its region; the agent rewrites only its region; each leaves
the other's bytes untouched. Every derived writer re-emits the section's
`<!-- derived: KIND; writer: W -->` marker and its region markers; `reconcile.py`
errors if a declared derived file is missing them.

For agent-owned derived content, Python produces an **extract bundle** (scratch
JSON, git-ignored) plus the agent's **prior file** so the agent can preserve
judgment for unaffected rows without a synthetic key.

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

Errors (nonzero exit, nothing dropped): bare gap tag; referenced-but-undefined ID;
ID prefix not matching its label; conflicting duplicate ID **within a procedure**.
The label↔prefix check is **new code owned by M3**.

**Noun matching → registry-backed, flag-don't-drop:**
- **Systems / roles**: Python takes the canonical plain-text mentions from
  `B. Quick Reference` ("Primary systems / tools", Preparer/Reviewer) and step
  `**System:**` fields and matches them against `systems.yaml` / `roles.yaml`
  **names + aliases**. A mention that matches nothing → **WARNING (flagged for the
  human to add an entry/alias)**, never dropped, never guessed.

**Prose → agent (not mechanical):**
- **Dependencies** — the agent reads each procedure's `A. Process Overview`.
  Python does not extract these.

**Appendix A single-source rule:** the inline `PP-`/`IO-` callout is the **sole
structured source** for Appendix A. `H. Known Issues` is free narrative, **not
parsed** (no double-write with the agent judgment cells).

---

## Build order

```
M0 (taxonomy + registry + scaffold) ─▶ fill agents (parallel) ─▶ M3 (mechanical views) ─▶ M5 (RACI/deps/risk judgment)
                                                                       │
                        M1 (template = A–H skeleton source) ┐          │
                        M4 (docx builder) ──────────────────┴──────────┘
M2 (split) = legacy IMPORT path only (single-file .md → folder)
M6 (taxonomy/registry REASSESSMENT on new sources) — DEFERRED
```

- After **M0 + fill + M3 + M4**: a full document renders — procedures, In-Scope
  index, Systems, Role Dictionary, Appendix B/C are real. Dependencies, RACI, and
  Appendix-A judgment show a `> _Pending synthesis (M5)._` placeholder.
- **M5** fills the remaining judgment. **M6** (reassessment) is deferred.

## Definition of done (every ticket)

Code + prescribed tests written and passing; `manifest.json` and `_reference/*`
still validate; no scratch artifacts committed; a one-paragraph report of what was
built, the test output, and any contract deviation.
