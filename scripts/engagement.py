#!/usr/bin/env python3
"""engagement.py — the knowledge-placement layer: one fact, one home (M24).

Usage:
    python3 scripts/engagement.py audit  [components-dir]
    python3 scripts/engagement.py brief  [components-dir]
    python3 scripts/engagement.py note   <area> --slug S --note "..."
    python3 scripts/engagement.py adopt  <area> --from <area>/<slug> \
        --touches <slug> [<slug> ...]
    python3 scripts/engagement.py route  intake/<file> --to a[,b] \
        [--note-for a "pointer"] [--new-area]
    python3 scripts/engagement.py park   intake/<file> --reason "..."
    python3 scripts/engagement.py register add|update|list ...   (M30 —
        the ONLY writer of _client/registers/; see registers.py)

The per-area guards (ownership map, taxonomy neighbors, reconcile check 17)
are PREVENTIVE and see only one area at a time. This module is the
RETROSPECTIVE, engagement-wide layer. The standing rule is that every fact
has exactly ONE home; the engagement's two chronic diseases are the two
directions of violating it — DUPLICATION (a fact with two homes) and a
CROSS-ANSWERABLE GAP (a fact with a broken pointer: one area asks what
another area documents). `audit` reports both directions from one walk:

  1. TWIN L3s     — two areas each scoped a procedure whose titles are the
                    same activity (normalized-token containment).
  2. MENTIONS     — one area's prose names another area's procedure title.
  3. SHARED PROSE — fragment pairs across areas sharing long word runs
                    (8-word shingles): the same source material drafted
                    twice, verbatim OR paraphrased around a shared skeleton.
  4. OPEN GAPS    — the engagement's unanswered questions, by area
                    (callouts.open_gaps — the one gap parser everywhere).
  5. INTERFACES   — the M26 derived spine: every [[area/slug]] token and
                    cross-area upstream declaration, read fresh off the
                    prose/manifests each run (owned and maintained by
                    nobody), plus asymmetric-seam findings.

`brief` prints the work order for the single placement-pass agent (three
moves: reduce-to-handoff, promote-to-register, adopt-as-source; policy /
control-design questions are reported, never resolved). `adopt` is the
prose-as-source verb: it REGISTERS another area's drafted fragment as an
ordinary hash-stamped source, so every invariant (citation resolution,
provenance, retirement accounting) survives because it IS a source.

Read-only except `note` (notes bus) and `adopt` (source registration);
exit 0 with findings (the human decides ownership), exit 2 on bad usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import callouts   # noqa: E402  (open_gaps — the one gap parser)
import doc_model  # noqa: E402  (section_of_heading — the one section parser)

_WORD_RE = re.compile(r"[a-z0-9]+")
#: Title tokens carrying no activity identity on their own.
_STOP = {"the", "a", "an", "and", "of", "to", "for", "in", "process",
         "processing", "management", "and"}
#: Shingle width (words) and how many shared shingles flag a fragment pair.
#: 8-word windows survive paraphrase-with-shared-skeleton (two drafters
#: working the same interview rarely produce IDENTICAL sentences, but their
#: sentences share long word runs); 4 shared shingles ≈ one identical 11-word
#: run or several shorter ones — below that is idiom, not duplication.
_SHINGLE_K = 8
_SHARED_SHINGLES_MIN = 4


def _tokens(title: str) -> frozenset[str]:
    return frozenset(w for w in _WORD_RE.findall(title.lower())
                     if w not in _STOP)


def _areas(root: Path) -> list[tuple[str, dict]]:
    out = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if d.name.startswith(("_", ".")):
            continue
        m = d / "manifest.json"
        if not m.is_file():
            continue
        try:
            out.append((d.name, json.loads(m.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            print(f"warning: {m} unreadable — area skipped", file=sys.stderr)
    return out


def _procedures(manifest: dict) -> list[dict]:
    return [c for c in manifest.get("components", [])
            if c.get("role") == "procedure"]


def _fragment_text(root: Path, area: str, comp: dict) -> str:
    p = root / area / comp.get("file", "")
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def _prose_paragraphs(text: str) -> list[str]:
    """Prose joined back into paragraphs. Fragments hard-wrap at ~80 columns,
    so shingling must run across line breaks; headings, tables, callout lines
    and fenced blocks are structure, not prose, and break a paragraph."""
    paras: list[str] = []
    cur: list[str] = []
    fenced = False
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("```"):
            fenced = not fenced
            continue
        if fenced or not s or s.startswith(("#", "|", ">", "<!--")):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            continue
        cur.append(re.sub(r"^[-*+]\s+|^\d+\.\s+", "", s))
    if cur:
        paras.append(" ".join(cur))
    return paras


def _shingles(text: str) -> set[str]:
    """All _SHINGLE_K-word windows over the fragment's prose paragraphs."""
    out: set[str] = set()
    for para in _prose_paragraphs(text):
        words = _WORD_RE.findall(para.lower())
        for i in range(len(words) - _SHINGLE_K + 1):
            out.add(" ".join(words[i:i + _SHINGLE_K]))
    return out


