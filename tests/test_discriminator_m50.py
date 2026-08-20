"""M50 acceptance tests — written BEFORE the build.

Pins: the `Nature:` enum declared on the process-step GAP callout (the
`field_enums:` surface on the declaration — data, not schema code), the
kernel loading and validating it, needs.py carrying `nature` on
discriminated recorded-gap entries (read from the declaration, never
typed), agenda.py splitting its confirm section mechanically on the
field, and the unconsumed-source fixture (M46 A1.5) exercising the
owed-a-read section positively.

Two independent skip gates so the packages land separately with the
suite green at each commit:
  * the enum appearing in the process-step declaration (Parts A-C);
  * an unconsumed source appearing in the IPO fixture ledger (Part D).
"""

import re
import shutil
from pathlib import Path

import pytest

import gatecheck
import yaml

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
DECL = REPO / "kernel" / "types" / "process-step.yaml"
SCRIPTS = REPO / "scripts"

NATURE_ENUM = ("conflict", "evidenced-absence")
SETTLE_HEADING = "what we need you to settle"
CONFIRM_HEADING = "what we would like to confirm"


def _decl_data():
    return yaml.safe_load(DECL.read_text(encoding="utf-8"))


def _gap_entry(data):
    for entry in data.get("callouts", []):
        if entry.get("prefix") == "GAP":
            return entry
    return None


def _enum_declared() -> bool:
    entry = _gap_entry(_decl_data())
    if not entry:
        return False
    enums = entry.get("field_enums") or {}
    return "Nature" in enums


def _fixture_has_unconsumed() -> bool:
    data = yaml.safe_load(
        (IPO_ROOT / "_sources" / "sources.yaml").read_text(encoding="utf-8"))
    for entry in data.get("sources", []):
        touches = entry.get("touches") or {}
        consumed = entry.get("consumed") or {}
        for area, slugs in touches.items():
            if set(slugs or []) - set(consumed.get(area) or []):
                return True
    return False


needs_enum = gatecheck.landed(
    not _enum_declared(),
    reason="M50 Nature enum not declared on process-step GAP yet — the target")

def _agenda_split_built() -> bool:
    src = SCRIPTS / "agenda.py"
    return src.is_file() and SETTLE_HEADING in src.read_text(
        encoding="utf-8").lower()

needs_split = gatecheck.landed(
    not (_enum_declared() and _agenda_split_built()),
    reason="M50 agenda split not built yet — the target")

needs_unconsumed = gatecheck.landed(
    not _fixture_has_unconsumed(),
    reason="M50 unconsumed-source fixture not landed yet — the target")


# --------------------------------------------------------------------------- #
# fixture helpers
# --------------------------------------------------------------------------- #

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


