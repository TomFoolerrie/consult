"""Tests for M21 — render signal correctness.

`--mode final` must behave exactly like `--slugs`: it NEVER writes
`.render.json`, so producing the client deliverable can no longer re-open the
review gate or discard a recorded `accept`. Working-mode behavior (the signal
it writes, its shape) must be byte-identical to pre-M21.

Reuses the synthetic area from test_render (same fixture shape used by
test_kits.py) and the orchestrate/scope_delta walk from test_orchestrate.py
(emit_aggregate -> emit_reconcile -> scope_delta.commit -> render -> review ->
accept -> done) to exercise the real advisor precedence table, not just the
signal file's raw JSON.
"""
import json

import orchestrate
import scope_delta

import render
from test_render import make_area


# --------------------------------------------------------------------------- #
# Acceptance: --mode final leaves .render.json byte-identical (or absent)
# --------------------------------------------------------------------------- #

def test_final_render_does_not_create_signal_when_absent(tmp_path):
    """Final render on an area never rendered in working mode does not create
    the signal (acceptance bullet 3)."""
    area = make_area(tmp_path)
    out = tmp_path / "final.docx"
    render.render_folder(area, out, mode="final")
    assert not (area / ".render.json").exists()


def test_final_render_leaves_existing_signal_byte_identical(tmp_path):
    """A working render writes .render.json; a subsequent final render must
    leave those bytes untouched — not rewritten with the same content, not
    repointed at the final docx (acceptance bullet 1)."""
    area = make_area(tmp_path)
    working_out = tmp_path / "working.docx"
    render.render_folder(area, working_out, mode="working", emit_signal=True)
    sig_path = area / ".render.json"
    before = sig_path.read_bytes()
    before_stat = sig_path.stat()

    final_out = tmp_path / "final.docx"
    render.render_folder(area, final_out, mode="final")

    after = sig_path.read_bytes()
    assert after == before
    # Not just logically equal — untouched (mtime/size unchanged too).
    assert sig_path.stat().st_mtime_ns == before_stat.st_mtime_ns
    payload = json.loads(after.decode("utf-8"))
    assert payload["docx"] == str(working_out)   # not repointed at final.docx
    assert payload["awaiting_review"] is True


def test_final_render_default_emit_signal_still_skips(tmp_path):
    """Default emit_signal=True (the CLI path) must not matter for final mode
    — the mode gate, not emit_signal, is what decides this."""
    area = make_area(tmp_path)
    out = tmp_path / "final.docx"
    stats = render.render_folder(area, out, mode="final", emit_signal=True)
    assert stats["mode"] == "final"
    assert not (area / ".render.json").exists()


# --------------------------------------------------------------------------- #
# Acceptance: working mode is unchanged — sets awaiting_review true w/ basis
# --------------------------------------------------------------------------- #

def test_working_render_still_sets_awaiting_review_true_with_basis(tmp_path):
    """Working-mode behavior must be byte-identical to pre-M21: it still
    writes {basis, docx, awaiting_review: true} (acceptance bullet 5)."""
    area = make_area(tmp_path)
    out = tmp_path / "working.docx"
    render.render_folder(area, out, emit_signal=True)   # mode defaults working
    sig = json.loads((area / ".render.json").read_text(encoding="utf-8"))
    assert sig["awaiting_review"] is True
    assert sig["docx"] == str(out)
    assert sig["basis"] == orchestrate.AreaState(str(area)).basis_hash()


# --------------------------------------------------------------------------- #
# Acceptance: --slugs behaviour is unchanged (still never writes the signal,
# in either mode)
# --------------------------------------------------------------------------- #

def test_slugs_subset_never_writes_signal_in_working_mode(tmp_path):
    area = make_area(tmp_path)
    out = tmp_path / "kit.docx"
    render.render_folder(area, out, slugs=["payment-run"], emit_signal=True)
    assert not (area / ".render.json").exists()


def test_slugs_subset_never_writes_signal_in_final_mode(tmp_path):
    area = make_area(tmp_path)
    out = tmp_path / "kit-final.docx"
    render.render_folder(area, out, mode="final", slugs=["payment-run"],
                         emit_signal=True)
    assert not (area / ".render.json").exists()


def test_slugs_subset_after_working_render_leaves_signal_untouched(tmp_path):
    """A kit render taken after a working render must not perturb the
    already-recorded signal, exactly like final mode."""
    area = make_area(tmp_path)
    render.render_folder(area, tmp_path / "working.docx", mode="working")
    before = (area / ".render.json").read_bytes()
    render.render_folder(area, tmp_path / "kit.docx", slugs=["payment-run"])
    assert (area / ".render.json").read_bytes() == before


# --------------------------------------------------------------------------- #
# Acceptance: working -> accept -> final -> advisor still reports `done`, not
# `review` (the actual bug this ticket fixes)
# --------------------------------------------------------------------------- #

def _walk_to_render_guard(area):
    """Drive a synthetic area through the M7 precedence table up to (but not
    including) the render stage, mirroring test_orchestrate's
    test_full_walk_to_done. Returns nothing; caller renders next."""
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=True)
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")


def test_working_accept_final_reports_done_not_review(tmp_path):
    """The exact regression from the spec: render working, accept the
    sign-off, render final for the client — the advisor must report `done`,
    never re-open `review` (acceptance bullet 2)."""
    area = make_area(tmp_path)
    area_s = str(area)
    _walk_to_render_guard(area_s)
    assert orchestrate.decide(area_s)["action"] == "render"

    working_out = tmp_path / "working.docx"
    render.render_folder(area, working_out, mode="working")
    d = orchestrate.decide(area_s)
    assert d["action"] == "review"
    assert d["human_gate"] is True

    res = orchestrate.accept_review(area_s)
    assert res["accepted"] is True
    assert orchestrate.decide(area_s)["action"] == "done"

    # The bug: producing the client deliverable used to re-open the gate.
    final_out = tmp_path / "final.docx"
    render.render_folder(area, final_out, mode="final")
    d = orchestrate.decide(area_s)
    assert d["action"] == "done", (
        "final render must not re-open the review gate after an accept"
    )
    assert d["details"]["docx"] == str(working_out)   # still the accepted doc


def test_final_render_never_creates_signal_after_accept_on_fresh_area(tmp_path):
    """A final render on an area that reached `done` via accept (so
    .render.json exists with awaiting_review: false) must not touch that
    file at all — not even to rewrite the same values."""
    area = make_area(tmp_path)
    area_s = str(area)
    _walk_to_render_guard(area_s)
    working_out = tmp_path / "working.docx"
    render.render_folder(area, working_out, mode="working")
    orchestrate.accept_review(area_s)
    sig_path = area / ".render.json"
    before = sig_path.read_bytes()

    render.render_folder(area, tmp_path / "final.docx", mode="final")
    assert sig_path.read_bytes() == before
