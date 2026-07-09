#!/usr/bin/env python3
"""
review_extract.py — Pull reviewer markup out of a rendered CONSULT .docx and turn
it into procedure-anchored review notes the consult-drafter (update mode) consumes.

The .docx is a *generated view* (M4 renders it); the Markdown procedure fragments
are the source of truth. We do NOT reverse-apply Word edits into the source — that
is the classic brittle round-trip. Instead we EXTRACT tracked changes + comments as
anchored feedback and let the drafter apply them with judgment.

What it does
------------
1. Open the .docx (a zip of XML) and parse, directly:
     - word/document.xml  — inline w:ins / w:del tracked changes (author + date) and
       commentRangeStart/End spans; the heading stack (H1 title, H2 section,
       H3 = A-H subsection, H4 = step).
     - word/comments.xml   — the comment bodies (text, author, date), keyed by id.
   python-docx does not expose tracked changes or comments, so we go to the XML.
   lxml is preferred; we fall back to xml.etree.ElementTree if lxml is absent.
2. Walk the heading stack while parsing and attribute every change/comment to
     procedure  ->  A-H subsection  ->  step,  with the exact anchor text.
   The H2 procedure heading carries its display number + title; we map it back to
   the stable `slug` via the folder manifest (doc_model.display_numbers).
3. Write ONE notes file per procedure that has feedback:
     {area}/_review/{slug}.notes.yaml
   A single reviewed .docx spans many procedures; we split the feedback by the
   procedure each item is anchored to. The filename IS the routing key the
   orchestrator uses to dispatch consult-drafter (mode: update) per slug.
4. Archive the consumed .docx to {area}/_review/processed/.

CLI
---
  python3 scripts/review_extract.py <reviewed.docx> [--area <area-folder>]
                                     [--no-archive] [--dry-run]

Notes land in _review/, never _sources/new/ — the folder is the routing signal
(review notes are content corrections to existing procedures; taxonomy is skipped).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# doc_model spine (OWNED BY M2). We import the shared helpers so numbers<->slugs
# map through the single authority. If M2's module is not on the path yet, we
# fall back to a minimal manifest reader + the documented number formula so this
# script stays runnable/testable standalone; doc_model remains the source of
# truth once present. (See the contract note in the ticket.)
# --------------------------------------------------------------------------- #
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from doc_model import load_manifest, display_numbers  # type: ignore
except Exception:  # pragma: no cover - exercised only until M2 lands
    import json

    def load_manifest(folder) -> dict:
        p = Path(folder) / "manifest.json"
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def display_numbers(manifest: dict) -> Dict[str, str]:
        """Fallback mirror of doc_model.display_numbers: {slug: "L2.seq"}.

        L2-ordinal = 1-based index in manifest['l2_order']; activity seq = the
        procedure's 1-based `order` rank within that L2 bucket. Kept identical to
        the documented formula; doc_model supersedes this when importable.
        """
        l2_order = manifest.get("l2_order", [])
        l2_rank = {name: i + 1 for i, name in enumerate(l2_order)}
        procs = [c for c in manifest.get("components", []) if c.get("role") == "procedure"]
        by_l2: Dict[str, List[dict]] = {}
        for c in procs:
            by_l2.setdefault(c.get("l2"), []).append(c)
        out: Dict[str, str] = {}
        for l2, comps in by_l2.items():
            comps.sort(key=lambda c: c.get("order", 0))
            ord2 = l2_rank.get(l2, len(l2_order) + 1)
            for seq, c in enumerate(comps, start=1):
                if c.get("slug"):
                    out[c["slug"]] = f"{ord2}.{seq}"
        return out


# --------------------------------------------------------------------------- #
# XML backend abstraction (lxml preferred, stdlib fallback)
# --------------------------------------------------------------------------- #
try:
    from lxml import etree as ET  # type: ignore

    _LXML = True
except Exception:  # pragma: no cover
    import xml.etree.ElementTree as ET  # type: ignore

    _LXML = False

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def wq(name: str) -> str:
    """{ns}name for the wordprocessingml namespace."""
    return f"{{{W}}}{name}"


def localname(el) -> str:
    tag = el.tag
    if not isinstance(tag, str):  # comments/PIs in lxml
        return ""
    return tag.rsplit("}", 1)[-1]


def parse_xml(data: bytes):
    if _LXML:
        return ET.fromstring(data)
    return ET.fromstring(data)


# --------------------------------------------------------------------------- #
# Text gathering helpers
# --------------------------------------------------------------------------- #
def gather_visible_text(el) -> str:
    """All w:t under `el` (inserted text included, deleted text excluded)."""
    parts: List[str] = []
    for t in el.iter():
        if localname(t) == "t" and t.text:
            parts.append(t.text)
    return "".join(parts)


def gather_ins_text(el) -> str:
    return "".join(t.text or "" for t in el.iter() if localname(t) == "t")


def gather_del_text(el) -> str:
    return "".join(t.text or "" for t in el.iter() if localname(t) == "delText")


def squeeze(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def clip(s: str, n: int = 160) -> str:
    s = squeeze(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


# --------------------------------------------------------------------------- #
# Heading / location model
# --------------------------------------------------------------------------- #
HEADING_RE = re.compile(r"heading\s*([1-9])", re.I)
NUMBER_PREFIX_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)[\.\)]?\s+(.*)$")
SUBSECTION_LETTER_RE = re.compile(r"^\s*([A-H])\b")


def paragraph_heading_level(p) -> Optional[int]:
    """Return 1-4 if this w:p uses a Heading style, else None."""
    ppr = p.find(wq("pPr"))
    if ppr is None:
        return None
    pstyle = ppr.find(wq("pStyle"))
    if pstyle is None:
        return None
    val = pstyle.get(wq("val")) or ""
    m = HEADING_RE.search(val)
    if m:
        return int(m.group(1))
    return None


class Location:
    """Tracks the current procedure / subsection / step while walking."""

    def __init__(self):
        self.slug: Optional[str] = None
        self.section_heading: str = ""   # raw H2 text (procedure or other)
        self.subsection: str = ""        # raw H3 text
        self.step: str = ""              # raw H4 text

    def enter_h2(self, heading: str, slug: Optional[str]) -> None:
        self.section_heading = heading
        self.slug = slug
        self.subsection = ""
        self.step = ""

    def enter_h3(self, heading: str) -> None:
        self.subsection = heading
        self.step = ""

    def enter_h4(self, heading: str) -> None:
        self.step = heading

    def as_string(self) -> str:
        sub = ""
        if self.subsection:
            m = SUBSECTION_LETTER_RE.match(self.subsection)
            sub = m.group(1) if m else squeeze(self.subsection)
        parts = [p for p in (sub, squeeze(self.step)) if p]
        return " · ".join(parts) if parts else "(procedure body)"

    def snapshot(self) -> Tuple[Optional[str], str]:
        return (self.slug, self.as_string())


# --------------------------------------------------------------------------- #
# Slug resolution (docx heading -> manifest slug)
# --------------------------------------------------------------------------- #
def build_slug_maps(manifest: dict) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return (number->slug, normalized-title->slug)."""
    numbers = display_numbers(manifest)
    num2slug = {num: slug for slug, num in numbers.items()}
    title2slug: Dict[str, str] = {}
    for c in manifest.get("components", []):
        if c.get("role") == "procedure" and c.get("slug"):
            title2slug[squeeze(c.get("heading", "")).lower()] = c["slug"]
    return num2slug, title2slug


