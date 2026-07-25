# M21 — Render signal correctness (final mode is an export, not a state)

> **Status: DESIGNED.** Smallest ticket in the set; one-line class of fix.
> Evidence: `docs/audit-decide-exhaustiveness.md` (F10).

## Goal

Stop the client-facing render from resetting the engagement's review state.

## Why

Measured: render `--mode working`, then `orchestrate.py accept` (sign-off
recorded), then render `--mode final` for the client. The final render writes the
**same** `.render.json`:

```
after working: {awaiting_review: true,  docx: working.docx, basis: 36df3c…}
after accept:  awaiting_review cleared → advisor moves on
after final:   {awaiting_review: true,  docx: final.docx,   basis: 36df3c…}
```

So producing the deliverable:

- re-opens the `review` gate on a document nobody needs to review internally,
- silently discards an `accept` that already happened, and
- repoints the recorded artifact at the client export.

The signal carries no `mode`, so afterwards working and final are
indistinguishable — the advisor cannot tell which document it is talking about.

## Design

`--mode final` should behave like `--slugs`: **never write `.render.json`.**

The precedent is already in the renderer. Subset renders skip the signal because a
kit document is an export, not a pipeline state, and `render.py`'s own docstring
says so. Final mode is the same category — a terminal artifact produced *from* an
accepted state, not a transition *into* a new one. Its own docstring already notes
final mode "has no provenance; there is no review round against a final
deliverable," which is precisely the argument for it not touching the review
signal.

This also removes the need for a `mode` field: if only working mode writes the
signal, the signal is unambiguously about the working document.

Path recording for the final artifact, if wanted, belongs somewhere that is not
the advisor's review signal — the checkpoint commit already dates and captures it.

## Acceptance

- `--mode final` leaves `.render.json` byte-identical.
- Working render → `accept` → final render → the advisor still reports `done`, not
  `review`.
- Final render on an area that was never rendered in working mode does not create
  the signal.
- `--slugs` behaviour is unchanged.
- Working-mode render still sets `awaiting_review: true` with its basis.

## Out of scope

- Adding a `mode` field to `.render.json` (unnecessary once only one mode writes
  it).
- Tracking a history of produced deliverables.
- Whether final mode should refuse on missing screenshots — it reports counts and
  never refuses, which is settled.