def twin_l3s(areas, out: list[str]) -> int:
    """Same activity scoped as an L3 in two areas (title containment)."""
    procs = [(a, c.get("slug", "?"), (c.get("heading") or "").strip())
             for a, m in areas for c in _procedures(m)]
    n = 0
    for i, (a1, s1, t1) in enumerate(procs):
        k1 = _tokens(t1)
        if len(k1) < 2:
            continue
        for a2, s2, t2 in procs[i + 1:]:
            if a1 == a2:
                continue
            k2 = _tokens(t2)
            if len(k2) < 2:
                continue
            overlap = len(k1 & k2) / min(len(k1), len(k2))
            if overlap >= 0.75:
                n += 1
                out.append(f"  - {a1}/{s1} ('{t1}')  <->  {a2}/{s2} "
                           f"('{t2}')")
    return n


def cross_mentions(root: Path, areas, out: list[str]) -> int:
    """One area's prose naming another area's procedure title."""
    titles = [(a, c.get("slug", "?"), (c.get("heading") or "").strip())
              for a, m in areas for c in _procedures(m)
              if len((c.get("heading") or "").split()) >= 2]
    n = 0
    for a, m in areas:
        for comp in _procedures(m):
            text = _fragment_text(root, a, comp).lower()
            if not text:
                continue
            for oa, oslug, title in titles:
                if oa == a:
                    continue
                if title.lower() in text:
                    n += 1
                    out.append(f"  - {a}/{comp.get('slug', '?')} names "
                               f"'{title}' (owned by {oa}/{oslug})")
    return n


def shared_prose(root: Path, areas, out: list[str]) -> int:
    """Shared prose skeletons across areas: fragment pairs whose prose has
    _SHARED_SHINGLES_MIN or more common _SHINGLE_K-word runs. Catches both
    verbatim duplication AND paraphrase-with-shared-skeleton — exact-sentence
    matching missed the latter, and paraphrase is what parallel drafters
    working the same source actually produce."""
    sh_map: dict[tuple[str, str], set[str]] = {}
    for a, m in areas:
        for comp in _procedures(m):
            text = _fragment_text(root, a, comp)
            if text:
                sh_map[(a, comp.get("slug", "?"))] = _shingles(text)
    keys = sorted(sh_map)
    n = 0
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            if k1[0] == k2[0]:
                continue
            common = sh_map[k1] & sh_map[k2]
            if len(common) >= _SHARED_SHINGLES_MIN:
                n += 1
                sample = sorted(common, key=len, reverse=True)[0]
                out.append(f"  - {k1[0]}/{k1[1]}  <->  {k2[0]}/{k2[1]}: "
                           f"{len(common)} shared {_SHINGLE_K}-word run(s), "
                           f"e.g. \"…{sample}…\"")
    return n


def open_gap_register(root: Path, areas) -> tuple[int, list[str]]:
    """(count, lines) — every open gap across the engagement, by area."""
    lines: list[str] = []
    n = 0
    for a, m in areas:
        area_lines: list[str] = []
        for comp in _procedures(m):
            text = _fragment_text(root, a, comp)
            if not text:
                continue
            gaps = callouts.open_gaps(text)
            if gaps:
                area_lines.append(f"  {a}/{comp.get('slug', '?')}")
                for gid, gtext in gaps:
                    gtext = gtext if len(gtext) <= 160 else gtext[:157] + "…"
                    area_lines.append(f"    {gid} — {gtext}")
                n += len(gaps)
        lines.extend(area_lines)
    return n, lines


def _scope_digest(root: Path, a: str, comp: dict) -> list[str]:
    """The fragment's Scope section body — enough for the placement pass to
    judge what an area covers without reading the fragments."""
    text = _fragment_text(root, a, comp)
    out: list[str] = []
    in_scope = False
    for line in text.split("\n"):
        if line.startswith("### "):
            in_scope = doc_model.section_of_heading(line) == "scope"
            continue
        if in_scope and line.strip():
            out.append(f"      {line.strip()}")
    return out


