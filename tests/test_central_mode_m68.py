"""M68 acceptance tests — central mode finishes the move.

Four v1 assumptions that survived M34/M37, one root cause: the detection seam
was wired into the loaders, and these consumers never got the memo.

Part A — brief and agenda resolve a ledger `file` at the ENGAGEMENT ROOT.
Part B — a central-mode checkpoint commits the engagement state the stage
         mutated, not the area alone.
Part C — the ladder routes before it scopes (central mode only).
Part D — mark-processed reports what actually happened.

Every fixture lives under tmp_path; the v1 halves pin that nothing moved.
"""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

import agenda
import brief
import orchestrate
import sources


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

PROC_SLUGS = {"p2p": ["receive-invoice"], "r2r": ["accrue-ap"]}


def _manifest(area_name: str, slugs: list[str]) -> dict:
    return {
        "schema": "consult-mvp-manifest/v1",
        "area": area_name, "l1": area_name.upper(), "title": area_name.upper(),
        "l2_order": ["main"],
        "components": [
            {"file": f"10_{s}.md", "heading": s, "order": i + 10,
             "role": "procedure", "slug": s, "l2": "main"}
            for i, s in enumerate(slugs)
        ],
    }


def make_engagement(tmp_path: Path, areas=("p2p",), manifests=True) -> Path:
    """A central-mode engagement: a real ledger file (the mode marker), a
    staging folder, and one or more scoped areas."""
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": []}), encoding="utf-8")
    for name in areas:
        area = root / "components" / name
        (area / "_review" / "processed").mkdir(parents=True)
        slugs = PROC_SLUGS.get(name, ["step-one"])
        if manifests:
            (area / "manifest.json").write_text(
                json.dumps(_manifest(name, slugs)), encoding="utf-8")
            for slug in slugs:
                (area / f"10_{slug}.md").write_text(
                    f"## {slug}\n\ndrafted text\n", encoding="utf-8")
    return root


def stage(root: Path, name: str, text: str = "interview transcript\n") -> Path:
    f = root / "_sources" / "new" / name
    f.write_text(text, encoding="utf-8")
    return f


def make_v1_area(tmp_path: Path) -> Path:
    """An area that owns its own registry and `_sources/` tree — no engagement
    ledger anywhere above it."""
    area = tmp_path / "solo" / "components" / "ap"
    (area / "_reference").mkdir(parents=True)
    (area / "_sources").mkdir()
    (area / "manifest.json").write_text(
        json.dumps(_manifest("ap", ["bank-rec"])), encoding="utf-8")
    (area / "10_bank-rec.md").write_text("## bank-rec\n\ndrafted\n",
                                         encoding="utf-8")
    (area / "_sources" / "int1.md").write_text("interview\n", encoding="utf-8")
    (area / "_reference" / "sources.yaml").write_text(yaml.safe_dump({
        "sources": [{"id": "SRC-001", "file": "_sources/int1.md",
                     "touches": ["bank-rec"], "consumed": []}]}),
        encoding="utf-8")
    return area


def git(cwd: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=False)


