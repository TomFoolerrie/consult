#!/usr/bin/env python3
"""docx_comments.py — extract tracked comments from a reviewed Word .docx.

Research spike (T30). A deterministic, stdlib-only helper that pulls **tracked
comments** out of a reviewed Word `.docx`, each re-associated with the body text
it anchors — the raw input the `consult-review-comment-resolver` needs.

python-docx does NOT expose comments, so this is raw OOXML work. We use only
`zipfile` + `xml.etree.ElementTree`.

OOXML approach
--------------
A `.docx` is a zip (an OPC package). Two parts matter here:

  * `word/comments.xml` — the comment store. Each `w:comment` carries `w:id`,
    `w:author`, `w:date`, and a body of `w:p`/`w:r`/`w:t` runs (the comment text).

  * `word/document.xml` — the body. A comment anchors a span of body text via a
    matched pair of empty marker elements that share the comment's id:
        <w:commentRangeStart w:id="0"/> ... runs ... <w:commentRangeEnd w:id="0"/>
    and a `w:commentReference w:id="0"` (usually inside a trailing run) marks
    where the comment balloon hangs. We walk document.xml in document order,
    and for each id accumulate the `w:t` text of every run that falls *between*
    its range start and range end — that is the anchored body span.

Tracked changes (`w:ins`/`w:del`) are surfaced best-effort as
`{type, author, date, text}` entries — see INCLUDE_TRACKED_CHANGES below.

Scope limitation: only `word/document.xml` is read. Comments anchored in
headers, footers, or footnotes (`word/header*.xml`, `word/footer*.xml`,
`word/footnotes.xml`) are **out of scope** and are NOT extracted (matches the
spike-level intent of T30). Reviewers should leave SOP comments in the document
body.

Usage
-----
  docx_comments.py extract --docx PATH [--json]

  - no comments        -> empty list, exit 0
  - non-docx / non-zip -> clear error, nonzero exit

Output (JSON list):
  [{id, author, date, comment, anchored_text, tracked_changes?}, ...]
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

# WordprocessingML main namespace.
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _q(tag: str) -> str:
    """Qualify a local name with the wordprocessingml namespace."""
    return f"{{{W}}}{tag}"


def _w(elem: ET.Element, attr: str) -> Optional[str]:
    """Read a w:-namespaced attribute off an element."""
    return elem.get(_q(attr))


def _local(tag: str) -> str:
    """Strip the namespace from a fully-qualified ElementTree tag."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _run_text(run: ET.Element) -> str:
    """Concatenate the visible text of a single `w:r` run.

    `w:t` is the literal text; `w:tab`/`w:br`/`w:cr` are whitespace; deleted
    text lives in `w:delText` (we include it so a span inside a deletion still
    reads sensibly).
    """
    parts: List[str] = []
    for node in run.iter():
        ln = _local(node.tag)
        if ln in ("t", "delText"):
            parts.append(node.text or "")
        elif ln in ("tab",):
            parts.append("\t")
        elif ln in ("br", "cr"):
            parts.append("\n")
    return "".join(parts)


def _element_text(elem: ET.Element) -> str:
    """All `w:t`/`w:delText` text under an element (e.g. a whole comment body)."""
    parts: List[str] = []
    for node in elem.iter():
        if _local(node.tag) in ("t", "delText"):
            parts.append(node.text or "")
    return "".join(parts)


# ---------------------------------------------------------------------------
# comments.xml
# ---------------------------------------------------------------------------
def parse_comments_xml(data: bytes) -> Dict[str, Dict[str, Any]]:
    """Parse `word/comments.xml` -> {id: {id, author, date, comment}}."""
    root = ET.fromstring(data)
    comments: Dict[str, Dict[str, Any]] = {}
    for c in root.iter(_q("comment")):
        cid = _w(c, "id")
        if cid is None:
            continue
        comments[cid] = {
            "id": cid,
            "author": _w(c, "author") or "",
            "date": _w(c, "date") or "",
            "initials": _w(c, "initials") or "",
            "comment": _element_text(c).strip(),
        }
    return comments


# ---------------------------------------------------------------------------
# document.xml — anchored spans + tracked changes
# ---------------------------------------------------------------------------
def parse_document_anchors(data: bytes) -> Dict[str, str]:
    """Walk `word/document.xml` and recover each comment's anchored body span.

    Returns {comment_id: anchored_text}. We iterate every descendant in document
    order. `w:commentRangeStart`/`End` toggle an "active id" set; any `w:r` run
    encountered while an id is active contributes its text to that id's span.

    Note: we collect text per-run rather than recursing whole subtrees so a run
    that nests under (say) a `w:ins` is still counted exactly once.
    """
    root = ET.fromstring(data)

    # Unbalanced-range guard: walk once to count starts/ends per id. A comment
    # whose range is unbalanced (a start with no matching end, or vice versa) is
    # NOT honored as an active range — otherwise a dangling start would leave its
    # id permanently active and vacuum every later run into it, mis-attributing
    # all the trailing body text. Such ids are reported on stderr and skipped.
    starts: Dict[str, int] = {}
    ends: Dict[str, int] = {}
    for elem in root.iter():
        ln = _local(elem.tag)
        if ln == "commentRangeStart":
            cid = _w(elem, "id")
            if cid is not None:
                starts[cid] = starts.get(cid, 0) + 1
        elif ln == "commentRangeEnd":
            cid = _w(elem, "id")
            if cid is not None:
                ends[cid] = ends.get(cid, 0) + 1
    balanced: set[str] = set()
    for cid in set(starts) | set(ends):
        if starts.get(cid, 0) == ends.get(cid, 0) and starts.get(cid, 0) > 0:
            balanced.add(cid)
        else:
            sys.stderr.write(
                f"docx_comments: unbalanced comment range for id {cid!r} "
                f"(starts={starts.get(cid, 0)}, ends={ends.get(cid, 0)}); "
                "anchored span not extracted.\n")

    active: set[str] = set()
    spans: Dict[str, List[str]] = {}

    for elem in root.iter():
        ln = _local(elem.tag)
        if ln == "commentRangeStart":
            cid = _w(elem, "id")
            if cid is not None and cid in balanced:
                active.add(cid)
                spans.setdefault(cid, [])
        elif ln == "commentRangeEnd":
            cid = _w(elem, "id")
            if cid is not None:
                active.discard(cid)
        elif ln == "r" and active:
            # A comment reference run is itself part of the balloon, not the
            # anchored body — skip runs that only carry a commentReference.
            if elem.find(_q("commentReference")) is not None:
                continue
            txt = _run_text(elem)
            if txt:
                for cid in active:
                    spans[cid].append(txt)

    return {cid: "".join(parts) for cid, parts in spans.items()}


