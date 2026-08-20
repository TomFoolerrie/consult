"""M57 gate — one address per callout: grounding stops crossing id namespaces.

The adversarial-review repros (F-06, F-12, F-11) on the standing fixtures.
docs/v2/M57-callout-addressing.md is the spec.
"""

import shutil
from pathlib import Path

import pytest

analysis = pytest.importorskip("analysis")
findings = pytest.importorskip("findings")
plan_views = pytest.importorskip("plan_views")

FIXTURES = Path(__file__).resolve().parent / "fixtures"
P2P_ROOT = FIXTURES / "p2p-complete"
P2P_AREA = P2P_ROOT / "components" / "procure-to-pay"
IPO_ROOT = FIXTURES / "ipo-engagement"


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


class TestF06AnalystLoopIsFollowable:
    def test_every_conflict_record_id_resolves_and_binds_its_procedure(self):
        recs = analysis.conflict_records(P2P_AREA)
        assert recs, "the p2p fixture carries conflict records"
        for rec in recs:
            resolved = findings.resolve_grounds(P2P_ROOT, [rec["id"]])
            assert resolved == [rec["id"]], (
                f"{rec['id']}: the id the brief shows must resolve as given")
            slug, _, _local = rec["id"].partition(":")
            assert slug == rec["step"], (
                f"{rec['id']}: must bind the callout in the procedure the "
                f"record came from, not a stranger procedure")

    def test_display_id_rides_alongside_for_the_human(self):
        for rec in analysis.conflict_records(P2P_AREA):
            assert rec.get("display_id"), rec["id"]

    def test_ambiguous_unqualified_ground_refused_with_candidates(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        # plant the same LOCAL id in a second procedure
        frag = area / "10_match-po.md"
        text = frag.read_text(encoding="utf-8")
        planted = (
            "\n> **VALIDATION REQUIRED — GAP-05:** A second GAP-05, "
            "colliding with the taxonomy node's.\n"
            "> - **Grounds:** SRC-002.\n")
        frag.write_text(text + planted, encoding="utf-8")
        with pytest.raises(findings.FindingsError) as exc:
            findings.resolve_grounds(root, ["GAP-05"])
        msg = str(exc.value)
        assert "ambiguous" in msg
        assert "match-po:GAP-05" in msg
        assert "invoice-handling:GAP-05" in msg

    def test_unambiguous_unqualified_ground_normalises(self, tmp_path):
        root, _area = ipo_copy(tmp_path)
        assert findings.resolve_grounds(root, ["GAP-02"]) == ["match-po:GAP-02"]


class TestF12ForAreaJoinsQualified:
    def _second_area(self, root):
        """A second area whose corpus also carries a GAP-01."""
        src = root / "components" / "purchasing"
        dst = root / "components" / "treasury"
        shutil.copytree(src, dst)
        return dst

    def test_finding_grounded_in_area_a_only_appears_in_a(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        dst = self._second_area(root)
        # retitle treasury's fragment slugs so its corpus is distinct but its
        # LOCAL callout ids still collide with purchasing's
        import json
        man = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))
        for comp in man["components"]:
            if comp.get("slug") == "receive-invoice":
                (dst / comp["file"]).rename(dst / "10_receive-wire.md")
                comp["slug"] = "receive-wire"
                comp["file"] = "10_receive-wire.md"
        (dst / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
        shutil.rmtree(dst / "_taxonomy")

        fid = findings.propose(root, "About purchasing's receive-invoice gap.",
                               ["receive-invoice:GAP-01"], "controls")
        assert fid in {e["id"] for e in findings.for_area(root, "purchasing")}
        assert fid not in {e["id"] for e in findings.for_area(root, "treasury")}

    def test_legacy_unqualified_stored_ground_still_attributes(self, tmp_path):
        import yaml
        root, _area = ipo_copy(tmp_path)
        fid = findings.propose(root, "Legacy.", ["GAP-02"], "controls")
        # rewrite the stored ground back to the legacy unqualified form
        reg = root / "_registers" / "findings.yaml"
        data = yaml.safe_load(reg.read_text(encoding="utf-8"))
        for e in data["findings"]:
            if e["id"] == fid:
                e["grounds"] = ["GAP-02"]
        reg.write_text(yaml.safe_dump(data), encoding="utf-8")
        assert fid in {e["id"] for e in findings.for_area(root, "purchasing")}


class TestF11NodeStepsKeyedBySlug:
    def test_duplicate_titles_both_keep_their_steps(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        before = plan_views.node_steps(area)
        assert "invoice-handling" in before and "schedule-payment" in before
        untouched = {k: v for k, v in before.items()
                     if k not in ("invoice-handling", "schedule-payment")}

        # retitle two nodes to the SAME H2 title (the review's repro)
        for slug in ("invoice-handling", "schedule-payment"):
            node = area / "_taxonomy" / f"{slug}.md"
            text = node.read_text(encoding="utf-8")
            first, rest = text.split("\n", 1)
            node.write_text("## Exceptions\n" + rest, encoding="utf-8")

        after = plan_views.node_steps(area)
        assert set(before) == set(after), (
            "a shared title must not make a node vanish from the relation")
        for slug in ("invoice-handling", "schedule-payment"):
            assert after[slug] == before[slug], (
                f"{slug}: steps reassigned by a title collision")
        for slug, steps in untouched.items():
            assert after[slug] == steps

    def test_coverage_unchanged_for_untouched_node(self, tmp_path):
        import coverage_map
        root, area = ipo_copy(tmp_path)
        before = coverage_map.coverage(root, plan_views.node_steps(area))
        for slug in ("invoice-handling", "schedule-payment"):
            node = area / "_taxonomy" / f"{slug}.md"
            _first, rest = node.read_text(encoding="utf-8").split("\n", 1)
            node.write_text("## Exceptions\n" + rest, encoding="utf-8")
        after = coverage_map.coverage(root, plan_views.node_steps(area))
        untouched = set(before) - {"invoice-handling", "schedule-payment"}
        for slug in untouched:
            assert after.get(slug) == before[slug]
        assert set(after) == set(before)
