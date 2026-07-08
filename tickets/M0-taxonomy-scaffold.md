# M0 — `consult-taxonomy`: scope + reference registry + scaffold

**Depends on:** M1 (A–H skeleton shape), M2·`doc_model.py` (manifest write/validate).
**Blocks:** fill agents, M3.

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
_sources/new/*  + reference taxonomy
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
- Read everything in `_sources/new/`; register each in `sources.yaml` (SRC- id +
  hash + state `new`). Map them onto the reference taxonomy; **propose a procedure
  set** — `{slug, title, group}` per L3 procedure. Slugs assigned here, once.
- Extract candidate **nouns** and stand up the registry:
  `systems.yaml` (slug, name, aliases, description, limitations),
  `roles.yaml` (slug, name, reports_to, responsibilities),
  `sources.yaml` (SRC- registry), optional `glossary.yaml`.
- **Credibility guardrail:** `description` / `limitations` are **sourced from the
  transcript (cite the source line) or left blank/`TBD` — never invented.** Same
  anti-anchoring rule as the original taxonomy-baselines guardrail.
- Write proposals to a **staging dir** `_reference/.proposed/` (proposed
  `systems.yaml`, `roles.yaml`, and a `procedures.yaml` list). Do **not** touch
  the real `_reference/` or scaffold anything yet.

**Human confirm gate** (explicit, concrete — not hand-wavy):
- The human edits the files in `_reference/.proposed/` directly (add/remove/merge
  procedures; fix a role mapping; add a system alias; blank a guessed limitation).
- Confirm = run `scaffold.py --confirm`: it **promotes** `.proposed/` → the real
  `_reference/`, then scaffolds the manifest + skeletons. Nothing reaches the live
  folder until this runs. This is the one high-blast-radius judgment in the
  system; it is never auto-applied.

**New scaffold script `scaffold.py`** (Python, imports `doc_model.py`):
- Input: the confirmed procedure set + area metadata (title/subtitle).
- Write `manifest.json` (v1, **sparse `order`** in gaps of 10) and one
  `10_<slug>.md` per procedure containing the **A–H skeleton only** (headings +
  Quick Reference bullet keys + empty callout slots), plus the `static`
  frontmatter files and the `<!-- derived -->` stubs for the derived sections
  (empty; M3 owns their content).
- Idempotent: re-running with the same confirmed set is a no-op; adding a
  procedure creates only its file + a manifest entry with an `order` *between*
  neighbours (sparse), touching no existing file.

**Fill agents** (parallel, one per procedure) — reuse/rename the existing
`consult-drafter` as the per-procedure filler:
- Input: the procedure's skeleton + `_sources/` (new + processed) + `_reference/`.
- Cite the `SRC-` id(s) it drew from in the procedure's Source Materials.
- Normalize messy mentions to canonical names **via the registry**, writing plain
  text (no tokens for nouns). In the `B. Quick Reference` "Primary systems /
  tools" slot, **copy the registry `name` verbatim** (the authoritative slot for
  the Systems join); list every system the procedure uses there. Use `[[slug]]`
  only for procedure→procedure refs.
- A system that surfaces in a transcript but isn't in the registry: write it
  plainly and it will be flagged by M3's WARNING for a human top-up — the fill
  agent does **not** silently invent a registry entry.
- Mint procedure-**local** IDs (`CTRL-001`, `PP-001`, …) — safe under parallel
  authoring because IDs are scoped per procedure (README "Callout ID scoping").
- Do not author derived sections.

## Acceptance

- On a seeded source set + reference taxonomy, `consult-taxonomy` writes proposals
  to `_reference/.proposed/` and scaffolds nothing.
- Editing a proposed file then `scaffold.py --confirm` promotes `.proposed/` →
  `_reference/` and scaffolds; the live folder is untouched before `--confirm`.
- A guessed system `limitations` value left by the agent is either transcript-cited
  or blank — never an invented claim.
- `scaffold.py` produces a schema-valid `manifest.json` and A–H skeletons whose
  split (M2 rules) yields exactly one fragment per section.
- Two fill agents run concurrently and both mint `CTRL-001` with no collision
  (distinct because procedure-scoped).
- A transcript mention with no registry match surfaces as a WARNING at aggregate
  (M3), not a silent miss.
- Re-scaffolding with one added procedure touches only the new file + manifest.

## Out of scope

- Moving consumed sources `_sources/new/` → `processed/` — done by the
  orchestrator (M7) after fill succeeds, not by M0's scripts.
- Automated **reassessment** when new sources arrive later (add/split/merge an
  existing set) — that's M6. M0 is the initial stand-up only.

## Adversarial review resolutions (r2→r3 design)

- Folds in the "folder-native, scaffold-then-fill" model and the reference
  registry (two-database thesis).
- ID collision under parallel fill resolved by procedure-scoped IDs.
- High-blast-radius scoping gated by an explicit human confirm step.
