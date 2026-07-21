"""Tests for scripts/kits.py — per-owner review kit emission (M9).

Reuses the synthetic area from test_render (same fixture shape: roles.yaml
people lists + org-chart ranks; three procedures with resolvable, resolvable-
to-another-person, and unresolvable preparers).
"""
import json
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn

import kits
from xlsx_min import read_xlsx
from test_render import make_area


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Build kits once for the read-only assertions below."""
    area = make_area(tmp_path_factory.mktemp("kits"))
    kits.build_kits(str(area))
    return area, area / "_review" / "kits"


def test_one_folder_per_resolved_owner_plus_unassigned(built):
    """Kits are grouped one folder per kebab-cased person slug, with an
    unassigned/ fallback for procedures whose preparer resolves to nobody."""
    _, out = built
    dirs = sorted(p.name for p in out.iterdir() if p.is_dir())
    assert dirs == ["carol-chief", "jane-junior", "unassigned"]


def test_owner_resolution_biases_lowest_ranked_person(built):
    """The 'AP Clerk' role resolves to Jane Junior (deepest reports_to chain),
    not the first-listed Mark Manager — org-chart rank wins over list order."""
    _, out = built
    assert (out / "jane-junior").is_dir()
    assert not (out / "mark-manager").exists()
    # her kit carries the procedure doc named <num>_<slug>.docx
    assert (out / "jane-junior" / "1.1_vendor-onboarding.docx").is_file()


def test_gap_workbook_rows_carry_ref_column(built):
    """Gap workbook rows carry a 'Ref (do not edit)' column of slug#LOCAL-ID
    (local id, not display id) so ingest maps rows without guessing."""
    _, out = built
    rows = read_xlsx(out / "jane-junior" / "gaps_jane-junior.xlsx")
    refs = sorted(r["Ref (do not edit)"] for r in rows)
    assert refs == ["payment-run#GAP-01", "vendor-onboarding#GAP-01"]
    # display ids in the visible Gap ID column stay global
    assert sorted(r["Gap ID"] for r in rows) == ["GAP-01", "GAP-02"]
    assert all(r["Answer"] == "" and r["Status"] == "" for r in rows)


def test_gap_lands_with_its_own_owner_not_procedure_owner(built):
    """A gap whose 'Owner to confirm' resolves to Jane lands in Jane's
    workbook even though the enclosing procedure (payment-run) is Carol's."""
    _, out = built
    jane = read_xlsx(out / "jane-junior" / "gaps_jane-junior.xlsx")
    assert any(r["Ref (do not edit)"] == "payment-run#GAP-01" for r in jane)
    assert not (out / "carol-chief" / "gaps_carol-chief.xlsx").exists()
    # escalation is the resolved owner's manager from the org chart
    assert all(r["Escalation"] == "Mark Manager" for r in jane)
    assert all(r["Contact"] == "Jane Junior" for r in jane)


def test_readme_and_index_written(built):
    """Every kit gets a README.md; index.md lists each kit with its person."""
    _, out = built
    for k in ("carol-chief", "jane-junior", "unassigned"):
        assert (out / k / "README.md").is_file()
    idx = (out / "index.md").read_text(encoding="utf-8")
    assert "| `jane-junior/` | Jane Junior |" in idx
    assert "| `carol-chief/` | Carol Chief |" in idx
    assert "| `unassigned/` |" in idx
    readme = (out / "jane-junior" / "README.md").read_text(encoding="utf-8")
    assert "Review kit — Jane Junior" in readme
    assert "1.1_vendor-onboarding.docx" in readme


def test_unassigned_kit_holds_unresolvable_procedure(built):
    """The procedure whose preparer matches no role lands in unassigned/."""
    _, out = built
    assert (out / "unassigned" / "2.2_cash-application.docx").is_file()


def test_kit_docs_have_tracked_changes_and_global_ids(built):
    """Kit procedure docs open with tracked changes enforced and use the same
    display numbers / global callout ids as the full draft."""
    _, out = built
    doc = Document(str(out / "carol-chief" / "2.1_payment-run.docx"))
    settings = doc.settings.element
    assert settings.find(qn("w:trackChanges")) is not None
    dp = settings.find(qn("w:documentProtection"))
    assert dp is not None and dp.get(qn("w:edit")) == "trackedChanges"
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "2.1 Payment Run" in text
    # callouts render inside 1x1 table cells, so look there for the id
    cell_text = "\n".join(c.text for t in doc.tables
                          for row in t.rows for c in row.cells)
    assert "GAP-02" in cell_text     # global display id, not local GAP-01
    assert "GAP-01" not in cell_text


def test_screenshot_template_boxes_and_sidecar_map(built):
    """The screenshot doc has one bookmarked (scr_NNN) paste box per SC item,
    and a consult-screens-map sidecar under _review/.maps keyed by the doc id
    stamped into core properties."""
    area, out = built
    sdoc_path = out / "jane-junior" / "screenshots_jane-junior.docx"
    assert sdoc_path.is_file()
    doc = Document(str(sdoc_path))
    names = [bm.get(qn("w:name"))
             for bm in doc.element.body.iter(qn("w:bookmarkStart"))]
    scr = [n for n in names if n and n.startswith("scr_")]
    assert scr == ["scr_000"]        # jane owns vendor-onboarding's one SC
    cat = doc.core_properties.category
    assert cat.startswith("cw-screens:")
    doc_id = cat.split(":", 1)[1]
    smap = json.loads((area / "_review" / ".maps" / f"{doc_id}.json")
                      .read_text(encoding="utf-8"))
    assert smap["schema"] == "consult-screens-map/v1"
    assert smap["entries"]["scr_000"] == {
        "slug": "vendor-onboarding", "local": "SC-01", "disp": "SC-01"}


def test_build_kits_regenerates_from_scratch(tmp_path):
    """Rebuilding removes stale kit content — kits are derived artifacts."""
    area = make_area(tmp_path)
    out = area / "_review" / "kits"
    stale = out / "old-person"
    stale.mkdir(parents=True)
    (stale / "junk.txt").write_text("x", encoding="utf-8")
    kits.build_kits(str(area))
    assert not stale.exists()
    assert (out / "index.md").is_file()


def test_build_kits_requires_manifest(tmp_path):
    """An area without manifest.json is rejected."""
    d = tmp_path / "noarea"
    d.mkdir()
    with pytest.raises(SystemExit, match="no manifest.json"):
        kits.build_kits(str(d))
