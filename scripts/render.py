#!/usr/bin/env python3
"""
render.py — thin top-level entrypoint the orchestrator invokes to build a Word
deliverable from a component folder (or, for back-compat, a single .md file).

    python3 scripts/render.py <area> -o <out.docx>

For a **folder** (an area dir containing `manifest.json`) this module does the
assembly glue and delegates styling to the bundled CFGI converter:

  1. `doc_model.assemble(folder)` -> structured AssembledDoc (title, subtitle,
     ordered sections each carrying heading / role / slug / number / body).
  2. `doc_model.display_numbers(manifest)` -> the ONE {slug: "L2.seq"} map.
  3. Procedure headings are prefixed with their display number ("1.1 Bank
     Reconciliation"); `[[slug]]` tokens in EVERY section body are resolved to
     display numbers via the same map, so derived tables (Systems "Related
     Procedures", Appendix A "Source Procedure") stay consistent with headings
     after any reorder.
  4. `<!-- derived: ... -->` markers and any fenced ```consult-meta``` block are
     stripped so neither reaches Word.
  5. Cover construction branches on input mode: folder -> title/subtitle from
     the manifest and the Document Profile card lifted from the
     `document-profile` static section; single-file -> the converter's legacy
     H1/tagline scan.

The assembled Markdown/structure is then handed to
`cfgi_markdown_to_word.convert_assembled` (folder) or `.convert` (single file).
`scripts/doc_model.py` is owned by M2 and imported here, never created.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

# Make both scripts/ (doc_model) and the skill's scripts/ (the converter)
# importable regardless of the caller's cwd.
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
_SKILL_SCRIPTS = _REPO_ROOT / "skills" / "consult-docx-builder" / "scripts"
for _p in (_SCRIPTS_DIR, _SKILL_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import doc_model  # noqa: E402  (M2-owned shared spine)
import cfgi_markdown_to_word as cfgi  # noqa: E402  (bundled converter)

# Static section(s) lifted onto the cover as the Document Profile card. Reuse
# the converter's set so the two stay in lock-step.
_PROFILE_HEADINGS = set(cfgi.COVER_SECTIONS)  # {"document profile"}


# --------------------------------------------------------------------------- #
# doc_model access shims (tolerant to dict- or dataclass-shaped returns and to
# resolve_tokens' exact signature, which M2 finalizes).
# --------------------------------------------------------------------------- #
def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _sections(assembled):
    secs = _attr(assembled, "sections")
    if secs is None:
        secs = _attr(assembled, "components")
    return secs or []


def _resolve_tokens(text: str, numbers) -> str:
    """Resolve `[[slug]]` cross-references to display numbers via doc_model."""
    try:
        return doc_model.resolve_tokens(text, numbers, "number")
    except TypeError:
        # M2 may expose resolve_tokens without a mode arg.
        return doc_model.resolve_tokens(text, numbers)


# --------------------------------------------------------------------------- #
# Body cleaning (things that must never reach Word)
# --------------------------------------------------------------------------- #
def _strip_derived_markers(text: str) -> str:
    """Remove `<!-- derived: KIND; writer: W -->` (and bare derived) comments."""
    return re.sub(r"<!--\s*derived\b.*?-->", "", text, flags=re.DOTALL | re.IGNORECASE)


def _strip_consult_meta(text: str) -> str:
    """Drop any fenced block whose info-string is `consult-meta` (```/~~~)."""
    lines = text.split("\n")
    out = []
    i = 0
    open_re = re.compile(r"^\s*(`{3,}|~{3,})\s*consult-meta\s*$", re.IGNORECASE)
    while i < len(lines):
        m = open_re.match(lines[i])
        if m:
            fence_char = m.group(1)[0]
            close_re = re.compile(r"^\s*" + re.escape(fence_char) + r"{3,}\s*$")
            i += 1
            while i < len(lines) and not close_re.match(lines[i]):
                i += 1
            i += 1  # consume the closing fence
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def _flag_gap_tags(text: str) -> str:
    """Render body gap tags `[[GAP-NN — label]]` as a visible bold flag.

    doc_model.resolve_tokens deliberately skips them (they are not procedure
    cross-refs), so without this they reach Word as raw wiki brackets.
    """
    return re.sub(r"\[\[\s*(GAP-\d+[^\]]*?)\s*\]\]", r"**[\1]**", text)


