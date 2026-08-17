# M50 — The gap discriminator: the callout declaration says what kind of gap it is

**Status: SPECCED** (backlog line, unscheduled — build on the human's go).
Origin: the charter follow-up "a semantic kind marker on callout
declarations (M43's `fields:` key is the surface it would use)", plus
M44 A2 item 5 (the recorded-gap mint discriminator stayed on the Wants
list) and M46 A1 item 1 (the agenda's one-feed-one-section rule is
explicitly waiting on it: "Revisit when the discriminator lands").

## Why

The two-mint doctrine (M44) gives every v2 GAP a `Nature:` field —
`conflict | evidenced-absence` — so the discrimination EXISTS at the
fragment level. But nothing structural consumes it:

- `needs.py`'s `recorded-gap` feed reports one undifferentiated kind; the
  reader re-reads the fragment to learn whether a need is "two sources
  disagree" or "the sources confirm it's missing" — two very different
  interview questions.
- `agenda.py` wanted separate "conflicts to resolve" and "absences to
  confirm" sections and could not have them without minting new gap
  judgment, so it ships one merged confirm section (M46 A1.1 — an
  invented rule documented in the module).
- The GAP callout **declaration** in `kernel/types/process-step.yaml`
  says nothing about the enum; the vocabulary lives only in agent prose
  (`agents/consult-drafter.md`'s GAP bar). The M36 shape-audit rule —
  vocabulary comes from the declarations — is bent at exactly this field.

## The shape

### Part A — the declaration carries the enum

`kernel/types/process-step.yaml`'s GAP callout entry grows a declared
enum for the `Nature` field (surface: the M43 `fields:` key, which
already declares `[Grounds]`): `Nature: [conflict, evidenced-absence]`.
Declaration syntax to be settled at build (a `field_enums:` sibling or an
inline map) — whichever reads as data, not schema code. The v1 `activity`
declaration is NOT touched (its `Nature: unknown|conflict|
unsupported-assumption` grammar is v1 law behind the compatibility gate).
Optional metadata, never a parse gate — CONTROL's posture holds: a GAP
without `Nature:` still parses; consumers treat it as undiscriminated.

### Part B — `needs.py` reads it

A `recorded-gap` entry whose fragment carries a declared `Nature:` value
adds it to the entry (a sixth key, `nature`, present only when the
fragment states one — absent is absent, never guessed). The enum
vocabulary is read from the type declaration (Part A), never typed in
needs.py. Determinism, order, and the five existing keys unchanged; the
whole-engagement fingerprint test is re-pinned (a licensed edit — the
fingerprint is the gate's own hash, not v1 law).

### Part C — the agenda splits its confirm section

`agenda.py`'s `recorded-gap` mapping splits mechanically on `nature`:
`conflict` → a "resolve" section (both readings, both citations — ask the
interviewee which is true), `evidenced-absence` → a "confirm" section
(the record says it's missing — ask whether that's right),
undiscriminated → the existing merged section (v1-grammar and legacy
fragments keep rendering). Still zero new judgment: the split is a field
read, exactly what M46 A1.1 said it was waiting for.

### Part D — the fixture gap (M46 A1.5)

The IPO fixture gains one registered-but-unconsumed source, so the
agenda's owed-a-read section renders a real row and the ledger-join
suppression is finally exercised positively (today every source is fully
consumed and the section renders `—` for every role). Additive fixture
change; every existing count-pinning test that would see the new SRC id
is a licensed re-pin, enumerated in the build plan before any edit.

## Test impact

New gate: `tests/test_discriminator_m50.py` (committed with this spec,
skip-gated on the enum appearing in the process-step declaration).
Licensed edits, enumerated: the M44 fingerprint re-pin (Part B), the M46
agenda section anchors (Part C), any IPO-fixture count pins the new
source disturbs (Part D — the build plan lists them by name first).
**Zero v1 tests change**; the v1 activity declaration and grammar are out
of scope by contract.

## Acceptance gate

`tests/test_discriminator_m50.py`: the enum is declared, not typed in any
consumer (mechanical grep of needs.py/agenda.py for the literals);
`needs()` carries `nature` for discriminated fragments and omits it
otherwise; the agenda renders resolve/confirm/merged correctly over
fixtures of all three kinds; a GAP with an undeclared `Nature:` value
still parses (metadata, not a gate); the unconsumed source renders in
owed-a-read and vanishes once a consumption record lands.
