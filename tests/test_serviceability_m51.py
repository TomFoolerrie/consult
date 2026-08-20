"""M51 acceptance tests — written BEFORE the build.

Pins: `definitions.serviceability_records` (the structured return — one
record per gap, binding attribution carried as data), the flat rendering
derived from the records (byte-equal to today's strings), needs.py
consuming the records in ONE loader pass per definition (the
single-binding-copy loop deleted), and the broken-area refusal (a
rootless area or an unreadable manifest refuses by name; a thin-but-real
area still renders — "thin is not a defect", BROKEN now is).

Everything skips until `definitions.serviceability_records` exists.
"""

import json
import shutil
from pathlib import Path

import pytest

import gatecheck

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
SCRIPTS = REPO / "scripts"


def _built() -> bool:
    import importlib
    try:
        definitions = importlib.import_module("definitions")
    except Exception:
        return False
    return hasattr(definitions, "serviceability_records")


needs_records = gatecheck.landed(
    not _built(),
    reason="M51 serviceability_records not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def write_objective(area):
    cdir = area / "_client"
    cdir.mkdir(exist_ok=True)
    (cdir / "objective.yaml").write_text(
        "objective:\n"
        "  goal: Deliver a controls matrix.\n"
        "  deliverables: [process-controls-matrix]\n"
        "  cycles: [procure-to-pay]\n", encoding="utf-8")


def _load(name, area):
    import definitions
    return definitions.load_definition(name, area=area)


def _empty_area(tmp_path):
    """A real engagement layout holding no entities: unserved gaps exist."""
    root = tmp_path / "empty-eng"
    area = root / "components" / "bare"
    area.mkdir(parents=True)
    (area / "manifest.json").write_text(json.dumps(
        {"area": "bare", "components": []}), encoding="utf-8")
    return root, area


# --------------------------------------------------------------------------- #
# Part A — the structured return
# --------------------------------------------------------------------------- #

@needs_records
class TestRecords:
    def test_records_carry_binding_attribution(self, tmp_path):
        import definitions
        root, area = _empty_area(tmp_path)
        defn = _load("process-controls-matrix", area)
        records = definitions.serviceability_records(defn, area)
        assert records, "an empty area must report unserved bindings"
        declared = set(defn.bindings or {})
        for rec in records:
            assert rec["binding"] in declared
            assert isinstance(rec["gap"], str) and rec["gap"].strip()

    def test_flat_rendering_is_derived_and_byte_equal(self, tmp_path):
        # one place formats: the strings the old surface returns ARE the
        # records' gap sentences, same order
        import definitions
        root, area = _empty_area(tmp_path)
        for name in ("process-controls-matrix", "information-request",
                     "findings-report"):
            defn = _load(name, area)
            records = definitions.serviceability_records(defn, area)
            flat = definitions.serviceability(defn, area)
            assert flat == [r["gap"] for r in records], name

    def test_served_area_yields_no_records(self, tmp_path):
        import definitions
        root, area = ipo_copy(tmp_path)
        defn = _load("process-controls-matrix", area)
        assert definitions.serviceability_records(defn, area) == []

    def test_attribution_matches_declaration_order(self, tmp_path):
        import definitions
        root, area = _empty_area(tmp_path)
        defn = _load("process-controls-matrix", area)
        records = definitions.serviceability_records(defn, area)
        declared = list(defn.bindings or {})
        seen = [r["binding"] for r in records]
        # records appear grouped in declaration order
        assert seen == sorted(seen, key=declared.index)


# --------------------------------------------------------------------------- #
# Part B — needs.py makes one loader pass
# --------------------------------------------------------------------------- #

@needs_records
class TestNeedsOnePass:
    def test_single_binding_copy_loop_is_gone(self):
        src = (SCRIPTS / "needs.py").read_text(encoding="utf-8")
        assert "replace(defn, bindings=" not in src
        assert "serviceability_records" in src

    def test_unserved_entries_unchanged(self, tmp_path):
        # same keys, same attribution, same sentences — the M44 fingerprint
        # test pins the byte identity engagement-wide; this pins the feed
        import needs
        root, area = _empty_area(tmp_path)
        write_objective(area)
        entries = [e for e in needs.needs(area, deliverable="process-controls-matrix")
                   if e["kind"] == "binding-unserved"]
        assert entries
        for e in entries:
            assert set(e) >= {"deliverable", "kind", "need", "where", "grounds"}
            assert e["need"] in e["grounds"][0] or e["need"] == e["grounds"][0]


# --------------------------------------------------------------------------- #
# Part C — the broken-area refusal
# --------------------------------------------------------------------------- #

@needs_records
class TestBrokenAreaRefusal:
    def test_rootless_area_refuses_by_name(self, tmp_path):
        import needs
        stray = tmp_path / "not-an-engagement" / "purchasing"
        stray.mkdir(parents=True)
        with pytest.raises(Exception) as exc:
            needs.needs(stray, deliverable="process-controls-matrix")
        assert "purchasing" in str(exc.value)

    def test_unreadable_manifest_refuses_by_name(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        (area / "manifest.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(Exception) as exc:
            needs.needs(area)
        assert "purchasing" in str(exc.value) or "manifest" in str(exc.value)

    def test_thin_area_still_renders(self, tmp_path):
        # a real root + readable manifest + nothing captured: an honest
        # near-empty report, never a refusal ("thin is not a defect")
        import needs
        root, area = _empty_area(tmp_path)
        write_objective(area)
        entries = needs.needs(area, deliverable="process-controls-matrix")
        assert isinstance(entries, list)
        assert all(e["kind"] == "binding-unserved" for e in entries)

    def test_agenda_inherits_the_refusal(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        (area / "manifest.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(Exception):
            agenda.render(area, role="ap-manager")
