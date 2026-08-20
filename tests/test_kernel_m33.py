"""M33 acceptance tests — written BEFORE the kernel, as the build target.

These tests define the kernel's public API (docs/v2/M33-brain-kernel.md).
The kernel is BUILT; these are its acceptance gate (the pre-build skip
gate was retired by M64's skip budget),
so the pre-M33 suite stays green; the moment the module lands they become
the acceptance gate. Implementers: make these pass without editing them —
an API disagreement is a spec conversation, not a test edit.

Fixture exception to the suite convention: the frozen engagement snapshot
under tests/fixtures/p2p-complete/ is read (never written) by the
golden-comparison tests below. It is a byte-frozen copy of the completed
procure-to-pay run (from claude/repo-primer-bidlgp) and must never be
regenerated or hand-edited — it is the corpus v1 behavior is measured
against.
"""

from pathlib import Path

import pytest

import doc_model
import callouts as callouts_mod
import aggregate

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
AREA = FIXTURE_ROOT / "components" / "procure-to-pay"

import kernel


# (Fixture integrity lives in test_fixture_p2p.py — it must run even while
# this module skips pre-kernel.)

# --------------------------------------------------------------------------- #
# 1. activity.yaml parity — the loaded declaration IS v1 written down
# --------------------------------------------------------------------------- #

class TestActivityParity:
    @pytest.fixture(scope="class")
    @classmethod
    def activity(cls):
        return kernel.load_type("activity")

    def test_part_slugs_and_titles_match_section_registry(self, activity):
        assert [p.slug for p in activity.parts] == doc_model.SECTION_SLUGS
        assert {p.slug: p.title for p in activity.parts} == doc_model.SECTION_TITLES

    def test_title_aliases_match(self, activity):
        assert activity.title_aliases == doc_model.SECTION_TITLE_ALIASES

    def test_letter_aliases_match(self, activity):
        assert activity.letter_aliases == doc_model.SECTION_LETTER_ALIASES

    def test_slug_aliases_match(self, activity):
        assert activity.slug_aliases == doc_model.SECTION_SLUG_ALIASES

    def test_callout_vocabulary_matches(self, activity):
        assert {c.label: c.prefix for c in activity.callouts} == \
            callouts_mod.LABEL_TO_PREFIX
        for c in activity.callouts:
            assert c.home == callouts_mod.home_section(c.label)

    def test_binding_channels_are_systems_and_roles(self, activity):
        chans = {ch.name: ch.registry for ch in activity.channels}
        assert chans == {"systems": "systems.yaml", "roles": "roles.yaml"}


# --------------------------------------------------------------------------- #
# 2. Fail-loud loader refusals — each names the file and the offending key
# --------------------------------------------------------------------------- #

def _load_bad(tmp_path, name, text):
    f = tmp_path / f"{name}.yaml"
    f.write_text(text, encoding="utf-8")
    with pytest.raises(kernel.TypeDeclError) as exc:
        kernel.load_type_file(f)
    msg = str(exc.value)
    assert name in msg or f.name in msg, "error must name the file"
    return msg


MINIMAL = """\
type: {name}
parts:
  - slug: scope
    title: Scope
    kind: prose
"""


class TestLoaderRefusals:
    def test_unknown_top_level_key(self, tmp_path):
        msg = _load_bad(tmp_path, "badkey",
                        MINIMAL.format(name="badkey") + "surprise: true\n")
        assert "surprise" in msg

    def test_duplicate_part_slug(self, tmp_path):
        msg = _load_bad(tmp_path, "dupe", """\
type: dupe
parts:
  - {slug: scope, title: Scope, kind: prose}
  - {slug: scope, title: Scope Again, kind: prose}
""")
        assert "scope" in msg

    def test_alias_collision_across_parts(self, tmp_path):
        msg = _load_bad(tmp_path, "collide", """\
type: collide
parts:
  - {slug: one, title: One, kind: prose, title_aliases: [Shared]}
  - {slug: two, title: Two, kind: prose, title_aliases: [Shared]}
""")
        assert "Shared" in msg or "shared" in msg

    def test_callout_homed_to_undeclared_part(self, tmp_path):
        msg = _load_bad(tmp_path, "orphanhome",
                        MINIMAL.format(name="orphanhome") + """\
callouts:
  - {label: Gap, prefix: GAP, home: nowhere}
""")
        assert "nowhere" in msg

    def test_channel_without_registry_file(self, tmp_path):
        msg = _load_bad(tmp_path, "nochan",
                        MINIMAL.format(name="nochan") + """\
channels:
  - {name: systems}
""")
        assert "systems" in msg

    def test_never_half_registers(self, tmp_path):
        _load_bad(tmp_path, "half", """\
type: half
parts:
  - {slug: ok, title: OK, kind: prose}
  - {slug: ok, title: Dupe, kind: prose}
""")
        assert not kernel.is_type_loaded("half")


