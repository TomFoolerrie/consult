#!/usr/bin/env python3
"""brief.py — deterministic work order for a subagent's pass over one area.

Usage:
    python3 scripts/brief.py <area> --slug <procedure-slug>              # drafter
    python3 scripts/brief.py <area> --slug <slug> --mode update          # drafter, mode-scoped
    python3 scripts/brief.py <area> --kind raci|dependencies             # synthesis
    python3 scripts/brief.py <area> --objective                          # objective block

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


def _sources_entries(folder: Path) -> list[dict]:
    # M34: ask the ONE detection seam. In central mode the area owns no
    # `_reference/sources.yaml` — the engagement ledger does — and `area_view`
    # hands back the v1 entry shape (flat area-local touches/consumed + derived
    # state), so the reading-list block below needs no change.
    if _central_root is not None and _area_view is not None:
        root = _central_root(str(folder))
        if root:
            return _area_view(root, Path(folder).name)
    folder = Path(folder)
    p = folder / "_reference" / "sources.yaml"
    if yaml is None or not p.is_file():
        return []
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
               "(serviceability, named per binding). A node serving an "
               "unserved binding is asked about FIRST, and an information "
               "request may cite the deliverable:")
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
            _reading_item(out, folder, f, note)
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


def main(argv=None) -> int:
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
