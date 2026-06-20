#!/usr/bin/env python3
"""
cfgi_markdown_to_word.py

Convert a built PharmmaEssential deliverable Markdown file into a CFGI-branded
Microsoft Word document (.docx).

Designed around:
- PharmmaEssential deliverable structure: headings, tables, bullets, callouts,
  horizontal rules, document profile, appendices.
- CFGI Brand Identity: Georgia headings, Arial body, CFGI color palette,
  table styling, footer/copyright, callout styling.

Usage:
    python cfgi_markdown_to_word.py input.md
    python cfgi_markdown_to_word.py input.md -o output.docx
    python cfgi_markdown_to_word.py input.md -o output.docx --include-generated-toc
    python cfgi_markdown_to_word.py input.md --config style_overrides.json

Optional JSON override example:
{
  "brand": {
    "colors": { "navy": "#002A5C" },
    "fonts": { "heading": "Georgia", "body": "Arial" }
  },
  "document": {
    "footer_text": "© CFGI | ALL RIGHTS RESERVED",
    "orientation": "portrait"
  }
}
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


# =============================================================================
# MODULAR CONFIGURATION
# Update these dictionaries, or pass a JSON file via --config, to change branding,
# layout, parsing behavior, or output behavior without touching conversion logic.
# =============================================================================

DEFAULT_CONFIG: Dict = {
    "brand": {
        "colors": {
            "navy": "#002A5C",
            "dark_navy": "#000D1C",
            "murrey": "#9A0B52",
            "teal": "#51C69E",
            "teal_light": "#A8E3CF",
            "green": "#066173",
            "green_light": "#83B0B9",
            "blue_mid": "#277FBB",
            "blue_light": "#4AC7FF",
            "yellow": "#FFDA3D",
            "yellow_light": "#FFED9E",
            "orange": "#FFBF3D",
            "orange_light": "#FFDF9E",
            "purple": "#5F4EB5",
            "purple_light": "#AFA7DA",
            "red": "#C83A20",
            "red_light": "#E49D90",
            "text": "#3D454E",
            "gray_mid": "#999FA4",
            "gray_light": "#D5DADE",
            "bg_light": "#F5F8FB",
            "white": "#FFFFFF",
        },
        "fonts": {
            "heading": "Georgia",
            "body": "Arial",
        },
        "type_scale": {
            "title_pt": 24,
            "h1_pt": 18,
            "h2_pt": 16,
            "h3_pt": 14,
            "h4_pt": 12,
            "body_pt": 12,
            "small_pt": 11,
            "footer_pt": 10,
        },
        "title": {
            "all_caps": True,
            # Word character spacing is in twentieths of a point; 3pt = 60.
            "letter_spacing_pt": 3,
        },
    },
    "document": {
        "page_width_inches": 8.5,
        "page_height_inches": 11.0,
        "orientation": "portrait",  # portrait | landscape
        "margins_inches": {
            "top": 0.75,
            "bottom": 0.65,
            "left": 0.75,
            "right": 0.75,
        },
        "footer_text": "© CFGI | ALL RIGHTS RESERVED",
        "include_footer": True,
        "include_page_numbers": True,
        "include_generated_toc": False,
        "page_break_on_h1": False,
        "remove_template_variable_catalog": False,
        "strip_yaml_front_matter": True,
        "default_output_suffix": "_CFGI.docx",
    },
    "styles": {
        "normal": {
            "font": "body",
            "size_key": "body_pt",
            "color": "text",
            "space_after_pt": 6,
            "line_spacing": 1.05,
        },
        "title": {
            "font": "heading",
            "size_key": "title_pt",
            "color": "navy",
            "bold": False,
            "space_after_pt": 10,
        },
        "heading_1": {
            "font": "heading",
            "size_key": "h1_pt",
            "color": "navy",
            "bold": True,
            "space_before_pt": 14,
            "space_after_pt": 6,
        },
        "heading_2": {
            "font": "body",
            "size_key": "h2_pt",
            "color": "navy",
            "bold": True,
            "space_before_pt": 10,
            "space_after_pt": 4,
        },
        "heading_3": {
            "font": "body",
            "size_key": "h3_pt",
            "color": "text",
            "bold": True,
            "space_before_pt": 8,
            "space_after_pt": 3,
        },
        "heading_4": {
            "font": "body",
            "size_key": "h4_pt",
            "color": "text",
            "bold": True,
            "space_before_pt": 6,
            "space_after_pt": 2,
        },
        "caption": {
            "font": "body",
            "size_key": "small_pt",
            "color": "gray_mid",
            "italic": True,
        },
        "blockquote": {
            "font": "body",
            "size_key": "body_pt",
            "color": "text",
            "background": "bg_light",
            "border": "blue_mid",
        },
        "hyperlink": {
            "color": "purple",
            "underline": True,
        },
    },
    "tables": {
        "header_fill": "navy",
        "header_text": "white",
        "body_text": "text",
        "border": "gray_light",
        "row_fills": ["white", "bg_light"],
        "font": "body",
        "font_size_pt": 10,
        "cell_margin_twips": 80,
        "repeat_header_row": True,
        "autofit": True,
    },
    "callouts": {
        # Keyword matching is case-insensitive against the text after blockquote marker.
        "warning": {"keywords": ["WARNING", "CAUTION"], "fill": "orange_light", "border": "orange", "text": "text"},
        "positive": {"keywords": ["POSITIVE"], "fill": "teal_light", "border": "teal", "text": "text"},
        "negative": {"keywords": ["NEGATIVE"], "fill": "red_light", "border": "red", "text": "text"},
        "important": {"keywords": ["IMPORTANT", "CONTROL POINT", "DECISION REQUIRED"], "fill": "navy", "border": "navy", "text": "white"},
        "kpi": {"keywords": ["KEY STAT", "KPI", "VALIDATION REQUIRED", "FUTURE-STATE OPPORTUNITY", "PAIN POINT"], "fill": "bg_light", "border": "blue_mid", "text": "navy"},
    },
    "markdown": {
        "horizontal_rule_patterns": [r"^\s*---+\s*$", r"^\s*\*\*\*+\s*$", r"^\s*___+\s*$"],
        "image_max_width_inches": 6.75,
    },
}


# =============================================================================
# LOW-LEVEL WORD/XML HELPERS
# =============================================================================

def deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override into base without mutating either object."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def hex_to_rgb(hex_color: str) -> RGBColor:
    color = hex_color.strip().lstrip("#")
    if len(color) != 6 or not re.fullmatch(r"[0-9A-Fa-f]{6}", color):
        raise ValueError(f"Invalid hex color: {hex_color}")
    return RGBColor(int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def hex_no_hash(hex_color: str) -> str:
    return hex_color.strip().lstrip("#").upper()


def color_value(config: Dict, color_key_or_hex: str) -> str:
    colors = config["brand"]["colors"]
    return colors.get(color_key_or_hex, color_key_or_hex)


def font_value(config: Dict, font_key_or_name: str) -> str:
    fonts = config["brand"]["fonts"]
    return fonts.get(font_key_or_name, font_key_or_name)


def set_cell_shading(cell, fill_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), hex_no_hash(fill_hex))


def set_cell_borders(cell, color_hex: str, size: str = "4") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = tc_pr.first_child_found_in("w:tcBorders")
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = tc_borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            tc_borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), hex_no_hash(color_hex))


def set_cell_margins(cell, margin_twips: int) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin_name in ["top", "start", "bottom", "end"]:
        node = tc_mar.find(qn(f"w:{margin_name}"))
        if node is None:
            node = OxmlElement(f"w:{margin_name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(margin_twips))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_paragraph_bottom_border(paragraph, color_hex: str, size: str = "6", space: str = "3") -> None:
    p = paragraph._p
    p_pr = p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    bottom = p_bdr.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        p_bdr.append(bottom)
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), space)
    bottom.set(qn("w:color"), hex_no_hash(color_hex))


def set_paragraph_left_border(paragraph, color_hex: str, size: str = "18", space: str = "6") -> None:
    p = paragraph._p
    p_pr = p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    left = p_bdr.find(qn("w:left"))
    if left is None:
        left = OxmlElement("w:left")
        p_bdr.append(left)
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), size)
    left.set(qn("w:space"), space)
    left.set(qn("w:color"), hex_no_hash(color_hex))


def set_paragraph_shading(paragraph, fill_hex: str) -> None:
    p = paragraph._p
    p_pr = p.get_or_add_pPr()
    shd = p_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        p_pr.append(shd)
    shd.set(qn("w:fill"), hex_no_hash(fill_hex))


def set_character_spacing(run, spacing_points: float) -> None:
    """Set character spacing in points on a run. Word stores this in twentieths of a point."""
    r_pr = run._r.get_or_add_rPr()
    spacing = r_pr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        r_pr.append(spacing)
    spacing.set(qn("w:val"), str(int(round(spacing_points * 20))))


def add_page_number(paragraph) -> None:
    """Insert a PAGE field into a paragraph."""
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr_text)
    run._r.append(fld_end)


def add_toc_field(paragraph, levels: str = "1-3") -> None:
    """Insert a Word TOC field. User can right-click Update Field in Word."""
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = f'TOC \\o "{levels}" \\h \\z \\u'
    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr_text)
    run._r.append(fld_separate)
    run._r.append(fld_end)


# =============================================================================
# MARKDOWN PARSING HELPERS
# =============================================================================

@dataclass
class TableBlock:
    header: List[str]
    align: List[str]
    rows: List[List[str]]


def strip_front_matter(markdown: str) -> Tuple[str, Dict[str, str]]:
    """Strip YAML-ish front matter if present; return body and simple metadata map."""
    text = markdown.lstrip("\ufeff")
    if not text.startswith("---"):
        return markdown, {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return markdown, {}
    end_idx = None
    for i in range(1, min(len(lines), 200)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return markdown, {}

    front_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :])
    metadata: Dict[str, str] = {}
    for line in front_lines:
        # Supports "key: value"; leaves nested YAML intentionally simple.
        m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$", line)
        if m:
            metadata[m.group(1)] = m.group(2).strip().strip('"')
    return body, metadata


def normalize_markdown(markdown: str) -> str:
    """Normalize common escaped characters produced by templating or LLM outputs."""
    replacements = {
        r"\_": "_",
        r"\*": "*",
        r"\|": "|",
        r"\[": "[",
        r"\]": "]",
        r"\`": "`",
    }
    text = markdown.replace("\r\n", "\n").replace("\r", "\n")
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def is_horizontal_rule(line: str, config: Dict) -> bool:
    return any(re.match(pattern, line) for pattern in config["markdown"]["horizontal_rule_patterns"])


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c or "") for c in cells)


def split_table_row(line: str) -> List[str]:
    """Split a GitHub-style Markdown table row, respecting escaped pipes."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells = []
    current = []
    escape = False
    for ch in s:
        if escape:
            current.append(ch)
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    cells.append("".join(current).strip())
    return cells


