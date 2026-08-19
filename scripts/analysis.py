#!/usr/bin/env python3
"""
analysis.py — the mechanical candidate generators (docs/v2/M39-analysis-verbs.md,
extended by M49) and the analyst's work-order CLI.

THE SHIPPED SURFACE. Four generators, each area-scoped, deterministic and
read-only:

  control_gap_candidates   verb 2 — steps that produce and declare no control
  handoff_candidates       verb 4 — orphan outputs and shared inputs (handoff
                           friction across the IPO edges)
  pain_inventory           verb 1's raw material — every pain-kind callout,
                           verbatim, with its sources
  conflict_records         the fourth verb (M49 Part B) — every gap that is a
                           conflict on its face (two+ distinct SRC citations,
                           or the v1 `Nature: conflict` grammar)

plus the CLI (M49 Part A): `analysis.py brief <area>` prints the analyst's
work order — the license block, all four feeds, the findings-register state
and the objective — as one read-only block (`analyst_brief`).

WHAT THIS MODULE IS, AND WHAT IT DELIBERATELY IS NOT. Everything here is a
CANDIDATE generator: a pure, deterministic pass over one area's corpus that says
"this step has outputs and declares no control", "nothing in this area consumes
this output", "these are the pains that were voiced, with their sources". Each
candidate carries its own MECHANICAL GROUNDS — the evidence the machine actually
looked at, in the corpus's own words.

Not one function here says whether a candidate MATTERS. Materiality, clustering,
severity, whether a "missing" control is really compensated elsewhere — that is
the analyst agent's judgment (the consult-analyst license), and the findings it
proposes go through the human gate in findings.py. The house pattern of the
ticket: mechanical candidates, bounded judgment. A generator that started
scoring candidates would be assessment leaking into the deterministic layer,
which is exactly the failure the M39 complexity accounting names.

READ-ONLY CONTRACT (pinned by tests/test_findings_m39.py::TestCandidates, which
fingerprints the whole engagement across a full generator pass): every function
below opens files for reading only. No write, no mkdir, no touch, no dotfile, no
cache — not even a module-level memo of a manifest (coverage_map.py's rule, same
reason: a cached candidate set is a persisted opinion that can drift out of step
with the corpus, and the pass is cheap enough that nobody needs one).

DECLARATION-DRIVEN, NO SHAPE LITERALS (the M36 shape audit is watching, and this
module is written to pass it on merit rather than by allowlist). Not one part
slug, part title, callout label or callout prefix is typed here. The vocabulary
comes from two declared sources, exactly as scripts/matrix_views.py does it:

  * `kernel.load_type(STEP_TYPE)` — the parts, their kinds and their order, and
    the callout kinds with their homes;
  * the SHIPPED DEFINITIONS' bindings — which parts are the IPO edges, which
    callout kind is the control, and (by subtraction, below) which is the pain.
    The loader's stage 2 has already checked every one of those names against
    the declaration, so a reshape of the type fails the definition rather than
    silently changing what these generators mean.

The only names typed in this module are BINDING NAMES and type names — the
contract with the definition files, not the document's shape.

  DERIVING THE THREE KINDS, each rule written down because each is a judgment
  about the DATA MODEL that a reader is entitled to check:

  inputs / outputs  the IPO binding (`io-edges`) selects the step's edge parts;
                    of those, the LIST-kind parts in DECLARATION ORDER are the
                    edges, and the type's order is the IPO order — what a step
                    consumes is declared before what it produces (the M33 IPO
                    parts table). So: first list part = consumed, last =
                    produced. If the declaration ever stops carrying exactly
                    two list edge parts, every generator here REFUSES by name
                    rather than guessing which half is which.
  control kind      the callout kind the matrix definition's `control-callouts`
                    binding selects. Cross-checked against the declaration: its
                    home must be a part that is NOT an edge part (a control kind
                    homed in a list part would mean the binding and this module
                    disagree about what a control is — refuse, do not adapt).
  pain kind         SUBTRACTION between two shipped definitions, both scoped to
                    this type: the matrix's `open-items` binding selects the
                    open callout kinds (pains and validation gaps), and the
                    information-request's `step-gaps` binding selects the gap
                    kind alone. What is open but is not a gap is the pain kind.
                    Indirect, and chosen deliberately: no shipped definition
                    binds the pain kind by itself, and the alternative was to
                    type its label — the one thing the audit exists to stop.
                    If the subtraction does not land on exactly one kind, the
                    inventory refuses and names both sets.

ARTIFACT MATCHING — the conservative rule, stated with its misses (verb 4 stands
or falls on this, and a fuzzy matcher tuned until the fixture came out right
would be fixture convenience dressed as analysis):

  normalize(item) = the item text, with any `[[slug]]` token reduced to its
  slug, cut at the FIRST em-dash (`—`) — the drafting convention for an edge's
  source/destination attribution, so the head is the artifact and the tail is
  the attribution — then lowercased and whitespace-collapsed (hard-wrapped
  items are one item, as matrix_views already treats them).

  Two edges are THE SAME ARTIFACT only when their normalized heads are EQUAL.
  That is all. No stemming, no substring containment, no synonym table, no
  token-overlap score.

  WHAT THIS MISSES, honestly (each of these is a false candidate the analyst may
  discard, or a real link this pass cannot see — never silently "resolved"):
    * paraphrase. "Payment register for the run" and "the weekly payment
      register" are two artifacts to this rule. An orphan-output candidate is
      therefore a candidate, not a proof of orphanhood.
    * parenthetical qualifiers are kept, so "captured invoice header record
      (pending bill)" matches only the same qualifier.
    * an item with no em-dash keeps its whole text as the artifact head.
    * a plural/singular difference is a difference.
  The consumer test is deliberately WIDER than the artifact match, to keep the
  false-positive rate honest: an output is an orphan only if no step's inputs
  name the same artifact AND the output item names no consumer step by
  `[[slug]]` token. A drafter who wrote the edge as a cross-reference has said
  who consumes it, whatever words they used for the thing.

Python 3, stdlib + the engine's own modules. Small parsing helpers are IMPORTED
from scripts/matrix_views.py (the module that already reads these parts for the
matrix) rather than re-spelled here — one parser for the IPO lists, so a
candidate can never disagree with the matrix about what a step's edges are. The
shared kind resolvers — the step walk, the callout reads, the gap-kind and
`Nature:` resolution — live in scripts/kinds.py (M53's shared public home) and
are re-exported here under their historical private names for this module's
own use and its older importers.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import argparse
import re

from pathlib import Path

import kernel
import kinds

# The IPO list parser, the manifest-ordered step walk, the node walk and the
# binding readers already exist for the matrix view. Reused, not re-spelled.
from matrix_views import (
    _binding as _binding,
    _names as _names,
    _nodes as _nodes,
    _prefixes as _prefixes,
    _steps as _steps,
    _LIST_ITEM_RE as _LIST_ITEM_RE,
    _TOKEN_RE as _TOKEN_RE,
    STEP_TYPE as STEP_TYPE,
)

#: The definitions whose bindings carry this module's vocabulary, and the
#: binding names inside them. Definition + binding names only: the contract with
#: the definition files, never the document's shape.
MATRIX_DEFINITION = "process-controls-matrix"
REQUEST_DEFINITION = kinds.REQUEST_DEFINITION
BINDING_IO = "io-edges"
BINDING_CONTROLS = "control-callouts"
BINDING_OPEN = "open-items"
BINDING_GAPS = kinds.BINDING_GAPS

#: An SRC id as the ledger mints it and as callout bodies name it (coverage_map's
#: grammar, same shape, matched on the id half so the v1 `area/SRC-001` form
#: counts too).
SRC_ID_RE = re.compile(r"\bSRC-[A-Za-z0-9]+\b")

#: The attribution separator in an authored edge item ("<artifact> — from X").
_ATTRIBUTION_DASH = "—"

#: The candidate kinds verb 4 emits. Kind names of THIS module's output — not
#: document shape, and named here so a caller can filter without typing strings
#: that only appear in a dict literal.
KIND_ORPHAN_OUTPUT = "orphan-output"
KIND_SHARED_INPUT = "shared-input"

#: The conflict-record kind (M49 Part B — the fourth M39 verb).
KIND_CONFLICT_RECORD = "conflict-record"

#: The v1 conflict grammar: a GAP callout field whose VALUE says the gap is a
#: conflict. Field name and value are compared case-insensitively — the field is
#: hand-authored prose furniture, not document shape (the shape audit's concern
#: is part/callout vocabulary, which still comes from the declaration below).
NATURE_FIELD = kinds.NATURE_FIELD
NATURE_CONFLICT = "conflict"

#: How many DISTINCT sources make a gap a conflict on its face (the two-mint
#: doctrine's conflict shape: both readings, both citations).
CONFLICT_MIN_SRCS = 2


class AnalysisError(RuntimeError):
    """A generator refused: the declaration or a binding does not support the
    question being asked. Never raised for a corpus that is merely thin."""


# --------------------------------------------------------------------------- #
# The derived vocabulary (see the docstring's three rules)
# --------------------------------------------------------------------------- #

def _definition_bindings(name: str, area) -> dict:
    import definitions
    return definitions.load_definition(name, area=area).bindings or {}


def _step_type():
    return kernel.load_type(STEP_TYPE)


def _node_type():
    """The taxonomy-node type declaration, named through the module that owns the
    node convention rather than re-typed here."""
    import coverage_map
    return kernel.load_type(coverage_map.NODE_TYPE)


def _edge_parts(tdecl, area) -> tuple[str, str]:
    """`(consumed part slug, produced part slug)` — rule 1 of the docstring."""
    bound = set(_names(_binding(_definition_bindings(MATRIX_DEFINITION, area),
                               BINDING_IO), "parts"))
    lists = [p.slug for p in tdecl.parts if p.slug in bound and p.kind == "list"]
    if len(lists) != 2:
        raise AnalysisError(
            f"{STEP_TYPE}: the {BINDING_IO!r} binding selects {len(lists)} "
            f"list-kind part(s) ({lists}) — the IPO generators need exactly two "
            f"(consumed, produced) and will not guess which half is which")
    return lists[0], lists[-1]


def _control_prefix(tdecl, area) -> str:
    """The control callout kind's prefix — rule 2 of the docstring."""
    labels = _names(_binding(_definition_bindings(MATRIX_DEFINITION, area),
                             BINDING_CONTROLS), "callouts")
    prefixes = _prefixes(tdecl, labels)
    if len(prefixes) != 1:
        raise AnalysisError(
            f"{BINDING_CONTROLS!r} selects {len(prefixes)} callout kind(s) "
            f"({prefixes}) — the control-gap generator asks about one kind")
    prefix = prefixes[0]
    homes = {c.prefix: c.home for c in tdecl.callouts}
    edges = set(_edge_parts(tdecl, area))
    if homes.get(prefix) in edges:
        raise AnalysisError(
            f"the control kind {prefix!r} is homed in the edge part "
            f"{homes.get(prefix)!r} — the binding and this generator disagree "
            f"about what a control is")
    return prefix


