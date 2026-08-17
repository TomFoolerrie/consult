# M44 build plan

Method as M40–M43: acceptance tests are already committed (skip-gated);
each WP owns its files exclusively, lands as one commit, suite green at
every commit, zero v1 tests edited. Friction reported verbatim → ticket
amendment.

## WP-G1 — the needs view (machinery)

**Owns:** `scripts/needs.py` (new), `scripts/aggregate.py` (import + one
`PY_BUILDERS` entry only).

- `needs(area, deliverable=None)` per spec Part B: objective-driven targets,
  three feeds (`binding-unserved` via `definitions.serviceability`;
  `coverage` via `plan_views._selected_statuses` + `plan_views.node_steps` +
  `coverage_map.coverage`, only for targets with a `coverage:` binding;
  `recorded-gap` via GAP-kind prefixes from the type declaration +
  `doc_model.callout_display_ids`, attributed to targets binding that entity
  type). Entry keys: deliverable/kind/need/where/grounds, all always present,
  grounds never empty.
- Stable order (deliverable, kind, document order); read-only; lazy imports
  inside functions (aggregate registers at import time — the plan_views cycle
  note applies verbatim).
- `main(argv)` CLI: render per deliverable; unconfigured objective prints the
  accessor's "no engagement objective" line, exit 0; unknown area/deliverable
  exit 2. Builder `engagement-needs` renders the same content in aggregate's
  derived-view idiom (italic lead-in, `—` for empty).
- Gate: `tests/test_needs_m44.py` sections 1–4 (`needs_module` gate).

## WP-G2 — the two-mint doctrine (prose)

**Owns:** `agents/consult-drafter.md`, `agents/consult-surveyor.md`,
`agents/consult-librarian.md`, `scripts/brief.py`.

- Drafter: rewrite the GAP bar per spec Part A — two mints (conflict,
  evidenced absence), the ask half deleted ("who can answer it, and what it
  blocks" — line and doctrine), generic-thinness rule restated, CTRL-bar
  interplay recast as an evidenced absence, worked example's GAP bodies
  reground (grounds instead of "confirm with the process owner").
- Surveyor: the ask agenda becomes a render — the surveyor runs
  `scripts/needs.py` and shapes client-facing asks from its entries.
- Librarian: one line admitting the ask-half trim as a proposable groom.
- Brief: `objective_block`'s per-deliverable lead-in points at the needs
  view (`scripts/needs.py`) as the deeper render; serviceability lines stay.
- Gate: `tests/test_needs_m44.py` section 5 (`needs_prose` gate on
  "evidenced absence" in the drafter).

## Order

G1 commits first (G2's brief pointer names a module that then exists), but
the packages build in parallel — no shared files.
