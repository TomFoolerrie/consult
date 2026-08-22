"""M67 acceptance tests — interpreter honesty.

Three pins, one theme: the engine must never report a BREAKAGE as a FACT.

  Part A — the >= 3.10 floor refuses, and the refusal can actually fire: the
  gate is the first executable block of every entry-point script, ahead of the
  first-party imports that are what die on an old interpreter.
  Part B — PyYAML missing is a refusal, not an empty result. "none (no
  engagement objective configured)" and "none — no objective-selected target
  reports a blocking need" may only ever mean their configured facts.
  Part C — the floor is written down.

Conventions: tmp_path fixtures, observable contracts, no network.
"""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import brief
import client_config
import _pyfloor

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"

# Every script under scripts/ with a `if __name__ == "__main__"` entry point,
# i.e. every file a human or an agent can invoke directly. The gate belongs in
# all of them; the list is asserted complete below, so a new entry point that
# forgets the gate fails here rather than lying on someone's 3.9 laptop.
ENTRY_POINTS = [
    "agenda", "aggregate", "analysis", "brief", "consolidate", "doc_model",
    "engagement", "gaps_ingest", "kits", "ledger", "migrate_sections",
    "needs", "orchestrate", "reconcile", "registers", "render",
    "review_apply", "review_extract", "scaffold", "scope_delta",
    "screens_ingest", "sources", "split_doc",
]

# First-party modules: anything importable out of scripts/. The helper itself
# is excluded — it is the ONE first-party import the gate is allowed to make,
# and it is 3.9-importable by contract.
FIRST_PARTY = {p.stem for p in SCRIPTS.glob("*.py")} - {"_pyfloor"}


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


# --------------------------------------------------------------------------- #
# Part A — the version gate
# --------------------------------------------------------------------------- #

class TestVersionGateHelper:
    def test_old_interpreter_exits_nonzero(self, capsys):
        with pytest.raises(SystemExit) as exc:
            _pyfloor.require(version_info=(3, 9, 6))
        assert exc.value.code != 0

    def test_message_names_interpreter_floor_and_fix(self, capsys):
        with pytest.raises(SystemExit):
            _pyfloor.require(version_info=(3, 9, 6),
                             executable="/usr/bin/python3",
                             script="scripts/brief.py")
        err = capsys.readouterr().err
        assert "3.9.6" in err                 # the running interpreter
        assert "/usr/bin/python3" in err      # ... and which one it is
        assert "3.10" in err                  # the floor
        assert "python3.12" in err            # the fix, as a command
        assert "scripts/brief.py" in err

    def test_healthy_interpreter_is_silent_and_returns(self, capsys):
        assert _pyfloor.require(version_info=(3, 12, 1)) is None
        assert _pyfloor.require() is None     # the real one, running us now
        assert capsys.readouterr().err == ""

    def test_floor_boundary_is_inclusive(self):
        assert _pyfloor.require(version_info=(3, 10, 0)) is None
        with pytest.raises(SystemExit):
            _pyfloor.require(version_info=(3, 9, 18))

    def test_helper_is_importable_on_an_old_interpreter(self):
        """The module that reports the floor may not trip over it: stdlib
        only, and no 3.10-dependent construct anywhere."""
        tree = ast.parse((SCRIPTS / "_pyfloor.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            # `X | Y` in an annotation is the exact 3.9 TypeError this ticket
            # exists for; `match` is the other 3.10-only construct.
            assert not isinstance(node, getattr(ast, "Match", ()))
            if isinstance(node, (ast.AnnAssign, ast.arg)) and node.annotation:
                assert not isinstance(node.annotation, ast.BinOp)
            if isinstance(node, ast.FunctionDef):
                assert node.returns is None or not isinstance(
                    node.returns, ast.BinOp)
        assert imported <= {"sys"}, imported


class TestGateInEveryEntryPoint:
    def test_entry_point_list_is_complete(self):
        found = sorted(
            p.stem for p in SCRIPTS.glob("*.py")
            if 'if __name__ == "__main__"' in p.read_text(encoding="utf-8"))
        assert found == sorted(ENTRY_POINTS)

    @pytest.mark.parametrize("name", ENTRY_POINTS)
    def test_gate_runs_before_any_first_party_import(self, name):
        path = SCRIPTS / f"{name}.py"
        src = path.read_text(encoding="utf-8")
        lines = src.splitlines()
        gate = [i + 1 for i, ln in enumerate(lines)
                if ln.strip() == "_pyfloor.require()"]
        assert gate, f"{name}.py carries no interpreter gate"
        gate_line = gate[0]

        tree = ast.parse(src)
        first_party_lines = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            else:
                continue
            if any(n in FIRST_PARTY for n in names):
                first_party_lines.append(node.lineno)
        assert first_party_lines, f"{name}.py imports nothing first-party?"
        assert gate_line < min(first_party_lines), (
            f"{name}.py runs a first-party import at line "
            f"{min(first_party_lines)} before the gate at {gate_line} — the "
            f"gate would never fire on a 3.9 interpreter")

    @pytest.mark.parametrize("name", ["brief", "orchestrate", "scaffold"])
    def test_gate_does_not_fire_on_a_healthy_interpreter(self, name):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / f"{name}.py"), "--help"],
            capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        assert "requires Python" not in proc.stderr

    def test_importing_an_entry_point_does_not_exit(self):
        """The suite imports these modules directly — the gate must be inert
        under a healthy interpreter, not merely quiet."""
        import importlib
        for name in ENTRY_POINTS:
            importlib.import_module(name)