def _gap_prefix(tdecl, area) -> str:
    """The validation-gap callout kind's prefix — `kinds.gap_prefix` (the
    shared resolver, one body since M53), refusing as `AnalysisError` so this
    module's callers keep their historical catch sites."""
    return kinds.gap_prefix(tdecl, area, _err=AnalysisError)


def _pain_prefix(tdecl, area) -> str:
    """The pain callout kind's prefix — rule 3 (open minus gap) of the docstring."""
    open_kinds = _prefixes(tdecl, _names(
        _binding(_definition_bindings(MATRIX_DEFINITION, area), BINDING_OPEN),
        "callouts"))
    gap_kinds = _prefixes(tdecl, _names(
        _binding(_definition_bindings(REQUEST_DEFINITION, area), BINDING_GAPS),
        "callouts"))
    rest = [p for p in open_kinds if p not in set(gap_kinds)]
    if len(rest) != 1:
        raise AnalysisError(
            f"the pain kind does not resolve: {BINDING_OPEN!r} selects "
            f"{open_kinds} and {BINDING_GAPS!r} selects {gap_kinds}, leaving "
            f"{rest} — the inventory needs exactly one kind and will not "
            f"fall back on a typed label")
    return rest[0]


# --------------------------------------------------------------------------- #
# Reading the corpus (read-only, and re-read on every call)
# --------------------------------------------------------------------------- #