def parse_table(lines: Sequence[str], start: int) -> Tuple[Optional[TableBlock], int]:
    if start + 1 >= len(lines):
        return None, start
    if "|" not in lines[start] or not is_table_separator(lines[start + 1]):
        return None, start

    header = split_table_row(lines[start])
    separator = split_table_row(lines[start + 1])
    align = []
    for cell in separator:
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            align.append("center")
        elif right:
            align.append("right")
        else:
            align.append("left")

    rows: List[List[str]] = []
    i = start + 2
    while i < len(lines) and "|" in lines[i].strip() and not is_horizontal_rule(lines[i], DEFAULT_CONFIG):
        # Stop on blank-ish or heading line accidentally containing a pipe.
        if not lines[i].strip() or re.match(r"^#{1,6}\s+", lines[i]):
            break
        row = split_table_row(lines[i])
        if len(row) < len(header):
            row.extend([""] * (len(header) - len(row)))
        rows.append(row[: len(header)])
        i += 1

    return TableBlock(header=header, align=align, rows=rows), i


def strip_markdown_links_for_toc(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def clean_inline_text(text: str) -> str:
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def parse_inline_segments(text: str) -> List[Dict[str, object]]:
    """
    Parse a pragmatic subset of inline Markdown: bold, italic, code, links.
    Returns ordered segments with formatting flags.
    """
    text = clean_inline_text(text)
    pattern = re.compile(
        r"(\*\*([^*]+?)\*\*)"          # bold
        r"|(\*([^*]+?)\*)"              # italic
        r"|(`([^`]+?)`)"                 # code
        r"|(\[([^\]]+?)\]\(([^)]+?)\))" # link
    )
    segments: List[Dict[str, object]] = []
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            segments.append({"text": text[pos : m.start()]})
        if m.group(2):
            segments.append({"text": m.group(2), "bold": True})
        elif m.group(4):
            segments.append({"text": m.group(4), "italic": True})
        elif m.group(6):
            segments.append({"text": m.group(6), "code": True})
        elif m.group(8):
            segments.append({"text": m.group(8), "link": m.group(9)})
        pos = m.end()
    if pos < len(text):
        segments.append({"text": text[pos:]})
    return segments


# =============================================================================
# DOCUMENT SETUP AND STYLING
# =============================================================================

def configure_document(doc: Document, config: Dict) -> None:
    section = doc.sections[0]

    orientation = config["document"].get("orientation", "portrait").lower()
    width = Inches(config["document"]["page_width_inches"])
    height = Inches(config["document"]["page_height_inches"])
    if orientation == "landscape":
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = height
        section.page_height = width
    else:
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = width
        section.page_height = height

    margins = config["document"]["margins_inches"]
    section.top_margin = Inches(margins["top"])
    section.bottom_margin = Inches(margins["bottom"])
    section.left_margin = Inches(margins["left"])
    section.right_margin = Inches(margins["right"])

    define_styles(doc, config)
    if config["document"].get("include_footer", True):
        apply_footer(doc, config)


def apply_font_to_style(style, font_name: str, size_pt: Optional[float], color_hex: Optional[str] = None,
                        bold: Optional[bool] = None, italic: Optional[bool] = None) -> None:
    style.font.name = font_name
    style._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    if size_pt is not None:
        style.font.size = Pt(size_pt)
    if color_hex:
        style.font.color.rgb = hex_to_rgb(color_hex)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic


def define_styles(doc: Document, config: Dict) -> None:
    colors = config["brand"]["colors"]
    scale = config["brand"]["type_scale"]
    styles_cfg = config["styles"]

    normal = doc.styles["Normal"]
    ncfg = styles_cfg["normal"]
    apply_font_to_style(
        normal,
        font_value(config, ncfg["font"]),
        scale[ncfg["size_key"]],
        colors[ncfg["color"]],
    )
    normal.paragraph_format.space_after = Pt(ncfg.get("space_after_pt", 6))
    normal.paragraph_format.line_spacing = ncfg.get("line_spacing", 1.05)

    # Built-in heading styles preserve Word navigation pane and TOC behavior.
    heading_map = {
        "Title": "title",
        "Heading 1": "heading_1",
        "Heading 2": "heading_2",
        "Heading 3": "heading_3",
        "Heading 4": "heading_4",
    }
    for word_style_name, cfg_key in heading_map.items():
        cfg = styles_cfg[cfg_key]
        style = doc.styles[word_style_name]
        apply_font_to_style(
            style,
            font_value(config, cfg["font"]),
            scale[cfg["size_key"]],
            colors[cfg["color"]],
            cfg.get("bold"),
            cfg.get("italic"),
        )
        style.paragraph_format.space_before = Pt(cfg.get("space_before_pt", 0))
        style.paragraph_format.space_after = Pt(cfg.get("space_after_pt", 0))
        style.paragraph_format.keep_with_next = True

    # Custom styles.
    if "CFGI Caption" not in [s.name for s in doc.styles]:
        caption_style = doc.styles.add_style("CFGI Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        caption_style = doc.styles["CFGI Caption"]
    ccfg = styles_cfg["caption"]
    apply_font_to_style(
        caption_style,
        font_value(config, ccfg["font"]),
        scale[ccfg["size_key"]],
        colors[ccfg["color"]],
        ccfg.get("bold"),
        ccfg.get("italic"),
    )
    caption_style.paragraph_format.space_after = Pt(4)

    if "CFGI Blockquote" not in [s.name for s in doc.styles]:
        quote_style = doc.styles.add_style("CFGI Blockquote", WD_STYLE_TYPE.PARAGRAPH)
    else:
        quote_style = doc.styles["CFGI Blockquote"]
    qcfg = styles_cfg["blockquote"]
    apply_font_to_style(
        quote_style,
        font_value(config, qcfg["font"]),
        scale[qcfg["size_key"]],
        colors[qcfg["color"]],
    )
    quote_style.paragraph_format.left_indent = Inches(0.18)
    quote_style.paragraph_format.right_indent = Inches(0.08)
    quote_style.paragraph_format.space_before = Pt(4)
    quote_style.paragraph_format.space_after = Pt(6)


def apply_footer(doc: Document, config: Dict) -> None:
    colors = config["brand"]["colors"]
    fonts = config["brand"]["fonts"]
    footer_text = config["document"].get("footer_text", "")
    for section in doc.sections:
        footer = section.footer
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.clear()
        run = paragraph.add_run(footer_text)
        run.font.name = fonts["body"]
        run._element.rPr.rFonts.set(qn("w:eastAsia"), fonts["body"])
        run.font.size = Pt(config["brand"]["type_scale"]["footer_pt"])
        run.font.color.rgb = hex_to_rgb(colors["gray_mid"])
        if config["document"].get("include_page_numbers", True):
            paragraph.add_run("  |  ")
            add_page_number(paragraph)


def add_horizontal_rule(doc: Document, config: Dict) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    set_paragraph_bottom_border(p, color_value(config, "gray_light"), size="6", space="3")


def add_styled_run(paragraph, segment: Dict[str, object], config: Dict, base_color: Optional[str] = None) -> None:
    text = str(segment.get("text", ""))
    if not text:
        return
    run = paragraph.add_run(text)
    body_font = font_value(config, "body")
    run.font.name = body_font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), body_font)
    run.font.size = Pt(config["brand"]["type_scale"]["body_pt"])
    run.font.color.rgb = hex_to_rgb(color_value(config, base_color or "text"))
    run.bold = bool(segment.get("bold", False))
    run.italic = bool(segment.get("italic", False))
    if segment.get("code"):
        run.font.name = "Consolas"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        run.font.size = Pt(config["brand"]["type_scale"]["small_pt"])
    if segment.get("link"):
        link_cfg = config["styles"]["hyperlink"]
        run.font.color.rgb = hex_to_rgb(color_value(config, link_cfg["color"]))
        run.underline = link_cfg.get("underline", True)