def interface_spine(root: Path, areas) -> tuple[list[str], list[str]]:
    """(spine lines, finding lines) — the M26 derived spine.

    The interface catalog is READ OFF the [[area/slug]] tokens in the prose
    plus the manifests' cross-area `upstream` declarations, fresh each run —
    owned by nobody, maintained by nobody, never stale. Findings:
      - asymmetric seam: a seam declared/tokened from one side only
        (expected during mixed scoping order; the fix is an incremental
        taxonomy pass on the older area);
      - dangling target: the token names an area/procedure the manifests do
        not carry (reconcile blocks this per-area; named here so the blast
        radius of a rename is enumerable before AND after).
    """
    known: dict[str, set[str]] = {a: {c.get("slug") for c in _procedures(m)}
                                  for a, m in areas}
    # seams[(from_area, to_area)] = [(holder "a/slug", target "a/slug", how)]
    seams: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    spine: list[str] = []
    findings: list[str] = []
    for a, m in areas:
        for comp in _procedures(m):
            holder = f"{a}/{comp.get('slug', '?')}"
            targets: list[tuple[str, str]] = []
            text = _fragment_text(root, a, comp)
            if text:
                for tok in callouts.XREF_RE.findall(
                        callouts.blank_fences(text)):
                    if "/" in tok:
                        targets.append((tok, "token"))
            for u in comp.get("upstream") or []:
                if "/" in str(u):
                    targets.append((str(u), "upstream"))
            for tgt, how in dict.fromkeys(targets):
                ta, ts = tgt.split("/", 1)
                dangling = ta not in known or ts not in known.get(ta, set())
                mark = "  [DANGLING — reconcile blocks the holder]" \
                    if dangling else ""
                spine.append(f"  {holder}  --{how}-->  {tgt}{mark}")
                if not dangling and ta != a:
                    seams.setdefault((a, ta), []).append((holder, tgt, how))
    for (a, b), entries in sorted(seams.items()):
        if (b, a) not in seams:
            findings.append(
                f"  - asymmetric seam: {a} declares toward {b} "
                f"({len(entries)}) but {b} declares nothing toward {a} — "
                f"expected during mixed scoping; fix with an incremental "
                f"taxonomy pass on {b}")
    return spine, findings


def _print_intake_block(root: Path) -> None:
    # M25 — intake is LOUD until empty: unprocessed and parked evidence can
    # never silently sit (the no-silent-caps standard applied to evidence).
    # Printed BEFORE the two-areas early return: a greenfield engagement (no
    # scoped areas yet) is exactly when staged fieldwork must not be silent
    # (v1.17.1 fix — the first local run found the audit mute on 13 files).
    unprocessed, parked = intake_status(root)
    if unprocessed or parked:
        print(f"\nINTAKE — {len(unprocessed)} unprocessed, "
              f"{len(parked)} parked:")
        for name in unprocessed:
            print(f"  unprocessed: {name}  (run the intake classifier, or "
                  f"route/park by hand)")
        for name, why in parked:
            print(f"  parked: {name} — {why}")


def audit(root: Path) -> int:
    areas = _areas(root)
    if len(areas) < 2:
        print(f"{root}: {len(areas)} area(s) found — the audit needs at "
              f"least two scoped areas under one components/ dir. If your "
              f"L1s live in separate folders, move each one under a single "
              f"engagement components/ directory first.")
        _print_intake_block(root)
        return 2 if not areas else 0
    print(f"ENGAGEMENT AUDIT — {len(areas)} areas under {root}: "
          + ", ".join(a for a, _ in areas))
    _print_intake_block(root)

    lines: list[str] = []
    n1 = twin_l3s(areas, lines)
    print(f"\n1. TWIN L3s — same activity scoped in two areas: {n1}")
    for ln in lines:
        print(ln)
    if n1:
        print("   fix: the human names the owner; the other area's "
              "procedure is retired (taxonomy retirement flow) or its "
              "drafter reduces it to the owner's handoff")

    lines = []
    n2 = cross_mentions(root, areas, lines)
    print(f"\n2. CROSS-AREA MENTIONS — prose naming another area's "
          f"procedure: {n2}")
    for ln in lines:
        print(ln)
    if n2:
        print("   fix: usually fine as ONE handoff sentence — flag only "
              "where the mention grew into documentation (see shape 3). "
              "Since the target is scoped, upgrade the mention to a "
              "[[area/slug]] token (M26): checkable identity instead of "
              "prose the audit must guess at")

    lines = []
    n3 = shared_prose(root, areas, lines)
    print(f"\n3. SHARED PROSE — fragment pairs sharing {_SHINGLE_K}-word "
          f"runs across areas (verbatim or paraphrased skeleton): {n3}")
    for ln in lines:
        print(ln)
    if n3:
        print("   fix: the human names the owning procedure; append a "
              "`kind: review` note to the OTHER procedure's notes bus "
              "naming the owner ('reduce to a handoff sentence'), then run "
              "its area's apply_review pass")

    n4, lines = open_gap_register(root, areas)
    print(f"\n4. OPEN GAPS — the engagement's unanswered questions, "
          f"by area: {n4}")
    for ln in lines:
        print(ln)
    if n4:
        print("   fix: many are answered elsewhere in the engagement or "
              "belong in a shared register — run the placement pass "
              "(engagement.py brief) before sending them to process owners")

    spine, seam_findings = interface_spine(root, areas)
    print(f"\n5. INTERFACES — the engagement spine, derived from "
          f"[[area/slug]] tokens and cross-area upstream declarations: "
          f"{len(spine)}")
    for ln in spine:
        print(ln)
    for ln in seam_findings:
        print(ln)
    if not spine:
        print("   (none declared yet — seams are still prose-only; see "
              "section 2 for upgrade candidates)")

    total = n1 + n2 + n3
    print(f"\n{total} duplication finding(s) · {n4} open gap(s) · "
          f"{len(spine)} declared interface(s)."
          if (total or n4 or spine) else "\nClean: no cross-area "
          "duplication, no open gaps, no declared interfaces.")
    return 0


