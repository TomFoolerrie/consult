"""M73 — run-2 paper cuts: stale contracts and undisclosed sweeps.

Four independent cuts, one gate each:

  A. `agents/consult-taxonomist.md` teaches the M65 truth — `--confirm` is ONE
     verb and promotes the staged nodes itself; `--promote-taxonomy` survives
     only as a hand-flow footnote. Grep-shaped: no two-verb sequence
     instruction remains, and the return section names no promotion command.
  B. The skill's checkpoint duty discloses what the FIRST checkpoint of a
     session is about to sweep — plus the read-only engine seam that hands the
     orchestrator the pathspecs it cannot compute itself (`checkpoint
     --dry-run`).
  C. Guard 0's missing-folder error states BOTH readings: committed content
     under the path → today's typo-shaped message; no committed content →
     fresh-area-shaped. Both keep "does not exist", both stay `error`, both
     exit nonzero; a non-git tree degrades to today's message.
  D. The draft-ready gate's details carry the check-23 (register blanks)
     warning count — additive, the answers list and `would_spend` untouched.
"""
import json
import os
import re
import subprocess
from pathlib import Path

import orchestrate

ROOT = Path(__file__).resolve().parents[1]
TAXONOMIST = ROOT / "agents" / "consult-taxonomist.md"
SKILL = ROOT / "skills" / "consult-orchestrate" / "SKILL.md"


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


# --------------------------------------------------------------------------- #
# A — the taxonomist contract catches up to M65
# --------------------------------------------------------------------------- #

#: A two-verb sequence instruction: the two flags paired on one line by a
#: separator that reads as "run both".
TWO_VERB = re.compile(
    r"--confirm\b[^\n]{0,40}?(?:/|,| and | then | plus )[^\n]{0,40}?"
    r"--promote-taxonomy"
    r"|--promote-taxonomy\b[^\n]{0,40}?(?:/|,| and | then | plus )"
    r"[^\n]{0,40}?--confirm")


def test_no_two_verb_sequence_instruction_survives():
    text = TAXONOMIST.read_text(encoding="utf-8")
    assert TWO_VERB.findall(text) == []


def test_every_promote_taxonomy_mention_is_the_hand_flow_footnote():
    """`--promote-taxonomy` may still be named — but only as the hand flow it
    is post-M65, never as the move the loop makes."""
    for para in paragraphs(TAXONOMIST.read_text(encoding="utf-8")):
        if "--promote-taxonomy" in para:
            assert "hand flow" in para.lower(), para


def test_confirm_is_named_as_the_one_verb_that_promotes_nodes():
    text = TAXONOMIST.read_text(encoding="utf-8")
    assert re.search(r"`scaffold\.py --confirm[^`]*`[^\n]*", text)
    low = text.lower()
    assert "one verb" in low
    # the M65 fact stated, not implied
    assert "m65" in low


def test_the_return_section_names_no_promotion_command():
    """The return-instructions section relays the gate; it does not tell the
    orchestrator to run a promotion verb."""
    text = TAXONOMIST.read_text(encoding="utf-8")
    tail = text[text.index("## What you return"):]
    assert "--promote-taxonomy" not in tail
    assert "promotion move" not in tail


def test_taxonomist_contract_stays_clear_of_the_banned_phrase():
    """The M43 hygiene grep (test_hygiene_m43.py) still passes over the file."""
    text = TAXONOMIST.read_text(encoding="utf-8").lower()
    assert "does not exist yet" not in text
    assert "hygiene" in text


# --------------------------------------------------------------------------- #
# B — the first checkpoint discloses what it sweeps
# --------------------------------------------------------------------------- #

def test_skill_checkpoint_duty_carries_the_first_checkpoint_disclosure():
    text = SKILL.read_text(encoding="utf-8")
    # markdown emphasis and hard wraps are cosmetic; the duty is the words
    flat = re.sub(r"[\s*]+", " ", text).lower()
    assert "--dry-run" in flat
    assert "first checkpoint of a session" in flat
    assert "pre-existing" in flat
    assert "before you run the real checkpoint" in flat