def add_inline_paragraph(doc: Document, text: str, config: Dict, style: Optional[str] = None,
                         alignment: Optional[int] = None, base_color: Optional[str] = None):
    p = doc.add_paragraph(style=style)
    if alignment is not None:
        p.alignment = alignment
    for segment in parse_inline_segments(text):
        add_styled_run(p, segment, config, base_color=base_color)
    return p


def style_heading_paragraph(paragraph, level: int, config: Dict) -> None:
    # Applies CFGI title rule for primary document title only.
    if level == 0:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in paragraph.runs:
            if config["brand"]["title"].get("all_caps", True):
                run.text = run.text.upper()
            run.font.name = font_value(config, "heading")
            run._element.rPr.rFonts.set(qn("w:eastAsia"), font_value(config, "heading"))
            run.font.size = Pt(config["brand"]["type_scale"]["title_pt"])
            run.font.color.rgb = hex_to_rgb(color_value(config, "navy"))
            run.bold = False
            set_character_spacing(run, config["brand"]["title"].get("letter_spacing_pt", 3))
        set_paragraph_bottom_border(paragraph, color_value(config, "blue_mid"), size="10", space="5")
        return

    # Add subtle divider under H1 sections.
    if level == 1:
        set_paragraph_bottom_border(paragraph, color_value(config, "gray_light"), size="4", space="2")


