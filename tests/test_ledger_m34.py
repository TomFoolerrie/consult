"""M34 acceptance tests — written BEFORE the ledger, as the build target.

These tests define the centralized-sources API
(docs/v2/M34-centralized-sources.md). Until `scripts/ledger.py` exists,
every test SKIPS (importorskip); the moment the module lands they become
the acceptance gate. Implementers: make these pass without editing them.

The frozen corpus under tests/fixtures/p2p-complete/ is read-only (adapter
tests). All mutating tests build synthetic engagements under tmp_path.
"""

from pathlib import Path

import pytest
import yaml

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
FIXTURE_AREA = FIXTURE_ROOT / "components" / "procure-to-pay"

ledger = pytest.importorskip(
    "ledger", reason="M34 ledger not built yet — these are the build target"
)


# --------------------------------------------------------------------------- #
# Synthetic engagement factory
# --------------------------------------------------------------------------- #

def make_engagement(tmp_path, areas=("p2p", "r2r")):
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    for a in areas:
        area = root / "components" / a
        (area / "_review" / "processed").mkdir(parents=True)
        # minimal manifest so touches-validation has an authority
        import json
        procs = {"p2p": ["receive-invoice", "match-po"],
                 "r2r": ["accrue-ap"]}.get(a, ["step-one"])
        manifest = {
            "schema": "consult-mvp-manifest/v1",
            "area": a, "l1": a.upper(), "title": a.upper(),
            "l2_order": ["main"],
            "components": [
                {"file": f"10_{s}.md", "heading": s, "order": i + 10,
                 "role": "procedure", "slug": s, "l2": "main"}
                for i, s in enumerate(procs)
            ],
        }
        (area / "manifest.json").write_text(json.dumps(manifest),
                                            encoding="utf-8")
    return root


def drop(root, name, text="interview transcript body\n"):
    f = root / "_sources" / "new" / name
    f.write_text(text, encoding="utf-8")
    return f


def write_source_note(root, area, slug, src_id):
    """A consumed (archived) note whose kind: source item names src_id —
    the v1 evidence shape (sources.note_src_ids)."""
    p = (root / "components" / area / "_review" / "processed"
         / f"{slug}.notes.yaml")
    p.write_text(yaml.safe_dump({
        "procedure": slug,
        "items": [{"kind": "source", "src": src_id,
                   "note": "read for update"}],
    }), encoding="utf-8")


# --------------------------------------------------------------------------- #
# 1. Register → tag → consume per area → auto-move
# --------------------------------------------------------------------------- #

class TestLedgerRoundTrip:
    def test_two_area_source_moves_only_when_both_consumed(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "t.md")
        sid = ledger.register(root, "t.md",
                              {"p2p": ["receive-invoice"],
                               "r2r": ["accrue-ap"]})
        assert (root / "_sources" / "new" / "t.md").is_file()

        moved = ledger.credit(root, "p2p", filled=["receive-invoice"])
        assert moved == 0, "one of two areas consumed — file must stay"
        assert (root / "_sources" / "new" / "t.md").is_file()
        assert ledger.outstanding(root, "p2p") == {}
        assert sid in ledger.outstanding(root, "r2r")

        moved = ledger.credit(root, "r2r", filled=["accrue-ap"])
        assert moved == 1
        assert not (root / "_sources" / "new" / "t.md").exists()
        assert (root / "_sources" / "processed" / "SRC-001--t.md").is_file()

    def test_one_area_source_behaves_like_v1(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "solo.md")
        ledger.register(root, "solo.md", {"p2p": ["match-po"]})
        assert ledger.credit(root, "p2p", filled=["match-po"]) == 1
        assert (root / "_sources" / "processed" / "SRC-001--solo.md").is_file()

    def test_partial_touches_within_area_hold_the_file(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "wide.md")
        sid = ledger.register(root, "wide.md",
                              {"p2p": ["receive-invoice", "match-po"]})
        ledger.credit(root, "p2p", filled=["receive-invoice"])
        assert (root / "_sources" / "new" / "wide.md").is_file()
        assert ledger.outstanding(root, "p2p") == {sid: ["match-po"]}


# --------------------------------------------------------------------------- #
# 2. Minting, idempotence, park, loud-until-empty
# --------------------------------------------------------------------------- #

