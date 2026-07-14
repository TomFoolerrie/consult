#!/usr/bin/env python3
"""
kits.py — per-owner review kit emitter (M9).

    python3 scripts/kits.py <area> [-o {area}/_review/kits]

After a working-mode render, this builds one folder per process owner:

    _review/kits/
      index.md                       who got what (the send checklist)
      <person-slug>/
        README.md                    instructions (usable as the email body)
        <num>_<slug>.docx            per-L3 renders, tracked changes ON
        gaps_<person-slug>.xlsx      their gap rows (blank Answer/Status cols)
        screenshots_<person-slug>.docx  their SC items + paste boxes

Ownership is deterministic string-work over data the pipeline already has:
  - procedure owner  = B. Quick Reference "Preparer" role → roles.yaml
    `people:` → LOWEST org-chart rank (deepest reports_to = closest to the
    work); their manager is listed as the escalation.
  - gap row owner    = the gap's "Owner to confirm" role, same resolution;
    falls back to the procedure owner. A gap can land in someone's workbook
    even if they don't own the procedure — intended.
  - screenshot owner = the procedure owner (SC callouts carry no owner field).
Anything unresolvable lands in an `unassigned/` kit for human triage.

Consistency guarantees: kit docs use the SAME display numbers and global
callout display IDs as the full draft (computed from the full manifest), so
"GAP-07" means the same thing in a workbook, a kit doc, and the master copy.

Python 3, stdlib + pyyaml + python-docx.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import doc_model  # noqa: E402
import render as render_mod  # noqa: E402
from aggregate import parse_callouts, parse_bullets, split_subsections, _pick  # noqa: E402
from people import People, person_slug  # noqa: E402
from xlsx_min import write_xlsx  # noqa: E402

from docx import Document  # noqa: E402
from docx.enum.table import WD_ALIGN_VERTICAL  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Pt, RGBColor  # noqa: E402

GREEN = RGBColor(0x1A, 0x7A, 0x3D)
DARK = RGBColor(0x0F, 0x4A, 0x22)
GRAY = RGBColor(0x59, 0x59, 0x59)
FONT = "Calibri"

GAP_HEADER = ["Gap ID", "Procedure", "Question to Confirm", "Nature",
              "Contact", "Escalation", "Answer", "Status",
              "Ref (do not edit)"]
GAP_WIDTHS = [10, 30, 55, 20, 20, 20, 55, 12, 8]

STEP_RE = re.compile(r"^####\s+(.*)$")


# --------------------------------------------------------------------------- #
# extraction
# --------------------------------------------------------------------------- #

def _step_of(raw_text: str) -> dict[str, str]:
    """{callout-id: enclosing '#### Step …' heading} for one fragment."""
    out: dict[str, str] = {}
    current = ""
    for line in raw_text.splitlines():
        m = STEP_RE.match(line)
        if m:
            current = m.group(1).strip()
            continue
        cm = re.match(r"^\s*>\s*\*\*.*?[-–—]\s*([A-Z]+-[A-Z0-9-]+)\s*:\*\*", line)
        if cm:
            out[cm.group(1)] = current
    return out


def collect(folder: Path):
    """Walk the area once; return (procs, gaps, screens).

    procs:   {slug: {slug,title,number,label,file,preparer_text,owner,role}}
    gaps:    [{slug, local, disp, text, nature, owner, escalation, proc_label}]
    screens: [{slug, local, disp, text, step, owner, proc_label}]
    """
    manifest = doc_model.load_manifest(folder)
    numbers = doc_model.display_numbers(manifest)
    disp = doc_model.callout_display_ids(folder)
    ppl = People(folder)

    procs: dict[str, dict] = {}
    gaps: list[dict] = []
    screens: list[dict] = []

    for comp in manifest.get("components", []):
        if comp.get("role") != "procedure":
            continue
        slug = comp["slug"]
        fpath = folder / comp["file"]
        if not fpath.is_file():
            continue
        raw = fpath.read_text(encoding="utf-8")
        subs = split_subsections(raw)
        preparer = _pick(parse_bullets(subs.get("B", "")), "preparer")
        owner, role = ppl.contact_for_text(preparer)
        label = f"{numbers.get(slug, '')} {comp.get('heading', '')}".strip()
        procs[slug] = {
            "slug": slug, "title": comp.get("heading", ""),
            "number": numbers.get(slug, ""), "label": label,
            "file": comp["file"], "preparer_text": preparer,
            "owner": owner, "role": role,
        }
        steps = _step_of(raw)
        for c in parse_callouts(slug, raw):
            d = disp.get((slug, c["id"]), c["id"])
            if c["prefix"] == "GAP":
                o_text = c["fields"].get("Owner to confirm", "")
                g_owner, _ = ppl.contact_for_text(o_text)
                g_owner = g_owner or owner
                gaps.append({
                    "slug": slug, "local": c["id"], "disp": d,
                    "text": c["text"],
                    "nature": c["fields"].get("Nature", ""),
                    "owner": g_owner,
                    "escalation": ppl.manager_of(g_owner) if g_owner else "",
                    "proc_label": label,
                })
            elif c["prefix"] == "SC":
                screens.append({
                    "slug": slug, "local": c["id"], "disp": d,
                    "text": c["text"], "step": steps.get(c["id"], ""),
                    "owner": owner, "proc_label": label,
                })
    return procs, gaps, screens


# --------------------------------------------------------------------------- #
# screenshot template
# --------------------------------------------------------------------------- #

def _bookmark(p, name: str, bid: int) -> None:
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bid))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bid))
    pPr = p._p.find(qn("w:pPr"))
    p._p.insert(1 if pPr is not None else 0, start)
    p._p.append(end)


def _cell_border(cell, color: str = "BFBFBF") -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "dashed")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:color"), color)
        borders.append(el)
    tcPr.append(borders)


def write_screenshot_template(path: Path, person: str, items: list[dict],
                              area_title: str) -> dict:
    """One entry per SC item: heading, italic what-to-capture, a dashed paste
    box anchored with a bookmark (screens_ingest keys extraction on it).
    Returns the anchor map {bookmark: {slug, local, disp}}."""
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(10)

    h = doc.add_paragraph()
    r = h.add_run(f"Screenshot Collection — {person}")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = DARK
    sub = doc.add_paragraph()
    r = sub.add_run(area_title)
    r.italic = True
    r.font.color.rgb = GREEN

    intro = doc.add_paragraph()
    r = intro.add_run(
        "For each item below: capture the screen described, paste it INSIDE "
        "the dashed box (click in the box, then paste), and save this file. "
        "Please don't delete or reorder the entries — an empty box just means "
        "\"not available\", which is also useful to know."
    )
    r.font.color.rgb = GRAY
    doc.add_paragraph()

    entries: dict[str, dict] = {}
    for n, it in enumerate(items):
        hp = doc.add_paragraph()
        r = hp.add_run(f"{it['disp']} — {it['proc_label']}"
                       + (f"  ·  {it['step']}" if it["step"] else ""))
        r.bold = True
        r.font.color.rgb = GREEN
        dp = doc.add_paragraph()
        r = dp.add_run(it["text"])
        r.italic = True

        t = doc.add_table(rows=1, cols=1)
        c = t.cell(0, 0)
        c.width = Inches(6.3)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _cell_border(c)
        p = c.paragraphs[0]
        name = f"scr_{n:03d}"
        _bookmark(p, name, 9500 + n)
        r = p.add_run("Paste screenshot here")
        r.font.color.rgb = GRAY
        r.italic = True
        # give the box some breathing room
        trPr = t.rows[0]._tr.get_or_add_trPr()
        trH = OxmlElement("w:trHeight")
        trH.set(qn("w:val"), "2400")
        trPr.append(trH)
        doc.add_paragraph()
        entries[name] = {"slug": it["slug"], "local": it["local"], "disp": it["disp"]}

    doc_id = uuid.uuid4().hex[:12]
    doc.core_properties.category = f"cw-screens:{doc_id}"
    doc.save(str(path))
    return {"schema": "consult-screens-map/v1", "doc_id": doc_id,
            "docx": path.name, "entries": entries}


# --------------------------------------------------------------------------- #
# kit assembly
# --------------------------------------------------------------------------- #

def _readme(person: str, kit: dict, area_title: str) -> str:
    doc_lines = "\n".join(f"- `{f}`" for f in kit["docs"])
    parts = [
        f"# Review kit — {person}",
        "",
        f"_{area_title}_",
        "",
        "Hi — you own the procedures below in the current-state process",
        "documentation. Three quick asks, all in this folder:",
        "",
        "1. **Review your procedure document(s)** and correct anything that is",
        "   wrong or missing — edit directly in Word. The document opens locked",
        "   in *Reviewing* mode: every edit is recorded automatically, even if",
        "   it displays as normal text (Word's *Simple Markup* view). Just",
        "   type — nothing extra to turn on. To see your edits as redlines,",
        "   pick **All Markup** in the Review ribbon. Add comments for anything",
        "   you want to explain rather than fix.",
        doc_lines,
    ]
    if kit["gaps"]:
        parts += [
            "",
            f"2. **Answer the open questions** in `{kit['xlsx']}` — fill the",
            "   *Answer* column (and *Status* if you like). \"I don't know\" or",
            "   \"ask X instead\" are useful answers too.",
        ]
    if kit["screens"]:
        parts += [
            "",
            f"3. **Capture the screenshots** listed in `{kit['screens_doc']}` —",
            "   paste each one inside its dashed box and save.",
        ]
    parts += [
        "",
        "When you're done, send the whole folder back. Thank you!",
        "",
    ]
    return "\n".join(parts)


def build_kits(area: str, out_dir: str | None = None) -> int:
    folder = Path(area).resolve()
    if not (folder / "manifest.json").is_file():
        raise SystemExit(f"error: no manifest.json in {folder}")
    manifest = doc_model.load_manifest(folder)
    area_title = manifest.get("title", folder.name)

    procs, gaps, screens = collect(folder)

    out = Path(out_dir) if out_dir else folder / "_review" / "kits"
    if out.exists():
        shutil.rmtree(out)   # kits are derived artifacts; regenerate whole
    out.mkdir(parents=True)

    # group work by person (fallback: role-<slug>, then unassigned)
    def key_of(owner: str, role: str) -> str:
        if owner:
            return person_slug(owner)
        if role:
            return f"role-{role}"
        return "unassigned"

    kits: dict[str, dict] = {}

    def kit_for(owner: str, role: str) -> dict:
        k = key_of(owner, role)
        return kits.setdefault(k, {
            "key": k, "person": owner or (role and f"({role} — no person mapped)")
            or "(unassigned)",
            "procs": [], "gap_rows": [], "screen_items": [],
            "docs": [], "xlsx": "", "screens_doc": "", "gaps": 0, "screens": 0,
        })

    for p in procs.values():
        kit_for(p["owner"], p["role"])["procs"].append(p)
    for g in gaps:
        kit_for(g["owner"], procs.get(g["slug"], {}).get("role", ""))[
            "gap_rows"].append(g)
    for s in screens:
        kit_for(s["owner"], procs.get(s["slug"], {}).get("role", ""))[
            "screen_items"].append(s)

    maps_dir = folder / "_review" / ".maps"
    maps_dir.mkdir(parents=True, exist_ok=True)

    for k, kit in sorted(kits.items()):
        kdir = out / k
        kdir.mkdir(parents=True)

        for p in sorted(kit["procs"], key=lambda x: x["number"]):
            fname = f"{p['number']}_{p['slug']}.docx"
            render_mod.render_folder(
                folder, kdir / fname, mode="working", slugs=[p["slug"]],
                track_changes=True, emit_signal=False)
            kit["docs"].append(fname)

        if kit["gap_rows"]:
            kit["gaps"] = len(kit["gap_rows"])
            kit["xlsx"] = f"gaps_{k}.xlsx"
            rows = [[g["disp"], g["proc_label"], g["text"], g["nature"],
                     g["owner"], g["escalation"], "", "",
                     f"{g['slug']}#{g['local']}"]
                    for g in sorted(kit["gap_rows"],
                                    key=lambda g: (g["proc_label"], g["disp"]))]
            write_xlsx(kdir / kit["xlsx"], GAP_HEADER, rows,
                       sheet_name="Open Questions", widths=GAP_WIDTHS)

        if kit["screen_items"]:
            kit["screens"] = len(kit["screen_items"])
            kit["screens_doc"] = f"screenshots_{k}.docx"
            items = sorted(kit["screen_items"],
                           key=lambda s: (s["proc_label"], s["disp"]))
            smap = write_screenshot_template(
                kdir / kit["screens_doc"], kit["person"], items, area_title)
            (maps_dir / f"{smap['doc_id']}.json").write_text(
                json.dumps(smap, indent=1, ensure_ascii=False) + "\n",
                encoding="utf-8")

        (kdir / "README.md").write_text(_readme(kit["person"], kit, area_title),
                                        encoding="utf-8")

    # index
    lines = [f"# Review kits — {area_title}", "",
             "| Kit | Person | Procedures | Gaps | Screenshots |",
             "|---|---|---|---|---|"]
    for k, kit in sorted(kits.items()):
        pl = ", ".join(p["number"] for p in
                       sorted(kit["procs"], key=lambda x: x["number"])) or "—"
        lines.append(f"| `{k}/` | {kit['person']} | {pl} | "
                     f"{kit['gaps']} | {kit['screens']} |")
    lines += ["", "Send each folder to its person; returned files go to "
              "`_review/returned/`.", ""]
    (out / "index.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"kits: {len(kits)} kit(s) under {out}")
    for k, kit in sorted(kits.items()):
        print(f"  {k}: {len(kit['procs'])} doc(s), {kit['gaps']} gap(s), "
              f"{kit['screens']} screenshot item(s)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Emit per-owner review kits (M9)")
    ap.add_argument("area", help="area folder")
    ap.add_argument("-o", "--out", default=None, help="kits output dir")
    a = ap.parse_args(argv)
    return build_kits(a.area, a.out)


if __name__ == "__main__":
    sys.exit(main())
