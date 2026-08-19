#!/usr/bin/env python3
"""
hygiene.py — M43's callout-hygiene feeder (docs/v2/M43-drafting-path-hygiene.md
Part D). The mechanical half of the librarian's callout-grooming trigger, which
until now had a license to groom and nothing feeding it.

WHAT THIS MODULE IS. Three candidate generators over one ENGAGEMENT's corpus.
Each says a small, checkable thing — "these two validation gaps say nearly the
same words", "this step's gap is open while a source tagged to that step is
still unread", "this control declares none of the four facts a control is made
of" — and each candidate carries its own MECHANICAL GROUNDS: the ids, the files,
the ledger's own note, the callout text verbatim. Nothing here says whether a
candidate MATTERS. Whether two gaps are really one question, whether the unread
source actually answers the gap, whether a prose CTRL already carries the four
facts in sentences — that is the librarian's judgment (the grooming license),
and it is the whole reason these are candidates and not verdicts. A generator
that started deciding would be judgment leaking into the deterministic layer,
which is precisely the failure M43's complexity accounting names.

WHY ENGAGEMENT-SCOPED, when analysis.py is area-scoped. Two of the three
questions are only answerable above the area: duplicate gaps travel BETWEEN
areas (two drafters working adjacent areas from the same interview mint the
same gap twice — the commonest real duplication), and the ledger is a single
engagement-level artifact. So every function takes `root` (the engagement root,
the folder holding `components/` and `_sources/`) and walks the areas the way
engagement.py and coverage_map.py already do — name order, manifest required —
rather than minting a third area walk.

READ-ONLY, CACHE-FREE. Every function opens files for reading only: no write,
no mkdir, no dotfile, and not even a module-level memo of a manifest or a
declaration (analysis.py's rule, same reason — a cached candidate set is a
persisted opinion that can drift out of step with the corpus, and the pass is
cheap). Pinned by tests/test_hygiene_m43.py, which fingerprints the whole
engagement across a full pass.

REFUSALS. `HygieneError` is raised only when the DECLARATION or a BINDING does
not support the question being asked — the same posture as AnalysisError. A
corpus that is merely thin (no areas, no steps, no gaps, no ledger) is not a
defect: it returns `[]`.

VOCABULARY COMES FROM THE DECLARATION AND THE BINDINGS, never from prose
constants typed here. Not one callout label, prefix, part slug or field name
appears in this file:

  * the GAP kind is the callout kind the shipped information-request
    definition's `step-gaps` binding selects;
  * the CONTROL kind is the callout kind the process-controls-matrix
    definition's `control-callouts` binding selects, cross-checked against the
    declaration by analysis.py's own rule;
  * the CONTROL's FIELD NAMES are read off that kind's `fields` declaration
    (M43 Part C, kernel/types/process-step.yaml). Typing "Performer" here
    would put the M42 doctrine in two places and let them drift; the point of
    declaring the vocabulary was to have one home for it.

The resolvers, the step walk, the IPO/citation helpers and the SRC grammar are
IMPORTED from analysis.py and matrix_views.py rather than re-spelled — one
parser for a callout, so a hygiene candidate can never disagree with the matrix
or the analyst about what a step's callouts are. The M36 shape audit passes this
module on merit, with zero allowlist entries.

THE DUPLICATE THRESHOLD, and how it was calibrated (the one tuned number in
this module, so it is written down with its evidence rather than left as a
magic constant):

  Similarity = JACCARD overlap of the two normalized gap bodies' token sets.
  Normalization: `[[slug]]` tokens flattened to their slug (markup, not
  words), SRC-id citations stripped (two gaps citing the same interview are
  not thereby the same gap — and the citations are the loudest shared tokens
  in a well-drafted corpus), lowercased, whitespace collapsed, then split into
  word tokens with a small closed-class STOPLIST removed (see `_STOP`:
  articles, copulas, pronouns and connectives carry no gap identity and
  otherwise dominate the overlap of any two English sentences).

  Threshold = 0.30, calibrated against the IPO exemplar corpus and the
  acceptance test's injected near-duplicate:

    the injected GAP (same question as purchasing/match-po's gap, different
    words: "SOP names two percent / AP Manager described plus or minus five
    percent") vs that gap                              0.37   -> PAIRED
    the corpus's four distinct gaps, worst pair
    (the Ephesoft-threshold gap vs the match-tolerance
    gap — same SOP-vs-practice SHAPE, different
    subject, which is exactly the hardest true
    negative in the corpus)                            0.20   -> not paired
    every other distinct pair                        <= 0.13   -> not paired

  0.30 sits in the middle of that 0.20/0.37 gap rather than snug against
  either side. Both failure modes are stated honestly: at this threshold a
  paraphrase sharing few words is MISSED (a duplicate this pass cannot see is
  never silently "resolved" — the librarian still reads the register), and two
  gaps about different subjects that share a drafting skeleton can be OFFERED
  (which costs the librarian one glance at two texts printed side by side).
  If real engagements drown, the threshold is the knob — never the honesty.

Python 3, stdlib + the engine's own modules.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import re

from itertools import combinations
from pathlib import Path

import kernel
import ledger

# The declaration-driven resolvers, the manifest-ordered step walk, the citation
# grammar and the token flattener already exist for the analyst's candidates.
# Reused, not re-spelled: the shared kind resolvers come from their M53 public
# home (scripts/kinds.py), the rest from analysis — one parser for a callout,
# so a hygiene candidate can never disagree with the matrix or the analyst
# about what a step's callouts are.
import kinds

from kinds import (
    area_steps as _area_steps,
    callout_blob as _callout_blob,
    callouts as _callouts,
)

from analysis import (
    SRC_ID_RE as SRC_ID_RE,
    REQUEST_DEFINITION as REQUEST_DEFINITION,
    BINDING_GAPS as BINDING_GAPS,
    _control_prefix as _control_prefix,
    _flatten as _flatten,
)

# The engagement's area walk (name order, `_`-prefixed dirs skipped).
from coverage_map import _area_dirs as _area_dirs

#: The candidate kinds this module emits — the librarian contract's existing
#: return vocabulary, named here so a caller can filter without typing a string
#: that only ever appeared inside a dict literal.
KIND_DUPLICATE_GAPS = "duplicate-gaps"
KIND_GAP_ANSWERED = "gap-likely-answered"
KIND_CTRL_MISSING_FIELD = "ctrl-missing-field"

#: The duplicate-detection threshold. See the module docstring for the full
#: calibration table; the short version is 0.30 sits mid-gap between the
#: corpus's worst true negative (0.20) and the injected near-duplicate (0.37).
DUPLICATE_THRESHOLD = 0.30

#: Closed-class words carrying no gap identity. Not document vocabulary — no
#: part, label, prefix or field name is in here, and the audit is welcome to
#: check: this is English function words, the same job engagement.py's `_STOP`
#: does for titles (a different list because that one scores TITLES and this one
#: scores sentences).
_STOP = frozenset("""
a an the and or but nor so if then than that this these those there here
is are was were be been being am do does did done have has had having
of to in on at by for from with without into onto over under about as
it its they them their he she her his we us our you your i me my
not no any all some each every both either neither only just also very
which who whom whose what when where whether why how while during since
can could may might must shall should will would
""".split())

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-]*")


class HygieneError(RuntimeError):
    """A generator refused: the declaration or a binding does not support the
    question being asked. Never raised for a corpus that is merely thin."""


# --------------------------------------------------------------------------- #
# The derived vocabulary
# --------------------------------------------------------------------------- #

def _gap_prefix(tdecl, area) -> str:
    """The gap callout kind's prefix — `kinds.gap_prefix` (the shared resolver,
    one body since M53), refusing as `HygieneError` so this module's callers
    keep their historical catch sites."""
    return kinds.gap_prefix(tdecl, area, _err=HygieneError)


def _declared_fields(tdecl, prefix: str) -> tuple[str, ...]:
    """The declared sub-field names of one callout kind, in DECLARATION order
    (M43 Part C). Empty when the kind declares none — and a thin-CTRL question
    asked of a kind that declares no fields has no answer, so the caller
    refuses rather than inventing names."""
    for callout in tdecl.callouts:
        if callout.prefix == prefix:
            return tuple(getattr(callout, "fields", ()) or ())
    raise HygieneError(
        f"{tdecl.name}: no callout kind with prefix {prefix!r} is declared — "
        f"the binding and the declaration disagree")


# --------------------------------------------------------------------------- #
# Reading the engagement (read-only, re-read on every call)
# --------------------------------------------------------------------------- #

def _areas(root) -> list[Path]:
    """The engagement's area directories that carry a manifest, name order.

    A directory mid-scaffold (no manifest) is not a defect here: hygiene is a
    reporting pass, and an area with nothing authored yet reads as "nothing to
    groom" rather than taking the whole feeder down."""
    return [d for d in _area_dirs(Path(root))
            if (d / "manifest.json").is_file()]


