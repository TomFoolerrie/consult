# M2 — Legacy import splitter + manifest + shared numbering helper

**Depends on:** M1. **Blocks:** M3, M4, M5 (via the shared `doc_model.py` helper).

## Goal

Provide (a) the shared `doc_model.py` helper the whole system depends on
(manifest load/validate, `display_numbers`, token resolution, structured
`assemble`), and (b) a **legacy import** splitter that converts a pre-existing
single-file `.md` into a folder. Retire user-facing assembly.

## Role after r3: import, not the primary entry

With M0 scaffolding the folder from sources, **split is no longer the normal
entry point** — the folder is born folder-native. Split survives only to
**import** a legacy single-file document (someone's existing SOP) into the folder
model **once**. After import (or scaffold), the **folder is authoritative**;
steady-state work is edit-in-place + `reconcile.py`. There is no "re-split the
folder" operation, so headings rename freely without churning slugs. On a
re-import, slugs carry forward by matching the prior `manifest.json`; a heading
with no prior match is reported for a human slug decision (never silently
re-slugged). This removes the slug-stability contradiction (review #3).

The **shared helper is the load-bearing deliverable of this ticket** — M0, M3,
M4, M5 all import it. The splitter itself is the smaller, now-optional part.

## Why the splitter is still trivial

Under M1's flat-H2 contract the rule collapses to: **start a new fragment at
every `##`** — no heuristics. Numbering lives in exactly one place (the helper)
or it drifts (review #4).

## Changes

New shared module `skills/consult-drafter/scripts/doc_model.py` (name TBD):
- `load_manifest(folder)`, `validate_manifest(m)` (v1 schema).
- `display_numbers(manifest) -> {slug: "g.s"}` — **the only** implementation of
  group.sequence numbering. Imported by reconcile (M2), aggregate (M3), and the
  docx builder (M4). No one else computes numbers.
- `resolve_tokens(text, numbers, mode) -> text` — replaces `[[slug]]` with the
  display number (or `number + title`); unknown slug → error.
- `assemble(folder) -> AssembledDoc` — returns **structured** data, not a bare
  string: `title`, `subtitle`, and an ordered list of
  `{heading, role, slug|None, number|None, body}`. (M4 needs role/number to know
  which H2s get numbered; a flat string cannot carry that — review #1.)

`skills/consult-drafter/scripts/split_doc.py`:
- New rule: fragment boundary = every `##` outside a fenced block (both ```` ``` ````
  and `~~~`). Everything before the first `##` is the title + subtitle → recorded
  in the manifest (`title`, `subtitle`), not duplicated into a fragment.
- Emit `manifest.json` per the v1 schema: `{schema, area, title, subtitle,
  components:[…]}` with per-component `file, role, heading, order`, plus `slug` +
  `group` for procedures and `derived_kind` + `writer` for derived.
- Role inference **at bootstrap only**: `derived` if the section carries the M1
  `<!-- derived: KIND; writer: W -->` marker; `static` for the pre-procedure
  human sections; otherwise `procedure` (slug = slugified heading, set once;
  group from `<!-- group: N -->` marker or 1).
- Filename = `{band}_{slug}.md` with coarse bands (static 00–09, procedures
  10–69, python-index 70–79, agent-derived 80–89, python-appendices 90–99).
  Bands are stable; inserting a procedure reuses band 10 with a new slug and
  renames nothing else.
- `slug` collision → deterministic `-2`, `-3`, … + warning.

`skills/consult-drafter/scripts/reconcile.py`:
- Validate `manifest.json` against v1; check `order` uniqueness; check `slug`
  uniqueness.
- Verify every `[[slug]]` token resolves via `display_numbers` (dangling token =
  ERROR).
- Verify every manifest `derived` file contains a matching `<!-- derived -->`
  marker (review #10).
- Keep ID-integrity checks. **Ordering:** reconcile is defined to run **after**
  aggregate (M3), so IDs that appear only in derived files exist by then
  (review #14). Drop the near-vacuous "display numbers unique per group" check —
  it's implied by unique `order` (review #19).

`skills/consult-drafter/scripts/assemble_doc.py`:
- **Remove the CLI entry point** (review #20). The `assemble` logic lives in
  `doc_model.py` as an importable function returning the structured `AssembledDoc`.
  No user-facing assembled-file step remains.

`skills/consult-drafter/SKILL.md`:
- Rewrite "Build Scripts, Don't Retype" / "Iterating on a large draft" to the
  folder-as-truth model: edit components in place, reconcile the folder; assembly
  happens only inside the docx build (M4). Split is a one-time bootstrap.

## Acceptance

- Splitting an M1 template produces one `00_`/`static` frontmatter set, one
  fragment per `##` section, and a schema-valid `manifest.json` carrying `title`
  + `subtitle`.
- `display_numbers` returns the expected `{group}.{seq}` for a multi-procedure,
  multi-group fixture; it is the only place numbering is computed.
- `resolve_tokens` turns `[[bank-reconciliation]]` into its number; an unknown
  slug errors.
- Renaming a procedure heading in-place and reconciling does **not** change its
  slug or filename.
- `reconcile.py` flags: a dangling `[[slug]]`, a derived file missing its marker,
  a duplicate `order`.
- `assemble_doc.py` has no CLI; `doc_model.assemble` returns structured sections
  with role + number populated.

## Out of scope

Generating derived content (M3/M5); numbers authored by a human.

## Adversarial review resolutions

- **#1:** `assemble` returns structured `AssembledDoc`, not a string.
- **#3:** split is a one-shot bootstrap; slug set once; rename-in-place is safe.
- **#4:** single `display_numbers` helper; all consumers import it.
- **#7:** coarse stable bands + manifest `order` authority; no insert/delete churn.
- **#10:** reconcile verifies derived marker presence.
- **#13:** backtick + tilde fences handled; ATX-only constraint documented.
- **#14:** reconcile runs after aggregate.
- **#19:** vacuous per-group uniqueness check dropped.
- **#20:** assemble CLI removed.