#: M24 `--full` size guard: a rough chars/4 token estimate over every
#: fragment. One strong agent comfortably reads a 4-L1 engagement in full
#: (~150–250k tokens); past the budget the brief recommends digest mode or
#: area-pair splits instead of silently overrunning the reader's context.
_FULL_READ_TOKEN_BUDGET = 300_000


def placement_brief(root: Path, full: bool = False) -> int:
    """The work order for the single knowledge-placement agent (M24).

    `full` (the field-finding fix): list whole fragment paths instead of
    Scope-only digests — gap answers live in step bodies, and the digest
    under-recalled on the first real engagement. The migration instrument
    for legacy prose and the periodic deep sweep."""
    areas = _areas(root)
    if len(areas) < 2:
        print(f"{root}: {len(areas)} area(s) — the placement pass needs at "
              f"least two areas under one components/ dir.")
        return 2 if not areas else 0
    print(f"WORK ORDER — knowledge-placement pass "
          f"({'FULL READ' if full else 'digest'}) · {root}")
    print("  read-only pass: you write NOTHING except through the two "
          "commands below — findings become notes; register content and "
          "adoptions are executed on the notes' say-so, never by you")
    print(f"  {len(areas)} areas: " + ", ".join(a for a, _ in areas))
    print()
    print("THE RULE — every fact has exactly ONE home. You route each "
          "finding (a duplication OR a gap another area answers) to ONE "
          "move, decided by the CLASS of the fact:")
    print("  - reduce to handoff — the work is owned by another L1: the "
          "non-owner keeps one sentence naming the owner's procedure")
    print("  - promote to register — the fact is SHARED and RECURRING "
          "(approval threshold, date/cutoff rule, system-of-record, master "
          "data, report definition): it belongs ONCE in "
          "components/_client/registers/, referenced everywhere. THE "
          "PRIMARY MOVE for recurring facts — adopting or restating "
          "shared-fact prose is the anti-pattern")
    print("  - adopt as source — one-off only: another area's SOURCED "
          "documentation genuinely answers a question inside this area's "
          "own scope")
    print("  - NONE OF THE ABOVE — a POLICY, CONTROL-DESIGN or SYSTEM-"
          "CONFIGURATION question (should a review exist? what should the "
          "threshold be?) is reported in your status, unresolved. No "
          "component may close it with prose.")
    print()
    print("TRIAGE QUESTIONS (ask per finding): owned by another L1? "
          "volatile shared data 2+ areas keep needing? one-off evidence "
          "match? does the downstream area need the calculation, or only "
          "the approved output? Report-don't-guess: a match you cannot "
          "place confidently rides back in your status, never the bus.")
    print()
    print("YOUR TWO COMMANDS:")
    print(f"  python3 <plugin>/scripts/engagement.py note "
          f"{root.parent / root.name}/<area> --slug <slug> --note "
          f"\"reduce to handoff; owner is <area>/[[slug]]\"")
    print(f"  (adopt is NAMED IN A NOTE, never run by you: include the "
          f"exact command — python3 <plugin>/scripts/engagement.py adopt "
          f"{root}/<area> --from <area>/<slug> --touches <slug> — in the "
          f"note text; the orchestrator runs it)")
    print()
    import registers as registers_mod
    regs = registers_mod.load_all(root)
    if regs:
        print("ENGAGEMENT REGISTERS (existing — propose ENTRIES as "
              "`<register>#<entry-id>` in your status, each with class "
              "(citable|context), text, provenance (per-area SRC ids + "
              "origin area) and the restating procedures; "
              "reference-don't-restate is the drafters' rule):")
        for p, title, entries in regs:
            if entries is None:
                print(f"  - {p}  (unstructured, pre-M30)")
                continue
            print(f"  - {p}  ({title})")
            for e in entries:
                print(f"      {p.stem}#{e.id}  [{e.cls}]  "
                      f"{registers_mod.first_line(e.text)}")
    else:
        print("ENGAGEMENT REGISTERS: none yet — propose the register name, "
              "entry ids (`<register>#<entry-id>`), class, text and "
              "provenance in your status (the human's word creates them "
              "via `engagement.py register add`)")
    print()
    print("MECHANICAL FINDINGS (script-computed — your judgment starts "
          "from these, it does not re-derive them):")
    lines: list[str] = []
    n1 = twin_l3s(areas, lines)
    print(f"  twin L3s: {n1}")
    for ln in lines:
        print(ln)
    lines = []
    n2 = cross_mentions(root, areas, lines)
    print(f"  cross-area mentions: {n2}")
    for ln in lines:
        print(ln)
    lines = []
    n3 = shared_prose(root, areas, lines)
    print(f"  shared prose: {n3}")
    for ln in lines:
        print(ln)
    spine, seam_findings = interface_spine(root, areas)
    print(f"  declared interfaces (M26 spine — seams already DECLARED; "
          f"your matching work starts where these end): {len(spine)}")
    for ln in spine + seam_findings:
        print(ln)
    n4, lines = open_gap_register(root, areas)
    print(f"\nOPEN GAP REGISTER ({n4} gap(s)):")
    for ln in lines:
        print(ln)
    print()
    if full:
        total_chars = 0
        blocks: list[str] = []
        for a, m in areas:
            blocks.append(f"  ── area {a} — {m.get('title', a)}")
            for comp in _procedures(m):
                p = root / a / comp.get("file", "")
                try:
                    total_chars += p.stat().st_size
                except OSError:
                    pass
                blocks.append(f"    [[{comp.get('slug', '?')}]] — "
                              f"{comp.get('heading', '')}  → READ IN FULL: "
                              f"{p}")
        est = total_chars // 4
        print(f"FRAGMENTS — FULL READ (M24 --full: gap answers live in "
              f"step bodies, not Scope digests). Read EVERY file below "
              f"whole (~{est:,} tokens est.):")
        if est > _FULL_READ_TOKEN_BUDGET:
            print(f"  SIZE GUARD: ~{est:,} tokens exceeds the single-read "
                  f"budget (~{_FULL_READ_TOKEN_BUDGET:,}). Recommend digest "
                  f"mode (drop --full), or run --full per area PAIR "
                  f"(smaller engagements read whole; this one has "
                  f"outgrown one context).")
        for ln in blocks:
            print(ln)
    else:
        print("AREA DIGESTS (procedure titles + Scope sections — your read "
              "of the areas; a finding that needs a full fragment names it "
              "in your status instead. Legacy/mixed-version prose? use "
              "--full):")
        for a, m in areas:
            print(f"  ── area {a} — {m.get('title', a)}")
            for comp in _procedures(m):
                print(f"    [[{comp.get('slug', '?')}]] — "
                      f"{comp.get('heading', '')}")
                for ln in _scope_digest(root, a, comp):
                    print(ln)
    print()
    print("WHAT YOU RETURN (COMPACT): findings per move; register "
          "proposals (file, key, suggested content, which procedures "
          "currently restate it); policy/control items (unresolved); "
          "unmatched gaps count; needs_full_read. Never paste digests or "
          "fragment text back.")
    return 0


