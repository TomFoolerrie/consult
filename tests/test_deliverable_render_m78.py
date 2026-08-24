"""M78 WP1 acceptance tests — the deliverable render path.

The gate from docs/v2/M78-the-last-hundred-yards.md, Parts A–D:

  A. `render.py --deliverable <name> <area>` — one verb, one pipeline
     (materialize_views -> aggregate over the area -> compile_plan ->
     render_plan), and a refusal by view name when the fill left a pending
     stub behind.
  B. The definition owns its shell: cover title from the definition's
     `title:` (new loader vocabulary), Document Control / Introduction / TOC
     only per `skin.requires`, and the plain area render byte-identical over
     a fixture the new verb never touched.
  C. The export lands under `<central_root>/_exports/` and the checkpoint
     pathspecs name it.
  D. `--mark-sent` advances the bound register's ACCEPTED asks only, and
     survives a second round.

Suite conventions honored: every filesystem fixture is a tmp_path copy of a
frozen one, no network, no wall-clock dependence, no order dependence.
"""

from __future__ import annotations

import json
import os
import shutil
import zipfile

from pathlib import Path

import pytest

import docx_compare

import aggregate
import asks
import definitions
import orchestrate
import render

FIXTURES = Path(__file__).resolve().parent / "fixtures"
IPO_ROOT = FIXTURES / "ipo-engagement"
P2P_AREA = FIXTURES / "p2p-complete" / "components" / "procure-to-pay"
GOLDEN = FIXTURES / "golden" / "p2p-v1"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def ipo_copy(tmp_path) -> tuple[Path, Path]:
    """A writable central-mode engagement: (root, area)."""
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def with_accepted_asks(root: Path, n: int = 2) -> list[str]:
    """The run-3 shape: a register whose asks the human has accepted."""
    ids = []
    for i in range(n):
        aid = asks.propose(
            root, text=f"Please walk us through invoice exception {i}.",
            gaps=[f"receive-invoice:GAP-0{i + 1}"],
            audience="AP Manager", artifact="a short walkthrough")
        asks.accept(root, aid)
        ids.append(aid)
    return ids


def doc_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read("word/document.xml").decode("utf-8")


