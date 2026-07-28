"""console_compat — never crash on a console that can't print our characters.

Windows consoles default to cp1252, and every CLI in this pipeline prints
em-dashes, arrows (→), middle dots and section signs. Python's default is
errors='strict', so the FIRST such character raises UnicodeEncodeError —
typically in a final summary print, turning a fully-successful run into an
ugly traceback and a nonzero exit that reads as failure (reported live from
scaffold.py confirm() on Windows).

Importing this module reconfigures stdout/stderr to errors='replace': the
console's native encoding is kept (no mojibake risk), and any character it
cannot represent degrades to '?' instead of crashing. UTF-8 terminals are
untouched. Imported for its side effect by every CLI entry script.
"""
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError, OSError):  # pragma: no cover
        pass  # non-reconfigurable stream (pipe wrapper, frozen env) — leave it
