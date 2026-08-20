"""M55 acceptance tests — written BEFORE the build.

Pins: `ledger.show` — the human-readable ledger verb (every SRC with its
consumption picture, the unconsumed tail flagged, provenance shown,
deterministic, read-only) — and appendix-controls optionality, which the
definition language ALREADY affords (probed 2026-08-18: a user-space
shadow copy of desktop-procedure without the `screenshot-index` block
renders without Appendix C, zero engine edits); Part B here pins that
affordance and the skill passage documenting it, so it cannot regress
silently. Default stays ON: the shipped definition is untouched and the
compatibility gate/goldens pin byte-identity.

Everything skips until ledger.py grows `show`.
"""

import shutil
from pathlib import Path

import pytest

import gatecheck
import yaml

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
P2P_ROOT = Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"
SHIPPED_DP = REPO / "kernel" / "deliverables" / "desktop-procedure.yaml"

needs_show = gatecheck.landed(
    "def show" not in (REPO / "scripts" / "ledger.py").read_text(
        encoding="utf-8"),
    reason="M55 ledger show verb not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest


# --------------------------------------------------------------------------- #
# Part A — the human-readable ledger verb
# --------------------------------------------------------------------------- #

@needs_show
class TestLedgerShow:
    def test_every_source_renders_with_its_consumption_picture(self, tmp_path):
        import ledger
        root = ipo_copy(tmp_path)
        out = ledger.show(root)
        for sid in ("SRC-001", "SRC-002", "SRC-003", "SRC-004"):
            assert sid in out
        assert "purchasing" in out          # who read it
        assert "schedule-payment" in out    # into what

    def test_the_unconsumed_tail_is_flagged(self, tmp_path):
        import ledger
        root = ipo_copy(tmp_path)
        out = ledger.show(root)
        # SRC-004 is the fixture's registered-but-never-read source; the
        # verb must call it out as owed a read, distinctly from the others
        tail = out[out.index("SRC-004"):]
        low = tail[:400].lower()
        assert "unconsumed" in low or "not yet" in low or "owe" in low

    def test_provenance_is_shown(self, tmp_path):
        import ledger
        root = ipo_copy(tmp_path)
        lpath = root / "_sources" / "sources.yaml"
        data = yaml.safe_load(lpath.read_text(encoding="utf-8"))
        data["sources"][0]["provenance"] = "public"
        lpath.write_text(yaml.safe_dump(data), encoding="utf-8")
        out = ledger.show(root)
        block = out[out.index("SRC-001"):out.index("SRC-002")]
        assert "public" in block.lower()

    def test_deterministic_and_read_only(self, tmp_path):
        import ledger
        root = ipo_copy(tmp_path)
        before = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                  for p in root.rglob("*") if p.is_file()}
        assert ledger.show(root) == ledger.show(root)
        after = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                 for p in root.rglob("*") if p.is_file()}
        assert before == after

    def test_cli_reachable(self, tmp_path):
        import subprocess
        import sys
        root = ipo_copy(tmp_path)
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "ledger.py"),
             "show", str(root)],
            capture_output=True, text=True)
        assert proc.returncode == 0 and "SRC-001" in proc.stdout


# --------------------------------------------------------------------------- #
# Part B — appendix optionality, in user space
# --------------------------------------------------------------------------- #

@needs_show
class TestAppendixOptOut:
    def _render(self, tmp_path, drop_id=None):
        import sys
        sys.path.insert(0, str(REPO / "tests"))
        import definitions
        import docx_compare
        import render_glue
        root = tmp_path / "eng"
        shutil.copytree(P2P_ROOT, root)
        area = root / "components" / "procure-to-pay"
        if drop_id:
            data = yaml.safe_load(SHIPPED_DP.read_text(encoding="utf-8"))
            data["shape"] = [s for s in data["shape"]
                             if s.get("id") != drop_id]
            dest = root / "components" / "_client" / "deliverables"
            dest.mkdir(parents=True)
            (dest / "desktop-procedure.yaml").write_text(
                yaml.safe_dump(data), encoding="utf-8")
        defn = definitions.load_definition("desktop-procedure", area=area)
        plan = definitions.compile_plan(defn, area)
        out = tmp_path / "dp.docx"
        render_glue.render_plan(plan, area, out)
        return docx_compare.read_docx_parts(out)["word/document.xml"]

    def test_opted_out_section_does_not_render(self, tmp_path):
        xml = self._render(tmp_path, drop_id="screenshot-index")
        assert "Screenshot / Evidence Index" not in xml
        assert "Validation Log" in xml        # its neighbours untouched

    def test_default_stays_on(self, tmp_path):
        # no shadow: the shipped definition renders every appendix — v1
        # output is law and the goldens pin the bytes elsewhere
        xml = self._render(tmp_path)
        assert "Screenshot / Evidence Index" in xml

    def test_shipped_definition_untouched(self):
        data = yaml.safe_load(SHIPPED_DP.read_text(encoding="utf-8"))
        ids = [s.get("id") for s in data["shape"]]
        assert "screenshot-index" in ids and "gap-log" in ids

    def test_skill_documents_the_opt_out(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "_client/deliverables" in low
        assert "opt" in low and "section" in low
