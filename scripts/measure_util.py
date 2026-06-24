#!/usr/bin/env python3
"""measure_util.py — content-free size side-channel for the input gatherers (T56).

Shared helper so consolidate_inputs.py / draft_inputs.py / synthesis_inputs.py
emit a deterministic, **content-free** size summary WITHOUT polluting the stdout
bundle the sub-agent consumes. The summary is the input-side complement to the
fan-out workflow's `budget.spent()` output-token deltas (persisted to
`cost_map.json`): `budget` sees output tokens, this sees the input the budget
can't.

HARD CONTRACT — content-free. Everything emitted here is a number, a count, or a
FIXED STRUCTURAL LABEL (taxonomy-slice / evidence / prior-MD / register / …). It
NEVER emits document text, evidence refs, dedup_keys, or `source#Lx-Ly` strings.
The per-section breakdown is keyed only by labels the *caller* supplies from a
fixed vocabulary; the values are the serialized byte/char sizes of each subtree,
never the subtree itself.

Sizing is done on the SAME compact serialization the worker consumes
(`json.dumps(..., ensure_ascii=False, separators=(",", ":"))`), so the char
count is both meaningful (it is the real inlined payload) and deterministic
(same fixture -> same numbers). The token figure is an ESTIMATE (chars / 4) and
is always labelled as such.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Tuple

# Estimated bytes-per-token. A coarse, documented heuristic (NOT a real
# tokenizer) — the output is always labelled "(est.)".
CHARS_PER_TOKEN = 4

# The exact serialization the `--json` worker bundle uses. Sizing must mirror it
# byte-for-byte so the measured chars equal the real inlined payload.
_COMPACT = dict(ensure_ascii=False, separators=(",", ":"))


def _serialized_len(obj: Any) -> int:
    """Char length of `obj` under the worker's compact JSON serialization."""
    return len(json.dumps(obj, **_COMPACT))


def est_tokens(chars: int) -> int:
    """Estimated token count for a char total (chars / 4, floored). ESTIMATE."""
    return chars // CHARS_PER_TOKEN


def summarize(bundle: Dict[str, Any],
              sections: List[Tuple[str, Any]]) -> Dict[str, Any]:
    """Build a content-free size summary for one gatherer bundle.

    `sections` is an ordered list of (FIXED_LABEL, subtree) pairs supplied by the
    caller from a fixed structural vocabulary. Only the label string and the
    serialized SIZE of each subtree leave this function — never the subtree.

    Returns a dict of pure numbers/labels:
      total_chars, est_tokens, est_tokens_basis, sections[{label, chars,
      est_tokens}].
    The total is measured on the *whole* bundle (the real payload), so it is
    exact; the per-section chars are each subtree's own serialized size and will
    not sum to the total (compact JSON keys/punctuation live between sections) —
    they are a relative breakdown, not a partition, and are labelled as such by
    the renderers.
    """
    total = _serialized_len(bundle)
    section_rows: List[Dict[str, Any]] = []
    for label, subtree in sections:
        chars = _serialized_len(subtree)
        section_rows.append({
            "label": label,
            "chars": chars,
            "est_tokens": est_tokens(chars),
        })
    return {
        "total_chars": total,
        "est_tokens": est_tokens(total),
        "est_tokens_basis": f"chars/{CHARS_PER_TOKEN} (estimate, not a tokenizer)",
        "sections": section_rows,
    }


def render_human(summary: Dict[str, Any], header: str) -> str:
    """Render the size summary as a content-free human block (for stderr)."""
    lines: List[str] = []
    lines.append(f"[measure] {header}")
    lines.append(f"  serialized bundle: {summary['total_chars']} chars  "
                 f"~{summary['est_tokens']} tokens (est., {summary['est_tokens_basis']})")
    lines.append("  per-section (serialized chars / est. tokens; labels only):")
    for row in summary["sections"]:
        lines.append(f"    - {row['label']}: {row['chars']} chars  "
                     f"~{row['est_tokens']} tok (est.)")
    return "\n".join(lines)


def emit(bundle: Dict[str, Any], sections: List[Tuple[str, Any]], header: str,
         as_json: bool, stream=sys.stderr) -> Dict[str, Any]:
    """Compute + print the content-free summary to a side-channel stream.

    `stream` defaults to stderr so it never pollutes the stdout `--json` bundle
    the worker consumes. With `as_json` the summary is emitted as a compact JSON
    object (still on the side-channel stream); otherwise as the human block.
    Returns the summary dict (so `measure` / tests can reuse it without re-walk).
    """
    summary = summarize(bundle, sections)
    if as_json:
        print(json.dumps(summary, **_COMPACT), file=stream)
    else:
        print(render_human(summary, header), file=stream)
    return summary