# --------------------------------------------------------------------------- #
# Part B — a missing dependency is a refusal, not an empty result
# --------------------------------------------------------------------------- #

FALSE_OBJECTIVE_LINE = "no engagement objective configured"
FALSE_NEEDS_LINE = "no objective-selected target reports a blocking need"


@pytest.fixture
def no_pyyaml(monkeypatch):
    monkeypatch.setattr(client_config, "yaml", None)
    monkeypatch.setattr(brief, "yaml", None)


class TestPyYAMLAbsentRefuses:
    def test_read_yaml_raises_naming_pyyaml(self, tmp_path, no_pyyaml):
        p = tmp_path / "objective.yaml"
        p.write_text("objective: {}\n", encoding="utf-8")
        with pytest.raises(client_config.MissingDependencyError) as exc:
            client_config._read_yaml(p)
        assert "PyYAML" in str(exc.value)
        assert sys.executable in str(exc.value)

    def test_missing_dependency_is_a_client_config_error(self):
        assert issubclass(client_config.MissingDependencyError,
                          client_config.ClientConfigError)

    def test_load_refuses_rather_than_returning_empty(self, tmp_path,
                                                      no_pyyaml):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(client_config.MissingDependencyError):
            client_config.load(area)

    def test_objective_accessor_refuses(self, tmp_path, no_pyyaml):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(client_config.MissingDependencyError) as exc:
            client_config.objective(area)
        assert "PyYAML" in str(exc.value)

    def test_report_line_refuses(self, tmp_path, no_pyyaml):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(client_config.MissingDependencyError):
            client_config.report_line(area)

    def test_objective_block_refuses_and_never_prints_the_false_line(
            self, tmp_path, no_pyyaml):
        root, area = ipo_copy(tmp_path)
        with pytest.raises(client_config.MissingDependencyError) as exc:
            brief.objective_block(area)
        assert FALSE_OBJECTIVE_LINE not in str(exc.value)

    def test_brief_objective_cli_refuses_loudly(self, tmp_path, no_pyyaml,
                                                capsys):
        root, area = ipo_copy(tmp_path)
        rc = brief.main([str(area), "--objective"])
        cap = capsys.readouterr()
        assert rc != 0
        assert "PyYAML" in cap.err
        assert FALSE_OBJECTIVE_LINE not in cap.out + cap.err

    def test_needs_section_refuses_instead_of_claiming_a_clean_state(
            self, tmp_path, no_pyyaml):
        root, area = ipo_copy(tmp_path)
        out = []
        brief._needs_section(out, area)
        text = "\n".join(out)
        assert FALSE_NEEDS_LINE not in text
        assert "UNREADABLE" in text
        assert "PyYAML" in text

    def test_sources_entries_refuses_when_the_file_exists(self, tmp_path,
                                                          no_pyyaml):
        folder = tmp_path / "purchasing"
        (folder / "_reference").mkdir(parents=True)
        (folder / "_reference" / "sources.yaml").write_text(
            "sources: []\n", encoding="utf-8")
        with pytest.raises(client_config.MissingDependencyError) as exc:
            brief._sources_entries(folder)
        assert "PyYAML" in str(exc.value)

    def test_absent_sources_file_still_reads_as_absent(self, tmp_path,
                                                       no_pyyaml):
        """The soft path that stays soft: no file is honestly no entries —
        the refusal is about a file the parser cannot read, not about one
        nobody wrote."""
        folder = tmp_path / "purchasing"
        folder.mkdir()
        assert brief._sources_entries(folder) == []


class TestHealthyInterpreterUnchanged:
    def test_absent_objective_still_says_none(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        block = brief.objective_block(area)
        assert f"objective: none ({FALSE_OBJECTIVE_LINE})" in block

    def test_no_needs_still_says_none(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        out = []
        brief._needs_section(out, area)
        assert f"  none — {FALSE_NEEDS_LINE}" in "\n".join(out)

    def test_malformed_yaml_still_names_the_file(self, tmp_path):
        p = tmp_path / "objective.yaml"
        p.write_text("objective: [unclosed\n", encoding="utf-8")
        with pytest.raises(client_config.ClientConfigError) as exc:
            client_config._read_yaml(p)
        assert "objective.yaml" in str(exc.value)
        assert "PyYAML" not in str(exc.value)


# --------------------------------------------------------------------------- #
# Part C — the floor is written down
# --------------------------------------------------------------------------- #

class TestFloorDocumented:
    def test_requirements_txt_states_the_floor(self):
        text = (REPO / "requirements.txt").read_text(encoding="utf-8")
        assert "# Requires Python >= 3.10" in text

    def test_readme_states_the_floor(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        assert "Python >= 3.10" in text