def manifest_of(area: Path) -> dict:
    return json.loads((area / "manifest.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Part A — the verb round-trips
# --------------------------------------------------------------------------- #
class TestDeliverableVerb:
    @pytest.fixture(scope="class")
    @classmethod
    def rendered(cls, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("m78-verb")
        root, area = ipo_copy(tmp)
        ids = with_accepted_asks(root)
        rc = render.main(["--deliverable", "information-request", str(area)])
        return {"rc": rc, "root": root, "area": area, "ids": ids,
                "out": root / "_exports" / "purchasing_information-request.docx"}

    def test_exit_zero_and_the_file_lands_in_exports(self, rendered):
        assert rendered["rc"] == 0
        assert rendered["out"].is_file() and rendered["out"].stat().st_size > 0

    def test_the_three_views_carry_real_content(self, rendered):
        xml = doc_text(rendered["out"])
        # The curated asks view renders the ACCEPTED asks' client-voiced text
        # (the register's ids deliberately never reach the page — see
        # plan_views.build_client_asks).
        assert "invoice exception 0" in xml
        assert "invoice exception 1" in xml
        assert "AP Manager" in xml
        # The two mechanical feeds below it.
        assert "GAP-" in xml

    def test_no_pending_stub_survives_into_the_document(self, rendered):
        xml = doc_text(rendered["out"])
        assert "Pending generation" not in xml
        assert "Pending synthesis" not in xml

    def test_deliverable_and_slugs_are_mutually_exclusive(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(SystemExit):
            render.main(["--deliverable", "information-request",
                         "--slugs", "receive-invoice", str(area)])

    def test_unknown_definition_refuses_by_name(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(Exception) as exc:
            render.main(["--deliverable", "no-such-deliverable", str(area)])
        assert "no-such-deliverable" in str(exc.value)


class TestFillIsTheRealPipeline:
    """The fill runs aggregate over the AREA — not a hand-built builder ctx.

    The proof is structural: `information-requests` is built by
    `plan_views.build_information_requests`, which reads coverage over the
    whole engagement, and `open-validations` reads the fragments' callouts.
    A hand-rolled minimal ctx cannot serve the manifest-driven derived loop,
    so the check is that the loop's own output (its per-file report and the
    written derived files) is what the verb produced.
    """

    def test_the_manifest_derived_files_are_rewritten_by_aggregate(
            self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with_accepted_asks(root)
        assert render.main(
            ["--deliverable", "information-request", str(area)]) == 0
        by_kind = {c["derived_kind"]: c for c in manifest_of(area)["components"]
                   if c.get("role") == "derived"}
        for kind in ("client-asks", "information-requests",
                     "open-validations"):
            body = (area / by_kind[kind]["file"]).read_text(encoding="utf-8")
            assert "_Pending generation._" not in body
            assert aggregate.marker(kind, "python") in body

    def test_the_v1_extract_bundle_proves_aggregate_ran_over_the_area(
            self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with_accepted_asks(root)
        bundle = area / "purchasing.extract.json"
        if bundle.exists():
            bundle.unlink()
        assert render.main(
            ["--deliverable", "information-request", str(area)]) == 0
        assert bundle.is_file()

    def test_a_view_with_no_registered_builder_refuses(self, tmp_path,
                                                       capsys):
        """N6: the named definition's views ride aggregate's fallback branch,
        so an unserved kind is skipped with a WARNING and the pending stub
        survives — the placeholder refusal is what catches it, by name."""
        root, area = ipo_copy(tmp_path)
        ddir = root / "components" / "_client" / "deliverables"
        ddir.mkdir(parents=True, exist_ok=True)
        (ddir / "made-up.yaml").write_text(
            "deliverable: made-up\n"
            "title: Made Up\n"
            "shape:\n"
            "  - id: nobody-builds-this\n"
            "    title: Nobody Builds This\n"
            "    kind: view\n"
            "    writer: python\n"
            "    numbering: none\n"
            "skin:\n"
            "  format: docx\n"
            "  requires:\n"
            "    - cover-page\n", encoding="utf-8")
        rc = render.main(["--deliverable", "made-up", str(area)])
        assert rc != 0
        assert "nobody-builds-this" in capsys.readouterr().out
        assert not (root / "_exports").exists()


class TestPlaceholderRefusal:
    def test_pending_generation_matches_the_placeholder_regex(self):
        assert render._PLACEHOLDER_RE.search("> _Pending generation._")
        # The v1 alternatives are untouched.
        for s in ("TBD", "Pending user input", "Pending synthesis"):
            assert render._PLACEHOLDER_RE.search(s)

    def test_a_stubbed_view_refuses_by_name_and_writes_nothing(
            self, tmp_path, monkeypatch, capsys):
        root, area = ipo_copy(tmp_path)
        with_accepted_asks(root)
        real = aggregate.run

        def stub_after(area_arg):
            rc = real(area_arg)
            by_kind = {c["derived_kind"]: c
                       for c in manifest_of(area)["components"]
                       if c.get("role") == "derived"}
            comp = by_kind["open-validations"]
            (area / comp["file"]).write_text(
                f"## {comp['heading']}\n\n"
                f"{aggregate.marker('open-validations', 'python')}\n\n"
                "> _Pending generation._\n", encoding="utf-8")
            return rc

        monkeypatch.setattr(aggregate, "run", stub_after)
        rc = render.main(["--deliverable", "information-request", str(area)])
        assert rc != 0
        out = capsys.readouterr().out
        assert "open-validations" in out
        assert not (root / "_exports").exists()

    def test_a_working_render_of_an_unaggregated_area_still_renders(
            self, tmp_path):
        """H7: the refusal is scoped to the --deliverable path. A
        `require_views=False` plan render over an area whose views carry the
        pending stub is a supported v1 shape and must keep rendering."""
        import render_glue
        root, area = ipo_copy(tmp_path)
        definitions.materialize_views(area, name="information-request")
        d = definitions.load_definition("information-request")
        plan = definitions.compile_plan(d, area)
        out = tmp_path / "working.docx"
        render_glue.render_plan(plan, area, out, skin=d.skin,
                                require_views=False)
        assert out.is_file() and out.stat().st_size > 0


# --------------------------------------------------------------------------- #
# Part B — the definition owns its shell
# --------------------------------------------------------------------------- #
class TestTitleVocabulary:
    def test_title_is_admitted_top_level_vocabulary(self):
        assert "title" in definitions._ALLOWED_TOP_KEYS

    def test_an_unknown_top_key_still_refuses(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("deliverable: bad\ntitle: Bad\ncaption: nope\n"
                     "shape: []\nskin:\n  format: docx\n", encoding="utf-8")
        with pytest.raises(definitions.DefinitionError) as exc:
            definitions.load_definition_file(p)
        assert "caption" in str(exc.value)

    def test_a_non_string_title_refuses(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("deliverable: bad\ntitle: []\nshape: []\n"
                     "skin:\n  format: docx\n", encoding="utf-8")
        with pytest.raises(definitions.DefinitionError) as exc:
            definitions.load_definition_file(p)
        assert "title" in str(exc.value)

    def test_the_shipped_information_request_carries_a_title(self):
        d = definitions.load_definition("information-request")
        assert definitions.deliverable_title(d) == "Information Request"

    def test_absent_title_defaults_from_the_name(self, tmp_path):
        p = tmp_path / "untitled.yaml"
        p.write_text("deliverable: some-thing\n"
                     "shape:\n"
                     "  - id: preamble\n"
                     "    title: Preamble\n"
                     "    kind: static\n"
                     "    text: hello\n"
                     "skin:\n  format: docx\n", encoding="utf-8")
        d = definitions.load_definition_file(p)
        assert d.title is None
        assert definitions.deliverable_title(d) == "Some Thing"


class TestShellFollowsTheSkin:
    @pytest.fixture(scope="class")
    @classmethod
    def xml(cls, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("m78-shell")
        root, area = ipo_copy(tmp)
        with_accepted_asks(root)
        assert render.main(
            ["--deliverable", "information-request", str(area)]) == 0
        return doc_text(root / "_exports"
                        / "purchasing_information-request.docx")

    def test_cover_is_titled_by_the_definition(self, xml):
        assert "Information Request" in xml

    def test_no_document_control_front_matter(self, xml):
        # information-request's skin requires neither document-control nor toc.
        assert "Summary of Changes" not in xml

    def test_no_introduction_divider(self, xml):
        assert "Introduction" not in xml

    def test_no_table_of_contents_field(self, xml):
        assert "TOC \\o" not in xml and 'w:instrText' not in xml

    def test_a_skin_that_requires_the_furniture_keeps_it(self, tmp_path):
        """desktop-procedure requires toc + document-control, so its
        definition render carries exactly the v1 furniture."""
        import render_glue
        area = tmp_path / "eng" / "components" / "p2p"
        area.parent.mkdir(parents=True)
        shutil.copytree(P2P_AREA, area)
        d = definitions.load_definition("desktop-procedure")
        plan = definitions.compile_plan(d, area)
        out = tmp_path / "dp.docx"
        render_glue.render_plan(plan, area, out, skin=d.skin,
                                furniture=d.skin.requires)
        body = doc_text(out)
        assert "Summary of Changes" in body
        assert "Introduction" in body


class TestV1RenderIsUntouched:
    def test_untouched_fixture_still_matches_the_committed_golden(
            self, tmp_path):
        """H6: `--deliverable` permanently adds view components to the manifest
        of the area it runs over, so the byte-identity comparison runs over a
        fixture the verb never touched."""
        root, ipo_area = ipo_copy(tmp_path)
        with_accepted_asks(root)
        assert render.main(
            ["--deliverable", "information-request", str(ipo_area)]) == 0

        area = tmp_path / "v1" / "components" / "p2p"
        area.parent.mkdir(parents=True)
        shutil.copytree(P2P_AREA, area)
        out = tmp_path / "p2p.docx"
        render.render_folder(area, out, mode="working", emit_signal=False)
        assert docx_compare.compare(GOLDEN, out,
                                    label_a="golden", label_b="v1") == []


# --------------------------------------------------------------------------- #
# Part C — the export has a home the checkpoint sees
# --------------------------------------------------------------------------- #
class TestExportHome:
    def test_output_override_still_wins(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with_accepted_asks(root)
        out = tmp_path / "elsewhere" / "ir.docx"
        out.parent.mkdir()
        assert render.main(["--deliverable", "information-request",
                            "-o", str(out), str(area)]) == 0
        assert out.is_file()
        assert not (root / "_exports").exists()

    def test_v1_area_default_output_is_unchanged(self, tmp_path):
        area = tmp_path / "components" / "p2p"
        area.parent.mkdir(parents=True)
        shutil.copytree(P2P_AREA, area)
        assert render._infer_output("folder", area, None) == \
            area / "procure-to-pay_process-doc.docx"

    def test_checkpoint_pathspecs_name_exports(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        (root / "_exports").mkdir()
        specs = orchestrate._checkpoint_pathspecs(str(area), str(root))
        assert specs[0] == "."
        assert specs.count(os.path.join("..", "..", "_exports")) == 1

    def test_absent_exports_is_dropped(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        assert not (root / "_exports").exists()
        specs = orchestrate._checkpoint_pathspecs(str(area), str(root))
        assert not any("_exports" in s for s in specs)

    def test_v1_pathspecs_stay_exactly_dot(self, tmp_path):
        area = tmp_path / "components" / "p2p"
        area.parent.mkdir(parents=True)
        shutil.copytree(P2P_AREA, area)
        assert orchestrate._checkpoint_pathspecs(str(area), None) == ["."]


# --------------------------------------------------------------------------- #
# Part D — the register keeps up with the send
# --------------------------------------------------------------------------- #
class TestMarkSent:
    def test_without_the_flag_the_register_is_untouched(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        ids = with_accepted_asks(root)
        assert render.main(
            ["--deliverable", "information-request", str(area)]) == 0
        assert {e["id"]: e["status"] for e in asks.entries(root)} == \
            {i: asks.ACCEPTED for i in ids}

    def test_two_rounds_send_once_and_do_not_crash(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        ids = with_accepted_asks(root)
        argv = ["--deliverable", "information-request", "--mark-sent",
                str(area)]
        assert render.main(argv) == 0
        assert {e["status"] for e in asks.entries(root)} == {asks.SENT}

        # Round two: a new accepted ask beside the already-sent ones. The
        # already-sent are skipped silently (H4) rather than crashing on the
        # sent -> sent transition the lifecycle forbids.
        more = with_accepted_asks(root, 1)
        assert render.main(argv) == 0
        by_id = {e["id"]: e["status"] for e in asks.entries(root)}
        assert by_id[more[0]] == asks.SENT
        for i in ids:
            assert by_id[i] == asks.SENT

    def test_proposed_asks_are_never_sent(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with_accepted_asks(root)
        pid = asks.propose(root, text="Not yet accepted.",
                           gaps=["receive-invoice:GAP-09"],
                           audience="Controller", artifact="an SOP")
        assert render.main(["--deliverable", "information-request",
                            "--mark-sent", str(area)]) == 0
        by_id = {e["id"]: e["status"] for e in asks.entries(root)}
        assert by_id[pid] == asks.PROPOSED

    def test_mark_sent_requires_the_deliverable_flag(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(SystemExit):
            render.main(["--mark-sent", str(area)])

    def test_a_definition_binding_no_asks_refuses_mark_sent(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(SystemExit) as exc:
            render.main(["--deliverable", "findings-report", "--mark-sent",
                         str(area)])
        assert "findings-report" in str(exc.value)