# Tracked-change extraction is cheap (same single pass over document.xml), so we
# include it rather than defer it.
INCLUDE_TRACKED_CHANGES = True


def parse_tracked_changes(data: bytes) -> List[Dict[str, str]]:
    """Best-effort tracked changes: `w:ins`/`w:del` -> {type, author, date, text}."""
    root = ET.fromstring(data)
    changes: List[Dict[str, str]] = []
    for elem in root.iter():
        ln = _local(elem.tag)
        if ln in ("ins", "del"):
            text = _element_text(elem)
            if not text:
                continue
            changes.append({
                "type": "insertion" if ln == "ins" else "deletion",
                "author": _w(elem, "author") or "",
                "date": _w(elem, "date") or "",
                "text": text,
            })
    return changes


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def extract_comments(docx_path: str) -> List[Dict[str, Any]]:
    """Extract comments (with anchored spans + tracked changes) from a .docx.

    Raises ValueError if the path is not a valid zip/docx package.
    """
    if not zipfile.is_zipfile(docx_path):
        raise ValueError(
            f"{docx_path!r} is not a valid .docx (not a zip/OPC package).")

    with zipfile.ZipFile(docx_path) as zf:
        names = set(zf.namelist())
        if "word/document.xml" not in names:
            raise ValueError(
                f"{docx_path!r} is not a Word document "
                "(missing word/document.xml).")

        # No comments part at all -> no comments.
        if "word/comments.xml" not in names:
            return []

        comments_data = zf.read("word/comments.xml")
        document_data = zf.read("word/document.xml")

    comments = parse_comments_xml(comments_data)
    if not comments:
        return []

    anchors = parse_document_anchors(document_data)

    result: List[Dict[str, Any]] = []
    for cid, c in comments.items():
        entry: Dict[str, Any] = {
            "id": c["id"],
            "author": c["author"],
            "date": c["date"],
            "comment": c["comment"],
            "anchored_text": anchors.get(cid, ""),
        }
        if c.get("initials"):
            entry["initials"] = c["initials"]
        result.append(entry)

    # Stable order: by integer id when possible, else lexical.
    def _key(e: Dict[str, Any]):
        try:
            return (0, int(e["id"]))
        except (ValueError, TypeError):
            return (1, e["id"])

    result.sort(key=_key)
    return result


def extract_payload(docx_path: str) -> Dict[str, Any]:
    """Full payload: comments plus (best-effort) document-level tracked changes."""
    comments = extract_comments(docx_path)
    payload: Dict[str, Any] = {"comments": comments}
    if INCLUDE_TRACKED_CHANGES:
        with zipfile.ZipFile(docx_path) as zf:
            document_data = zf.read("word/document.xml")
        payload["tracked_changes"] = parse_tracked_changes(document_data)
    return payload


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_table(comments: List[Dict[str, Any]],
                 tracked: List[Dict[str, str]]) -> None:
    if not comments:
        print("(no comments)")
    for c in comments:
        print(f"[{c['id']}] {c['author']} ({c['date']})")
        print(f"    comment : {c['comment']}")
        print(f"    anchors : {c['anchored_text']!r}")
        print()
    if tracked:
        print(f"Tracked changes ({len(tracked)}):")
        for t in tracked:
            print(f"  - {t['type']} by {t['author']}: {t['text']!r}")


def cmd_extract(docx_path: str, as_json: bool) -> int:
    try:
        payload = extract_payload(docx_path)
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except FileNotFoundError:
        sys.stderr.write(f"error: no such file: {docx_path}\n")
        return 2

    comments = payload["comments"]
    tracked = payload.get("tracked_changes", [])

    if as_json:
        # The brief's primary contract is the comments list. Tracked changes ride
        # along under a wrapper only when present, to stay backward-friendly:
        # an empty/no-comments doc still prints `[]`.
        if tracked:
            print(json.dumps(
                {"comments": comments, "tracked_changes": tracked},
                indent=2, ensure_ascii=False))
        else:
            print(json.dumps(comments, indent=2, ensure_ascii=False))
    else:
        _print_table(comments, tracked)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Extract tracked comments (and best-effort tracked changes) "
                    "from a reviewed Word .docx, each re-associated with the "
                    "body text it anchors.")
    sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("extract", help="Extract comments from a .docx.")
    e.add_argument("--docx", required=True, help="Path to the reviewed .docx.")
    e.add_argument("--json", action="store_true",
                   help="Emit JSON (default: readable table).")

    args = p.parse_args(argv)
    if args.command == "extract":
        return cmd_extract(args.docx, args.json)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
