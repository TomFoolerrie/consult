"""M39 acceptance tests (deterministic half) — written BEFORE the build.

Pins: the findings lifecycle (the register class M30 A1 deferred, built
here), grounds-or-refused, the one-direction rule (analysis never writes
into the capture layer), the mechanical candidate generators over the IPO
fixture, and the findings-report definition. The consult-analyst brief is
prose, orchestrator-reviewed.

Skips until scripts/findings.py exists.
"""

import shutil
from pathlib import Path

import pytest

import findings

IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in base.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# 1. The findings lifecycle — propose / accept / reject, grounds-or-refused
# --------------------------------------------------------------------------- #

class TestLifecycle:
    def test_propose_accept_round_trip(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        fid = findings.propose(
            root,
            claim="Variance dispositions carry no system approval",
            grounds=["PP-03", "SRC-001"],
            theme="control-gaps")
        assert fid.startswith("FIND-")
        assert findings.entries(root, status="proposed")
        findings.accept(root, fid)
        accepted = findings.entries(root, status="accepted")
        assert [e["id"] for e in accepted] == [fid]
        assert not findings.entries(root, status="proposed")

    def test_groundless_finding_refused(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(findings.FindingsError):
            findings.propose(root, claim="Everything is bad",
                             grounds=[], theme="vibes")

    def test_unresolvable_ground_refused_by_name(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(findings.FindingsError) as exc:
            findings.propose(root, claim="X", grounds=["SRC-999"],
                             theme="t")
        assert "SRC-999" in str(exc.value)

    def test_reject_is_terminal_and_kept(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        fid = findings.propose(root, claim="C", grounds=["PP-01"],
                               theme="t")
        findings.reject(root, fid, reason="not material")
        rejected = findings.entries(root, status="rejected")
        assert [e["id"] for e in rejected] == [fid]
        # a rejected finding cannot be accepted
        with pytest.raises(findings.FindingsError):
            findings.accept(root, fid)


# --------------------------------------------------------------------------- #
# 2. One direction — analysis never touches the capture layer
# --------------------------------------------------------------------------- #

class TestOneDirection:
    def test_full_lifecycle_leaves_components_untouched(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root / "components")
        src_before = fingerprint(root / "_sources")
        fid = findings.propose(root, claim="C", grounds=["PP-04"],
                               theme="t")
        findings.accept(root, fid)
        fid2 = findings.propose(root, claim="D", grounds=["GAP-05"],
                                theme="t")
        findings.reject(root, fid2, reason="dup")
        assert fingerprint(root / "components") == before
        assert fingerprint(root / "_sources") == src_before


# --------------------------------------------------------------------------- #
# 3. Mechanical candidate generation over the fixture's awkward cases
# --------------------------------------------------------------------------- #

class TestCandidates:
    def test_control_gap_candidates_name_the_controlless_step(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        cands = analysis.control_gap_candidates(area)
        assert any(c["slug"] == "approve-exceptions" for c in cands)
        # every candidate carries its mechanical grounds
        for c in cands:
            assert c.get("grounds"), c

    def test_handoff_candidates_find_the_orphan_output(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        cands = analysis.handoff_candidates(area)
        joined = str(cands).lower()
        assert "reconcile-statements" in joined
        assert any(c["kind"] == "orphan-output" for c in cands)

    def test_pain_inventory_collects_all_voiced_pains(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        pains = analysis.pain_inventory(area)
        assert {p["id"] for p in pains} == {"PP-01", "PP-02", "PP-03", "PP-04"}
        for p in pains:
            assert p.get("srcs"), "every pain carries its source ids"

    def test_candidates_are_read_only(self, tmp_path):
        import analysis
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root)
        analysis.control_gap_candidates(area)
        analysis.handoff_candidates(area)
        analysis.pain_inventory(area)
        assert fingerprint(root) == before


# --------------------------------------------------------------------------- #
# 4. The findings-report definition
# --------------------------------------------------------------------------- #

class TestFindingsReport:
    def test_ships_and_loads(self):
        import definitions
        d = definitions.load_definition("findings-report")
        assert d.skin.format == "docx"

    def test_accepted_only_reaches_a_render_binding(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        a = findings.propose(root, claim="Accepted claim",
                             grounds=["PP-03"], theme="control-gaps")
        findings.accept(root, a)
        r = findings.propose(root, claim="Rejected claim",
                             grounds=["PP-01"], theme="control-gaps")
        findings.reject(root, r, reason="no")
        p = findings.propose(root, claim="Still proposed claim",
                             grounds=["PP-02"], theme="control-gaps")
        renderable = findings.renderable(root)
        ids = {e["id"] for e in renderable}
        assert a in ids and r not in ids and p not in ids
