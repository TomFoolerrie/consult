"""Tests for M25 — engagement intake: the route/park deterministic verbs
(file copies ONLY — the M6 'hash = assessed' contract means route never
touches sources.yaml), the pointer sidecar's path to the drafter, the
sidecar's exclusion from source assessment, and the audit's INTAKE lines."""
import json
from pathlib import Path

import yaml

import engagement
import scaffold
import sources


def make_engagement(tmp_path: Path) -> Path:
    """Engagement root with components/{cash,p2p} and an intake/ folder."""
    root = tmp_path / "components"
    for area in ("cash", "p2p"):
        d = root / area
        d.mkdir(parents=True)
        comps = [{"file": "10_x.md", "role": "procedure", "slug": "x",
                  "heading": f"{area} proc", "order": 10}]
        (d / "manifest.json").write_text(json.dumps(
            {"area": area, "title": area.upper(), "components": comps}),
            encoding="utf-8")
        (d / "10_x.md").write_text(f"## {area} proc\n\nText.\n",
                                   encoding="utf-8")
    (tmp_path / "intake").mkdir()
    return tmp_path


def stage(engroot: Path, name="walkthrough.md",
          text="Receiving dock AND valuation discussion.\n") -> Path:
    p = engroot / "intake" / name
    p.write_text(text, encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# route — file copies only
# --------------------------------------------------------------------------- #

def test_route_copies_byte_identical_and_writes_nothing_else(tmp_path,
                                                             capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    original = f.read_bytes()
    rc = engagement.main(["route", str(f), "--to", "cash,p2p",
                          "--note-for", "cash", "pp. 4-9 cover the dock"])
    assert rc == 0
    for area in ("cash", "p2p"):
        copy = engroot / "components" / area / "_sources" / "new" \
            / "intake-walkthrough.md"
        assert copy.read_bytes() == original          # the no-reduction rule
        # THE M6 CONTRACT: no ledger entry, no hash stamp — assessment must
        # still happen, so sources.yaml does not even exist yet.
        assert not (engroot / "components" / area / "_reference"
                    / "sources.yaml").exists()
    side = engroot / "components" / "cash" / "_sources" / "new" \
        / "intake-walkthrough.md.route.md"
    assert "pp. 4-9" in side.read_text(encoding="utf-8")
    assert not (engroot / "components" / "p2p" / "_sources" / "new"
                / "intake-walkthrough.md.route.md").exists()
    # original moved to routed/ with a manifest line
    assert not f.exists()
    assert (engroot / "intake" / "routed" / "walkthrough.md").is_file()
    log = (engroot / "intake" / "routed" / "manifest.log") \
        .read_text(encoding="utf-8")
    assert "walkthrough.md -> cash, p2p" in log


def test_route_is_idempotent_at_same_content(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    assert engagement.main(["route", str(f), "--to", "cash"]) == 0
    capsys.readouterr()
    f2 = stage(engroot)  # same name, same bytes, re-dropped
    assert engagement.main(["route", str(f2), "--to", "cash"]) == 0
    assert "no-op" in capsys.readouterr().out


def test_route_refuses_different_content_at_same_name(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    assert engagement.main(["route", str(f), "--to", "cash"]) == 0
    f2 = stage(engroot, text="ENTIRELY different bytes.\n")
    assert engagement.main(["route", str(f2), "--to", "cash"]) == 2
    assert "never overwritten" in capsys.readouterr().err


def test_route_noop_when_content_already_in_ledger(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    import hashlib
    digest = hashlib.sha256(f.read_bytes()).hexdigest()
    ref = engroot / "components" / "cash" / "_reference"
    ref.mkdir()
    (ref / "sources.yaml").write_text(yaml.safe_dump(
        {"sources": [{"id": "SRC-001", "file": "_sources/processed/old.md",
                      "hash": digest, "state": "processed"}]}),
        encoding="utf-8")
    assert engagement.main(["route", str(f), "--to", "cash"]) == 0
    assert "already in the source ledger" in capsys.readouterr().out
    assert not (engroot / "components" / "cash" / "_sources" / "new"
                / "intake-walkthrough.md").exists()


def test_route_unknown_area_needs_human_new_area_flag(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    assert engagement.main(["route", str(f), "--to", "treasury"]) == 2
    err = capsys.readouterr().err
    assert "cash" in err and "--new-area" in err and "parks" in err
    # the human's one-line override formalizes today's hand-drop
    assert engagement.main(["route", str(f), "--to", "treasury",
                            "--new-area"]) == 0
    assert (engroot / "components" / "treasury" / "_sources" / "new"
            / "intake-walkthrough.md").is_file()


def test_route_rejects_non_top_level_files(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    assert engagement.main(["route", str(f), "--to", "cash"]) == 0
    routed = engroot / "intake" / "routed" / "walkthrough.md"
    assert engagement.main(["route", str(routed), "--to", "p2p"]) == 2
    assert "top-level" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# park — always loud
# --------------------------------------------------------------------------- #

def test_park_requires_reason_and_records_it(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot, name="treasury-notes.md")
    assert engagement.main(["park", str(f)]) == 2
    assert "reason" in capsys.readouterr().err
    assert engagement.main(["park", str(f), "--reason",
                            "mentions treasury; no scoped area"]) == 0
    assert (engroot / "intake" / "parked" / "treasury-notes.md").is_file()
    log = (engroot / "intake" / "parked" / "reasons.log") \
        .read_text(encoding="utf-8")
    assert "treasury-notes.md — mentions treasury" in log


# --------------------------------------------------------------------------- #
# audit — INTAKE is loud until empty
# --------------------------------------------------------------------------- #

def test_audit_reports_unprocessed_and_parked_with_reasons(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    stage(engroot, name="fresh.md")
    parked = stage(engroot, name="odd.md")
    engagement.main(["park", str(parked), "--reason", "no scoped area"])
    capsys.readouterr()
    assert engagement.main(["audit", str(engroot / "components")]) == 0
    out = capsys.readouterr().out
    assert "INTAKE — 1 unprocessed, 1 parked" in out
    assert "unprocessed: fresh.md" in out
    assert "parked: odd.md — no scoped area" in out


def test_audit_silent_when_intake_empty(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    assert engagement.main(["audit", str(engroot / "components")]) == 0
    assert "INTAKE" not in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# the sidecar: never a source, retires with its source, reaches the drafter
# --------------------------------------------------------------------------- #

def test_sidecar_excluded_from_source_assessment(tmp_path):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    engagement.main(["route", str(f), "--to", "cash",
                     "--note-for", "cash", "dock pages only"])
    area = str(engroot / "components" / "cash")
    files = sources.new_source_files(area)
    assert files == ["_sources/new/intake-walkthrough.md"]  # no sidecar


def test_mark_processed_moves_sidecar_with_its_source(tmp_path, capsys):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    engagement.main(["route", str(f), "--to", "cash",
                     "--note-for", "cash", "dock pages only"])
    area = engroot / "components" / "cash"
    ref = area / "_reference"
    ref.mkdir()
    import hashlib
    src_rel = "_sources/new/intake-walkthrough.md"
    digest = hashlib.sha256((area / src_rel).read_bytes()).hexdigest()
    (ref / "sources.yaml").write_text(yaml.safe_dump(
        {"sources": [{"id": "SRC-001", "file": src_rel, "hash": digest,
                      "state": "new", "touches": ["x"]}]}), encoding="utf-8")
    assert sources.mark_processed(str(area), filled={"x"}) == 0
    proc = area / "_sources" / "processed"
    assert (proc / "intake-walkthrough.md").is_file()
    assert (proc / "intake-walkthrough.md.route.md").is_file()
    assert not list((area / "_sources" / "new").iterdir())  # nothing lingers


def test_stamp_sources_folds_pointer_into_note_idempotently(tmp_path):
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    engagement.main(["route", str(f), "--to", "cash",
                     "--note-for", "cash", "pp. 4-9 cover the dock"])
    area = engroot / "components" / "cash"
    ref = area / "_reference"
    ref.mkdir()
    (ref / "sources.yaml").write_text(yaml.safe_dump(
        {"sources": [{"id": "SRC-001",
                      "file": "_sources/new/intake-walkthrough.md",
                      "touches": ["x"]}]}), encoding="utf-8")
    scaffold.stamp_sources(area)
    scaffold.stamp_sources(area)  # idempotent
    data = yaml.safe_load((ref / "sources.yaml").read_text(encoding="utf-8"))
    note = data["sources"][0]["note"]
    assert note.count("intake pointer: pp. 4-9 cover the dock") == 1
    assert data["sources"][0]["hash"]  # ordinary stamping still happened


def test_brief_carries_the_pointer_note_to_the_drafter(tmp_path, capsys):
    import brief
    engroot = make_engagement(tmp_path)
    f = stage(engroot)
    engagement.main(["route", str(f), "--to", "cash",
                     "--note-for", "cash", "pp. 4-9 cover the dock"])
    area = engroot / "components" / "cash"
    ref = area / "_reference"
    ref.mkdir()
    (ref / "sources.yaml").write_text(yaml.safe_dump(
        {"sources": [{"id": "SRC-001",
                      "file": "_sources/new/intake-walkthrough.md",
                      "touches": ["x"]}]}), encoding="utf-8")
    scaffold.stamp_sources(area)
    capsys.readouterr()
    assert brief.main([str(area), "--slug", "x"]) == 0
    out = capsys.readouterr().out
    assert "intake pointer: pp. 4-9 cover the dock" in out
