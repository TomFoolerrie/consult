#!/usr/bin/env python3
"""
needs.py — M44's needs view (docs/v2/M44-needs-view.md Part B): a
PER-DELIVERABLE gap render over the brain, in the hygiene.py idiom
(engagement-scoped reads, deterministic, read-only, candidates-not-verdicts).

WHY A RENDER AND NOT A DRAFTER'S JOB (the ruling this module encodes): the gap
machinery was noisy because every gap was voiced at capture time, ranked by
whoever happened to be drafting, and blind to what the engagement was actually
hired to produce. "The shape of what we need changes on deliverables" — so the
inventory of need is COMPUTED from the objective (M41) plus the definitions,
never authored. An engagement that starts as audit readiness and later sells a
second service re-renders its needs by editing one `objective.yaml`; nothing in
the capture layer moves. That is the whole point, and it is why this module
writes nothing and caches nothing.

WHAT ONE NEED IS. A dict with five keys, always all five present, plus one
optional sixth key (`nature`) on the recorded-gap feed:

  deliverable  the definition name this need BLOCKS (every need names it —
               a need with no target is exactly the noise being deleted)
  kind         one of the three feeds below
  need         one sentence, the thing that is missing
  where        the binding name, the taxonomy node slug, or the step slug
  grounds      a non-empty list of MECHANICAL basis lines (binding name,
               coverage status, callout display id, SRC ids) — the reader
               judges from the grounds, this module never ranks

and, ONLY on a `recorded-gap` entry whose fragment states which of the two
mints it is (M50 Part B):

  nature       the gap callout's declared `Nature:` value — the two-mint
               discrimination, read from the fragment and validated against
               the enum the TYPE DECLARATION carries (never typed here). The
               one optional key: absent when the fragment states nothing, and
               absent when it states something the declaration does not admit.
               Absent is absent, never guessed — a consumer that finds no
               `nature` treats the need as undiscriminated.

THE THREE FEEDS, and why they are three and not one:

  binding-unserved  `definitions.serviceability_records(defn, area)`, one
                    entry per gap record, ONE loader pass per definition —
                    attribution arrives as data on the record's `binding` key
                    (M51), so nothing here re-parses a sentence or re-loads a
                    definition per binding. The structural floor: nothing here
                    is new judgment, it is the M35 report already shipped,
                    attributed to a deliverable.
  coverage          only for a target whose definition carries a `coverage:`
                    binding. Every taxonomy node the coverage map reports at
                    one of that binding's selected statuses. SKIPPED ENTIRELY
                    for a deliverable with no coverage binding — the shape of
                    need follows the deliverable, which is the ruling.
  recorded-gap      every gap-kind callout on the area's entity fragments,
                    attributed to each target whose bindings bind that entity
                    type. These are M44 Part A's two mints (a conflict, or an
                    evidenced absence) surfacing: a recorded fact about the
                    evidence blocks any deliverable that renders the entity
                    carrying it.

VOCABULARY COMES FROM THE BINDINGS AND THE DECLARATIONS (the M36 shape-audit
rule). This module types no coverage status word, no callout label and no
callout prefix. The gap kind is resolved through `kinds.gap_prefix`, which
reads the information-request definition's callout binding and translates it
into the prefix the fragments carry through the type declaration; the coverage
statuses are whatever the `coverage:` binding names; the entity type is
`analysis.STEP_TYPE`, the constant the modules that own the step population
already publish. The surveyor's `thin` alias expands in exactly one place in
the codebase — `kinds.selected_statuses` — and this module calls it rather
than collapsing the alias a second time.

MACHINERY IS IMPORTED, NEVER RE-DERIVED. `plan_views.node_steps` (the node→step
relation, itself matrix_views' grouping), `kinds.selected_statuses`,
`kinds.engagement_root`, `coverage_map.coverage`, `matrix_views._nodes` /`_ids`,
`kinds.area_steps` / `callouts` / `callout_blob`,
`doc_model.callout_display_ids`. A need must never be able to disagree with the
document that would have rendered it.

LAZY IMPORTS INSIDE FUNCTIONS: aggregate.py registers this module's builder at
import time and kernel.py imports aggregate, so a module-level import of
kernel/definitions/coverage_map/doc_model would close an import cycle — the
note plan_views.py and matrix_views.py both carry, applying here verbatim.

DETERMINISM AND ORDER. Targets in the order the objective (or the caller)
named them; within a target, the three feeds in the fixed order above; within a
feed, document order (declaration order for bindings, node order for coverage,
manifest-then-document order for callouts). Two calls are byte-equal. Nothing
is written — pinned by a whole-engagement fingerprint in
tests/test_needs_m44.py.

REFUSALS. An unknown deliverable name raises (definitions.DefinitionError,
which names it) — a report about a document nobody installed would be a lie.
A BROKEN area also raises, by name, before any feed runs (M51 Part C): an
area path outside any engagement's components/ tree, or an area whose
manifest.json exists but cannot be parsed as JSON — a "no needs" render of
either would be a lie the taxonomist and the agenda now act on. Everything
else that is merely NOT YET — no objective, no nodes, no steps, no gaps, a
real-but-thin area — returns `[]` or a "nothing outstanding" line, never an
exception: thin is not a defect, broken is.

Python 3, stdlib + the engine's own modules.
"""

