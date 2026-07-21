"""Tests for scripts/sources.py — mark-processed and archive-review moves."""
import os

import yaml

import sources


def make_area(tmp_path, entries):
    area = tmp_path / "area"
    (area / "_reference").mkdir(parents=True)
    (area / "_sources" / "new").mkdir(parents=True)
    (area / "_reference" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": entries}), encoding="utf-8")
    for e in entries:
        if e.get("file"):
            f = area / e["file"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("content of %s" % e.get("id"), encoding="utf-8")
    return area


def read_sources(area):
    return yaml.safe_load(
        (area / "_reference" / "sources.yaml").read_text(encoding="utf-8"))["sources"]


def test_fully_consumed_source_moves(tmp_path):
    """A source whose whole touches set is filled moves to processed/ and flips state."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/new/a.md", "touches": ["p1", "p2"],
         "state": "new"}])
    assert sources.mark_processed(str(area), {"p1", "p2", "p3"}) == 0
    assert (area / "_sources" / "processed" / "a.md").is_file()
    assert not (area / "_sources" / "new" / "a.md").exists()
    entry = read_sources(area)[0]
    assert entry["state"] == "processed"
    assert entry["file"] == os.path.join("_sources", "processed", "a.md")


def test_partially_consumed_source_stays(tmp_path):
    """A source touching an unfilled slug stays in new/ with state unchanged."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/new/a.md", "touches": ["p1", "p2"],
         "state": "new"}])
    sources.mark_processed(str(area), {"p1"})
    assert (area / "_sources" / "new" / "a.md").is_file()
    assert read_sources(area)[0]["state"] == "new"


def test_empty_touches_never_moves(tmp_path):
    """A source with no touches never auto-moves — stays for a human."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/new/a.md", "touches": [], "state": "new"}])
    sources.mark_processed(str(area), {"p1"})
    assert (area / "_sources" / "new" / "a.md").is_file()
    assert read_sources(area)[0]["state"] == "new"


def test_already_processed_skipped(tmp_path):
    """Entries already state=processed are left entirely alone."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/new/a.md", "touches": ["p1"],
         "state": "processed"}])
    sources.mark_processed(str(area), {"p1"})
    assert (area / "_sources" / "new" / "a.md").is_file()


def test_stale_recorded_file_falls_back_to_basename(tmp_path):
    """A stale recorded path falls back to _sources/new/<basename>."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/gone/a.md", "touches": ["p1"],
         "state": "new"}])
    (area / "_sources" / "gone" / "a.md").unlink()  # make recorded path stale
    (area / "_sources" / "new" / "a.md").write_text("x", encoding="utf-8")
    sources.mark_processed(str(area), {"p1"})
    assert (area / "_sources" / "processed" / "a.md").is_file()
    assert read_sources(area)[0]["state"] == "processed"


def test_missing_file_still_flips_state(tmp_path):
    """A fully-consumed entry whose file is missing still flips to processed."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/new/a.md", "touches": ["p1"],
         "state": "new"}])
    (area / "_sources" / "new" / "a.md").unlink()
    sources.mark_processed(str(area), {"p1"})
    assert read_sources(area)[0]["state"] == "processed"


def test_archive_review_selected_slugs(tmp_path):
    """archive-review with slugs moves only those notes to _review/processed/."""
    area = tmp_path / "area"
    (area / "_review").mkdir(parents=True)
    for s in ("p1", "p2"):
        (area / "_review" / f"{s}.notes.yaml").write_text("items: []\n",
                                                          encoding="utf-8")
    assert sources.archive_review(str(area), ["p1"], None) == 0
    assert (area / "_review" / "processed" / "p1.notes.yaml").is_file()
    assert (area / "_review" / "p2.notes.yaml").is_file()


def test_archive_review_all_and_docx(tmp_path):
    """With no slugs, every *.notes.yaml is archived; a --docx moves too."""
    area = tmp_path / "area"
    (area / "_review").mkdir(parents=True)
    for s in ("p1", "p2"):
        (area / "_review" / f"{s}.notes.yaml").write_text("items: []\n",
                                                          encoding="utf-8")
    docx = tmp_path / "reviewed.docx"
    docx.write_bytes(b"PK")
    assert sources.archive_review(str(area), None, str(docx)) == 0
    proc = area / "_review" / "processed"
    assert (proc / "p1.notes.yaml").is_file()
    assert (proc / "p2.notes.yaml").is_file()
    assert (proc / "reviewed.docx").is_file()
    assert not docx.exists()


def test_archive_review_missing_slug_ignored(tmp_path):
    """A named slug with no notes file is skipped without error."""
    area = tmp_path / "area"
    (area / "_review").mkdir(parents=True)
    assert sources.archive_review(str(area), ["ghost"], None) == 0
    assert not (area / "_review" / "processed" / "ghost.notes.yaml").exists()


def test_cli_mark_processed(tmp_path):
    """main() wires the mark-processed subcommand and exits 0."""
    area = make_area(tmp_path, [
        {"id": "s1", "file": "_sources/new/a.md", "touches": ["p1"],
         "state": "new"}])
    rc = sources.main(["mark-processed", str(area), "--filled", "p1"])
    assert rc == 0
    assert (area / "_sources" / "processed" / "a.md").is_file()


def test_resolve_area_passthrough(tmp_path):
    """resolve_area returns an existing dir path (trailing slash stripped)."""
    d = tmp_path / "x"
    d.mkdir()
    assert sources.resolve_area(str(d) + "/") == str(d)
    assert sources.resolve_area("no-such-dir-xyz") == "no-such-dir-xyz"
