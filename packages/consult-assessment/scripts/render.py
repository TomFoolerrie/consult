#!/usr/bin/env python3
"""Render ledgers into tables, figure specs, and the assessment-output bundle.

  render.py tables|figures|bundle --manifest M                    # locations from the manifest's paths block
  render.py tables|figures|bundle --ledger-dir D --taxonomy T --out OUT/   # standalone: OUT/tables, OUT/figures, OUT/story.md, OUT/assessment-output.json

Figure specs are brand-agnostic JSON: {id, type, title, question, data, sources}.
A brand renderer turns them into slides. The story writer references
figures by id and never computes its own numbers.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EVIDENCE_TYPES, axes, current, ledger_dir, load_taxonomy, md_table, primary_axis, resolve_manifest  # noqa: E402
from trace import build as build_trace  # noqa: E402


def load_all(ldir):
    return {k: current(ldir, k) for k in ("findings", "themes", "recommendations", "initiatives")}


# ---------------------------------------------------------------- tables
def vals(r, name):
    v = r.get(name)
    return v if isinstance(v, list) else ([] if v in (None, "") else [v])


def tables(ldir, tax, paths):
    d = load_all(ldir)
    pa = primary_axis(tax)
    order = {c: i for i, c in enumerate(tax["axes"][pa]["values"])}
    out = Path(paths["tables"])
    out.mkdir(parents=True, exist_ok=True)
    ax_names = list(tax["axes"])

    F = sorted(d["findings"].values(), key=lambda r: (order.get(r.get(pa), 99), -r.get("severity", 0), r["id"]))
    (out / "findings.md").write_text(md_table(
        ["id", "type"] + [tax["axes"][n]["label"] for n in ax_names] + ["sev", "basis", "finding", "sources"],
        [[r["id"], r["type"]] + ["; ".join(vals(r, n)) for n in ax_names] +
         [r.get("severity"), r["evidence_basis"], r["observation"], "; ".join(r["sources"])] for r in F]), encoding="utf-8")

    t_axes = list(axes(tax, on_theme=True))
    (out / "themes.md").write_text(md_table(
        ["id", "theme", "root cause"] + [tax["axes"][n]["label"] for n in t_axes] + ["impact", "findings"],
        [[t["id"], t["theme"], t["root_cause"]] + [t.get(n, "") for n in t_axes] + [t["impact"], "; ".join(t["findings"])]
         for t in d["themes"].values()]), encoding="utf-8")

    (out / "recommendations.md").write_text(md_table(
        ["id", "solution", "principle", "what changes", "what stops", "themes"],
        [[r["id"], r["solution"], r["principle"], r.get("what_changes", ""), r.get("what_stops", ""),
          "; ".join(r["themes"])] for r in d["recommendations"].values()]), encoding="utf-8")

    (out / "initiatives.md").write_text(md_table(
        ["id", "initiative", "owner", "impact", "effort", "time", "dependencies", "success measure", "recs"],
        [[i["id"], i["initiative"], i["owner"], i["impact"], i["effort"], i["time_required"],
          "; ".join(i.get("dependencies", [])), i["success_measure"], "; ".join(i["recommendations"])]
         for i in d["initiatives"].values()]), encoding="utf-8")
    print(f"tables -> {out}")


# ---------------------------------------------------------------- figures
def fig(id_, type_, title, question, data, sources, **extra):
    spec = {"id": id_, "type": type_, "title": title, "question": question, "data": data, "sources": sorted(sources)}
    spec.update(extra)
    return spec


def figures(ldir, tax, paths):
    d = load_all(ldir)
    F, T, R, I = d["findings"], d["themes"], d["recommendations"], d["initiatives"]
    pa = primary_axis(tax)
    figs = []
    evidence = [f for f in F.values() if f["type"] in EVIDENCE_TYPES]

    # A theme has no coordinates of its own; its footprint on any axis is the
    # union of its findings' values. Figures count themes for "how many
    # problems" and findings for "how much evidence".
    def footprint(t, name):
        return {v for fid in t["findings"] if fid in F for v in vals(F[fid], name)}

    def cell_map(rows_axis, cols_axis):
        cells = defaultdict(lambda: {"findings": 0, "themes": [], "max_severity": 0, "ids": []})
        for f in evidence:
            for rv in vals(f, rows_axis):
                for cv in vals(f, cols_axis):
                    c = cells[(rv, cv)]
                    c["findings"] += 1
                    c["max_severity"] = max(c["max_severity"], f.get("severity", 0))
                    c["ids"].append(f["id"])
        for tid, t in T.items():
            for rv in footprint(t, rows_axis):
                for cv in footprint(t, cols_axis):
                    if (rv, cv) in cells:
                        cells[(rv, cv)]["themes"].append(tid)
        return cells

    # --- house figures, declared in the taxonomy -------------------------
    for spec in tax.get("figures", []):
        if spec["type"] == "heatmap":
            ra, ca = spec["rows"], spec["cols"]
            cells = cell_map(ra, ca)
            figs.append(fig(spec["id"], "heatmap", spec.get("title", spec["id"]), spec.get("question", ""),
                            {"rows": tax["axes"][ra]["values"], "cols": tax["axes"][ca]["values"],
                             "row_axis": ra, "col_axis": ca,
                             "cells": [{"row": r, "col": c, "themes": len(v["themes"]), "theme_ids": v["themes"],
                                        "findings": v["findings"], "max_severity": v["max_severity"], "ids": v["ids"]}
                                       for (r, c), v in cells.items()]},
                            {i for v in cells.values() for i in v["ids"]},
                            unit="themes (label) / findings (evidence)",
                            hint="colour = max_severity; label = themes, or findings where no theme has formed yet"))
        elif spec["type"] == "bar":
            ax = spec["axis"]
            cats = tax["axes"][ax]["values"]
            on_theme = tax["axes"][ax].get("on_theme")
            theme_counts = Counter(v for t in T.values() for v in (vals(t, ax) if on_theme else footprint(t, ax)))
            find_counts = Counter(v for f in evidence for v in vals(f, ax))
            data = {"categories": cats, "axis": ax,
                    "themes": [theme_counts.get(x, 0) for x in cats],
                    "findings": [find_counts.get(x, 0) for x in cats]}
            if spec.get("by"):
                by = spec["by"]
                by_cat = defaultdict(Counter)
                for t in T.values():
                    for bv in footprint(t, by):
                        for v in (vals(t, ax) if on_theme else footprint(t, ax)):
                            by_cat[bv][v] += 1
                data["by_axis"] = by
                data["themes_by"] = {b: [by_cat[b].get(x, 0) for x in cats] for b in tax["axes"][by]["values"] if by_cat[b]}
            figs.append(fig(spec["id"], "bar", spec.get("title", spec["id"]), spec.get("question", ""), data,
                            set(T) | {f["id"] for f in evidence},
                            unit="themes (primary series) / findings (evidence series)",
                            hint="if no themes exist yet, render the findings series alone and say so"))
        else:
            print(f"figure {spec.get('id')}: unknown type {spec['type']} (heatmap|bar)", file=sys.stderr)

    # --- method figures, always -----------------------------------------
    # Scorecard by the primary axis
    theme_by_pa = defaultdict(set)
    for tid, t in T.items():
        for v in footprint(t, pa):
            theme_by_pa[v].add(tid)
    rows = []
    for c in tax["axes"][pa]["values"]:
        fs = [f for f in F.values() if c in vals(f, pa)]
        if not fs:
            continue
        gaps = [f for f in fs if f["type"] in EVIDENCE_TYPES]
        rows.append({"category": c, "findings": len(gaps), "strengths": len(fs) - len(gaps),
                     "max_severity": max((f.get("severity", 0) for f in gaps), default=0),
                     "high": sum(1 for f in gaps if f.get("severity") == max((int(k) for k in tax["scales"]["severity"]), default=3)),
                     "themes": sorted(theme_by_pa[c]), "ids": [f["id"] for f in fs]})
    figs.append(fig("fig-scorecard", "table", f"{tax['axes'][pa]['label']} scorecard",
                    f"How does each {tax['axes'][pa]['label'].lower()} stand overall?", {"axis": pa, "rows": rows},
                    {i for r in rows for i in r["ids"]}, unit="themes (problems) + findings (evidence) per category"))

    # 4. Theme cards
    cards = []
    t_axes = list(axes(tax, on_theme=True))
    for t in T.values():
        fs = [F[f] for f in t["findings"] if f in F]
        cards.append({"id": t["id"], "theme": t["theme"], "root_cause": t["root_cause"], "impact": t["impact"],
                      **{n: t.get(n) for n in t_axes},
                      "finding_count": len(fs), "footprint": sorted(footprint(t, pa)),
                      "max_severity": max((f.get("severity", 0) for f in fs), default=0),
                      "findings": t["findings"],
                      "recommendations": [r["id"] for r in R.values() if t["id"] in r["themes"]]})
    figs.append(fig("fig-themes", "cards", "Themes", "What are the underlying patterns?", {"cards": cards}, set(T), unit="themes"))

    # 5. Prioritization 2x2
    pts = [{"id": i["id"], "label": i["initiative"], "impact": i["impact"], "effort": i["effort"], "owner": i["owner"]}
           for i in I.values()]
    figs.append(fig("fig-priority", "quadrant", "Initiative prioritization", "What should we do first?",
                    {"x": "effort", "y": "impact", "points": pts,
                     "quadrants": {"high_impact_low_effort": "Quick wins", "high_impact_high_effort": "Strategic",
                                   "low_impact_low_effort": "Fill-ins", "low_impact_high_effort": "Reconsider"}},
                    set(I), unit="initiatives"))

    # 6. Roadmap (dependency-ordered)
    items = [{"id": i["id"], "label": i["initiative"], "time_required": i["time_required"],
              "dependencies": i.get("dependencies", []), "owner": i["owner"]} for i in I.values()]
    figs.append(fig("fig-roadmap", "timeline", "Roadmap", "In what order, and how long?",
                    {"items": items}, set(I), unit="initiatives", hint="sequence by dependencies; time_required is free text"))

    # 7. Traceability
    tr = build_trace(ldir)
    figs.append(fig("fig-trace", "funnel", "How we got here",
                    "How many findings roll up into how many actions?",
                    {"stages": [["findings", tr["counts"]["findings"]], ["themes", tr["counts"]["themes"]],
                                ["recommendations", tr["counts"]["recommendations"]],
                                ["initiatives", tr["counts"]["initiatives"]]],
                     "orphans": tr["orphans"]}, set(), unit="counts per layer"))

    # 8. Evidence coverage
    figs.append(fig("fig-coverage", "bar", "Evidence base", "Which sources drove the findings?",
                    {"categories": list(tr["coverage_by_source"]), "values": list(tr["coverage_by_source"].values()),
                     "evidence_basis": dict(Counter(f["evidence_basis"] for f in F.values()))},
                    set(F), unit="findings"))

    # 8b. Unthemed: seen, sourced, did not form a pattern. Stays visible.
    themed = {f for t in T.values() for f in t["findings"]} | {f for r in R.values() for f in r.get("findings", [])}
    unthemed = [{"id": f["id"], "type": f["type"], "category": f.get(pa), "severity": f.get("severity"),
                 "text": f["observation"]} for f in F.values() if f["id"] not in themed and f["type"] in EVIDENCE_TYPES]
    figs.append(fig("fig-unthemed", "list", "Observations outside the themes",
                    "What did we see that did not form a pattern?", {"items": unthemed},
                    {u["id"] for u in unthemed}, unit="findings",
                    hint="appendix by default; promote any severity-3 item into the main deck"))

    # 8c. Open items: not discussed / outstanding / to ask. Not evidence about the client.
    opens = [{"id": f["id"], "category": f.get(pa), "text": f["observation"], "sources": f["sources"]}
             for f in F.values() if f["type"] == "open_item"]
    figs.append(fig("fig-open-items", "list", "Open items and scope gaps",
                    "What did we not get to, and what is still outstanding?", {"items": opens},
                    {o["id"] for o in opens}, unit="findings",
                    hint="appendix or workplan; never in the findings narrative"))

    # 9. Strengths (what's working - for the validation beat in the story)
    strengths = [{"id": f["id"], "category": f.get(pa), "text": f["observation"]}
                 for f in F.values() if f["type"] == "strength"]
    figs.append(fig("fig-strengths", "list", "What is working", "What should the client keep doing?",
                    {"items": strengths}, {s["id"] for s in strengths}, unit="findings"))

    fdir = Path(paths["figures"])
    fdir.mkdir(parents=True, exist_ok=True)
    for s in figs:
        (fdir / f"{s['id']}.json").write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    (fdir / "catalog.md").write_text("# Figure catalog\n\n" + md_table(
        ["id", "type", "title", "answers", "unit", "n sources"],
        [[s["id"], s["type"], s["title"], s["question"], s.get("unit", ""), len(s["sources"])] for s in figs]), encoding="utf-8")
    print(f"{len(figs)} figures -> {fdir}")
    return figs


# ---------------------------------------------------------------- bundle
def bundle(ldir, tax, paths):
    tables(ldir, tax, paths)
    figs = figures(ldir, tax, paths)
    d = load_all(ldir)
    story = Path(paths["story"])
    story_text = story.read_text(encoding="utf-8") if story.exists() else None
    story_client = None
    if story_text:
        story_client = re.sub(r"\s?\[(?:F|T|R|I|P)-\d+(?:,\s*(?:F|T|R|I|P)-\d+)*\]", "", story_text)
        story_client = re.sub(r"\s?\[fig-[\w-]+\]", "", story_client)
        story_client = re.sub(r"<!--.*?-->\n?", "", story_client, flags=re.S)
        Path(str(story).replace(".md", "") + "-client.md").write_text(story_client, encoding="utf-8")
    payload = {
        "contract": "assessment-output",
        "version": "0.1",
        "taxonomy": tax,
        "ledgers": {k: list(v.values()) for k, v in d.items()},
        "trace": build_trace(ldir),
        "figures": figs,
        "story": story_text,
        "story_client": story_client,
    }
    bp = Path(paths["bundle"])
    bp.parent.mkdir(parents=True, exist_ok=True)
    bp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"bundle -> {bp}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["tables", "figures", "bundle"])
    p.add_argument("--manifest", help="take ledger dir, taxonomy, and all output locations from the manifest")
    p.add_argument("--ledger-dir")
    p.add_argument("--taxonomy")
    p.add_argument("--out", help="standalone mode: parent dir for tables/, figures/, story.md, assessment-output.json")
    a = p.parse_args()
    if a.manifest:
        m = resolve_manifest(a.manifest, Path(__file__).resolve().parent.parent)
        ldir, tax, paths = ledger_dir(m["paths"]["ledger_dir"]), load_taxonomy(m["taxonomy"]), m["paths"]
    else:
        if not (a.taxonomy and a.out):
            sys.exit("either --manifest, or --taxonomy and --out")
        out = Path(a.out)
        paths = {"tables": out / "tables", "figures": out / "figures", "story": out / "story.md",
                 "bundle": out / "assessment-output.json"}
        ldir, tax = ledger_dir(a.ledger_dir), load_taxonomy(a.taxonomy)
    {"tables": tables, "figures": figures, "bundle": bundle}[a.cmd](ldir, tax, paths)


if __name__ == "__main__":
    main()
