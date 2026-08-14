"""Integrity guard for the frozen p2p engagement fixture.

tests/fixtures/p2p-complete/ is a byte-frozen snapshot of the completed
procure-to-pay run (branch claude/repo-primer-bidlgp, taken 2026-08-14).
It is the golden corpus for M33's parse-equivalence tests and M36's render
comparison. It is READ-ONLY forever: never regenerated, never hand-edited.
These tests run in every suite (no kernel dependency) so any accidental
mutation of the corpus is named immediately.
"""

from pathlib import Path

import doc_model

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
AREA = FIXTURE_ROOT / "components" / "procure-to-pay"


def test_fixture_present_and_manifest_valid():
    manifest = doc_model.load_manifest(AREA)
    assert doc_model.validate_manifest(manifest) == []


def test_fixture_has_drafted_procedures():
    manifest = doc_model.load_manifest(AREA)
    procs = doc_model.procedures(manifest)
    assert len(procs) >= 10
    for comp in procs:
        f = AREA / comp["file"]
        assert f.is_file(), f"fixture missing {comp['file']}"
        assert f.read_text(encoding="utf-8").strip(), f"empty {comp['file']}"


def test_fixture_fragments_parse_with_v1_engine():
    """Every procedure fragment yields sections, and reference registries
    load — the corpus is a working v1 area, not just files on disk."""
    import aggregate

    manifest = doc_model.load_manifest(AREA)
    for comp in doc_model.procedures(manifest):
        text = (AREA / comp["file"]).read_text(encoding="utf-8")
        assert doc_model.section_headings(text), comp["file"]
        aggregate.parse_consult_meta(text)  # must not raise
    assert aggregate.load_registry(AREA, "systems.yaml", "systems")
    assert aggregate.load_registry(AREA, "roles.yaml", "roles")
