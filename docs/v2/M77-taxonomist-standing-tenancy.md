# M77 — Standing tenancy: the taxonomist's judgment survives between dispatches

**Status: BUILT** (`2.5.0`, gate 41/41 — see Amendment A1).
Origin: the agent-ownership design conversation (2026-08-23) after the
second Nordhaven run. The governing observation: across both live
runs, the agents' error count is approximately zero and every defect
lived in the harness — yet the system re-briefs its most-redispatched
judgment agent from scratch every time, discarding exactly the
reasoning it will need next. The direction this ticket sets, recorded
as doctrine for future tickets too: **grow the tenancy, not the
harness** — agents invoke the verbs themselves, briefs over guards,
judgment persists in files the agents own.

## Why

1. **The taxonomist is stateless by accident, not design.** Each
   dispatch reconstructs its whole picture from sources + nodes +
   brief, does its work, and everything that did not land in a staged
   file evaporates: the `unresolved` list, `overlap_flags`, why three
   request paths merged into one node, which sufficiency calls were
   made reluctantly. Run 2's return carried all of these; none
   persisted (M76 catches the flag-shaped subset; the reasoning
   record has no home at all). The next incremental dispatch pays
   ~100k tokens to re-derive judgment already paid for — and may
   re-derive it DIFFERENTLY, because a fresh judge has no case law.

2. **The domain is already almost its house.** Post-M66 the live
   `_taxonomy/` is guarded (`.taxonomy.json` hashes, check 15.5);
   post-M75 its asks persist; post-M76 its flags persist; post-M74
   its confidence calls persist. What is missing is the connective
   tissue: the WORKING RECORD — deferred decisions, standing
   rationale, doubts — and a brief that feeds the taxonomist its own
   precedent back.

## The shape

### Part A — the tenure file

One taxonomist-owned working record per area — likeliest
`<area>/_taxonomy/.tenure.yaml` (inside the house it already owns,
dot-named like the guard file; builder confirms placement — the
set review verified the obvious objection away: `taxonomy_hashes`
globs `_taxonomy/*.md` only (`scaffold.py:535–541`), so a
`.tenure.yaml` there does NOT trip the M66 node guard, reconcile
check 15.5), written only through a deterministic verb — **hosted in
`scripts/flags.py`** (ruled per the set review: two near-identical
one-writer library+CLI modules is exactly the harness sprawl this
ticket's doctrine warns against; `flags.py` grows a `tenure`
subcommand, NOT a new module, NOT `notes_util`). Entries are typed:

- `ruling` — a structural decision and its one-line rationale
  ("merged the three request paths: same trigger/system/output,
  diamond not arrow");
- `deferred` — a decision explicitly not taken, with what would
  settle it ("supplier-onboarding split: wait for org answer to
  ask F");
- `doubt` — a call made reluctantly, worth revisiting on new
  evidence ("catalog-maintenance L2 placement is weak").

Each entry: state (`standing | superseded | resolved`), and a
superseding/resolving reference on close — the M76 flag discipline;
nothing is deleted, precedent accumulates append-only. The
taxonomist FILES ITS OWN entries (the M76 Part B tenancy ruling
applies verbatim — it has the tools and already writes through
verbs).

### Part B — the brief feeds the precedent back

The taxonomist brief (M52, `brief.py … taxonomist path`) gains a
tenure section: standing rulings, open deferrals, live doubts —
alongside the open flags (M76) and the ask register state (M75) it
already gains. The dispatch prompt's framing changes one sentence:
an incremental pass STARTS FROM its own precedent ("here is what you
previously decided, deferred, and doubted") instead of re-surveying;
it may supersede any ruling, but knowingly, by filing the
superseding entry. Contract text in `consult-taxonomist.md`
matching.

### Part C — the boundary (so this composes instead of sprawling)

- The tenure file is REASONING, not state: no consumer but the
  taxonomist's own brief reads it for decisions. The advisor never
  reads it; no guard keys off it; render never sees it. (Contrast:
  flags are cross-agent signal, asks are client-facing, confidence
  is advisor signal. A tenure entry that another agent needs is,
  by definition, a flag — file it as one.)
- Store-budget honesty: this IS a new persistent file, landing beside
  M75's register and M76's queue. The set ruling stands — after
  M75/M76/M77, no new persistent stores without retiring one — and
  this file is inside the taxonomist's existing house, one writer,
  one reader, the narrowest possible tenancy.
- v1 areas: file absent → brief byte-identical; nothing creates it
  outside a taxonomist dispatch on a v2 area.

### Part D — set close-out (M77 builds LAST)

Per the set build order (recorded in M76), M77 carries the release
close-out for M71–M77: README rows, CHANGELOG section, version
**2.5.0** (three new persistent stores, a new binding verb, a new
reconcile check, two agent-tenancy contract changes — minor-version
weight, same bar as 2.4.0's six), plugin.json bump. The CHANGELOG
entry records the two set doctrines where releases record law:
"grow the tenancy, not the harness" and "no new persistent stores
without retiring one."

## The gate

- Verb round-trip: entries filed, typed, append-only; supersede links
  resolve; malformed type/state refused loudly.
- Brief fixture: an area with tenure entries → the taxonomist brief
  carries the section (standing/deferred/doubt, superseded omitted);
  file absent → brief byte-identical to today's.
- Boundary pinned: the advisor's output over an area with a tenure
  file is byte-identical to the same area without it (no guard reads
  it); grep-shaped test that no module outside the brief/verb reads
  the file.
- Contract text: the taxonomist's filing duty and start-from-precedent
  framing present.
- Full suite + compat gate untouched.

## Amendment A1 — build rulings (2026-08-23)

* Verb landed as hyphen-prefixed flat siblings in `flags.py`
  (`tenure-add/-supersede/-resolve/-list`) — argparse subparsers are
  flat; the prefix keeps the two vocabularies unambiguous and the
  flag verbs byte-unchanged. Ids are `TEN-nnn` (area-scoped, max+1,
  never reused).
* File shape `{tenure: [{id,type,state,text,history[,reference]}]}`;
  history appends on close; re-close refused naming the current
  state; malformed record is loud-never-fatal in the brief.
* Brief section lands in `taxonomist_picture` beside M76's flags
  section — both taxonomist entrypoints print it; heading "YOUR
  STANDING TENURE", standing entries only.
* Boundary pinned three ways: advisor output byte-identical with and
  without the file (path-scrubbed comparison); grep over scripts/
  that only brief.py/flags.py name the file; `scripts/tenure.py`
  asserted absent.
* Non-collision claim verified true: `taxonomy_hashes` and reconcile
  check 15.5 are silent over the tenure file.
* Suite 1779 -> 1820, zero skips/xfails. Set close-out (Part D) done
  by the orchestrator in the release commit.
