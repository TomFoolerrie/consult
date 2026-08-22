"""_pyfloor.py — the interpreter floor gate (M67 Part A).

The engine's Python floor is >= 3.10, and it is a RUNTIME floor rather than a
syntax one: `callouts.py` evaluates `str | None` at def time, so a 3.9
interpreter dies with a `TypeError` while IMPORTING callouts — transitively,
through `client_config`, `engagement`, `render`, `consolidate`, `brief`. A
guard placed after those imports can therefore never fire. So every
entry-point script calls `require()` as its first executable statement, ahead
of every first-party import, and this module is the one place the message
lives.

Two hard constraints follow from that job:

  - **This file must import under 3.9** (and older). Standard library only,
    no annotations, no `X | Y`, no 3.10-dependent construct anywhere — the
    module that reports the floor cannot be the module that trips over it.
  - **Importing it is silent.** `require()` is called explicitly, so tests
    (and any other module import) are unaffected on a healthy interpreter.

Python 3, stdlib only.
"""

import sys

FLOOR = (3, 10)

# The interpreter the plugin's own prose recommends when the default `python3`
# is too old — named in the fix line so the reader has a command, not a rule.
SUGGESTED = "python3.12"


def running_version(version_info=None):
    """`3.9.6`-style string for the interpreter this call is running on."""
    info = version_info or sys.version_info
    return "%d.%d.%d" % (info[0], info[1], info[2])


def floor_text(floor=FLOOR):
    """`3.10`-style string for the floor."""
    return "%d.%d" % (floor[0], floor[1])


def message(floor=FLOOR, version_info=None, executable=None, script=None):
    """The one refusal message: interpreter, floor, and the fix."""
    exe = executable or sys.executable or "python3"
    where = script or (sys.argv[0] if sys.argv else "") or "scripts/<script>.py"
    return (
        "ERROR: this script requires Python >= %s, but it is running on "
        "Python %s (%s).\n"
        "  The floor is not cosmetic: the engine's modules fail at IMPORT "
        "time on an older interpreter.\n"
        "  Fix: re-run as `%s %s ...` (any Python >= %s with the packages in "
        "requirements.txt installed)."
        % (floor_text(floor), running_version(version_info), exe,
           SUGGESTED, where, floor_text(floor))
    )


def require(floor=FLOOR, version_info=None, executable=None, script=None,
            stream=None):
    """Refuse on an interpreter below `floor`: one message, nonzero exit.

    Raises `SystemExit(2)` — usage-shaped, like the argparse refusals the
    entry points already use — after printing to stderr. Returns None on a
    healthy interpreter so the calling script proceeds untouched.
    """
    info = tuple(version_info or sys.version_info)
    if info[:2] >= tuple(floor[:2]):
        return
    out = stream or sys.stderr
    print(message(floor, info, executable, script), file=out)
    raise SystemExit(2)
