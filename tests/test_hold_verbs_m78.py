"""M78 Parts E and F — the gate answer writes the hold, and damage is not done.

Part E: `orchestrate.py hold/release-hold` are the M17 amendment — the rule
NARROWS ("no writer outside an explicit human gate answer"), it does not fall.
The pins here are the ones that make the amendment safe:

  * LINE SURGERY: every byte of the file that is not part of the `hold:` block
    survives, comments inside the block included (client_config is
    `safe_load`-only, so a round-trip would eat them)
  * SELF-VERIFICATION: the verb re-reads through `client_config.holds()` and
    RESTORES the original bytes when the result is not exactly what it meant
  * the OWNING file and layer are edited — never a second `hold:` key in the
    same layer (which raises and would wedge every `decide()` in the area)
  * area shadows engagement WHOLE, so an engagement-layer hold refuses at
    `--area` scope and NAMES the engagement file
  * unknown names, GATE names and no-ops refuse loudly, exit 2, write nothing
  * no `decide()` guard and no agent contract invokes the verbs

Part F: a deleted `_sources/sources.yaml` reads as a finished engagement. It
routes to the EXISTING `unresolvable` gate (no new action name), detected as a
strict conjunction at one ancestor, with `p2p-complete` as the named negative.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import client_config
import orchestrate

from test_sticky_holds import area_with, write_hold

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def hold_path(folder):
    return Path(folder) / "_client" / "consult.yaml"


def run_cli(*argv):
    return subprocess.run([sys.executable, str(SCRIPTS / "orchestrate.py"),
                           *argv], capture_output=True, text=True)


# --------------------------------------------------------------------------- #
# 1. Line surgery — every non-`hold:` byte survives
# --------------------------------------------------------------------------- #

COMMENTED = """\
# our engagement policy, hand-written
people:
  - name: Dana   # the AP lead
hold:
  # the taxonomist is still curating asks
  - fill
lexicon:
  terms: [BlackLine]