def _items(step: dict, part: str) -> list[str]:
    """The authored list items of one part, as items.

    matrix_views._list_items joins them into a cell; the generators need them
    separately, so the same regex and the same hard-wrap tolerance (a
    continuation line belongs to the item above) are applied item-wise here."""
    body = step["entity"].parts_bodies().get(part, "") or ""
    items: list[str] = []
    for line in body.splitlines():
        m = _LIST_ITEM_RE.match(line)
        if m:
            items.append(m.group("item").strip())
        elif items and line.strip():
            items[-1] = f"{items[-1]} {line.strip()}"
    return items


def _flatten(text: str) -> str:
    """`[[slug]]` / `[[#slug]]` reduced to the bare slug (tokens are markup, and
    the artifact's words are what the matching rule compares)."""
    return _TOKEN_RE.sub(lambda m: m.group(1).strip(), text)


def normalize_artifact(item: str) -> str:
    """The artifact identity of one edge item — THE matching rule, in one place.

    Tokens flattened, cut at the first em-dash (the attribution tail),
    lowercased, whitespace collapsed. Exact equality of the result is the only
    sameness this module claims; see the module docstring for what it misses."""
    head = _flatten(item).split(_ATTRIBUTION_DASH)[0]
    return re.sub(r"\s+", " ", head).strip().lower()


