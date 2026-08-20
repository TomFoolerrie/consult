"""M56 gate — evidence identity: the ledger stops keying bytes by basename.

The adversarial-review repros (F-01 critical, F-02, F-03, F-17), each as a
test through the PUBLIC API. docs/v2/M56-evidence-identity.md is the spec.
"""

import hashlib

import pytest
import yaml

import ledger

from test_ledger_m34 import drop, make_engagement  # noqa: E402


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestF01CreditNeverDestroysRetiredEvidence:
    def test_redrop_same_basename_new_bytes_both_streams_survive(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "interview.md", "first interview bytes\n")
        sid1 = ledger.register(root, "interview.md", {"p2p": ["match-po"]})
        assert ledger.credit(root, "p2p", filled=["match-po"]) == 1

        # the client re-sends interview.md with NEW content
        drop(root, "interview.md", "second interview, different bytes\n")
        sid2 = ledger.register(root, "interview.md",
                               {"p2p": ["receive-invoice"]})
        assert sid2 != sid1, "new bytes must mint a new id"
        assert ledger.credit(root, "p2p", filled=["receive-invoice"]) == 1

        # BOTH byte streams exist on disk and both hashes verify.
        entries = {str(e["id"]): e for e in ledger.entries(root)}
        assert set(entries) == {sid1, sid2}
        for sid, entry in entries.items():
            f = root / str(entry["file"])
            assert f.is_file(), f"{sid}: recorded file missing on disk"
            assert _hash(f) == entry["hash"], f"{sid}: hash does not verify"
        f1 = root / str(entries[sid1]["file"])
        f2 = root / str(entries[sid2]["file"])
        assert f1 != f2, "two sources must never share a destination"

    def test_retire_refuses_to_overwrite_different_bytes(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md", "real bytes\n")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        # an alien file already squats on the id-qualified destination
        pdir = root / "_sources" / "processed"
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / f"{sid}--a.md").write_text("squatter bytes\n", encoding="utf-8")
        with pytest.raises(ledger.LedgerError) as exc:
            ledger.credit(root, "p2p", filled=["match-po"])
        assert sid in str(exc.value)
        assert "overwrite" in str(exc.value)
        # the staged bytes were not destroyed either
        assert (root / "_sources" / "new" / "a.md").is_file()


class TestF02CentralizeNeverCollapsesDistinctSources:
    def _v1_area(self, root, area, body):
        a = root / "components" / area
        (a / "_sources" / "new").mkdir(parents=True, exist_ok=True)
        (a / "_sources" / "new" / "interview.md").write_text(
            body, encoding="utf-8")
        (a / "_reference").mkdir(exist_ok=True)
        slug = {"p2p": "match-po", "r2r": "accrue-ap"}[area]
        (a / "_reference" / "sources.yaml").write_text(yaml.safe_dump({
            "sources": [{
                "id": "SRC-001", "file": "_sources/new/interview.md",
                "hash": hashlib.sha256(body.encode()).hexdigest(),
                "touches": [slug], "consumed": [], "state": "new",
            }]}), encoding="utf-8")

    def test_same_basename_different_bytes_both_verify(self, tmp_path):
        root = make_engagement(tmp_path)
        self._v1_area(root, "p2p", "p2p's own interview\n")
        self._v1_area(root, "r2r", "r2r's own, different interview\n")
        remap = ledger.centralize(root)
        entries = ledger.entries(root)
        assert len(entries) == 2, "distinct bytes must stay distinct entries"
        assert len({str(e["file"]) for e in entries}) == 2
        for e in entries:
            f = root / str(e["file"])
            assert f.is_file(), f"{e['id']}: bytes never landed on disk"
            assert _hash(f) == e["hash"], f"{e['id']}: hash does not verify"
        assert remap["p2p/SRC-001"] != remap["r2r/SRC-001"]


class TestF03StatusDiffsByHashAlone:
    def test_new_bytes_under_registered_basename_are_loud(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "interview.md", "registered bytes\n")
        ledger.register(root, "interview.md", {"p2p": ["match-po"]})
        batch2 = root / "_sources" / "new" / "batch2"
        batch2.mkdir()
        (batch2 / "interview.md").write_text("brand new bytes\n",
                                             encoding="utf-8")
        st = ledger.status(root)
        assert st["unregistered"] == ["batch2/interview.md"], (
            "un-ingested evidence hidden behind a basename match")

    def test_same_bytes_under_new_name_stay_quiet(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "interview.md", "registered bytes\n")
        ledger.register(root, "interview.md", {"p2p": ["match-po"]})
        drop(root, "copy-of-interview.md", "registered bytes\n")
        assert ledger.status(root)["unregistered"] == []


