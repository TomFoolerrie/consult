# M61 — The xlsx round trip: what the client typed is what the drafter reads

**Status: BUILT** (`2.3.1-alpha.6`, gate 8/8 — see Amendment A1).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-13, F-14, F-25 — F-13 and F-14 reproduced through the
gap-kit path.

## Why

`scripts/xlsx_min.py` is the engine's own minimal writer/reader for the
gap kits — the workbook the CLIENT fills in and returns. Three holes in
the round trip:

1. **`write_xlsx` emits XML-forbidden control characters**
   (lines 90–93). Cell text gets only `saxutils.escape()` (`& < >`).
   C0 controls — a form-feed pasted from a client PDF where a page
   break was — are flat-out illegal in XML 1.0 (not even representable
   as entities), producing a workbook Excel reports as corrupt and that
   the engine's own `read_xlsx` cannot re-open (`ParseError`,
   reproduced for 0x00, 0x07, 0x0C, 0x1B, 0x1F). `build_kits` still
   prints success and exits 0.

2. **`read_xlsx` returns raw serials** (lines 166–175, consumed at
   `gaps_ingest.py:49, 65`). The reader resolves shared strings but
   takes raw `<v>` text for every non-string cell, with no number-format
   handling. Excel auto-coerces typed answers — dates to serials,
   percentages to fractions, TRUE to 1 — so a client answering "When is
   the cutoff?" with 12/31/2025 flows into the review note as
   "answered: 46022". The drafter cannot recover the intent.

3. **No limits on client-controlled input** (line 143 and the docx
   readers). `read_xlsx` feeds zip members straight into
   `ElementTree.fromstring` with no size cap — a decompression-bomb
   workbook exhausts the consultant's machine. Low severity (the
   counterparty is a client, not an anonymous attacker) but a one-line
   guard.

## The shape

### Part A — the writer refuses or repairs, never corrupts

Before emission, cell text is sanitized: XML-1.0-illegal characters are
replaced with a visible placeholder (`�` or a documented space)
— OR the write fails loud naming the sheet/row/col. Pick one policy and
write it in the module docstring; the review's read is replace-and-note
(the kit ships, the drafter sees a marker) since the characters are
never meaningful. Either way: `write_xlsx` output ALWAYS re-opens in
Excel and in `read_xlsx`.

### Part B — the reader interprets what Excel stored

`read_xlsx` learns the minimum typing the kits need: cells whose style
carries a date number format come back as ISO dates (serial → date is
pure arithmetic from the 1900 epoch, no dependency needed); `t="b"`
comes back TRUE/FALSE; plain numbers keep their text. Requires parsing
`styles.xml` for `numFmtId` per cell `s=` index — bounded scope: the
builtin date formats (14–22, 45–47) plus custom formats containing
`d`/`m`/`y` outside quotes. Everything else stays raw text, as today.

### Part C — belt-and-braces limits

A per-member decompressed-size cap (e.g. 50 MB) on every zip member
the engine reads from client-returned files (`xlsx_min.read_xlsx`, and
the same guard where review kits are opened). Over the cap → loud
refusal naming the file.

## The gate

- Round-trip property: `write_xlsx` with strings containing every C0
  control, `<`, `&`, unicode → `read_xlsx` re-opens it; the placeholder
  policy is asserted.
- The 46022 repro: a serial-formatted date cell reads back as
  `2025-12-31`; a `t="b"` cell reads TRUE; a plain number stays "5".
- `gaps_ingest` note text carries the interpreted answer.
- An over-cap zip member → refusal naming the file, no parse attempt.
- Existing kit/ingest tests pass untouched.

## Amendment A1 — build rulings (2026-08-20)

* **Sanitize-vs-refuse (Part A's "pick one"):** replace-and-note, per the
  review's read — illegal characters become U+FFFD, the kit ships, the
  drafter sees the marker. Policy stated in the module docstring.
* Part B scope as ticketed: builtin ids 14–22/45–47 plus custom formats with
  `d`/`m`/`y` (date) or `h`/`s` (time) outside quoted literals; the phantom
  1900-02-29 handled by the 1899-12-30 epoch with the <60 correction.
* Part C's cap is `xlsx_min.MEMBER_CAP` (50 MB); `review_extract` guards its
  docx members through the same constant.
