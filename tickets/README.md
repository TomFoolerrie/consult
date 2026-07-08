# CONSULT MVP — Build Tickets

Shared architecture for the MVP rebuild. Every ticket (M1–M6) references the
contracts defined here so the individual tickets don't restate them. Read this
first.

> **Revision note.** This spec was revised after an adversarial full-system
> review. The key changes from the first draft: procedure display numbers are
> **never baked into content** — derived views reference procedures by a stable
> `[[slug]]` token and numbers are resolved at render time by one shared helper;
> `split` is a **one-shot bootstrap** (the folder is authoritative afterward);
> role `frontmatter` is renamed `static`; the In-Scope index is python-owned;
> the change signal is a **content hash** (not git-diff). Per-finding traceability
> is at the bottom of each ticket.

---

## The thesis

**Procedures are the database; everything else is a generated view.**

An engagement area is a folder of Markdown component files. The **L3 procedure
fragments hold every primary fact** (systems, controls, pain points, gaps,
screenshots, roles). All other sections — Roles & Responsibilities, Systems &
Data Inputs, Key Dependencies, and the Appendices — are **projections** of the
procedures, regenerated rather than hand-maintained.

Humans edit the component files directly. Reviewers read the rendered Word
document. The assembled single `.md` is **not** an artifact — it exists only
transiently inside the docx build.

---

## Folder model (the primary artifact)

```
components/
  <l1-area>/                 one area = one "document" = its own git history
    00_document-profile.md   static (human-owned) — H2 sections
    01_how-to-use.md
    02_document-control.md
    03_source-materials.md
    04_process-overview.md    static (human-owned) — Purpose narrative
    10_<proc-slug>.md        procedure fragments (human/drafter-owned = SOURCE OF TRUTH)
    10_<proc-slug>.md         (band 10 = procedures; multiple share the band)
    ...
    70_procedure-index.md    derived, PYTHON-owned (In-Scope index; pure SELECT)
    80_roles.md              derived, agent-owned  (judgment)
    81_systems.md            derived, agent-owned  (judgment)
    82_dependencies.md       derived, agent-owned  (judgment)
    88_appendix-a-risks.md   derived, agent-owned  (mechanical rows + judgment cells)
    90_appendix-b-gaps.md    derived, PYTHON-owned (pure mechanical)
    91_appendix-c-screens.md derived, PYTHON-owned (pure mechanical)
    manifest.json            order, grouping, roles, ownership, title/subtitle
    .hashes.json             per-procedure content hashes (M5 change signal; git-ignored)
```

Filename prefixes are **coarse bands** (00–09 static, 10–69 procedures, 70–79
python-derived index, 80–89 agent-derived, 90–99 python-derived appendices) for
human browsing only — several files share a band and are disambiguated by slug.
**`manifest.json` `order` is the sole authority** for assembly/numbering; a
reorder edits `order`, never filenames (so per-file git history survives).

---

## Heading contract (the one rule)

- Exactly **one `#`** per *assembled* document — the title (held in the manifest,
  not in any fragment). Component files carry no `#`.
- **Every section is `##`.** `##` is the *only* thing that starts a new fragment.
- Inside a procedure fragment: A–H sub-sections are `###`, steps are `####`.
  Nothing below `##` ever causes a split.
- Fenced code blocks are ignored for splitting — both ```` ``` ```` and `~~~`
  fences. Constraint (documented, not a bug): ATX headings only; setext (`---`
  underline) headings are not recognized as sections.

That is the entire split rule. No numbered-module regex, no appendix regex, no
"shallowest level" computation.

### Procedure identity, cross-references, and display number

- **Identity = a stable `slug`**, assigned **once at creation** and stored in the
  manifest. Tooling never re-derives it. Renaming a heading does **not** change
  the slug (see "split is a one-shot bootstrap").
- **Cross-references use the slug token `[[<slug>]]`.** Any derived view that
  needs to point at a procedure emits `[[bank-reconciliation]]` — never a number,
  never a title copy. Stable across every reorder/rename.
- **Display number (`1.1`, `2.3`) = derived and rendered late.** A single shared
  helper `display_numbers(manifest) -> {slug: "g.s"}` (in a shared module) is the
  *only* implementation of "group.sequence." At render time (M4) the docx builder
  (a) prefixes each procedure heading with its number and (b) resolves every
  `[[slug]]` token to that number (optionally `number + title`). `reconcile.py`
  uses the same helper to validate tokens resolve. Numbers therefore live in
  exactly one place and can never drift between reconcile, aggregator, and render.
- Callout IDs (`CTRL-`, `PP-`, `IO-`, `GAP-`, `SC-`, `SRC-`) are independent of
  the procedure number, so reordering never cascades.

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

    { "file": "70_procedure-index.md", "role": "derived", "derived_kind": "procedure-index",
      "writer": "python", "heading": "In-Scope Sub-Processes", "order": 70 },

    { "file": "80_roles.md", "role": "derived", "derived_kind": "roles",
      "writer": "agent", "heading": "Roles & Responsibilities", "order": 80 },

    { "file": "90_appendix-b-gaps.md", "role": "derived", "derived_kind": "gap-log",
      "writer": "python", "heading": "Appendix B | Gap / Validation Log", "order": 90 }
  ]
}
```

