"""Tests for scripts/scope_delta.py — the M5 content-hash change signal.

Pins changed_procedure_slugs against a committed baseline, the .hashes.json
commit round-trip, and the work-order shape. Areas are synthetic under
tmp_path.
"""
import json
import os

import pytest

import scope_delta


def make_area(tmp_path, slugs=("alpha", "beta"), name="treasury"):
    area = tmp_path / name
    area.mkdir()
    components = []
    for i, slug in enumerate(slugs):
        fname = f"10_{slug}.md"
        components.append({"file": fname, "role": "procedure", "slug": slug,
                           "heading": slug.title(), "l2": "ops",
                           "order": 10 + 10 * i})
        (area / fname).write_text(f"## {slug}\n\ncontent {slug}\n",
                                  encoding="utf-8")
    manifest = {"schema": "consult-mvp-manifest/v1", "area": name,
                "l1": "finance", "l2_order": ["ops"], "title": "T",
                "components": components}
    (area / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return str(area)


def test_first_run_all_procedures_changed(tmp_path):
    """No baseline for the kind: every current procedure is 'changed', sorted."""
    area = make_area(tmp_path)
    assert scope_delta.changed_procedure_slugs(area, "dependencies") == ["alpha", "beta"]


def test_commit_writes_hashes_json_and_quiesces(tmp_path):
    """commit rebaselines .hashes.json for the kind; the changed set then becomes empty."""
    area = make_area(tmp_path)
    current = scope_delta.commit(area, "dependencies")
    assert set(current) == {"alpha", "beta"}
    with open(os.path.join(area, ".hashes.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["dependencies"] == current
    assert scope_delta.changed_procedure_slugs(area, "dependencies") == []


def test_changed_detects_edited_procedure_only(tmp_path):
    """After a commit, only the procedure whose file bytes changed is reported."""
    area = make_area(tmp_path)
    scope_delta.commit(area, "raci")
    with open(os.path.join(area, "10_beta.md"), "a", encoding="utf-8") as fh:
        fh.write("edited\n")
    assert scope_delta.changed_procedure_slugs(area, "raci") == ["beta"]


def test_changed_includes_procedure_absent_from_baseline(tmp_path):
    """A procedure added to the manifest after the baseline is 'changed' (absent from baseline)."""
    area = make_area(tmp_path)
    scope_delta.commit(area, "dependencies")
    m_path = os.path.join(area, "manifest.json")
    with open(m_path, encoding="utf-8") as fh:
        m = json.load(fh)
    m["components"].append({"file": "10_gamma.md", "role": "procedure",
                            "slug": "gamma", "heading": "Gamma", "l2": "ops",
                            "order": 30})
    with open(m_path, "w", encoding="utf-8") as fh:
        json.dump(m, fh)
    with open(os.path.join(area, "10_gamma.md"), "w", encoding="utf-8") as fh:
        fh.write("## gamma\n")
    assert scope_delta.changed_procedure_slugs(area, "dependencies") == ["gamma"]


def test_deleted_procedure_file_not_reported(tmp_path):
    """A procedure whose file is missing on disk is absent from the hash map, so it is never 'changed'."""
    area = make_area(tmp_path)
    scope_delta.commit(area, "dependencies")
    os.remove(os.path.join(area, "10_beta.md"))
    assert scope_delta.changed_procedure_slugs(area, "dependencies") == []


def test_baselines_are_per_kind(tmp_path):
    """Committing one kind leaves the other kind's baseline untouched (still first-run)."""
    area = make_area(tmp_path)
    scope_delta.commit(area, "dependencies")
    assert scope_delta.changed_procedure_slugs(area, "raci") == ["alpha", "beta"]


def test_work_order_shape(tmp_path):
    """work_order carries derived_kind, sorted changed slugs, and the area-named bundle path — no prior file contents."""
    area = make_area(tmp_path)
    wo = scope_delta.work_order(area, "dependencies")
    assert wo == {
        "derived_kind": "dependencies",
        "changed_procedure_slugs": ["alpha", "beta"],
        "bundle_path": os.path.join(area, "treasury.extract.json"),
    }


def test_unknown_kind_rejected(tmp_path):
    """work_order and commit both reject a derived_kind outside AGENT_DERIVED_KINDS."""
    area = make_area(tmp_path)
    with pytest.raises(ValueError):
        scope_delta.work_order(area, "systems")
    with pytest.raises(ValueError):
        scope_delta.commit(area, "systems")
