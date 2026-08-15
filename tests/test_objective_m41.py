"""M41 acceptance tests — written BEFORE the build.

Pins: the engagement objective (M13 config block, typed accessor,
validated names), the business-cycle skeleton (seed to the surveyor's
staging path, promote at the confirm gate — the path M37 A1 recorded as
missing), the objective brief block (goal + cycles + per-deliverable
serviceability gaps), and the prose admissions in the surveyor/librarian
contracts.

Each class skips until its target verb exists — the work packages land
in parallel.
"""

import shutil
from pathlib import Path

import pytest

import client_config
import definitions  # noqa: F401

IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
REPO = Path(__file__).resolve().parent.parent

needs_objective = pytest.mark.skipif(
    not hasattr(client_config, "objective"),
    reason="M41 objective accessor not built yet — the target")


def _scaffold_mod():
    import scaffold
    return scaffold


def needs(attr, module="scaffold"):
    try:
        mod = __import__(module)
    except ImportError:
        return pytest.mark.skip(reason=f"{module} not importable")
    return pytest.mark.skipif(
        not hasattr(mod, attr),
        reason=f"M41 {module}.{attr} not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def write_objective(area, body):
    cdir = area / "_client"
    cdir.mkdir(exist_ok=True)
    (cdir / "objective.yaml").write_text(body, encoding="utf-8")


GOOD_OBJECTIVE = """\
objective:
  goal: Document purchasing and deliver a controls matrix.
  deliverables: [process-controls-matrix, information-request]
  cycles: [procure-to-pay]
"""


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in base.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# 1. The objective accessor (WP-O1)
# --------------------------------------------------------------------------- #

@needs_objective
class TestObjective:
    def test_parses_the_block(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        write_objective(area, GOOD_OBJECTIVE)
        obj = client_config.objective(area)
        assert obj.configured
        assert obj.deliverables == ["process-controls-matrix",
                                    "information-request"]
        assert obj.cycles == ["procure-to-pay"]
        assert "controls matrix" in obj.goal

    def test_absent_means_unconfigured(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        obj = client_config.objective(area)
        assert not obj.configured
        assert obj.deliverables == [] and obj.cycles == []

    def test_bad_deliverable_name_refuses_by_name(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        write_objective(area, """\
objective:
  deliverables: [no-such-deliverable]
""")
        with pytest.raises(client_config.ClientConfigError) as exc:
            client_config.objective(area)
        assert "no-such-deliverable" in str(exc.value)

    def test_bad_cycle_slug_refuses_by_name(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        write_objective(area, """\
objective:
  cycles: [underwater-basket-weaving]
""")
        with pytest.raises(client_config.ClientConfigError) as exc:
            client_config.objective(area)
        assert "underwater-basket-weaving" in str(exc.value)

    def test_unknown_field_refuses(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        write_objective(area, """\
objective:
  goal: g
  surprise: true
""")
        with pytest.raises(client_config.ClientConfigError):
            client_config.objective(area)

    def test_empty_block_is_configured_no_target(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        write_objective(area, "objective: {}\n")
        obj = client_config.objective(area)
        assert obj.configured
        assert obj.deliverables == [] and obj.cycles == []


# --------------------------------------------------------------------------- #
# 2. Seed (WP-O2)
# --------------------------------------------------------------------------- #

@needs("seed_taxonomy")
class TestSeed:
    STAGED = "_reference/.proposed/_taxonomy"

    def test_seeds_reference_l2s_as_parseable_nodes(self, tmp_path):
        import kernel
        import scaffold
        root, area = ipo_copy(tmp_path)
        scaffold.seed_taxonomy(area, "procure-to-pay")
        staged = sorted((area / self.STAGED).glob("*.md"))
        slugs = {p.stem for p in staged}
        assert "invoice-processing" in slugs and "payments" in slugs
        tdecl = kernel.load_type("taxonomy-node")
        for p in staged:
            entity = kernel.parse_entity(p.read_text(encoding="utf-8"),
                                         tdecl, slug=p.stem)
            assert entity is not None

    def test_idempotent_and_never_overwrites(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        scaffold.seed_taxonomy(area, "procure-to-pay")
        staged = area / self.STAGED / "payments.md"
        staged.write_text(staged.read_text(encoding="utf-8")
                          + "\nrefined by an agent\n", encoding="utf-8")
        before = staged.read_text(encoding="utf-8")
        scaffold.seed_taxonomy(area, "procure-to-pay")
        assert staged.read_text(encoding="utf-8") == before

    def test_live_node_outranks_the_skeleton(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        # fixture already has a LIVE _taxonomy/invoice-handling.md set; add
        # one that collides with a reference L2 slug
        live = area / "_taxonomy" / "payments.md"
        live.write_text("# Payments\n\n### Scope\n\nThe live truth.\n",
                        encoding="utf-8")
        scaffold.seed_taxonomy(area, "procure-to-pay")
        assert not (area / self.STAGED / "payments.md").exists()
        assert "live truth" in live.read_text(encoding="utf-8")

    def test_unknown_cycle_refuses_by_name(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        with pytest.raises(Exception) as exc:
            scaffold.seed_taxonomy(area, "not-a-cycle")
        assert "not-a-cycle" in str(exc.value)


# --------------------------------------------------------------------------- #
# 3. Promote (WP-O2)
# --------------------------------------------------------------------------- #

@needs("promote_taxonomy")
class TestPromote:
    def test_staged_nodes_land_live_and_coverage_claims_them(self, tmp_path):
        import coverage_map
        import scaffold
        root, area = ipo_copy(tmp_path)
        scaffold.seed_taxonomy(area, "procure-to-pay")
        scaffold.promote_taxonomy(area)
        assert (area / "_taxonomy" / "payments.md").is_file()
        assert not list((area / "_reference/.proposed/_taxonomy").glob("*.md"))
        cov = coverage_map.coverage(root, {})
        assert cov.get("payments") == "claimed"

    def test_live_collision_refuses_by_name(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        staged_dir = area / "_reference/.proposed/_taxonomy"
        staged_dir.mkdir(parents=True, exist_ok=True)
        (staged_dir / "invoice-handling.md").write_text(
            "# Invoice Handling\n\n### Scope\n\nA colliding proposal.\n",
            encoding="utf-8")
        with pytest.raises(Exception) as exc:
            scaffold.promote_taxonomy(area)
        assert "invoice-handling" in str(exc.value)

    def test_touches_nothing_else_in_proposed(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        proposed = area / "_reference" / ".proposed"
        (proposed / "_taxonomy").mkdir(parents=True, exist_ok=True)
        (proposed / "systems.yaml").write_text("systems: {}\n",
                                               encoding="utf-8")
        (proposed / "_taxonomy" / "payments.md").write_text(
            "# Payments\n\n### Scope\n\nStaged.\n", encoding="utf-8")
        scaffold.promote_taxonomy(area)
        assert (proposed / "systems.yaml").is_file()


# --------------------------------------------------------------------------- #
# 4. The objective block (WP-O3)
# --------------------------------------------------------------------------- #

@needs("objective_block", module="brief")
class TestObjectiveBlock:
    def test_carries_goal_cycles_and_deliverable_gaps(self, tmp_path):
        import brief
        root, area = ipo_copy(tmp_path)
        write_objective(area, GOOD_OBJECTIVE)
        block = brief.objective_block(area)
        assert "controls matrix" in block          # the goal line
        assert "procure-to-pay" in block           # the scope
        assert "process-controls-matrix" in block  # per-deliverable section
        assert "information-request" in block

    def test_unconfigured_says_so(self, tmp_path):
        import brief
        root, area = ipo_copy(tmp_path)
        block = brief.objective_block(area)
        assert "no engagement objective" in block.lower()

    def test_no_manifest_reports_not_scaffolded_never_raises(self, tmp_path):
        import brief
        root, area = ipo_copy(tmp_path)
        write_objective(area, GOOD_OBJECTIVE)
        (area / "manifest.json").unlink()
        block = brief.objective_block(area)   # must not raise
        assert isinstance(block, str) and block.strip()

    def test_read_only(self, tmp_path):
        import brief
        root, area = ipo_copy(tmp_path)
        write_objective(area, GOOD_OBJECTIVE)
        before = fingerprint(root)
        brief.objective_block(area)
        assert fingerprint(root) == before


@needs("objective_block", module="brief")
class TestLibrarianBrief:
    def test_placement_brief_carries_the_objective_section(self, tmp_path):
        import engagement
        root, area = ipo_copy(tmp_path)
        write_objective(area, GOOD_OBJECTIVE)
        out = engagement.placement_brief(root / "components")
        assert "objective" in out.lower()
        assert "procure-to-pay" in out


# --------------------------------------------------------------------------- #
# 5. Prose admissions (WP-O4) — mechanical greps
# --------------------------------------------------------------------------- #

class TestAgentProse:
    def _text(self, rel):
        return (REPO / rel).read_text(encoding="utf-8")

    @needs("objective_block", module="brief")
    def test_surveyor_admits_the_objective_input(self):
        text = self._text("agents/consult-surveyor.md")
        assert "objective" in text.lower()

    @needs("objective_block", module="brief")
    def test_skill_dispatch_row_carries_the_objective(self):
        text = self._text("skills/consult-orchestrate/SKILL.md")
        assert "objective" in text.lower()