# The callout reads and the step walk moved to scripts/kinds.py (M53); the
# historical private names remain as aliases for this module and its importers.
_callouts = kinds.callouts
_callout_blob = kinds.callout_blob
_area_steps = kinds.area_steps


# --------------------------------------------------------------------------- #
# Verb 2 — control coverage candidates
# --------------------------------------------------------------------------- #

def control_gap_candidates(area) -> list[dict]:
    """Steps that PRODUCE something and declare no control of the control kind.

    One candidate per such step, in manifest order (the area's row order). The
    mechanical claim is exactly two facts — this step's produced-edge items
    exist, and no callout of the control kind is declared on it — and both are
    carried in `grounds` in the corpus's own words, so the analyst judges
    materiality against the evidence rather than against this module's summary.

    Prose in the control part is NOT counted as a control: a step may describe
    the absence of one (the fixture's exception-disposition step does exactly
    that), and treating narrative as a control assignment would hide the very
    candidates this verb exists to raise. That prose is handed over in
    `control_prose` instead — the analyst reads it, this module does not judge
    it. Read-only."""
    area = Path(area)
    tdecl, steps = _area_steps(area)
    _consumed, produced = _edge_parts(tdecl, area)
    prefix = _control_prefix(tdecl, area)
    homes = {c.prefix: c.home for c in tdecl.callouts}
    control_part = homes.get(prefix, "")

    out: list[dict] = []
    for step in steps:
        produced_edges = _items(step, produced)
        if not produced_edges:
            continue
        if _callouts(step["entity"], prefix):
            continue
        prose = (step["entity"].parts_bodies().get(control_part, "") or "").strip()
        out.append({
            "slug": step["slug"],
            "heading": step["heading"],
            "produced": produced_edges,
            "control_prose": prose,
            "srcs": sorted(set(SRC_ID_RE.findall(prose))),
            "grounds": [f"{len(produced_edges)} produced edge(s) declared: "
                        + "; ".join(produced_edges),
                        f"no {prefix} callout declared on {step['slug']}"]
                       + ([f"{control_part} prose present but carries no "
                           f"{prefix} callout"] if prose else []),
        })
    return out


# --------------------------------------------------------------------------- #
# Verb 4 — handoff friction candidates
# --------------------------------------------------------------------------- #