def resolve_slug(heading: str, num2slug: Dict[str, str], title2slug: Dict[str, str]) -> Optional[str]:
    """Map a rendered H2 heading ('1.1 Bank Reconciliation') back to its slug."""
    heading = squeeze(heading)
    m = NUMBER_PREFIX_RE.match(heading)
    title = heading
    if m:
        num, title = m.group(1), m.group(2)
        if num in num2slug:
            return num2slug[num]
    return title2slug.get(squeeze(title).lower())


# --------------------------------------------------------------------------- #
# Core: walk document.xml
# --------------------------------------------------------------------------- #
class Item:
    def __init__(self, kind: str, slug: Optional[str], location: str,
                 anchor: str, author: str, date: str,
                 change: str = "", note: str = ""):
        self.kind = kind          # 'tracked-change' | 'comment'
        self.slug = slug
        self.location = location
        self.anchor = anchor
        self.author = author
        self.date = date
        self.change = change
        self.note = note


def _run_events(p) -> List[Tuple[str, str, str, str]]:
    """Ordered (op, text, author, date) tuples for w:ins / w:del in a paragraph.

    op is 'ins' or 'del'. Adjacent del->ins pairs are later collapsed into a
    single 'X -> Y' replacement.
    """
    events: List[Tuple[str, str, str, str]] = []

    def walk(el):
        for child in el:
            ln = localname(child)
            if ln == "ins":
                txt = gather_ins_text(child)
                if txt.strip():
                    events.append(("ins", txt, child.get(wq("author")) or "",
                                   child.get(wq("date")) or ""))
                # do not recurse: its runs are captured
            elif ln == "del":
                txt = gather_del_text(child)
                if txt.strip():
                    events.append(("del", txt, child.get(wq("author")) or "",
                                   child.get(wq("date")) or ""))
            else:
                walk(child)

    walk(p)
    return events