# --------------------------------------------------------------------------- #
# 3. parse_entity ≡ the v1 parsers, over the whole frozen corpus
# --------------------------------------------------------------------------- #

class TestParseEquivalence:
    @pytest.fixture(scope="class")
    @classmethod
    def corpus(cls):
        manifest = doc_model.load_manifest(AREA)
        out = []
        for comp in doc_model.procedures(manifest):
            text = (AREA / comp["file"]).read_text(encoding="utf-8")
            out.append((comp["slug"], text))
        assert out
        return out

    def test_parts_match_split_subsections(self, corpus):
        activity = kernel.load_type("activity")
        for slug, text in corpus:
            entity = kernel.parse_entity(text, activity)
            assert entity.parts_bodies() == aggregate.split_subsections(text), slug

    def test_meta_matches_parse_consult_meta(self, corpus):
        activity = kernel.load_type("activity")
        for slug, text in corpus:
            entity = kernel.parse_entity(text, activity)
            assert entity.bindings() == aggregate.parse_consult_meta(text), slug

    def test_callouts_match_parse_callouts(self, corpus):
        activity = kernel.load_type("activity")
        for slug, text in corpus:
            entity = kernel.parse_entity(text, activity, slug=slug)
            assert entity.callout_dicts() == aggregate.parse_callouts(slug, text), slug

    def test_duplicate_parts_tolerate_and_report(self, corpus):
        # M16 doctrine generalized: duplicate_parts mirrors duplicate_sections.
        activity = kernel.load_type("activity")
        for slug, text in corpus:
            entity = kernel.parse_entity(text, activity)
            assert entity.duplicate_parts() == doc_model.duplicate_sections(text), slug


# --------------------------------------------------------------------------- #
# 4. The second shipped type loads through the SAME code paths
# --------------------------------------------------------------------------- #

class TestProcessStepType:
    def test_loads_with_charter_parts(self):
        ps = kernel.load_type("process-step")
        assert [p.slug for p in ps.parts] == [
            "scope", "inputs", "transformation", "outputs", "controls", "issues",
        ]

    def test_pain_callout_is_declared(self):
        # Continuity ruling (build prep): the pain kind keeps v1's existing
        # PAIN POINT label and PP- prefix — v2 adds the discipline
        # (observation, never assessment; attributed; SRC-evidenced), not a
        # new prefix.
        ps = kernel.load_type("process-step")
        pains = [c for c in ps.callouts if "PAIN" in c.label.upper()]
        assert len(pains) == 1
        assert pains[0].prefix == "PP"
        assert pains[0].home == "issues"

    def test_ipo_fixture_round_trips(self, tmp_path):
        ps = kernel.load_type("process-step")
        text = (Path(__file__).parent / "fixtures" / "ipo-fragment.md").read_text(
            encoding="utf-8")
        entity = kernel.parse_entity(text, ps, slug="approve-invoice")
        bodies = entity.parts_bodies()
        for slug in ("scope", "inputs", "transformation", "outputs"):
            assert bodies.get(slug, "").strip(), f"empty part {slug}"
        assert any("PP-01" in str(c) for c in entity.callout_dicts())


# --------------------------------------------------------------------------- #
# 5. can_serve — precise serviceability answers
# --------------------------------------------------------------------------- #

class TestCanServe:
    def test_unknown_type_and_part_are_named(self):
        errors = kernel.can_serve(
            {"entities": "no-such-type", "parts": ["nope"]}, AREA)
        joined = " ".join(errors)
        assert "no-such-type" in joined

    def test_v1_view_requirements_are_served_by_fixture(self):
        req = {"entities": "activity",
               "parts": ["scope", "steps", "controls"],
               "channels": ["systems", "roles"]}
        assert kernel.can_serve(req, AREA) == []