def _clean_body(text: str, numbers) -> str:
    text = _strip_consult_meta(text)
    text = _strip_derived_markers(text)
    text = _resolve_tokens(text, numbers)
    text = _flag_gap_tags(text)
    return text.strip("\n")


# --------------------------------------------------------------------------- #
# Folder assembly glue
# --------------------------------------------------------------------------- #
def _heading_for(section, numbers) -> str:
    heading = (_attr(section, "heading") or "").strip()
    if _attr(section, "role") == "procedure":
        num = _attr(section, "number")
        if not num:
            slug = _attr(section, "slug")
            num = numbers.get(slug) if slug else None
        if num:
            return f"{num} {heading}"
    return heading


def _render_folder(folder: Path, out: Path, include_toc: bool,
                   landscape: bool, do_cover: bool) -> None:
    manifest = doc_model.load_manifest(folder)
    doc_model.validate_manifest(manifest)
    numbers = doc_model.display_numbers(manifest)
    assembled = doc_model.assemble(folder)

    title = _attr(assembled, "title") or ""
    subtitle = _attr(assembled, "subtitle") or ""

    profile_md = ""
    body_parts = []
    for section in _sections(assembled):
        heading = (_attr(section, "heading") or "").strip()
        raw_body = _attr(section, "body") or ""
        body = _clean_body(raw_body, numbers)
        is_profile = heading.lower() in _PROFILE_HEADINGS

        # Lift the Document Profile onto the cover card (only when a cover is
        # being built); otherwise it renders inline like any other section.
        if do_cover and is_profile:
            profile_md = body
            continue

        body_parts.append(f"## {_heading_for(section, numbers)}")
        body_parts.append("")
        if body:
            body_parts.append(body)
            body_parts.append("")

    body_md = "\n".join(body_parts)
    cfgi.convert_assembled(
        body_md, out, title=title, subtitle=subtitle, profile_md=profile_md,
        include_toc=include_toc, landscape=landscape, do_cover=do_cover,
    )


# --------------------------------------------------------------------------- #
# Input resolution
# --------------------------------------------------------------------------- #
def _resolve_input(area: str):
    """Return (kind, path). kind is 'folder' or 'file'."""
    p = Path(area)
    candidates = [p, _REPO_ROOT / "components" / area, Path("components") / area]
    for c in candidates:
        if c.is_dir() and (c / "manifest.json").is_file():
            return "folder", c
    if p.is_dir():
        # A directory without a manifest is not a valid area.
        raise SystemExit(f"error: no manifest.json in folder: {p}")
    if p.is_file():
        return "file", p
    raise SystemExit(f"error: input not found (no folder/manifest or .md): {area}")


def _infer_output(kind: str, path: Path, output_arg) -> Path:
    if output_arg:
        return Path(output_arg)
    if kind == "folder":
        name = _attr(doc_model.load_manifest(path), "area") or path.name
        return path / f"{name}_process-doc.docx"
    return cfgi.infer_output(path, None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Render a CONSULT component folder (or single .md) to a CFGI-styled .docx")
    ap.add_argument("area", help="area folder (containing manifest.json) or a single .md file")
    ap.add_argument("-o", "--output")
    ap.add_argument("--include-toc", action="store_true", help="Insert a generated Table of Contents")
    ap.add_argument("--landscape", action="store_true", help="Use landscape orientation")
    ap.add_argument("--no-cover", action="store_true", help="Skip the generated cover page")
    a = ap.parse_args(argv)

    kind, path = _resolve_input(a.area)
    out = _infer_output(kind, path, a.output)
    do_cover = not a.no_cover
    if kind == "folder":
        _render_folder(path, out, a.include_toc, a.landscape, do_cover)
    else:
        cfgi.convert(path, out, a.include_toc, a.landscape, do_cover)
    print("Wrote " + str(out))
    # M7 signal file (folder input only — single-file render isn't an area):
    # record basis + docx + awaiting_review so the advisor moves to the review
    # gate rather than re-rendering.
    if kind == "folder":
        import orchestrate
        orchestrate.emit_render(str(path), str(out), awaiting_review=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
