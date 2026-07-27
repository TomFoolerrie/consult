"""Tests for scripts/client_config.py — M13 engagement-level config resolution.

One test per Acceptance bullet in docs/M13-engagement-config.md, plus the
fail-loud-on-malformed-YAML rule and the reporting line.
"""
from pathlib import Path

import pytest

import client_config
from client_config import ClientConfigError
from people import People
from reconcile import load_people_names

PARENT_ORG = """
people:
  - name: Alice Boss
    title: CFO
  - name: Bob Middle
    title: Controller
    reports_to: Alice Boss
"""

AREA_ORG = """
people:
  - name: Zed Local
    title: AP Manager
"""

TAXONOMY = """
taxonomy:
  - l1: accounts-payable
"""


def make_engagement(tmp_path, areas=("accounts-payable", "record-to-report")) -> Path:
    """`components/` with N area folders and no `_client/` anywhere."""
    components = tmp_path / "components"
    for a in areas:
        (components / a).mkdir(parents=True)
    return components


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ------------------------------------------------------------------ bullet 1
def test_parent_only_config_resolves_identically_for_two_areas(tmp_path):
    """Parent-only config: both areas resolve the same org chart, and both
    report the engagement layer."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)

    ap = client_config.load(components / "accounts-payable")
    rr = client_config.load(components / "record-to-report")

    assert ap["people"] == rr["people"]
    assert [p["name"] for p in ap["people"]] == ["Alice Boss", "Bob Middle"]
    assert ap.layer_label() == rr.layer_label() == "_client/ (engagement)"
    assert ap.layers["people"] == "engagement"


def test_parent_only_name_check_fires_identically_in_each_area(tmp_path):
    """reconcile's name source sees the shared org chart from both areas."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)

    ap = load_people_names(components / "accounts-payable")
    rr = load_people_names(components / "record-to-report")

    assert ap == rr == ["Alice Boss", "Bob Middle"]


def test_parent_only_org_chart_ranks_through_people(tmp_path):
    """People (the rank authority) reads the parent layer and says so."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)

    ppl = People(components / "accounts-payable")
    assert ppl.rank("Bob Middle") == 1
    assert ppl.client_layer == "_client/ (engagement)"


# ------------------------------------------------------------------ bullet 2
def test_area_override_shadows_whole_key_and_both_layers_report(tmp_path):
    """Area override of org-chart.yaml: that area uses its own file, the other
    still uses the parent, and both report which layer they used."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    write(components / "accounts-payable" / "_client" / "org-chart.yaml", AREA_ORG)

    ap = client_config.load(components / "accounts-payable")
    rr = client_config.load(components / "record-to-report")

    assert [p["name"] for p in ap["people"]] == ["Zed Local"]
    assert [p["name"] for p in rr["people"]] == ["Alice Boss", "Bob Middle"]
    assert ap.layer_label() == "_client/ (area)"
    assert rr.layer_label() == "_client/ (engagement)"
    assert ap.layers["people"] == "area"
    assert rr.layers["people"] == "engagement"

    assert load_people_names(components / "accounts-payable") == ["Zed Local"]
    assert load_people_names(components / "record-to-report") == [
        "Alice Boss", "Bob Middle"]


def test_area_override_is_per_key_not_whole_layer(tmp_path):
    """A key absent from the area layer still comes from the parent — the area
    file shadows its own top-level key only, with no deep merge."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    write(components / "_client" / "taxonomy.yaml", TAXONOMY)
    write(components / "accounts-payable" / "_client" / "org-chart.yaml", AREA_ORG)

    cfg = client_config.load(components / "accounts-payable")
    assert [p["name"] for p in cfg["people"]] == ["Zed Local"]   # shadowed
    assert cfg["taxonomy"] == [{"l1": "accounts-payable"}]       # inherited
    assert cfg.layers == {"people": "area", "taxonomy": "engagement"}


def test_area_layer_alone_resolves_as_area(tmp_path):
    """No parent `_client/` at all: the area layer answers and reports itself."""
    components = make_engagement(tmp_path)
    write(components / "accounts-payable" / "_client" / "org-chart.yaml", AREA_ORG)

    cfg = client_config.load(components / "accounts-payable")
    assert [p["name"] for p in cfg["people"]] == ["Zed Local"]
    assert cfg.layer_label() == "_client/ (area)"


# ------------------------------------------------------------------ bullet 3
def test_no_client_anywhere_is_the_old_no_context_behavior(tmp_path):
    """No `_client/` anywhere: empty config, `none` reported, and every
    consumer behaves exactly as it did before M13."""
    components = make_engagement(tmp_path)
    area = components / "accounts-payable"

    cfg = client_config.load(area)
    assert cfg == {}
    assert cfg.layers == {} and cfg.conventions == {}
    assert cfg.layer is None
    assert cfg.layer_label() == "none"
    assert client_config.report_line(area) == "client config: none"

    assert load_people_names(area) == []
    ppl = People(area)
    assert ppl.org == {}
    assert ppl.rank("Nobody At All") == 0
    assert ppl.client_layer == "none"


def test_no_client_dir_but_reference_roles_still_feed_the_name_check(tmp_path):
    """The `_reference/` half of the name check is untouched by M13."""
    components = make_engagement(tmp_path)
    area = components / "accounts-payable"
    write(area / "_reference" / "roles.yaml",
          "roles:\n  - slug: ap-clerk\n    people: [Dana Clerk]\n")

    assert load_people_names(area) == ["Dana Clerk"]
    assert client_config.load(area).layer_label() == "none"


# ------------------------------------------------------------------ bullet 4
def test_conventions_merge_by_file_with_area_shadowing(tmp_path):
    """A drafter sees parent files plus its area's, with same-name area files
    shadowing the parent's."""
    components = make_engagement(tmp_path)
    pconv = components / "_client" / "conventions"
    write(pconv / "tone.md", "parent tone\n")
    write(pconv / "numbers.md", "parent numbers\n")
    aconv = components / "accounts-payable" / "_client" / "conventions"
    write(aconv / "tone.md", "area tone\n")
    write(aconv / "vendors.md", "area vendors\n")

    cfg = client_config.load(components / "accounts-payable")
    assert sorted(cfg.conventions) == ["numbers.md", "tone.md", "vendors.md"]
    assert cfg.conventions["tone.md"].read_text(encoding="utf-8") == "area tone\n"
    assert cfg.conventions["numbers.md"].read_text(
        encoding="utf-8") == "parent numbers\n"
    assert cfg.convention_layers == {
        "tone.md": "area", "numbers.md": "engagement", "vendors.md": "area"}

    files = client_config.conventions(components / "accounts-payable")
    assert [p.name for p in files] == ["numbers.md", "tone.md", "vendors.md"]

    # the other area sees only the parent's two
    other = client_config.load(components / "record-to-report")
    assert sorted(other.conventions) == ["numbers.md", "tone.md"]
    assert other.conventions["tone.md"].read_text(encoding="utf-8") == "parent tone\n"