def git_area(tmp_path, name="cash"):
    root = tmp_path / "eng"
    folder = root / "components" / name
    folder.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for cfg in (("user.email", "t@example.com"), ("user.name", "T")):
        subprocess.run(["git", "-C", str(root), "config", *cfg], check=True)
    return root, folder


def commit_all(root, message="seed"):
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", message],
                   check=True)


def test_checkpoint_dry_run_names_the_dirty_paths_and_commits_nothing(tmp_path):
    root, folder = git_area(tmp_path)
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root)
    (folder / "10_a.md").write_text("draft\n", encoding="utf-8")

    res = orchestrate.checkpoint(str(folder), "fill", dry_run=True)
    assert res["committed"] is False
    assert res["dry_run"] is True
    assert res["pathspecs"] == ["."]
    assert any(p.endswith("10_a.md") for p in res["dirty"]), res
    # read-only: nothing staged, nothing committed, no .gitignore seeded
    assert not (folder / ".gitignore").exists()
    head = subprocess.run(["git", "-C", str(root), "log", "--oneline"],
                          capture_output=True, text=True).stdout
    assert head.count("\n") == 1
    staged = subprocess.run(["git", "-C", str(root), "diff", "--cached",
                             "--name-only"], capture_output=True, text=True)
    assert staged.stdout.strip() == ""


def test_checkpoint_dry_run_on_a_clean_tree_reports_nothing_dirty(tmp_path):
    root, folder = git_area(tmp_path)
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root)
    res = orchestrate.checkpoint(str(folder), "fill", dry_run=True)
    assert res["dirty"] == []


def test_checkpoint_dry_run_outside_git_degrades(tmp_path):
    folder = tmp_path / "loose"
    folder.mkdir()
    res = orchestrate.checkpoint(str(folder), "fill", dry_run=True)
    assert res["committed"] is False
    assert res["dirty"] == []
    assert "git work tree" in res["reason"]


def test_checkpoint_still_commits_when_not_a_dry_run(tmp_path):
    root, folder = git_area(tmp_path)
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root)
    (folder / "10_a.md").write_text("draft\n", encoding="utf-8")
    res = orchestrate.checkpoint(str(folder), "fill")
    assert res["committed"] is True


# --------------------------------------------------------------------------- #
# C — the missing-folder error states both readings
# --------------------------------------------------------------------------- #

def test_absent_folder_with_committed_content_stays_typo_shaped(tmp_path):
    root, folder = git_area(tmp_path, "treasury")
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root)
    import shutil
    shutil.rmtree(folder)

    d = orchestrate.decide(str(folder))
    assert d["action"] == "error"
    assert d["human_gate"] is False
    assert "does not exist" in d["reason"]
    assert "check the --area name" in d["reason"]
    assert "no committed content" not in d["reason"]
    assert d["details"]["missing_folder"] == str(folder)
    assert d["details"]["committed_content"] is True


def test_absent_folder_with_no_committed_content_is_fresh_area_shaped(tmp_path):
    root, folder = git_area(tmp_path, "kept")
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root)
    fresh = root / "components" / "never-scoped"

    d = orchestrate.decide(str(fresh))
    assert d["action"] == "error"
    assert d["human_gate"] is False
    assert "does not exist" in d["reason"]
    assert "no committed content under this path" in d["reason"]
    assert "create the folder and re-run" in d["reason"]
    assert d["details"]["missing_folder"] == str(fresh)
    assert d["details"]["committed_content"] is False


def test_non_git_tree_degrades_to_todays_message(tmp_path):
    d = orchestrate.decide(str(tmp_path / "no-such-area"))
    assert d["action"] == "error"
    assert "does not exist" in d["reason"]
    assert "check the --area name" in d["reason"]
    assert "no committed content" not in d["reason"]
    assert d["details"]["missing_folder"].endswith("no-such-area")
    assert "committed_content" not in d["details"]