def _gap_records(root) -> list[dict]:
    """Every gap-kind callout in the engagement: areas in name order, steps in
    manifest order, callouts in document order."""
    out: list[dict] = []
    for area in _areas(root):
        tdecl, steps = _area_steps(area)
        prefix = _gap_prefix(tdecl, area)
        for step in steps:
            for callout in _callouts(step["entity"], prefix):
                out.append({
                    "id": str(callout.get("id") or ""),
                    "area": area.name,
                    "slug": step["slug"],
                    "heading": step["heading"],
                    "text": str(callout.get("text") or ""),
                    "blob": _callout_blob(callout),
                })
    return out


def _tokens(text: str) -> frozenset[str]:
    """The token set the duplicate rule compares — see the docstring's
    normalization paragraph."""
    flat = SRC_ID_RE.sub(" ", _flatten(text))
    flat = re.sub(r"\s+", " ", flat).strip().lower()
    return frozenset(w for w in _WORD_RE.findall(flat) if w not in _STOP)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


# --------------------------------------------------------------------------- #
# 1 — duplicate gap candidates
# --------------------------------------------------------------------------- #

def duplicate_gap_candidates(root) -> list[dict]:
    """Pairs of gap-kind callouts whose normalized bodies overlap at or above
    `DUPLICATE_THRESHOLD`, anywhere in the engagement.

    Cross-area pairs are included from day one (M43's deferred list says so
    explicitly): two areas drafted from one interview are where the same
    question gets minted twice. Each candidate names BOTH ids, BOTH steps and
    areas, and BOTH texts verbatim — the librarian judges by reading them side
    by side, which is only possible if this module hands over the words rather
    than a score. Order: the engagement walk's order, first member then second
    (deterministic, no ranking implied). Read-only."""
    records = _gap_records(root)
    tokens = {i: _tokens(r["blob"]) for i, r in enumerate(records)}

    out: list[dict] = []
    for i, j in combinations(range(len(records)), 2):
        score = _jaccard(tokens[i], tokens[j])
        if score < DUPLICATE_THRESHOLD:
            continue
        a, b = records[i], records[j]
        shared = sorted(tokens[i] & tokens[j])
        out.append({
            "kind": KIND_DUPLICATE_GAPS,
            "ids": [a["id"], b["id"]],
            "slugs": [a["slug"], b["slug"]],
            "areas": [a["area"], b["area"]],
            "texts": [a["text"], b["text"]],
            "similarity": round(score, 3),
            "grounds": [
                f"{a['id']} on {a['area']}/{a['slug']}: {a['text']}",
                f"{b['id']} on {b['area']}/{b['slug']}: {b['text']}",
                f"normalized token overlap {score:.2f} at or above the "
                f"{DUPLICATE_THRESHOLD:.2f} threshold; shared terms: "
                + ", ".join(shared),
            ],
        })
    return out


