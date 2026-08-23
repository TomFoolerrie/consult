"""M77 acceptance tests — standing tenancy, written BEFORE the build.

Pins:

  * Part A — `<area>/_taxonomy/.tenure.yaml`, the taxonomist's own working
    record, written ONLY through `scripts/flags.py` tenure subcommands
    (`tenure-add` / `tenure-supersede` / `tenure-resolve` / `tenure-list`).
    Entries typed `ruling | deferred | doubt`, state
    `standing | superseded | resolved`, a reference REQUIRED on every close,
    append-only (nothing is ever deleted; the M76 flag history pattern);
  * the verified non-collision: `scaffold.taxonomy_hashes` globs
    `_taxonomy/*.md` only, so the dot-named yaml does NOT trip the M66 node
    guard (reconcile check 15.5);
  * Part B — the taxonomist brief feeds the precedent back: standing rulings,
    open deferrals, live doubts; superseded/resolved omitted; printed only
    when the file exists, from `taxonomist_picture` so BOTH entrypoints carry
    it (the M76 flags-section precedent). Contract text: file your own
    entries, start from your own precedent, supersede knowingly;
  * Part C — the boundary: the advisor's decision over an area with a tenure
    file is byte-identical to the same area without it, and no module outside
    `brief.py` / `flags.py` names the file.

Everything is conditional on the tenure file existing, so a v1 area is
byte-identical to pre-M77.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

import brief
import flags
import orchestrate
import reconcile
import scaffold

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
CONTRACT = REPO / "agents" / "consult-taxonomist.md"

from test_stage_gates import simple, walk_to_gate  # noqa: E402
from test_capture_scaffold_m66 import (NODE_A, _manifest, make_central)  # noqa: E402


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def an_area(tmp_path, name="purchasing"):
    area = tmp_path / "components" / name
    (area / "_taxonomy").mkdir(parents=True)
    return area


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in Path(base).rglob("*") if p.is_file()}


def run_cli(*argv):
    return flags.main([str(a) for a in argv])


# --------------------------------------------------------------------------- #
# Part A — the tenure file and its verb
# --------------------------------------------------------------------------- #

class TestTenureFile:
    def test_the_file_lives_in_the_house_the_taxonomist_owns(self, tmp_path):
        area = an_area(tmp_path)
        assert flags.tenure_path(area) == area / "_taxonomy" / ".tenure.yaml"

    def test_add_mints_typed_standing_entries(self, tmp_path):
        area = an_area(tmp_path)
        tid = flags.tenure_add(area, kind="ruling",
                               text="merged the three request paths")
        assert tid == "TEN-001"
        second = flags.tenure_add(area, kind="doubt",
                                  text="catalog-maintenance L2 placement weak")
        assert second == "TEN-002"
        rows = flags.tenure_entries(area)
        assert [r["id"] for r in rows] == ["TEN-001", "TEN-002"]
        assert rows[0]["type"] == "ruling"
        assert rows[0]["state"] == "standing"
        assert rows[0]["text"] == "merged the three request paths"
        assert rows[1]["type"] == "doubt"

    def test_the_file_is_yaml_with_a_tenure_list(self, tmp_path):
        area = an_area(tmp_path)
        flags.tenure_add(area, kind="deferred", text="wait for ask F")
        data = yaml.safe_load(
            flags.tenure_path(area).read_text(encoding="utf-8"))
        assert isinstance(data["tenure"], list) and len(data["tenure"]) == 1

    def test_missing_file_is_an_empty_record_not_an_error(self, tmp_path):
        area = an_area(tmp_path)
        assert flags.tenure_entries(area) == []
        assert flags.tenure_standing(area) == []

    def test_bad_type_is_refused_loudly_and_nothing_is_written(self, tmp_path):
        area = an_area(tmp_path)
        with pytest.raises(flags.FlagsError) as exc:
            flags.tenure_add(area, kind="hunch", text="something")
        assert "hunch" in str(exc.value)
        assert not flags.tenure_path(area).is_file()

    def test_empty_text_is_refused(self, tmp_path):
        area = an_area(tmp_path)
        with pytest.raises(flags.FlagsError):
            flags.tenure_add(area, kind="ruling", text="   ")
        assert not flags.tenure_path(area).is_file()

    def test_supersede_requires_a_reference(self, tmp_path):
        area = an_area(tmp_path)
        tid = flags.tenure_add(area, kind="ruling", text="a call")
        with pytest.raises(flags.FlagsError) as exc:
            flags.tenure_supersede(area, tid, reference="")
        assert "reference" in str(exc.value).lower()
        assert flags.tenure_entries(area)[0]["state"] == "standing"

    def test_resolve_requires_a_reference(self, tmp_path):
        area = an_area(tmp_path)
        tid = flags.tenure_add(area, kind="deferred", text="a deferral")
        with pytest.raises(flags.FlagsError):
            flags.tenure_resolve(area, tid, reference=None)
        assert flags.tenure_entries(area)[0]["state"] == "standing"

    def test_supersede_links_resolve_and_the_entry_survives(self, tmp_path):
        area = an_area(tmp_path)
        old = flags.tenure_add(area, kind="ruling", text="diamond not arrow")
        new = flags.tenure_add(area, kind="ruling", text="arrow after all")
        flags.tenure_supersede(area, old, reference=new)
        rows = {r["id"]: r for r in flags.tenure_entries(area)}
        assert rows[old]["state"] == "superseded"
        assert rows[old]["reference"] == new
        assert rows[old]["text"] == "diamond not arrow"    # nothing deleted
        assert rows[new]["state"] == "standing"

    def test_resolve_records_what_settled_it(self, tmp_path):
        area = an_area(tmp_path)
        tid = flags.tenure_add(area, kind="deferred", text="wait for ask F")
        flags.tenure_resolve(area, tid, reference="ASK-006 answered")
        row = flags.tenure_entries(area)[0]
        assert row["state"] == "resolved"
        assert row["reference"] == "ASK-006 answered"

    def test_append_only_history(self, tmp_path):
        area = an_area(tmp_path)
        tid = flags.tenure_add(area, kind="doubt", text="weak placement")
        flags.tenure_resolve(area, tid, reference="evidence arrived")
        hist = flags.tenure_entries(area)[0]["history"]
        assert [h["state"] for h in hist] == ["standing", "resolved"]
        assert hist[-1]["reference"] == "evidence arrived"

    def test_a_closed_entry_is_never_re_closed(self, tmp_path):
        area = an_area(tmp_path)
        tid = flags.tenure_add(area, kind="ruling", text="a call")
        flags.tenure_supersede(area, tid, reference="TEN-009")
        with pytest.raises(flags.FlagsError) as exc:
            flags.tenure_resolve(area, tid, reference="anything")
        assert "superseded" in str(exc.value)

    def test_unknown_id_refuses_by_name(self, tmp_path):
        area = an_area(tmp_path)
        flags.tenure_add(area, kind="ruling", text="a call")
        with pytest.raises(flags.FlagsError) as exc:
            flags.tenure_supersede(area, "TEN-404", reference="TEN-001")
        assert "TEN-404" in str(exc.value)

    def test_unknown_state_filter_refuses(self, tmp_path):
        area = an_area(tmp_path)
        with pytest.raises(flags.FlagsError):
            flags.tenure_entries(area, state="pending")

    def test_malformed_file_is_fail_loud(self, tmp_path):
        area = an_area(tmp_path)
        flags.tenure_path(area).write_text("- not: a mapping\n",
                                           encoding="utf-8")
        with pytest.raises(flags.FlagsError):
            flags.tenure_entries(area)

    def test_ids_are_never_reused(self, tmp_path):
        area = an_area(tmp_path)
        a = flags.tenure_add(area, kind="ruling", text="one")
        flags.tenure_supersede(area, a, reference="superseded by hand")
        b = flags.tenure_add(area, kind="ruling", text="two")
        assert b == "TEN-002"

    def test_standing_view_drops_closed_entries(self, tmp_path):
        area = an_area(tmp_path)
        keep = flags.tenure_add(area, kind="ruling", text="standing call")
        gone = flags.tenure_add(area, kind="ruling", text="old call")
        flags.tenure_supersede(area, gone, reference=keep)
        assert [r["id"] for r in flags.tenure_standing(area)] == [keep]


class TestTenureCLI:
    def test_round_trip_through_the_verb(self, tmp_path, capsys):
        area = an_area(tmp_path)
        assert run_cli("tenure-add", "--area", area, "--type", "ruling",
                       "--text", "merged the request paths") == 0
        assert capsys.readouterr().out.strip() == "TEN-001"
        assert run_cli("tenure-add", "--area", area, "--type", "deferred",
                       "--text", "supplier split waits on ask F") == 0
        capsys.readouterr()
        assert run_cli("tenure-supersede", "--area", area, "TEN-001",
                       "--ref", "TEN-002") == 0
        capsys.readouterr()
        assert run_cli("tenure-list", "--area", area) == 0
        out = capsys.readouterr().out
        assert "TEN-001" in out and "TEN-002" in out and "superseded" in out

    def test_list_state_filter(self, tmp_path, capsys):
        area = an_area(tmp_path)
        run_cli("tenure-add", "--area", area, "--type", "doubt",
                "--text", "weak placement")
        run_cli("tenure-add", "--area", area, "--type", "ruling",
                "--text", "old call")
        run_cli("tenure-resolve", "--area", area, "TEN-002",
                "--ref", "evidence arrived")
        capsys.readouterr()
        run_cli("tenure-list", "--area", area, "--state", "standing")
        out = capsys.readouterr().out
        assert "TEN-001" in out and "TEN-002" not in out

    def test_empty_list_says_so(self, tmp_path, capsys):
        area = an_area(tmp_path)
        assert run_cli("tenure-list", "--area", area) == 0
        assert "empty" in capsys.readouterr().out.lower()

    def test_bad_type_exits_two_and_names_it(self, tmp_path, capsys):
        area = an_area(tmp_path)
        assert run_cli("tenure-add", "--area", area, "--type", "vibe",
                       "--text", "x") == 2
        assert "vibe" in capsys.readouterr().err

    def test_close_without_ref_is_an_argparse_refusal(self, tmp_path):
        area = an_area(tmp_path)
        run_cli("tenure-add", "--area", area, "--type", "ruling", "--text", "x")
        with pytest.raises(SystemExit):
            run_cli("tenure-supersede", "--area", area, "TEN-001")

    def test_the_flag_verbs_are_untouched(self, tmp_path, capsys):
        area = tmp_path / "components" / "purchasing"
        (area / "_reference").mkdir(parents=True)
        assert run_cli("add", "--area", area, "--target", "area",
                       "--origin", "consult-taxonomist/area",
                       "--text", "a flag") == 0
        assert capsys.readouterr().out.strip() == "FLAG-001"


class TestNoCollisionWithTheNodeGuard:
    def test_taxonomy_hashes_globs_md_only(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        before = scaffold.taxonomy_hashes(area)
        flags.tenure_add(area, kind="ruling", text="a standing call")
        assert flags.tenure_path(area).is_file()
        assert scaffold.taxonomy_hashes(area) == before

    def test_check_15_5_is_silent_over_a_tenure_file(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        flags.tenure_add(area, kind="doubt", text="weak placement")
        ctx = reconcile.Ctx(area, _manifest(area))
        reconcile.check_taxonomy_record(ctx)
        assert ctx.errors == []


# --------------------------------------------------------------------------- #
# Part B — the brief feeds the precedent back
# --------------------------------------------------------------------------- #

def run_brief(capsys, area, kind="CURATION"):
    capsys.readouterr()
    code = brief.main(["taxonomist", str(area), "--kind", kind])
    return code, capsys.readouterr().out


class TestBriefSection:
    def test_absent_file_leaves_the_brief_byte_identical(self, tmp_path,
                                                         capsys):
        _root, area = ipo_copy(tmp_path)
        _, baseline = run_brief(capsys, area)
        assert not flags.tenure_path(area).is_file()
        assert "TENURE" not in baseline.upper()
        _, again = run_brief(capsys, area)
        assert again == baseline

    def test_the_section_appears_when_the_file_exists(self, tmp_path, capsys):
        _root, area = ipo_copy(tmp_path)
        _, baseline = run_brief(capsys, area)
        flags.tenure_add(area, kind="ruling",
                         text="merged the three request paths")
        flags.tenure_add(area, kind="deferred",
                         text="supplier-onboarding split waits on ask F")
        flags.tenure_add(area, kind="doubt",
                         text="catalog-maintenance L2 placement is weak")
        _, out = run_brief(capsys, area)
        assert out != baseline
        assert "TENURE" in out.upper()
        assert "merged the three request paths" in out
        assert "supplier-onboarding split waits on ask F" in out
        assert "catalog-maintenance L2 placement is weak" in out

    def test_superseded_and_resolved_are_omitted(self, tmp_path, capsys):
        _root, area = ipo_copy(tmp_path)
        keep = flags.tenure_add(area, kind="ruling", text="the standing call")
        old = flags.tenure_add(area, kind="ruling", text="the old call")
        settled = flags.tenure_add(area, kind="deferred",
                                   text="the settled deferral")
        flags.tenure_supersede(area, old, reference=keep)
        flags.tenure_resolve(area, settled, reference="ASK-006 answered")
        _, out = run_brief(capsys, area)
        assert "the standing call" in out
        assert "the old call" not in out
        assert "the settled deferral" not in out

    def test_an_empty_but_present_record_says_so(self, tmp_path, capsys):
        _root, area = ipo_copy(tmp_path)
        tid = flags.tenure_add(area, kind="ruling", text="the only call")
        flags.tenure_supersede(area, tid, reference="a later pass")
        _, out = run_brief(capsys, area)
        assert "TENURE" in out.upper()
        assert "none" in out.lower()

    def test_unreadable_record_is_loud_never_fatal(self, tmp_path, capsys):
        _root, area = ipo_copy(tmp_path)
        flags.tenure_path(area).parent.mkdir(parents=True, exist_ok=True)
        flags.tenure_path(area).write_text("- broken\n", encoding="utf-8")
        code, out = run_brief(capsys, area)
        assert code == 0
        assert "UNREADABLE" in out

    def test_both_entrypoints_carry_it(self, tmp_path):
        import engagement
        root, area = ipo_copy(tmp_path)
        flags.tenure_add(area, kind="ruling", text="merged the request paths")
        picture = brief.taxonomist_picture(root / "components", area)
        assert "merged the request paths" in picture
        assert "merged the request paths" in engagement.placement_brief(
            root / "components")

    def test_the_section_carries_no_kind_token(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        flags.tenure_add(area, kind="ruling", text="merged the request paths")
        picture = brief.taxonomist_picture(root / "components", area)
        assert "KIND" not in picture

    def test_the_brief_stays_read_only(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        flags.tenure_add(area, kind="doubt", text="weak placement")
        before = fingerprint(root)
        run_brief(capsys, area, "SCOPING")
        run_brief(capsys, area, "CURATION")
        assert fingerprint(root) == before


class TestContractText:
    def test_the_taxonomist_files_its_own_entries(self):
        text = CONTRACT.read_text(encoding="utf-8")
        assert "tenure" in text.lower()
        assert "flags.py" in text and "tenure-add" in text

    def test_start_from_your_own_precedent_framing(self):
        low = CONTRACT.read_text(encoding="utf-8").lower()
        assert "precedent" in low
        assert "supersede" in low

    def test_no_banned_phrase(self):
        low = CONTRACT.read_text(encoding="utf-8").lower()
        assert "does not exist yet" not in low


# --------------------------------------------------------------------------- #
# Part C — the boundary
# --------------------------------------------------------------------------- #

class TestBoundary:
    def test_the_advisor_never_reads_it(self, tmp_path):
        plain = simple(tmp_path / "plain")
        withfile = simple(tmp_path / "withfile")
        flags.tenure_add(Path(withfile), kind="ruling",
                         text="merged the request paths")
        flags.tenure_add(Path(withfile), kind="doubt", text="weak placement")
        a = walk_to_gate(plain)
        b = walk_to_gate(withfile)

        def scrub(d):
            return json.dumps(d, sort_keys=True, default=str).replace(
                str(withfile), "AREA").replace(str(plain), "AREA").replace(
                str(tmp_path / "withfile"), "ROOT").replace(
                str(tmp_path / "plain"), "ROOT")

        assert scrub(a) == scrub(b)

    def test_no_module_outside_the_brief_and_the_verb_reads_it(self):
        offenders = []
        for path in sorted((REPO / "scripts").glob("*.py")):
            if path.name in ("brief.py", "flags.py"):
                continue
            if ".tenure.yaml" in path.read_text(encoding="utf-8"):
                offenders.append(path.name)
        assert offenders == []

    def test_the_verb_is_hosted_in_flags_not_a_new_module(self):
        assert not (REPO / "scripts" / "tenure.py").exists()
        src = (REPO / "scripts" / "flags.py").read_text(encoding="utf-8")
        assert "tenure_path" in src

    def test_the_verb_writes_nothing_else(self, tmp_path):
        area = an_area(tmp_path)
        (area / "_reference").mkdir(parents=True, exist_ok=True)
        before = fingerprint(area)
        flags.tenure_add(area, kind="ruling", text="a call")
        after = fingerprint(area)
        new = set(after) - set(before)
        assert new == {flags.tenure_path(area)}
        assert {p: after[p] for p in before} == before

    def test_the_cli_module_runs_standalone(self, tmp_path):
        area = an_area(tmp_path)
        r = subprocess.run(
            ["python3", str(REPO / "scripts" / "flags.py"), "tenure-add",
             "--area", str(area), "--type", "ruling", "--text", "a call"],
            capture_output=True, text=True)
        assert r.returncode == 0 and r.stdout.strip() == "TEN-001"
