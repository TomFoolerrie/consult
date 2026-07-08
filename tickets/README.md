# CONSULT MVP — Build Tickets

Shared architecture for the MVP rebuild. Every ticket (M1–M6) references the
contracts defined here so the individual tickets don't restate them. Read this
first.

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
    00_document-profile.md   frontmatter (H2 sections, human-owned)
    01_how-to-use.md
    02_document-control.md
    03_source-materials.md
    10_<proc-slug>.md        procedure fragments (human/drafter-owned = SOURCE OF TRUTH)
    11_<proc-slug>.md
    ...
    80_roles.md              derived, agent-owned  (judgment)
    81_systems.md            derived, agent-owned  (judgment)
    82_dependencies.md       derived, agent-owned  (judgment)
    88_appendix-a-risks.md   derived, agent-owned  (mechanical rows + judgment cells)
    90_appendix-b-gaps.md    derived, PYTHON-owned (pure mechanical)
    91_appendix-c-screens.md derived, PYTHON-owned (pure mechanical)
    manifest.json            order, grouping, roles, ownership
```

Filename numeric prefixes are just a sort convenience; **`manifest.json` is
authoritative** for order and role.

---

## Heading contract (the one rule)

- Exactly **one `#`** per assembled document — the title. Component files carry
  no `#`; the title lives in the manifest / frontmatter.
- **Every section is `##`.** `##` is the *only* thing that starts a new fragment.
- Inside a procedure fragment: A–H sub-sections are `###`, steps are `####`.
  Nothing below `##` ever causes a split.
- Headings inside fenced code blocks (```` ``` ````) are ignored.

That is the entire split rule. No numbered-module regex, no appendix regex, no
"shallowest level" computation.

### Procedure identity vs. display number

- **Identity = a stable `slug`** (the durable part of the filename, e.g.
  `bank-reconciliation`). Set once, never changed by tooling.
- **Display number (`1.1`, `2.3`) = derived**, computed at render time as
  `{group}.{sequence-within-group}` from the manifest. Never authored into the
  heading text (headings hold the plain title only).
- Cross-reference IDs (`CTRL-`, `PP-`, `IO-`, `GAP-`, `SC-`, `SRC-`) are
  independent of the procedure number, so reordering/renumbering never cascades.

---

## `manifest.json` schema (v1)

```jsonc
{
  "schema": "consult-mvp-manifest/v1",
  "area": "fixed-assets",
  "title": "Fixed Assets — Desktop Procedures",
  "components": [
    { "file": "00_document-profile.md", "role": "frontmatter",
      "heading": "Document Profile", "order": 0 },

    { "file": "10_bank-reconciliation.md", "role": "procedure",
      "slug": "bank-reconciliation", "heading": "Bank Reconciliation",
      "group": 1, "order": 10 },

    { "file": "80_roles.md", "role": "derived", "derived_kind": "roles",
      "writer": "agent", "heading": "Roles & Responsibilities", "order": 80 },

    { "file": "90_appendix-b-gaps.md", "role": "derived", "derived_kind": "gap-log",
      "writer": "python", "heading": "Appendix B | Gap / Validation Log", "order": 90 }
  ]
}
```

Fields:
- `role` ∈ `frontmatter` | `procedure` | `derived`.
- `procedure` rows carry `slug` (identity) and `group` (int, default 1;
  the "1.x / 2.x" clustering, expressed as data, no header needed).
- `derived` rows carry `derived_kind` and `writer` ∈ `python` | `agent`.
- `order` sorts everything; display number for a procedure =
  `{group}.{1-based index of this proc within its group, in order}`.

---

## Ownership rule (no file has two writers)

| Fragment kind | Writer | Contents |
|---|---|---|
| frontmatter | human | Document Profile, How to Use, Control, Sources |
| procedure | human / drafter | the source of truth |
| derived, pure-mechanical (`gap-log`, `screenshot-index`) | **Python** | full file rebuilt every run |
| derived, mixed (`roles`, `systems`, `dependencies`, `risks`) | **agent** | agent writes the whole file, copying Python-extracted mechanical rows through verbatim and reasoning only on judgment cells |

Python and an agent never write the same file. For agent-owned derived files,
Python produces an **extract bundle** (in-memory / scratch JSON, never committed)
that the agent consumes.

---

## Extraction contract (what Python reads from procedures)

Deterministic, strict, and **fail-loud** — on a malformed match Python emits an
error and a nonzero exit, never a silently-dropped row.

Recognized in procedure fragments:
- **Inline callout IDs** — blockquote lines of the form
  `> **<LABEL> — <ID>:** <text>` where LABEL ∈ {CONTROL, VALIDATION REQUIRED,
  PAIN POINT, IMPROVEMENT OPPORTUNITY, SCREENSHOT PLACEHOLDER} and ID matches the
  prefix for that label (`CTRL-`, `GAP-`, `PP-`, `IO-`, `SC-`).
- **Body gap tags** — `[[GAP-NN — TEXT]]`. A bare `[[GAP — …]]` with no ID is an
  ERROR.
- **Table-defined IDs** — rows in `F. Key Controls` (CTRL-), etc.
- **Systems** — `B. Quick Reference` "Primary systems / tools" + step-level
  `**System:**` fields.
- **Roles** — `B. Quick Reference` Preparer / Reviewer.

Errors (nonzero exit): bare gap tag; ID referenced but never defined; ID whose
prefix doesn't match its callout label; duplicate ID with conflicting text.

---

## Build order

```
M1 (template) ─┬─▶ M2 (split/manifest) ─▶ M3 (mechanical aggregator) ─▶ M5 (synthesis agents)
               └─▶ M4 (docx builder)  ────────────────────────────────┘
M6 (scoping / taxonomy reassessment) — DEFERRED, do not build yet
```

- Useful, token-free system after **M3 + M4**.
- **M5** is the synthesis layer (pure upside).
- **M6** is stubbed so the design isn't lost; explicitly out of MVP scope.

## Definition of done (every ticket)

Code + prescribed tests written and passing; `manifest.json` still validates;
no scratch artifacts committed; a one-paragraph report of what was built, the
test output, and any contract deviation.
