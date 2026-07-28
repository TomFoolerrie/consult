"""Tests for scripts/engagement.py — the cross-area duplication audit."""
import json
from pathlib import Path

import engagement


LONG = ("The sales package is assembled from the trial balance schedules "
        "and circulated to the site controllers for sign-off.")


def make_engagement(tmp_path: Path) -> Path:
    root = tmp_path / "components"
    for area, procs in {
        "fscp": [("sales-package-preparation", "Sales Package Preparation",
                  f"## Sales Package Preparation\n\n{LONG}\n"),
                 ("close-calendar", "Close Calendar Management",
                  "## Close Calendar Management\n\nOwn text here.\n")],
        "inventory": [("cycle-counts", "Cycle Counts",
                       f"## Cycle Counts\n\nCounting text.\n\n{LONG}\n\n"
                       "The sales package preparation is described here "
                       "too.\n"),
                      ("sales-package-prep", "Preparation of the Sales "
                       "Package",
                       "## Preparation of the Sales Package\n\nDup.\n")],
    }.items():
        d = root / area
        d.mkdir(parents=True)
        comps = [{"file": f"10_{s}.md", "role": "procedure", "slug": s,
                  "heading": h, "order": 10 + i}
                 for i, (s, h, _) in enumerate(procs)]
        (d / "manifest.json").write_text(json.dumps(
            {"area": area, "title": area.upper(), "components": comps}),
            encoding="utf-8")
        for s, _h, text in procs:
            (d / f"10_{s}.md").write_text(text, encoding="utf-8")
    return root


def test_audit_finds_all_three_shapes(tmp_path, capsys):
    root = make_engagement(tmp_path)
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    # twin L3s: 'Sales Package Preparation' vs 'Preparation of the Sales
    # Package' (token containment across word order)
    assert "fscp/sales-package-preparation" in out
    assert "inventory/sales-package-prep" in out
    # cross mention: inventory prose names fscp's procedure title
    assert "names 'Sales Package Preparation'" in out
    # shared prose: the identical long sentence in both areas
    assert "shared sentence(s)" in out
    assert "finding(s)." in out


def test_clean_engagement_reports_clean(tmp_path, capsys):
    root = make_engagement(tmp_path)
    # remove the duplication: distinct titles, distinct prose
    inv = root / "inventory"
    m = json.loads((inv / "manifest.json").read_text(encoding="utf-8"))
    m["components"] = [c for c in m["components"]
                       if c["slug"] == "cycle-counts"]
    (inv / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    (inv / "10_cycle-counts.md").write_text(
        "## Cycle Counts\n\nEntirely distinct counting prose that shares "
        "nothing with the close process narrative at all.\n",
        encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert "Clean: no cross-area duplication detected." in out


def test_single_area_engagement_explains_layout(tmp_path, capsys):
    root = tmp_path / "components"
    (root / "only").mkdir(parents=True)
    (root / "only" / "manifest.json").write_text(
        json.dumps({"area": "only", "components": []}), encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    assert "at least two scoped areas" in capsys.readouterr().out


def test_missing_root_exits_2(tmp_path, capsys):
    assert engagement.main(["audit", str(tmp_path / "nope")]) == 2
    assert "engagement root" in capsys.readouterr().err


def test_note_queues_review_item_idempotently(tmp_path, capsys):
    root = make_engagement(tmp_path)
    area = root / "inventory"
    args = ["note", str(area), "--slug", "cycle-counts", "--note",
            "Reduce the sales package text to a handoff; owner is "
            "fscp/sales-package-preparation."]
    assert engagement.main(args) == 0
    assert "queued 1 review note" in capsys.readouterr().out
    notes = (area / "_review" / "cycle-counts.notes.yaml") \
        .read_text(encoding="utf-8")
    assert 'kind: "review"' in notes and "handoff" in notes
    # idempotent: same note again is a no-op
    assert engagement.main(args) == 0
    assert "no-op" in capsys.readouterr().out


def test_note_unknown_slug_exits_2(tmp_path, capsys):
    root = make_engagement(tmp_path)
    assert engagement.main(["note", str(root / "inventory"),
                            "--slug", "nope", "--note", "x"]) == 2
    assert "cycle-counts" in capsys.readouterr().err
