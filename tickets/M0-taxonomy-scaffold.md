# M0 — `consult-taxonomy`: scope + reference registry + scaffold

**Depends on:** M1 (needs the A–H skeleton shape). **Blocks:** fill agents, M3.

## Goal

Turn raw sources into a folder-native, scaffolded area: an agent determines the
procedure set against a reference taxonomy and stands up the `_reference/`
registry; a human confirms both; Python scaffolds `manifest.json` + one empty
A–H skeleton per confirmed procedure; parallel fill agents populate them.

## Why

This makes the system folder-native from birth (no "write a big doc then split"
bootstrap), enforces template adherence by construction (Python emits the exact
A–H skeleton), and grounds messy-transcript intake in a canonical noun registry.

## The flow

```
sources + reference taxonomy
        │
        ▼  (agent: consult-taxonomy)
  proposes: procedure set (slug, title, group)   ──┐
            + first-cut _reference/ (systems, roles, aliases, sources) ─┤
        │                                                               │
        ▼                                                    HUMAN CONFIRM GATE
  Python scaffold: manifest.json + A–H skeleton per confirmed procedure
        │
        ▼  (fill agents, parallel — one per procedure)
  each reads its sources + the registry → fills its skeleton, writing
  canonical noun names as PLAIN TEXT and procedure↔procedure refs as [[slug]]
```

## Changes

**New skill `skills/consult-taxonomy/SKILL.md`** (+ a `reference_taxonomy.yaml`
under its `reference/` as the default backbone; the user may supply their own):
- Read the sources; map them onto the reference taxonomy; **propose a procedure
  set** — `{slug, title, group}` per L3 procedure. Slugs assigned here, once.
- Extract candidate **nouns** and stand up `_reference/`:
  `systems.yaml` (slug, name, aliases, description, limitations),
  `roles.yaml` (slug, name, reports_to, responsibilities),
  `sources.yaml` (SRC- registry), optional `glossary.yaml`.
- Emit both proposals for the confirm gate; do **not** scaffold until confirmed.

**Human confirm gate** (explicit, cheap): the human reviews/edits the proposed
procedure list **and** the registry (add/remove/merge procedures; fix a role
mapping; add a system alias) before anything is scaffolded. This is the one
high-blast-radius judgment in the system; it is not auto-applied.

**New scaffold script `scaffold.py`** (Python, imports `doc_model.py`):
- Input: the confirmed procedure set + area metadata (title/subtitle).
- Write `manifest.json` (v1) and one `10_<slug>.md` per procedure containing the
  **A–H skeleton only** (headings + Quick Reference bullet keys + empty callout
  slots), plus the `static` frontmatter files and the `<!-- derived -->` stubs
  for the derived sections (empty; M3 owns their content).
- Idempotent: re-running with the same confirmed set is a no-op; adding a
  procedure creates only its file + manifest entry (existing files untouched).

**Fill agents** (parallel, one per procedure) — reuse/rename the existing
`consult-drafter` as the per-procedure filler:
- Input: the procedure's skeleton + the relevant sources + `_reference/`.
- Normalize messy mentions to canonical names **via the registry**, writing plain
  text (no tokens for nouns). Use `[[slug]]` only for procedure→procedure refs.
- Mint procedure-**local** IDs (`CTRL-001`, `PP-001`, …) — safe under parallel
  authoring because IDs are scoped per procedure (README "Callout ID scoping").
- Do not author derived sections.

## Acceptance

- On a seeded source set + reference taxonomy, `consult-taxonomy` emits a
  procedure-set proposal and a first-cut `_reference/` without scaffolding.
- Nothing is written to the folder until the confirm step returns an approved set.
- `scaffold.py` produces a schema-valid `manifest.json` and A–H skeletons whose
  split (M2 rules) yields exactly one fragment per section.
- Two fill agents run concurrently and both mint `CTRL-001` with no collision
  (distinct because procedure-scoped).
- A transcript mention with no registry match surfaces as a WARNING at aggregate
  (M3), not a silent miss.
- Re-scaffolding with one added procedure touches only the new file + manifest.

## Out of scope

Automated **reassessment** when new sources arrive later (add/split/merge an
existing set) — that's M6. M0 is the initial stand-up only.

## Adversarial review resolutions (r2→r3 design)

- Folds in the "folder-native, scaffold-then-fill" model and the reference
  registry (two-database thesis).
- ID collision under parallel fill resolved by procedure-scoped IDs.
- High-blast-radius scoping gated by an explicit human confirm step.