@pytest.fixture
def repo(tmp_path):
    """A git work tree whose root sits ABOVE the engagement root — the layout
    the widened pathspec has to survive."""
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    (r / "README.md").write_text("host repo\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    return r


def committed_files(repo_root: Path) -> set[str]:
    out = git(repo_root, "show", "--name-only", "--pretty=format:", "HEAD")
    return {ln.strip() for ln in out.stdout.splitlines() if ln.strip()}


# --------------------------------------------------------------------------- #
# Part A — the brief resolves ledger paths at the root
# --------------------------------------------------------------------------- #

def test_central_brief_resolves_every_tagged_source(tmp_path, capsys):
    """F4: the entry's `file` is engagement-root-relative, so joining it to the
    area folder named a path that never exists. Every tagged source resolves."""
    root = make_engagement(tmp_path)
    stage(root, "int1.md")
    import ledger
    ledger.register(root, "int1.md", {"p2p": ["receive-invoice"]})

    area = root / "components" / "p2p"
    assert brief.main([str(area), "--slug", "receive-invoice"]) == 0
    out = capsys.readouterr().out

    src_lines = [ln for ln in out.splitlines() if "SRC-001" in ln]
    assert len(src_lines) == 1
    line = src_lines[0]
    assert "MISSING" not in line
    assert str(root / "_sources" / "new" / "int1.md") in line


def test_central_brief_still_marks_a_genuinely_absent_source(tmp_path, capsys):
    """The mark goes back to MEANING missing: delete the staged bytes and the
    same line flags again."""
    root = make_engagement(tmp_path)
    stage(root, "int1.md")
    import ledger
    ledger.register(root, "int1.md", {"p2p": ["receive-invoice"]})
    (root / "_sources" / "new" / "int1.md").unlink()

    area = root / "components" / "p2p"
    assert brief.main([str(area), "--slug", "receive-invoice"]) == 0
    out = capsys.readouterr().out
    src_line = next(ln for ln in out.splitlines() if "SRC-001" in ln)
    assert "MISSING — report it, do not guess" in src_line


def test_v1_reading_list_line_is_byte_identical(tmp_path, capsys):
    """The v1 half of Part A: an area-local entry still resolves against the
    AREA, and the printed line is unchanged, character for character."""
    area = make_v1_area(tmp_path)
    assert brief.main([str(area), "--slug", "bank-rec"]) == 0
    out = capsys.readouterr().out
    expected = f"  - {area / '_sources' / 'int1.md'}  (SRC-001, tagged to you)"
    assert expected in out.splitlines()


def test_central_agenda_renders_a_resolvable_source_path(tmp_path):
    """agenda's ask-list rendered the same root-relative path bare — a client
    following it landed nowhere."""
    root = make_engagement(tmp_path)
    stage(root, "int1.md")
    import ledger
    ledger.register(root, "int1.md", {"p2p": ["receive-invoice"]})

    area = root / "components" / "p2p"
    owed = agenda._owed(area, {"entities": {"receive-invoice"}})
    assert len(owed) == 1
    assert Path(owed[0]["file"]).is_file()
    assert Path(owed[0]["file"]) == root / "_sources" / "new" / "int1.md"


# --------------------------------------------------------------------------- #
# Part B — the checkpoint covers what the stage mutated
# --------------------------------------------------------------------------- #

def test_central_checkpoint_commits_engagement_state(tmp_path, repo):
    """F5: the run's most valuable state is OUTSIDE the area. A stage mutation
    in the ledger and in the shared client layer is committed WITH the area."""
    root = make_engagement(repo / "eng")
    (root / "components" / "_client").mkdir(parents=True, exist_ok=True)
    area = root / "components" / "p2p"

    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "engagement in")

    # a stage mutates all three places
    (area / "10_receive-invoice.md").write_text("## receive-invoice\n\nnew\n",
                                                encoding="utf-8")
    stage(root, "int1.md")
    (root / "_sources" / "sources.yaml").write_text(yaml.safe_dump(
        {"sources": [{"id": "SRC-001", "file": "_sources/new/int1.md",
                      "hash": "abc", "touches": {"p2p": []},
                      "consumed": {}}]}), encoding="utf-8")
    (root / "components" / "_client" / "org-chart.yaml").write_text(
        "people: []\n", encoding="utf-8")

    res = orchestrate.checkpoint(str(area), "taxonomy")
    assert res["committed"] is True

    files = committed_files(repo)
    assert "eng/engagement/components/p2p/10_receive-invoice.md" in files
    assert "eng/engagement/_sources/sources.yaml" in files
    assert "eng/engagement/_sources/new/int1.md" in files
    assert "eng/engagement/components/_client/org-chart.yaml" in files


def test_central_checkpoint_seeds_the_engagement_gitignore_once(tmp_path, repo):
    root = make_engagement(repo / "eng")
    area = root / "components" / "p2p"
    gi = root / ".gitignore"
    assert not gi.exists()

    orchestrate.checkpoint(str(area), "taxonomy")
    assert gi.is_file()
    assert ".DS_Store" in gi.read_text(encoding="utf-8")

    gi.write_text(".DS_Store\n# edited by hand\n", encoding="utf-8")
    (area / "10_receive-invoice.md").write_text("## x\n\nagain\n",
                                                encoding="utf-8")
    orchestrate.checkpoint(str(area), "fill")
    assert "# edited by hand" in gi.read_text(encoding="utf-8")


