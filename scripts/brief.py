#!/usr/bin/env python3
"""brief.py — deterministic work order for a subagent's pass over one area.

Usage:
    python3 scripts/brief.py <area> --slug <procedure-slug>              # drafter
    python3 scripts/brief.py <area> --slug <slug> --mode update          # drafter, mode-scoped
    python3 scripts/brief.py <area> --kind raci|dependencies             # synthesis
    python3 scripts/brief.py <area> --objective                          # objective block
    python3 scripts/brief.py taxonomist <area-or-root> --kind SCOPING|CURATION|ADOPT-ROUTE
                                                                         # taxonomist (M52)

Why this exists (design note): the orchestrator's advisor works because
orchestration is a state machine; a drafting pass is one sitting of judgment
work, so it gets no advisor loop. But the PROCEDURAL half of a drafter's
contract — which files exist, which profile layer applies, which sources are
tagged to it, whether notes are queued — is mechanical, and every place an
agent re-derives it from prose is a place an input gets silently skipped.
This script resolves the inputs once, from the same loaders the enforcement
points use (client_config, sources, notes_util, doc_model), and prints a
reading list + finish checklist. It decides NOTHING about mode or content:
the dispatch prompt stays authoritative for the trigger; the fragment stays
the agent's judgment.

M31 (mode-scoped reading contract): `--mode` RELAYS the dispatch's trigger —
the brief still never decides it. With `--mode update` the reading list is
scoped to the delta: already-consumed sources and upstream seams become
CONDITIONAL reads, each line printing its mechanical condition, and the
drafter must disclose every skipped read in its return status. Without the
flag (or with `--mode first-draft`) the list is the full read-everything
set, unchanged.

Read-only by contract: this script never writes, so any agent may run it
without touching the one-writer rule.

Exit codes: 0 = brief printed (warnings inline); 2 = bad usage, unknown
area/slug/kind; 1 = area state invalid (e.g. malformed profile) — surface
that error to the orchestrator instead of drafting over it.
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

import argparse
import json
import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import client_config  # noqa: E402
import doc_model      # noqa: E402
import notes_util     # noqa: E402

# The `unfilled` sentinel grammar — borrowed from orchestrate (like reconcile
# does) so the fill predicate cannot drift.
try:
    from orchestrate import UNFILLED_RE
except ImportError:  # pragma: no cover - orchestrate ships beside us
    UNFILLED_RE = re.compile(
        r"(<!--\s*unfilled\s*-->)|(status\s*:\s*unfilled)", re.I)

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml ships in requirements
    yaml = None

# M34 central mode: the ONE detection seam (sources.central_root) plus the
# v1-SHAPED slice of the engagement ledger it points at. Borrowed the same
# defensive way as UNFILLED_RE above — if either is unavailable, `_sources_entries`
# runs exactly the v1 per-area read it ran before M34.
try:
    from sources import central_root as _central_root  # type: ignore
except Exception:  # pragma: no cover - sources.py ships beside us
    _central_root = None
try:
    from ledger import area_view as _area_view  # type: ignore
except Exception:  # pragma: no cover - ledger.py ships beside us
    _area_view = None

SYNTH_KINDS = {"raci": "84_raci.md", "dependencies": "82_dependencies.md"}
REGISTRY_FILES = ("systems.yaml", "roles.yaml", "sources.yaml",
                  "glossary.yaml")


def _fail(msg: str, code: int = 2) -> "SystemExit":
    print(f"error: {msg}", file=sys.stderr)
    return SystemExit(code)


def _load_area(area: str) -> tuple[Path, dict]:
    folder = Path(area)
    manifest = folder / "manifest.json"
    if not manifest.is_file():
        raise _fail(f"{folder} has no manifest.json — pass the AREA FOLDER "
                    f"path (e.g. components/<area>)")
    return folder, doc_model.load_manifest(folder)


def _procedures(manifest: dict) -> list[dict]:
    return [c for c in manifest.get("components", [])
            if c.get("role") == "procedure"]


def _sources_base(folder: Path) -> Path:
    """THE FOLDER a source entry's `file` value is relative to (M68).

    Centrally that is the ENGAGEMENT ROOT — `ledger.register` records
    `_sources/new/<name>`, measured from the root, not from the area. Joining
    it to the area folder named a path that never exists, so every tagged
    source in every brief printed `[MISSING — report it, do not guess]` and
    the mark stopped meaning anything. In v1 the entries are area-local and
    the base is the area, exactly as before.

    Asked separately from `_sources_entries` on purpose: that function's
    return shape is the loaders' contract and other readers pin it.
    """
    if _central_root is not None and _area_view is not None:
        root = _central_root(str(folder))
        if root:
            return Path(root)
    return Path(folder)


def _sources_entries(folder: Path) -> list[dict]:
    # M34: ask the ONE detection seam. In central mode the area owns no
    # `_reference/sources.yaml` — the engagement ledger does — and `area_view`
    # hands back the v1 entry shape (flat area-local touches/consumed + derived
    # state), so the reading-list block below needs no change. The entries'
    # `file` values are ROOT-relative there: pair every read with
    # `_sources_base(folder)` before resolving one (M68).
    if _central_root is not None and _area_view is not None:
        root = _central_root(str(folder))
        if root:
            return _area_view(root, Path(folder).name)
    folder = Path(folder)
    p = folder / "_reference" / "sources.yaml"
    if not p.is_file():
        return []
    # M67: the file EXISTS, so an empty list here would be a lie of the same
    # shape as the objective one — the reading list would silently drop every
    # tagged source. No parser, no answer.
    if yaml is None:
        raise client_config.MissingDependencyError(
            client_config._missing_yaml_message(p))
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    return [e for e in (data.get("sources") or []) if isinstance(e, dict)]


def _line(out: list[str], s: str = "") -> None:
    out.append(s)


def _reading_item(out: list[str], folder: Path, rel: str, note: str = "") -> None:
    p = folder / rel
    mark = "" if p.exists() else "  [MISSING — report it, do not guess]"
    note = f"  ({note})" if note else ""
    _line(out, f"  - {folder / rel}{note}{mark}")


def _profile_block(out: list[str], folder: Path) -> None:
    prof = client_config.profile(folder)
    _line(out, "DOCUMENT PROFILE (resolved — the correct layer already "
               "applied):")
    _line(out, f"  {prof.report_line()}")
    _line(out, f"  callout kinds in play: {', '.join(prof.callouts) or '—'}")
    _line(out, f"  inline step tags in play: "
               f"{', '.join(prof.inline_tags) or '—'}")
    if prof.body_omit:
        _line(out, f"  body_omit ({', '.join(prof.body_omit)}): draft these "
                   f"sections exactly as normal — only the rendered body "
                   f"hides them")
    _line(out)


def objective_block(area) -> str:
    """The engagement objective as one printable block (M41 Part C).

    Deterministic and READ-ONLY, like every other block here: the goal line,
    the in-scope cycles, and — the deliverable-aware half — per target
    deliverable the named gaps `definitions.serviceability` reports, so the
    taxonomy agents ask about what the ENGAGEMENT was hired to produce
    instead of asking generically whether evidence exists.

    The block ALWAYS renders. An unconfigured objective prints the accessor's
    own "none (no engagement objective configured)" line rather than nothing:
    a missing section reads as a bug, a "none" line reads as a choice.

    Guards, both because an initial survey legitimately pre-dates the area's
    manifest and because a block that crashes takes a whole dispatch with it:
    a definition that will not load, and a serviceability read that cannot
    find/parse the manifest, each report as a LINE under their deliverable.
    """
    folder = Path(area)
    obj = client_config.objective(folder)
    out: list[str] = []
    _line(out, "ENGAGEMENT OBJECTIVE (what this engagement is FOR — stated "
               "by the human, not inferred):")
    _line(out, f"  {obj.report_line()}")
    if not obj.configured:
        _line(out, "  no goal is stated, so nothing narrows attention: work "
                   "the area as you would today, and say in your return that "
                   "an objective would have aimed the pass")
        _line(out)
        return "\n".join(out)

    goal = obj.goal or ("(stated block, no goal sentence — treat the "
                        "cycles/deliverables below as the goal)")
    _line(out, f"  goal: {goal}")
    if obj.cycles:
        _line(out, f"  in-scope cycles: {', '.join(obj.cycles)}")
        _line(out, "  the skeleton is a PROPOSAL like any other: refine a "
                   "seeded node the client's business contradicts, and "
                   "propose removing what the engagement does not cover — "
                   "never force-fit the client to the shape")
    else:
        _line(out, "  in-scope cycles: none stated — no cycle is out of "
                   "scope by omission; ask before narrowing")

    if not obj.deliverables:
        _line(out, "  target deliverables: none stated — judge sufficiency "
                   "generically (is there evidence?) and say so")
        _line(out)
        return "\n".join(out)

    _line(out, "  target deliverables — what each still NEEDS from this area "
               "(serviceability, named per binding; `python3 scripts/needs.py "
               "<area>` renders the deeper needs view — coverage and recorded "
               "gaps too). A node serving an unserved binding is asked about "
               "FIRST, and an information request may cite the deliverable:")
    import definitions  # lazy: brief.py stays cheap for the drafter path
    for name in obj.deliverables:
        _line(out, f"    {name}:")
        try:
            defn = definitions.load_definition(name, folder)
        except Exception as exc:  # validated at config time — never fatal here
            _line(out, f"      - definition did not load ({exc}) — report "
                       f"this, do not guess what it needs")
            continue
        try:
            gaps = definitions.serviceability(defn, folder)
        except (OSError, ValueError) as exc:
            _line(out, f"      - area not yet scaffolded (no readable "
                       f"manifest): serviceability unavailable until the "
                       f"area is scaffolded ({exc})")
            continue
        if not gaps:
            _line(out, "      - fully serviceable")
            continue
        for gap in gaps:
            _line(out, f"      - {gap}")
    _line(out)
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# M52 — the one taxonomist work order
#
# THE ONE ASSEMBLY SITE for the taxonomist's picture of the engagement:
# `taxonomist_picture` composes objective + coverage + needs + grooming +
# write boundary, and BOTH entrypoints (`brief.py taxonomist` here, and
# `engagement.py brief`, which delegates) print these same words. The DISPATCH
# KIND selects emphasis, never content — every kind-dependent line the verb
# emits carries the uppercase token "KIND", so two kinds' briefs are provably
# the same engagement picture once those lines are dropped (the M52 gate's
# content pin). Read-only and deterministic, like every block in this file.

#: The dispatch kinds the taxonomist verb relays (M52). The caller sets one;
#: the brief never decides it — the drafter `--mode` precedent, verbatim.
TAXONOMIST_KINDS = ("SCOPING", "CURATION", "ADOPT-ROUTE")


def _taxonomist_targets(path: str) -> tuple[Path, Path]:
    """`(root, area)` for the taxonomist picture — `root` is what the hygiene
    feeder walks (a components/ dir, or a v1 engagement root), `area` is the
    folder the config layers and the needs view resolve through.

    Accepts an AREA folder (`components/<area>` — the dispatch's usual shape,
    manifest not required: a SCOPING pass legitimately pre-dates it) or an
    engagement/components ROOT (the area then resolves to the first area dir,
    engagement.py's `_objective_area` rule). Anything that is not a directory
    refuses by name via `_fail` — a brief about a folder that is not there
    would be a lie."""
    p = Path(path)
    if not p.is_dir():
        raise _fail(f"{p} is not a directory — pass the AREA folder "
                    f"(components/<area>) or the engagement root")
    if (p / "components").is_dir():
        comps = p / "components"
    elif p.name == "components":
        comps = p
    else:
        return p.parent, p
    area = next((d for d in sorted(comps.iterdir())
                 if d.is_dir() and not d.name.startswith(("_", "."))), None)
    if area is None:
        raise _fail(f"{comps} holds no area directories — nothing to brief")
    return comps, area


def _one_line(text: str, limit: int = 160) -> str:
    """One line, bounded — the compactness the summary sections promise."""
    s = " ".join(str(text or "").split())
    return s if len(s) <= limit else s[:limit - 1] + "…"


def _coverage_section(out: list[str], root: Path) -> None:
    """COVERAGE MAP summary — `coverage_map.coverage` over the node→step
    relation, the relation itself from `plan_views.node_steps` (imported,
    never re-derived: the charter's cache/derivation guardrail)."""
    _line(out, "COVERAGE MAP (coverage_map.coverage over the node→step "
               "relation — derived on demand, cached nowhere; you are handed "
               "it, you never re-derive it and never write a coverage file):")
    eng_root = root.parent if root.name == "components" else root
    try:
        import coverage_map
        import plan_views
        relation: dict[str, list[str]] = {}
        comps = eng_root / "components"
        areas = sorted(d for d in comps.iterdir()
                       if d.is_dir() and not d.name.startswith(("_", "."))) \
            if comps.is_dir() else []
        for d in areas:
            try:
                relation.update(plan_views.node_steps(d))
            except Exception:      # noqa: BLE001 - a pre-manifest area has
                pass               # no relation to contribute, not an error
        cov = coverage_map.coverage(eng_root, relation)
    except Exception as exc:                     # noqa: BLE001 - loud, not fatal
        _line(out, f"  UNREADABLE — {type(exc).__name__}: {exc}; report it, "
                   f"do not reconstruct coverage yourself")
        _line(out)
        return
    if not cov:
        _line(out, "  no taxonomy nodes yet — coverage starts when node "
                   "files exist under <area>/_taxonomy/")
        _line(out)
        return
    counts: dict[str, int] = {}
    for status in cov.values():
        counts[status] = counts.get(status, 0) + 1
    _line(out, "  " + ", ".join(f"{k}: {n}" for k, n in sorted(counts.items())))
    for slug in sorted(cov):
        steps = relation.get(slug) or []
        _line(out, f"  - {slug}: {cov[slug]}  ({len(steps)} step(s))")
    _line(out)


def _needs_section(out: list[str], area: Path) -> None:
    """ENGAGEMENT NEEDS summary — `needs.needs(area)` (M44's render), counts
    per feed plus bounded one-liners; the full view stays a render the agent
    runs itself."""
    _line(out, "ENGAGEMENT NEEDS (summary of `needs.needs` — the full "
               "engagement-needs render is `python3 scripts/needs.py "
               "<area>`; nothing here is ranked):")
    try:
        import needs as needs_mod
        items = needs_mod.needs(area)
    except Exception as exc:                     # noqa: BLE001 - loud, not fatal
        _line(out, f"  UNREADABLE — {type(exc).__name__}: {exc}; report it, "
                   f"do not guess what blocks the deliverables")
        _line(out)
        return
    if not items:
        _line(out, "  none — no objective-selected target reports a "
                   "blocking need")
        _line(out)
        return
    counts: dict[str, int] = {}
    for it in items:
        k = str(it.get("kind", "?"))
        counts[k] = counts.get(k, 0) + 1
    _line(out, "  " + ", ".join(f"{k}: {n}" for k, n in sorted(counts.items())))
    for it in items[:12]:
        _line(out, f"  - [{it.get('kind', '?')}] {it.get('deliverable', '?')}"
                   f" · {it.get('where', '?')}: {_one_line(it.get('need'))}")
    if len(items) > 12:
        _line(out, f"  … {len(items) - 12} more — run the needs render for "
                   f"the full list")
    _line(out)


def _grooming_section(out: list[str], root: Path) -> None:
    """CALLOUT HYGIENE (M43 Part E) — the grooming feed the curation kind
    reads: `scripts/hygiene.py` computes the candidates, this prints them.
    Candidates, never verdicts. Moved here from engagement.py at M52 so both
    entrypoints print the same feed; a refusing generator is named LOUD and
    does not take the brief with it (the M41 objective-section precedent)."""
    _line(out, "CALLOUT HYGIENE (mechanical candidates for your grooming "
               "judgment — candidates, never verdicts; you read the words "
               "and decide):")
    try:
        import hygiene
    except Exception as exc:                     # noqa: BLE001 - loud, not fatal
        _line(out, f"  UNREADABLE — the hygiene feeder did not import "
                   f"({type(exc).__name__}: {exc}); groom from the registers "
                   f"and say so in your status.")
        _line(out)
        return
    eng_root = root.parent if root.name == "components" else root
    if not (eng_root / "components").is_dir():
        _line(out, f"  UNREADABLE — {root} is not a components/ dir under an "
                   f"engagement root; the hygiene feeder is engagement-scoped "
                   f"and will not guess the walk.")
        _line(out)
        return
    total = 0
    for kind, gen in ((hygiene.KIND_DUPLICATE_GAPS,
                       hygiene.duplicate_gap_candidates),
                      (hygiene.KIND_GAP_ANSWERED,
                       hygiene.answered_gap_candidates),
                      (hygiene.KIND_CTRL_MISSING_FIELD,
                       hygiene.thin_ctrl_candidates)):
        try:
            cands = gen(eng_root)
        except hygiene.HygieneError as exc:
            _line(out, f"  {kind}: UNREADABLE — {exc}")
            continue
        except Exception as exc:                 # noqa: BLE001 - loud, not fatal
            _line(out, f"  {kind}: UNREADABLE — {type(exc).__name__}: {exc}")
            continue
        _line(out, f"  {kind}: {len(cands)}")
        total += len(cands)
        for c in cands:
            if kind == hygiene.KIND_DUPLICATE_GAPS:
                ids, areas_, slugs = c["ids"], c["areas"], c["slugs"]
                _line(out, f"    - {ids[0]} ({areas_[0]}/{slugs[0]}) ≈ "
                           f"{ids[1]} ({areas_[1]}/{slugs[1]})  "
                           f"overlap {c['similarity']}: "
                           f"{_one_line(c['texts'][0])} || "
                           f"{_one_line(c['texts'][1])}")
            elif kind == hygiene.KIND_GAP_ANSWERED:
                _line(out, f"    - {c['id']} ({c['area']}/{c['slug']}) ← "
                           f"{c['src']} ({c['src_file']}), tagged not consumed"
                           + (f"; note: {_one_line(c['note'])}"
                              if c['note'] else "")
                           + f"  gap: {_one_line(c['text'])}")
            else:
                _line(out, f"    - {c['id']} ({c['area']}/{c['slug']}) missing "
                           f"{', '.join(c['missing'])}: {_one_line(c['text'])}")
    if total == 0:
        _line(out, "  none — no duplicate-gap pairs, no gap a tagged-"
                   "unconsumed source may answer, no control missing a "
                   "declared field. Nothing to groom mechanically.")
    _line(out)


def taxonomist_picture(root, area=None) -> str:
    """The taxonomist's engagement picture (M52) — THE one assembly site.

    Kind-INDEPENDENT by construction: no line here mentions any dispatch
    kind, so the M52 content pin (drop the KIND lines, the remainder is
    byte-equal across kinds) holds trivially. `engagement.py brief` prints
    this same block, so the two entrypoints cannot drift."""
    root = Path(root)
    if area is None:
        area = next((d for d in sorted(root.iterdir())
                     if d.is_dir() and not d.name.startswith(("_", "."))),
                    None)
    out: list[str] = []
    if area is None:
        _line(out, "ENGAGEMENT OBJECTIVE: no area under this components/ dir "
                   "to resolve the config layers through — report it.")
        _line(out)
    else:
        try:
            _line(out, objective_block(area).rstrip("\n"))
        except client_config.ClientConfigError as exc:
            # LOUD, never fatal — the M41 WP-O3 precedent: a malformed
            # objective must not take the dispatch down.
            _line(out, f"ENGAGEMENT OBJECTIVE: UNREADABLE — {exc}")
            _line(out, "  fix the `objective:` block before trusting this "
                       "pass's scope judgments; do not guess the goal.")
        _line(out)
    _line(out, "SCOPE TRIGGER (M41): a LIVE taxonomy node outside the "
               "objective's cycles is a finding — propose removal or a scope "
               "amendment to the human in your status. Deletion stays "
               "proposed, never executed by you.")
    _line(out)
    _coverage_section(out, root)
    if area is not None:
        _needs_section(out, area)
    _grooming_section(out, root)
    _line(out, "WRITE BOUNDARY (M45 — said once, the same for every "
               "dispatch):")
    _line(out, "  - LIVE node refinement happens IN PLACE: you edit "
               "<area>/_taxonomy/<node>.md directly — you are its one writer")
    _line(out, "  - FRESH node sets stage under "
               "<area>/_reference/.proposed/_taxonomy/ for the human confirm "
               "gate (promoted by scaffold.py --promote-taxonomy, never by "
               "you)")
    _line(out, "  - never delete a live node: removal, merge or retirement "
               "is a proposal to the human, never your edit")
    _line(out, "  - everything outside your files is another writer's: "
               "propose through the notes bus (engagement.py note), never "
               "edit")
    return "\n".join(out)


def taxonomist_brief(path: str, kind: str) -> str:
    """The merged taxonomist work order: the engagement picture, framed by
    the DISPATCH KIND lines. Every kind-dependent line carries the token
    "KIND" — the M52 design rule the acceptance gate enforces."""
    root, area = _taxonomist_targets(path)
    out: list[str] = []
    _line(out, f"WORK ORDER — consult-taxonomist · {area}")
    _line(out, f"  YOUR DISPATCH KIND: {kind}  (relayed from your dispatch — "
               f"the KIND selects emphasis, never content)")
    _line(out)
    _line(out, taxonomist_picture(root, area))
    _line(out)
    _line(out, "DISPATCH KIND (one brief, three emphases — every line here "
               "carries KIND; the picture above is identical for all):")
    _line(out, "  KIND SCOPING — propose/refine the L3 node set, judge "
               "per-node sufficiency against the coverage map, return "
               "client-ready information requests for thin/empty/conflicted "
               "nodes")
    _line(out, "  KIND CURATION — groom the existing population "
               "(engagement-scoped, one area suffices): hygiene candidates, "
               "the needs view, one-fact-one-home placement; proposals ride "
               "the notes bus to the scope gate")
    _line(out, "  KIND ADOPT-ROUTE — judge intake routing and adoption "
               "against the structure: refine tags only; sources enter only "
               "through engagement.py route/adopt — you never mint an entry, "
               "never write a hash")
    _line(out, f"  THIS DISPATCH'S KIND: {kind}")
    return "\n".join(out)


def _drafter_register_block(out: list[str], parent: Path) -> None:
    """Engagement registers, listed BY CLASS (M30): citable entries carry the
    M24 reference-don't-restate rule; context entries are pre-read — facts
    the drafter aligns with but never cites by register name. Compact by
    design (ids + first line): the register file itself is the read."""
    import registers
    for path, title, entries in registers.load_all(parent):
        if entries is None:
            # Pre-M30 freeform seed file — the old whole-file rule still
            # applies until its content is migrated into entries.
            _line(out, f"  - {path}  (ENGAGEMENT REGISTER — reference, "
                       f"never restate: cite the register for shared "
                       f"values like thresholds, codes, terms and "
                       f"cutoff rules; hard-code only stable values "
                       f"essential to executing YOUR steps)")
            continue
        _line(out, f"  - {path}  (ENGAGEMENT REGISTER — {title}; entries "
                   f"by class below, ids are `{path.stem}#<entry-id>`)")
        cit = [e for e in entries if e.cls == "citable"]
        ctx = [e for e in entries if e.cls == "context"]
        if cit:
            _line(out, "      citable — reference, never restate: cite "
                       "the register for these shared values; hard-code "
                       "only stable values essential to executing YOUR "
                       "steps:")
            for e in cit:
                _line(out, f"        {path.stem}#{e.id}: "
                           f"{registers.first_line(e.text)}")
        if ctx:
            _line(out, "      context — facts already established: align; "
                       "cite the provenance source if you state one, GAP "
                       "if you can't; NEVER cite the register by name for "
                       "these:")
            for e in ctx:
                _line(out, f"        {path.stem}#{e.id}: "
                           f"{registers.first_line(e.text)}  "
                           f"(provenance: {e.provenance})")


def _sibling_areas(folder: Path) -> list[tuple[str, str]]:
    """(area-name, title) for every sibling area under the same components/
    parent — the drafter's cross-L1 boundary list."""
    out: list[tuple[str, str]] = []
    parent = folder.resolve().parent
    # Canonical engagement layout only (components/<area>) — an area parked
    # elsewhere has no siblings to scan.
    if parent.name != "components" or not parent.is_dir():
        return out
    for sib in sorted(parent.iterdir()):
        if not sib.is_dir() or sib.resolve() == folder.resolve() \
                or sib.name.startswith(("_", ".")):
            continue
        mpath = sib / "manifest.json"
        if not mpath.is_file():
            continue
        try:
            data = json.loads(mpath.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            out.append((sib.name, sib.name, []))
            continue
        procs = [(c.get("heading") or "").strip()
                 for c in data.get("components", [])
                 if c.get("role") == "procedure" and c.get("heading")]
        out.append((sib.name, data.get("title", sib.name), procs))
    return out


# The seam lives in these sections — upstream fragments are read for the
# handoff only, so these are the only upstream sections a drafter opens.
SEAM_SECTIONS = "Scope, At a Glance, Outputs & Evidence"


# --------------------------------------------------------------------------- #
# M43 Part B — the unit line
#
# WHICH DRAFTING PATH the drafter reads is not a new dispatch key and not a
# hand-typed flag: the definition layer already knows what an area is made of.
# The area's RESOLVED deliverable definition carries an entity-part binding (a
# binding that selects `parts` of an entity), and that binding NAMES its entity
# type — `process-step` (the M43 Part A path) or `activity` (the v1
# seven-section path). We read that name and print it. Nothing is decided here.
#
# Which definition is the area's is read the same mechanical way: the manifest's
# derived components carry `derived_kind` values, and a derived kind that names
# an installed deliverable is that deliverable (the IPO area's
# `process-controls-matrix`); an area whose derived kinds are all blocks of the
# default deliverable (every v1 area) resolves the default. Manifest order
# decides, so the read is deterministic.
#
# LOUD fallback, never a dead dispatch: `resolve_definition` raises on config
# problems (a broken user definition, an unreadable profile), and a broken
# definition must not stop a drafter from drafting. The line then states the
# default AND names the error — the drafter reports it instead of guessing.
#: The unit the v1 seven-section path drafts — the stated default.
DEFAULT_UNIT = "activity"


def _entity_part_unit(defn) -> str | None:
    """The entity type named by `defn`'s entity-part binding, or None when the
    definition binds no parts of any entity (a channels/callouts-only
    deliverable has no drafting unit to report)."""
    for spec in (defn.bindings or {}).values():
        if not isinstance(spec, dict) or not spec.get("parts"):
            continue
        ent = spec.get("entities")
        if isinstance(ent, str) and ent.strip():
            return ent.strip()
    return None


UNIT_PATHS = {
    "process-step": "agents/drafting/process-step.md",
    "activity": "agents/drafting/activity.md",
}


def _unit_path(unit: str) -> str:
    """The path document a drafter on `unit` reads — the v1 activity path is
    the fallback for any unit with no document of its own (M48)."""
    return UNIT_PATHS.get(unit, UNIT_PATHS[DEFAULT_UNIT])


def _unit_line(folder: Path, manifest: dict) -> str:
    """The `YOUR UNIT` line's text — one line, always."""
    try:
        import definitions
        names = []
        for comp in manifest.get("components", []):
            kind = comp.get("derived_kind")
            if isinstance(kind, str) and kind and kind not in names:
                names.append(kind)
        defn = None
        for name in names:
            try:
                defn = definitions.resolve_definition(folder, name)
                break
            except Exception:                   # not this area's deliverable
                defn = None
        if defn is None:
            defn = definitions.resolve_definition(folder)
        unit = _entity_part_unit(defn)
        if unit is None:
            return (f"YOUR UNIT: {DEFAULT_UNIT} (default — no definition "
                    f"resolved: {defn.name} binds no entity parts)"
                    f" — read {_unit_path(DEFAULT_UNIT)}")
        return (f"YOUR UNIT: {unit}  (deliverable definition: {defn.name})"
                f" — read {_unit_path(unit)} (that ONE path document, plus "
                f"the shared law in agents/consult-drafter.md)")
    except Exception as exc:                    # noqa: BLE001 - loud fallback
        return (f"YOUR UNIT: {DEFAULT_UNIT} (default — no definition "
                f"resolved: {type(exc).__name__}: {exc}) "
                f"[report this in your return — the definition layer is "
                f"broken, the drafting path below is the v1 default]"
                f" — read {_unit_path(DEFAULT_UNIT)}")


def drafter_brief(folder: Path, manifest: dict, slug: str,
                  mode: str | None = None) -> str:
    procs = _procedures(manifest)
    comp = next((c for c in procs if c.get("slug") == slug), None)
    if comp is None:
        known = ", ".join(sorted(c.get("slug", "?") for c in procs)) or "none"
        raise _fail(f"unknown procedure slug {slug!r} in {folder} "
                    f"(known: {known})")

    out: list[str] = []
    frag = comp.get("file", "")
    frag_path = folder / frag
    sentinel = bool(frag_path.is_file() and UNFILLED_RE.search(
        frag_path.read_text(encoding="utf-8")))
    _line(out, f"WORK ORDER — consult-drafter · {slug} · {folder}")
    _line(out, f"  your file (the ONLY file you write): {frag_path}")
    _line(out, f"  fragment state: "
               f"{'unfilled skeleton (first-draft expected)' if sentinel else 'drafted (update expected)'}"
               f" — your dispatch names the trigger; if it disagrees with "
               f"this state, say so in your return instead of guessing")
    if mode:
        mismatch = (mode == "update" and sentinel) or \
                   (mode == "first-draft" and not sentinel)
        _line(out, f"  mode (relayed from your dispatch): {mode}"
                   + ("  [MISMATCH vs fragment state above — report it, "
                      "do not guess]" if mismatch else ""))
    # M43 Part B: which drafting path your contract sends you to. It precedes
    # the reading list on purpose — it selects which instructions you read.
    _line(out, "  " + _unit_line(folder, manifest))
    _line(out)

    _profile_block(out, folder)

    update_mode = mode == "update"
    if update_mode:
        _line(out, "READING LIST (complete — nothing else is required "
                   "input; UPDATE MODE: lines marked CONDITIONAL are "
                   "skipped by default — read one only when its printed "
                   "condition holds, and disclose every skip in your "
                   "return status under `skipped_reads`):")
    else:
        _line(out, "READING LIST (complete — nothing else is required "
                   "input):")
    _reading_item(out, folder, frag, "your skeleton/draft")
    source_base = _sources_base(folder)
    tagged = [e for e in _sources_entries(folder)
              if slug in (e.get("touches") or [])]
    if tagged:
        for e in tagged:
            sid, f = e.get("id", "?"), e.get("file", "")
            done = slug in (e.get("consumed") or [])
            note = f"{sid}, tagged to you"
            if done and update_mode:
                note += ("; already consumed by you — CONDITIONAL: read "
                         "only if your dispatch names it or your delta "
                         f"touches a claim cited to {sid}")
            elif done:
                note += ("; already consumed by you — re-read only if your "
                         "dispatch names it")
            entry_note = str(e.get("note") or "").strip()
            if entry_note:
                # M24 adoption provenance / M25 intake pointers ride here.
                trimmed = entry_note if len(entry_note) <= 200 \
                    else entry_note[:197] + "…"
                note += f"; note: {trimmed}"
            _reading_item(out, source_base, f, note)
    else:
        _line(out, "  - (no sources tagged to this procedure in "
                   "sources.yaml — if your dispatch passes source paths, "
                   "read those)")
    for name in REGISTRY_FILES:
        if (folder / "_reference" / name).is_file():
            _reading_item(out, folder, f"_reference/{name}")
    conv = sorted((folder / "_reference" / "conventions").glob("*.md"))
    for c in conv:
        _reading_item(out, folder, str(c.relative_to(folder)),
                      "conventions digest — phrasing already decided")
    parent = folder.resolve().parent
    if parent.name == "components":
        _drafter_register_block(out, parent)
    ups = [u for u in (comp.get("upstream") or [])]
    siblings = doc_model.sibling_procedures(folder) if any(
        "/" in u for u in ups) else {}
    for u in ups:
        uarea, ulocal = doc_model.split_xref(u)
        if uarea is None:
            ucomp = next((c for c in procs if c.get("slug") == u), None)
            if ucomp:
                unote = (f"upstream seam ({u}) — READ-ONLY context; seam "
                         f"sections only: {SEAM_SECTIONS}")
                if update_mode:
                    unote += ("; CONDITIONAL: read only if your delta "
                              "changes your own seam sections (Scope, "
                              "Before You Start, Outputs & Evidence)")
                _reading_item(out, folder, ucomp.get("file", ""), unote)
            continue
        # M26 cross-area seam: the counterpart fragment is READ-ONLY seam
        # context — align artifact names, timing and state, and write the
        # handoff sentence with the [[area/slug]] token. Never document the
        # other area's work.
        sib = siblings.get(uarea)
        if sib is None:
            _line(out, f"  - CROSS-AREA upstream [[{u}]] — sibling area "
                       f"not visible (not under a components/ root?) — "
                       f"report this, do not guess")
            continue
        sfolder = sib["path"]
        ufile = None
        try:
            um = doc_model.load_manifest(sfolder)
            ucomp = next((c for c in um.get("components", [])
                          if c.get("role") == "procedure"
                          and c.get("slug") == ulocal), None)
            ufile = ucomp.get("file") if ucomp else None
        except doc_model.ManifestError:
            pass
        upath = (sfolder / ufile) if ufile else None
        drafted = bool(upath and upath.is_file()
                       and not UNFILLED_RE.search(
                           upath.read_text(encoding="utf-8")))
        if drafted:
            xnote = (f"  - {upath}  (CROSS-AREA upstream seam "
                     f"[[{u}]] — READ-ONLY: align artifact names, "
                     f"timing and state; write your handoff sentence "
                     f"with the [[{u}]] token; never document that "
                     f"area's work; seam sections only: {SEAM_SECTIONS}")
            if update_mode:
                xnote += ("; CONDITIONAL: read only if your delta "
                          "changes your own seam sections (Scope, "
                          "Before You Start, Outputs & Evidence)")
            _line(out, xnote + ")")
        else:
            _line(out, f"  - [[{u}]] — CROSS-AREA upstream: scoped, not "
                       f"yet drafted — seam context UNAVAILABLE; draft "
                       f"the handoff from your own sources, still use "
                       f"the [[{u}]] token (it is valid), and return "
                       f"seam_unverified for this seam")
    _line(out)

    _line(out, "OWNERSHIP MAP — work owned elsewhere is NEVER documented in "
               "your file, even when your sources describe it richly "
               "(sources are tagged to several procedures; each activity "
               "has ONE owner):")
    for c in procs:
        if c.get("slug") != slug:
            _line(out, f"  - [[{c.get('slug', '?')}]] — "
                       f"{c.get('heading', '')}  (sibling procedure: "
                       f"reference it with its [[slug]]; one linking "
                       f"sentence max)")
    if folder.resolve().parent.name != "components":
        _line(out, "  - (no sibling areas visible: this area is not under "
                   "a components/ engagement root, so cross-L1 boundaries "
                   "are UNAVAILABLE — mention this in your return)")
    else:
        for aname, atitle, aprocs in _sibling_areas(folder):
            _line(out, f"  - area {aname} — {atitle}  (another L1: OUT OF "
                       f"SCOPE — one handoff sentence naming the process, "
                       f"no steps; report the overlap in your status)")
            if aprocs:
                _line(out, f"    its procedures (each already documented "
                           f"there — never re-document, even a step of "
                           f"one): {'; '.join(aprocs)}")
    _line(out)

    items = notes_util.load_items(folder, slug)
    if items:
        kinds: dict[str, int] = {}
        for it in items:
            kinds[it.get("kind", "?")] = kinds.get(it.get("kind", "?"), 0) + 1
        counts = ", ".join(f"{k}: {n}" for k, n in sorted(kinds.items()))
        _line(out, f"NOTES QUEUED for you ({counts}) — "
                   f"{folder / '_review' / (slug + '.notes.yaml')}")
        _line(out, "  route each item on its kind: (see your contract)")
    else:
        _line(out, "NOTES QUEUED for you: none")
    _line(out)

    # The M41 objective block (M42 Part B4): appended as the LAST context
    # section, immediately before the finish checklist — the checklist is the
    # dispatch's exit instruction and stays the final words, while "what this
    # engagement is FOR" belongs with the inputs it aims (reading list, notes).
    # Purely additive: no existing section is reshaped or reordered.
    try:
        _line(out, objective_block(folder).rstrip("\n"))
    except client_config.ClientConfigError as exc:
        # The engagement.py precedent (M41 WP-O3): LOUD, never fatal — a
        # malformed objective must not take the drafter dispatch down.
        _line(out, f"ENGAGEMENT OBJECTIVE: UNREADABLE — {exc}")
        _line(out, "  fix the `objective:` block before trusting this "
                   "dispatch's scope judgments; do not guess the goal, and "
                   "say in your return that the objective was unreadable.")
    _line(out)

    _line(out, "BEFORE YOU FINISH:")
    _line(out, "  1. The final-mode read-through (your contract: reread as "
               "if every callout, tag and citation were deleted)")
    _line(out, f"  2. python3 <plugin>/scripts/reconcile.py {folder}   "
               f"(fix ERRORS attributed to YOUR file only)")
    _line(out, "  3. Return the compact status — never paste draft text")
    return "\n".join(out)


def synthesis_brief(folder: Path, manifest: dict, kind: str) -> str:
    fname = SYNTH_KINDS[kind]
    comp = next((c for c in manifest.get("components", [])
                 if c.get("derived_kind") == kind), None)
    out: list[str] = []
    target = folder / (comp.get("file") if comp else fname)
    first = not target.is_file()
    _line(out, f"WORK ORDER — consult-{kind} · {folder}")
    _line(out, f"  your file (the ONLY file you write): {target}")
    _line(out, f"  pass type: "
               f"{'first derivation (Write the whole file)' if first else 'incremental (Edit changed rows in place; carry everything else verbatim)'}")
    if not first:
        _line(out, "  changed procedures come from your dispatch "
                   "(changed_procedure_slugs) — re-derive exactly those rows")
    _line(out)
    _profile_block(out, folder)
    _line(out, "READING LIST (complete — nothing else is required input; "
               "your contract: you do NOT open procedure files — the "
               "extract bundle is your evidence):")
    if not first:
        _reading_item(out, folder, str(target.relative_to(folder)),
                      "your prior file — the carry-over baseline")
    bundle = f"{manifest.get('area', folder.name)}.extract.json"
    _reading_item(out, folder, bundle,
                  ("raci_inputs" if kind == "raci" else "raw_dependencies")
                  + " — your evidence, tagged by slug")
    _reading_item(out, folder, "manifest.json",
                  "valid [[slug]] set for your references")
    if kind == "raci" and (folder / "_reference" / "roles.yaml").is_file():
        _reading_item(out, folder, "_reference/roles.yaml",
                      "canonical role names")
    if kind == "raci":
        for cand in ("_client/org-chart.yaml", "../_client/org-chart.yaml"):
            if (folder / cand).is_file():
                _reading_item(out, folder, cand,
                              "person→title grounding (optional input)")
                break
    _line(out)
    _line(out, "BEFORE YOU FINISH:")
    _line(out, f"  1. python3 <plugin>/scripts/reconcile.py {folder}   "
               f"(fix ERRORS attributed to YOUR file only)")
    _line(out, "  2. Return the compact status — never paste the table back")
    return "\n".join(out)


def _taxonomist_main(argv: list[str]) -> int:
    """The `taxonomist` verb (M52): parse, print the merged work order."""
    ap = argparse.ArgumentParser(
        prog="brief.py taxonomist",
        description="The merged taxonomist work order (M52) — read-only.")
    ap.add_argument("area", help="area folder (components/<area>) or the "
                                 "engagement root")
    ap.add_argument("--kind", required=True, choices=TAXONOMIST_KINDS,
                    help="the dispatch kind — relayed, never decided here; "
                         "selects emphasis, never content")
    a = ap.parse_args(argv)
    print(taxonomist_brief(a.area, a.kind))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "taxonomist":
        # M52: the one subcommand this CLI grew. Dispatched before the flat
        # parser because `--kind` means a synthesis kind there — the two
        # grammars must not blur.
        return _taxonomist_main(argv[1:])
    ap = argparse.ArgumentParser(
        description="Deterministic work order for a subagent pass "
                    "(read-only).")
    ap.add_argument("area", help="area folder, e.g. components/<area>")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slug", help="procedure slug (drafter brief)")
    g.add_argument("--kind", choices=sorted(SYNTH_KINDS),
                   help="derived kind (synthesis brief)")
    g.add_argument("--objective", action="store_true",
                   help="print the engagement objective block alone (M41) — "
                        "what the taxonomy dispatches carry; needs no "
                        "manifest, so an initial survey can run it")
    ap.add_argument("--mode", choices=("first-draft", "update"),
                    help="relay the dispatch's trigger (drafter briefs "
                         "only); `update` scopes the reading list to the "
                         "delta — the brief never decides the mode itself")
    a = ap.parse_args(argv)

    if a.mode and not a.slug:
        raise _fail("--mode applies to drafter briefs only (--slug)")

    if a.objective:
        # No _load_area: the objective block is the one brief a pre-manifest
        # area can still print (an initial survey pre-dates the manifest).
        try:
            print(objective_block(a.area))
        except client_config.ClientConfigError as e:
            print(f"ERROR: {e}\nfix the objective block before dispatching "
                  f"over it", file=sys.stderr)
            return 1
        return 0

    folder, manifest = _load_area(a.area)
    try:
        if a.slug:
            print(drafter_brief(folder, manifest, a.slug, mode=a.mode))
        else:
            print(synthesis_brief(folder, manifest, a.kind))
    except client_config.ClientConfigError as e:
        print(f"ERROR: {e}\nfix the client config before drafting over it",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
