"""M36 WP-G0 — the normalized-docx comparison harness (proof obligation 2, A1).

Amendment A1 softened the render proof from raw byte identity to *normalized
XML semantic identity*. This module is that normalizer plus the differ. It is
deliberately dependency-free (stdlib `zipfile` + `xml.etree`) so the gate never
depends on a library that could itself change the answer.

WHAT IS COMPARED
    Only three parts of the package:
        word/document.xml   (required — the document itself)
        word/styles.xml     (compared when present)
        word/numbering.xml  (compared when present)
    Everything else is either derived (`[Content_Types].xml`, `_rels`),
    genuinely volatile (`docProps/core.xml` carries created/modified
    timestamps and the render's `cw-map:<doc_id>` category;
    `word/settings.xml` carries the `w:rsids` save-id table), or invariant
    boilerplate shipped by the template (`theme/`, `fontTable.xml`). Not
    comparing a part is not the same as normalizing it away: the three parts
    above carry the whole of the A1 protected set — text, element structure,
    ordering, numbering references, style references.

WHAT IS NORMALIZED, AND WHY EACH RULE STRIPS VOLATILITY AND NOT SEMANTICS
    1. `w:rsid*` attributes are dropped (`w:rsidR`, `w:rsidRPr`, `w:rsidDel`,
       `w:rsidTr`, `w:rsidSect`, ...). These are Word/python-docx *revision
       save identifiers*: opaque session tags used to attribute edits to an
       editing session. They name no content, no order, no style and no
       number. Two renders of identical content may carry different ones.
    2. Attribute ORDER is canonicalized (sorted by qualified name). XML
       attribute order is not information; a serializer is free to change it.
       Attribute NAMES and VALUES are all kept, so `w:val="ListParagraph"`
       (a style reference) and `w:numId`/`w:ilvl` (numbering references)
       survive intact.
    3. Whitespace that is structurally insignificant is dropped: element
       *tails*, and the *text* of elements that have children. WordprocessingML
       has no mixed content in these parts — a paragraph's text lives in leaf
       `w:t` elements — so this only removes pretty-printer indentation.
       Leaf text is preserved VERBATIM, including whitespace-only leaf text
       (`<w:t xml:space="preserve"> </w:t>` is a real space between runs).
       If a non-leaf element ever carries non-whitespace text, this module
       RAISES rather than dropping it (see `MixedContentError`) — the harness
       refuses to silently discard content it does not understand.
    4. Namespace prefixes are re-derived from a fixed table so the canonical
       form is stable and readable; the namespace URIs themselves are kept, so
       an element moving to a different namespace is still a difference.

    Nothing else is touched. Element names, element order, the number of
    elements, every attribute value, and every character of text are all
    load-bearing and all retained — over-normalizing would defeat the gate.

CANONICAL FORM
    A canonicalized part is itself valid XML: one element per line, indented
    by depth, attributes sorted, leaf text inline. It is therefore committable
    as a `.xml` golden, re-readable by this same module, and normalization is
    idempotent (`canonicalize(canonicalize(x)) == canonicalize(x)`).

USAGE
    parts = canonical_parts(some_docx)            # {part: canonical xml text}
    write_golden(some_docx, golden_dir)           # commit the reference
    diffs = compare(golden_dir, other_docx)       # [] means semantically equal
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile

from pathlib import Path

#: The parts the A1 comparison covers. `document.xml` is required of any real
#: render; the other two are compared when the package carries them.
DOCUMENT_PART = "word/document.xml"
COMPARED_PARTS = (DOCUMENT_PART, "word/styles.xml", "word/numbering.xml")
OPTIONAL_PARTS = frozenset(COMPARED_PARTS) - {DOCUMENT_PART}

#: part -> the filename it is committed under inside a golden directory.
GOLDEN_NAMES = {p: p.split("/")[-1] for p in COMPARED_PARTS}

#: Stable prefixes for the namespaces WordprocessingML actually uses here.
#: Anything unlisted keeps its URI in braces, so an unexpected namespace is
#: visible in the diff instead of being quietly folded away.
NS_PREFIXES = {
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main": "w",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships": "r",
    "http://schemas.openxmlformats.org/markup-compatibility/2006": "mc",
    "http://schemas.openxmlformats.org/drawingml/2006/main": "a",
    "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing":
        "wp",
    "http://schemas.openxmlformats.org/drawingml/2006/picture": "pic",
    "http://schemas.microsoft.com/office/word/2010/wordml": "w14",
    "http://schemas.microsoft.com/office/word/2012/wordml": "w15",
    "http://schemas.microsoft.com/office/word/2006/wordml": "w10prop",
    "http://www.w3.org/XML/1998/namespace": "xml",
}

_WS_RE = re.compile(r"\A\s*\Z")
_XMLNS_RE = re.compile(r'xmlns(?::([A-Za-z0-9_.-]+))?\s*=\s*"([^"]*)"')
_ESCAPES = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"))
_INDENT = "  "


class MixedContentError(ValueError):
    """An element carries BOTH children and real text.

    Raised instead of guessing: dropping such text would strip semantics, and
    keeping it would break the one-element-per-line canonical form. If this
    ever fires, the harness needs extending — not loosening.
    """


class DocxCompareError(ValueError):
    """The source is not a usable docx / golden directory."""


# --------------------------------------------------------------------------- #
# Canonicalization
# --------------------------------------------------------------------------- #
def _split(tag: str) -> tuple[str, str]:
    if tag.startswith("{"):
        uri, _, local = tag[1:].partition("}")
        return uri, local
    return "", tag


def _qname(tag: str, pfx: dict[str, str] | None = None) -> str:
    uri, local = _split(tag)
    if not uri:
        return local
    prefix = (pfx or NS_PREFIXES).get(uri, NS_PREFIXES.get(uri))
    if prefix is None:
        return f"{{{uri}}}{local}"
    return f"{prefix}:{local}" if prefix else local


def _prefix_map(nsmap: dict[str, str]) -> dict[str, str]:
    """{uri: prefix}, preferring the prefixes the SOURCE root declared.

    Using the source's own declarations is what keeps the canonical form valid
    XML (every prefix it uses is declared on the canonical root); NS_PREFIXES
    only fills in namespaces the root did not declare.
    """
    pfx = dict(NS_PREFIXES)
    for prefix, uri in nsmap.items():
        pfx[uri] = prefix
    return pfx


def _is_rsid(tag: str) -> bool:
    """`w:rsidR`, `w:rsidRPr`, `w:rsidSect`, ... — revision save ids."""
    return _split(tag)[1].startswith("rsid")


def _escape(text: str) -> str:
    for raw, enc in _ESCAPES:
        text = text.replace(raw, enc)
    return text


def _escape_attr(text: str) -> str:
    return _escape(text).replace('"', "&quot;")


def _root_nsmap(xml_text: str) -> dict[str, str]:
    """The xmlns declarations on the source root, as {prefix: uri} ('' = default)."""
    # Skip the `<?xml ...?>` prolog (and any comment/doctype) so the head we
    # scan is the ROOT element's own start tag, not the declaration.
    m = re.search(r"<[A-Za-z_]", xml_text)
    start = m.start() if m else 0
    end = xml_text.find(">", start)
    head = xml_text[start:end + 1] if end != -1 else xml_text[start:]
    return {(m.group(1) or ""): m.group(2) for m in _XMLNS_RE.finditer(head)}


def _emit(el, path: str, depth: int, out: list, decls: str, pfx: dict) -> None:
    """Append canonical (path, line) records for `el` and its subtree."""
    name = _qname(el.tag, pfx)
    attrs = []
    for key in sorted(el.keys(), key=lambda k: _qname(k, pfx)):
        if _is_rsid(key):
            continue                    # rule 1: revision save ids
        attrs.append(f'{_qname(key, pfx)}="{_escape_attr(el.get(key))}"')
    head = " ".join([name] + attrs)
    if decls:
        head = f"{name} {decls}" + (" " + " ".join(attrs) if attrs else "")
    pad = _INDENT * depth
    all_children = list(el)
    # rule 1b: `<w:rsid w:val="..."/>` records (styles.xml carries one per
    # style) are the element form of the same revision save id — dropped for
    # the same reason, and they hold no other field.
    children = [c for c in all_children if not _is_rsid(c.tag)]
    text = el.text
    if all_children and text is not None and not _WS_RE.match(text):
        raise MixedContentError(
            f"{path}: element has {len(all_children)} children AND text "
            f"{text!r} — refusing to normalize away real content")
    if children:
        out.append((path, f"{pad}<{head}>"))
        counts: dict[str, int] = {}
        for child in children:
            cn = _qname(child.tag, pfx)
            counts[cn] = counts.get(cn, 0) + 1
            _emit(child, f"{path}/{cn}[{counts[cn]}]", depth + 1, out, "", pfx)
        out.append((path, f"{pad}</{name}>"))
    elif all_children or text is None:
        out.append((path, f"{pad}<{head}/>"))
    else:
        # Leaf text verbatim (rule 3): whitespace-only leaf text is real.
        out.append((path, f"{pad}<{head}>{_escape(text)}</{name}>"))


def canonical_records(xml_text: str) -> list[tuple[str, str]]:
    """(element path, canonical line) for every line of the canonical form."""
    root = ET.fromstring(xml_text)
    nsmap = _root_nsmap(xml_text)
    pfx = _prefix_map(nsmap)
    decls = " ".join(
        f'xmlns{":" + p if p else ""}="{uri}"'
        for p, uri in sorted(nsmap.items()))
    out: list[tuple[str, str]] = []
    _emit(root, _qname(root.tag, pfx), 0, out, decls, pfx)
    return out


def canonicalize(xml_text: str) -> str:
    """Normalize one part to canonical XML text (valid, idempotent)."""
    return "\n".join(line for _, line in canonical_records(xml_text)) + "\n"


# --------------------------------------------------------------------------- #
# Sources: a .docx, or a committed golden directory
# --------------------------------------------------------------------------- #
def read_docx_parts(docx: Path) -> dict[str, str]:
    """Raw XML text of the compared parts inside a .docx (zip order ignored)."""
    docx = Path(docx)
    if not docx.is_file():
        raise DocxCompareError(f"not a file: {docx}")
    parts: dict[str, str] = {}
    with zipfile.ZipFile(docx) as zf:
        names = set(zf.namelist())
        for part in COMPARED_PARTS:
            if part in names:
                parts[part] = zf.read(part).decode("utf-8")
            elif part not in OPTIONAL_PARTS:
                raise DocxCompareError(f"{docx.name}: missing {part}")
    return parts


def canonical_parts(source) -> dict[str, str]:
    """{part: canonical xml text} from a .docx file OR a golden directory."""
    path = Path(source)
    if path.is_dir():
        out = {}
        for part, name in GOLDEN_NAMES.items():
            f = path / name
            if f.is_file():
                out[part] = canonicalize(f.read_text(encoding="utf-8"))
            elif part not in OPTIONAL_PARTS:
                raise DocxCompareError(f"{path}: golden is missing {name}")
        if not out:
            raise DocxCompareError(f"{path}: no golden parts found")
        return out
    return {part: canonicalize(text)
            for part, text in read_docx_parts(path).items()}


def write_golden(docx: Path, out_dir: Path) -> list[Path]:
    """Write the canonical parts of `docx` into `out_dir`. Returns the files."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for part, text in canonical_parts(docx).items():
        f = out_dir / GOLDEN_NAMES[part]
        f.write_text(text, encoding="utf-8")
        written.append(f)
    return written


