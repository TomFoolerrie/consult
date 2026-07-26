# M20 — Canonical rename propagation

> **Status: DESIGNED.** Depends on nothing; overlaps M12 conceptually but cannot
> be delegated to it (see below).
> Evidence: `docs/audit-decide-exhaustiveness.md` (F9).

## Goal

When a canonical noun is renamed in `_reference/` — the client rebrands a system,
or you learn the real product name mid-engagement — bring the **prose** along.
Today the derived views update and every procedure keeps the old name, silently.

## Why

Measured: rename `name: NetSuite` → `Oracle NetSuite ERP`, keeping `NetSuite` in
`aliases` — the designed path. Result:

- `08_systems.md` regenerates to **Oracle NetSuite ERP** (bindings are by slug, so
  the view is correct);
- all fifteen procedures keep saying **NetSuite** in their steps;
- `aggregate` exits 0 with **no unmatched-mention warning**, because the old name
  is still a legitimate alias.

The deliverable ships with the Systems table and the steps disagreeing, and nothing
in the pipeline says so.

This is not a bug in the two-database model — it is that model working as
specified. Identity binds by slug; prose is plain text and is never scraped to
establish identity. The gap is the absence of a **workflow** for the one event that
makes prose and registry disagree by construction.

### Why M12 cannot absorb this

The consolidator looks like the natural owner and is the wrong one, for two
independent reasons:

1. Its `naming` rule is a **mechanical majority** over `consult-meta` bindings.
   After a rename the majority *is* the old name — fifteen procedures to zero — so
   a majority rule either does nothing or actively proposes keeping the stale form.
2. Its alias rule classifies a registry-known synonym as legitimate and explicitly
   proposes **no drafter dispatch** for it.

M12 is registry-blind by design: it asks "do these procedures agree with each
other?", never "do they agree with the registry?" Both questions are worth asking;
they are different questions.

## Design

### The trigger is a registry diff, not a prose scan

The rename is knowable exactly: `_reference/*.yaml` is versioned, so a canonical
`name` change on an existing `slug` is a diff, not an inference. That diff is the
whole signal — no prose scanning is needed to *detect* the event, only to locate
the mentions to fix.

### Detection: which procedures cite the superseded form

For a renamed slug, the mentions to update are the procedures **bound to that slug**
via `consult-meta` whose prose contains the superseded form. Both halves are already
available — bindings from the aggregate join, alias matching from the registry — so
this is a mechanical list, not a judgment.

### Remediation: notes, not rewriting

A rename produces one `_review/{slug}.notes.yaml` entry per affected procedure —
"canonical name for `systems/netsuite` changed to *Oracle NetSuite ERP*; this
procedure still uses *NetSuite*" — stamped `kind: rename` per M6's notes bus
contract (freely deletable, never counted toward source retirement), and guard 2
dispatches update drafters. Same
route M6 uses for new sources, and the same reason: a drafter owns its fragment's
prose, and a mechanical find-and-replace would edit sentences it cannot read.

The old form **stays in `aliases`** regardless. Aliases exist so intake can still
normalize messy input that uses the old name; removing it would break the next
transcript that says "NetSuite."

### The human decision this preserves

Not every rename should propagate. "AP Clerk" → "Accounts Payable Specialist" may
be a title change the client wants reflected everywhere, or may be a formalism the
procedures should not adopt. So the rename produces **notes the human can delete
before drafters run** — the same escape hatch M12 gives its findings.

## Acceptance

- Renaming a canonical `name` on an existing slug produces notes for exactly the
  procedures bound to that slug whose prose carries the superseded form.
- A procedure bound to the slug but not mentioning the old form in prose gets no
  note.
- Adding a brand-new registry entry produces no rename notes (that path is M6's
  unmatched-mention flow).
- The superseded form remains in `aliases`, and intake still normalizes it.
- Deleting a note before `apply_review` suppresses that procedure's update.
- After the drafters run, the Systems view and the procedure prose agree.

## Out of scope

- Renaming a **slug** (identity change, not a display change) — that is a manifest
  and binding migration, not this.
- Cross-area rename propagation (M13 supplies the shared registry layer first).
- Mechanical find-and-replace in fragment prose.
