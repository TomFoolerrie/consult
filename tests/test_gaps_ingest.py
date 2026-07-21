"""Tests for scripts/gaps_ingest.py — gap-workbook return-trip (M9)."""
from pathlib import Path

import yaml

import gaps_ingest
from gaps_ingest import UNASSIGNED, ingest_workbook
from xlsx_min import write_xlsx

HEADER = ["Gap ID", "Procedure", "Question to Confirm", "Nature",
          "Contact", "Escalation", "Answer", "Status", "Ref (do not edit)"]


def make_area(tmp_path: Path) -> Path:
    area = tmp_path / "ap"
    (area / "_review" / "returned").mkdir(parents=True)
    return area


def make_workbook(path: Path, rows: list[list[str]]) -> Path:
    write_xlsx(path, HEADER, rows, sheet_name="Open Questions")
    return path


def load_notes(area: Path, slug: str) -> dict:
    f = area / "_review" / f"{slug}.notes.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def test_answered_row_appends_note_via_ref(tmp_path):
    """A row with a non-empty Answer becomes a note in
    _review/<slug>.notes.yaml, routed by the Ref column's slug#LOCAL-ID."""
    area = make_area(tmp_path)
    wb = make_workbook(tmp_path / "gaps.xlsx", [
        ["GAP-02", "1.1 Vendor Onboarding", "Approval threshold?", "Missing",
         "Jane", "Mark", "USD 5,000", "Answered", "vendor-onboarding#GAP-01"],
    ])
    total, unmatched = ingest_workbook(area, wb)
    assert (total, unmatched) == (1, 0)
    notes = load_notes(area, "vendor-onboarding")
    assert notes["procedure"] == "vendor-onboarding"
    (item,) = notes["items"]
    assert item["note"] == "GAP-01 answered: USD 5,000 [status: Answered]"
    assert item["type"] == "comment"
    assert item["anchor"] == "Approval threshold?"
    assert item["source"] == "gaps.xlsx"


def test_empty_answer_rows_are_skipped(tmp_path):
    """Rows with a blank Answer are ignored — no notes file is created."""
    area = make_area(tmp_path)
    wb = make_workbook(tmp_path / "gaps.xlsx", [
        ["GAP-01", "1.1 X", "Q?", "Missing", "", "", "", "",
         "vendor-onboarding#GAP-01"],
        ["GAP-02", "1.1 X", "Q2?", "Missing", "", "", "   ", "",
         "vendor-onboarding#GAP-02"],
    ])
    total, unmatched = ingest_workbook(area, wb)
    assert (total, unmatched) == (0, 0)
    assert not (area / "_review" / "vendor-onboarding.notes.yaml").exists()


def test_damaged_ref_falls_back_to_unassigned(tmp_path):
    """An answered row whose Ref lost its slug#id shape lands in the
    _unassigned notes bucket and is counted as unmatched — never dropped."""
    area = make_area(tmp_path)
    wb = make_workbook(tmp_path / "gaps.xlsx", [
        ["GAP-03", "2.1 Y", "Cut-off time?", "Missing", "", "",
         "4pm ET", "", "oops no hash"],
    ])
    total, unmatched = ingest_workbook(area, wb)
    assert (total, unmatched) == (1, 1)
    notes = load_notes(area, UNASSIGNED)
    (item,) = notes["items"]
    assert item["note"].startswith("GAP-03 answered: 4pm ET")


def test_reingest_is_idempotent(tmp_path):
    """Ingesting the same workbook twice adds no duplicate notes."""
    area = make_area(tmp_path)
    wb = make_workbook(tmp_path / "gaps.xlsx", [
        ["GAP-01", "1.1 X", "Q?", "", "", "", "Yes", "",
         "vendor-onboarding#GAP-01"],
    ])
    assert ingest_workbook(area, wb)[0] == 1
    assert ingest_workbook(area, wb)[0] == 0
    assert len(load_notes(area, "vendor-onboarding")["items"]) == 1


def test_main_sweeps_returned_and_archives(tmp_path, capsys):
    """With no explicit files, main sweeps _review/returned/*.xlsx and moves
    each processed workbook to _review/processed/."""
    area = make_area(tmp_path)
    returned = area / "_review" / "returned"
    make_workbook(returned / "gaps_jane.xlsx", [
        ["GAP-01", "1.1 X", "Q?", "", "", "", "Answer text", "",
         "vendor-onboarding#GAP-01"],
    ])
    assert gaps_ingest.main([str(area)]) == 0
    assert not (returned / "gaps_jane.xlsx").exists()
    assert (area / "_review" / "processed" / "gaps_jane.xlsx").is_file()
    assert (area / "_review" / "vendor-onboarding.notes.yaml").is_file()
    assert "ingested 1 answer(s)" in capsys.readouterr().out


def test_main_no_archive_keeps_workbook_in_place(tmp_path):
    """--no-archive ingests but leaves the workbook where it was."""
    area = make_area(tmp_path)
    returned = area / "_review" / "returned"
    make_workbook(returned / "gaps.xlsx", [
        ["GAP-01", "1.1 X", "Q?", "", "", "", "A", "",
         "vendor-onboarding#GAP-01"],
    ])
    assert gaps_ingest.main([str(area), "--no-archive"]) == 0
    assert (returned / "gaps.xlsx").exists()
    assert not (area / "_review" / "processed").exists()


def test_main_no_workbooks_is_a_noop(tmp_path, capsys):
    """An empty returned/ dir exits 0 with a friendly message."""
    area = make_area(tmp_path)
    assert gaps_ingest.main([str(area)]) == 0
    assert "no workbooks to ingest" in capsys.readouterr().out
