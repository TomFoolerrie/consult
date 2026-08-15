"""Regenerate tests/fixtures/golden/p2p-v1/ from the frozen p2p fixture.

Run from the repo root:  python3 tests/fixtures/golden/p2p-v1/regenerate.py
(This file is the committed regeneration script; see README.md beside it.)

It renders a TMP COPY of the fixture area through the v1 render path — the
frozen fixture is never written — normalizes per M36 A1, and overwrites the
committed golden parts. Regeneration is a GATE DECISION, not maintenance.
"""
import shutil
import sys
import tempfile

from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]                      # repo root
sys.path[:0] = [str(ROOT / "tests"),
                str(ROOT / "scripts"),
                str(ROOT / "skills" / "consult-docx-builder" / "scripts")]

import docx_compare                                            # noqa: E402
import render                                                  # noqa: E402

FIXTURE = (ROOT / "tests" / "fixtures" / "p2p-complete" / "components"
           / "procure-to-pay")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        area = Path(tmp) / "eng" / "components" / "procure-to-pay"
        area.parent.mkdir(parents=True)
        shutil.copytree(FIXTURE, area)
        out = Path(tmp) / "p2p.docx"
        render.render_folder(area, out, mode="working", emit_signal=False)
        for f in docx_compare.write_golden(out, HERE):
            print(f"wrote {f.relative_to(ROOT)}  ({f.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
