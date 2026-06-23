#!/usr/bin/env python3
"""ingest_normalize.py — Stage 1 ingest (CONSULT pipeline).

Converts raw client files into clean Markdown with a YAML header under
`engagements/{id}/ingested/`. Artifacts are **immutable** and keyed by the
**source content hash** (sha256 of the raw bytes) — this is the line-stability
guarantee Stage 2 (classify) depends on: once an ingested MD is written it is
**never rewritten**, so a `path#Lstart-Lend` evidence ref stays valid forever.

Idempotency is by **dir-check dedup** (no manifest in Slice 1): before writing,
we scan `engagements/{id}/ingested/*.md` for a header carrying the same
`source_hash`. If one exists we **skip** (re-ingest of the same bytes is a
no-op). A *changed* source = different bytes = different hash = a **new** MD;
the old one is left untouched.

v1 handlers (per ingest_contract.md §5):
  - transcript (`.vtt .srt`, and transcript-like `.txt`) — REUSES the existing
    `skills/consult-transcript-cleaner/scripts/clean_vtt.py` cleaning logic by
    importing its pure `clean_text(str)->str` function (no temp files, no exec).
  - text passthrough (`.txt .md`) — light whitespace normalization.
  - table (`.csv .tsv`) — rendered as a Markdown table.
  - docx (`.docx`) — text + tables, headings preserved (python-docx).

Out of scope (v2/v3): pdf/pptx/xlsx/images, the manifest + supersession,
page/slide provenance markers beyond what docx headings give for free.

Command:
  ingest --engagement E --source PATH [PATH...]   (each PATH may be a file or dir)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

import consult_io

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"
HEADER_SCHEMA = REPO_ROOT / "schemas" / "ingested_header.schema.json"
CLEAN_VTT_DIR = (REPO_ROOT / "skills" / "consult-transcript-cleaner"
                 / "scripts")

# Import the transcript cleaner's pure clean_text() directly (no exec hack).
# Its dir is not on sys.path, so add it before importing.
if str(CLEAN_VTT_DIR) not in sys.path:
    sys.path.insert(0, str(CLEAN_VTT_DIR))
import clean_vtt  # noqa: E402

SCRIPT_NAME = "ingest_normalize.py"

# Extension -> (doc_type, handler_version, handler key). Transcript-like .txt is
# decided at runtime by sniffing the bytes; the table here gives the default.
TRANSCRIPT_EXTS = {".vtt", ".srt"}
TEXT_EXTS = {".txt", ".md"}
TABLE_EXTS = {".csv", ".tsv"}
DOCX_EXTS = {".docx"}
SUPPORTED_EXTS = TRANSCRIPT_EXTS | TEXT_EXTS | TABLE_EXTS | DOCX_EXTS

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "with",
    "at", "by", "from", "as", "is", "are", "be", "this", "that", "draft",
    "final", "copy", "v1", "v2", "notes", "note", "meeting", "call",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def ingested_dir(eid: str) -> Path:
    return engagement_dir(eid) / "ingested"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_iso_z() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


def slugify(text: str, max_words: int = 6) -> str:
    """Lowercase kebab slug from likely topic words; stopwords dropped."""
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    kept = [w for w in words if w not in STOPWORDS and len(w) > 1]
    if not kept:
        kept = words or ["document"]
    return "-".join(kept[:max_words]) or "document"


def titleize(stem: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", stem)
    return " ".join(w.capitalize() for w in words) if words else stem


def file_date(path: Path) -> str:
    """YYYY-MM-DD from the file's mtime (transcript date isn't reliably known)."""
    ts = _dt.datetime.fromtimestamp(path.stat().st_mtime, _dt.timezone.utc)
    return ts.strftime("%Y-%m-%d")


def parse_header(md_path: Path) -> Optional[Dict[str, Any]]:
    """Read just the YAML front matter from an ingested MD (None if absent)."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def find_existing_for_hash(eid: str, source_hash: str) -> Optional[Path]:
    """Dir-check dedup: return an existing ingested MD whose header carries this
    source_hash, else None. This is what makes re-ingest idempotent."""
    d = ingested_dir(eid)
    if not d.is_dir():
        return None
    for md in sorted(d.glob("*.md")):
        hdr = parse_header(md)
        if hdr and hdr.get("source_hash") == source_hash:
            return md
    return None


def looks_like_transcript(raw_bytes: bytes) -> bool:
    """Sniff a .txt to decide if the transcript handler should run: WEBVTT/SRT
    markers, --> cue timing, or <v Speaker> tags."""
    try:
        head = raw_bytes[:4000].decode("utf-8", errors="replace")
    except Exception:
        return False
    if head.lstrip().upper().startswith("WEBVTT"):
        return True
    if re.search(r"\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}\s*-->", head):
        return True
    if re.search(r"<v [^>]+>", head):
        return True
    return False


# --------------------------------------------------------------------------- #
# Handlers — each returns (doc_type, ingester_tag, markdown_body, provenance)
# --------------------------------------------------------------------------- #