"""


class TestSurgeryIsByteFaithful:
    def _write(self, tmp_path, body):
        folder = area_with(tmp_path)
        path = hold_path(folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return folder, path

    def test_holding_leaves_every_other_line_identical(self, tmp_path):
        folder, path = self._write(tmp_path, COMMENTED)
        before = path.read_text(encoding="utf-8").splitlines()
        out = orchestrate.edit_hold(folder, "render")
        after = path.read_text(encoding="utf-8").splitlines()
        assert out["held"] == ["fill", "render"]
        # every line that is not a hold item is byte-identical, in order
        assert [ln for ln in before if ln.strip() != "- fill"] == \
               [ln for ln in after if ln.strip() not in ("- fill", "- render")]
        assert "  # the taxonomist is still curating asks" in after
        assert orchestrate._holds(folder).actions == ["fill", "render"]

    def test_releasing_keeps_the_comment_inside_the_block(self, tmp_path):
        folder, path = self._write(tmp_path, COMMENTED)
        out = orchestrate.edit_hold(folder, "fill", release=True)
        text = path.read_text(encoding="utf-8")
        assert out["held"] == []
        assert "# the taxonomist is still curating asks" in text
        assert "# our engagement policy, hand-written" in text
        assert "- name: Dana   # the AP lead" in text
        assert "terms: [BlackLine]" in text
        assert orchestrate._holds(folder).actions == []

    def test_a_flow_list_stays_a_flow_list(self, tmp_path):
        folder, path = self._write(tmp_path,
                                   "hold: [fill]  # ask-first round 2\nx: 1\n")
        orchestrate.edit_hold(folder, "render")
        assert path.read_text(encoding="utf-8") == \
            "hold: [fill, render]  # ask-first round 2\nx: 1\n"
        orchestrate.edit_hold(folder, "fill", release=True)
        assert path.read_text(encoding="utf-8") == \
            "hold: [render]  # ask-first round 2\nx: 1\n"

    def test_an_empty_block_takes_the_first_hold(self, tmp_path):
        folder, path = self._write(tmp_path, "hold: []\n")
        orchestrate.edit_hold(folder, "fill")
        assert orchestrate._holds(folder).actions == ["fill"]

    def test_the_created_file_says_it_is_human_owned(self, tmp_path):
        folder = area_with(tmp_path)
        assert not hold_path(folder).exists()
        out = orchestrate.edit_hold(folder, "fill")
        text = hold_path(folder).read_text(encoding="utf-8")
        assert out["created"] is True
        assert text.splitlines()[0].startswith("# Human-owned")
        assert "Hand edits win" in text
        assert orchestrate._holds(folder).actions == ["fill"]
        # nothing but the hold key: the file is the human's from here on
        assert set(client_config.load(folder).layers) == {"hold"}


# --------------------------------------------------------------------------- #
# 2. The owning file, the owning layer — the wedge is unreachable
# --------------------------------------------------------------------------- #

class TestOwningFile:
    def test_a_hold_in_another_file_is_edited_in_place(self, tmp_path):
        """The duplicate-key wedge: `hold:` in a non-`consult.yaml` file of the
        same layer. Creating `consult.yaml` with a second `hold:` would raise
        on every later `decide()`, so the verb edits the file that OWNS the
        key (`cfg.key_files`) and creates nothing."""
        folder = area_with(tmp_path)
        owner = Path(folder) / "_client" / "policy.yaml"
        owner.parent.mkdir(parents=True, exist_ok=True)
        owner.write_text("hold:\n  - fill\n", encoding="utf-8")
        out = orchestrate.edit_hold(folder, "render")
        assert out["file"] == str(owner)
        assert not hold_path(folder).exists()
        assert orchestrate._holds(folder).actions == ["fill", "render"]
        # and the config still loads — no duplicate key anywhere
        assert client_config.load(folder)["hold"] == ["fill", "render"]

    def test_release_against_an_engagement_hold_refuses_and_names_it(self,
                                                                     tmp_path):
        folder = area_with(tmp_path, engagement_hold=["fill", "render"])
        eng = Path(tmp_path) / "_client" / "consult.yaml"
        before = eng.read_text(encoding="utf-8")
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "fill", release=True)
        assert str(eng) in str(exc.value)
        assert "shadows it WHOLE" in str(exc.value)
        assert eng.read_text(encoding="utf-8") == before
        assert not hold_path(folder).exists()

    def test_hold_against_an_engagement_list_refuses_too(self, tmp_path):
        folder = area_with(tmp_path, engagement_hold=["render"])
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "fill")
        assert str(Path(tmp_path) / "_client" / "consult.yaml") in str(exc.value)
        assert not hold_path(folder).exists()

    def test_an_area_list_shadowing_an_engagement_one_is_editable(self,
                                                                  tmp_path):
        """The area layer answers, so the area file is the one edited — the
        engagement file is never touched."""
        folder = area_with(tmp_path, hold=["fill"], engagement_hold=["render"])
        eng = Path(tmp_path) / "_client" / "consult.yaml"
        before = eng.read_text(encoding="utf-8")
        out = orchestrate.edit_hold(folder, "aggregate")
        assert out["file"] == str(hold_path(folder))
        assert eng.read_text(encoding="utf-8") == before
        assert orchestrate._holds(folder).actions == ["fill", "aggregate"]


# --------------------------------------------------------------------------- #
# 3. Refusals — loud, exit 2, nothing written
# --------------------------------------------------------------------------- #

class TestRefusals:
    def test_an_unknown_action_refuses(self, tmp_path):
        folder = area_with(tmp_path)
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "fil")
        assert "unknown action" in str(exc.value)
        assert not hold_path(folder).exists()

    @pytest.mark.parametrize("gate", ["confirm", "done", "review", "route"])
    def test_a_gate_action_refuses(self, tmp_path, gate):
        folder = area_with(tmp_path)
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, gate)
        assert "already a stop" in str(exc.value)
        assert not hold_path(folder).exists()

    def test_holding_a_held_action_refuses(self, tmp_path):
        folder = area_with(tmp_path, hold=["fill"])
        before = hold_path(folder).read_text(encoding="utf-8")
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "fill")
        assert "already held" in str(exc.value)
        assert hold_path(folder).read_text(encoding="utf-8") == before

    def test_releasing_an_unheld_action_refuses(self, tmp_path):
        folder = area_with(tmp_path, hold=["render"])
        before = hold_path(folder).read_text(encoding="utf-8")
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "fill", release=True)
        assert "is not held" in str(exc.value)
        assert hold_path(folder).read_text(encoding="utf-8") == before

    def test_releasing_with_no_hold_key_anywhere_refuses(self, tmp_path):
        folder = area_with(tmp_path)
        with pytest.raises(orchestrate.HoldEditError):
            orchestrate.edit_hold(folder, "fill", release=True)
        assert not hold_path(folder).exists()

    def test_a_bare_scalar_hold_refuses_by_name(self, tmp_path):
        """The shape this surgery does not support, refused BY NAME rather than
        guessed at — a guess here rewrites a human's policy file."""
        folder = area_with(tmp_path)
        path = hold_path(folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("hold: fill\n", encoding="utf-8")
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "render")
        assert "bare scalar" in str(exc.value)
        assert path.read_text(encoding="utf-8") == "hold: fill\n"

    def test_a_multiline_flow_list_refuses(self, tmp_path):
        folder = area_with(tmp_path)
        path = hold_path(folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        body = "hold: [\n  fill,\n]\n"
        path.write_text(body, encoding="utf-8")
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "render")
        assert "more than one line" in str(exc.value)
        assert path.read_text(encoding="utf-8") == body


