# Golden: `p2p-v1` — the v1 render of the frozen p2p fixture (M36 proof obligation 2)

These three files are the **committed reference render**: the normalized
`word/` XML parts of the procure-to-pay fixture rendered through the **v1
render path**, normalized per **M36 Amendment A1** (normalized-XML semantic
identity, not raw byte identity).

They exist to be a tripwire. Today they pin v1's self-consistency (the render
is deterministic and nothing has drifted). During the M36 migration they are
what the definition-driven render must reproduce **exactly** — same text, same
element structure, same ordering, same numbering references, same style
references.

## Contents

| file | what it is | size (bytes) |
| --- | --- | --- |
| `document.xml` | canonicalized `word/document.xml` — the document itself | 3,013,350 |
| `styles.xml` | canonicalized `word/styles.xml` — every style reference resolves here | 435,410 |
| `numbering.xml` | canonicalized `word/numbering.xml` — list definitions the body's `w:numId` point at | 7,060 |
| `regenerate.py` | the generation script (below) | — |

Each file is valid XML in the canonical form produced by
[`tests/docx_compare.py`](../../../docx_compare.py): one element per line,
attributes sorted, `rsid` revision-save ids removed, structurally
insignificant whitespace dropped, all text and ordering preserved.
Normalization is idempotent, so the golden re-normalizes to itself. That
module's docstring is the authoritative list of normalization rules and the
justification for each.

Parts deliberately **not** compared: `docProps/core.xml` (created/modified
timestamps and the per-render `cw-map:<doc_id>` category), `word/settings.xml`
(the `w:rsids` save-id table), and the derived/boilerplate remainder
(`[Content_Types].xml`, `_rels/`, `theme/`, `fontTable.xml`). All of the A1
protected content lives in the three parts above.

## Generation command (exact)

Run from the repo root:

```
python3 tests/fixtures/golden/p2p-v1/regenerate.py
```

That script renders a **temporary copy** of
`tests/fixtures/p2p-complete/components/procure-to-pay/` (the frozen fixture is
never written) via `render.render_folder(area, out, mode="working",
emit_signal=False)` — the v1 path, working mode, no review signal — then writes
`docx_compare.write_golden(out, <this dir>)`.

## Source context of the committed generation

- repo: `/home/user/consult`, branch `v2`
- commit at generation: `7419772a0b79c90e5c99ebb6a2336c81cdb30e3a`
  ("M36 build plan: G0 golden harness -> G1 plan assembly -> G2 deterministic
  layer -> G3 retirement+audits")
- generated: 2026-08-15, work package **WP-G0**
- python 3.11.15, `python-docx` 1.2.0 (stdlib only for the comparison itself)
- fixture: unmodified `tests/fixtures/p2p-complete` (frozen; M36 forbids
  fixture edits)

## The rule for changing this golden

**This golden changes ONLY with an explicit M36-gate decision, recorded in the
ticket's landing note.** A render change that makes
`tests/test_render_golden_m36.py::test_v1_render_matches_committed_golden`
fail is, by default, **a defect in the change** — not a stale golden. Do not
regenerate to make a red test green.

Regeneration is admissible only when the gate has *decided* that the new output
is the correct one (a deliberate, documented output change agreed at the M36
gate). In that case: regenerate with the command above, and commit the new
golden together with the decision that authorized it and a diff summary of what
moved.

`regenerate.py` is committed to make an authorized regeneration exactly
reproducible — not to make it routine.
