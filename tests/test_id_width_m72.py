"""M72 — one id width for local CALLOUT ids.

Three gates:
  1. No 3-digit CALLOUT-prefix example id survives in the drafter contract or
     in the process-step skeleton seed bodies — and `SRC-nnn` examples, which
     are engine-minted and NOT callouts, are still there (the sweep boundary
     pinned from both sides).
  2. `callout_display_ids` maps BOTH widths onto sequential 2-digit display
     ids — the tolerance that makes the rule prospective style, not
     retroactive validation.
  3. The width rule is DECLARED in the contract, not inferred from examples.
"""

import json
import re
from pathlib import Path

import doc_model
import scaffold
from callouts import PREFIXES

ROOT = Path(__file__).resolve().parents[1]
DRAFTER = ROOT / "agents" / "consult-drafter.md"

#: A CALLOUT-prefix id with a 3-or-more-digit number. SRC is deliberately not
#: in `PREFIXES` (callouts.py LABEL_TO_PREFIX) and so is never matched here.
WIDE_CALLOUT_ID = re.compile(
    r"\b(" + "|".join(PREFIXES) + r")-[0-9]{3,}\b")


# --------------------------------------------------------------------------- #
# 1. the sweep, and its boundary
# --------------------------------------------------------------------------- #

def test_drafter_contract_has_no_three_digit_callout_ids():
    text = DRAFTER.read_text(encoding="utf-8")
    assert WIDE_CALLOUT_ID.findall(text) == []


def test_drafter_contract_keeps_three_digit_src_examples():
    """SRC ids are engine-minted 3-digit (`engagement.py`) — not swept."""
    text = DRAFTER.read_text(encoding="utf-8")
    assert re.search(r"\bSRC-[0-9]{3}\b", text)


def test_process_step_skeleton_seeds_have_no_three_digit_callout_ids():
    for slug, body in scaffold._FALLBACK_PART_BODIES.items():
        assert WIDE_CALLOUT_ID.findall(body) == [], slug


def test_process_step_skeleton_render_has_no_three_digit_callout_ids():
    body = scaffold.render_skeleton("Some Step", unit="process-step")
    assert WIDE_CALLOUT_ID.findall(body) == []


# --------------------------------------------------------------------------- #
# 2. the tolerance: both widths render identically
# --------------------------------------------------------------------------- #

FRAG = """## {title}

### E. Step-by-Step Procedure

1. Do the thing.

{callouts}
"""


def _write_area(tmp_path, fragments):
    """fragments: [(slug, order, callout-text)] in manifest order."""
    components = [
        {"file": f"{order}_{slug}.md", "heading": slug.title(), "order": order,
         "role": "procedure", "slug": slug, "l2": "bank-ops"}
        for slug, order, _ in fragments
    ]
    manifest = {
        "schema": doc_model.SCHEMA_V1,
        "area": "cash",
        "l1": "Cash Management",
        "title": "Cash Management Processes",
        "subtitle": "FY26",
        "l2_order": ["bank-ops"],
        "components": components,
    }
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    for comp, (slug, _order, callouts) in zip(components, fragments):
        (tmp_path / comp["file"]).write_text(
            FRAG.format(title=slug.title(), callouts=callouts),
            encoding="utf-8")
    return tmp_path


def test_mixed_width_locals_get_sequential_two_digit_display_ids(tmp_path):
    """A 2-digit local and a 3-digit local, in the same area, both land on
    sequential 2-digit display ids — the widths are indistinguishable
    downstream."""
    _write_area(tmp_path, [
        ("match-po", 10,
         "> **VALIDATION REQUIRED — GAP-01:** Confirm the tolerance.\n"),
        ("goods-receipt", 20,
         "> **VALIDATION REQUIRED — GAP-001:** Confirm the receipt window.\n"),
    ])
    assert doc_model.callout_display_ids(tmp_path) == {
        ("match-po", "GAP-01"): "GAP-01",
        ("goods-receipt", "GAP-001"): "GAP-02",
    }


def test_mixed_width_locals_within_one_fragment(tmp_path):
    """Both widths inside ONE procedure still number sequentially, and a
    second prefix keeps its own counter."""
    _write_area(tmp_path, [
        ("match-po", 10,
         "> **VALIDATION REQUIRED — GAP-001:** First.\n\n"
         "> **VALIDATION REQUIRED — GAP-02:** Second.\n\n"
         "> **PAIN POINT — PP-001:** Manual matching.\n"),
    ])
    assert doc_model.callout_display_ids(tmp_path) == {
        ("match-po", "GAP-001"): "GAP-01",
        ("match-po", "GAP-02"): "GAP-02",
        ("match-po", "PP-001"): "PP-01",
    }


# --------------------------------------------------------------------------- #
# 3. the rule is declared, not inferred
# --------------------------------------------------------------------------- #

def test_drafter_contract_declares_the_width_rule():
    text = DRAFTER.read_text(encoding="utf-8")
    assert "local callout ids are 2-digit" in text
    assert "`SRC-` ids are engine-minted 3-digit" in text


# --------------------------------------------------------------------------- #
# 4. v1 stamp source is untouched (the ticket's explicit ruling)
# --------------------------------------------------------------------------- #

def test_v1_skeleton_file_still_mixes_widths_by_ruling():
    """`procedure_skeleton.md` is v1's stamp source and stays byte-identical:
    the one-width rule is v2-prospective. Pinned so a later sweep of this file
    is a deliberate decision, not a tidy-up."""
    v1 = (ROOT / "skills" / "consult-drafter" / "reference"
          / "procedure_skeleton.md").read_text(encoding="utf-8")
    assert "CTRL-001" in v1 and "PP-001" in v1
    assert "GAP-01:" in v1