class TestSelfVerification:
    def test_a_bad_edit_is_restored_and_refused(self, tmp_path, monkeypatch):
        """Surgery that cannot verify itself does not land: the intended set is
        re-read through `client_config.holds()` and a mismatch puts the
        original bytes back."""
        folder = area_with(tmp_path, hold=["fill"])
        path = hold_path(folder)
        before = path.read_text(encoding="utf-8")
        monkeypatch.setattr(orchestrate, "_hold_lines",
                            lambda *a, **k: ["hold: [aggregate]\n"])
        with pytest.raises(orchestrate.HoldEditError) as exc:
            orchestrate.edit_hold(folder, "render")
        assert "did not verify" in str(exc.value)
        assert path.read_text(encoding="utf-8") == before
        assert orchestrate._holds(folder).actions == ["fill"]

    def test_a_bad_creation_leaves_no_file_behind(self, tmp_path, monkeypatch):
        folder = area_with(tmp_path)
        monkeypatch.setattr(orchestrate, "_hold_lines",
                            lambda *a, **k: ["hold: [aggregate]\n"])
        with pytest.raises(orchestrate.HoldEditError):
            orchestrate.edit_hold(folder, "fill")
        assert not hold_path(folder).exists()

    def test_a_wedged_result_is_restored(self, tmp_path, monkeypatch):
        """A landed edit that makes the config UNREADABLE is a failure too —
        the restore path covers the wedge, not just the wrong list."""
        folder = area_with(tmp_path, hold=["fill"])
        path = hold_path(folder)
        before = path.read_text(encoding="utf-8")
        monkeypatch.setattr(orchestrate, "_hold_lines",
                            lambda *a, **k: ["hold: [fill, render\n"])
        with pytest.raises(orchestrate.HoldEditError):
            orchestrate.edit_hold(folder, "render")
        assert path.read_text(encoding="utf-8") == before


# --------------------------------------------------------------------------- #
# 4. The CLI surface — the verbs the gate answer names
# --------------------------------------------------------------------------- #

class TestCLI:
    def test_the_round_trip_runs_from_the_command_line(self, tmp_path):
        folder = area_with(tmp_path)
        r = run_cli("hold", "--area", folder, "fill")
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["held"] == ["fill"]
        assert orchestrate._holds(folder).actions == ["fill"]
        r = run_cli("release-hold", "--area", folder, "fill")
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout)["held"] == []
        assert orchestrate._holds(folder).actions == []

    def test_a_refusal_exits_two_and_writes_nothing(self, tmp_path):
        folder = area_with(tmp_path)
        r = run_cli("hold", "--area", folder, "confirm")
        assert r.returncode == 2
        assert "refused" in r.stderr
        assert not hold_path(folder).exists()


# --------------------------------------------------------------------------- #
# 5. The doctrine, grep-shaped — the verbs run only from a human answer
# --------------------------------------------------------------------------- #

def test_no_guard_or_agent_contract_invokes_the_verbs():
    """The narrowed rule's teeth: `edit_hold` has exactly one caller (the CLI
    dispatch), no `decide()` guard reaches it, and no agent contract names it.
    An agent that could run the verb would be a writer outside a human answer.
    """
    def code(text):
        """The file minus its comments — the doctrine is about what RUNS."""
        return "\n".join(ln.split("#", 1)[0] for ln in text.splitlines())

    src = (SCRIPTS / "orchestrate.py").read_text(encoding="utf-8")
    body = src.split("def decide(", 1)[1].split("\ndef _write_json", 1)[0]
    assert "edit_hold" not in code(body)
    for path in sorted(SCRIPTS.glob("*.py")):
        if path.name == "orchestrate.py":
            continue
        assert "edit_hold" not in code(path.read_text(encoding="utf-8")), \
            path.name
    for path in sorted((REPO / "agents").rglob("*.md")):
        low = path.read_text(encoding="utf-8").lower()
        assert "release-hold" not in low, path.name
        assert "orchestrate.py hold" not in low, path.name