from __future__ import annotations

# M67 interpreter floor: this block runs BEFORE any first-party import, because
# a < 3.10 interpreter dies inside `callouts.py` at import time and a check
# placed after those imports could never fire.
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _pyfloor  # noqa: E402  (3.9-importable by contract)

_pyfloor.require()

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import re
import sys

from pathlib import Path

# kernel / definitions / client_config / coverage_map / doc_model / analysis /
# hygiene / matrix_views / plan_views are imported LAZILY inside the functions —
# see the docstring's import-cycle note.

#: The derived kind / view-block id / `PY_BUILDERS` key. One string, three roles
#: (D1's convention, as in plan_views).
NEEDS_KIND = "engagement-needs"

#: The three feed names, in RENDER ORDER. Named constants so a caller can filter
#: without typing a string that only ever appeared in a dict literal (hygiene's
#: rule), and so the order is stated once.
KIND_UNSERVED = "binding-unserved"
KIND_COVERAGE = "coverage"
KIND_RECORDED = "recorded-gap"
#: M75's fourth feed: the CURATED asks — the outstanding client requests the
#: engagement has accepted. It leads the render because it is the only feed a
#: human has already curated: the three below it are mechanical populations,
#: this one is the question actually being asked. CONDITIONAL on the engagement
#: having an ask register at all — no register, no entries, and every pre-M75
#: area's needs view is byte-identical to what it was.
KIND_ASK = "open-ask"
KIND_ORDER = (KIND_ASK, KIND_UNSERVED, KIND_COVERAGE, KIND_RECORDED)

#: The binding key that marks a coverage selection. Not a status word — the KEY
#: definitions.py's stage-2 admits for the derived coverage selection, the same
#: key `definitions.serviceability` switches on.
COVERAGE_KEY = "coverage"

#: The binding key that marks an ask-register selection (M75) — the same
#: relationship to `_asks` that COVERAGE_KEY has to `_coverage`.
ASKS_KEY = "asks"

#: An SRC id as it appears in a callout body (coverage_map's grammar, mirrored
#: as plan_views mirrors it — grounds cite sources, they do not join on them).
_SRC_ID_RE = re.compile(r"\bSRC-[A-Za-z0-9]+\b")


# --------------------------------------------------------------------------- #
# Target selection
# --------------------------------------------------------------------------- #

def targets(area, deliverable=None) -> list[str]:
    """The definition names this render is about.

    An explicit `deliverable` wins outright — it is how the surveyor asks "what
    would block THIS document", with or without an objective on file. Otherwise
    the objective's `deliverables:` list selects, and an engagement with no
    objective configured selects nothing (`[]` — the CLI prints the accessor's
    own report line, which is a report and not a crash)."""
    import client_config
    if deliverable is not None:
        return [str(deliverable)]
    return list(client_config.objective(Path(area)).deliverables)


