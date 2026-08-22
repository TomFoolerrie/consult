"""M65 — the confirm gate must consume the survey, not destroy it.

`--confirm` ends by removing `_reference/.proposed/` wholesale, and the
taxonomist stages its node fragments INSIDE that tree. These tests pin the
fix: confirm promotes the staged nodes itself (late, after the last raise
site), refuses early and whole on a live collision, reports what it did, and
prints a clean `error:` line through the CLI instead of a traceback. The
standalone `--promote-taxonomy` verb is unchanged and pinned as it stands.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import orchestrate
import scaffold

REPO = Path(__file__).resolve().parent.parent
SCAFFOLD = REPO / "scripts" / "scaffold.py"

NODE_A = """\
# Cash Management

## Scope
Bank reconciliations, sweeps and the daily cash position.
"""
NODE_B = """\
# Payments

## Scope
Outbound payment runs, approvals and the bank file handoff.
"""


def make_area(tmp_path, nodes=None, live_nodes=None):
    """A confirm-ready area: two proposed procedures, a systems registry, a
    notes file, and (optionally) staged and/or live taxonomy nodes."""
    area = tmp_path / "components" / "treasury"
    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True)
    (proposed / "procedures.yaml").write_text(yaml.safe_dump({
        "procedures": [
            {"slug": "cash-recon", "title": "Cash Reconciliation", "l2": "cash"},
            {"slug": "payment-run", "title": "Payment Run", "l2": "payments"},
        ]
    }), encoding="utf-8")
    (proposed / "systems.yaml").write_text(yaml.safe_dump({
        "systems": [{"slug": "sap", "name": "SAP"}]
    }), encoding="utf-8")
    (proposed / "notes.yaml").write_text(yaml.safe_dump({"notes": []}),
                                         encoding="utf-8")
    for name, body in (nodes or {}).items():
        staged = scaffold.proposed_taxonomy_dir(area)
        staged.mkdir(parents=True, exist_ok=True)
        (staged / f"{name}.md").write_text(body, encoding="utf-8")
    for name, body in (live_nodes or {}).items():
        live = scaffold.live_taxonomy_dir(area)
        live.mkdir(parents=True, exist_ok=True)
        (live / f"{name}.md").write_text(body, encoding="utf-8")

    taxonomy = tmp_path / "taxonomy.yaml"
    taxonomy.write_text(yaml.safe_dump({
        "taxonomy": {"categories": [
            {"slug": "finance", "subcategories": [{"slug": "cash"},
                                                  {"slug": "payments"}]},
        ]}
    }), encoding="utf-8")
    return area, taxonomy


def tree_bytes(root: Path) -> dict:
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


# --------------------------------------------------------------------------- #
# Part A — the confirm gate promotes the survey
# --------------------------------------------------------------------------- #

def test_confirm_promotes_staged_nodes_with_their_bytes(tmp_path, capsys):
    """The survey survives the gate: staged fragments land byte-identical in
    the live `_taxonomy/`, `.proposed/` is consumed, and confirm's own report
    names the promoted slugs."""
    area, taxonomy = make_area(tmp_path, nodes={"cash-management": NODE_A,
                                                "payments": NODE_B})
    assert scaffold.confirm(area, "finance", taxonomy, None, None) == 0

    live = scaffold.live_taxonomy_dir(area)
    assert (live / "cash-management.md").read_text(encoding="utf-8") == NODE_A
    assert (live / "payments.md").read_text(encoding="utf-8") == NODE_B
    assert not (area / "_reference" / ".proposed").exists()

    out = capsys.readouterr().out
    assert "promoted taxonomy nodes: cash-management, payments" in out


def test_confirm_without_staged_nodes_says_so(tmp_path, capsys):
    """The gate always states what happened to the survey — the silence is
    what let the loss hide."""
    area, taxonomy = make_area(tmp_path)
    assert scaffold.confirm(area, "finance", taxonomy, None, None) == 0
    assert "no staged taxonomy nodes" in capsys.readouterr().out
    assert not scaffold.live_taxonomy_dir(area).exists()


def test_confirm_refuses_whole_gate_on_live_node_collision(tmp_path):
    """A collision refuses BY NAME before anything is promoted: `.proposed/`
    (nodes, registry proposals, notes.yaml) and the live folder are
    byte-for-byte what they were."""
    live_body = "# Payments\n\nThe confirmed truth.\n"
    area, taxonomy = make_area(
        tmp_path,
        nodes={"cash-management": NODE_A, "payments": NODE_B},
        live_nodes={"payments": live_body})
    proposed = area / "_reference" / ".proposed"
    before_proposed = tree_bytes(proposed)
    before_live = tree_bytes(scaffold.live_taxonomy_dir(area))

    with pytest.raises(scaffold.ScaffoldError) as exc:
        scaffold.confirm(area, "finance", taxonomy, None, None)
    assert "payments" in str(exc.value)
    assert "cash-management" not in str(exc.value)

    assert tree_bytes(proposed) == before_proposed
    assert tree_bytes(scaffold.live_taxonomy_dir(area)) == before_live
    # Nothing else of the gate ran either: no manifest, no skeletons.
    assert not (area / "manifest.json").exists()
    assert not (area / "10_cash-recon.md").exists()
    assert not (area / "_reference" / "systems.yaml").exists()


def test_late_failure_leaves_nodes_staged(tmp_path, monkeypatch):
    """The MOVE runs after the last raise site: a confirm that dies in manifest
    validation leaves the staged set whole in `.proposed/_taxonomy/`, so the
    re-run does not collide with nodes the failed run itself moved."""
    area, taxonomy = make_area(tmp_path, nodes={"cash-management": NODE_A})
    staged = scaffold.proposed_taxonomy_dir(area)
    before = tree_bytes(staged)

    monkeypatch.setattr(scaffold.doc_model, "validate_manifest",
                        lambda manifest: ["synthetic validation failure"])
    with pytest.raises(SystemExit):
        scaffold.confirm(area, "finance", taxonomy, None, None)

    assert tree_bytes(staged) == before
    assert not scaffold.live_taxonomy_dir(area).exists()


def test_confirm_is_repeatable_after_the_collision_is_resolved(tmp_path):
    """The refusal is recoverable: delete the staged duplicate and the same
    command completes, promoting the rest."""
    area, taxonomy = make_area(
        tmp_path,
        nodes={"cash-management": NODE_A, "payments": NODE_B},
        live_nodes={"payments": "# Payments\n"})
    with pytest.raises(scaffold.ScaffoldError):
        scaffold.confirm(area, "finance", taxonomy, None, None)
    (scaffold.proposed_taxonomy_dir(area) / "payments.md").unlink()
    assert scaffold.confirm(area, "finance", taxonomy, None, None) == 0
    live = scaffold.live_taxonomy_dir(area)
    assert (live / "cash-management.md").read_text(encoding="utf-8") == NODE_A
    assert (live / "payments.md").read_text(encoding="utf-8") == "# Payments\n"


# --------------------------------------------------------------------------- #
# Part A — the refusal prints as a refusal through the CLI
# --------------------------------------------------------------------------- #

def _run_cli(*args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "scripts") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, str(SCAFFOLD), *args],
                          capture_output=True, text=True, env=env)


def test_confirm_cli_prints_error_line_not_a_traceback(tmp_path):
    """`main()` wraps the confirm path too: the ScaffoldError it can now raise
    reaches the operator as the same clean `error:` line every other verb
    prints, with a nonzero exit and no traceback."""
    area, taxonomy = make_area(tmp_path, nodes={"payments": NODE_B},
                               live_nodes={"payments": "# Payments\n"})
    proc = _run_cli("--confirm", "--area", str(area),
                    "--l1", "finance", "--taxonomy", str(taxonomy))
    assert proc.returncode != 0
    assert "Traceback" not in proc.stderr
    assert proc.stderr.strip().startswith("error: refusing to promote")
    assert "payments" in proc.stderr


def test_confirm_cli_reports_the_promotion(tmp_path):
    """The happy path through the CLI names the slugs on stdout."""
    area, taxonomy = make_area(tmp_path, nodes={"cash-management": NODE_A})
    proc = _run_cli("--confirm", "--area", str(area),
                    "--l1", "finance", "--taxonomy", str(taxonomy))
    assert proc.returncode == 0, proc.stderr
    assert "promoted taxonomy nodes: cash-management" in proc.stdout
    assert json.loads((area / "manifest.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Part B — the standalone verb is unchanged, and now covered
# --------------------------------------------------------------------------- #

def test_promote_taxonomy_cli_empty_set_reports_nothing_to_promote(tmp_path,
                                                                   capsys):
    """The graceful no-op stays: the human's go is safe to repeat, and the log
    says which case fired."""
    area, _ = make_area(tmp_path)
    assert scaffold.main(["--promote-taxonomy", "--area", str(area)]) == 0
    out = capsys.readouterr().out
    assert "nothing to promote" in out
    assert str(scaffold.proposed_taxonomy_dir(area)) in out
    assert "promoted taxonomy nodes" not in out


def test_promote_taxonomy_cli_success_reports_the_slugs(tmp_path, capsys):
    """The success line is distinct from the no-op line, and names the slugs."""
    area, _ = make_area(tmp_path, nodes={"cash-management": NODE_A,
                                         "payments": NODE_B})
    assert scaffold.main(["--promote-taxonomy", "--area", str(area)]) == 0
    out = capsys.readouterr().out
    assert "promoted taxonomy nodes: cash-management, payments" in out
    assert "nothing to promote" not in out
    # The verb touches nothing else under `.proposed/`.
    assert (area / "_reference" / ".proposed" / "procedures.yaml").is_file()


# --------------------------------------------------------------------------- #
# Part D — the pre-confirm checkpoint, flagged by the advisor
# --------------------------------------------------------------------------- #

def git_engagement(tmp_path):
    area, _ = make_area(tmp_path, nodes={"cash-management": NODE_A})
    root = tmp_path
    for cmd in (["init", "-q"], ["config", "user.email", "t@example.com"],
                ["config", "user.name", "T"]):
        subprocess.run(["git", "-C", str(root), *cmd], check=True,
                       capture_output=True)
    return root, area


def git_commit_all(root: Path):
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True,
                   capture_output=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "checkpoint"],
                   check=True, capture_output=True)


def test_advisor_flags_an_uncommitted_proposal_set_at_the_gate(tmp_path):
    """`--confirm` consumes `.proposed/`, so proposals that were never
    checkpointed are evidence that stops existing at the gate. Advisory: the
    action and the gate are unchanged."""
    _, area = git_engagement(tmp_path)
    d = orchestrate.decide(str(area))
    assert d["action"] == "confirm" and d["human_gate"] is True
    assert d["details"]["uncommitted_proposals"] is True
    assert "checkpoint" in d["details"]["checkpoint_first"].lower()


def test_advisor_stays_quiet_when_the_proposals_are_checkpointed(tmp_path):
    """A committed `.proposed/` raises nothing — the flag names a real risk,
    not a permanent decoration on the gate."""
    root, area = git_engagement(tmp_path)
    git_commit_all(root)
    d = orchestrate.decide(str(area))
    assert d["action"] == "confirm"
    assert "uncommitted_proposals" not in d.get("details", {})


def test_advisor_stays_quiet_outside_a_work_tree(tmp_path):
    """Untracked engagements already hear about it once, through `details.git`
    — the checkpoint flag would only repeat that."""
    area, _ = make_area(tmp_path, nodes={"cash-management": NODE_A})
    d = orchestrate.decide(str(area))
    assert d["action"] == "confirm"
    assert "uncommitted_proposals" not in d.get("details", {})
    assert d["details"]["git"]["tracked"] is False