# --------------------------------------------------------------------------- #
# The differ
# --------------------------------------------------------------------------- #
def _clip(line: str, width: int = 180) -> str:
    line = line.strip()
    return line if len(line) <= width else line[:width] + "…"


def compare(a, b, *, label_a: str = "a", label_b: str = "b") -> list[str]:
    """Normalized-XML comparison per M36 A1.

    `a` / `b` are each a .docx path, a golden directory, or an already-built
    {part: canonical text} mapping. Returns a list of human-readable
    difference strings — EMPTY means semantically identical. Each string names
    the part and, for content divergence, the first divergent element path plus
    both lines, so a failure is debuggable without re-running the render.
    """
    pa = a if isinstance(a, dict) else canonical_parts(a)
    pb = b if isinstance(b, dict) else canonical_parts(b)
    diffs: list[str] = []

    for part in sorted(set(pa) | set(pb)):
        if part not in pa:
            diffs.append(f"{part}: present in {label_b} only")
            continue
        if part not in pb:
            diffs.append(f"{part}: present in {label_a} only")
            continue
        ra = canonical_records(pa[part])
        rb = canonical_records(pb[part])
        first = None
        for i in range(min(len(ra), len(rb))):
            if ra[i][1] != rb[i][1]:
                first = i
                break
        differing = sum(1 for i in range(min(len(ra), len(rb)))
                        if ra[i][1] != rb[i][1])
        if first is not None:
            path = ra[first][0] if ra[first][0] == rb[first][0] else \
                f"{ra[first][0]} vs {rb[first][0]}"
            diffs.append(
                f"{part}: first difference at {path} (canonical line "
                f"{first + 1}): {label_a}={_clip(ra[first][1])!r} "
                f"{label_b}={_clip(rb[first][1])!r} "
                f"[{differing} differing line(s)]")
        if len(ra) != len(rb):
            diffs.append(
                f"{part}: element count differs — {label_a} has {len(ra)} "
                f"canonical lines, {label_b} has {len(rb)}"
                + ("" if first is not None else
                   f"; common prefix identical, first extra line is "
                   f"{_clip((rb if len(rb) > len(ra) else ra)[min(len(ra), len(rb))][1])!r}"))
    return diffs