def add_heading(doc: Document, raw_text: str, level: int, config: Dict, first_heading_seen: bool) -> bool:
    text = strip_markdown_links_for_toc(raw_text.strip())
    if level == 1 and not first_heading_seen:
        p = add_inline_paragraph(doc, text, config, style="Title")
        style_heading_paragraph(p, 0, config)
        return True

    if level == 1 and config["document"].get("page_break_on_h1", False) and first_heading_seen:
        doc.add_page_break()

    style_name = f"Heading {min(level, 4)}"
    p = add_inline_paragraph(doc, text, config, style=style_name)
    style_heading_paragraph(p, min(level, 4), config)
    return first_heading_seen


def add_list_item(doc: Document, line: str, config: Dict, ordered: bool = False, level: int = 0) -> None:
    cleaned = re.sub(r"^\s*([-+*])\s+", "", line)
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned)
    style = "List Number" if ordered else "List Bullet"
    p = add_inline_paragraph(doc, cleaned, config, style=style)
    p.paragraph_format.left_indent = Inches(0.25 + level * 0.2)
    p.paragraph_format.first_line_indent = Inches(-0.15)
    for run in p.runs:
        run.font.name = font_value(config, "body")
        run._element.rPr.rFonts.set(qn("w:eastAsia"), font_value(config, "body"))
        run.font.color.rgb = hex_to_rgb(color_value(config, "text"))


