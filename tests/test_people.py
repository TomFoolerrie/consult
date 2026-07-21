"""Tests for scripts/people.py — rank, role→contact resolution, prose matching."""
from pathlib import Path

import people as people_mod
from people import People, person_slug


def make_area(tmp_path, org_yaml=None, roles_yaml=None) -> Path:
    area = tmp_path / "area"
    if org_yaml is not None:
        d = area / "_client"
        d.mkdir(parents=True, exist_ok=True)
        (d / "org-chart.yaml").write_text(org_yaml, encoding="utf-8")
    if roles_yaml is not None:
        d = area / "_reference"
        d.mkdir(parents=True, exist_ok=True)
        (d / "roles.yaml").write_text(roles_yaml, encoding="utf-8")
    area.mkdir(parents=True, exist_ok=True)
    return area


ORG = """
people:
  - name: Alice Boss
    title: CFO
  - name: Bob Middle
    title: Controller
    reports_to: Alice Boss
  - name: Carol Deep
    title: Staff Accountant
    reports_to: Bob Middle
  - name: Dan Deep
    title: Senior Accountant
    reports_to: Bob Middle
"""

ROLES = """
roles:
  - slug: preparer
    name: Preparer
    aliases: ["Staff Accountant", "Senior Accountant"]
    people: [Carol Deep, Dan Deep]
  - slug: reviewer
    name: Reviewer
    people: [Bob Middle]
  - slug: approver
    name: Approver
    people: []
  - slug: cfo
    name: Chief Financial Officer
    aliases: [CFO]
    people: [Alice Boss]
"""


def test_person_slug_kebab_cases():
    """person_slug lowercases and kebab-cases, stripping edge punctuation."""
    assert person_slug("  Alice O'Brien-Smith ") == "alice-o-brien-smith"


def test_rank_depth_in_tree(tmp_path):
    """rank is depth in the reports_to tree with root at 0."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.rank("Alice Boss") == 0
    assert p.rank("Bob Middle") == 1
    assert p.rank("Carol Deep") == 2


def test_rank_unknown_person_is_zero(tmp_path):
    """A person absent from the org chart ranks 0."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.rank("Nobody Here") == 0


def test_rank_case_insensitive(tmp_path):
    """rank lookup is case-insensitive on the name."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.rank("carol deep") == 2


def test_rank_dangling_manager_counts_one_level(tmp_path):
    """A manager named but not charted still adds one level of depth."""
    org = "people:\n  - name: X\n    reports_to: Ghost Manager\n"
    p = People(make_area(tmp_path, org, ROLES))
    assert p.rank("X") == 1


def test_rank_cycle_terminates(tmp_path):
    """A reports_to cycle terminates the walk instead of looping forever."""
    org = ("people:\n"
           "  - name: A\n    reports_to: B\n"
           "  - name: B\n    reports_to: A\n")
    p = People(make_area(tmp_path, org, ROLES))
    assert isinstance(p.rank("A"), int)  # terminates


def test_contact_for_role_prefers_deepest(tmp_path):
    """contact_for_role picks the deepest-ranked person; the CFO role gets Alice."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.contact_for_role("reviewer") == "Bob Middle"
    assert p.contact_for_role("cfo") == "Alice Boss"


def test_contact_for_role_tie_first_listed(tmp_path):
    """On equal rank, the first person listed in roles.yaml wins."""
    p = People(make_area(tmp_path, ORG, ROLES))
    # Carol and Dan both rank 2; Carol is listed first.
    assert p.contact_for_role("preparer") == "Carol Deep"


def test_contact_for_role_no_people(tmp_path):
    """A role with no people (or an unknown slug) resolves to ''."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.contact_for_role("approver") == ""
    assert p.contact_for_role("nope") == ""


def test_match_role_longest_match_wins(tmp_path):
    """match_role picks the longest matching label across names + aliases."""
    p = People(make_area(tmp_path, ORG, ROLES))
    # "Senior Accountant" (preparer alias) is longer than "Reviewer".
    assert p.match_role("Prepared by the Senior Accountant, Reviewer signs") == "preparer"
    assert p.match_role("escalate to CFO") == "cfo"


def test_match_role_empty_and_no_match(tmp_path):
    """match_role returns '' for empty text or no matching label."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.match_role("") == ""
    assert p.match_role("the janitor") == ""


def test_contact_for_text(tmp_path):
    """contact_for_text returns (person, slug), ('', slug) when role empty, ('','') otherwise."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.contact_for_text("ask the Reviewer") == ("Bob Middle", "reviewer")
    assert p.contact_for_text("the Approver") == ("", "approver")
    assert p.contact_for_text("nobody relevant") == ("", "")


def test_missing_files_degrade_gracefully(tmp_path):
    """No org chart / roles files → empty model, rank 0, '' contacts."""
    p = People(make_area(tmp_path))
    assert p.rank("Anyone") == 0
    assert p.contact_for_role("x") == ""
    assert p.match_role("Preparer") == ""


def test_malformed_yaml_ignored(tmp_path):
    """Unparseable YAML is treated as absent, not raised."""
    p = People(make_area(tmp_path, org_yaml=": [unbalanced", roles_yaml="{{{"))
    assert p.org == {} and p.role_people == {}


def test_title_and_manager_of(tmp_path):
    """title_of/manager_of return charted values, '' for unknown people."""
    p = People(make_area(tmp_path, ORG, ROLES))
    assert p.title_of("Bob Middle") == "Controller"
    assert p.manager_of("Bob Middle") == "Alice Boss"
    assert p.title_of("Nobody") == ""
    assert p.manager_of("Nobody") == ""