def handoff_candidates(area) -> list[dict]:
    """Orphan outputs and shared inputs across one area's IPO edges.

    * `orphan-output` — a produced edge whose artifact no step consumes AND
      whose item names no consumer step by `[[slug]]` token (the wider consumer
      test of the docstring). One candidate per orphan edge.
    * `shared-input` — one artifact consumed by two or more steps: a handoff
      several steps depend on, which is friction when the producer is one step's
      by-product. One candidate per artifact, its steps in manifest order.

    Owner-change detection (the ticket's third handoff shape) is NOT emitted:
    the area's steps carry role BINDINGS, but which of several bound roles owns
    an artifact at a given moment is authored in prose, so a mechanical
    owner-change claim here would be an inference wearing mechanical clothing.
    Recorded as a miss, not implemented quietly.

    Orphan candidates come first (in manifest order), then shared inputs (in
    artifact order) — deterministic, no ranking implied. Read-only."""
    area = Path(area)
    tdecl, steps = _area_steps(area)
    consumed_part, produced_part = _edge_parts(tdecl, area)
    known = {s["slug"] for s in steps}

    consumers: dict[str, list[str]] = {}
    for step in steps:
        for item in _items(step, consumed_part):
            consumers.setdefault(normalize_artifact(item), []).append(step["slug"])

    out: list[dict] = []
    for step in steps:
        for item in _items(step, produced_part):
            artifact = normalize_artifact(item)
            named = [t.strip().lstrip("#") for t in _TOKEN_RE.findall(item)]
            named = [t for t in named if t in known and t != step["slug"]]
            by_text = [s for s in consumers.get(artifact, [])
                       if s != step["slug"]]
            if named or by_text:
                continue
            out.append({
                "kind": KIND_ORPHAN_OUTPUT,
                "slug": step["slug"],
                "slugs": [step["slug"]],
                "artifact": artifact,
                "item": item,
                "grounds": [f"{step['slug']} declares the produced edge: {item}",
                            f"no step in this area declares a consumed edge "
                            f"normalizing to {artifact!r}",
                            "the item names no consumer step by cross-reference"],
            })

    for artifact in sorted(consumers):
        slugs = [s["slug"] for s in steps if s["slug"] in set(consumers[artifact])]
        if len(set(slugs)) < 2:
            continue
        out.append({
            "kind": KIND_SHARED_INPUT,
            "slug": slugs[0],
            "slugs": slugs,
            "artifact": artifact,
            "item": artifact,
            "grounds": [f"consumed edge normalizing to {artifact!r} declared by "
                        f"{len(slugs)} steps: " + ", ".join(slugs)],
        })
    return out


# --------------------------------------------------------------------------- #
# Verb 1's raw material — the pain inventory
# --------------------------------------------------------------------------- #

def pain_inventory(area) -> list[dict]:
    """Every pain-kind callout in one area, with the sources it names.

    Steps first (manifest order, document order within a step), then the area's
    taxonomy nodes IF the node type declares the pain kind — it need not, and a
    node fragment parsed for a callout kind its own declaration does not admit
    would be this module inventing vocabulary for a type it does not own.

    The pain's TEXT is carried verbatim, in the interviewee's framing. Nothing
    here summarises, rewrites or grades it: the capture layer's trustworthiness
    is the whole reason the pains are worth clustering, and the M39 review risk
    is assessment contaminating that record. `srcs` is the SRC ids named in the
    callout body — a pain with none is still inventoried (it is what was
    written), and the empty list is the grounds problem the analyst must see.
    Read-only."""
    area = Path(area)
    tdecl, steps = _area_steps(area)
    prefix = _pain_prefix(tdecl, area)

    out: list[dict] = []
    for step in steps:
        for callout in _callouts(step["entity"], prefix):
            blob = _callout_blob(callout)
            out.append({
                "id": str(callout.get("id") or ""),
                "slug": step["slug"],
                "heading": step["heading"],
                "home": step["slug"],
                "text": str(callout.get("text") or ""),
                "fields": dict(callout.get("fields") or {}),
                "srcs": sorted(set(SRC_ID_RE.findall(blob))),
            })

    ndecl = _node_type()
    if prefix in {c.prefix for c in ndecl.callouts}:
        for node in _nodes(area):
            entity = kernel.parse_entity(node["text"], ndecl, slug=node["slug"])
            for callout in _callouts(entity, prefix):
                blob = _callout_blob(callout)
                out.append({
                    "id": str(callout.get("id") or ""),
                    "slug": node["slug"],
                    "heading": node["title"],
                    "home": node["slug"],
                    "text": str(callout.get("text") or ""),
                    "fields": dict(callout.get("fields") or {}),
                    "srcs": sorted(set(SRC_ID_RE.findall(blob))),
                })
    return out


# --------------------------------------------------------------------------- #
# M49 Part B — the fourth verb: conflict records
# --------------------------------------------------------------------------- #

# The `Nature:` field read moved to scripts/kinds.py (M53), alias as above.
_nature = kinds.nature