def classify_callout(text: str, config: Dict) -> Dict[str, str]:
    upper = text.upper()
    for rule in config["callouts"].values():
        if any(keyword.upper() in upper for keyword in rule.get("keywords", [])):
            return rule
    return config["styles"]["blockquote"]


def add_blockquote(doc: Document, lines: Sequence[str], config: Dict) -> None:
    text = "\n".join(re.sub(r"^\s*>\s?", "", line).strip() for line in lines).strip()
    rule = classify_callout(text, config)
    p = add_inline_paragraph(doc, text, config, style="CFGI Blockquote", base_color=rule.get("text", "text"))
    set_paragraph_shading(p, color_value(config, rule.get("fill", rule.get("background", "bg_light"))))
    set_paragraph_left_border(p, color_value(config, rule.get("border", "blue_mid")))
    for run in p.runs:
        run.font.color.rgb = hex_to_rgb(color_value(config, rule.get("text", "text")))
        if rule.get("text") == "white":
            run.bold = True


def add_table(doc: Document, table_block: TableBlock, config: Dict) -> None:
    rows_count = 1 + len(table_block.rows)
    cols_count = max(1, len(table_block.header))
    table = doc.add_table(rows=rows_count, cols=cols_count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = bool(config["tables"].get("autofit", True))

    header_fill = color_value(config, config["tables"]["header_fill"])
    header_text = color_value(config, config["tables"]["header_text"])
    body_text = color_value(config, config["tables"]["body_text"])
    border = color_value(config, config["tables"]["border"])
    row_fills = [color_value(config, c) for c in config["tables"].get("row_fills", ["white", "bg_light"])]
    font_name = font_value(config, config["tables"]["font"])
    font_size = Pt(config["tables"]["font_size_pt"])
    margin = int(config["tables"].get("cell_margin_twips", 80))

    # Header row.
    for col_idx, value in enumerate(table_block.header):
        cell = table.cell(0, col_idx)
        cell.text = ""
        set_cell_shading(cell, header_fill)
        set_cell_borders(cell, border)
        set_cell_margins(cell, margin)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for segment in parse_inline_segments(value):
            add_styled_run(p, segment, config, base_color="white")
        for run in p.runs:
            run.font.name = font_name
            run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
            run.font.size = font_size
            run.font.color.rgb = hex_to_rgb(header_text)
            run.bold = True

    if config["tables"].get("repeat_header_row", True):
        set_repeat_table_header(table.rows[0])

    # Body rows.
    for row_idx, row_values in enumerate(table_block.rows, start=1):
        fill = row_fills[(row_idx - 1) % len(row_fills)]
        for col_idx in range(cols_count):
            value = row_values[col_idx] if col_idx < len(row_values) else ""
            cell = table.cell(row_idx, col_idx)
            cell.text = ""
            set_cell_shading(cell, fill)
            set_cell_borders(cell, border)
            set_cell_margins(cell, margin)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            p = cell.paragraphs[0]
            alignment = table_block.align[col_idx] if col_idx < len(table_block.align) else "left"
            if alignment == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif alignment == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for segment in parse_inline_segments(value):
                add_styled_run(p, segment, config, base_color="text")
            for run in p.runs:
                run.font.name = font_name
                run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
                run.font.size = font_size
                run.font.color.rgb = hex_to_rgb(body_text)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_image_if_exists(doc: Document, markdown_image_line: str, markdown_path: Path, config: Dict) -> bool:
    """Add image from Markdown syntax if the referenced local file exists."""
    m = re.match(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$", markdown_image_line)
    if not m:
        return False
    caption, path_text = m.group(1), m.group(2).strip().strip('"')
    img_path = Path(path_text)
    if not img_path.is_absolute():
        img_path = markdown_path.parent / img_path
    if not img_path.exists():
        add_inline_paragraph(doc, f"[Image not found: {path_text}]", config, style="CFGI Caption")
        return True
    max_width = Inches(config["markdown"].get("image_max_width_inches", 6.75))
    doc.add_picture(str(img_path), width=max_width)
    if caption:
        add_inline_paragraph(doc, caption, config, style="CFGI Caption", alignment=WD_ALIGN_PARAGRAPH.CENTER)
    return True


# =============================================================================
# CONVERSION ENGINE
# =============================================================================

def convert_markdown_to_docx(input_md: Path, output_docx: Path, config: Dict) -> None:
    raw = input_md.read_text(encoding="utf-8")
    if config["document"].get("strip_yaml_front_matter", True):
        raw, _metadata = strip_front_matter(raw)
    text = normalize_markdown(raw)

    if config["document"].get("remove_template_variable_catalog", False):
        text = re.split(r"(?im)^#\s+Appendix\s+F\s+\|\s+Template Variable Catalog\s*$", text)[0].rstrip()

    doc = Document()
    configure_document(doc, config)

    if config["document"].get("include_generated_toc", False):
        toc_heading = doc.add_paragraph("Table of Contents", style="Heading 1")
        style_heading_paragraph(toc_heading, 1, config)
        toc_p = doc.add_paragraph()
        add_toc_field(toc_p)
        doc.add_page_break()

    lines = text.splitlines()
    i = 0
    first_heading_seen = False
    paragraph_buffer: List[str] = []

    def flush_paragraph_buffer() -> None:
        nonlocal paragraph_buffer
        if paragraph_buffer:
            para_text = " ".join(x.strip() for x in paragraph_buffer if x.strip()).strip()
            if para_text:
                add_inline_paragraph(doc, para_text, config)
            paragraph_buffer = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph_buffer()
            i += 1
            continue

        # Horizontal rule / section divider.
        if is_horizontal_rule(line, config):
            flush_paragraph_buffer()
            add_horizontal_rule(doc, config)
            i += 1
            continue

        # Markdown table.
        table_block, new_i = parse_table(lines, i)
        if table_block:
            flush_paragraph_buffer()
            add_table(doc, table_block, config)
            i = new_i
            continue

        # Blockquote / callout. Collapse consecutive blockquote lines.
        if stripped.startswith(">"):
            flush_paragraph_buffer()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i])
                i += 1
            add_blockquote(doc, quote_lines, config)
            continue

        # Headings.
        hm = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if hm:
            flush_paragraph_buffer()
            level = len(hm.group(1))
            heading_text = hm.group(2).strip()
            first_heading_seen = add_heading(doc, heading_text, level, config, first_heading_seen)
            i += 1
            continue

        # Images.
        if add_image_if_exists(doc, line, input_md, config):
            flush_paragraph_buffer()
            i += 1
            continue

        # Lists.
        if re.match(r"^\s*[-+*]\s+", line):
            flush_paragraph_buffer()
            indent_spaces = len(line) - len(line.lstrip(" "))
            add_list_item(doc, line, config, ordered=False, level=indent_spaces // 2)
            i += 1
            continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph_buffer()
            indent_spaces = len(line) - len(line.lstrip(" "))
            add_list_item(doc, line, config, ordered=True, level=indent_spaces // 2)
            i += 1
            continue

        # Everything else gets accumulated into paragraphs, allowing hard-wrapped Markdown.
        paragraph_buffer.append(line)
        i += 1

    flush_paragraph_buffer()

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_docx))