def adopt(area: Path, from_ref: str, touches: list[str]) -> int:
    """Register another area's drafted fragment as a second-hand source
    (M24 'prose as source', made literal). Copies the fragment into
    _sources/new/, appends a hash-stamped sources.yaml entry, and queues a
    `kind: source` note per touched procedure — the ordinary apply_review
    loop does the rest. Idempotent at the content hash."""
    import notes_util
    import sources as sources_mod
    try:
        import yaml
    except ImportError:
        print("error: pyyaml is required for adopt", file=sys.stderr)
        return 2
    manifest = area / "manifest.json"
    if not manifest.is_file():
        print(f"error: {area} has no manifest.json — pass the AREA folder",
              file=sys.stderr)
        return 2

    # The sticky-hold brake (M17): enforced at the verb, since the advisor
    # never schedules adopt. `hold: [adopt]` in either _client layer wins.
    import client_config
    held = client_config.holds(str(area), holdable=("adopt",))
    if "adopt" in held:
        print(f"held: adopt ({held.layer_label()}) — this engagement "
              f"requires a human to pre-approve source adoption. Edit the "
              f"hold: list in _client/consult.yaml to release. Nothing "
              f"was written.", file=sys.stderr)
        return 3

    m = re.fullmatch(r"([^/]+)/([^/]+)", from_ref or "")
    if not m:
        print("error: --from takes <area>/<slug>, e.g. "
              "procure-to-pay/goods-receipt", file=sys.stderr)
        return 2
    from_area, from_slug = m.group(1), m.group(2)
    src_area = area.resolve().parent / from_area
    src_manifest = src_area / "manifest.json"
    if not src_manifest.is_file():
        print(f"error: no area {from_area!r} beside {area.name} "
              f"(looked at {src_area})", file=sys.stderr)
        return 2
    src_m = json.loads(src_manifest.read_text(encoding="utf-8"))
    comp = next((c for c in src_m.get("components", [])
                 if c.get("role") == "procedure"
                 and c.get("slug") == from_slug), None)
    if comp is None:
        known = ", ".join(sorted(c.get("slug", "?")
                                 for c in src_m.get("components", [])
                                 if c.get("role") == "procedure"))
        print(f"error: no procedure {from_slug!r} in {from_area} "
              f"(known: {known})", file=sys.stderr)
        return 2
    frag = src_area / comp.get("file", "")
    if not frag.is_file():
        print(f"error: {frag} is missing", file=sys.stderr)
        return 2

    slugs = {c.get("slug") for c in
             json.loads(manifest.read_text(encoding="utf-8"))
             .get("components", []) if c.get("role") == "procedure"}
    bad = [t for t in touches if t not in slugs]
    if bad:
        print(f"error: --touches slug(s) not in {area.name}: "
              f"{', '.join(bad)} "
              f"(known: {', '.join(sorted(s for s in slugs if s))})",
              file=sys.stderr)
        return 2
    if not touches:
        print("error: --touches requires at least one procedure slug (the "
              "gap's home — who reads the adopted source)", file=sys.stderr)
        return 2

    content = frag.read_bytes()
    import hashlib
    digest = hashlib.sha256(content).hexdigest()

    try:
        data = sources_mod._load_sources(str(area))
    except FileNotFoundError:
        # A legacy/minimal area with no sources.yaml yet — adopt may be its
        # very first source; start the ledger rather than refusing.
        data = {"sources": []}
    if not isinstance(data, dict):
        data = {"sources": []}
    (area / "_reference").mkdir(parents=True, exist_ok=True)
    entries = data.setdefault("sources", [])
    existing = next((e for e in entries if isinstance(e, dict)
                     and e.get("hash") == digest), None)
    if existing:
        sid = existing.get("id", "?")
        print(f"already adopted (hash match) as {sid} — no-op")
    else:
        nums = [int(mm.group(1)) for e in entries if isinstance(e, dict)
                for mm in [re.fullmatch(r"SRC-(\d+)",
                                        str(e.get("id", "")))] if mm]
        sid = f"SRC-{(max(nums) + 1 if nums else 1):03d}"
        rel = f"_sources/new/adopted-{from_area}-{from_slug}.md"
        dest = area / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        entries.append({
            "id": sid, "file": rel, "touches": list(touches),
            "hash": digest, "state": "new",
            "note": (f"internal: drafted {from_area} procedure "
                     f"'{comp.get('heading', from_slug)}' adopted as a "
                     f"second-hand source (M24). Frozen copy — the living "
                     f"text is {from_area}/{comp.get('file', '')}."),
        })
        sources_mod._dump_sources(str(area), data)
        print(f"adopted {from_area}/{from_slug} → {dest}  ({sid}, "
              f"hash-stamped, state: new)")

    queued = 0
    for t in touches:
        queued += notes_util.append_items(area, t, [{
            "kind": "source", "src": sid,
            "note": (f"adopted second-hand source from {from_area}/"
                     f"[[{from_slug}]] — read it and close the gap(s) it "
                     f"answers, citing {sid}; if it conflicts with your "
                     f"existing sources, keep the GAP and say so"),
            "source": "adopt",
        }])
    print(f"queued {queued} source note(s) on: {', '.join(touches)} — the "
          f"ordinary apply_review loop dispatches the drafter(s)")
    return 0


