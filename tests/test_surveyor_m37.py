"""M37 acceptance tests (deterministic half) — written BEFORE the build.

Pins: the taxonomy-node entity type, coverage as a PURE FUNCTION (the
charter's hard guardrail: never a file), the conflicted status from
two-source disagreement, and the information-request deliverable loading
through the M35 stages. The surveyor/librarian agent briefs are prose,
reviewed by the orchestrator — this gate covers everything mechanical.

Skips until scripts/coverage_map.py exists.
"""

import json
from pathlib import Path

import pytest

coverage_map = pytest.importorskip(
    "coverage_map", reason="M37 coverage function not built yet — the target")

import kernel      # noqa: E402
import ledger      # noqa: E402
import definitions # noqa: E402


# --------------------------------------------------------------------------- #
# Factory: a central engagement with taxonomy nodes
# --------------------------------------------------------------------------- #

NODE_TMPL = """\
## {title}

### Scope

{prose}

```consult-meta
systems: []
roles: []
```
"""


def make_engagement(tmp_path):
    root = tmp_path / "eng"
    (root / "_sources" / "new").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text("sources: []\n",
                                                    encoding="utf-8")
    area = root / "components" / "p2p"
    (area / "_taxonomy").mkdir(parents=True)
    manifest = {
        "schema": "consult-mvp-manifest/v1",
        "area": "p2p", "l1": "P2P", "title": "P2P", "l2_order": ["main"],
        "components": [
            {"file": "10_receive-invoice.md", "heading": "Receive Invoice",
             "order": 10, "role": "procedure", "slug": "receive-invoice",
             "l2": "main"},
            {"file": "10_match-po.md", "heading": "Match PO", "order": 11,
             "role": "procedure", "slug": "match-po", "l2": "main"},
        ],
    }
    (area / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    # a drafted fragment WITH a citation (evidenced) and one skeleton
    (area / "10_receive-invoice.md").write_text(
        "## Receive Invoice\n\n### Scope\n\nMail intake (SRC-001).\n",
        encoding="utf-8")
    (area / "10_match-po.md").write_text(
        "## Match PO\n\n### Scope\n\nunfilled\n", encoding="utf-8")
    return root, area


def write_node(area, slug, title, prose="Covers X.", fname=None):
    f = area / "_taxonomy" / (fname or f"{slug}.md")
    f.write_text(NODE_TMPL.format(title=title, prose=prose), encoding="utf-8")
    return f


# --------------------------------------------------------------------------- #
# 1. The taxonomy-node type loads and parses through the kernel
# --------------------------------------------------------------------------- #

class TestTaxonomyNodeType:
    def test_type_loads(self):
        t = kernel.load_type("taxonomy-node")
        assert [p.slug for p in t.parts][0] == "scope"

    def test_node_fragment_parses(self, tmp_path):
        root, area = make_engagement(tmp_path)
        f = write_node(area, "invoice-handling", "Invoice Handling")
        t = kernel.load_type("taxonomy-node")
        e = kernel.parse_entity(f.read_text(encoding="utf-8"), t,
                                slug="invoice-handling")
        assert e.parts_bodies().get("scope", "").strip()


# --------------------------------------------------------------------------- #
# 2. coverage() — pure, derived, four statuses, never a file
# --------------------------------------------------------------------------- #

class TestCoverage:
    def test_four_statuses(self, tmp_path):
        root, area = make_engagement(tmp_path)
        # evidenced: node whose step is drafted with a citation
        write_node(area, "invoice-handling", "Invoice Handling")
        (root / "_sources" / "new" / "s1.md").write_text("i\n",
                                                         encoding="utf-8")
        ledger.register(root, "s1.md",
                        {"p2p": ["receive-invoice"]})
        ledger.credit(root, "p2p", filled=["receive-invoice"])
        # sourced: node with a tagged, unconsumed source
        write_node(area, "po-matching", "PO Matching")
        (root / "_sources" / "new" / "s2.md").write_text("j\n",
                                                         encoding="utf-8")
        ledger.register(root, "s2.md", {"p2p": ["match-po"]})
        # claimed: node with nothing tagged
        write_node(area, "vendor-master", "Vendor Master")

        cov = coverage_map.coverage(
            root,
            node_steps={"invoice-handling": ["receive-invoice"],
                        "po-matching": ["match-po"],
                        "vendor-master": []})
        assert cov["invoice-handling"] == "evidenced"
        assert cov["po-matching"] == "sourced"
        assert cov["vendor-master"] == "claimed"

    def test_conflicted_wins(self, tmp_path):
        root, area = make_engagement(tmp_path)
        write_node(area, "approvals", "Approvals",
                   prose=("Ownership disputed.\n\n"
                          "> **VALIDATION REQUIRED — GAP-01:** Owner "
                          "disputed: AP Manager per SRC-001; Controller "
                          "per SRC-002. Both claims recorded.\n"))
        cov = coverage_map.coverage(root, node_steps={"approvals": []})
        assert cov["approvals"] == "conflicted"

    def test_coverage_writes_nothing(self, tmp_path):
        root, area = make_engagement(tmp_path)
        write_node(area, "invoice-handling", "Invoice Handling")
        before = sorted(str(p) for p in root.rglob("*"))
        mtimes = {p: p.stat().st_mtime_ns
                  for p in root.rglob("*") if p.is_file()}
        coverage_map.coverage(root,
                              node_steps={"invoice-handling": []})
        after = sorted(str(p) for p in root.rglob("*"))
        assert before == after, "coverage must never create a file"
        assert mtimes == {p: p.stat().st_mtime_ns
                          for p in root.rglob("*") if p.is_file()}

    def test_no_module_level_cache(self, tmp_path):
        root, area = make_engagement(tmp_path)
        write_node(area, "vendor-master", "Vendor Master")
        assert coverage_map.coverage(
            root, node_steps={"vendor-master": []}
        )["vendor-master"] == "claimed"
        # tag a source; a fresh call must see it (recompute, no cache)
        (root / "_sources" / "new" / "s9.md").write_text("k\n",
                                                         encoding="utf-8")
        ledger.register(root, "s9.md", {"p2p": ["match-po"]})
        assert coverage_map.coverage(
            root, node_steps={"vendor-master": ["match-po"]}
        )["vendor-master"] == "sourced"


# --------------------------------------------------------------------------- #
# 3. The information-request deliverable ships and loads (M35 stages)
# --------------------------------------------------------------------------- #

class TestInformationRequestDefinition:
    def test_ships_and_loads(self):
        d = definitions.load_definition("information-request")
        assert d.skin.format == "docx"
        assert any(b.kind == "view" for b in d.shape)

    def test_coverage_binding_verb_admitted(self):
        d = definitions.load_definition("information-request")
        assert any("coverage" in (b or {})
                   for b in d.bindings.values()), \
            "the info-request definition binds coverage — its named consumer"
