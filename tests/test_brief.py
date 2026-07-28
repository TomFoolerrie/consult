"""Tests for scripts/brief.py — the deterministic subagent work order.

The brief resolves INPUTS (reading list, profile, notes) from the same
loaders the enforcement points use; it never decides mode and never writes.
"""
import json
from pathlib import Path

import pytest
import yaml

import brief


PROFILE_YAML = """profile:
  sections: [scope, quick-reference, before-you-start, steps, outputs,
             controls, issues]
  body_omit: [issues]
"""


def make_area(tmp_path: Path) -> Path:
    area = tmp_path / "ap"
    (area / "_reference" / "conventions").mkdir(parents=True)
    (area / "_client").mkdir()
    (area / "_review").mkdir()
    (area / "_sources").mkdir()
    manifest = {
        "schema": "consult-mvp-manifest/v1", "area": "ap", "l1": "finance",
        "title": "AP", "l2_order": ["invoices"],
        "components": [
            {"file": "10_bank-rec.md", "heading": "Bank Rec",
             "role": "procedure", "slug": "bank-rec", "l2": "invoices",
             "order": 10},
            {"file": "20_payment-run.md", "heading": "Payment Run",
             "role": "procedure", "slug": "payment-run", "l2": "invoices",
             "order": 20, "upstream": ["bank-rec"]},
            {"file": "84_raci.md", "heading": "RACI Matrix",
             "role": "derived", "derived_kind": "raci", "writer": "agent",
             "order": 84},
        ],
    }
    (area / "manifest.json").write_text(json.dumps(manifest),
                                        encoding="utf-8")
    (area / "10_bank-rec.md").write_text("## Bank Rec\n\ndrafted text\n",
                                         encoding="utf-8")
    (area / "20_payment-run.md").write_text(
        "## Payment Run\n\n<!-- unfilled -->\n", encoding="utf-8")
    (area / "_client" / "profile.yaml").write_text(PROFILE_YAML,
                                                   encoding="utf-8")
    (area / "_reference" / "roles.yaml").write_text("roles: []\n",
                                                    encoding="utf-8")
    (area / "_reference" / "conventions" / "bank-rec.md").write_text(
        "phrasings\n", encoding="utf-8")
    (area / "_sources" / "int1.md").write_text("interview\n",
                                               encoding="utf-8")
    (area / "_reference" / "sources.yaml").write_text(yaml.safe_dump({
        "sources": [
            {"id": "SRC-001", "file": "_sources/int1.md",
             "touches": ["bank-rec"], "consumed": ["bank-rec"]},
            {"id": "SRC-002", "file": "_sources/int2.md",
             "touches": ["payment-run"]},
        ]}), encoding="utf-8")
    (area / "_review" / "bank-rec.notes.yaml").write_text(yaml.safe_dump({
        "items": [
            {"kind": "review", "note": "fix the cutoff wording"},
            {"kind": "source", "src": "SRC-002", "note": "new interview"},
        ]}), encoding="utf-8")
    return area


def snapshot(area: Path) -> set[str]:
    return {str(p) for p in area.rglob("*")}


def test_drafter_brief_resolves_inputs_and_is_read_only(tmp_path, capsys):
    area = make_area(tmp_path)
    before = snapshot(area)
    assert brief.main([str(area), "--slug", "bank-rec"]) == 0
    out = capsys.readouterr().out
    assert snapshot(area) == before                      # read-only

    assert "10_bank-rec.md" in out and "the ONLY file you write" in out
    assert "drafted (update expected)" in out
    # tagged source listed with id + consumed note; the OTHER slug's source
    # is not in this brief
    assert "SRC-001" in out and "already consumed by you" in out
    assert "int2.md" not in out
    # only existing registry files; conventions digest listed
    assert "_reference/roles.yaml" in out.replace("\\", "/")
    assert "systems.yaml" not in out
    assert "conventions/bank-rec.md" in out.replace("\\", "/")
    # resolved profile facts
    assert "body_omit (issues)" in out
    assert "callout kinds in play" in out
    # notes queued, counted by kind
    assert "review: 1" in out and "source: 1" in out
    assert "reconcile.py" in out


def test_unfilled_skeleton_reports_first_draft_and_upstream(tmp_path, capsys):
    area = make_area(tmp_path)
    assert brief.main([str(area), "--slug", "payment-run"]) == 0
    out = capsys.readouterr().out
    assert "unfilled skeleton (first-draft expected)" in out
    # upstream hint resolved to the upstream fragment, marked read-only
    assert "10_bank-rec.md" in out and "READ-ONLY" in out
    # missing tagged source file is flagged, not silently listed
    assert "int2.md" in out and "MISSING" in out
    assert "NOTES QUEUED for you: none" in out


def test_unknown_slug_exits_2_naming_known_slugs(tmp_path, capsys):
    area = make_area(tmp_path)
    with pytest.raises(SystemExit) as e:
        brief.main([str(area), "--slug", "nope"])
    assert e.value.code == 2
    assert "bank-rec" in capsys.readouterr().err


def test_synthesis_brief_first_derivation_vs_incremental(tmp_path, capsys):
    area = make_area(tmp_path)
    assert brief.main([str(area), "--kind", "raci"]) == 0
    out = capsys.readouterr().out
    assert "first derivation (Write the whole file)" in out
    # contract: synthesis agents read the EXTRACT BUNDLE, never fragments
    assert "ap.extract.json" in out and "raci_inputs" in out
    assert "10_bank-rec.md" not in out
    assert "_reference/roles.yaml" in out.replace("\\", "/")

    (area / "84_raci.md").write_text("## RACI Matrix\n", encoding="utf-8")
    assert brief.main([str(area), "--kind", "raci"]) == 0
    out = capsys.readouterr().out
    assert "incremental (Edit changed rows in place" in out
    assert "carry-over baseline" in out


def test_missing_manifest_exits_2(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        brief.main([str(tmp_path), "--slug", "x"])
    assert e.value.code == 2
    assert "manifest.json" in capsys.readouterr().err


def test_ownership_map_lists_siblings_and_other_areas(tmp_path, capsys):
    area = make_area(tmp_path / "components")
    fscp = tmp_path / "components" / "fscp"
    fscp.mkdir()
    (fscp / "manifest.json").write_text(json.dumps({
        "area": "fscp", "title": "Financial Statement Close Process",
        "components": [{"file": "10_sales-package-preparation.md",
                        "role": "procedure",
                        "slug": "sales-package-preparation",
                        "heading": "Sales Package Preparation"}]}),
        encoding="utf-8")
    assert brief.main([str(area), "--slug", "bank-rec"]) == 0
    out = capsys.readouterr().out
    assert "OWNERSHIP MAP" in out
    assert "[[payment-run]]" in out and "sibling procedure" in out
    assert "area fscp — Financial Statement Close Process" in out
    assert "OUT OF SCOPE" in out
