#!/usr/bin/env python3
"""consolidate.py — the deterministic half of M12 (cross-procedure consistency).

Usage:
    python3 scripts/consolidate.py plan   <area>                # dispatch plan
    python3 scripts/consolidate.py brief  <area> --bucket <l2>  # per-bucket work order
    python3 scripts/consolidate.py brief  <area> --cross        # cross-bucket work order
    python3 scripts/consolidate.py note   <area> --slug S --category C \
        --note "..." --peers "a, b" [--location L] [--anchor A]
    python3 scripts/consolidate.py report <area>                # gate summary
    python3 scripts/consolidate.py mark   <area>                # record the pass

Why this exists (design note): M12 splits on identity vs equivalence —
equivalence judgments ("do these two strings denote one report?") belong to
the consult-consolidator agent; everything decidable in Python belongs here.
That is: WHICH fragments each agent reads (`brief --bucket`), the bounded
cross-bucket DIGEST (scope + at-a-glance verbatim, step headings + first body
line — extracted by script so the context bound is guaranteed, not hoped
for), the mechanical NAMING TALLY (counted over `consult-meta` slug bindings
via aggregate.parse_consult_meta, never over prose), and the gate REPORT
(assembled from the queued notes, not re-parsed from agent prose).

Writers: `note` is the ONLY fragment-adjacent writer, and it writes notes —
never fragments — through notes_util.append_items (merge-append + dedupe, so
a rerun is idempotent). `mark` is the SOLE writer of `.consolidate.json`
({"draft_basis": sha}), which the draft-ready gate reads to say whether this
exact draft already had a pass. Everything else is read-only.

Exit codes: 0 = ok; 2 = bad usage / unknown area, bucket, slug or category.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doc_model    # noqa: E402
import notes_util   # noqa: E402
from aggregate import parse_consult_meta  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml ships in requirements
    yaml = None

#: The M12 finding taxonomy — closed; anything else the agent wants to raise
#: is out of bounds by contract.
CATEGORIES = ("naming", "duplication", "seam", "phrasing", "sequence")

#: Per category, per bucket (M12 settled decision 3). Enforced agent-side —
#: the script cannot know which bucket a note came from — but restated in
#: every brief and checked loosely by `report` (a category way past the cap
#: across ALL buckets is worth flagging).
CAP_PER_CATEGORY_PER_BUCKET = 10

#: The primer layer the cross-bucket digest carries verbatim (section SLUGS,
#: M23): the process overview and the at-a-glance table — where cross-bucket
#: drift surfaces.
PRIMER_SECTIONS = ("scope", "quick-reference")

REGISTRY_FILES = ("systems.yaml", "roles.yaml", "glossary.yaml")

STEP_HEADING_RE = re.compile(r"^####\s+(?P<title>\S.*?)\s*$")

MARK_FILE = ".consolidate.json"


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


def _buckets(manifest: dict) -> dict[str, list[dict]]:
    """{l2: [procedure components, manifest order]} in l2_order; buckets not
    in l2_order (a manifest defect doc_model already flags) trail first-seen."""
    order = list(manifest.get("l2_order") or [])
    out: dict[str, list[dict]] = {l2: [] for l2 in order}
    for c in sorted(_procedures(manifest), key=lambda c: c.get("order", 0)):
        out.setdefault(c.get("l2") or "?", []).append(c)
    return {l2: procs for l2, procs in out.items() if procs}


def _line(out: list[str], s: str = "") -> None:
    out.append(s)


def _read(folder: Path, comp: dict) -> str:
    p = folder / comp.get("file", "")
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")


def _queued(folder: Path) -> dict[str, list[dict]]:
    """{slug: [consolidation items]} across the whole notes queue."""
    out: dict[str, list[dict]] = {}
    rev = folder / "_review"
    if not rev.is_dir():
        return out
    for f in sorted(rev.glob("*" + notes_util.NOTES_SUFFIX)):
        slug = f.name[: -len(notes_util.NOTES_SUFFIX)]
        items = [it for it in notes_util.load_items_from(f)
                 if it.get("kind") == "consolidation"]
        if items:
            out[slug] = items
    return out


def _note_command(folder: Path) -> str:
    return (f"python3 <plugin>/scripts/consolidate.py note {folder} "
            f"--slug <slug> --category <"
            + "|".join(CATEGORIES)
            + "> --note \"...\" --peers \"<slug>, <slug>\" "
              "[--location \"...\"] [--anchor \"...\"]")


def _rules_block(out: list[str], folder: Path) -> None:
    _line(out, "FINDING RULES (your contract has the full taxonomy):")
    _line(out, f"  - categories: {', '.join(CATEGORIES)} — nothing else")
    _line(out, "  - EVERY finding cites >=2 procedures (a single-procedure "
               "nit is out of bounds); the `note` command refuses empty "
               "--peers")
    _line(out, f"  - cap: {CAP_PER_CATEGORY_PER_BUCKET} per category for "
               f"your pass; when you truncate, SAY WHAT WAS DROPPED in your "
               f"status (no silent caps)")
    _line(out, "  - factual CONFLICTS are reported in your status, never "
               "written as notes — you have no sources, so you cannot know "
               "which side is right")
    _line(out, "  - you write NOTHING except through:")
    _line(out, f"      {_note_command(folder)}")
    _line(out)


def _notes_block(out: list[str], folder: Path) -> None:
    queued = _queued(folder)
    if queued:
        counts = ", ".join(f"{s}: {len(items)}"
                           for s, items in sorted(queued.items()))
        _line(out, f"CONSOLIDATION NOTES ALREADY QUEUED ({counts}) — "
                   f"re-raising one is a harmless no-op (the bus dedupes), "
                   f"but read them first so your pass adds, not repeats")
    else:
        _line(out, "CONSOLIDATION NOTES ALREADY QUEUED: none")
    _line(out)


# --------------------------------------------------------------------------- #
# brief --bucket <l2>
# --------------------------------------------------------------------------- #

def bucket_brief(folder: Path, manifest: dict, l2: str) -> str:
    buckets = _buckets(manifest)
    if l2 not in buckets:
        known = ", ".join(sorted(buckets)) or "none"
        raise _fail(f"unknown L2 bucket {l2!r} in {folder} (known: {known})")
    out: list[str] = []
    _line(out, f"WORK ORDER — consult-consolidator · bucket {l2} · {folder}")
    _line(out, "  read-only pass: you write NO fragment, NO registry file, "
               "NO derived view — findings go to the notes bus via the "
               "`note` command below")
    _line(out, "  your lens: seam + sequence live here — hold this bucket's "
               "procedures side by side")
    _line(out)
    _line(out, "READING LIST (complete — the fragments below ARE your "
               "bucket, in document order):")
    for c in buckets[l2]:
        p = folder / c.get("file", "")
        mark = "" if p.is_file() else "  [MISSING — report it, do not guess]"
        _line(out, f"  - {p}  ([[{c.get('slug', '?')}]] — "
                   f"{c.get('heading', '')}){mark}")
    for name in REGISTRY_FILES:
        if (folder / "_reference" / name).is_file():
            _line(out, f"  - {folder / '_reference' / name}")
    for conv in sorted((folder / "_reference" / "conventions").glob("*.md")):
        _line(out, f"  - {conv}  (conventions digest — phrasing already "
                   f"decided; drift FROM it is a `phrasing` finding)")
    _line(out)
    _rules_block(out, folder)
    _notes_block(out, folder)
    _line(out, "BEFORE YOU FINISH:")
    _line(out, "  1. Re-read your notes' anchors against the fragments — an "
               "anchor that no longer matches strands the drafter")
    _line(out, "  2. Return the compact status (findings per category, "
               "truncations, conflicts) — never paste fragment text")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# brief --cross  (the digest is computed HERE — the context bound is the
# script's guarantee, not agent discipline)
# --------------------------------------------------------------------------- #

def _sections(text: str) -> list[tuple[str | None, str, list[str]]]:
    """[(section-slug-or-None, heading line, body lines)] split on `###`."""
    out: list[tuple[str | None, str, list[str]]] = []
    cur: tuple[str | None, str, list[str]] | None = None
    for line in (text or "").split("\n"):
        if line.startswith("### "):
            if cur:
                out.append(cur)
            cur = (doc_model.section_of_heading(line), line, [])
        elif cur:
            cur[2].append(line)
    if cur:
        out.append(cur)
    return out


def _step_digest(body: list[str]) -> list[str]:
    """Each `####` step heading + the first non-empty, non-callout body line."""
    out: list[str] = []
    i = 0
    while i < len(body):
        m = STEP_HEADING_RE.match(body[i])
        if m:
            out.append(f"    {m.group('title')}")
            j = i + 1
            while j < len(body) and not STEP_HEADING_RE.match(body[j]):
                s = body[j].strip()
                if s and not s.startswith(">"):
                    out.append(f"      {s}")
                    break
                j += 1
            i = j if j > i else i + 1
        else:
            i += 1
    return out


def _digest(folder: Path, comp: dict) -> list[str]:
    out: list[str] = []
    text = _read(folder, comp)
    slug = comp.get("slug", "?")
    if not text:
        return [f"  [[{slug}]] — fragment file MISSING; report it"]
    out.append(f"  ── [[{slug}]] — {comp.get('heading', '')} "
               f"(l2: {comp.get('l2', '?')})")
    secs = _sections(text)
    for sec_slug, heading, body in secs:
        if sec_slug in PRIMER_SECTIONS:
            out.append(f"    {heading.lstrip('# ').strip()}:")
            out.extend(f"      {ln}" for ln in body if ln.strip())
        elif sec_slug == "steps":
            steps = _step_digest(body)
            if steps:
                out.append("    steps (heading + first line only — the full "
                           "body was NOT read; if a finding needs more, name "
                           "the fragment in your status):")
                out.extend(steps)
    return out


def _naming_tally(folder: Path, manifest: dict) -> list[str]:
    """The mechanical majority basis: per registry axis, slug → binding
    procedures, counted over `consult-meta` — never over prose."""
    binds: dict[str, dict[str, list[str]]] = {"systems": {}, "roles": {}}
    for c in _procedures(manifest):
        text = _read(folder, c)
        if not text:
            continue
        try:
            meta = parse_consult_meta(text)
        except Exception as exc:  # aggregate's FragmentError — surface, skip
            binds.setdefault("_errors", {}).setdefault(str(exc), []).append(
                c.get("slug", "?"))
            continue
        for axis in ("systems", "roles"):
            for s in meta.get(axis, []):
                binds[axis].setdefault(s, []).append(c.get("slug", "?"))
    names: dict[str, str] = {}
    for fname, key in (("systems.yaml", "systems"), ("roles.yaml", "roles")):
        p = folder / "_reference" / fname
        if yaml is None or not p.is_file():
            continue
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        for e in data.get(key) or []:
            if isinstance(e, dict) and e.get("slug"):
                names[e["slug"]] = e.get("name", e["slug"])
    out: list[str] = []
    for axis in ("systems", "roles"):
        for s, procs in sorted(binds[axis].items()):
            canon = names.get(s)
            label = f"{s} (canonical name: {canon})" if canon \
                else f"{s} (NOT in the registry — candidate top-up)"
            out.append(f"  - {axis[:-1]} {label}: bound by {len(procs)} — "
                       f"{', '.join(procs)}")
    for err, procs in sorted(binds.get("_errors", {}).items()):
        out.append(f"  - [malformed consult-meta in {', '.join(procs)}: "
                   f"{err} — report it]")
    return out


def cross_brief(folder: Path, manifest: dict) -> str:
    out: list[str] = []
    procs = _procedures(manifest)
    _line(out, f"WORK ORDER — consult-consolidator · cross-bucket · {folder}")
    _line(out, "  read-only pass: you write NO fragment — findings go to "
               "the notes bus via the `note` command below")
    _line(out, "  your lens: global naming drift + duplication — what no "
               "per-bucket pass can see")
    _line(out, f"  {len(procs)} procedures · "
               f"{len(_buckets(manifest))} L2 buckets")
    _line(out)
    _line(out, "READING LIST — the DIGEST below IS your read of the "
               "fragments (extracted by script: scope + at-a-glance "
               "verbatim, step headings + first body line). Do NOT open the "
               "fragment files; a finding that needs a full step body names "
               "the fragment in your status instead. Read in addition:")
    for name in REGISTRY_FILES:
        if (folder / "_reference" / name).is_file():
            _line(out, f"  - {folder / '_reference' / name}")
    for conv in sorted((folder / "_reference" / "conventions").glob("*.md")):
        _line(out, f"  - {conv}  (conventions digest)")
    _line(out)
    _line(out, "NAMING TALLY (mechanical majority basis — counted over "
               "`consult-meta` slug bindings, NEVER over prose; your "
               "judgment covers only nouns the registry does not know, "
               "justified overrides, and even splits, which go to the human "
               "unresolved):")
    tally = _naming_tally(folder, manifest)
    for ln in tally or ["  - (no consult-meta bindings found)"]:
        _line(out, ln)
    _line(out)
    _rules_block(out, folder)
    _notes_block(out, folder)
    _line(out, "DIGEST:")
    for c in sorted(procs, key=lambda c: c.get("order", 0)):
        for ln in _digest(folder, c):
            _line(out, ln)
    _line(out)
    _line(out, "BEFORE YOU FINISH:")
    _line(out, "  1. Route naming findings vocabulary-first: registry alias "
               "top-up / conventions entry PROPOSALS go in your status (a "
               "human confirms; you never edit _reference/)")
    _line(out, "  2. Return the compact status (findings per category, "
               "proposals, conflicts, truncations) — never paste the digest "
               "back")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# plan / note / report / mark
# --------------------------------------------------------------------------- #

def plan(folder: Path, manifest: dict) -> str:
    buckets = _buckets(manifest)
    n = len(buckets)
    agents = n + (1 if n > 1 else 0)
    out: list[str] = []
    _line(out, f"CONSOLIDATE PLAN — {folder}")
    _line(out, f"  {len(_procedures(manifest))} procedures · {n} L2 "
               f"bucket(s) · {agents} agent(s)"
               + ("" if n > 1 else "  (single bucket: the bucket pass "
                                   "covers everything; no cross-bucket "
                                   "agent)"))
    _line(out)
    _line(out, "DISPATCH (per-bucket agents in parallel, then the "
               "cross-bucket agent — each runs its brief as its first "
               "action):")
    for l2, procs in buckets.items():
        _line(out, f"  - consult-consolidator · bucket {l2} "
                   f"({len(procs)} procedures)")
        _line(out, f"      brief: python3 <plugin>/scripts/consolidate.py "
                   f"brief {folder} --bucket {l2}")
    if n > 1:
        _line(out, "  - consult-consolidator · cross-bucket")
        _line(out, f"      brief: python3 <plugin>/scripts/consolidate.py "
                   f"brief {folder} --cross")
    _line(out)
    _line(out, "THEN (free):")
    _line(out, f"  1. python3 <plugin>/scripts/consolidate.py report "
               f"{folder}   (the human-facing summary; they may delete "
               f"notes before anything consumes them)")
    _line(out, f"  2. python3 <plugin>/scripts/consolidate.py mark {folder} "
               f"  (records the pass at the current draft basis)")
    _line(out, "  3. Re-run the advisor: queued notes route to the drafters "
               "through the ordinary apply_review loop; the tail "
               "(synthesize/render) has NOT run yet, so it runs once")
    return "\n".join(out)


def _parse_peers(raw: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,\s]+", raw or "") if p.strip()]


def add_note(folder: Path, manifest: dict, a: argparse.Namespace) -> str:
    slugs = {c.get("slug") for c in _procedures(manifest)}
    if a.slug not in slugs:
        raise _fail(f"unknown procedure slug {a.slug!r} in {folder} "
                    f"(known: {', '.join(sorted(s for s in slugs if s))})")
    if a.category not in CATEGORIES:
        raise _fail(f"unknown category {a.category!r} — the M12 taxonomy is: "
                    f"{', '.join(CATEGORIES)}. Anything else is out of "
                    f"bounds for the consolidator")
    peers = _parse_peers(a.peers)
    bad = [p for p in peers if p not in slugs]
    if bad:
        raise _fail(f"peer slug(s) not in the manifest: {', '.join(bad)}")
    peers = [p for p in peers if p != a.slug]
    if not peers:
        raise _fail("a consolidation finding cites >=2 procedures — pass "
                    "--peers with at least one OTHER procedure slug (a "
                    "single-procedure nit is out of bounds; M12 evidence "
                    "rule)")
    item = {
        "kind": "consolidation",
        "type": "consolidation",
        "category": a.category,
        "location": a.location or "",
        "anchor": a.anchor or "",
        "note": a.note,
        "peers": ", ".join(peers),
        "source": "consolidate",
    }
    added = notes_util.append_items(folder, a.slug, [item])
    verb = "queued" if added else "already queued (deduped — no-op)"
    return (f"{verb}: {a.category} finding on [[{a.slug}]] "
            f"(peers: {', '.join(peers)}) → "
            f"{folder / '_review' / (a.slug + notes_util.NOTES_SUFFIX)}")


def report(folder: Path, manifest: dict) -> str:
    queued = _queued(folder)
    by_cat: dict[str, int] = {c: 0 for c in CATEGORIES}
    for items in queued.values():
        for it in items:
            by_cat[it.get("category", "?")] = \
                by_cat.get(it.get("category", "?"), 0) + 1
    total = sum(by_cat.values())
    out: list[str] = []
    _line(out, f"CONSOLIDATION — {manifest.get('area', folder.name)}")
    n_buckets = len(_buckets(manifest))
    _line(out, f"{len(_procedures(manifest))} procedures · {n_buckets} L2 "
               f"bucket(s)")
    _line(out)
    for cat in CATEGORIES:
        _line(out, f"{cat:<14} {by_cat.get(cat, 0)} finding(s)")
    stray = {c: n for c, n in by_cat.items() if c not in CATEGORIES and n}
    for c, n2 in sorted(stray.items()):
        _line(out, f"{c:<14} {n2} finding(s)  [NOT in the M12 taxonomy — a "
                   f"producer bypassed the note command]")
    _line(out)
    _line(out, "CONFLICTS are never queued as notes — they live in the "
               "agents' returned statuses; relay them to the human "
               "unresolved.")
    _line(out)
    _line(out, "─" * 60)
    _line(out, f"{total} finding(s) · {len(queued)} procedure(s) touched")
    _line(out, f"ACCEPTING IMPLIES {len(queued)} DRAFTER DISPATCH(ES)  "
               f"(one per slug, batched by apply_review — per slug, not per "
               f"finding)")
    _line(out)
    _line(out, f"Notes live in {folder / '_review'}/<slug>.notes.yaml — "
               f"nothing else changed.")
    _line(out, "Delete any note you disagree with before apply_review runs.")
    return "\n".join(out)


def mark(folder: Path) -> str:
    import orchestrate
    st = orchestrate.AreaState(str(folder))
    basis = st.draft_basis()
    (folder / MARK_FILE).write_text(
        json.dumps({"draft_basis": basis}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return (f"marked: consolidation pass recorded at draft_basis {basis} → "
            f"{folder / MARK_FILE} (any fragment or registry edit moves the "
            f"basis and reads as un-consolidated again)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="M12 consolidator — deterministic layer (briefs, notes, "
                    "report).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "report", "mark"):
        p = sub.add_parser(name)
        p.add_argument("area", help="area folder, e.g. components/<area>")
    p_b = sub.add_parser("brief")
    p_b.add_argument("area")
    g = p_b.add_mutually_exclusive_group(required=True)
    g.add_argument("--bucket", help="L2 bucket slug (per-bucket work order)")
    g.add_argument("--cross", action="store_true",
                   help="cross-bucket work order (digest computed here)")
    p_n = sub.add_parser("note")
    p_n.add_argument("area")
    p_n.add_argument("--slug", required=True,
                     help="the procedure the note is FOR (its drafter acts)")
    p_n.add_argument("--category", required=True,
                     help="|".join(CATEGORIES))
    p_n.add_argument("--note", required=True)
    p_n.add_argument("--peers", required=True,
                     help="comma-separated OTHER procedure slugs evidencing "
                          "the finding (>=1)")
    p_n.add_argument("--location", default="")
    p_n.add_argument("--anchor", default="")
    a = ap.parse_args(argv)

    folder, manifest = _load_area(a.area)
    if a.cmd == "plan":
        print(plan(folder, manifest))
    elif a.cmd == "brief":
        print(cross_brief(folder, manifest) if a.cross
              else bucket_brief(folder, manifest, a.bucket))
    elif a.cmd == "note":
        print(add_note(folder, manifest, a))
    elif a.cmd == "report":
        print(report(folder, manifest))
    elif a.cmd == "mark":
        print(mark(folder))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