def test_v1_checkpoint_does_not_sweep_work_outside_the_area(tmp_path, repo):
    """The v1 half of Part B: still an area pathspec, still nothing else."""
    area = make_v1_area(repo)
    outside = repo / "solo" / "notes.md"
    outside.write_text("unrelated work\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "v1 in")

    (area / "10_bank-rec.md").write_text("## bank-rec\n\nedited\n",
                                         encoding="utf-8")
    outside.write_text("unrelated work, edited\n", encoding="utf-8")

    res = orchestrate.checkpoint(str(area), "fill")
    assert res["committed"] is True
    files = committed_files(repo)
    assert "solo/components/ap/10_bank-rec.md" in files
    assert "solo/notes.md" not in files


# --------------------------------------------------------------------------- #
# Part C — the ladder routes before it scopes
# --------------------------------------------------------------------------- #

def test_central_unrouted_sources_route_before_they_scope(tmp_path):
    """F2: a scoping dispatch never again runs against an empty ledger while
    sources sit staged. One area, so the instruction can name the target."""
    root = make_engagement(tmp_path, areas=("p2p",), manifests=False)
    stage(root, "int1.md")
    stage(root, "int2.md")

    d = orchestrate.decide(str(root / "components" / "p2p"))
    assert d["action"] == "route"
    assert d["human_gate"] is False
    assert d["details"]["target_area"] == "p2p"
    assert d["details"]["unrouted"] == ["_sources/new/int1.md",
                                        "_sources/new/int2.md"]
    assert len(d["details"]["commands"]) == 2
    assert "engagement.py\" route" in d["details"]["commands"][0]
    assert d["details"]["commands"][0].endswith("--to p2p")


def test_central_multi_area_unrouted_sources_are_a_human_gate(tmp_path):
    """Which area a source informs is a classification decision, never a
    default — so with siblings present the advisor stops."""
    root = make_engagement(tmp_path, areas=("p2p", "r2r"), manifests=False)
    stage(root, "int1.md")

    d = orchestrate.decide(str(root / "components" / "p2p"))
    assert d["action"] == "route"
    assert d["human_gate"] is True
    assert d["details"]["areas"] == ["p2p", "r2r"]
    assert d["details"]["unrouted"] == ["_sources/new/int1.md"]
    assert "--to <area>" in d["details"]["command_shape"]
    assert "target_area" not in d["details"]


def test_central_routed_sources_still_dispatch_taxonomy(tmp_path):
    """The other side: once the ledger knows the file, guard 3 behaves exactly
    as it did — `taxonomy`, mode initial."""
    root = make_engagement(tmp_path, areas=("p2p",), manifests=True)
    stage(root, "int1.md")
    import ledger
    ledger.register(root, "int1.md", {"p2p": []})
    (root / "components" / "p2p" / "manifest.json").unlink()

    d = orchestrate.decide(str(root / "components" / "p2p"))
    assert d["action"] == "taxonomy"
    assert d["details"]["mode"] == "initial"


def test_v1_unregistered_source_is_still_taxonomy_work(tmp_path):
    """The doctrine Part C deliberately does NOT overturn (the guard keys off
    the central seam), pinned here beside its central-mode counterpart."""
    area = make_v1_area(tmp_path)
    (area / "manifest.json").unlink()
    (area / "_sources" / "new").mkdir(parents=True)
    (area / "_sources" / "new" / "june.md").write_text("notes\n",
                                                       encoding="utf-8")

    d = orchestrate.decide(str(area))
    assert d["action"] == "taxonomy"
    assert d["details"]["mode"] == "initial"


# --------------------------------------------------------------------------- #
# Part D — the messages audit clean
# --------------------------------------------------------------------------- #

def test_mark_processed_reports_credits_when_nothing_moved(tmp_path, capsys):
    """F6: slugs were credited but no source is fully consumed yet — "moved 0"
    read as failure. The message now says what happened."""
    root = make_engagement(tmp_path, areas=("p2p", "r2r"))
    stage(root, "int1.md")
    import ledger
    ledger.register(root, "int1.md",
                    {"p2p": ["receive-invoice"], "r2r": ["accrue-ap"]})

    area = root / "components" / "p2p"
    assert sources.mark_processed(str(area), {"receive-invoice"}) == 0
    out = capsys.readouterr().out.strip()
    assert out == ("credited 1 slug(s) across 1 source(s); 0 fully consumed "
                   "and moved (ledger: p2p)")
    # the file has NOT moved — r2r still owes a read
    assert (root / "_sources" / "new" / "int1.md").is_file()


def test_mark_processed_counts_the_move_when_the_last_area_credits(
        tmp_path, capsys):
    root = make_engagement(tmp_path, areas=("p2p",))
    stage(root, "int1.md")
    import ledger
    ledger.register(root, "int1.md", {"p2p": ["receive-invoice"]})

    area = root / "components" / "p2p"
    assert sources.mark_processed(str(area), {"receive-invoice"}) == 0
    out = capsys.readouterr().out.strip()
    assert out == ("credited 1 slug(s) across 1 source(s); 1 fully consumed "
                   "and moved (ledger: p2p)")
    # M56: retired bytes land at the ID-QUALIFIED path
    assert (root / "_sources" / "processed" / "SRC-001--int1.md").is_file()
