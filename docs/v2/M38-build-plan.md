# M38 build plan — the process & controls matrix

> Foundation for [`M38-second-deliverable.md`](M38-second-deliverable.md).
> Gate: `tests/test_matrix_m38.py` (skips until the definition + IPO
> fixture exist). Ground rules as ever.
>
> **Orchestrator ruling on "zero engine edits":** the bar means no
> special cases in the loader, compiler, or renderer. A NEW view-builder
> module registered through the existing `aggregate.PY_BUILDERS` registry
> (one-line hook) is the sanctioned extension mechanism — named in the
> landing note, exactly like binding verbs and renderer capabilities.
> Anything beyond that (an if-statement keyed on the matrix anywhere in
> definitions/render_glue/render/aggregate) fails the ticket.

## Work packages

### WP-M1 — the IPO fixture engagement (frozen fixture #2)
Owns `tests/fixtures/ipo-engagement/` only. A central-mode engagement:
root ledger with 2-3 REGISTERED AND CONSUMED sources (consistent
consumed maps), one area `purchasing/` with a manifest, one taxonomy
node per L2-ish grouping under `_taxonomy/` (node slug == step slug
convention for L3s where sensible; at least one node grouping several
steps), and 4-6 hand-authored `process-step` fragments in the
`ipo-fragment.md` grammar (numbered transformation sub-steps, IPO edges
as [[slug]] references, consult-meta systems/roles that exist in
`_reference/systems.yaml`/`roles.yaml` — author those registries too).
THE AWKWARD CASES ARE MANDATORY (anti-convenience clause): a step with
no controls; a shared input (two steps consuming one artifact); an
unresolved two-source conflict recorded on a node (GAP naming both SRC
ids); a pain with no gap beside it; an orphan output (an output no step
consumes). Every SRC- citation must resolve to the ledger. Gate class:
TestIpoFixture (read it first — it pins the layout and cases).

### WP-M2 — the matrix definition + builder + capabilities
Owns `kernel/deliverables/process-controls-matrix.yaml`, a NEW
`scripts/matrix_views.py` (the python builder(s) for the matrix view:
rows = steps grouped by taxonomy node, columns = owner (roles channel),
system(s), inputs/outputs, CTRL count/ids, open PP/GAP counts), the
one-line PY_BUILDERS registry hook, binding-verb additions ONLY as the
matrix demands (join/group/count family, each with the consuming
binding named in a comment), `landscape-tables` + any other capability
the skin needs declared truthfully (render.py already supports
--landscape per M36 G0's capability list). The matrix renders through
the ordinary plan path (render_glue) — landscape via the skin.
Gate classes: TestMatrixDefinition, TestMatrixRender, TestCoexistence.
The shape audit will see your new module: allowlist entries with
reasons where literals are genuinely required, else derive from
declarations.

### WP-M3 — the review round-trip (proves inheritance for a table-first doc)
Owns a new test file only (tests/test_matrix_roundtrip_m38.py):
reviewer edit simulation on the rendered matrix (reuse the existing
review_extract/tracked-changes test machinery — find it in the v1
review suites) -> extract -> notes bus -> the OWNING step is the note
target (never the matrix) -> matrix view rebuilds -> re-render. If the
existing machinery cannot mark up a table-first docx without new engine
code, report the gap honestly instead of forcing it — a documented
partial (comment-extraction-only round trip) with the gap named beats a
fake pass.

## Sequencing
WP-M1 ∥ WP-M2 (M2 develops against the ipo-fragment grammar and the
gate; final verification needs M1's fixture — coordinate via the gate),
then WP-M3, then close-out (alpha.8).
