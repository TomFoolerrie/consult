"""M35 WP-D3 gate — the M14 profile alias + the toy end-to-end render smoke.

Two claims, both about the SEAM between the M35 definition language and the
engagement config / render machinery that already exist:

  1. `definitions.resolve_definition(area)` — an engagement that never wrote a
     deliverable definition still has one: the shipped desktop-procedure
     definition shaded by its M14 document profile (sections dropped from the
     bindings, `body_omit` recorded on the block, pruned derived views gone),
     with the profile's provenance line surfaced. No profile at all -> the
     shipped definition unchanged.
  2. A compiled plan is EXECUTABLE: a toy three-block definition compiled
     against a copy of the frozen p2p area renders to a real .docx through the
     existing render path (see scripts/render_glue.py for exactly what
     fidelity that does and does not provide).

The frozen fixture is read-only: every render runs over a tmp_path COPY, and
the render smoke fingerprints the fixture to prove it.
"""

import shutil

from pathlib import Path

import pytest

FIXTURE_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
                / "components" / "procure-to-pay")

import definitions
import client_config


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def area_copy(tmp_path: Path, name: str = "p2p") -> Path:
    """A writable copy of the frozen fixture area, inside an engagement-shaped
    `components/` tree (so `_engagement_root` and client_config both resolve)."""
    area = tmp_path / "eng" / "components" / name
    area.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_AREA, area)
    return area


def fingerprint(root: Path) -> dict:
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in root.rglob("*") if p.is_file()}


#: A profile that exercises all three subtractions at once: `outputs` does not
#: exist, `issues` exists but leaves the rendered body (its register,
#: appendix-a, stays in `derived:` — the validator's cross-field rule), and the
#: screenshot index is pruned.
SHADING_PROFILE = """\
profile:
  sections: [scope, quick-reference, before-you-start, steps, controls, issues]
  body_omit: [issues]
  derived: [procedure-index, role-dictionary, systems, dependencies, raci,
            appendix-a, gap-log]
"""

TOY = """\
deliverable: toy-procedure
shape:
  - id: toy-overview
    title: Toy Overview
    kind: static
    text: This toy deliverable exists to prove a plan is executable.
  - id: procedure-body
    title: Procedures
    kind: entity-part
    binding: steps
    repeat: {over: activity, order: manifest}
  - id: procedure-index
    title: In-Scope Procedures
    kind: view
    writer: python
    binding: procedures
bindings:
  steps: {entities: activity, parts: [steps], order: manifest}
  procedures: {entities: activity, order: manifest}
skin:
  format: docx
  requires: [toc, cover-page]
"""


def toy_definition(tmp_path: Path):
    f = tmp_path / "toy-procedure.yaml"
    f.write_text(TOY, encoding="utf-8")
    return definitions.load_definition_file(f)


# --------------------------------------------------------------------------- #
# 1. The profile alias
# --------------------------------------------------------------------------- #

SHIPPED_IDS = ["process-overview", "procedure-index", "role-dictionary",
               "systems", "procedure-body", "dependencies", "raci",
               "appendix-a", "gap-log", "screenshot-index"]


