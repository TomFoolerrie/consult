"""M34 consumer-wiring acceptance tests — written BEFORE the wiring.

Central mode = an engagement whose root carries _sources/sources.yaml (the
M34 ledger). These tests pin the wiring contract: v1 areas behave exactly
as before (the 844-test suite is the proof), and a central-mode engagement
routes every source question through the ledger.

Skips as a module until the wiring lands (gated on ledger.assess, the
guard-5 query added by this build).
"""

from pathlib import Path

import pytest
import yaml

import ledger
assert hasattr(ledger, "assess"), (
    "M34 consumer wiring missing — a failure, not a skip")

import sources as sources_mod  # noqa: E402
import brief as brief_mod      # noqa: E402
import engagement as eng_mod   # noqa: E402


# --------------------------------------------------------------------------- #
# Factory: a central-mode engagement (mirrors test_ledger_m34.make_engagement)
# --------------------------------------------------------------------------- #

def make_central(tmp_path, areas=("p2p", "r2r")):
    import json
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    # empty ledger file IS the central-mode marker
    (root / "_sources" / "sources.yaml").write_text("sources: []\n",
                                                    encoding="utf-8")
    procs = {"p2p": ["receive-invoice", "match-po"], "r2r": ["accrue-ap"]}
    for a in areas:
        area = root / "components" / a
        (area / "_review" / "processed").mkdir(parents=True)
        manifest = {
            "schema": "consult-mvp-manifest/v1",
            "area": a, "l1": a.upper(), "title": a.upper(),
            "l2_order": ["main"],
            "components": [
                {"file": f"10_{s}.md", "heading": s, "order": i + 10,
                 "role": "procedure", "slug": s, "l2": "main"}
                for i, s in enumerate(procs.get(a, ["step-one"]))
            ],
        }
        (area / "manifest.json").write_text(json.dumps(manifest),
                                            encoding="utf-8")
    return root


def drop(root, name, text="transcript body\n"):
    f = root / "_sources" / "new" / name
    f.write_text(text, encoding="utf-8")
    return f


# --------------------------------------------------------------------------- #
# 1. Central-mode detection — ONE seam
# --------------------------------------------------------------------------- #

class TestDetection:
    def test_area_under_central_engagement_resolves_to_root(self, tmp_path):
        root = make_central(tmp_path)
        area = root / "components" / "p2p"
        assert Path(sources_mod.central_root(str(area))) == root

    def test_v1_area_resolves_to_none(self, tmp_path):
        area = tmp_path / "components" / "cash"
        area.mkdir(parents=True)
        assert sources_mod.central_root(str(area)) is None

    def test_frozen_fixture_is_v1(self):
        fx = (Path(__file__).parent / "fixtures" / "p2p-complete"
              / "components" / "procure-to-pay")
        assert sources_mod.central_root(str(fx)) is None


# --------------------------------------------------------------------------- #
# 2. ledger.assess — the guard-5 question, engagement scope
#    ("has the taxonomy pass read these exact bytes?")
# --------------------------------------------------------------------------- #

class TestAssess:
    def test_unregistered_file_is_unassessed(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "a.md")
        unassessed, assessed = ledger.assess(root)
        assert unassessed == ["a.md"] and assessed == []

    def test_registered_same_bytes_is_assessed_with_entry(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "a.md", "bytes v1\n")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        unassessed, assessed = ledger.assess(root)
        assert unassessed == []
        assert [e["id"] for e in assessed] == [sid]

    def test_changed_bytes_go_back_to_unassessed(self, tmp_path):
        root = make_central(tmp_path)
        f = drop(root, "a.md", "bytes v1\n")
        ledger.register(root, "a.md", {"p2p": ["match-po"]})
        f.write_text("bytes v2 — edited after registration\n",
                     encoding="utf-8")
        unassessed, _ = ledger.assess(root)
        assert unassessed == ["a.md"]


# --------------------------------------------------------------------------- #
# 3. The v1-shaped area view — what re-pointed consumers read
# --------------------------------------------------------------------------- #