def _collapse_changes(events: List[Tuple[str, str, str, str]]) -> List[Tuple[str, str, str]]:
    """Collapse adjacent del->ins into a replacement. Return (change, author, date)."""
    out: List[Tuple[str, str, str]] = []
    i = 0
    while i < len(events):
        op, txt, author, date = events[i]
        if op == "del" and i + 1 < len(events) and events[i + 1][0] == "ins":
            _, ins_txt, ins_author, ins_date = events[i + 1]
            out.append((f"{squeeze(txt)} → {squeeze(ins_txt)}",
                        ins_author or author, ins_date or date))
            i += 2
            continue
        if op == "ins":
            out.append((f"inserted: {squeeze(txt)}", author, date))
        else:
            out.append((f"deleted: {squeeze(txt)}", author, date))
        i += 1
    return out


def extract_document(doc_root, comments: Dict[str, dict],
                     num2slug: Dict[str, str], title2slug: Dict[str, str],
                     warnings: List[str]) -> List[Item]:
    body = None
    for el in doc_root.iter():
        if localname(el) == "body":
            body = el
            break
    if body is None:
        return []

    loc = Location()
    items: List[Item] = []
    # Comment ranges can span paragraphs: id -> {loc: (slug, locstr), anchor: [texts]}
    open_comments: Dict[str, dict] = {}
    seen_comment_ids: set = set()

    for p in body:
        if localname(p) != "p":
            continue

        level = paragraph_heading_level(p)
        para_text = gather_visible_text(p)

        if level is not None:
            if level == 2:
                slug = resolve_slug(para_text, num2slug, title2slug)
                loc.enter_h2(para_text, slug)
            elif level == 3:
                loc.enter_h3(para_text)
            elif level == 4:
                loc.enter_h4(para_text)
            # H1 = document title; ignore for attribution.
            # Headings themselves rarely carry markup; still scan them below.

        # --- comment range starts/ends + span-text accrual (document order) ---
        def walk_comments(el):
            for child in el:
                ln = localname(child)
                if ln == "commentRangeStart":
                    cid = child.get(wq("id"))
                    if cid is not None:
                        open_comments[cid] = {"loc": loc.snapshot(), "anchor": []}
                elif ln == "commentRangeEnd":
                    cid = child.get(wq("id"))
                    if cid in open_comments:
                        _finalize_comment(cid)
                elif ln == "t" and child.text:
                    for rec in open_comments.values():
                        rec["anchor"].append(child.text)
                    walk_comments_leaf(child)
                else:
                    walk_comments(child)

        def walk_comments_leaf(_el):
            return  # w:t has no element children we care about

        def _finalize_comment(cid: str):
            rec = open_comments.pop(cid)
            if cid in seen_comment_ids:
                return
            seen_comment_ids.add(cid)
            body_txt = comments.get(cid, {})
            slug, locstr = rec["loc"]
            if slug is None:
                warnings.append(
                    f"comment id={cid} anchored outside any procedure "
                    f"(section: {loc.section_heading or '?'}); skipped")
                return
            items.append(Item(
                kind="comment", slug=slug, location=locstr,
                anchor=clip("".join(rec["anchor"])) or clip(para_text),
                author=body_txt.get("author", ""),
                date=body_txt.get("date", ""),
                note=squeeze(body_txt.get("text", "")),
            ))

        walk_comments(p)

        # --- tracked changes in this paragraph ---
        events = _run_events(p)
        if events:
            anchor = clip(para_text) or clip("; ".join(t for _, t, _, _ in events))
            for change, author, date in _collapse_changes(events):
                if loc.slug is None:
                    warnings.append(
                        f"tracked change '{clip(change, 60)}' outside any procedure "
                        f"(section: {loc.section_heading or '?'}); skipped")
                    continue
                items.append(Item(
                    kind="tracked-change", slug=loc.slug, location=loc.as_string(),
                    anchor=anchor, author=author, date=date, change=change,
                ))

    # Any comment ranges that never closed (missing End): finalize at doc end.
    for cid in list(open_comments.keys()):
        rec = open_comments.pop(cid)
        if cid in seen_comment_ids:
            continue
        seen_comment_ids.add(cid)
        slug, locstr = rec["loc"]
        if slug is None:
            warnings.append(f"comment id={cid} (unterminated range) outside any procedure; skipped")
            continue
        body_txt = comments.get(cid, {})
        items.append(Item(
            kind="comment", slug=slug, location=locstr,
            anchor=clip("".join(rec["anchor"])),
            author=body_txt.get("author", ""), date=body_txt.get("date", ""),
            note=squeeze(body_txt.get("text", "")),
        ))

    return items