Fields:
- `role` ∈ `static` | `procedure` | `derived`.
  - `static` = human-owned, non-procedure, not generated (Document Profile, How to
    Use, Document Control, Source Materials, Process Overview / Purpose).
  - `procedure` = source of truth; carries `slug` (identity) and `group` (int,
    default 1; the "1.x / 2.x" clustering as data, no header needed).
  - `derived` = generated; carries `derived_kind` and `writer` ∈ `python` | `agent`.
- `order` sorts everything; display number for a procedure =
  `{group}.{1-based index within its group, ordered by order}`, from the helper.
- **`role` is authoritative** — read from the manifest, never re-inferred from
  file content at steady state (see bootstrap note).

---

## Ownership rule (no file has two writers)

| Fragment kind | Writer | Contents |
|---|---|---|
| static | human | Document Profile, How to Use, Control, Sources, Process Overview |
| procedure | human / drafter | the source of truth |
| derived `procedure-index` | **Python** | In-Scope index (pure SELECT), full rebuild |
| derived `gap-log`, `screenshot-index` | **Python** | full file rebuilt every run |
| derived `roles`, `systems`, `dependencies`, `risks` | **agent** | agent writes the whole file, copies Python-extracted mechanical rows through verbatim, reasons only on judgment cells |

Python and an agent never write the same file. For agent-owned derived files,
Python produces an **extract bundle** (scratch JSON, git-ignored, never committed)
that the agent consumes; the agent is also handed **its own prior file** so it can
preserve judgment cells for unaffected rows (no brittle synthetic join key needed).

Every derived-file writer (python and agent) **must re-emit the section's
`<!-- derived: KIND; writer: W -->` marker**; `reconcile.py` errors if a
manifest-declared derived file is missing its matching marker.

---

## Extraction contract (what Python reads from procedures)

Deterministic where the syntax is strict; **honest about where it isn't.**

**Strict → Python owns it (fail-loud on malformed ID grammar):**
- **Inline callout IDs** — blockquote lines `> **<LABEL> — <ID>:** <text>`.
  The delimiter is parsed **tolerantly** (accept `-`, `–`, `—` and surrounding
  spaces); the **ID grammar is strict**. LABEL→prefix map (a referenced ID whose
  prefix doesn't match its label is an ERROR):

  | Label | ID prefix |
  |---|---|
  | CONTROL | `CTRL-` |
  | VALIDATION REQUIRED | `GAP-` |
  | PAIN POINT | `PP-` |
  | IMPROVEMENT OPPORTUNITY | `IO-` |
  | SCREENSHOT PLACEHOLDER | `SC-` |

- **Body gap tags** — `[[GAP-NN — TEXT]]`. A bare `[[GAP — …]]` with no ID is an
  ERROR.
- **Table-defined IDs** — rows in `F. Key Controls` (CTRL-), etc.

Errors (nonzero exit, nothing dropped silently): bare gap tag; ID referenced but
never defined; ID whose prefix doesn't match its callout label; duplicate ID with
conflicting text. This label↔prefix check is **new code owned by M3** (today's
`reconcile.py` does not do it).

**Not strict → NOT mechanical; the agent reads it (M5):**
- **Systems** — Python emits a **raw, un-deduped mention list** (the literal
  strings from `B. Quick Reference` "Primary systems / tools" and step
  `**System:**` fields) each tagged with its source procedure slug. Canonicalizing
  / deduping ("SAP" vs "SAP S/4") is the **systems agent's** job, not Python's.
- **Dependencies** — a straight **agent read** of each procedure's
  `A. Process Overview` prose. Python does not attempt to extract these.
- **Roles** — Python emits the raw Preparer/Reviewer strings from `B. Quick
  Reference`, tagged by procedure; the roles agent canonicalizes and assigns RACI.

**Appendix A single-source rule:** the inline `PP-`/`IO-` callout is the **sole
structured source** for Appendix A. The procedure's `H. Known Issues` section is
free narrative for the preparer and is **not parsed** — this prevents a
double-write between H's prose and the agent-authored Impact/Recommendation cells.

---

## Build order

```
M1 (template) ─┬─▶ M2 (split/manifest + shared helper) ─▶ M3 (mechanical aggregator) ─▶ M5 (synthesis agents)
               └─▶ M4 (docx builder: structured input) ──────────────────────────────┘
M6 (scoping / taxonomy reassessment) — DEFERRED, do not build yet
```

- After **M3 + M4**: procedures render, plus Appendix B/C and the In-Scope index
  are real. Roles / Systems / Dependencies / Appendix A are agent-owned (M5) — M3
  writes a **"pending synthesis" placeholder** into those files so the interim
  Word doc shows an explicit pending state, not raw `TBD` rows.
- **M5** is the synthesis layer (pure upside).
- **M6** is stubbed so the design isn't lost; explicitly out of MVP scope.

## Definition of done (every ticket)

Code + prescribed tests written and passing; `manifest.json` still validates;
no scratch artifacts committed; a one-paragraph report of what was built, the
test output, and any contract deviation.