def test_the_two_vocabularies_stay_disjoint():
    """The verbs do not widen what is holdable: the hold vocabulary is still
    the non-gate half of the ladder."""
    assert not (set(orchestrate.HOLDABLE_ACTIONS)
                & set(orchestrate.GATE_ACTIONS))


def test_the_confirm_gate_names_the_verb(tmp_path):
    from test_ask_loop_m75 import ipo_copy
    root, area = ipo_copy(tmp_path)
    (area / "_reference" / ".proposed").mkdir(parents=True, exist_ok=True)
    (area / "_reference" / ".proposed" / "procedures.yaml").write_text(
        "procedures: []\n", encoding="utf-8")
    ask_first = orchestrate.decide(str(area))["details"]["answers"][1]
    assert "orchestrate.py hold --area" in ask_first["human_action"]
    assert "release-hold" in ask_first["human_action"]


# --------------------------------------------------------------------------- #
# 6. Part F — damage is not done
# --------------------------------------------------------------------------- #

from test_central_mode_m68 import make_engagement, make_v1_area  # noqa: E402


class TestMarkerGap:
    def test_a_wiped_engagement_is_unresolvable_not_done(self, tmp_path):
        root = make_engagement(tmp_path, manifests=False)
        area = str(root / "components" / "p2p")
        assert orchestrate.decide(area)["action"] == "done"
        (root / "_sources" / "sources.yaml").unlink()
        d = orchestrate.decide(area)
        assert d["action"] == "unresolvable"
        assert d["human_gate"] is True
        assert d["details"]["state"] == "central marker missing"
        assert "sources.yaml" in d["details"]["why_no_stage"]
        assert "restore" in d["details"]["human_action"]
        assert d["details"]["would_have_been"].startswith("done: ")

    def test_a_finished_engagement_still_says_done(self, tmp_path):
        root = make_engagement(tmp_path, manifests=False)
        assert orchestrate.decide(
            str(root / "components" / "p2p"))["action"] == "done"

    def test_a_v1_area_with_its_own_sources_is_untouched(self, tmp_path):
        """The conjunction, not the disjunction: a v1 area owns a markerless
        `_sources/` and must never read as a wiped engagement."""
        area = make_v1_area(tmp_path)
        assert (area / "_sources").is_dir()
        assert orchestrate._marker_gap(str(area)) is None
        assert orchestrate.decide(str(area))["details"].get("state") != \
            "central marker missing"

    def test_the_p2p_complete_fixture_is_the_named_negative(self):
        """tests/fixtures/p2p-complete/components/procure-to-pay — a real v1
        area with its own markerless `_sources/`. Only the components-sibling
        requirement at the SAME ancestor keeps it out."""
        area = REPO / "tests" / "fixtures" / "p2p-complete" / "components" \
            / "procure-to-pay"
        assert (area / "_sources").is_dir()
        assert not (area / "_sources" / "sources.yaml").exists()
        assert orchestrate._marker_gap(str(area)) is None

    def test_the_check_is_read_only(self, tmp_path):
        root = make_engagement(tmp_path, manifests=False)
        (root / "_sources" / "sources.yaml").unlink()
        area = root / "components" / "p2p"
        before = sorted(p.relative_to(root) for p in root.rglob("*"))
        orchestrate.decide(str(area))
        assert sorted(p.relative_to(root) for p in root.rglob("*")) == before

    def test_the_walk_stops_at_the_git_root(self, tmp_path):
        """A repo root that happens to carry `_sources/` and `components/`
        above the engagement is not the engagement — and nothing above a git
        root is ever consulted."""
        outer = tmp_path / "outer"
        (outer / ".git").mkdir(parents=True)
        (outer / "_sources").mkdir()
        (outer / "components").mkdir()
        area = outer / "components" / "solo"
        (area / "_reference").mkdir(parents=True)
        # the git root IS a candidate; anything above it is not
        assert orchestrate._marker_gap(str(area)) == str(outer.resolve())
        above = tmp_path / "outer" / "components" / "solo"
        (outer / "_sources" / "sources.yaml").write_text("sources: []\n",
                                                         encoding="utf-8")
        assert orchestrate._marker_gap(str(above)) is None


def test_the_action_name_vocabulary_did_not_grow():
    """No new action name: the marker gap routes to the EXISTING gate."""
    assert "central marker missing" not in orchestrate.GATE_ACTIONS
    assert "unresolvable" in orchestrate.GATE_ACTIONS