def _area_name(area: Path) -> str:
    """The area's folder name for a grounds line, robust to `.` on the CLI (a
    relative path's `.name` is empty, which would print a bare slash)."""
    return Path(area).resolve().name or str(area)


def _definition(name: str, area: Path):
    """The installed definition, user file shadowing shipped.

    `definitions.load_definition` already refuses an uninstalled name and NAMES
    it in the message, so there is no name check here to drift out of step with
    the loader's."""
    import definitions
    return definitions.load_definition(name, area=area)


# --------------------------------------------------------------------------- #
# Feed 1 — binding-unserved (the structural floor)
# --------------------------------------------------------------------------- #

def _unserved(defn, area: Path) -> list[dict]:
    """M35's serviceability report, read as records in one pass (M51).

    `definitions.serviceability_records` carries the binding name as data on
    each record, so `where` is attribution the report itself states — no
    per-binding single-binding copy of the definition, no re-parsing a gap
    sentence, one loader pass per definition. The sentences are the same
    strings the flat report renders (the records are where they are
    formatted), in the same declaration-grouped order — the entries here are
    byte-identical to what the per-binding loop produced."""
    import definitions
    out: list[dict] = []
    for rec in definitions.serviceability_records(defn, area):
        bname, gap = rec["binding"], rec["gap"]
        out.append({
            "deliverable": defn.name,
            "kind": KIND_UNSERVED,
            "need": gap,
            "where": bname,
            "grounds": [gap,
                        f'binding "{bname}" of deliverable '
                        f'"{defn.name}" cannot be served by area '
                        f"{_area_name(area)} as it stands"],
        })
    return out


# --------------------------------------------------------------------------- #
# Feed 2 — coverage (only where a coverage binding asks for it)
# --------------------------------------------------------------------------- #

def _asks_bindings(defn) -> list[tuple[str, dict]]:
    """The definition's ask-register selections, declaration order.

    `_coverage_bindings`' twin, and the reason it exists: that function
    switches on ONE key and every other binding verb falls through it
    SILENTLY, so a new verb produces no needs feed until this module learns
    it. M75's `asks:` is learned here — the register would otherwise be
    invisible to the needs view, the agenda and every consumer downstream of
    them."""
    return [(bname, spec) for bname, spec in (defn.bindings or {}).items()
            if ASKS_KEY in spec]


def _asks(defn, area: Path) -> list[dict]:
    """One entry per RENDERABLE ask (M75) — the curated client request.

    Reached through `asks.renderable()`, the same seam the rendered document
    binds, so the needs view and the request list can never disagree about
    which asks are live. `where` is the ASK id (the address a need has),
    `need` is the client-voiced text verbatim — this module never rewrites an
    ask, exactly as it never rewrites a callout — and the grounds carry the
    binding, the audience/artifact grouping and the gap ids the ask would
    settle, which is the mechanical basis for it being on the page.

    Empty (never an error) for a deliverable that binds no asks, an area
    outside an engagement tree, or an engagement with no register: this feed
    is conditional on the register existing, which is what keeps every
    pre-M75 render byte-identical."""
    specs = _asks_bindings(defn)
    if not specs:
        return []
    import asks as _asks_mod
    import kinds
    try:
        root = kinds.engagement_root(area)
    except ValueError:
        return []
    if not _asks_mod.asks_path(root).is_file():
        return []
    try:
        entries = _asks_mod.renderable(root)
    except Exception:
        # An unreadable register is reconcile's business to name, not a
        # reason for the needs view to refuse to render.
        return []

    out: list[dict] = []
    for bname, _spec in specs:
        for entry in entries:
            gaps = [str(g) for g in (entry.get("gaps") or [])]
            grounds = [f'binding "{bname}" of deliverable "{defn.name}" '
                       f"selects accepted asks",
                       f"{entry.get('id')}: {entry.get('audience')} — "
                       f"{entry.get('artifact')}"]
            if gaps:
                grounds.append("would settle: " + ", ".join(gaps))
            out.append({
                "deliverable": defn.name,
                "kind": KIND_ASK,
                "need": str(entry.get("text") or "").strip(),
                "where": str(entry.get("id") or ""),
                "grounds": grounds,
            })
    return out


