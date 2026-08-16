"""M47 acceptance tests — written BEFORE the build.

Pins: the staged `_client/.proposed/` promotion path (mirrors M41's
taxonomy seed/promote discipline), the `provenance: public` ledger field,
the hard rule "public sources inform the needs view; they never discharge
it", and the orchestrate skill's research recipe + review gate.

Two gates: `promote_client` on scaffold (the staging half) and the
provenance handling (the read-side half) — the packages may land
separately, suite green at each commit.
"""

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"


def _has(module, attr):
    try:
        mod = __import__(module)
    except ImportError:
        return False
    return hasattr(mod, attr)


needs_promote = pytest.mark.skipif(
    not _has("scaffold", "promote_client"),
    reason="M47 promote_client not built yet — the target")

needs_provenance = pytest.mark.skipif(
    "provenance" not in (REPO / "scripts" / "coverage_map.py").read_text(
        encoding="utf-8"),
    reason="M47 public-provenance read-side not built yet — the target")

needs_recipe = pytest.mark.skipif(
    "_client/.proposed" not in SKILL.read_text(encoding="utf-8"),
    reason="M47 research recipe not landed in the skill yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def stage_profile(root, name="company_profile.md",
                  body="# Company Profile\n\nStaged research.\n"):
    staged = root / "components" / "_client" / ".proposed"
    staged.mkdir(parents=True, exist_ok=True)
    (staged / name).write_text(body, encoding="utf-8")
    return staged / name


# --------------------------------------------------------------------------- #
# 1. The staging + promote path
# --------------------------------------------------------------------------- #

@needs_promote
class TestPromoteClient:
    def test_reviewed_files_land_live(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        stage_profile(root)
        stage_profile(root, "systems-landscape.md", "# Systems\n\nStaged.\n")
        scaffold.promote_client(root)
        live = root / "components" / "_client"
        assert (live / "company_profile.md").is_file()
        assert (live / "systems-landscape.md").is_file()
        assert not list((live / ".proposed").glob("*.md"))

    def test_live_collision_refuses_by_name(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        live = root / "components" / "_client"
        live.mkdir(parents=True, exist_ok=True)
        (live / "company_profile.md").write_text("# The live truth.\n",
                                                 encoding="utf-8")
        stage_profile(root)
        with pytest.raises(Exception) as exc:
            scaffold.promote_client(root)
        assert "company_profile" in str(exc.value)
        assert "live truth" in (live / "company_profile.md").read_text(
            encoding="utf-8")

    def test_touches_nothing_outside_client(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        stage_profile(root)
        before = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                  for p in root.rglob("*")
                  if p.is_file() and "_client" not in p.parts}
        scaffold.promote_client(root)
        after = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                 for p in root.rglob("*")
                 if p.is_file() and "_client" not in p.parts}
        assert before == after

    def test_nothing_staged_is_a_report_not_a_crash(self, tmp_path):
        import scaffold
        root, area = ipo_copy(tmp_path)
        scaffold.promote_client(root)   # must not raise


# --------------------------------------------------------------------------- #
# 2. Public provenance never discharges a need
# --------------------------------------------------------------------------- #

@needs_provenance
class TestPublicNeverDischarges:
    def _mark_all_public(self, root):
        import yaml
        ledger_path = root / "_sources" / "sources.yaml"
        data = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
        for entry in (data.get("sources") or data.get("entries") or []):
            entry["provenance"] = "public"
        ledger_path.write_text(yaml.safe_dump(data, sort_keys=False),
                               encoding="utf-8")

    def test_public_only_evidence_leaves_every_node_in_the_needs_view(
            self, tmp_path):
        # With EVERY held source public, no taxonomy node can be discharged:
        # the needs view's coverage feed must report every node the area
        # holds. Public informs; it never discharges.
        import needs
        root, area = ipo_copy(tmp_path)
        self._mark_all_public(root)
        entries = needs.needs(area, deliverable="information-request")
        covered = {e["where"] for e in entries if e["kind"] == "coverage"}
        node_slugs = {p.stem for p in (area / "_taxonomy").glob("*.md")}
        assert node_slugs and node_slugs <= covered, (node_slugs, covered)

    def test_client_provided_sources_still_discharge(self, tmp_path):
        # the baseline, untouched: the fixture's client-provided sources keep
        # working exactly as before M47 (provenance defaults to client)
        import needs
        root, area = ipo_copy(tmp_path)
        baseline = needs.needs(area, deliverable="information-request")
        self._mark_all_public(root)
        public = needs.needs(area, deliverable="information-request")
        base_cov = {e["where"] for e in baseline if e["kind"] == "coverage"}
        pub_cov = {e["where"] for e in public if e["kind"] == "coverage"}
        assert base_cov <= pub_cov   # going public never discharges MORE


# --------------------------------------------------------------------------- #
# 3. The recipe (prose)
# --------------------------------------------------------------------------- #

@needs_recipe
class TestRecipe:
    def test_skill_carries_the_recipe_and_the_gate(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "_client/.proposed" in low
        assert "research" in low
        assert "provenance" in low and "public" in low
        assert "review" in low and "promote" in low

    def test_the_hard_rule_is_stated_where_asks_are_shaped(self):
        # "public sources inform the needs view; they never discharge it" —
        # the sentence must live in the dispatch surface, not only in a spec
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "never discharge" in low
