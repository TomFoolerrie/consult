# M34 build plan — work packages for centralized sources

> Orchestration foundation for building
> [`M34-centralized-sources.md`](M34-centralized-sources.md). The
> acceptance gate is ALREADY WRITTEN (`tests/test_ledger_m34.py`) — it
> skips until `scripts/ledger.py` exists, then becomes the gate. Build to
> the tests; never edit them. Same ground rules as
> [`M33-build-plan.md`](M33-build-plan.md): branch `v2`, full suite green
> before finishing, one writer per file, frozen fixtures read-only,
> doc_model.py style, escalate friction verbatim.

## The API contract (what the tests pin)

All in a NEW module `scripts/ledger.py` (engagement-root scope; v1's
per-area `sources.py` is untouched this ticket — reuse its helpers by
import where they fit, e.g. hashing and the notes-bus join):

```
ledger.LedgerError
ledger.register(root, filename, touches: {area: [slugs]}) -> "SRC-nnn"
    # mints engagement-globally in order; idempotent by content hash
    # (re-register merges touches, returns the existing id, never dupes);
    # refuses (LedgerError) a touches slug absent from that area's manifest
ledger.park(root, filename, reason) -> None      # new/ -> parked/, reason kept
ledger.status(root) -> {"unregistered": [names], "parked": [(name, reason)]}
ledger.entries(root) -> [entry dicts: id, file, hash, touches, consumed, ...]
ledger.outstanding(root, area) -> {src_id: [uncredited slugs]}
ledger.credit(root, area, filled=(), updated=()) -> files_moved: int
    # filled: unconditional credit (v1 rule); updated: requires an archived
    # kind: source note naming the id (v1 note_src_ids semantics, at
    # components/<area>/_review/processed/<slug>.notes.yaml); non-source
    # notes credit nothing; consumption accumulates, never resets;
    # a file moves new/ -> processed/ ONLY when the ENTIRE touches map is
    # covered by consumed (all areas)
ledger.entries_for_area(area_path) -> [entries]      # dual-layout adapter:
    # a v1 per-area registry read through the unified API, ids presented
    # as "<area-name>/SRC-nnn"; READ-ONLY (adapter never writes)
ledger.outstanding_for_area(area_path) -> {prefixed_id: [slugs]}
ledger.centralize(root) -> remap: {"<area>/SRC-nnn": "SRC-mmm"}
    # folds v1 per-area registries into the root ledger: dedupe by hash,
    # remint ids, merge touches/consumed maps per area, place each file in
    # new/ or processed/ by the DERIVED state (file position is display;
    # the ledger is truth), and persist the remap table under _sources/
```

Layout owned by this module: `<root>/_sources/{sources.yaml,new/,processed/,parked/}`.
Doctrine to honor in code comments: **file position is display; the ledger
is truth** — every outstanding-ness answer comes from the ledger, never
from listing folders.

## Work packages (sequential — one file, one writer at a time)

### WP-A — ledger core
Owns `scripts/ledger.py` (create). register / park / status / entries,
minting, hash idempotence, manifest-validated touches (import the
manifest-slug read from `sources.py`/`doc_model` rather than reimplementing).
Target: `TestRegistration`.

### WP-B — consumption + the move rule (extends ledger.py after WP-A)
outstanding / credit with the v1 evidence rules (reuse the
`note_src_ids` join semantics — kind: source items in archived notes),
never-resets accumulation, the all-areas move rule.
Targets: `TestLedgerRoundTrip`, `TestCreditEvidence`.

### WP-C — adapter + centralize (extends ledger.py after WP-B)
entries_for_area / outstanding_for_area (read-only, prefixed ids) and
centralize (dedupe, remint, merge, remap table, derived file placement).
Targets: `TestAdapter`, `TestCentralize`.

## Explicitly OUT of scope this build

Consumer wiring — orchestrate/brief/scaffold/intake reading the central
ledger, retiring `intake/` and the route sidecar — is the second half of
the M34 ticket and lands as a separate build once the ledger module is
proven (it touches the v1 engine and needs its own careful package plan).
Nothing in WP-A..C may modify any existing script.

## Sequencing

WP-A → WP-B → WP-C, each ending with `python3 -m pytest -q` fully green
(827 passing pre-M34; ledger tests activate as the module grows — a
target class for a LATER package failing with AttributeError is expected
and reported, never patched around).