def _coverage_bindings(defn) -> list[tuple[str, dict]]:
    """The definition's coverage selections, declaration order. Empty for a
    deliverable that binds no coverage at all — and an empty list here is the
    whole reason such a deliverable gets no coverage entries."""
    return [(bname, spec) for bname, spec in (defn.bindings or {}).items()
            if COVERAGE_KEY in spec]


def _coverage(defn, area: Path) -> list[dict]:
    """One entry per taxonomy node the map reports at a selected status.

    Every status word in an entry arrived from the coverage map, which was
    filtered by the statuses the BINDING named; `kinds.selected_statuses`
    performs the one documented `thin` expansion, here as in the request list,
    so this module and the rendered document can never select different nodes.
    Coverage is computed ON DEMAND over the whole engagement (nothing is
    persisted for it to read — the charter's guardrail)."""
    specs = _coverage_bindings(defn)
    if not specs:
        return []

    import coverage_map
    import kinds
    import plan_views
    from matrix_views import _nodes

    try:
        root = kinds.engagement_root(area)
    except ValueError:
        # An area outside an engagement tree has no coverage to report; a needs
        # render of it is thin, not broken.
        return []
    relation = plan_views.node_steps(area)
    cov = coverage_map.coverage(root, relation)
    nodes = _nodes(area)

    out: list[dict] = []
    for bname, spec in specs:
        wanted = kinds.selected_statuses(spec)
        for node in nodes:
            slug, title = node["slug"], node["title"]
            status = cov.get(slug)
            if status not in wanted:
                continue
            held = plan_views._node_evidence(area, slug, relation.get(slug) or [])
            grounds = [f'binding "{bname}" of deliverable "{defn.name}" '
                       f"selects {status}",
                       f"taxonomy node {slug} ({title}) in area {_area_name(area)}"]
            grounds.append(
                f"evidence already held on it: {', '.join(held)}" if held
                else "no source is cited on the node or the steps it covers")
            out.append({
                "deliverable": defn.name,
                "kind": KIND_COVERAGE,
                "need": f"{title} is not yet evidenced well enough for "
                        f"{defn.name}: the coverage map reports it at "
                        f"{status}.",
                "where": slug,
                "grounds": grounds,
            })
    return out


# --------------------------------------------------------------------------- #
# Feed 3 — recorded-gap (the two mints surfacing)
# --------------------------------------------------------------------------- #

def _binds_type(defn, type_name: str) -> bool:
    """Does any of this definition's bindings bind that entity population?

    The attribution rule for a recorded gap: a fact recorded about an entity
    blocks every deliverable that RENDERS that entity, and a definition renders
    what its bindings bind."""
    for spec in (defn.bindings or {}).values():
        named = spec.get("entities")
        if isinstance(named, str) and named.strip() == type_name:
            return True
    return False


def _declared_natures(tdecl, prefix: str) -> dict[str, str]:
    """The gap callout's declared `Nature:` vocabulary: {lowered -> declared}.

    Read off the `CalloutDecl.field_enums` the type declaration carries (M50
    Part A), keyed by the field name `kinds.NATURE_FIELD` names and matched
    case-insensitively on both the key and the values — this module types
    neither the field name nor any of its values. Delegates to
    `kinds.declared_natures`, the shared resolver's M53 home."""
    import kinds
    return kinds.declared_natures(tdecl, prefix)


