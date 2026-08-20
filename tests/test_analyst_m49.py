"""M49 acceptance tests — written BEFORE the build.

Pins: the analyst brief CLI (`analysis.py brief <area>` — license, the
four candidate feeds, the register state, the objective block, the
refusals), the fourth generator (`conflict_records` — two-citation v2
conflicts and v1 `Nature: conflict`, absences excluded), the per-area
findings filter (`findings.for_area`), and the dispatch surface prose.

Four skip gates, one per part — the packages land independently with
the suite green at each commit.
"""

import shutil
from pathlib import Path

import pytest

import gatecheck

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
P2P_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
            / "components" / "procure-to-pay")

SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"
ANALYST = REPO / "agents" / "consult-analyst.md"


def _has(module, attr):
    try:
        mod = __import__(module)
    except ImportError:
        return False
    return hasattr(mod, attr)


needs_brief = gatecheck.landed(
    not _has("analysis", "main"),
    reason="M49 analysis.py brief CLI not built yet — the target")

needs_extractor = gatecheck.landed(
    not _has("analysis", "conflict_records"),
    reason="M49 conflict_records not built yet — the target")

needs_filter = gatecheck.landed(
    not _has("findings", "for_area"),
    reason="M49 findings.for_area not built yet — the target")

needs_dispatch = gatecheck.landed(
    "analysis.py brief" not in SKILL.read_text(encoding="utf-8"),
    reason="M49 dispatch passage not landed yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in base.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# 1. The brief (Part A)
# --------------------------------------------------------------------------- #

@needs_brief
class TestBrief:
    def _brief(self, area, capsys):
        import analysis
        rc = analysis.main(["brief", str(area)])
        return rc, capsys.readouterr().out

    def test_prints_license_feeds_register_objective(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        rc, out = self._brief(area, capsys)
        assert rc == 0
        low = out.lower()
        assert "propose" in low and "never" in low        # the license
        assert "conflict-record" in low or "conflict record" in low
        assert "pain" in low                              # the feeds named
        assert "finding" in low                           # register state
        assert "objective" in low                         # the M41 block

    def test_read_only(self, tmp_path, capsys):
        import analysis
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root)
        analysis.main(["brief", str(area)])
        capsys.readouterr()
        assert fingerprint(root) == before

    def test_unknown_area_exits_2(self, tmp_path, capsys):
        import analysis
        rc = analysis.main(["brief", str(tmp_path / "nope")])
        capsys.readouterr()
        assert rc == 2

    def test_area_outside_engagement_refuses(self, tmp_path, capsys):
        import analysis
        root, area = ipo_copy(tmp_path)
        parked = tmp_path / "parked"
        shutil.copytree(area, parked)
        rc = analysis.main(["brief", str(parked)])
        capsys.readouterr()
        assert rc != 0


# --------------------------------------------------------------------------- #
# 2. The fourth generator (Part B)
# --------------------------------------------------------------------------- #

@needs_extractor
class TestConflictRecords:
    def test_two_citation_conflicts_are_records(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        recs = analysis.conflict_records(area)
        ids = {r["id"] for r in recs}
        # M57: record ids are procedure-qualified callout addresses
        assert "receive-invoice:GAP-01" in ids and "match-po:GAP-02" in ids
        for r in recs:
            assert r["kind"] == "conflict-record"
            assert len(set(r["srcs"])) >= 2 or r.get("nature") == "conflict"
            assert r["step"] and r["text"]

    def test_single_source_absence_is_not_a_record(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        frag = area / "10_receive-invoice.md"
        text = frag.read_text(encoding="utf-8")
        absence = (
            "\n> **VALIDATION REQUIRED — GAP-90:** The archive retention "
            "period is not stated.\n"
            "> - **Grounds:** SRC-002 read in full; no figure given.\n")
        frag.write_text(text.replace("### Issues", "### Issues\n" + absence,
                                     1), encoding="utf-8")
        recs = analysis.conflict_records(area)
        assert "receive-invoice:GAP-90" not in {r["id"] for r in recs}

    def test_v1_nature_conflict_grammar_counts(self):
        import analysis
        recs = analysis.conflict_records(P2P_AREA)
        assert recs                       # the fixture carries Nature: conflict
        assert all(r["kind"] == "conflict-record" for r in recs)

    def test_deterministic_and_read_only(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root)
        a = analysis.conflict_records(area)
        b = analysis.conflict_records(area)
        assert a == b
        assert fingerprint(root) == before


# --------------------------------------------------------------------------- #
# 3. The per-area filter (Part C)
# --------------------------------------------------------------------------- #

@needs_filter
class TestForArea:
    def test_partitions_by_grounds_home(self, tmp_path):
        import findings
        root, area = ipo_copy(tmp_path)
        fid = findings.propose(
            root, "The match tolerance is contested across sources.",
            ["GAP-02"], "controls")
        mine = findings.for_area(root, "purchasing")
        assert fid in {e["id"] for e in mine}

    def test_src_only_grounds_are_not_area_bound(self, tmp_path):
        import findings
        root, area = ipo_copy(tmp_path)
        fid = findings.propose(
            root, "The SOP predates the NetSuite migration.",
            ["SRC-002"], "sources")
        mine = findings.for_area(root, "purchasing")
        assert fid not in {e["id"] for e in mine}

    def test_accepts_a_path_too(self, tmp_path):
        import findings
        root, area = ipo_copy(tmp_path)
        fid = findings.propose(root, "Claim.", ["GAP-01"], "controls")
        assert fid in {e["id"] for e in findings.for_area(root, area)}

    def test_status_filter_passes_through(self, tmp_path):
        import findings
        root, area = ipo_copy(tmp_path)
        fid = findings.propose(root, "Claim.", ["GAP-01"], "controls")
        findings.accept(root, fid)
        assert fid in {e["id"]
                       for e in findings.for_area(root, "purchasing",
                                                  status="accepted")}
        assert not findings.for_area(root, "purchasing", status="proposed")


# --------------------------------------------------------------------------- #
# 4. The dispatch surface (Part D)
# --------------------------------------------------------------------------- #

@needs_dispatch
class TestDispatchSurface:
    def test_skill_carries_the_passage(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "consult-analyst" in low
        assert "analysis.py brief" in low
        assert "accept" in low and "human" in low   # the gate stays stated
        # never inside the drafting loop — stated, not implied
        assert "never" in low

    def test_analyst_contract_names_the_brief_first(self):
        low = ANALYST.read_text(encoding="utf-8").lower()
        assert "analysis.py" in low and "brief" in low
