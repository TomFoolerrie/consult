"""M43 acceptance tests — written BEFORE the build.

Pins: the process-step drafting path in the drafter contract (prose
anchors for the grammar the IPO fixture already speaks), the unit line
in the drafter brief (derived from the resolved definition, both unit
types), the declared CTRL field vocabulary, the three hygiene
generators (engagement-scoped, read-only, candidates-not-verdicts),
and the librarian brief's CALLOUT HYGIENE section.

Classes skip until their work package lands.
"""

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
P2P_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
            / "components" / "procure-to-pay")

DRAFTER = REPO / "agents" / "consult-drafter.md"


def _drafter_text():
    return DRAFTER.read_text(encoding="utf-8")


def needs_module():
    try:
        import hygiene  # noqa: F401
        return False
    except ImportError:
        return True


needs_hygiene = pytest.mark.skipif(
    needs_module(), reason="M43 hygiene module not built yet — the target")

needs_path = pytest.mark.skipif(
    "— from" not in _drafter_text() or "process step" not in _drafter_text().lower(),
    reason="M43 drafting path prose not landed yet — the target")

# WP-H2 gates on its own files, not on WP-H1's module — the packages land
# and commit independently, and the suite must be green at each commit.
needs_unit_line = pytest.mark.skipif(
    "YOUR UNIT" not in (REPO / "scripts" / "brief.py").read_text("utf-8"),
    reason="M43 unit line not built yet — the target")