def conflict_records(area) -> list[dict]:
    """Every gap-kind callout that is a CONFLICT ON ITS FACE, in document order.

    Two grammars, both read from what the drafter actually wrote:

      * v2 (the two-mint doctrine's conflict shape) — the callout body cites
        `CONFLICT_MIN_SRCS` or more DISTINCT SRC ids. Two readings, two
        citations: the drafter recorded a disagreement rather than an absence.
      * v1 — the callout carries a `Nature:` field whose value is `conflict`
        (the p2p corpus's grammar, where the nature of a gap was authored as a
        field rather than implied by its citations).

    A gap citing fewer than two sources and carrying no conflict nature is an
    ABSENCE, not a conflict, and is not a record. That line is the whole point
    of the verb: the resolution QUESTIONs these records feed ask a client to
    SETTLE something two sources say differently, which is a different ask from
    "we hold no source for this".

    `{"kind", "step", "id", "srcs", "text"}` per record, plus `"nature"` when
    the field was present. `id` is the DISPLAY id
    (`doc_model.callout_display_ids` — the document-global numbering authority,
    the map render.py and the derived views already share), so a record cites a
    gap by the id the rendered document shows. `text` is the callout's own words
    with `[[slug]]` tokens flattened; nothing here summarises or grades it.

    The gap kind comes from the information request's `step-gaps` binding, not
    from a typed label (`_gap_prefix`). Both unit shapes are served by the one
    walk: `_area_steps` parses each manifest-listed fragment against the step
    type declaration, whose callout vocabulary the activity type shares, so an
    activity-shaped area's gaps are read by the same pass as a process-step
    area's — no per-area type switch, and no second parser to disagree with.

    Deterministic (manifest order, then document order within a step) and
    READ-ONLY, like every other generator here. This verb RECORDS a conflict; it
    never resolves one (the M39 one-direction rule)."""
    import doc_model

    area = Path(area)
    tdecl, steps = _area_steps(area)
    prefix = _gap_prefix(tdecl, area)
    disp = doc_model.callout_display_ids(area)

    out: list[dict] = []
    for step in steps:
        for callout in _callouts(step["entity"], prefix):
            blob = _callout_blob(callout)
            srcs = sorted(set(SRC_ID_RE.findall(blob)))
            nature = _nature(callout)
            if len(srcs) < CONFLICT_MIN_SRCS and nature != NATURE_CONFLICT:
                continue
            local = str(callout.get("id") or "")
            record = {
                "kind": KIND_CONFLICT_RECORD,
                "step": step["slug"],
                "id": disp.get((step["slug"], local), local),
                "srcs": srcs,
                "text": _flatten(str(callout.get("text") or "")),
            }
            if nature is not None:
                record["nature"] = nature
            out.append(record)
    return out


# --------------------------------------------------------------------------- #
# M49 Part A — the analyst work order (`analysis.py brief <area>`)
# --------------------------------------------------------------------------- #

#: The feeds the brief prints, in order: (heading, generator). The brief is a
#: view over this module's own verbs — it computes nothing of its own.
def _feeds():
    return (
        ("CONTROL GAP CANDIDATES", control_gap_candidates),
        ("HANDOFF CANDIDATES", handoff_candidates),
        ("PAIN INVENTORY", pain_inventory),
        ("CONFLICT RECORDS", conflict_records),
    )


def _entry_line(feed: str, item: dict) -> str:
    """One compact line per candidate — enough to see the candidate, never
    enough to stand in for reading the corpus."""
    if feed == "CONTROL GAP CANDIDATES":
        return (f"{item['slug']} — {item['heading']}: "
                f"{len(item['produced'])} produced edge(s), no control callout"
                + ("  [control prose present]" if item["control_prose"] else ""))
    if feed == "HANDOFF CANDIDATES":
        return f"{item['kind']}: {item['artifact']}  ({', '.join(item['slugs'])})"
    if feed == "PAIN INVENTORY":
        srcs = ", ".join(item["srcs"]) or "NO SOURCE NAMED"
        return f"{item['id']} on {item['home']} ({srcs}): {item['text']}"
    nature = f", nature: {item['nature']}" if item.get("nature") else ""
    return (f"{item['id']} on {item['step']} "
            f"({', '.join(item['srcs']) or 'no SRC cited'}{nature}): "
            f"{item['text']}")


