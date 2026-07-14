# M9 — Dual-mode render + per-owner review kits

> **Status: BUILT.** Deltas from this design: the gap workbook carries a
> hidden `Ref (do not edit)` column (`slug#LOCAL-ID`) so answers round-trip
> with no display-ID guessing; workbooks fall back to a built-in stdlib xlsx
> writer (never CSV); screenshot templates self-identify via a core-property
> doc id + `_review/.maps/` sidecar (same pattern as review docs); notes files
> are merge-append (`notes_util.py`) since a slug now accumulates notes from
> several returned files.

## Goal

Make the review loop person-shaped and the deliverable mode-aware:

1. **Working mode** renders the full draft (gaps + pain points visible, as today)
   **plus** a `_review/kits/` tree — one folder per process owner containing the
   per-L3 procedure docs they own (tracked changes on by default), a gap
   workbook scoped to their items, and a screenshot template scoped to their
   items. The engagement lead sends each folder to its person; nothing needs
   explaining.
2. **Final mode** renders the client-facing document: VALIDATION REQUIRED
   callouts, `[[GAP-…]]` body flags, and Appendix B are stripped (count
   reported, never refused — accepting open gaps is the user's judgment);
   screenshot placeholders become embedded images with a small italic caption
   below each, where a captured image exists.
3. Deterministic **return-trip ingestion** for the two structured kit pieces:
   workbook answers → review notes; pasted screenshots → image files. (Tracked
   changes in the docs are M10.)

## Why

Field experience: one full draft bouncing around the org is slow and lossy.
Reviews actually happen per person, and the people who can answer are the ones
closest to the work (lowest in the org chart), not their managers. Gaps are
produced liberally by drafters (correct behavior) and will not all be filled —
so gap triage needs a form (Excel) a non-consultant can fill, and the final
deliverable needs to shed the scaffolding cleanly.

## Design

### Render modes

`render.py <area> --mode working|final` (default `working`, current behavior
preserved).

- **working** — unchanged output, plus (folder input only) provenance anchors
  (see M10 — landed here so the first kits sent out are already
  M10-compatible): each emitted paragraph gets an opaque Word bookmark
  (`cw_<n>`) and the renderer writes a sidecar `<docx>.map.json`:
  `{n: {file, slug, l2, subsection, para_index, sha1(rendered_text)}}`.
- **final** —
  - VALIDATION REQUIRED callouts removed; `[[GAP-…]]` body flags removed
    (deleted, not bolded); Appendix B (gap log) omitted.
  - SCREENSHOT PLACEHOLDER callouts: if `_assets/screens/{slug}/{local-id}.*`
    exists, embed the image with the SC text as an *italic caption paragraph
    below the image* (no callout box). No image → keep the placeholder box and
    count it.
  - Exit report: `stripped N open gaps; M screenshots embedded, K placeholders
    remain`. Never refuses.

### Subset render

`render.py <area> --slugs a,b,c` renders cover + only those procedure sections.
**Display numbers and global callout display IDs are computed from the FULL
manifest/folder** — a subset doc shows the same `2.3` and `GAP-07` as the full
draft, so kit conversations and the master copy always agree. Derived/back
matter sections are omitted from subset docs (the full draft is the context
document).

### People + rank (`scripts/people.py`, new shared module)

- Load `_reference/roles.yaml` (`people:` lists) + `_client/org-chart.yaml`.
- `rank(person)` = depth in the `reports_to` tree (root = 0). Deeper = lower
  rank = **preferred contact** (closest to the work); their manager is the
  natural escalation, listed alongside.
- `contact_for_role(role)` → the lowest-ranked person holding that role
  (tie → first listed; role with no people → None).
- Person folder slugs are kebab-case full names.

### Ownership resolution (deterministic)

- **Procedure owner** = the Preparer line in `B. Quick Reference`, matched
  against registry role names/aliases (string match, no judgment), resolved via
  `contact_for_role`. Unresolvable → `unassigned/` kit.
- **Gap row owner** = the gap's `Owner to confirm` role resolved the same way;
  falls back to the procedure owner when TBD/unresolvable. A gap may therefore
  land in a workbook of someone who doesn't own the procedure — intended.
- **Screenshot item owner** = the procedure owner (SC callouts carry no owner
  field).

### Kit emission (`scripts/kits.py`, new)

`python3 kits.py <area> [-o {area}/_review/kits]` — runs after a working-mode
render (advisor: same stage).

```
_review/kits/
  index.md                       person → procedures / gap count / SC count (send checklist)
  <person-slug>/
    README.md                    instructions blurb (usable as the email body)
    <num>_<slug>.docx            one per owned procedure; tracked changes ON by
                                 default (settings.xml <w:trackChanges/>); sidecar .map.json each
    gaps_<person-slug>.xlsx      their gap rows: Gap ID (display), Procedure,
                                 Question, Nature, Escalation, Answer (blank), Status (blank)
    screenshots_<person-slug>.docx  their SC items: display id, procedure+step,
                                 italic what-to-capture, bordered paste box (anchored per entry)
```

- Workbooks via `openpyxl` when importable, else a **minimal built-in xlsx
  writer** (a single-sheet workbook is just zipped XML — stdlib `zipfile` does
  it) so the deliverable is always a real `.xlsx`, never a CSV consolation.
- Everything regenerates idempotently; kits are derived artifacts (git-ignored
  under `_review/`).

### Return-trip ingestion (deterministic, zero tokens)

Returned files are dropped into `{area}/_review/returned/` (any mix, any
subset):

- `gaps_ingest.py` — filled workbooks: each non-empty Answer becomes a
  procedure-anchored note (`_review/{slug}.notes.yaml`, same shape the drafters
  already consume: "GAP-xx — answer: …"). Closing a gap rewrites prose →
  drafter work, by design.
- `screens_ingest.py` — filled screenshot templates: images extracted per
  anchored entry → `_assets/screens/{slug}/{local-id}.png` (+ an index of
  entries returned empty). Final mode embeds them.
- Reviewed `.docx` with tracked changes/comments → M10 (`review_apply.py`);
  until M10 lands, `review_extract.py` keeps handling them as today.

### Advisor / orchestrator glue

- `render` (working) emits kits in the same stage; the `review` gate message
  lists `_review/kits/index.md` as "send these".
- New files under `_review/returned/` → advisor routes to the ingestion
  scripts before `apply_review`.
- `review_extract.py` learns to accept a directory (kit returns arrive as many
  files, not one).

## Acceptance

- Working render of the live test area emits full draft + kits; every procedure
  lands in exactly one kit (or `unassigned/`); subset docs show identical
  display numbers/callout IDs to the full draft.
- Kit docx opens in Word with track changes already on.
- Round trip on synthetic returns: filled workbook → notes.yaml rows; filled
  screenshot template → files under `_assets/screens/`; final render embeds
  them with italic captions and reports stripped-gap count.
- Final render of an area with zero captured screenshots still succeeds
  (placeholders remain, counted).

## Out of scope (→ M10)

Applying tracked changes from returned docs deterministically; richer notes
from anchors. M9 only *stamps* the anchors + sidecars so round-1 kits are
already apply-ready.