class TestF17CentralizeFailsLoud:
    def test_malformed_v1_registry_refuses_and_folds_nothing(self, tmp_path):
        root = make_engagement(tmp_path)
        good = root / "components" / "p2p"
        (good / "_sources" / "new").mkdir(parents=True)
        (good / "_sources" / "new" / "ok.md").write_text("ok\n",
                                                         encoding="utf-8")
        (good / "_reference").mkdir(exist_ok=True)
        (good / "_reference" / "sources.yaml").write_text(yaml.safe_dump({
            "sources": [{"id": "SRC-001", "file": "_sources/new/ok.md",
                         "hash": hashlib.sha256(b"ok\n").hexdigest(),
                         "touches": ["match-po"], "consumed": []}],
        }), encoding="utf-8")
        bad = root / "components" / "r2r" / "_reference"
        bad.mkdir(parents=True, exist_ok=True)
        (bad / "sources.yaml").write_text("sources: [unclosed\n",
                                          encoding="utf-8")
        with pytest.raises(ledger.LedgerError) as exc:
            ledger.centralize(root)
        assert "r2r" in str(exc.value)
        assert "sources.yaml" in str(exc.value)
        # nothing partially folded
        assert ledger.entries(root) == []
        assert not (root / "_sources" / "remap.yaml").exists()

    def test_non_mapping_registry_also_refused(self, tmp_path):
        root = make_engagement(tmp_path)
        bad = root / "components" / "p2p" / "_reference"
        bad.mkdir(parents=True, exist_ok=True)
        (bad / "sources.yaml").write_text("- just\n- a\n- list\n",
                                          encoding="utf-8")
        with pytest.raises(ledger.LedgerError):
            ledger.centralize(root)

    def test_tolerant_adapter_still_reads_quietly(self, tmp_path):
        root = make_engagement(tmp_path)
        bad = root / "components" / "p2p" / "_reference"
        bad.mkdir(parents=True, exist_ok=True)
        (bad / "sources.yaml").write_text("sources: [unclosed\n",
                                          encoding="utf-8")
        assert ledger.entries_for_area(root / "components" / "p2p") == []


class TestLegacyPathMigration:
    def test_readers_accept_unqualified_legacy_paths(self, tmp_path):
        root = make_engagement(tmp_path)
        pdir = root / "_sources" / "processed"
        pdir.mkdir(parents=True)
        (pdir / "old.md").write_text("legacy bytes\n", encoding="utf-8")
        (root / "_sources" / "sources.yaml").write_text(yaml.safe_dump({
            "sources": [{
                "id": "SRC-001", "file": "_sources/processed/old.md",
                "hash": hashlib.sha256(b"legacy bytes\n").hexdigest(),
                "state": "processed",
                "touches": {"p2p": ["match-po"]},
                "consumed": {"p2p": ["match-po"]},
            }]}), encoding="utf-8")
        view = ledger.area_view(root, "p2p")
        assert view[0]["file"] == "_sources/processed/old.md"
        assert "SRC-001" in ledger.show(root)

    def test_first_credit_touch_upgrades_legacy_entry_in_place(self, tmp_path):
        root = make_engagement(tmp_path)
        pdir = root / "_sources" / "processed"
        pdir.mkdir(parents=True)
        (pdir / "old.md").write_text("legacy bytes\n", encoding="utf-8")
        (root / "_sources" / "sources.yaml").write_text(yaml.safe_dump({
            "sources": [{
                "id": "SRC-001", "file": "_sources/processed/old.md",
                "hash": hashlib.sha256(b"legacy bytes\n").hexdigest(),
                "state": "processed",
                "touches": {"p2p": ["match-po"]},
                "consumed": {"p2p": ["match-po"]},
            }]}), encoding="utf-8")
        ledger.credit(root, "p2p", filled=[])
        entry = ledger.entries(root)[0]
        assert entry["file"] == "_sources/processed/SRC-001--old.md"
        f = root / str(entry["file"])
        assert f.is_file() and _hash(f) == entry["hash"]
        assert not (pdir / "old.md").exists()