def _license_block(out: list[str], area: Path) -> None:
    out.append(f"WORK ORDER — consult-analyst · {area}")
    out.append("")
    out.append("YOUR LICENSE (assessment only — the M39 one-direction rule):")
    out.append("  * you ASSESS. The candidates below are mechanical: this "
               "module says what the corpus declares, never what matters. "
               "Materiality, clustering and severity are your judgment.")
    out.append("  * you PROPOSE findings and nothing else — "
               "`findings.propose(root, claim, grounds, theme)`. A proposed "
               "finding is a claim awaiting the human gate; accept/reject is "
               "the human's, and only accepted findings render.")
    out.append("  * you NEVER write an area file. Not a fragment, not a "
               "manifest, not a callout — findings never flow back into the "
               "capture layer.")
    out.append("  * you NEVER resolve a gap, settle a conflict or rephrase "
               "capture content. A conflict record is raw material for a "
               "resolution QUESTION; the client settles it, not you.")
    out.append("")


def _register_block(out: list[str], root: Path) -> None:
    import findings
    out.append(f"FINDINGS REGISTER — {findings.findings_path(root)} (the "
               "engagement-wide state; ids are stable and citable):")
    for status in findings.STATUSES:
        rows = findings.entries(root, status=status)
        ids = ", ".join(str(e.get("id")) for e in rows) or "—"
        out.append(f"  {status}: {len(rows)}  [{ids}]")


def analyst_brief(area: Path, root: Path) -> str:
    """The analyst's work order as one printable block. Read-only."""
    import brief
    import findings

    out: list[str] = []
    _license_block(out, area)

    for name, generator in _feeds():
        try:
            items = generator(area)
        except AnalysisError as exc:
            out.append(f"{name}: UNAVAILABLE — {exc}")
            out.append("  report this in your return; do not assess around a "
                       "feed that refused.")
            out.append("")
            continue
        out.append(f"{name} ({len(items)}):")
        if not items:
            out.append("  none")
        for item in items:
            out.append(f"  - {_entry_line(name, item)}")
        out.append("")

    _register_block(out, root)

    findings_here = findings.for_area(root, area)
    ids = ", ".join(str(e.get("id")) for e in findings_here) or "—"
    out.append(f"  grounded in THIS area ({len(findings_here)}): [{ids}] "
               f"— read these before proposing: a claim already on the "
               f"register is not a new finding.")
    out.append("")

    out.append(brief.objective_block(area).rstrip("\n"))
    out.append("")

    out.append("BEFORE YOU FINISH:")
    out.append("  1. Every finding you propose carries GROUNDS that resolve "
               "(SRC ids, callout ids, entity slugs) — a finding that does "
               "not trace does not exist, and `propose` refuses it by name.")
    out.append("  2. Say what you considered and set aside, and why — the "
               "candidates you judged immaterial are part of the trail.")
    out.append("  3. Return the proposed finding ids with a one-line claim "
               "each. Never paste corpus text back, and never render: the "
               "human accepts or rejects, and only accepted findings reach a "
               "deliverable.")
    return "\n".join(out)


def main(argv=None) -> int:
    """`analysis.py brief <area>` — the analyst dispatch's work order.

    Read-only by contract, like every verb in this module. Exit 0 on a printed
    brief; exit 2 on an unknown area or an area outside an engagement's
    `components/` tree (the findings register and the ledger live at the
    ENGAGEMENT root, so an area with no derivable root has no register to
    report and no grounds universe to resolve against — refused by name rather
    than briefed over)."""
    import sys

    ap = argparse.ArgumentParser(
        prog="analysis.py",
        description="The analyst's deterministic work order (read-only).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("brief", help="print the analyst work order for one area")
    b.add_argument("area", help="area folder, e.g. components/<area>")
    a = ap.parse_args(argv)

    area = Path(a.area)
    if not (area / "manifest.json").is_file():
        print(f"error: {area} has no manifest.json — pass the AREA FOLDER "
              f"path (e.g. components/<area>)", file=sys.stderr)
        return 2

    try:
        root = kinds.engagement_root(area)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        print(analyst_brief(area, root))
    except AnalysisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
