#!/usr/bin/env python3
"""Traceability and orphan report.

  trace.py --ledger-dir D [--json]

Reports: F->T->R->I counts, orphans at every layer (a finding in no theme,
a theme in no recommendation, ...), and findings per source document.
Orphans are not errors; they are either noise to retire or a gap to fill,
and the orchestrator should surface them to a human either way.
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import EVIDENCE_TYPES, current, ledger_dir, load_taxonomy, md_table, primary_axis  # noqa: E402


def build(ldir, tax=None):
    F = current(ldir, "findings")
    T = current(ldir, "themes")
    R = current(ldir, "recommendations")
    I = current(ldir, "initiatives")

    f2t, t2r, r2i = defaultdict(list), defaultdict(list), defaultdict(list)
    for tid, t in T.items():
        for f in t.get("findings", []):
            f2t[f].append(tid)
    for rid, r in R.items():
        for t in r.get("themes", []):
            t2r[t].append(rid)
    for iid, i in I.items():
        for r in i.get("recommendations", []):
            r2i[r].append(iid)

    # findings directly cited by recs (allowed) count as covered
    f_direct = {f for r in R.values() for f in r.get("findings", [])}

    orphans = {
        "findings_in_no_theme": sorted(f for f in F if f not in f2t and f not in f_direct),
        "themes_in_no_recommendation": sorted(t for t in T if t not in t2r),
        "recommendations_in_no_initiative": sorted(r for r in R if r not in r2i),
    }
    strengths_unthemed = [f for f in orphans["findings_in_no_theme"] if F[f].get("type") == "strength"]

    coverage = Counter(s.split(":")[0] for f in F.values() for s in f.get("sources", []))
    by_author = Counter(f.get("author") for f in F.values())

    # full chain per initiative
    chains = []
    for iid, i in I.items():
        recs = i.get("recommendations", [])
        themes = sorted({t for r in recs for t in R.get(r, {}).get("themes", [])})
        finds = sorted({f for t in themes for f in T.get(t, {}).get("findings", [])} |
                       {f for r in recs for f in R.get(r, {}).get("findings", [])})
        chains.append({"initiative": iid, "recommendations": recs, "themes": themes, "findings": finds})

    coverage_by_category, uncovered, thin = {}, [], []
    if tax:
        pa = primary_axis(tax)
        for c in tax["axes"][pa]["values"]:
            n = sum(1 for f in F.values() if f["type"] in EVIDENCE_TYPES and (c in f.get(pa, []) if isinstance(f.get(pa), list) else f.get(pa) == c))
            coverage_by_category[c] = n
            (uncovered if n == 0 else thin if n <= 2 else []).append(c)

    return {
        "counts": {"findings": len(F), "themes": len(T), "recommendations": len(R), "initiatives": len(I),
                   "open_items": sum(1 for f in F.values() if f["type"] == "open_item")},
        "coverage_by_category": coverage_by_category, "uncovered_categories": uncovered, "thin_categories": thin,
        "orphans": orphans,
        "strengths_unthemed": strengths_unthemed,
        "coverage_by_source": dict(sorted(coverage.items())),
        "findings_by_author": dict(by_author),
        "finding_to_themes": dict(f2t),
        "theme_to_recommendations": dict(t2r),
        "recommendation_to_initiatives": dict(r2i),
        "chains": chains,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ledger-dir")
    p.add_argument("--json", action="store_true")
    p.add_argument("--taxonomy", help="enables coverage-by-category and the uncovered/thin report")
    a = p.parse_args()
    rep = build(ledger_dir(a.ledger_dir), load_taxonomy(a.taxonomy) if a.taxonomy else None)
    if a.json:
        print(json.dumps(rep, indent=2))
        return

    c = rep["counts"]
    print(f"## Traceability\n\n{c['findings']} findings -> {c['themes']} themes -> "
          f"{c['recommendations']} recommendations -> {c['initiatives']} initiatives\n")
    print("## Orphans\n")
    for k, v in rep["orphans"].items():
        note = ""
        if k == "findings_in_no_theme" and rep["strengths_unthemed"]:
            note = f"  ({len(rep['strengths_unthemed'])} are strengths - may be intentional)"
        print(f"- {k}: {len(v)}{note}" + (f" -> {', '.join(v)}" if v else ""))
    if rep["coverage_by_category"]:
        print("\n## Coverage by category (primary axis)\n")
        print(md_table(["category", "evidence findings"], [[c, n] for c, n in rep["coverage_by_category"].items()]))
        if rep["uncovered_categories"]:
            print(f"\nUNCOVERED (zero findings): {', '.join(rep['uncovered_categories'])} - a scope decision or a hole; say which")
        if rep["thin_categories"]:
            print(f"THIN (<=2 findings): {', '.join(rep['thin_categories'])}")
    print("\n## Coverage by source\n")
    print(md_table(["source", "findings"], [[s, n] for s, n in rep["coverage_by_source"].items()]))
    print("\n## Findings by author\n")
    print(md_table(["author", "findings"], [[s, n] for s, n in rep["findings_by_author"].items()]))
    if rep["chains"]:
        print("\n## Chains\n")
        print(md_table(["initiative", "recs", "themes", "findings"],
                       [[ch["initiative"], len(ch["recommendations"]), len(ch["themes"]), len(ch["findings"])]
                        for ch in rep["chains"]]))


if __name__ == "__main__":
    main()
