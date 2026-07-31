"""Tests for scripts/callouts.py — ID grammar, fence blanking, callout definition scan."""
import callouts
from callouts import (BARE_GAP_RE, BODY_GAP_RE, ID_INLINE_RE, ID_STRICT_RE,
                      LABEL_TO_PREFIX, XREF_RE, blank_fences, iter_defined_ids,
                      strip_fences)


def test_id_strict_accepts_valid():
    """ID_STRICT_RE matches <PREFIX>-<UPPER-ALNUM> with optional segments."""
    for good in ("CTRL-01", "GAP-A1", "PP-REV-2", "IO-XY-Z9", "SC-1"):
        assert ID_STRICT_RE.match(good), good


def test_id_strict_rejects_invalid():
    """ID_STRICT_RE rejects wrong prefixes, lowercase, trailing/empty segments."""
    for bad in ("CTL-01", "gap-01", "GAP-", "GAP-01-", "GAP_01",
                "GAP-01x extra", " GAP-01", "PPX-01"):
        assert not ID_STRICT_RE.match(bad), bad


def test_id_inline_finds_in_prose():
    """ID_INLINE_RE finds well-formed IDs embedded in prose."""
    found = ID_INLINE_RE.findall("see CTRL-02 and GAP-REV-1, not xGAP-9")
    assert ("CTRL", "02") in found and ("GAP", "REV-1") in found


def test_body_gap_re_all_delimiters():
    """BODY_GAP_RE matches [[GAP-NN <dash> ...]] with -, en-dash, or em-dash."""
    for d in ("-", "–", "—"):
        assert BODY_GAP_RE.search(f"[[GAP-07 {d} missing detail]]")


def test_bare_gap_re():
    """BARE_GAP_RE matches an id-less [[GAP — reason]] but not an id'd one."""
    assert BARE_GAP_RE.search("[[GAP — reason]]")
    assert BARE_GAP_RE.search("[[GAP]]")
    assert not BARE_GAP_RE.search("[[GAP-01 — reason]]")


def test_xref_re():
    """XREF_RE captures [[slug]] and [[#slug]] slugs; uppercase forms don't match."""
    assert XREF_RE.findall("see [[monthly-close]] and [[#ap-run]]") == \
        ["monthly-close", "ap-run"]
    assert not XREF_RE.search("[[GAP-01]]")  # uppercase: not an xref


def test_blank_fences_preserves_line_count():
    """blank_fences blanks fenced bodies but keeps total line count stable."""
    text = "a\n```\n> **CONTROL — CTRL-01:** hidden\n```\nb\n"
    out = blank_fences(text)
    assert out.count("\n") == text.count("\n")
    assert "CTRL-01" not in out
    assert strip_fences is blank_fences  # back-compat alias


def test_blank_fences_tilde():
    """~~~ fences are blanked just like backtick fences."""
    assert "secret" not in blank_fences("~~~\nsecret\n~~~\n")


def test_blank_fences_indented_fence_is_blanked():
    """M28 — a fence opened/closed with up to 3 leading spaces (e.g. inside a
    list item) is still a fence; example callouts inside it must not parse."""
    text = ("- an example:\n"
            "  ```\n"
            "  > **CONTROL — CTRL-09:** example only\n"
            "  ```\n"
            "after\n")
    out = blank_fences(text)
    assert "CTRL-09" not in out
    assert out.count("\n") == text.count("\n")
    assert "after" in out


def test_blank_fences_unclosed_fence_blanks_to_eof():
    """M28 — an unclosed fence blanks to end-of-text instead of escaping
    blanking entirely (the old false-positive source for DANGLING ids)."""
    text = "prose\n```\n> **CONTROL — CTRL-09:** example\n[[no-such-slug]]\n"
    out = blank_fences(text)
    assert "CTRL-09" not in out and "no-such-slug" not in out
    assert out.count("\n") == text.count("\n")
    assert "prose" in out


def test_iter_defined_ids_basic():
    """iter_defined_ids yields (prefix, id) for each well-labelled callout in order."""
    text = (
        "> **CONTROL — CTRL-01:** desc\n"
        "body\n"
        "> **VALIDATION REQUIRED — GAP-02:** ask\n"
        "> **PAIN POINT - PP-03:** slow\n"
    )
    assert list(iter_defined_ids(text)) == [
        ("CTRL", "CTRL-01"), ("GAP", "GAP-02"), ("PP", "PP-03")]


def test_iter_defined_ids_skips_fenced_and_mismatched():
    """Callouts inside fences or with label/prefix mismatch are not yielded."""
    text = (
        "```\n> **CONTROL — CTRL-09:** in code\n```\n"
        "> **CONTROL — GAP-01:** wrong prefix for label\n"
        "> **UNKNOWN LABEL — CTRL-02:** unmapped label\n"
    )
    assert list(iter_defined_ids(text)) == []


def test_iter_defined_ids_collapses_label_whitespace():
    """Multiple internal spaces in the label still map via LABEL_TO_PREFIX."""
    text = "> **IMPROVEMENT  OPPORTUNITY — IO-01:** faster\n"
    assert list(iter_defined_ids(text)) == [("IO", "IO-01")]


def test_label_map_and_enum():
    """The label→prefix map and severity enum match the documented contract."""
    assert LABEL_TO_PREFIX == {
        "CONTROL": "CTRL",
        "VALIDATION REQUIRED": "GAP",
        "PAIN POINT": "PP",
        "IMPROVEMENT OPPORTUNITY": "IO",
        "SCREENSHOT PLACEHOLDER": "SC",
    }
    assert callouts.LABEL_PREFIX is LABEL_TO_PREFIX
    assert callouts.SEVERITY_ENUM == {"High", "Medium", "Low"}
    assert callouts.PREFIXES == sorted(set(LABEL_TO_PREFIX.values()))


def test_fragment_error_is_exception():
    """FragmentError is a raisable Exception subclass."""
    assert issubclass(callouts.FragmentError, Exception)


def test_iter_defined_ids_empty_text():
    """Empty input yields nothing."""
    assert list(iter_defined_ids("")) == []