def _recorded(defn, area: Path) -> list[dict]:
    """Every gap-kind callout on the area's entity fragments.

    The kind is resolved, never typed: `kinds.gap_prefix` reads the
    definition binding that names it and translates label→prefix through the
    type declaration. Display ids come from `doc_model.callout_display_ids` —
    the document-global numbering authority render.py itself uses, so a need
    cites the id the reader will see in the document rather than the drafter's
    local one. Manifest order, then document order within a step.

    An entry gains the optional `nature` key when the callout states a
    `Nature:` value the DECLARATION admits (`_declared_natures` below). The
    vocabulary is never typed here — same rule as the callout prefix."""
    import analysis
    if not _binds_type(defn, analysis.STEP_TYPE):
        return []

    import doc_model
    import kinds
    from matrix_views import _ids

    try:
        tdecl, steps = kinds.area_steps(area)
    except Exception:
        # No manifest, or an area whose fragments this type cannot be read
        # over: nothing recorded to surface, which is a thin area, not a defect.
        return []
    if not steps:
        return []
    try:
        prefix = kinds.gap_prefix(tdecl, area)
    except kinds.KindsError:
        # The binding does not resolve to exactly one gap kind — this feed will
        # not fall back on a typed label, so it stays silent (the refusal is
        # the resolver's to raise where it is the question being asked).
        return []

    disp = doc_model.callout_display_ids(area)
    natures = _declared_natures(tdecl, prefix)
    out: list[dict] = []
    for step in steps:
        mine = kinds.callouts(step["entity"], prefix)
        for callout, shown in zip(mine, _ids(step, prefix, disp)):
            text = " ".join(kinds.callout_blob(callout).split())
            srcs: list[str] = []
            for sid in _SRC_ID_RE.findall(text):
                if sid not in srcs:
                    srcs.append(sid)
            grounds = [f"{shown} recorded on {_area_name(area)}/{step['slug']} "
                       f"({step['heading']}): {text}",
                       f"deliverable \"{defn.name}\" binds the "
                       f"{analysis.STEP_TYPE} population that carries it"]
            if srcs:
                grounds.append(f"sources cited in it: {', '.join(srcs)}")
            entry = {
                "deliverable": defn.name,
                "kind": KIND_RECORDED,
                "need": f"{shown} on {step['heading']} is recorded against the "
                        f"evidence and still open: {text}",
                "where": step["slug"],
                "grounds": grounds,
            }
            stated = kinds.nature(callout)
            if stated is not None and stated in natures:
                entry["nature"] = natures[stated]
            out.append(entry)
    return out


# --------------------------------------------------------------------------- #
# The view
# --------------------------------------------------------------------------- #

def _preflight(area: Path) -> None:
    """The broken-area refusal (M51 Part C), before any feed runs.

    Two defects refuse BY NAME rather than rendering "no needs": an area path
    that resolves to no engagement root (`kinds.engagement_root`, the same
    refusal the other views use, which names the area), and a manifest.json
    that EXISTS but cannot be parsed as JSON (named too — area and manifest
    both). A merely THIN area — real root, readable manifest, nothing
    captured yet — passes untouched and renders its honest near-empty report:
    thin is not a defect, broken is. Nothing feed-internal changes; this is
    one gate at the door."""
    import json
    import kinds
    kinds.engagement_root(area)        # raises ValueError, naming the area
    manifest = area / "manifest.json"
    if manifest.is_file():
        try:
            json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"{area.name}: manifest.json exists but cannot be parsed as "
                f"JSON ({exc}) — this area is broken, not thin; fix the "
                f"manifest before asking what it needs") from exc


def needs(area, deliverable=None) -> list[dict]:
    """The needs view for one engagement area: what blocks each target.

    Order: targets as named, then the four feeds in `KIND_ORDER`, then
    document order inside each feed — built in that order rather than sorted
    afterwards, so the order is the walk and cannot drift from it. Read-only,
    cache-free, byte-equal on a repeat call.

    Raises for an unknown deliverable name (the loader's own refusal, which
    names it) and for a BROKEN area (the preflight below, which names it too).
    No objective and no name → `[]`."""
    area = Path(area)
    _preflight(area)
    out: list[dict] = []
    for name in targets(area, deliverable):
        defn = _definition(name, area)
        out.extend(_asks(defn, area))
        out.extend(_unserved(defn, area))
        out.extend(_coverage(defn, area))
        out.extend(_recorded(defn, area))
    return out


