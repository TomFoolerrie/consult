"""M37 WP-S3 — the advisor's dispatch hint, and the directory-resident
entity-count path.

Two small additive contracts:

1. The `taxonomy` ACTION NAME never changes (v1 tests pin it, and the ladder's
   shape is the contract). What M37 splits is the BRIEF behind it: in central
   mode the surveyor serves the initial survey and the librarian the incremental
   curation pass. The advisor states which in `details.brief`; a v1 engagement
   carries no such key at all.
2. `definitions._area_entity_count` learns a second lookup path for types whose
   entities are directory-resident (`taxonomy-node` -> `<area>/_taxonomy/*.md`).
   The manifest-role table cannot express those truthfully, so the honest fix is
   a separate path, not a widened table entry.
"""

import json
from pathlib import Path

import pytest

import orchestrate  # noqa: E402
import definitions  # noqa: E402


# --------------------------------------------------------------------------- #
# Factories
# --------------------------------------------------------------------------- #

def _manifest(area: Path, slugs=("receive-invoice",)):
    area.mkdir(parents=True, exist_ok=True)
    (area / "manifest.json").write_text(json.dumps({
        "schema": "consult-mvp-manifest/v1",
        "area": area.name, "l1": area.name.upper(), "title": area.name.upper(),
        "l2_order": ["main"],
        "components": [
            {"file": f"10_{s}.md", "heading": s, "order": i + 10,
             "role": "procedure", "slug": s, "l2": "main"}
            for i, s in enumerate(slugs)
        ],
    }), encoding="utf-8")


def make_central(tmp_path, staged="walkthrough.md"):
    """A central-mode engagement: the root carries the M34 ledger."""
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    # M68: a staged file arrives ROUTED (sources enter a central engagement
    # through `route`/`adopt`), so the ledger knows it. An unrouted file is now
    # the `route` action's business, not the taxonomist's — see
    # tests/test_central_mode_m68.py.
    entry = ("sources: []\n" if not staged else
             "sources:\n"
             "  - id: SRC-001\n"
             f"    file: _sources/new/{staged}\n"
             "    hash: deadbeef\n"
             "    touches: {p2p: []}\n"
             "    consumed: {}\n")
    (root / "_sources" / "sources.yaml").write_text(entry, encoding="utf-8")
    if staged:
        (root / "_sources" / "new" / staged).write_text("transcript\n",
                                                        encoding="utf-8")
    return root


def make_v1(tmp_path, staged="walkthrough.md"):
    """A v1 area: sources live in the area's own tree, no central ledger."""
    area = tmp_path / "components" / "cash"
    (area / "_sources" / "new").mkdir(parents=True)
    if staged:
        (area / "_sources" / "new" / staged).write_text("transcript\n",
                                                        encoding="utf-8")
    return area


# --------------------------------------------------------------------------- #
# 1. The dispatch hint
# --------------------------------------------------------------------------- #

class TestDispatchHint:
    def test_central_initial_names_the_surveyor_brief(self, tmp_path):
        root = make_central(tmp_path)
        area = root / "components" / "p2p"
        area.mkdir(parents=True)          # scoped folder, deliberately no manifest
        d = orchestrate.decide(str(area))
        assert d["action"] == "taxonomy"            # name unchanged
        assert d["details"]["mode"] == "initial"
        # M52 mechanical repoint: the hint names the ONE assembled work-order
        # command (was the agent contract path, agents/consult-taxonomist.md)
        assert d["details"]["brief"] == \
            "scripts/brief.py taxonomist <area> --kind SCOPING"

    def test_central_incremental_names_the_librarian_brief(self, tmp_path):
        root = make_central(tmp_path)
        area = root / "components" / "p2p"
        _manifest(area)
        d = orchestrate.decide(str(area))
        assert d["action"] == "taxonomy"
        assert d["details"]["mode"] == "incremental"
        # M52 mechanical repoint: same anchor meaning, new assembly — the
        # curation kind of the one taxonomist brief command
        assert d["details"]["brief"] == \
            "scripts/brief.py taxonomist <area> --kind CURATION"

    def test_v1_carries_no_brief_key(self, tmp_path):
        area = make_v1(tmp_path)
        d = orchestrate.decide(str(area))
        assert d["action"] == "taxonomy" and d["details"]["mode"] == "initial"
        assert "brief" not in d["details"]

    def test_v1_incremental_carries_no_brief_key(self, tmp_path):
        area = make_v1(tmp_path)
        _manifest(area)
        d = orchestrate.decide(str(area))
        assert d["action"] == "taxonomy"
        assert d["details"]["mode"] == "incremental"
        assert "brief" not in d["details"]

    def test_hint_is_the_only_change_to_the_decision(self, tmp_path):
        """Additive: everything else about the decision is what v1 returns."""
        area = make_v1(tmp_path)
        v1 = orchestrate.decide(str(area))
        root = make_central(tmp_path / "central")
        carea = root / "components" / "p2p"
        carea.mkdir(parents=True)
        central = orchestrate.decide(str(carea))
        assert central["action"] == v1["action"]
        assert central["human_gate"] == v1["human_gate"]
        assert (set(central["details"]) - set(v1["details"])) == {"brief"}


# --------------------------------------------------------------------------- #
# 2. Directory-resident entity counting
# --------------------------------------------------------------------------- #

class TestDirectoryResidentEntities:
    def test_taxonomy_nodes_are_counted_from_the_directory(self, tmp_path):
        area = tmp_path / "components" / "p2p"
        _manifest(area)
        (area / "_taxonomy").mkdir()
        for slug in ("ap-aging", "invoice-intake"):
            (area / "_taxonomy" / f"{slug}.md").write_text(
                f"# {slug}\n", encoding="utf-8")
        assert definitions._area_entity_count(area, "taxonomy-node") == 2

    def test_absent_directory_counts_zero_not_an_error(self, tmp_path):
        area = tmp_path / "components" / "p2p"
        _manifest(area)
        assert definitions._area_entity_count(area, "taxonomy-node") == 0

    def test_counted_without_a_manifest(self, tmp_path):
        """Nodes are not manifest members, so a missing manifest must not raise
        for this type — the manifest read is skipped entirely."""
        area = tmp_path / "components" / "p2p"
        (area / "_taxonomy").mkdir(parents=True)
        (area / "_taxonomy" / "ap-aging.md").write_text("# x\n",
                                                        encoding="utf-8")
        assert definitions._area_entity_count(area, "taxonomy-node") == 1

    def test_manifest_role_path_is_untouched(self, tmp_path):
        area = tmp_path / "components" / "p2p"
        _manifest(area, slugs=("a", "b", "c"))
        assert definitions._area_entity_count(area, "activity") == 3

    def test_unmapped_type_still_counts_zero(self, tmp_path):
        """`process-step` has no population of its own in a v1-shaped area, and
        saying so is the honest answer — not a mapping to widen."""
        area = tmp_path / "components" / "p2p"
        _manifest(area)
        assert definitions._area_entity_count(area, "process-step") == 0

    def test_missing_manifest_still_raises_for_manifest_types(self, tmp_path):
        area = tmp_path / "components" / "p2p"
        area.mkdir(parents=True)
        with pytest.raises(OSError):
            definitions._area_entity_count(area, "activity")