def parse_comments(data: Optional[bytes]) -> Dict[str, dict]:
    if not data:
        return {}
    root = parse_xml(data)
    out: Dict[str, dict] = {}
    for c in root.iter():
        if localname(c) != "comment":
            continue
        cid = c.get(wq("id"))
        if cid is None:
            continue
        # Preserve paragraph breaks in a comment body as spaces.
        paras: List[str] = []
        for p in c.iter():
            if localname(p) == "p":
                paras.append(gather_visible_text(p))
        text = " ".join(squeeze(x) for x in paras if x.strip())
        if not text:
            text = squeeze(gather_visible_text(c))
        out[cid] = {
            "author": c.get(wq("author")) or "",
            "date": c.get(wq("date")) or "",
            "text": text,
        }
    return out


# --------------------------------------------------------------------------- #
# YAML emission (dependency-free, controlled shape)
# --------------------------------------------------------------------------- #
def _yaml_scalar(v: str) -> str:
    """Emit a double-quoted YAML scalar (always safe for our free text)."""
    s = str(v)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").replace("\t", " ")
    return f'"{s}"'


def render_notes_yaml(slug: str, source_docx: str, items: List[Item]) -> str:
    lines: List[str] = []
    lines.append(f"# _review/{slug}.notes.yaml")
    lines.append("# Procedure-anchored review notes extracted from a reviewed .docx by")
    lines.append("# scripts/review_extract.py (M8). Consumed by consult-drafter (mode: update).")
    lines.append(f"procedure: {_yaml_scalar(slug)}")
    lines.append(f"source_docx: {_yaml_scalar(source_docx)}")
    lines.append("items:")
    for it in items:
        lines.append(f"  - type: {it.kind}")
        lines.append(f"    location: {_yaml_scalar(it.location)}")
        lines.append(f"    anchor: {_yaml_scalar(it.anchor)}")
        if it.kind == "tracked-change":
            lines.append(f"    change: {_yaml_scalar(it.change)}")
        else:
            lines.append(f"    note: {_yaml_scalar(it.note)}")
        if it.author:
            lines.append(f"    author: {_yaml_scalar(it.author)}")
        if it.date:
            lines.append(f"    date: {_yaml_scalar(it.date)}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def infer_area(docx_path: Path, area_arg: Optional[str]) -> Path:
    if area_arg:
        return Path(area_arg)
    parent = docx_path.parent
    # Dropped into {area}/_review/ (the normal path) -> area is its parent.
    if parent.name == "_review":
        return parent.parent
    if (parent / "manifest.json").exists():
        return parent
    return parent


def run(docx_path: Path, area_arg: Optional[str], archive: bool, dry_run: bool) -> int:
    if not docx_path.exists():
        print(f"error: file not found: {docx_path}", file=sys.stderr)
        return 2

    area = infer_area(docx_path, area_arg)
    manifest_path = area / "manifest.json"
    if not manifest_path.exists():
        print(f"error: no manifest.json under area '{area}' "
              f"(pass --area to point at the area folder)", file=sys.stderr)
        return 2

    manifest = load_manifest(area)
    num2slug, title2slug = build_slug_maps(manifest)

    with zipfile.ZipFile(docx_path) as z:
        names = set(z.namelist())
        if "word/document.xml" not in names:
            print("error: not a Word document (no word/document.xml)", file=sys.stderr)
            return 2
        doc_bytes = z.read("word/document.xml")
        comments_bytes = z.read("word/comments.xml") if "word/comments.xml" in names else None

    comments = parse_comments(comments_bytes)
    doc_root = parse_xml(doc_bytes)

    warnings: List[str] = []
    items = extract_document(doc_root, comments, num2slug, title2slug, warnings)

    # Group by slug, preserving document order.
    by_slug: Dict[str, List[Item]] = {}
    for it in items:
        by_slug.setdefault(it.slug, []).append(it)

    review_dir = area / "_review"
    written: List[str] = []
    for slug, its in sorted(by_slug.items()):
        content = render_notes_yaml(slug, docx_path.name, its)
        out = review_dir / f"{slug}.notes.yaml"
        if dry_run:
            print(f"--- {out} ---")
            print(content)
        else:
            review_dir.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
        written.append(f"{out} ({len(its)} item{'s' if len(its) != 1 else ''})")

    # Archive the consumed .docx.
    archived_to = None
    if archive and not dry_run:
        processed = review_dir / "processed"
        processed.mkdir(parents=True, exist_ok=True)
        dest = processed / docx_path.name
        if dest.resolve() != docx_path.resolve():
            if dest.exists():
                dest.unlink()
            shutil.move(str(docx_path), str(dest))
            archived_to = dest

    # Report.
    print(f"Reviewed doc: {docx_path.name}")
    print(f"Area:         {area}")
    print(f"Backend:      {'lxml' if _LXML else 'xml.etree'}")
    print(f"Items:        {len(items)} across {len(by_slug)} procedure(s)")
    for w in written:
        print(f"  wrote {w}")
    if archived_to:
        print(f"  archived .docx -> {archived_to}")
    if not by_slug:
        print("  (no attributable feedback found)")
    for w in warnings:
        print(f"  WARN: {w}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Extract Word tracked-changes + comments into procedure-anchored "
                    "review notes ({area}/_review/{slug}.notes.yaml).")
    ap.add_argument("docx", help="path to the reviewed .docx")
    ap.add_argument("--area", help="area folder (default: inferred from the docx path)")
    ap.add_argument("--no-archive", action="store_true",
                    help="do not move the consumed .docx into _review/processed/")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the notes instead of writing files (implies no archive)")
    a = ap.parse_args(argv)
    return run(Path(a.docx), a.area, archive=not a.no_archive, dry_run=a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