needs_wiring = pytest.mark.skipif(
    "CALLOUT HYGIENE" not in (REPO / "scripts" / "engagement.py").read_text("utf-8"),
    reason="M43 librarian wiring not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in base.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# 1. The drafting path (WP-H3, prose)
# --------------------------------------------------------------------------- #

@needs_path
class TestDraftingPath:
    def test_part_order_and_grammar_anchors(self):
        text = _drafter_text()
        low = text.lower()
        # the six parts in declaration order appear as a stated sequence
        assert "scope" in low and "transformation" in low
        assert "— from" in text and "— to" in text
        assert "[[" in text  # slug-token grammar shown

    def test_law_vs_style_split_is_stated(self):
        low = _drafter_text().lower()
        assert "law" in low
        assert "house style" in low or "style" in low

    def test_substep_list_rules_restated_in_the_path(self):
        low = _drafter_text().lower()
        assert "numbered" in low or "1." in _drafter_text()
        assert "no callouts" in low or "carry no callouts" in low

    def test_unit_line_admitted_in_dispatch_inputs(self):
        low = _drafter_text().lower()
        assert "unit" in low

    def test_honest_absence_is_content(self):
        low = _drafter_text().lower()
        assert "not found" in low or "honest absence" in low \
            or "no system-enforced" in low


# --------------------------------------------------------------------------- #
# 2. The unit line (WP-H2, brief)
# --------------------------------------------------------------------------- #

class TestUnitLine:
    def _brief(self, area, slug):
        import brief
        manifest = json.loads((area / "manifest.json").read_text("utf-8"))
        return brief.drafter_brief(area, manifest, slug)

    @needs_unit_line
    def test_ipo_area_says_process_step(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        out = self._brief(area, "receive-invoice")
        assert "process-step" in out

    @needs_unit_line
    def test_v1_area_says_activity(self):
        out = self._brief(P2P_AREA, "goods-receipt")
        assert "activity" in out


# --------------------------------------------------------------------------- #
# 3. The declared CTRL fields (WP-H1, declaration + kernel)
# --------------------------------------------------------------------------- #

@needs_hygiene
class TestDeclaredFields:
    def test_control_callout_declares_the_four_fields(self):
        import kernel
        tdecl = kernel.load_type("process-step")
        ctrl = [c for c in tdecl.callouts if c.prefix == "CTRL"]
        assert len(ctrl) == 1
        fields = list(getattr(ctrl[0], "fields", []) or [])
        assert fields == ["Performer", "Comparison", "Trigger", "Evidence"]

    def test_fields_are_optional_on_other_callouts(self):
        import kernel
        tdecl = kernel.load_type("process-step")
        pain = [c for c in tdecl.callouts if c.prefix == "PP"]
        assert not (getattr(pain[0], "fields", []) or [])

    def test_activity_type_still_loads_without_fields(self):
        import kernel
        assert kernel.load_type("activity") is not None


# --------------------------------------------------------------------------- #
# 4. The generators (WP-H1)
# --------------------------------------------------------------------------- #

DUP_GAP = """
> **VALIDATION REQUIRED — GAP-90:** The live three-way match tolerance. The
> SOP names two percent; the AP Manager described plus or minus five percent.
> Confirm which tolerance is configured in NetSuite.
"""


@needs_hygiene
class TestDuplicateGaps:
    def test_injected_near_duplicate_is_paired(self, tmp_path):
        import hygiene
        root, area = ipo_copy(tmp_path)
        frag = area / "10_schedule-payment.md"
        text = frag.read_text(encoding="utf-8")
        frag.write_text(text.replace("### Issues", "### Issues\n" + DUP_GAP, 1),
                        encoding="utf-8")
        cands = hygiene.duplicate_gap_candidates(root)
        joined = str(cands)
        assert "GAP-90" in joined and "GAP-02" in joined

    def test_distinct_fixture_gaps_not_paired(self, tmp_path):
        import hygiene
        root, area = ipo_copy(tmp_path)
        assert hygiene.duplicate_gap_candidates(root) == []


@needs_hygiene
class TestAnsweredGaps:
    def test_touched_unconsumed_source_pairs_with_the_steps_gap(self, tmp_path):
        import hygiene
        import yaml
        root, area = ipo_copy(tmp_path)
        ledger_path = root / "_sources" / "sources.yaml"
        data = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
        entries = data.get("sources") or data.get("entries") or []
        # tag the first entry to touch match-po without a consumption record
        entry = entries[0]
        touches = entry.setdefault("touches", {})
        slugs = touches.setdefault("purchasing", [])
        if "match-po" not in slugs:
            slugs.append("match-po")
        consumed = entry.get("consumed") or {}
        if "match-po" in (consumed.get("purchasing") or []):
            consumed["purchasing"].remove("match-po")
        ledger_path.write_text(yaml.safe_dump(data, sort_keys=False),
                               encoding="utf-8")
        cands = hygiene.answered_gap_candidates(root)
        joined = str(cands)
        assert "GAP-02" in joined          # match-po's open gap
        assert entry["id"] in joined       # the unconsumed source named
        for c in cands:
            assert c.get("grounds"), c


@needs_hygiene
class TestThinCtrls:
    def test_prose_only_fixture_ctrls_all_flagged_with_missing_names(
            self, tmp_path):
        import hygiene
        root, area = ipo_copy(tmp_path)
        cands = hygiene.thin_ctrl_candidates(root)
        ids = {c["id"] for c in cands}
        assert "CTRL-01" in ids            # every fixture CTRL is prose-only
        for c in cands:
            assert c.get("missing"), c     # the absent field names, listed
            assert c.get("grounds"), c

    def test_fielded_ctrl_not_flagged(self, tmp_path):
        import hygiene
        root, area = ipo_copy(tmp_path)
        frag = area / "10_receive-invoice.md"
        text = frag.read_text(encoding="utf-8")
        fielded = (
            "> **CONTROL — CTRL-91:** Duplicate-bill refusal, restated.\n"
            "> - **Performer:** NetSuite (system-enforced)\n"
            "> - **Comparison:** supplier id + supplier invoice number vs "
            "existing bills\n"
            "> - **Trigger:** every bill submission\n"
            "> - **Evidence:** the rejected-submission log (SRC-002)\n")
        frag.write_text(text.replace("### Issues",
                                     fielded + "\n### Issues", 1),
                        encoding="utf-8")
        cands = hygiene.thin_ctrl_candidates(root)
        assert "CTRL-91" not in {c["id"] for c in cands}


@needs_hygiene
class TestGeneratorDiscipline:
    def test_all_three_read_only(self, tmp_path):
        import hygiene
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root)
        hygiene.duplicate_gap_candidates(root)
        hygiene.answered_gap_candidates(root)
        hygiene.thin_ctrl_candidates(root)
        assert fingerprint(root) == before

    def test_deterministic_order(self, tmp_path):
        import hygiene
        root, area = ipo_copy(tmp_path)
        a = hygiene.thin_ctrl_candidates(root)
        b = hygiene.thin_ctrl_candidates(root)
        assert a == b


# --------------------------------------------------------------------------- #
# 5. The librarian brief section (WP-H2)
# --------------------------------------------------------------------------- #

@needs_wiring
class TestLibrarianWiring:
    def test_placement_brief_carries_the_hygiene_section(self, tmp_path):
        import engagement
        root, area = ipo_copy(tmp_path)
        out = engagement.placement_brief(root / "components")
        assert "CALLOUT HYGIENE" in out.upper()
        assert "ctrl-missing-field" in out   # the kind vocabulary, synced

    def test_librarian_contract_names_the_feeder(self):
        text = (REPO / "agents" / "consult-librarian.md").read_text("utf-8")
        assert "hygiene" in text.lower()
        assert "does not exist yet" not in text.lower()
