# M10 — Deterministic tracked-changes apply

> **Status: BUILT** (`scripts/review_apply.py`). Deltas from this design:
> callout boxes are 1×1 tables, so anchored cell paragraphs ARE appliable —
> the table fallback applies only to UNanchored table edits (derived/agent
> tables, which are never bookmarked); verification synthesizes the rendered
> text from the current fragment through an ALIGNED re-run of the render
> transforms (IDs, [[slug]] tokens, gap flags, marker strip), so the splice
> preserves formatting/tokens outside the edit region; only edited segments
> are re-emitted (no cosmetic reflow of untouched hard-wrapped lines);
> review_apply never archives — review_extract --comments-only runs after it
> and archives the doc.

## Goal

Apply reviewers' **tracked changes** back into the markdown fragments
mechanically — zero token spend — with a verified-or-fallback guarantee:
every deterministic application must prove itself, and anything that can't
degrades to the existing notes.yaml → drafter path. **Comments keep flowing
through drafters unchanged** (a comment is an instruction; applying it is
judgment).

## Why

Most SME edits are wording fixes, corrected thresholds, renamed reports —
mechanical text surgery that today costs a drafter dispatch each. The docx is
our own render, so we can carry provenance out and invert the transforms on the
way back. The risk to manage is silent corruption; the design below converts
every failure mode into "falls back to today's workflow" rather than "wrong
text in a fragment".

## Design

### Provenance (landed in M9)

Every rendered paragraph carries an opaque bookmark `cw_<n>`; the sidecar
`<docx>.map.json` maps `n → {file, slug, l2, subsection, para_index,
sha1(rendered_text)}`. Names stay opaque (Word caps bookmark names at 40
chars); the context lives in the sidecar — strictly more context than encoding
the L2 header in the name, plus a tamper check.

Key property of tracked changes: deleted text **remains in the XML** (marked
`w:del`) until accepted, so anchors survive deletion; splits keep the bookmark
on the first half; brand-new paragraphs have no anchor but sit between two
anchored neighbours.

### `review_apply.py` (new; replaces the tracked-changes half of review_extract)

Per returned docx, per paragraph carrying `w:ins`/`w:del`:

1. **Anchor** — bookmark → sidecar entry. Verify: reject-all-changes on the
   paragraph and compare `sha1` against the recorded hash. Mismatch → anchor
   suspect → fallback. No bookmark (new paragraph) → position between
   neighbouring verified anchors (an insertion at a known position is still
   deterministic *placement*; whether its *content* is appliable is decided
   below). Still ambiguous → fallback.
2. **Route** by target + edit shape (the decision table):

   | Tracked change | Route |
   |---|---|
   | Text-level edit in a `procedure` or `static` file, anchor verified | apply pipeline (step 3) |
   | Adds/removes/restructures a callout definition line (`> **LABEL — ID:**`) | notes.yaml → drafter (ID minting + grammar) |
   | Edit inside a Python-derived file | triage list (regenerated file; real fix is fragment/registry) |
   | Edit in an agent-owned derived file (RACI, dependencies) | notes.yaml → that agent |
   | Anchor missing / ambiguous / hash-mismatched | notes.yaml → drafter |

3. **Apply pipeline** (in memory, per edit):
   - Compute the reviewer-accepted text of the paragraph.
   - Inverse transforms: global display callout IDs → this procedure's local
     IDs (invert `doc_model.callout_display_ids`); resolved cross-reference
     text is left literal (a reviewer types plain text, not tokens).
   - Splice into the fragment at the mapped paragraph (whole-paragraph
     replacement; edited paragraphs are written as one line — markdown does
     not require wrapping).
   - **Verify or revert**: (a) run reconcile's per-fragment checks on the
     spliced fragment; (b) forward-render the spliced paragraph with the same
     transforms and require byte-equality with the reviewer-accepted text.
     Any failure → revert the splice, emit a note instead (carrying original
     text, edited text, and the anchor context — a *richer* note than today).
4. Emit a compact report: applied / noted / triaged counts per file, so the
   orchestrator's gate message shows the split.

Precision is 100% by construction (nothing unverified is written); recall is
best-effort and its failures cost tokens, not correctness.

### Notes quality upgrade

Fallback notes gain the anchor context (procedure → A–H subsection → step,
original + edited text) so the drafter — and the human at triage — see exactly
where the reviewer was, even when the apply couldn't be mechanical.

### Orchestrator glue

`_review/returned/*.docx` → `review_apply.py` first; its fallback notes merge
into `_review/{slug}.notes.yaml`; `apply_review` then dispatches drafters only
for procedures that actually have notes. Comments are extracted exactly as
today. Applied-only returns with no notes skip the drafter pass entirely.

## Acceptance

Round-trip live test on the test area:
- Render a kit doc; script a set of edits into the XML the way Word writes them
  (insert, delete, replace, paragraph split, edit inside a callout body, edit
  of a callout label line, edit in a derived table).
- `review_apply.py` applies the text edits (fragments diff as expected,
  reconcile clean), routes the callout-line edit + derived-table edit to
  notes/triage, and the re-rendered doc reproduces every applied edit.
- Corrupt one bookmark deliberately → that edit lands in notes, nothing is
  written for it.

## Out of scope

- Applying comments (stays with drafters — by design).
- Edits to headings/titles (manifest identity → human/triage).
- Cross-fragment moves (cut from one procedure, paste into another) → notes on
  both sides.
