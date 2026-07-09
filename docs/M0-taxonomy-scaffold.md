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
prescribed L1 + _sources/new/*  + reference taxonomy
        │
        ▼  (agent: consult-taxonomy)
  proposes: procedure set (slug, title, l2, confidence)   ──┐
            + new-L2-bucket requests (needs-approval)        │
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
- Operates in **one prescribed L1** (the orchestrator passes `l1`). Reads the
  reference taxonomy to get that L1's **L2 sub-process buckets** (the known
  backbone) and **best-guesses the L3 activities** from the sources, filing each
  under an L2 bucket. One L3 = one procedure.
- Read everything in `_sources/new/`; register each in `sources.yaml` (SRC- id +
  `touches` tags). **`hash` and `state` are stamped by the Python scaffold step,
  not the agent** (hashing is deterministic byte-work). **Propose a procedure
  set** — `{slug, title, l2, confidence, sources}` per L3. Slugs assigned here,
  once.
- **New L2 buckets need approval.** If sources describe work fitting no existing
  L2 bucket, propose it in `new_buckets.yaml` flagged `needs-approval` and surface
  it in the return — never silently invent a bucket. The human approves/rejects at
  the confirm gate (a subagent can't round-trip mid-run; the gate is the
  permission point). Activities belonging to a **different L1** are reported, not
  scoped.
- See `.claude/agents/consult-taxonomy.md` for the full proposal shapes.
- **Tag sources → procedures.** For each source, record which procedure slugs it
  informs (in `sources.yaml`, e.g. `touches: [bank-reconciliation, close]`). This
  is what lets the orchestrator hand each parallel `consult-drafter` only its
  relevant sources instead of every drafter re-reading every transcript. A source
  may touch many procedures; a procedure may draw on many sources.
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
- **On the incremental path, promote is a MERGE, not a replace** (r3 review #12):
  a delta in `.proposed/` is merged into the existing `_reference/` (new entries
  added, existing ones untouched unless the delta changes them; approved
  `new_buckets` appended to the manifest's `l2_order`). It must not wipe registry
  entries the delta didn't re-emit.

**New scaffold script `scaffold.py`** (Python, imports `doc_model.py`):
- Input: the confirmed procedure set + area metadata (title/subtitle).
- Write `manifest.json` (v1, **sparse `order`** in gaps of 10). Include area-level
  `l1` (the L1 **slug**) and **`l2_order`** — the area's L2 bucket slugs in
  reference-taxonomy order, with any **approved `new_buckets`** appended (this is
  the ordering authority `display_numbers` reads; the immutable taxonomy is never
  mutated).
- Write one `10_<slug>.md` per procedure containing the **A–H skeleton only**
  (headings + Quick Reference bullet keys + empty callout slots), **stamped with an
  `unfilled` sentinel** (`<!-- unfilled -->`, or `status: unfilled` in its
  `consult-meta`) that the drafter removes on first write — this is the advisor's
  `fill` predicate. Plus the `static` frontmatter files and the `<!-- derived -->`
  stubs for the derived sections (empty; M3 owns their content).
- Stamp `sources.yaml` `hash` + `state` (deterministic byte-work belongs here, not
  in the agent).
- Idempotent: re-running with the same confirmed set is a no-op; adding a
  procedure creates only its file + a manifest entry with an `order` *between*
  neighbours (sparse), touching no existing file.

**Concrete build (what this ticket delivers):**
- **Invocation** (the confirm gate; run by the human / orchestrator):
  ```text
  python3 scripts/scaffold.py --confirm --area components/<area> \
      [--l1 <slug>] [--taxonomy <path>] [--title "..."] [--subtitle "..."]
  ```
  Without `--confirm` the script refuses and points back to `.proposed/` — the
  gate is never auto-applied. `--l1` may be omitted if it can be read from an
  existing `manifest.json` (incremental) or `.proposed/area.yaml`.
- **Promotion is a MERGE keyed by slug/id.** Only the registry files
  (`systems.yaml`, `roles.yaml`, `sources.yaml`, optional `glossary.yaml`) are
  promoted; `procedures.yaml` and `new_buckets.yaml` are *consumed* to build the
  manifest and are never copied live. Re-emitted entries win; entries the delta
  didn't touch survive.
- **`l2_order`** = existing order (preserved verbatim, so ordinals never drift) +
  taxonomy-order buckets actually used + approved new buckets (any `l2` a
  procedure uses that isn't in the taxonomy) appended in first-seen order.
- **`order`** = static `00`→0, `04`→5; procedures sparse from 10 in gaps of 10,
  existing procedures keeping their value and new ones inserted between
  neighbours; derived files at their filename prefix (70, 80, 81, 82, 84, 88, 90,
  91). A full-gap collision triggers a manifest-only renormalize (never renames a
  file). The written manifest is validated via `doc_model.validate_manifest`.
- **File inventory scaffolded:** static `00_document-profile.md`,
  `04_process-overview.md`; one `10_<slug>.md` A–H skeleton per procedure (stamped
  from M1's `procedure_skeleton.md` if present — taken from its first `##` onward
  with the title substituted — else a built-in A–H shell, always carrying the
  `<!-- unfilled -->` sentinel and an empty `consult-meta` block); and derived
  stubs `70_procedure-index`, `80_role-dictionary`, `81_systems`,
  `82_dependencies`, `84_raci`, `88_appendix-a`, `90_appendix-b-gaps`,
  `91_appendix-c-screens`, each empty but carrying its
  `<!-- derived: KIND; writer: W -->` marker.
- **Dependencies observed:** imports `scripts/doc_model.py` (M2) to validate;
  reads `skills/consult-drafter/reference/procedure_skeleton.md` (M1) if present.
  Neither is created or edited here.

**Fill agents** (parallel, one per procedure) — reuse/rename the existing
`consult-drafter` as the per-procedure filler:
- Input: the procedure's skeleton + `_sources/` (new + processed) + `_reference/`.
- Cite the `SRC-` id(s) it drew from in the procedure's Source Materials.
- Normalize messy mentions to canonical names **via the registry**, writing plain
  text in the prose (no tokens for nouns). Use `[[slug]]` only for
  procedure→procedure refs.
- **Populate the `consult-meta` end-matter block** with the registry **slugs** for
  every system and role the procedure uses — this is the machine binding M3 reads
  (no prose scraping). The prose names are for the reader; the slug list is
  authoritative.
- A system that surfaces in a transcript but isn't in the registry: put its slug
  in `consult-meta` anyway (best guess) and mention it plainly; M3 flags the
  unknown slug as a WARNING for a human top-up — the fill agent does **not**
  silently invent a registry entry.
- Mint procedure-**local** IDs (`CTRL-001`, `PP-001`, …) — safe under parallel
  authoring because IDs are scoped per procedure (README "Callout ID scoping").
- Do not author derived sections.

**The drafter is the procedure's durable owner (first-draft *and* update).** When
a new source is tagged to a procedure (or a reviewer edit lands), the orchestrator
re-dispatches `consult-drafter` in `update` mode on that one procedure. In update
mode it works newly-known facts into the body and **removes the GAPs they close**
(never leaving "resolved" artifacts), never renumbering existing IDs — producing a
clean finished document each pass. See `.claude/agents/consult-drafter.md`.

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
