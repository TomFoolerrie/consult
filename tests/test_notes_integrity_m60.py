"""M60 gate — notes-bus integrity: escape, dedup, atomic.

The adversarial-review repros (F-05, F-10, F-24) with exact inputs.
docs/v2/M60-notes-bus-integrity.md is the spec.
"""

import os

import pytest
import yaml

import notes_util
from notes_util import NotesError, append_items, load_items


def notes_path(area, slug):
    return area / "_review" / f"{slug}.notes.yaml"


class TestPartAWriterAlwaysParses:
    @pytest.mark.parametrize("code", list(range(0x00, 0x20))
                             + list(range(0x7F, 0xA0)))
    def test_every_control_char_round_trips(self, tmp_path, code):
        raw = f"before{chr(code)}after"
        item = {"kind": "review", "type": "comment", "note": raw}
        assert append_items(tmp_path, "s", [item]) == 1
        loaded = load_items(tmp_path, "s")     # parses, drafter-visible
        assert len(loaded) == 1
        assert loaded[0]["note"] == notes_util._stored_form(raw)
        assert "before" in loaded[0]["note"] and "after" in loaded[0]["note"]

    def test_quotes_backslashes_newlines_round_trip(self, tmp_path):
        raw = 'She said "hi"\\there\nand\tleft'
        append_items(tmp_path, "s", [{"kind": "review", "note": raw}])
        assert load_items(tmp_path, "s")[0]["note"] == \
            'She said "hi"\\there and left'

    def test_f05_mojibake_never_erases_history(self, tmp_path):
        # prior history on the bus
        append_items(tmp_path, "s", [{"kind": "review", "note": "first"},
                                     {"kind": "review", "note": "second"}])
        # a C1 mojibake character (Windows-1252 smart quote seen as U+0092)
        append_items(tmp_path, "s",
                     [{"kind": "review", "note": "moji\x92bake"}])
        items = load_items(tmp_path, "s")
        assert [i["note"] for i in items[:2]] == ["first", "second"], (
            "prior notes must still load")
        # and a LATER append preserves everything
        append_items(tmp_path, "s", [{"kind": "review", "note": "fourth"}])
        notes = [i["note"] for i in load_items(tmp_path, "s")]
        assert notes[0] == "first" and "fourth" in notes and len(notes) == 4


class TestPartBStoreFormDedup:
    def test_f10_multiline_ingest_is_idempotent(self, tmp_path):
        answer = {"kind": "review", "type": "gap-answer",
                  "note": "The cutoff is Friday.\nExcept at quarter end,\n"
                          "when it moves to Thursday."}
        assert append_items(tmp_path, "s", [answer]) == 1
        assert append_items(tmp_path, "s", [dict(answer)]) == 0, (
            "re-running the same ingest must add nothing")
        assert len(load_items(tmp_path, "s")) == 1

    def test_reloaded_item_matches_raw_twin(self, tmp_path):
        raw = {"kind": "review", "note": "line one\nline two"}
        append_items(tmp_path, "s", [raw])
        stored = load_items(tmp_path, "s")[0]
        assert notes_util._fingerprint(stored) == notes_util._fingerprint(raw)


class TestPartCAtomicAndLoud:
    def test_crash_mid_write_leaves_original_intact(self, tmp_path,
                                                    monkeypatch):
        append_items(tmp_path, "s", [{"kind": "review", "note": "precious"}])
        before = notes_path(tmp_path, "s").read_text(encoding="utf-8")

        def boom(src, dst):
            raise OSError("simulated crash between truncate and write")

        monkeypatch.setattr(os, "replace", boom)
        monkeypatch.setattr(notes_util.os, "replace", boom, raising=True)
        with pytest.raises(OSError):
            append_items(tmp_path, "s", [{"kind": "review", "note": "new"}])
        assert notes_path(tmp_path, "s").read_text(
            encoding="utf-8") == before, "original file must be untouched"

    def test_corrupt_file_plus_append_fails_loud_never_overwrites(
            self, tmp_path):
        f = notes_path(tmp_path, "s")
        f.parent.mkdir(parents=True)
        f.write_text('procedure: "s"\nitems: [::', encoding="utf-8")
        before = f.read_text(encoding="utf-8")
        with pytest.raises(NotesError) as exc:
            append_items(tmp_path, "s", [{"kind": "review", "note": "x"}])
        assert "s.notes.yaml" in str(exc.value)
        assert f.read_text(encoding="utf-8") == before, (
            "a corrupt history must never be silently overwritten")

    def test_non_mapping_file_refused(self, tmp_path):
        f = notes_path(tmp_path, "s")
        f.parent.mkdir(parents=True)
        f.write_text("- a\n- list\n", encoding="utf-8")
        with pytest.raises(NotesError):
            load_items(tmp_path, "s")

    def test_absent_file_still_reads_empty(self, tmp_path):
        assert load_items(tmp_path, "ghost") == []

    def test_no_tmp_droppings_after_success(self, tmp_path):
        append_items(tmp_path, "s", [{"kind": "review", "note": "x"}])
        leftovers = list((tmp_path / "_review").glob("*.tmp"))
        assert leftovers == []