class TestRegistration:
    def test_ids_are_engagement_global_and_ordered(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md", "one\n")
        drop(root, "b.md", "two\n")
        assert ledger.register(root, "a.md", {"p2p": ["match-po"]}) == "SRC-001"
        assert ledger.register(root, "b.md", {"r2r": ["accrue-ap"]}) == "SRC-002"

    def test_redrop_same_bytes_is_idempotent(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md", "same bytes\n")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        # re-register: same file, new tag — merges touches, same id, no dupe
        sid2 = ledger.register(root, "a.md", {"r2r": ["accrue-ap"]})
        assert sid2 == sid
        assert len(ledger.entries(root)) == 1
        assert sid in ledger.outstanding(root, "r2r")

    def test_unknown_touches_slug_refused_loudly(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md")
        with pytest.raises(ledger.LedgerError) as exc:
            ledger.register(root, "a.md", {"p2p": ["not-a-real-slug"]})
        assert "not-a-real-slug" in str(exc.value)

    def test_park_with_reason_and_status(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "junk.md")
        drop(root, "pending.md")
        ledger.park(root, "junk.md", "marketing brochure, not evidence")
        st = ledger.status(root)
        assert st["unregistered"] == ["pending.md"]
        assert st["parked"] == [("junk.md", "marketing brochure, not evidence")]
        assert (root / "_sources" / "parked" / "junk.md").is_file()

    def test_status_quiet_when_empty(self, tmp_path):
        root = make_engagement(tmp_path)
        st = ledger.status(root)
        assert st["unregistered"] == [] and st["parked"] == []


# --------------------------------------------------------------------------- #
# 3. Consumption evidence rules (v1 semantics, one scope up)
# --------------------------------------------------------------------------- #

class TestCreditEvidence:
    def test_filled_credits_unconditionally(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        assert ledger.credit(root, "p2p", filled=["match-po"]) == 1
        assert sid not in ledger.outstanding(root, "p2p")

    def test_updated_requires_source_note_evidence(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        # no note evidence -> no credit
        assert ledger.credit(root, "p2p", updated=["match-po"]) == 0
        assert sid in ledger.outstanding(root, "p2p")
        # archived kind: source note naming the id -> credit
        write_source_note(root, "p2p", "match-po", sid)
        assert ledger.credit(root, "p2p", updated=["match-po"]) == 1
        assert sid not in ledger.outstanding(root, "p2p")

    def test_non_source_notes_credit_nothing(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["match-po"]})
        p = (root / "components" / "p2p" / "_review" / "processed"
             / "match-po.notes.yaml")
        p.write_text(yaml.safe_dump({
            "procedure": "match-po",
            "items": [{"kind": "review", "type": "comment",
                       "note": f"reviewer mentions {sid} in prose"}],
        }), encoding="utf-8")
        assert ledger.credit(root, "p2p", updated=["match-po"]) == 0
        assert sid in ledger.outstanding(root, "p2p")

    def test_consumption_never_resets(self, tmp_path):
        root = make_engagement(tmp_path)
        drop(root, "a.md")
        sid = ledger.register(root, "a.md",
                              {"p2p": ["receive-invoice", "match-po"]})
        ledger.credit(root, "p2p", filled=["receive-invoice"])
        # a later unrelated credit pass must not lose the earlier credit
        ledger.credit(root, "p2p", updated=[])
        assert ledger.outstanding(root, "p2p") == {sid: ["match-po"]}


# --------------------------------------------------------------------------- #
# 4. The dual-layout adapter — v1 areas read through the unified API
# --------------------------------------------------------------------------- #

class TestAdapter:
    def test_fixture_area_entries_with_prefixed_ids(self):
        entries = ledger.entries_for_area(FIXTURE_AREA)
        ids = {e["id"] for e in entries}
        assert len(entries) == 6
        assert ids == {f"procure-to-pay/SRC-{n:03d}" for n in range(1, 7)}

    def test_fixture_area_is_fully_consumed(self):
        assert ledger.outstanding_for_area(FIXTURE_AREA) == {}

    def test_adapter_never_writes(self):
        import time
        before = {p: p.stat().st_mtime_ns
                  for p in FIXTURE_AREA.rglob("*") if p.is_file()}
        ledger.entries_for_area(FIXTURE_AREA)
        ledger.outstanding_for_area(FIXTURE_AREA)
        after = {p: p.stat().st_mtime_ns
                 for p in FIXTURE_AREA.rglob("*") if p.is_file()}
        assert before == after


# --------------------------------------------------------------------------- #
# 5. centralize — fold a v1 engagement into one ledger (golden)
# --------------------------------------------------------------------------- #

def make_v1_engagement(tmp_path):
    """Two v1 areas; one transcript double-routed (same bytes, two ids)."""
    root = make_engagement(tmp_path)  # gives manifests + root _sources
    body = "shared transcript bytes\n"
    import hashlib
    h = hashlib.sha256(body.encode()).hexdigest()
    for area, sid, slugs, consumed in (
            ("p2p", "SRC-001", ["receive-invoice"], ["receive-invoice"]),
            ("r2r", "SRC-001", ["accrue-ap"], [])):
        a = root / "components" / area
        (a / "_sources" / "processed").mkdir(parents=True)
        (a / "_sources" / "new").mkdir(parents=True)
        sub = "processed" if consumed else "new"
        (a / "_sources" / sub / "shared.md").write_text(body, encoding="utf-8")
        (a / "_reference").mkdir(exist_ok=True)
        (a / "_reference" / "sources.yaml").write_text(yaml.safe_dump({
            "sources": [{"id": sid, "file": f"_sources/{sub}/shared.md",
                         "touches": slugs, "hash": h,
                         "state": sub, "consumed": consumed}],
        }), encoding="utf-8")
    return root


class TestCentralize:
    def test_double_routed_file_dedupes_with_merged_maps(self, tmp_path):
        root = make_v1_engagement(tmp_path)
        remap = ledger.centralize(root)
        entries = ledger.entries(root)
        assert len(entries) == 1, "hash dedupe must collapse the copies"
        e = entries[0]
        assert e["touches"] == {"p2p": ["receive-invoice"],
                                "r2r": ["accrue-ap"]}
        assert e["consumed"].get("p2p") == ["receive-invoice"]
        assert not e["consumed"].get("r2r")
        # remap covers both old area-local ids
        assert remap["p2p/SRC-001"] == e["id"]
        assert remap["r2r/SRC-001"] == e["id"]

    def test_centralized_file_position_reflects_derived_state(self, tmp_path):
        root = make_v1_engagement(tmp_path)
        ledger.centralize(root)
        # r2r never consumed it -> someone still owes a read -> new/
        assert (root / "_sources" / "new" / "SRC-001--shared.md").is_file()
        assert ledger.credit(root, "r2r", filled=["accrue-ap"]) == 1
        assert (root / "_sources" / "processed" / "SRC-001--shared.md").is_file()