class TestProfileAlias:
    def test_unconfigured_profile_leaves_shipped_definition_unchanged(
            self, tmp_path):
        area = area_copy(tmp_path)
        assert not client_config.profile(area).configured, "fixture carries none"
        shipped = definitions.load_definition("desktop-procedure")
        resolved = definitions.resolve_definition(area)
        assert [b.id for b in resolved.shape] == [b.id for b in shipped.shape]
        assert [b.id for b in resolved.shape] == SHIPPED_IDS
        assert resolved.bindings == shipped.bindings
        assert all(not b.body_omit for b in resolved.shape)

    def test_unconfigured_profile_surfaces_provenance(self, tmp_path):
        area = area_copy(tmp_path)
        resolved = definitions.resolve_definition(area)
        assert resolved.provenance == client_config.profile(area).report_line()
        assert "none" in resolved.provenance

    def test_profile_subtracts_section_prunes_view_and_records_body_omit(
            self, tmp_path):
        area = area_copy(tmp_path)
        (area / "_client").mkdir(exist_ok=True)
        (area / "_client" / "profile.yaml").write_text(SHADING_PROFILE,
                                                       encoding="utf-8")
        prof = client_config.profile(area)
        assert prof.configured
        assert prof.dropped_sections() == {"outputs"}

        resolved = definitions.resolve_definition(area)
        ids = [b.id for b in resolved.shape]

        # the pruned derived view is gone from the shape (and only that one)
        assert "screenshot-index" not in ids
        assert ids == [i for i in SHIPPED_IDS if i != "screenshot-index"]
        # ...and so is the binding it was the only consumer of
        assert "screenshots" not in resolved.bindings

        # the dropped section leaves every binding that named the part
        assert "outputs" not in resolved.bindings["procedure-parts"]["parts"]
        assert "steps" in resolved.bindings["procedure-parts"]["parts"]
        assert "outputs" not in resolved.bindings["dependencies"]["parts"]

        # body_omit is recorded on the affected block, and its part STAYS bound
        # (a body_omit section is drafted, aggregated and register-collected)
        body = next(b for b in resolved.shape if b.id == "procedure-body")
        assert body.body_omit == ["issues"]
        assert "issues" in resolved.bindings["procedure-parts"]["parts"]

    def test_shaded_definition_still_passes_the_loader_stages(self, tmp_path):
        area = area_copy(tmp_path)
        (area / "_client").mkdir(exist_ok=True)
        (area / "_client" / "profile.yaml").write_text(SHADING_PROFILE,
                                                       encoding="utf-8")
        resolved = definitions.resolve_definition(area)
        # stages 1/2/4 ran during shading; re-run them over the round-tripped
        # form to prove the result is a legal definition, not a private shape.
        raw = definitions._definition_to_raw(resolved)
        again = definitions._stage1_syntax(Path("shaded.yaml"), raw)
        definitions._stage2_vocabulary(again, Path("shaded.yaml"))
        skin = definitions._stage4_skin(again, Path("shaded.yaml"),
                                        raw.get("skin"))
        assert skin.format == "docx"
        assert [b.id for b in again.shape] == [b.id for b in resolved.shape]
        # stage 3 stays a report, and says nothing about the pruned view
        gaps = definitions.serviceability(resolved, area)
        assert all("screenshots" not in g for g in gaps), gaps

    def test_shaded_definition_surfaces_the_profile_report_line(self, tmp_path):
        area = area_copy(tmp_path)
        (area / "_client").mkdir(exist_ok=True)
        (area / "_client" / "profile.yaml").write_text(SHADING_PROFILE,
                                                       encoding="utf-8")
        resolved = definitions.resolve_definition(area)
        prof = client_config.profile(area)
        assert resolved.provenance == prof.report_line()
        assert "body_omit issues" in resolved.provenance
        assert prof.layer_label() in resolved.provenance

    def test_authored_definition_wins_over_the_alias(self, tmp_path):
        """An engagement that wrote its own definition is the whole truth about
        its shape: routing hands back the ordinary (shadowing) load path, with
        no profile shading applied — but provenance is still surfaced."""
        area = area_copy(tmp_path)
        (area / "_client").mkdir(exist_ok=True)
        (area / "_client" / "profile.yaml").write_text(SHADING_PROFILE,
                                                       encoding="utf-8")
        ddir = area.parent / "_client" / "deliverables"
        ddir.mkdir(parents=True)
        (ddir / "desktop-procedure.yaml").write_text(
            TOY.replace("toy-procedure", "desktop-procedure"),
            encoding="utf-8")
        resolved = definitions.resolve_definition(area)
        assert [b.id for b in resolved.shape] == [
            "toy-overview", "procedure-body", "procedure-index"]
        assert resolved.provenance == client_config.profile(area).report_line()


# --------------------------------------------------------------------------- #
# 2. The toy end-to-end render smoke
# --------------------------------------------------------------------------- #

class TestToyRenderSmoke:
    def test_toy_plan_renders_a_docx(self, tmp_path):
        area = area_copy(tmp_path)
        defn = toy_definition(tmp_path)
        plan = definitions.compile_plan(defn, area)
        assert [b.id for b in plan.blocks] == [
            "toy-overview", "procedure-body", "procedure-index"]
        assert [v.kind for v in plan.views] == ["procedure-index"]

        out = tmp_path / "toy.docx"
        stats = definitions.render_plan(plan, area, out)
        assert out.is_file(), "the plan must be executable to a real .docx"
        assert out.stat().st_size > 0
        assert isinstance(stats, dict)

    def test_render_smoke_never_touches_the_frozen_fixture(self, tmp_path):
        before = fingerprint(FIXTURE_AREA)
        area = area_copy(tmp_path)
        defn = toy_definition(tmp_path)
        plan = definitions.compile_plan(defn, area)
        definitions.render_plan(plan, area, tmp_path / "frozen-check.docx")
        assert fingerprint(FIXTURE_AREA) == before

    def test_unexecutable_plan_refuses_by_name(self, tmp_path):
        """A view the area's manifest cannot serve is refused, so the glue
        never quietly renders v1's document instead of the plan's."""
        import render_glue
        area = area_copy(tmp_path)
        f = tmp_path / "unservable.yaml"
        f.write_text(TOY.replace("id: procedure-index",
                                 "id: appendix-controls"), encoding="utf-8")
        plan = definitions.compile_plan(definitions.load_definition_file(f),
                                        area)
        with pytest.raises(render_glue.RenderGlueError) as exc:
            definitions.render_plan(plan, area, tmp_path / "nope.docx")
        assert "appendix-controls" in str(exc.value)
