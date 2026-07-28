#!/usr/bin/env python3
"""brief.py — deterministic work order for a subagent's pass over one area.

Usage:
    python3 scripts/brief.py <area> --slug <procedure-slug>     # drafter
    python3 scripts/brief.py <area> --kind raci|dependencies    # synthesis

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


def drafter_brief(folder: Path, manifest: dict, slug: str) -> str:
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
    _line(out)

    _profile_block(out, folder)

    _line(out, "READING LIST (complete — nothing else is required input):")
    _reading_item(out, folder, frag, "your skeleton/draft")
    tagged = [e for e in _sources_entries(folder)
              if slug in (e.get("touches") or [])]
    if tagged:
        for e in tagged:
            sid, f = e.get("id", "?"), e.get("file", "")
            done = slug in (e.get("consumed") or [])
            note = f"{sid}, tagged to you"
            if done:
                note += ("; already consumed by you — re-read only if your "
                         "dispatch names it")
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
    ups = [u for u in (comp.get("upstream") or [])]
    for u in ups:
        ucomp = next((c for c in procs if c.get("slug") == u), None)
        if ucomp:
            _reading_item(out, folder, ucomp.get("file", ""),
                          f"upstream seam ({u}) — READ-ONLY context")
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
    a = ap.parse_args(argv)

    folder, manifest = _load_area(a.area)
    try:
        if a.slug:
            print(drafter_brief(folder, manifest, a.slug))
        else:
            print(synthesis_brief(folder, manifest, a.kind))
    except client_config.ClientConfigError as e:
        print(f"ERROR: {e}\nfix the client config before drafting over it",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