# --------------------------------------------------------------------------- #
# 2 — gaps a tagged-but-unread source may already answer
# --------------------------------------------------------------------------- #

def answered_gap_candidates(root) -> list[dict]:
    """A step's open gap × every source tagged to that step and not yet
    consumed by that area (`ledger.outstanding`, M34's primitive).

    The mechanical claim is exactly two facts: this gap is open, and material
    the ledger says was tagged to this very step has not been read. Whether
    the source answers the gap is the librarian's read of the source — which
    is why the grounds carry the SRC id, its file, the ledger's own note and
    the gap text verbatim, and why nothing here closes anything.

    An engagement with no ledger has nothing outstanding, so this returns `[]`
    rather than refusing. Order: areas in name order, steps in manifest order,
    gaps in document order, sources in registration order. Read-only."""
    root = Path(root)
    out: list[dict] = []
    try:
        notes = {str(e.get("id") or ""): e for e in ledger.entries(root)}
    except ledger.LedgerError as exc:
        raise HygieneError(f"the ledger cannot be read: {exc}") from exc

    for area in _areas(root):
        owed = ledger.outstanding(root, area.name)
        if not owed:
            continue
        tdecl, steps = _area_steps(area)
        prefix = _gap_prefix(tdecl, area)
        for step in steps:
            gaps = _callouts(step["entity"], prefix)
            if not gaps:
                continue
            # registration order, filtered to the sources owing THIS step
            for sid in [s for s in notes if step["slug"] in (owed.get(s) or [])]:
                entry = notes[sid]
                src_file = str(entry.get("file") or "")
                note = str(entry.get("note") or "")
                for callout in gaps:
                    gap_id = str(callout.get("id") or "")
                    gap_text = str(callout.get("text") or "")
                    out.append({
                        "kind": KIND_GAP_ANSWERED,
                        "id": gap_id,
                        "slug": step["slug"],
                        "heading": step["heading"],
                        "area": area.name,
                        "src": sid,
                        "src_file": src_file,
                        "note": note,
                        "text": gap_text,
                        "grounds": [
                            f"{gap_id} is open on {area.name}/{step['slug']}: "
                            f"{gap_text}",
                            f"{sid} ({src_file}) is tagged to "
                            f"{area.name}/{step['slug']} and not yet consumed "
                            f"by this area",
                        ] + ([f"ledger note for {sid}: {note}"] if note else []),
                    })
    return out