LEAD_IN = ("_Every item below names a deliverable it blocks, what is missing, "
           "and the mechanical grounds for saying so. Nothing here is ranked: "
           "which need to chase first is a judgment this render does not "
           "make._")


def render(area, deliverable=None) -> str:
    """The needs view as markdown, grouped per deliverable then per feed.

    aggregate's derived-view idiom: an italic lead-in line, then list content,
    `—` for an empty view. An area whose targets are fully served renders the
    dash and says so in words — an empty render must read as an answer, never
    as a failed build."""
    area = Path(area)
    entries = needs(area, deliverable)
    lines = [LEAD_IN, ""]
    if not entries:
        lines += ["—", "",
                  "_No need is outstanding for the selected deliverable(s) in "
                  "this area._"]
        return "\n".join(lines)

    order = {kind: i for i, kind in enumerate(KIND_ORDER)}
    seen: list[str] = []
    for entry in entries:
        if entry["deliverable"] not in seen:
            seen.append(entry["deliverable"])
    for name in seen:
        lines += [f"### {name}", ""]
        mine = [e for e in entries if e["deliverable"] == name]
        for kind in sorted({e["kind"] for e in mine}, key=lambda k: order[k]):
            lines += [f"**{kind}**", ""]
            for entry in [e for e in mine if e["kind"] == kind]:
                lines.append(f"- ({entry['where']}) {entry['need']}")
                for ground in entry["grounds"]:
                    lines.append(f"    - _{ground}_")
            lines.append("")
    return "\n".join(lines).rstrip()


def build_engagement_needs(ctx) -> str:
    """`engagement-needs` — the derived-view builder, over `ctx["area"]`.

    Registered through `aggregate.PY_BUILDERS` (one import + one entry, the
    plan_views/matrix_views pattern); no shipped definition binds it yet, and
    the future one (the interview agenda) will bind it by this name alone. The
    targets are the objective's, because a view of "what we still need" that
    ignored what the engagement was hired for is the noise M44 deletes.
    Read-only."""
    area = (ctx or {}).get("area")
    if not area:
        raise KeyError(
            f"{NEEDS_KIND}: the builder ctx carries no 'area' — this view is "
            f"built over an engagement area (see needs.py)")
    return render(Path(area))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

USAGE = "usage: needs.py <area> [--deliverable NAME]"


def main(argv=None) -> int:
    """Print the needs view for one area. 0 on a printed report (including the
    empty one and the unconfigured-objective line), 2 on bad usage, an area
    that is not a directory, or a deliverable nobody installed."""
    argv = list(sys.argv[1:] if argv is None else argv)
    area = None
    deliverable = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--deliverable":
            if i + 1 >= len(argv):
                print(f"needs.py: --deliverable needs a name\n{USAGE}",
                      file=sys.stderr)
                return 2
            deliverable = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--"):
            print(f"needs.py: unknown option {arg}\n{USAGE}", file=sys.stderr)
            return 2
        if area is not None:
            print(f"needs.py: unexpected argument {arg}\n{USAGE}",
                  file=sys.stderr)
            return 2
        area = arg
        i += 1

    if area is None:
        print(USAGE, file=sys.stderr)
        return 2
    path = Path(area)
    if not path.is_dir():
        print(f"needs.py: {area} is not a directory", file=sys.stderr)
        return 2

    import client_config
    if deliverable is None:
        try:
            objective = client_config.objective(path)
        except client_config.ObjectiveError as exc:
            print(f"needs.py: {exc}", file=sys.stderr)
            return 2
        # The accessor owns the wording of its own absence (M41): an
        # unconfigured objective prints ITS line, not a second phrasing of it.
        print(objective.report_line())
        if not objective.configured:
            return 0

    try:
        print(render(path, deliverable))
    except Exception as exc:            # loader-grade refusals, named
        print(f"needs.py: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":            # pragma: no cover
    raise SystemExit(main())