def handle_transcript(path: Path, raw: bytes) -> Tuple[str, str, str, Dict[str, Any]]:
    """Reuse clean_vtt.py's cleaning logic by importing its pure clean_text():
    decode the raw bytes and pass them through in-memory. clean_text returns the
    cleaned `**Speaker:** text` body directly (no front matter to strip)."""
    text = raw.decode("utf-8", errors="replace")
    cleaned_body = clean_vtt.clean_text(text).strip()
    return "transcript", "transcript@1", cleaned_body, {"pages": None, "slides": None, "sheets": None}


def handle_text(path: Path, raw: bytes) -> Tuple[str, str, str, Dict[str, Any]]:
    """Text passthrough: decode, normalize trailing whitespace and runs of
    blank lines. Substance and structure are preserved as-is."""
    text = raw.decode("utf-8", errors="replace")
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: List[str] = []
    blank = 0
    for ln in lines:
        if ln == "":
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(ln)
    body = "\n".join(out).strip()
    return "text", "text@1", body, {"pages": None, "slides": None, "sheets": None}


def _md_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)

    def _cell(c: Any) -> str:
        # Escape pipes and collapse any embedded newlines (CR/LF) to <br> so a
        # multiline cell can't break the single-line Markdown table row.
        s = (c if c is not None else "")
        s = s.replace("|", r"\|")
        s = re.sub(r"\r\n?|\n", "<br>", s)
        return s.strip()

    norm = [[_cell(c) for c in r] + [""] * (width - len(r)) for r in rows]
    header = norm[0]
    body = norm[1:]
    out = ["| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    for r in body:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def handle_table(path: Path, raw: bytes) -> Tuple[str, str, str, Dict[str, Any]]:
    """CSV/TSV -> Markdown table."""
    import csv
    import io

    text = raw.decode("utf-8-sig", errors="replace")
    delim = "\t" if path.suffix.lower() == ".tsv" else ","
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = [r for r in reader if any((c or "").strip() for c in r)]
    body = _md_table(rows)
    return "csv", "table@1", body, {"pages": None, "slides": None, "sheets": None}


def handle_docx(path: Path, raw: bytes) -> Tuple[str, str, str, Dict[str, Any]]:
    """.docx -> text + tables, headings preserved. Reads paragraphs and tables
    in document order via python-docx. Heading styles map to Markdown headings.

    TODO (v2): emit `<!-- page N -->` provenance markers — docx has no reliable
    page boundaries, so for now headings are the only structural anchors."""
    try:
        import docx  # python-docx
    except ImportError as e:  # pragma: no cover - environment guard
        raise SystemExit(
            "python-docx is required for .docx ingest. Install with: "
            "pip install python-docx") from e
    import io

    document = docx.Document(io.BytesIO(raw))

    # Walk the body in document order so tables stay positioned among paragraphs.
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent_elm = document.element.body
    out: List[str] = []

    def heading_level(style_name: str) -> Optional[int]:
        m = re.match(r"heading\s+(\d+)", (style_name or "").strip().lower())
        if m:
            return min(int(m.group(1)), 6)
        if (style_name or "").strip().lower() == "title":
            return 1
        return None

    for child in parent_elm.iterchildren():
        if child.tag.endswith("}p"):
            para = Paragraph(child, document)
            txt = para.text.strip()
            if not txt:
                continue
            lvl = heading_level(para.style.name if para.style else "")
            if lvl:
                out.append(f"{'#' * lvl} {txt}")
            else:
                out.append(txt)
        elif child.tag.endswith("}tbl"):
            table = Table(child, document)
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            tbl_md = _md_table(rows)
            if tbl_md:
                out.append(tbl_md)

    body = "\n\n".join(out).strip()
    return "docx", "docx@1", body, {"pages": None, "slides": None, "sheets": None}


def dispatch(path: Path, raw: bytes):
    ext = path.suffix.lower()
    if ext in TRANSCRIPT_EXTS:
        return handle_transcript(path, raw)
    if ext in TABLE_EXTS:
        return handle_table(path, raw)
    if ext in DOCX_EXTS:
        return handle_docx(path, raw)
    if ext in TEXT_EXTS:
        if ext == ".txt" and looks_like_transcript(raw):
            return handle_transcript(path, raw)
        return handle_text(path, raw)
    raise SystemExit(f"Unsupported extension '{ext}' for {path} (v1 handles "
                     f"{sorted(SUPPORTED_EXTS)}).")


# --------------------------------------------------------------------------- #
# MD assembly + write
# --------------------------------------------------------------------------- #

def build_md(source: str, source_hash_hex: str, doc_type: str, ingester_tag: str,
             title: str, provenance: Dict[str, Any], body: str) -> str:
    header = {
        "source": source,
        "source_hash": f"sha256:{source_hash_hex}",
        "doc_type": doc_type,
        "ingested_at": now_iso_z(),
        "ingester": f"{SCRIPT_NAME}/{ingester_tag}",
        "title": title,
        "provenance": provenance,
        "hints": {"client": None, "systems": [], "people": []},
        "immutable": True,
    }
    yaml_block = yaml.safe_dump(header, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{yaml_block}\n---\n\n# {title}\n\n{body}\n"


def validate_header(header: Dict[str, Any]) -> None:
    """Validate a header dict against the ingested_header JSON Schema."""
    import json
    try:
        import jsonschema
    except ImportError as e:  # pragma: no cover
        raise SystemExit("jsonschema is required. pip install jsonschema") from e
    schema = json.loads(HEADER_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(instance=header, schema=schema)


def output_name(path: Path, doc_type: str, source_hash_hex: str) -> str:
    date = file_date(path)
    slug = slugify(path.stem)
    short = source_hash_hex[:12]
    return f"{date}_{slug}.{doc_type}.{short}.md"


def ingest_one(eid: str, src: Path) -> Tuple[str, Path]:
    """Ingest a single file. Returns (status, md_path) where status is
    'skipped' (hash already ingested) or 'written'.

    The dedup-check -> write window runs under an engagement-level advisory lock
    so two concurrent ingests of identical bytes can't both write, and the MD is
    committed via an atomic write (no truncated file on a crash mid-write)."""
    raw = src.read_bytes()
    h = sha256_hex(raw)

    # Build/validate the MD up front (no shared state) so the lock is held only
    # across the dedup-check -> write window.
    doc_type, ingester_tag, body, provenance = dispatch(src, raw)
    title = titleize(src.stem)
    md_text = build_md(
        source=str(src), source_hash_hex=h, doc_type=doc_type,
        ingester_tag=ingester_tag, title=title, provenance=provenance, body=body,
    )
    # Validate the header we just produced before committing it to disk.
    header = parse_header_from_text(md_text)
    validate_header(header)

    out_dir = ingested_dir(eid)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Serialize the dedup-check -> write across concurrent ingests of the same
    # engagement (TOCTOU): the lock is engagement-level (sidecar .consult.lock).
    with consult_io.locked(engagement_dir(eid)):
        existing = find_existing_for_hash(eid, h)
        if existing is not None:
            return "skipped", existing

        out_path = out_dir / output_name(src, doc_type, h)

        # Immutability guard: never rewrite an existing ingested MD.
        if out_path.exists():
            # Same hash should have been caught by dir-check above; a name
            # collision without a hash match is a genuine conflict — refuse
            # rather than clobber.
            existing_hdr = parse_header(out_path)
            if not (existing_hdr and existing_hdr.get("source_hash") == f"sha256:{h}"):
                raise SystemExit(f"Refusing to overwrite existing ingested MD: {out_path}")
            return "skipped", out_path

        consult_io.write_text_atomic(out_path, md_text)
    return "written", out_path


def parse_header_from_text(md_text: str) -> Dict[str, Any]:
    m = re.match(r"^---\n(.*?)\n---\n", md_text, re.DOTALL)
    if not m:
        raise SystemExit("Internal error: produced MD has no YAML header.")
    data = yaml.safe_load(m.group(1))
    if not isinstance(data, dict):
        raise SystemExit("Internal error: produced MD front matter is not a mapping.")
    return data


def iter_sources(paths: List[str]) -> List[Path]:
    """Expand each --source into concrete supported files (dirs recursed)."""
    out: List[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for f in sorted(path.rglob("*")):
                if not (f.is_file() and f.suffix.lower() in SUPPORTED_EXTS):
                    continue
                # Never re-ingest our own output: when --source points at an
                # engagement dir, rglob would otherwise sweep ingested/*.md.
                if "ingested" in f.relative_to(path).parts:
                    continue
                out.append(f)
        elif path.is_file():
            out.append(path)
        else:
            raise SystemExit(f"Source not found: {p}")
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def cmd_ingest(args: argparse.Namespace) -> int:
    sources = iter_sources(args.source)
    if not sources:
        print("No supported source files found.", file=sys.stderr)
        return 1
    written = skipped = 0
    failures: List[Tuple[Path, str]] = []
    for src in sources:
        try:
            status, md_path = ingest_one(args.engagement, src)
        except Exception as e:  # noqa: BLE001 — per-file isolation: one bad
            # file (e.g. validation failure) must not kill the whole batch.
            failures.append((src, str(e)))
            print(f"{'FAILED':8s} {src} -> {e}", file=sys.stderr)
            continue
        rel = md_path.relative_to(REPO_ROOT) if REPO_ROOT in md_path.parents else md_path
        print(f"{status:8s} {src} -> {rel}")
        if status == "written":
            written += 1
        else:
            skipped += 1
    print(f"Done. {written} written, {skipped} skipped, {len(failures)} failed "
          f"(engagement '{args.engagement}').")
    if failures:
        print("Failures:", file=sys.stderr)
        for src, msg in failures:
            print(f"  {src}: {msg}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="CONSULT Stage 1 ingest — raw files to immutable hashed "
                    "Markdown + YAML header.")
    sub = p.add_subparsers(dest="command", required=True)

    ing = sub.add_parser("ingest", help="Ingest one or more sources (files or dirs).")
    ing.add_argument("--engagement", required=True, help="Engagement id.")
    ing.add_argument("--source", required=True, nargs="+",
                     help="One or more source files or directories.")
    ing.set_defaults(func=cmd_ingest)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
