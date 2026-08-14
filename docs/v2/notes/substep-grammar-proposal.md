# Sub-step grammar inside `transformation` — proposal (WP3, propose-only)

Status: proposal for the orchestrator. Grounded in `tests/fixtures/ipo-fragment.md`,
which already exhibits the grammar; nothing here changes what that fragment parses to.

## What the fragment actually does

The `### Transformation` body has two layers:

1. **The step line** — leading prose ("The AP Manager performs the three-way
   match … releases or holds each invoice."): who decides what, in which
   system, at step altitude.
2. **Sub-steps** — a Markdown ordered list (`1.` `2.` `3.`) following the
   prose: the ordered "how" (screens, filters, actions), same owner and same
   system throughout, per the step-granularity rule.

## Identification (mechanical)

- Within the `transformation` part body only, a **sub-step block** is a
  maximal run of top-level ordered-list items (`^\d+\.\s`), CommonMark
  numbering (renumber on render; source numbers are not identity).
- Everything in the body **before** the first ordered-list item is the
  **step line** (required); everything in the block is the sub-step list
  (optional). Multiple ordered lists in one body: reject at reconcile
  (one block per step keeps identity trivial) rather than concatenate.
- Sub-step identity: positional (`<step-slug>/t1`, `/t2`, …). No stable
  per-sub-step slugs in M33 — they are below the accountability boundary,
  so nothing off-step may reference them. Continuation lines/indented
  content under an item belong to that item (standard list nesting);
  SCREENSHOT PLACEHOLDER callouts nested under an item attach to it.

## Altitude request (deliverable side)

A deliverable's requirements dict says what depth it consumes, e.g.:

```yaml
parts:
  - transformation            # step line only (default) — controls matrix
  - transformation: substeps  # unfold the ordered list — desktop procedure
```

`can_serve` treats `substeps` as a *capability of the type* (transformation
is declared prose-with-substeps), never as a data requirement: **absence of
sub-steps in an entity is never a gap** (A2). A step-line-only consumer
must render identically whether or not sub-steps exist.

## What reconcile should check

- Step line present and non-empty before any ordered list.
- At most one ordered-list block; no ordered list outside it.
- Granularity smell (warn, not fail): a sub-step naming a different system
  or owner than the step's `consult-meta` bindings suggests it should be
  promoted to its own step.
- `[[slug]]` tokens inside sub-steps resolve like anywhere else; callouts
  other than SCREENSHOT PLACEHOLDER found inside the sub-step block warn —
  their homes are part-level (controls/issues), not sub-step-level.