def load_config(config_path: Optional[Path]) -> Dict:
    config = copy.deepcopy(DEFAULT_CONFIG)
    if config_path:
        overrides = json.loads(config_path.read_text(encoding="utf-8"))
        config = deep_merge(config, overrides)
    return config


def infer_output_path(input_md: Path, output_arg: Optional[str], config: Dict) -> Path:
    if output_arg:
        return Path(output_arg)
    suffix = config["document"].get("default_output_suffix", "_CFGI.docx")
    return input_md.with_name(input_md.stem + suffix)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a built PharmmaEssential Markdown deliverable into a CFGI-branded Word document."
    )
    parser.add_argument("input_md", help="Path to the built output Markdown file.")
    parser.add_argument("-o", "--output", help="Output .docx path. Defaults to <input>_CFGI.docx.")
    parser.add_argument("--config", help="Optional JSON file with modular style/config overrides.")
    parser.add_argument("--include-generated-toc", action="store_true", help="Insert a Word-generated TOC field before content.")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation, helpful for wide process tables.")
    parser.add_argument("--page-break-on-h1", action="store_true", help="Start each H1 section on a new page after the title.")
    parser.add_argument("--remove-template-variable-catalog", action="store_true", help="Drop Appendix F variable catalog if present.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    input_md = Path(args.input_md)
    if not input_md.exists():
        print(f"ERROR: Input Markdown file not found: {input_md}", file=sys.stderr)
        return 2
    if input_md.suffix.lower() not in {".md", ".markdown", ".txt"}:
        print(f"WARNING: Input file does not look like Markdown: {input_md}", file=sys.stderr)

    config = load_config(Path(args.config) if args.config else None)
    if args.include_generated_toc:
        config["document"]["include_generated_toc"] = True
    if args.landscape:
        config["document"]["orientation"] = "landscape"
    if args.page_break_on_h1:
        config["document"]["page_break_on_h1"] = True
    if args.remove_template_variable_catalog:
        config["document"]["remove_template_variable_catalog"] = True

    output_docx = infer_output_path(input_md, args.output, config)
    convert_markdown_to_docx(input_md, output_docx, config)
    print(f"Created: {output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