def test_both_readings_exit_nonzero(tmp_path, capsys):
    root, folder = git_area(tmp_path, "kept")
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root)
    import shutil
    gone = root / "components" / "gone"
    gone.mkdir()
    (gone / "manifest.json").write_text("{}", encoding="utf-8")
    commit_all(root, "gone")
    shutil.rmtree(gone)

    for target in (gone, root / "components" / "never-scoped"):
        rc = orchestrate.main(["next", "--area", str(target)])
        out = json.loads(capsys.readouterr().out)
        assert rc == 2, target
        assert out["action"] == "error"
        assert "does not exist" in out["reason"]


def test_skill_error_row_recites_both_readings():
    text = SKILL.read_text(encoding="utf-8")
    row = [ln for ln in text.splitlines() if ln.startswith("| `error` |")]
    assert len(row) == 1
    low = row[0].lower()
    assert "no committed content" in low
    assert "committed_content" in row[0]


# --------------------------------------------------------------------------- #
# D — the register-blanks warning count reaches the gate
# --------------------------------------------------------------------------- #

ROLES_BLANK = ("roles:\n"
               "  - slug: controller\n    name: Controller\n"
               "  - slug: ap-clerk\n    name: AP Clerk\n")
SYSTEMS_OK = ("systems:\n  - slug: netsuite\n    name: NetSuite\n"
              "    description: The ledger of record.\n")


def gate_area(tmp_path, files):
    from test_stage_gates import make_area, proc, derived, FILLED, DEP_MARKER, \
        RACI_MARKER, walk_to_gate
    base = {"10_bank-rec.md": FILLED,
            "82_dependencies.md":
                "## Dependencies\n\n%s\n\nDepends on nothing.\n" % DEP_MARKER,
            "84_raci.md": "## Raci\n\n%s\n\nNo rows.\n" % RACI_MARKER}
    base.update(files)
    area = make_area(tmp_path, "cash",
                     [proc("bank-rec"),
                      derived("82_dependencies.md", "dependencies", 82),
                      derived("84_raci.md", "raci", 84)],
                     base)
    return area, walk_to_gate(area)


def test_gate_details_carry_the_register_warning_count(tmp_path):
    """Two roles with no `reports_to` — check 23 warns twice, and the gate
    says so before anything is paid for."""
    area, d = gate_area(tmp_path, {"_reference/roles.yaml": ROLES_BLANK,
                                   "_reference/systems.yaml": SYSTEMS_OK})
    assert d["action"] == "draft_ready"
    assert d["details"]["register_warnings"] == 2


def test_a_clean_register_reports_zero(tmp_path):
    roles = ROLES_BLANK.replace("    name: Controller\n",
                                "    name: Controller\n"
                                "    reports_to: Not applicable\n")
    roles = roles.replace("    name: AP Clerk\n",
                          "    name: AP Clerk\n    reports_to: controller\n")
    area, d = gate_area(tmp_path, {"_reference/roles.yaml": roles,
                                   "_reference/systems.yaml": SYSTEMS_OK})
    assert d["action"] == "draft_ready"
    assert d["details"]["register_warnings"] == 0


def test_the_count_is_additive_only(tmp_path):
    """The answers list and `would_spend` are pinned elsewhere; the new key
    rides beside them and changes neither."""
    area, d = gate_area(tmp_path, {"_reference/roles.yaml": ROLES_BLANK,
                                   "_reference/systems.yaml": SYSTEMS_OK})
    assert sorted(a["name"] for a in d["details"]["answers"]) == [
        "accept", "consolidate", "read"]
    assert d["details"]["would_spend"] == "synthesize"


def test_skill_draft_ready_row_names_the_count():
    text = SKILL.read_text(encoding="utf-8")
    row = [ln for ln in text.splitlines() if ln.startswith("| `draft_ready` |")]
    assert len(row) == 1
    assert "register_warnings" in row[0]
