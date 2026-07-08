# M2 — Dead-simple splitter + manifest (folder-as-truth)

**Depends on:** M1. **Blocks:** M3, M4, M5.

## Goal

Replace the heuristic splitter with the one-rule splitter and make the exploded
folder + `manifest.json` the primary artifact. Retire user-facing assembly.

## Why

`split_doc.py` currently stacks three heuristics ("shallowest level after
title" + numbered-module regex + appendix regex) and breaks on any document
that deviates from the template's exact shape. Under M1's flat-H2 contract the
rule collapses to: **start a new fragment at every `##`.**

## Changes

`skills/consult-drafter/scripts/split_doc.py`:
- New rule: fragment boundary = every `##` outside a fenced block. Everything
  before the first `##` (the `#` title + any preamble) is frontmatter fragment
  `00_…`, and the title is recorded in the manifest, not duplicated into a
  fragment.
- Emit `manifest.json` per the v1 schema in `tickets/README.md`:
  `{schema, area, title, components:[…]}` with per-component
  `file, role, heading, order` and, for procedures, `slug` + `group`, and for
  derived, `derived_kind` + `writer`.
- Role inference on split: a section is `derived` if it carries the M1
  `<!-- derived: KIND; writer: W -->` marker; `frontmatter` for the pre-content
  sections; otherwise `procedure` (slug = slugified heading; group defaults to
  1 unless a `<!-- group: N -->` marker is present).
- `slug` collision handling: append `-2`, `-3`, … deterministically and warn.
- Idempotent re-split: re-splitting an already-split folder must not churn
  filenames for unchanged sections (stable slug → stable filename).

`skills/consult-drafter/scripts/reconcile.py`:
- Keep walking `manifest.json`. Add: validate manifest against the v1 schema;
  check `order` uniqueness; check `slug` uniqueness; compute + verify display
  numbers are unique per group; keep the existing ID-integrity checks.
- Continue to distinguish ORPHAN (warning) from ERROR (nonzero exit).

`skills/consult-drafter/scripts/assemble_doc.py`:
- **Demote from a user command.** Keep an internal `assemble(folder) -> str`
  function (manifest-ordered concatenation under the single `#` title, whitespace
  normalized) for M4 to import. Remove/deprecate the CLI entry point, or leave it
  but document that the assembled file is ephemeral, never an artifact.

`skills/consult-drafter/SKILL.md`:
- Rewrite "Build Scripts, Don't Retype" / "Iterating on a large draft" to the
  folder-as-truth model: you edit components in place and reconcile the folder;
  assembly happens only inside the docx build (M4), not as a step you run.

## Acceptance

- Splitting an M1 template produces: one `00_` frontmatter fragment, one fragment
  per `##` section, and a schema-valid `manifest.json`.
- Each procedure fragment's derived display number (`{group}.{seq}`) is unique
  and matches expectation.
- Re-running split on the output folder is a no-op for unchanged sections
  (no filename churn).
- `reconcile.py` on the split folder passes (ORPHAN warnings allowed for
  unpopulated template rows; zero ERRORS).
- A round-trip (split → internal assemble) reproduces the section set and order;
  content is byte-preserved modulo normalized inter-section whitespace.
- `assemble_doc.py` is no longer presented to users as a build step.

## Out of scope

Generating derived content (M3/M5); numbering *authored* by a human (numbers are
derived here).
