# tests — the executable spec

Written before the build (the mock-out method's last step). Every file
is red until its module lands in Phase 1/2 — turning one file green IS
building that module. `tests/helpers.ts` pins the on-disk shapes: the
fragment format there is the three-primitive grammar made concrete, and
changing it is a design decision, not a refactor.

What the suite encodes, beyond per-verb behavior:
- consumption/settlement are DERIVED from capture citations (A18) —
  there is a test that settles an ask by *editing capture*, no verb;
- synthesis never upgrades standing (A12) — a statement citing an
  ungrounded synthesis source stays claimed;
- absent standings carry the question's ADDRESS, not phrased text (A18);
- both gates land in the session record (A18);
- refusals are NAMED — every throws-assertion checks the message names
  the offender;
- state is recomputed, never cached — a direct edit changes the next
  snapshot.

Run: `npm test` (Node ≥ 22.6 — type stripping). Typecheck: `npm run typecheck`.
