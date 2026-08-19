"""M53 acceptance tests — written BEFORE the build.

Pins: the kind resolvers' shared public home (`scripts/kinds.py` — the
callout walk, the prefix-through-declaration read, the nature helpers,
the step-type constant), the published engagement-root helper and the
`selected_statuses` owner living beside them, zero cross-module
private-resolver imports left in scripts/, and the analysis.py module
docstring refreshed to the shipped surface (the brief CLI + all four
generators). Behavior identical by contract — the existing suite green
before and after IS the behavior gate; these tests pin the relocation.

Everything skips until scripts/kinds.py exists.
"""

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
KINDS = SCRIPTS / "kinds.py"

#: private resolver names that must no longer be read across module lines
#: (the owner module keeps whatever private machinery it likes)
_CROSS_MODULE_PRIVATES = (
    "analysis._area_steps",
    "analysis._callouts",
    "analysis._callout_blob",
    "analysis._nature",
    "hygiene._gap_prefix",
    "needs._declared_natures",
    "plan_views._root_of",
    "plan_views._selected_statuses",
)

needs_kinds = pytest.mark.skipif(
    not KINDS.is_file(),
    reason="M53 kinds.py not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


# --------------------------------------------------------------------------- #
# Part A — the shared public home
# --------------------------------------------------------------------------- #

@needs_kinds
class TestPublicHome:
    def test_the_public_surface_exists(self):
        import kinds
        for name in ("area_steps", "callouts", "callout_blob", "nature",
                     "declared_natures", "gap_prefix", "STEP_TYPE",
                     "engagement_root", "selected_statuses"):
            assert hasattr(kinds, name), name
            assert not name.startswith("_")

    def test_resolvers_answer_over_the_fixture(self, tmp_path):
        import kinds
        root, area = ipo_copy(tmp_path)
        tdecl, steps = kinds.area_steps(area)
        assert steps and tdecl.name == kinds.STEP_TYPE
        prefix = kinds.gap_prefix(tdecl, area)
        assert prefix == "GAP"
        gaps = [c for s in steps for c in kinds.callouts(s["entity"], prefix)]
        assert gaps
        assert any("SRC-" in kinds.callout_blob(c) for c in gaps)
        natures = kinds.declared_natures(tdecl, prefix)
        assert natures and all(v == v.strip() for v in natures.values())

    def test_no_cross_module_private_resolver_imports(self):
        for path in sorted(SCRIPTS.glob("*.py")):
            src = path.read_text(encoding="utf-8")
            for pattern in _CROSS_MODULE_PRIVATES:
                owner = pattern.split(".")[0] + ".py"
                if path.name == owner:
                    continue
                assert pattern not in src, f"{path.name} still reads {pattern}"


# --------------------------------------------------------------------------- #
# Part B — the analysis.py docstring
# --------------------------------------------------------------------------- #

@needs_kinds
class TestDocstring:
    def test_names_the_shipped_surface(self):
        import analysis
        doc = analysis.__doc__.lower()
        assert "brief" in doc                     # the M49 CLI
        assert "conflict_records" in doc          # the fourth generator
        assert "control" in doc and "handoff" in doc and "pain" in doc


# --------------------------------------------------------------------------- #
# Part C — the root helper and the statuses owner
# --------------------------------------------------------------------------- #

@needs_kinds
class TestRootHelper:
    def test_resolves_the_engagement_root(self, tmp_path):
        import kinds
        root, area = ipo_copy(tmp_path)
        assert Path(kinds.engagement_root(area)) == root

    def test_rootless_area_refuses_by_name(self, tmp_path):
        import kinds
        stray = tmp_path / "nowhere" / "purchasing"
        stray.mkdir(parents=True)
        with pytest.raises(Exception) as exc:
            kinds.engagement_root(stray)
        assert "purchasing" in str(exc.value)


@needs_kinds
class TestSelectedStatuses:
    def test_the_alias_expands_in_one_place(self, tmp_path):
        import kinds
        expanded = kinds.selected_statuses({"coverage": ["thin"]})
        assert len(expanded) >= 2   # an alias that expands to itself is no alias
        literal = kinds.selected_statuses({"coverage": ["claimed"]})
        assert literal == {"claimed"}

    def test_the_expansion_logic_moved_out_of_plan_views(self):
        src = (SCRIPTS / "plan_views.py").read_text(encoding="utf-8")
        # plan_views may keep a thin delegating alias for its own callers,
        # but the alias table itself lives with the resolvers now
        assert "THIN_MEANS if" not in src