def add_note(area: Path, slug: str, note: str) -> int:
    """Queue a `kind: review` item on a procedure's notes bus — the
    sanctioned fix path for audit findings ('reduce X to a handoff sentence;
    owner is <area>/<slug>'). Goes through notes_util.append_items, so it is
    validated and idempotent like every other producer."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import notes_util
    manifest = area / "manifest.json"
    if not manifest.is_file():
        print(f"error: {area} has no manifest.json — pass the AREA folder",
              file=sys.stderr)
        return 2
    slugs = {c.get("slug") for c in
             json.loads(manifest.read_text(encoding="utf-8"))
             .get("components", []) if c.get("role") == "procedure"}
    if slug not in slugs:
        print(f"error: unknown slug {slug!r} in {area} "
              f"(known: {', '.join(sorted(s for s in slugs if s))})",
              file=sys.stderr)
        return 2
    added = notes_util.append_items(area, slug,
                                    [{"kind": "review", "note": note}])
    print(f"{'queued 1 review note' if added else 'already queued (no-op)'} "
          f"for {slug} — the area's apply_review pass consumes it")
    return 0


# --------------------------------------------------------------------------- #
# M25 — intake: ONE drop point, deterministic route/park (the only writers)
#
# `intake/` sits at the engagement root (sibling of components/). route COPIES
# a staged document into each target area's `_sources/new/` and writes NOTHING
# else — no sources.yaml entry, no hash stamp (M6 contract: a hash at the
# file's current content means "already assessed" at guard 5, so pre-stamping
# would silently skip source assessment and strand the source). The per-area
# relevance pointer is a SIDECAR (`<copy>.route.md`) that scaffold's
# stamp_sources folds into the entry's `note:` at confirm, so it reaches the
# drafter's brief. park moves a file to intake/parked/ with a stated reason.
# The folder state is self-describing: top level = unprocessed, parked/ =
# awaiting a human, nothing is ever deleted.
# --------------------------------------------------------------------------- #

ROUTE_SIDECAR_SUFFIX = ".route.md"


def _sha256_file(path: Path) -> str:
    import hashlib
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _intake_context(file: Path) -> tuple[Path, Path]:
    """(engagement root, components dir) for a staged intake file, or raise
    SystemExit(2). The file must sit at intake/ TOP LEVEL (routed/ and
    parked/ files are already processed)."""
    file = file.resolve()
    if file.parent.name != "intake" or not file.is_file():
        print(f"error: {file} is not a top-level file in an intake/ folder "
              f"(already routed/parked files are not re-routable — copy "
              f"back to intake/ top level to redo)", file=sys.stderr)
        raise SystemExit(2)
    engroot = file.parent.parent
    comps = engroot / "components"
    return engroot, comps


def _ledger_hashes(area: Path) -> set[str]:
    """Content hashes sources.yaml already knows — the by-content half of
    route's idempotency (a re-dropped file whose bytes are already registered
    is a no-op, even after the copy moved to _sources/processed/)."""
    p = area / "_reference" / "sources.yaml"
    if not p.is_file():
        return set()
    try:
        import yaml
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()
    return {str(e.get("hash") or "") for e in (data.get("sources") or [])
            if isinstance(e, dict)} - {""}


def route(file: Path, to_areas: list[str], pointers: dict[str, str],
          new_area: bool = False) -> int:
    """Copy a staged intake file to each target area's _sources/new/, write
    pointer sidecars, move the original to intake/routed/. File copies ONLY —
    the ordinary assess/confirm flow does everything else."""
    engroot, comps = _intake_context(file)
    if not to_areas:
        print("error: route requires --to <area>[,<area>...]", file=sys.stderr)
        return 2
    known = {d.name for d in comps.iterdir()
             if d.is_dir() and not d.name.startswith(("_", "."))} \
        if comps.is_dir() else set()
    for aname in to_areas:
        if aname not in known and not new_area:
            print(f"error: no area {aname!r} under {comps} (known: "
                  f"{', '.join(sorted(known)) or 'none'}). A not-yet-scoped "
                  f"area is created only on HUMAN direction: re-run with "
                  f"--new-area. The classifier parks instead.",
                  file=sys.stderr)
            return 2
    digest = _sha256_file(file)
    lines = []
    for aname in to_areas:
        area = comps / aname
        new_dir = area / "_sources" / "new"
        new_dir.mkdir(parents=True, exist_ok=True)
        dest = new_dir / f"intake-{file.name}"
        if dest.is_file():
            if _sha256_file(dest) == digest:
                lines.append(f"  {aname}: already present (no-op)")
            else:
                print(f"error: {dest} exists with DIFFERENT content — "
                      f"never overwritten; rename the intake file",
                      file=sys.stderr)
                return 2
        elif digest and digest in _ledger_hashes(area):
            lines.append(f"  {aname}: content already in the source ledger "
                         f"(no-op)")
        else:
            import shutil
            shutil.copy2(file, dest)
            lines.append(f"  {aname}: → {dest.relative_to(engroot)}")
        pointer = pointers.get(aname)
        if pointer:
            side = Path(str(dest) + ROUTE_SIDECAR_SUFFIX)
            side.write_text(pointer.strip() + "\n", encoding="utf-8")
            lines.append(f"  {aname}: pointer sidecar "
                         f"{side.name} (folded into sources.yaml note: at "
                         f"confirm)")
    routed = file.parent / "routed"
    routed.mkdir(exist_ok=True)
    import shutil
    shutil.move(str(file), str(routed / file.name))
    with (routed / "manifest.log").open("a", encoding="utf-8") as fh:
        fh.write(f"{file.name} -> {', '.join(to_areas)}\n")
    print(f"routed {file.name} -> {', '.join(to_areas)}")
    for ln in lines:
        print(ln)
    return 0


def park(file: Path, reason: str) -> int:
    _intake_context(file)
    if not (reason or "").strip():
        print("error: park requires --reason (parked is LOUD by contract — "
              "a file nobody can place still says why)", file=sys.stderr)
        return 2
    parked = file.parent / "parked"
    parked.mkdir(exist_ok=True)
    import shutil
    shutil.move(str(file), str(parked / file.name))
    with (parked / "reasons.log").open("a", encoding="utf-8") as fh:
        fh.write(f"{file.name} — {reason.strip()}\n")
    print(f"parked {file.name} — {reason.strip()}")
    return 0


def intake_status(components_root: Path) -> tuple[list[str],
                                                  list[tuple[str, str]]]:
    """(unprocessed names, [(parked name, reason)]) — empty lists when there
    is no intake/ folder beside components/."""
    intake = components_root.resolve().parent / "intake"
    if not intake.is_dir():
        return [], []
    unprocessed = sorted(p.name for p in intake.iterdir()
                         if p.is_file() and not p.name.startswith("."))
    reasons: dict[str, str] = {}
    rlog = intake / "parked" / "reasons.log"
    if rlog.is_file():
        for ln in rlog.read_text(encoding="utf-8").splitlines():
            name, _, why = ln.partition(" — ")
            if name:
                reasons[name.strip()] = why.strip()
    parked_dir = intake / "parked"
    parked = [(p.name, reasons.get(p.name, "(no reason recorded)"))
              for p in sorted(parked_dir.iterdir())
              if parked_dir.is_dir() and p.is_file()
              and not p.name.startswith(".") and p.name != "reasons.log"] \
        if parked_dir.is_dir() else []
    return unprocessed, parked


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["register"]:
        # M30 — the register verb lives in registers.py (own parser: its
        # flag set does not overlap this one's); dispatched here so the
        # documented entry point stays engagement.py.
        import registers
        return registers.main(argv[1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["audit", "brief", "note", "adopt",
                                        "route", "park"])
    ap.add_argument("root", nargs="?", default="components",
                    help="audit/brief: the engagement components/ dir "
                         "(default: ./components); note/adopt: the AREA "
                         "folder; route/park: the staged intake/<file>")
    ap.add_argument("--slug", help="note: procedure slug to queue on")
    ap.add_argument("--note", help="note: the review instruction text")
    ap.add_argument("--from", dest="from_ref",
                    help="adopt: <area>/<slug> to adopt as a source")
    ap.add_argument("--touches", nargs="+", default=[],
                    help="adopt: procedure slug(s) in the target area that "
                         "read the adopted source")
    ap.add_argument("--to", default="",
                    help="route: comma-separated target area name(s)")
    ap.add_argument("--note-for", dest="note_for", nargs=2, action="append",
                    default=[], metavar=("AREA", "TEXT"),
                    help="route: per-area relevance pointer (repeatable) — "
                         "written as a sidecar the confirm step folds into "
                         "sources.yaml note:")
    ap.add_argument("--new-area", action="store_true",
                    help="route: allow a not-yet-scoped target area (HUMAN "
                         "direction only — the classifier parks instead)")
    ap.add_argument("--reason", default="",
                    help="park: why no scoped area can take this file")
    ap.add_argument("--full", action="store_true",
                    help="brief: list whole fragment paths instead of Scope "
                         "digests (the M24 deep-sweep / legacy-migration "
                         "read; a size guard warns past the token budget)")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.command in ("route", "park"):
        try:
            if a.command == "route":
                return route(root,
                             [s.strip() for s in a.to.split(",")
                              if s.strip()],
                             {area: text for area, text in a.note_for},
                             new_area=a.new_area)
            return park(root, a.reason)
        except SystemExit as exc:   # _intake_context fails loud with code 2
            return exc.code if isinstance(exc.code, int) else 2
    if a.command == "note":
        if not a.slug or not a.note:
            print("error: note requires --slug and --note", file=sys.stderr)
            return 2
        return add_note(root, a.slug, a.note)
    if a.command == "adopt":
        if not a.from_ref:
            print("error: adopt requires --from <area>/<slug>",
                  file=sys.stderr)
            return 2
        return adopt(root, a.from_ref, list(a.touches))
    if not root.is_dir():
        print(f"error: {root} is not a directory — run from the engagement "
              f"root (the folder containing components/)", file=sys.stderr)
        return 2
    return placement_brief(root, full=a.full) if a.command == "brief" \
        else audit(root)


if __name__ == "__main__":
    raise SystemExit(main())
