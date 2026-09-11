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
  the offender, and the CLI's refusals are checked on STDERR: each line
  starts `refused:` and carries no stack frame;
- state is recomputed, never cached — a direct edit changes the next
  snapshot.

What the conformance test pins (tests/conformance.test.ts, A27): a
well-behaved skill — a scripted stub standing in for a dispatch — writes ONE
carded work product under `_synthesis/<skill>/run-1/`, publishes it through
`ledger.publishSynthesis` with every input declared by hash, and writes its
return file OUTSIDE the stores; that run yields no findings. Each way of
becoming a second brain is caught and NAMED by path: writing `STATE.md`,
editing a registered source's bytes (the path AND the source id whose hash no
longer verifies), writing under another skill's synthesis directory, an
artifact with no card, touching `_registers/asks.yaml` (and the capture
fragment written without a `writes: capture-fragment` grant), a return
carrying `[HUMAN]`, and a return that is missing, lacks `skill:`, or was
written inside a store. The fixture root is the harness's, not the suite's —
`harness/fixtures/conformance/engagement.ts` — so a skill author proves a
skill against exactly the ground the suite uses.

Store hygiene: a test never writes a scratch file into a store it is not
testing. A scout report a test needs is written to a temp dir OUTSIDE the
engagement root (see `scanned()` in tests/index.test.ts) — writing one
into `_synthesis/` pollutes the store under test and makes the index,
cards and check assertions read the fixture's own litter.

Run: `npm test` (Node ≥ 22.6 — type stripping). Typecheck: `npm run typecheck`.