# --------------------------------------------------------------------------- #
# 3 — controls carrying none of the declared facts
# --------------------------------------------------------------------------- #

def thin_ctrl_candidates(root) -> list[dict]:
    """Control-kind callouts missing one or more of the DECLARED field names.

    The names come from the declaration (M43 Part C) and are compared against
    the callout's parsed sub-fields case-insensitively — a drafter's casing is
    not a hygiene finding — but `missing` reports the DECLARED spelling, in
    declaration order, because that is the vocabulary the drafter is being
    pointed at.

    The whole frozen IPO corpus appears here, BY DESIGN: its CTRLs are
    prose-only, and whether the prose already carries performer, comparison,
    trigger and evidence is exactly the judgment a candidate exists to invite.
    This is also the flood risk M43 names — a presenter must show counts and
    samples, not a wall, and the answer is never to quietly drop candidates.
    Order: areas in name order, steps in manifest order, callouts in document
    order. Read-only."""
    out: list[dict] = []
    for area in _areas(root):
        tdecl, steps = _area_steps(area)
        prefix = _control_prefix(tdecl, area)
        declared = _declared_fields(tdecl, prefix)
        if not declared:
            raise HygieneError(
                f"{tdecl.name}: the control kind {prefix!r} declares no "
                f"`fields` — there is no field vocabulary to check against, "
                f"and this generator will not type one")
        for step in steps:
            for callout in _callouts(step["entity"], prefix):
                present = {str(k).strip().lower()
                           for k in (callout.get("fields") or {})}
                missing = [f for f in declared if f.lower() not in present]
                if not missing:
                    continue
                text = str(callout.get("text") or "")
                out.append({
                    "kind": KIND_CTRL_MISSING_FIELD,
                    "id": str(callout.get("id") or ""),
                    "slug": step["slug"],
                    "heading": step["heading"],
                    "area": area.name,
                    "missing": missing,
                    "declared": list(declared),
                    "text": text,
                    "grounds": [
                        f"{callout.get('id')} on {area.name}/{step['slug']}: "
                        f"{text}",
                        f"declares no {', '.join(missing)} sub-field"
                        f"{'s' if len(missing) > 1 else ''} "
                        f"(declared vocabulary: {', '.join(declared)})",
                    ],
                })
    return out