def add_nature(area, fragment: str, gap_id: str, value: str):
    """Append `> - **Nature:** <value>` to the named GAP's blockquote."""
    path = area / fragment
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if gap_id in ln
                 and "VALIDATION REQUIRED" in ln)
    end = start
    while end + 1 < len(lines) and lines[end + 1].startswith(">"):
        end += 1
    lines.insert(end + 1, f"> - **Nature:** {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Part A — the declaration carries the enum
# --------------------------------------------------------------------------- #

@needs_enum
class TestDeclaration:
    def test_gap_declares_nature_field_and_enum(self):
        entry = _gap_entry(_decl_data())
        assert "Nature" in (entry.get("fields") or [])
        assert list(entry["field_enums"]["Nature"]) == list(NATURE_ENUM)

    def test_kernel_exposes_the_enum(self):
        import kernel
        tdecl = kernel.load_type("process-step")
        gap = next(c for c in tdecl.callouts if c.prefix == "GAP")
        assert tuple(gap.field_enums["Nature"]) == NATURE_ENUM

    def test_v1_activity_declaration_untouched(self):
        # the v1 grammar is law behind the compatibility gate — no enum there
        import kernel
        tdecl = kernel.load_type("activity")
        for c in tdecl.callouts:
            assert not getattr(c, "field_enums", {}), c.label

    def test_enum_for_undeclared_field_refuses(self, tmp_path):
        import kernel
        bad = tmp_path / "bad-type.yaml"
        data = _decl_data()
        data["type"] = "bad-type"
        entry = _gap_entry(data)
        entry["field_enums"] = {"Mood": ["sunny"]}  # Mood is not in fields
        bad.write_text(yaml.safe_dump(data), encoding="utf-8")
        with pytest.raises(kernel.TypeDeclError) as exc:
            kernel._parse_decl(bad, yaml.safe_load(bad.read_text()))
        assert "Mood" in str(exc.value)

    def test_empty_enum_refuses(self, tmp_path):
        import kernel
        bad = tmp_path / "bad-type.yaml"
        data = _decl_data()
        data["type"] = "bad-type"
        _gap_entry(data)["field_enums"] = {"Nature": []}
        bad.write_text(yaml.safe_dump(data), encoding="utf-8")
        with pytest.raises(kernel.TypeDeclError):
            kernel._parse_decl(bad, yaml.safe_load(bad.read_text()))

    def test_not_a_parse_gate(self, tmp_path):
        # a GAP with an out-of-enum Nature value still parses — metadata,
        # never a gate (CONTROL's posture, restated for the enum)
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        add_nature(area, "10_receive-invoice.md", "GAP-01", "bananas")
        entries = [e for e in needs.needs(area) if e["kind"] == "recorded-gap"]
        assert any("GAP-01" in g for e in entries for g in e["grounds"])


# --------------------------------------------------------------------------- #
# Part B — needs.py reads it
# --------------------------------------------------------------------------- #

@needs_enum
class TestNeedsNature:
    def test_discriminated_entry_carries_nature(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        add_nature(area, "10_receive-invoice.md", "GAP-01", "conflict")
        add_nature(area, "10_reconcile-statements.md", "GAP-04",
                   "evidenced-absence")
        recorded = [e for e in needs.needs(area)
                    if e["kind"] == "recorded-gap"]
        by_gap = {}
        for e in recorded:
            for g in e["grounds"]:
                m = re.search(r"GAP-\d+", g)
                if m:
                    by_gap.setdefault(m.group(0), e)
        assert by_gap["GAP-01"].get("nature") == "conflict"
        assert by_gap["GAP-04"].get("nature") == "evidenced-absence"

    def test_undiscriminated_entry_omits_the_key(self, tmp_path):
        # absent is absent, never guessed — the fixture's GAPs carry no
        # Nature field, so no entry carries the key
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        recorded = [e for e in needs.needs(area)
                    if e["kind"] == "recorded-gap"]
        assert recorded and all("nature" not in e for e in recorded)

    def test_out_of_enum_value_is_undiscriminated(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        add_nature(area, "10_receive-invoice.md", "GAP-01", "unknown")
        recorded = [e for e in needs.needs(area)
                    if e["kind"] == "recorded-gap"]
        assert all("nature" not in e for e in recorded)

    def test_vocabulary_is_declared_not_typed(self):
        # the enum literals appear in the declaration, never as quoted
        # string literals in the consumers (the M36 shape-audit rule)
        for mod in ("needs.py", "agenda.py"):
            src = (SCRIPTS / mod).read_text(encoding="utf-8")
            assert '"evidenced-absence"' not in src, mod
            assert "'evidenced-absence'" not in src, mod


# --------------------------------------------------------------------------- #
# Part C — the agenda splits its confirm section
# --------------------------------------------------------------------------- #

@needs_split
class TestAgendaSplit:
    _seq = 0

    def _render(self, tmp_path, natures: dict):
        import agenda
        TestAgendaSplit._seq += 1
        root, area = ipo_copy(tmp_path / f"run{TestAgendaSplit._seq}")
        write_objective(area)
        for (fragment, gap_id), value in natures.items():
            add_nature(area, fragment, gap_id, value)
        return agenda.render(area, role="ap-manager").lower()

    def test_conflict_routes_to_the_settle_section(self, tmp_path):
        out = self._render(tmp_path, {
            ("10_reconcile-statements.md", "GAP-04"): "conflict"})
        assert SETTLE_HEADING in out
        settle = out.split(SETTLE_HEADING, 1)[1].split("what we")[0]
        assert "gap-04" in settle

    def test_absence_routes_to_the_confirm_section(self, tmp_path):
        out = self._render(tmp_path, {
            ("10_reconcile-statements.md", "GAP-04"): "evidenced-absence"})
        confirm = out.split(CONFIRM_HEADING, 1)[1].split("what we")[0]
        assert "gap-04" in confirm

    def test_undiscriminated_keeps_the_merged_section(self, tmp_path):
        # legacy and v1-grammar fragments keep rendering where they always did
        out = self._render(tmp_path, {})
        confirm = out.split(CONFIRM_HEADING, 1)[1].split("what we")[0]
        assert "gap-" in confirm

    def test_empty_settle_section_reads_as_an_answer(self, tmp_path):
        # the section renders with its lead-in even when nothing is a
        # conflict — an empty section is an answer, never a failed build
        out = self._render(tmp_path, {})
        assert SETTLE_HEADING in out

    def test_split_is_a_field_read_not_new_judgment(self, tmp_path):
        # the same gap moves sections when only its Nature value changes —
        # nothing else in the record differs
        settled = self._render(tmp_path, {
            ("10_reconcile-statements.md", "GAP-04"): "conflict"})
        confirmed = self._render(tmp_path, {
            ("10_reconcile-statements.md", "GAP-04"): "evidenced-absence"})
        settle_a = settled.split(SETTLE_HEADING, 1)[1].split("what we")[0]
        settle_b = confirmed.split(SETTLE_HEADING, 1)[1].split("what we")[0]
        assert "gap-04" in settle_a and "gap-04" not in settle_b


# --------------------------------------------------------------------------- #
# Part D — the unconsumed-source fixture (M46 A1.5)
# --------------------------------------------------------------------------- #

@needs_unconsumed
class TestUnconsumedSource:
    def test_ledger_carries_a_registered_unread_source(self):
        assert _fixture_has_unconsumed()

    def test_owed_a_read_renders_positively(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        data = yaml.safe_load(
            (root / "_sources" / "sources.yaml").read_text(encoding="utf-8"))
        outstanding = []
        for entry in data["sources"]:
            touches = entry.get("touches") or {}
            consumed = entry.get("consumed") or {}
            for a, slugs in touches.items():
                if set(slugs or []) - set(consumed.get(a) or []):
                    outstanding.append(entry["id"])
        assert outstanding
        out = agenda.render(area, role="ap-manager")
        assert any(sid in out for sid in outstanding)

    def test_consumption_record_clears_the_row(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        ledger = root / "_sources" / "sources.yaml"
        data = yaml.safe_load(ledger.read_text(encoding="utf-8"))
        outstanding = None
        for entry in data["sources"]:
            touches = entry.get("touches") or {}
            consumed = entry.setdefault("consumed", {})
            for a, slugs in touches.items():
                if set(slugs or []) - set(consumed.get(a) or []):
                    outstanding = entry["id"]
                    consumed[a] = list(slugs)
        assert outstanding
        ledger.write_text(yaml.safe_dump(data), encoding="utf-8")
        out = agenda.render(area, role="ap-manager")
        # anchor matches the rendered heading ("...we still owe a read on");
        # the held line above it correctly keeps naming the source
        assert "owe a read" in out.lower()
        owed = out.lower().split("owe a read", 1)[-1]
        assert outstanding.lower() not in owed
