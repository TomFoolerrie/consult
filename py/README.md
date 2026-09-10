# py — the one Python seam

The language ruling (2026-08-26): the engine is TypeScript; Python remains
exactly here — `render_worker.py`, a bounded subprocess that owns Word XML
and nothing else. Built under A23. Dependency: python-docx only; stdlib
otherwise. Nothing else in the system touches Python.

## The contract

`src/render.ts` assembles the job (pure `assembleJob`) and spawns
`python3 py/render_worker.py` with it on stdin; the worker writes the file
and answers on stdout. All content decisions — what the sections say, in
what order, the title, whether it is a draft, what was refused — are made
in TypeScript before the job is emitted. The worker formats; it never
thinks, never reads the engagement folder, never touches the network.

Job v1 (stdin):

```json
{ "version": 1, "title": "Information Request", "draft": false,
  "skin": { "format": "docx", "requires": ["title-page"] },
  "sections": [ { "id": "intro", "title": "Purpose", "body": "…" } ],
  "out": "/abs/path/engagement/_synthesis/information-request.docx" }
```

Result (stdout, exit 0): `{ "path": "...", "sections": 3, "warnings": [] }`.

Exit 2 with `{ "error": "..." }` on stdout for a job the worker declines
(any version other than 1, a non-docx skin, no `out`). Exit 1 with one
message on stderr for any other failure. render.ts turns each into a
named refusal at the render verb: `python3 not available`, `render_worker
missing at <path>`, `render_worker failed — <stderr first line>`.

## What the worker draws

- `skin.requires` containing `title-page`: the title as a Title paragraph,
  the line "DRAFT — not for distribution" when `draft` is true, a page break.
- One Heading 1 per section, `section.title`.
- The body's light markup, exactly what the view builders emit:
  `- item` → List Bullet · `### text` → Heading 2 · blank line → paragraph
  break · anything else → a Normal paragraph (consecutive lines join).
- `draft: true` also puts "DRAFT" in the document's page header.
- A skin capability it does not understand, or an empty section body, is
  a WARNING in the result, never a refusal — the caller decides.

Output priority is shifting away from docx toward YAML/markdown anyway; if
a future ruling adds an html or md skin, those renderers are TypeScript
and this directory does not grow.