def test_conventions_only_area_layer_still_reports_area(tmp_path):
    """A `conventions/`-only area layer counts as the area layer answering."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    write(components / "accounts-payable" / "_client" / "conventions" / "tone.md", "x")

    cfg = client_config.load(components / "accounts-payable")
    assert cfg.layer_label() == "_client/ (area)"
    assert cfg.layers["people"] == "engagement"   # yaml still from the parent


# ------------------------------------------------------- fail loud / degrade
@pytest.mark.parametrize("layer", ["_client", "accounts-payable/_client"])
def test_malformed_yaml_anywhere_in_the_walk_stops_the_run(tmp_path, layer):
    components = make_engagement(tmp_path)
    bad = write(components / layer / "org-chart.yaml", "people:\n  - name: [x\n")

    with pytest.raises(ClientConfigError) as exc:
        client_config.load(components / "accounts-payable")
    assert str(bad) in str(exc.value)


def test_non_mapping_top_level_is_malformed(tmp_path):
    components = make_engagement(tmp_path)
    bad = write(components / "_client" / "org-chart.yaml", "- just\n- a list\n")
    with pytest.raises(ClientConfigError) as exc:
        client_config.load(components / "accounts-payable")
    assert str(bad) in str(exc.value)


def test_malformed_yaml_reaches_the_name_check_and_people(tmp_path):
    components = make_engagement(tmp_path)
    area = components / "accounts-payable"
    write(components / "_client" / "org-chart.yaml", "people: [unclosed\n")
    with pytest.raises(ClientConfigError):
        load_people_names(area)
    with pytest.raises(ClientConfigError):
        People(area)


def test_duplicate_top_level_key_in_one_layer_stops_the_run(tmp_path):
    """Two files in the same layer claiming one key is ambiguous, not a merge."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    write(components / "_client" / "people-extra.yaml", AREA_ORG)
    with pytest.raises(ClientConfigError) as exc:
        client_config.load(components / "accounts-payable")
    assert "people" in str(exc.value)


def test_same_key_across_layers_is_not_a_duplicate_error(tmp_path):
    """The duplicate guard is per layer — shadowing across layers is the point."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    write(components / "accounts-payable" / "_client" / "people-extra.yaml", AREA_ORG)
    cfg = client_config.load(components / "accounts-payable")
    assert [p["name"] for p in cfg["people"]] == ["Zed Local"]


def test_empty_yaml_file_is_not_malformed(tmp_path):
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", "\n")
    cfg = client_config.load(components / "accounts-payable")
    assert cfg == {}
    # the file exists, so the engagement layer is still what answered
    assert cfg.layer_label() == "_client/ (engagement)"


def test_load_returns_a_plain_dict(tmp_path):
    """`load(area) -> dict`, per the spec — usable anywhere a dict is."""
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    cfg = client_config.load(components / "accounts-payable")
    assert isinstance(cfg, dict)
    assert dict(cfg) == {"people": [
        {"name": "Alice Boss", "title": "CFO"},
        {"name": "Bob Middle", "title": "Controller", "reports_to": "Alice Boss"},
    ]}


def test_report_line_prefix_is_overridable(tmp_path):
    components = make_engagement(tmp_path)
    write(components / "_client" / "org-chart.yaml", PARENT_ORG)
    cfg = client_config.load(components / "accounts-payable")
    assert cfg.report_line("org chart") == "org chart: _client/ (engagement)"
