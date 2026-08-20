"""M52 acceptance tests — written BEFORE the build.

Pins: the one assembled taxonomist work order (`brief.py taxonomist
<area> --kind ...`) — objective + coverage + needs/grooming feeds + the
write boundary, with a DISPATCH KIND line selecting emphasis and never
content; the dispatch surface (orchestrate routing, the skill, the
contract) pointing every kind at the one command; read-only; the
one-area curation call rendering instead of demanding a second area.

THE DESIGN RULE THE CONTENT PIN ENCODES: every kind-dependent line the
builder emits carries the token "KIND" (uppercase), so two kinds' briefs
are provably the same engagement picture once those lines are dropped.

Everything skips until brief.py grows the `taxonomist` verb.
"""

import shutil
from pathlib import Path

import pytest

import gatecheck

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"
CONTRACT = REPO / "agents" / "consult-taxonomist.md"
BRIEF_SRC = REPO / "scripts" / "brief.py"

KINDS = ("SCOPING", "CURATION", "ADOPT-ROUTE")

needs_verb = gatecheck.landed(
    "taxonomist" not in BRIEF_SRC.read_text(encoding="utf-8"),
    reason="M52 taxonomist brief verb not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def write_objective(area):
    cdir = area / "_client"
    cdir.mkdir(exist_ok=True)
    (cdir / "objective.yaml").write_text(
        "objective:\n"
        "  goal: Deliver a controls matrix.\n"
        "  deliverables: [process-controls-matrix]\n"
        "  cycles: [procure-to-pay]\n", encoding="utf-8")


def run_brief(capsys, area, kind):
    import brief
    code = brief.main(["taxonomist", str(area), "--kind", kind])
    out = capsys.readouterr().out
    return code, out


@needs_verb
class TestTheMergedBrief:
    def test_prints_the_merged_work_order(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        code, out = run_brief(capsys, area, "SCOPING")
        assert code == 0
        low = out.lower()
        assert "controls matrix" in low            # the objective block
        assert "coverage" in low                   # the survey feed
        assert "needs" in low or "groom" in low    # the curation feeds
        assert ".proposed/_taxonomy" in out        # the write boundary...
        assert "never" in low and "delete" in low  # ...said once, plainly
        assert "KIND" in out                       # the dispatch-kind line

    def test_every_kind_renders(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        for kind in KINDS:
            code, out = run_brief(capsys, area, kind)
            assert code == 0 and kind in out, kind

    def test_kind_selects_emphasis_never_content(self, tmp_path, capsys):
        # drop every line carrying the KIND token: what remains — the
        # engagement picture — must be identical across kinds
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        pictures = []
        for kind in KINDS:
            _, out = run_brief(capsys, area, kind)
            pictures.append("\n".join(
                ln for ln in out.splitlines() if "KIND" not in ln))
        assert pictures[0] == pictures[1] == pictures[2]

    def test_one_area_curation_still_renders(self, tmp_path, capsys):
        # the old placement brief demanded two areas; grooming an existing
        # population is engagement-scoped and needs no second area
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        code, out = run_brief(capsys, area, "CURATION")
        assert code == 0 and out.strip()

    def test_unknown_area_refuses_by_name(self, tmp_path, capsys):
        import brief
        with pytest.raises(SystemExit) as exc:
            brief.main(["taxonomist", str(tmp_path / "no-such-area"),
                        "--kind", "CURATION"])
        assert exc.value.code not in (0, None)

    def test_read_only(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        before = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                  for p in root.rglob("*") if p.is_file()}
        run_brief(capsys, area, "SCOPING")
        run_brief(capsys, area, "CURATION")
        after = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                 for p in root.rglob("*") if p.is_file()}
        assert before == after


@needs_verb
class TestOneAssemblySite:
    def test_orchestrate_routes_both_modes_to_the_verb(self):
        src = (REPO / "scripts" / "orchestrate.py").read_text(encoding="utf-8")
        start = src.index("_CENTRAL_TAXONOMY_BRIEFS")
        block = src[start:start + 800]
        assert "taxonomist" in block

    def test_skill_names_the_one_command(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "brief.py" in low and "taxonomist" in low
        # the M48 tier hints survive beside the new command
        assert "curation" in low and "scoping" in low

    def test_contract_names_the_brief_first(self):
        low = CONTRACT.read_text(encoding="utf-8").lower()
        assert "brief.py" in low and "taxonomist" in low
