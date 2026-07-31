#!/usr/bin/env python3
"""consolidate.py — the deterministic half of M12 (cross-procedure consistency).

Usage:
    python3 scripts/consolidate.py plan   <area>                # dispatch plan
    python3 scripts/consolidate.py brief  <area> --bucket <l2>[,<l2>...]  # group work order
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

import callouts     # noqa: E402  (open_gaps — the one gap parser)
import doc_model    # noqa: E402
import notes_util   # noqa: E402
from aggregate import parse_consult_meta  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml ships in requirements
    yaml = None

#: The M12 finding taxonomy — closed; anything else the agent wants to raise
#: is out of bounds by contract. `gap-answer` (A2): a GAP in one procedure
#: that a sibling procedure answers — within-area only, where the source
#: pool is shared so the resolution is a pointer to the sibling's SRC id.
CATEGORIES = ("naming", "duplication", "seam", "phrasing", "sequence",
              "gap-answer")

#: Per category, per bucket (M12 settled decision 3). Enforced agent-side —
#: the script cannot know which bucket a note came from — but restated in
#: every brief and checked loosely by `report` (a category way past the cap
#: across ALL buckets is worth flagging).
CAP_PER_CATEGORY_PER_BUCKET = 10

#: Bucket-group packing budget: consecutive `l2_order` buckets pack into one
#: agent until the group would exceed this many fragments. Adjacency is the
#: point — handoffs flow between neighboring buckets, so packing consecutive
#: buckets puts the bucket-boundary seams (which one-agent-per-bucket
#: structurally missed) inside a single read. Buckets are never split; a
#: bucket larger than the budget rides alone, over budget (its seam density
#: is exactly why it must be read together).
FRAGMENT_BUDGET = 5

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


def _groups(manifest: dict) -> list[list[str]]:
    """Deterministic bucket-group packing: walk `l2_order` (document order),
    greedy-pack consecutive buckets under FRAGMENT_BUDGET, never split a
    bucket, then fold any 1-fragment group into its neighbor (an agent
    reading one fragment can meet the evidence rule only via conventions —
    run-4 measured that as dispatch waste)."""
    buckets = _buckets(manifest)
    size = {l2: len(procs) for l2, procs in buckets.items()}
    groups: list[list[str]] = []
    count = 0
    for l2 in buckets:
        if groups and count + size[l2] <= FRAGMENT_BUDGET:
            groups[-1].append(l2)
            count += size[l2]
        else:
            groups.append([l2])
            count = size[l2]

    def _gsize(g: list[str]) -> int:
        return sum(size[l2] for l2 in g)

    i = 0
    while i < len(groups):
        if _gsize(groups[i]) == 1 and len(groups) > 1:
            if i > 0:
                groups[i - 1].extend(groups.pop(i))
                i -= 1
            else:
                groups[0] = groups[0] + groups.pop(1)
        else:
            i += 1
    return groups


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


def _register_lines(folder: Path) -> list[str]:
    """Engagement registers (components/_client/registers/*), listed in
    every brief with the M24 rule: values are referenced, never restated.
    M30: structured files list their entries (ids + class) so findings and
    proposals target ENTRIES (`<register>#<entry-id>`), not files."""
    parent = folder.resolve().parent
    if parent.name != "components":
        return []
    import registers
    out: list[str] = []
    for p, title, entries in registers.load_all(parent):
        if entries is None:
            out.append(f"  - {p}  (ENGAGEMENT REGISTER — the one home of "
                       f"shared facts; a procedure restating one of its "
                       f"values is a `phrasing`/`duplication` finding)")
            continue
        out.append(f"  - {p}  (ENGAGEMENT REGISTER — {title}; a procedure "
                   f"restating a CITABLE value is a `phrasing`/"
                   f"`duplication` finding; propose NEW entries in your "
                   f"status as `{p.stem}#<entry-id>` with class + "
                   f"provenance)")
        for e in entries:
            out.append(f"      {p.stem}#{e.id}  [{e.cls}]  "
                       f"{registers.first_line(e.text)}")
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
# brief --bucket <l2>[,<l2>...]  (a bucket GROUP — the plan computes groups)
# --------------------------------------------------------------------------- #

def _handoff_lines(counterpart_text: str, this_area: str) -> tuple[str, list[str]]:
    """The counterpart's HANDOFF SENTENCE(S), extracted by literal line scan
    (M12-A3 item 1 — deterministic, no judgment): (a) up to 3 lines holding a
    token pointing back at `this_area` ([[<this-area>/...]]); else (b) the
    Scope section's first 2 non-empty lines as fallback context."""
    blanked = callouts.blank_fences(counterpart_text)
    back: list[str] = []
    for line in blanked.split("\n"):
        if any(doc_model.split_xref(t)[0] == this_area
               for t in callouts.XREF_RE.findall(line)):
            back.append(line.strip())
            if len(back) == 3:
                break
    if back:
        return "back-reference", back
    scope: list[str] = []
    for sec_slug, _heading, body in _sections(blanked):
        if sec_slug == "scope":
            scope = [ln.strip() for ln in body if ln.strip()][:2]
            break
    return "scope-fallback", scope


def _cross_seam_block(folder: Path, group_comps: list[dict]) -> list[str]:
    """CROSS-AREA SEAMS lines for the group brief (M26/M12-A3): one sub-item
    per distinct cross-area token in the group's blanked fragment text, with
    the counterpart's handoff sentence(s) so the group agent can verify the
    boundary. Empty outside a components/ root or with no cross tokens."""
    siblings = doc_model.sibling_procedures(folder)
    if not siblings:
        return []
    this_area = folder.resolve().name
    tokens: dict[str, list[str]] = {}   # token -> local slugs holding it
    for c in group_comps:
        blanked = callouts.blank_fences(_read(folder, c))
        for t in callouts.XREF_RE.findall(blanked):
            if "/" in t:
                tokens.setdefault(t, [])
                slug = c.get("slug", "?")
                if slug not in tokens[t]:
                    tokens[t].append(slug)
    if not tokens:
        return []
    out: list[str] = ["CROSS-AREA SEAMS (M26/M12-A3) — your fragments hand "
                      "off across an area boundary; the counterpart's handoff "
                      "sentence(s) are extracted below so you can check the "
                      "seam without leaving your read:"]
    for tok in sorted(tokens):
        area, slug = doc_model.split_xref(tok)
        holders = ", ".join(f"[[{s}]]" for s in tokens[tok])
        sib = siblings.get(area)
        heading = (sib or {}).get("slugs", {}).get(slug)
        if sib is None or heading is None:
            out.append(f"  - [[{tok}]] (in {holders}) — counterpart NOT "
                       f"resolvable via the sibling manifests (reconcile "
                       f"flags dangling cross tokens; report it, do not "
                       f"guess)")
            continue
        out.append(f"  - [[{tok}]] (in {holders}) — counterpart: {heading} "
                   f"({sib['title']}, area {area})")
        cm = doc_model.load_manifest(sib["path"])
        comp = next((c for c in cm.get("components", [])
                     if c.get("role") == "procedure"
                     and c.get("slug") == slug), None)
        text = _read(sib["path"], comp or {})
        if not text:
            out.append("      counterpart fragment file MISSING/empty — "
                       "report it")
            continue
        kind, lines = _handoff_lines(text, this_area)
        if kind == "back-reference":
            out.append("      its handoff sentence(s) back toward this "
                       "area (verbatim):")
        else:
            out.append("      no back-reference to this area found — its "
                       "Scope opening as context (verbatim):")
        for ln in lines or ["(none — empty counterpart)"]:
            out.append(f"        > {ln}")
    out.append("  - verify artifact names, timing and state agree across "
               "the boundary; a mismatch is an ordinary `seam` finding on "
               "YOUR side's procedure (peers = the local procedures "
               "involved; name the cross-area counterpart in the note text "
               "— you cannot write notes to another area); if the "
               "counterpart is an unfilled skeleton say so in your status "
               "under `seam_unverified_counterpart` instead")
    return out

def bucket_brief(folder: Path, manifest: dict, bucket_arg: str) -> str:
    buckets = _buckets(manifest)
    group = [b.strip() for b in bucket_arg.split(",") if b.strip()]
    unknown = [b for b in group if b not in buckets]
    if unknown:
        known = ", ".join(sorted(buckets)) or "none"
        raise _fail(f"unknown L2 bucket(s) {', '.join(unknown)!s} in "
                    f"{folder} (known: {known})")
    full_area = set(group) == set(buckets)
    label = ", ".join(group)
    out: list[str] = []
    _line(out, f"WORK ORDER — consult-consolidator · bucket group "
               f"[{label}] · {folder}")
    _line(out, "  read-only pass: you write NO fragment, NO registry file, "
               "NO derived view — findings go to the notes bus via the "
               "`note` command below")
    if full_area:
        _line(out, "  your lens: ALL of it — this group covers the whole "
                   "area, so no cross-bucket agent runs after you: seam, "
                   "sequence, naming, duplication and phrasing are all "
                   "yours (the NAMING TALLY below is your mechanical "
                   "majority basis)")
    elif len(group) > 1:
        _line(out, "  your lens: seam + sequence — hold these procedures "
                   "side by side; seams BETWEEN your buckets are yours "
                   "too, not just seams within each")
    else:
        _line(out, "  your lens: seam + sequence live here — hold this "
                   "bucket's procedures side by side")
    _line(out)
    _line(out, "READING LIST (complete — the fragments below ARE your "
               "group, in document order):")
    for l2 in group:
        for c in buckets[l2]:
            p = folder / c.get("file", "")
            mark = ("" if p.is_file()
                    else "  [MISSING — report it, do not guess]")
            _line(out, f"  - {p}  ([[{c.get('slug', '?')}]] — "
                       f"{c.get('heading', '')}; l2: {l2}){mark}")
    for name in REGISTRY_FILES:
        if (folder / "_reference" / name).is_file():
            _line(out, f"  - {folder / '_reference' / name}")
    for conv in sorted((folder / "_reference" / "conventions").glob("*.md")):
        _line(out, f"  - {conv}  (conventions digest — phrasing already "
                   f"decided; drift FROM it is a `phrasing` finding)")
    for ln in _register_lines(folder):
        _line(out, ln)
    _line(out)
    group_comps = [c for l2 in group for c in buckets[l2]]
    seam_lines = _cross_seam_block(folder, group_comps)
    if seam_lines:
        for ln in seam_lines:
            _line(out, ln)
        _line(out)
    if full_area:
        _line(out, "NAMING TALLY (mechanical majority basis — counted over "
                   "`consult-meta` slug bindings, NEVER over prose; your "
                   "judgment covers only nouns the registry does not know, "
                   "justified overrides, and even splits, which go to the "
                   "human unresolved):")
        for ln in _naming_tally(folder, manifest) \
                or ["  - (no consult-meta bindings found)"]:
            _line(out, ln)
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
    # A2: the digest deliberately skips callout (`>`) lines, which is where
    # GAP callouts live — so the open gaps ride along mechanically, or the
    # cross pass would be structurally blind to the gap-answer category.
    gaps = callouts.open_gaps(text)
    if gaps:
        out.append("    open gaps (still unanswered here — if another "
                   "procedure's digest answers one, that is a `gap-answer` "
                   "finding):")
        for gid, gtext in gaps:
            gtext = gtext if len(gtext) <= 160 else gtext[:157] + "…"
            out.append(f"      {gid} — {gtext}")
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
    for ln in _register_lines(folder):
        _line(out, ln)
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
    groups = _groups(manifest)
    single = len(groups) == 1
    agents = len(groups) + (0 if single else 1)
    out: list[str] = []
    _line(out, f"CONSOLIDATE PLAN — {folder}")
    _line(out, f"  {len(_procedures(manifest))} procedures · "
               f"{len(buckets)} L2 bucket(s) · {len(groups)} bucket "
               f"group(s) (budget {FRAGMENT_BUDGET} fragments, buckets "
               f"never split) · {agents} agent(s)"
               + ("  (single group: it reads the whole area in full, so "
                  "it carries the cross lens too — no cross-bucket agent)"
                  if single else ""))
    _line(out)
    _line(out, "DISPATCH (group agents in parallel"
               + ("" if single else ", then the cross-bucket agent")
               + " — each runs its brief as its first action):")
    for g in groups:
        n_frag = sum(len(buckets[l2]) for l2 in g)
        _line(out, f"  - consult-consolidator · bucket group "
                   f"[{', '.join(g)}] ({n_frag} procedures)")
        _line(out, f"      brief: python3 <plugin>/scripts/consolidate.py "
                   f"brief {folder} --bucket {','.join(g)}")
    if not single:
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
    g.add_argument("--bucket",
                   help="L2 bucket slug or comma-joined bucket GROUP as "
                        "printed by `plan` (group work order)")
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
