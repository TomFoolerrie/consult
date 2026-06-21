# T35 — `validate` coherence check (structured ↔ narrative)

- **Slice:** 2 · **Depends:** T13 (node MDs) · **Touches:** `scripts/state_machine.py` (extend `validate`)
- **Refs:** spec §3 (Precedence & coherence); `consolidate_contract.md` §5; adversarial P2 #10.

## Goal
Make structured↔narrative drift **detectable**: extend `validate` so it checks the node MDs against state +
register. Catches dangling citations and stale lens prose the moment a human edits a narrative.

## Scope (build)
Add a **coherence** section to `state_machine.py validate --engagement E` (after the existing node-set + schema
checks; add a `--coherence-only` convenience and include it in the default run):
1. **Cited IDs exist** — for every node MD (`nodes/{l1}/{l2}.md`), find register-id citations
   (`(IMP|GAP|SC|UNM|THM|GAP-STRUCT|GAP-CONFLICT)-[\w-]+`) and assert each exists in `register.json`
   (active or archived). Report any dangling citation with its node + id.
2. **Frontmatter lenses match state** — the node MD's YAML frontmatter carries a `lenses:` block; assert each
   non-null frontmatter lens equals the state node's lens value. Report mismatches (these are stale narratives
   after a state change — exactly the "structured wins, MD not yet re-rendered" signal).
3. Summarize: N MDs checked, N dangling citations, N lens mismatches. Non-fatal by default (report + count);
   exit nonzero only with `--strict`.

## Out of scope
Auto-fixing drift (that's re-consolidation). Deep NLP of prose lens claims (frontmatter is the checkable anchor).

## Tests (scratch `__t35__`; do not commit)
1. A node MD citing a real register id + frontmatter lens matching state → coherence clean.
2. A node MD citing `IMP-9999` (not in register) → reported as dangling.
3. A node MD whose frontmatter `process: pain_high` while state has `pain_med` → reported as a lens mismatch.
4. `--strict` exits nonzero when issues exist; default exits 0 with the report. Compiles; state schema-valid.

## Done when
Coherence check in `validate`; tests pass; report output + deviations.