class TestAreaView:
    def test_view_flattens_maps_to_v1_entry_shape(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "t.md")
        sid = ledger.register(root, "t.md",
                              {"p2p": ["receive-invoice"],
                               "r2r": ["accrue-ap"]})
        ledger.credit(root, "p2p", filled=["receive-invoice"])
        view = ledger.area_view(root, "p2p")
        assert len(view) == 1
        e = view[0]
        assert e["id"] == sid
        assert e["touches"] == ["receive-invoice"]      # flat, area-local
        assert e["consumed"] == ["receive-invoice"]     # flat, area-local
        # an area that never touched the source sees nothing
        drop(root, "solo.md", "other\n")
        ledger.register(root, "solo.md", {"p2p": ["match-po"]})
        assert len(ledger.area_view(root, "r2r")) == 1


# --------------------------------------------------------------------------- #
# 4. sources.py re-points in central mode; v1 signatures unchanged
# --------------------------------------------------------------------------- #

class TestSourcesModule:
    def test_registered_ids_reads_the_ledger(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        area = str(root / "components" / "p2p")
        assert sources_mod.registered_ids(area) == {sid}

    def test_assess_new_sources_delegates(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "fresh.md")
        area = str(root / "components" / "p2p")
        unassessed, assessed = sources_mod.assess_new_sources(area)
        assert unassessed == ["fresh.md"] and assessed == []

    def test_mark_processed_credits_and_moves_at_root(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "a.md")
        ledger.register(root, "a.md", {"p2p": ["match-po"]})
        area = str(root / "components" / "p2p")
        rc = sources_mod.mark_processed(area, filled={"match-po"})
        assert rc == 0
        assert (root / "_sources" / "processed" / "SRC-001--a.md").is_file()

    def test_two_area_source_survives_one_areas_mark(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "t.md")
        ledger.register(root, "t.md", {"p2p": ["match-po"],
                                       "r2r": ["accrue-ap"]})
        sources_mod.mark_processed(str(root / "components" / "p2p"),
                                   filled={"match-po"})
        assert (root / "_sources" / "new" / "t.md").is_file(), \
            "r2r still owes a read — the file must not move"


# --------------------------------------------------------------------------- #
# 5. brief reads the ledger slice through the same v1 shape
# --------------------------------------------------------------------------- #

class TestBrief:
    def test_sources_entries_come_from_the_ledger(self, tmp_path):
        root = make_central(tmp_path)
        drop(root, "t.md")
        sid = ledger.register(root, "t.md", {"p2p": ["receive-invoice"]})
        entries = brief_mod._sources_entries(str(root / "components" / "p2p"))
        assert [e["id"] for e in entries] == [sid]
        assert entries[0]["touches"] == ["receive-invoice"]


# --------------------------------------------------------------------------- #
# 6. Intake verbs: route registers + tags, copies nothing; park delegates
# --------------------------------------------------------------------------- #

class TestIntakeVerbs:
    def test_route_registers_without_copying(self, tmp_path):
        root = make_central(tmp_path)
        f = drop(root, "walkthrough.md")
        eng_mod.route(f, ["p2p", "r2r"],
                      {"p2p": "AP walkthrough", "r2r": "accruals context"})
        entries = ledger.entries(root)
        assert len(entries) == 1
        e = entries[0]
        assert set(e["touches"]) == {"p2p", "r2r"}
        # tagging, not copying: file stays put, no per-area copies, no sidecar
        assert f.is_file()
        assert not list((root / "components").rglob("intake-*"))
        assert not list(root.rglob("*.route.md"))
        # pointer content reaches the ledger entry
        assert "walkthrough" in yaml.safe_dump(e) or e.get("note")

    def test_routed_file_is_no_longer_unregistered(self, tmp_path):
        root = make_central(tmp_path)
        f = drop(root, "doc.md")
        eng_mod.route(f, ["p2p"], {"p2p": "pointer"})
        assert ledger.status(root)["unregistered"] == []

    def test_park_delegates_to_ledger(self, tmp_path):
        root = make_central(tmp_path)
        f = drop(root, "brochure.md")
        eng_mod.park(f, "marketing, not evidence")
        st = ledger.status(root)
        assert st["parked"] == [("brochure.md", "marketing, not evidence")]
