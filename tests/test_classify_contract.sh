#!/usr/bin/env bash
# =============================================================================
# test_classify_contract.sh — T49 classify-merge contract regressions
#
# Two unexercised classify-contract paths, each on its own scratch engagement:
#
#  ITEM 2 — LENS CONFLICT (engagement __t49c__):
#    Two canned classify artifacts genuinely DISAGREE on one lens for the same
#    node (record-to-report.close: doc A says process=pain_high, doc B says
#    process=strength, both high-confidence). The deterministic merge must:
#      * leave that lens NULL (no value wins a real disagreement), and
#      * raise EXACTLY ONE GAP-CONFLICT-record-to-report-close-process row.
#    A non-conflicting lens (current_state, agreed by both) is still set, proving
#    the conflict is per-lens, not a blanket bail-out.
#
#  ITEM 3 — PHANTOM EVIDENCE REF (engagement __t49d__):
#    A canned artifact cites `#L9999`, far past the end of the ingested MD. The
#    merge validates every artifact first (fail-closed), so the phantom ref must
#    be REJECTED/REPORTED at merge: the artifact is SKIPPED (not merged) and the
#    merge output names the out-of-range line. The same ref is also rejected by
#    the standalone validate_artifact.py the merge delegates to.
#
# Both fixtures are SYNTHETIC (written inline, referencing the real ingested R2R
# close transcript). Scratch engagements are removed at the end. Exits 0 only if
# every assertion passes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
SM="scripts/state_machine.py"
INGEST="scripts/ingest_normalize.py"
VALIDATE="scripts/validate_artifact.py"
MERGE="scripts/classify_merge.py"
FIX="fixtures/r2r"
NODE="record-to-report.close"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi; }

EID_C="__t49c__"
EID_D="__t49d__"
cleanup() { rm -rf "engagements/$EID_C" "engagements/$EID_D"; }
trap cleanup EXIT
cleanup

# Resolve the engagement-relative path of the ingested close MD (hash unknown
# until after ingest).
ingested_close_rel() { # $1 = engagement id
  "$PY" - "$1" <<'PY'
import sys
from pathlib import Path
ing = Path("engagements") / sys.argv[1] / "ingested"
m = sorted(p for p in ing.glob("*.md") if "close-walkthrough" in p.name)
print(f"ingested/{m[0].name}")
PY
}

count_conflict_gaps() { # $1 = engagement id
  "$PY" - "engagements/$1/register.json" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
n = 0
for r in rows:
    if str(r.get("id") or "").startswith("GAP-CONFLICT-record-to-report-close-process"):
        if (r.get("record_status") or "active") not in ("archived","deleted","inactive"):
            n += 1
print(n)
PY
}

node_lens() { # $1 engagement  $2 lens
  "$PY" - "$1" "$NODE" "$2" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
      "get-node", "--engagement", sys.argv[1], "--node", sys.argv[2], "--json"])
v = (json.loads(out).get("lenses") or {}).get(sys.argv[3])
print("NULL" if v is None else v)
PY
}

# =============================================================================
echo "================================================================"
echo "ITEM 2: lens conflict -> one GAP-CONFLICT + null lens  ($EID_C)"
echo "================================================================"
"$PY" "$SM" init --engagement "$EID_C" --region NA >/dev/null
"$PY" "$INGEST" ingest --engagement "$EID_C" --source "$FIX/close_walkthrough.vtt" >/dev/null
CLOSE_REL="$(ingested_close_rel "$EID_C")"
mkdir -p "engagements/$EID_C/classify"

# Two artifacts that AGREE on current_state (present) but DISAGREE on process
# (pain_high vs strength), both high-confidence -> genuine lens conflict.
"$PY" - "engagements/$EID_C/classify" "$CLOSE_REL" <<'PY'
import json, sys
from pathlib import Path
outdir, rel = Path(sys.argv[1]), sys.argv[2]
def art(value):
    return {
        "doc": {"source": rel, "doc_type": "transcript",
                "classified_at": "2026-06-21T00:00:00Z"},
        "node_hits": [{
            "node": "record-to-report.close",
            "confidence": "high",
            "rationale": "Close walkthrough.",
            "lens_signals": [
                {"lens": "current_state", "value": "present", "confidence": "high",
                 "evidence_ref": f"{rel}#L23", "rationale": "Close process exists."},
                {"lens": "process", "value": value, "confidence": "high",
                 "evidence_ref": f"{rel}#L27", "rationale": f"process={value}."},
            ],
        }],
    }
(outdir / "docA.artifact.json").write_text(json.dumps(art("pain_high"), indent=2))
(outdir / "docB.artifact.json").write_text(json.dumps(art("strength"), indent=2))
print("wrote 2 conflicting artifacts")
PY

# Both artifacts validate cleanly (the conflict is a merge-policy outcome, not a
# validation error).
for a in "engagements/$EID_C/classify"/*.artifact.json; do
  "$PY" "$VALIDATE" validate --artifact "$a" --engagement "$EID_C" >/dev/null \
    && ok "artifact validates: $(basename "$a")" \
    || bad "artifact failed validation: $(basename "$a")"
done

MERGE_OUT_C="$("$PY" "$MERGE" merge --engagement "$EID_C" 2>&1)"
echo "$MERGE_OUT_C" | sed 's/^/    /'
# Agreed lens is set; conflicting lens is left null.
assert_eq "present" "$(node_lens "$EID_C" current_state)" "agreed lens current_state is SET (present)"
assert_eq "NULL"    "$(node_lens "$EID_C" process)"       "conflicting lens process is left NULL"
# Exactly one GAP-CONFLICT row for the process lens.
assert_eq "1" "$(count_conflict_gaps "$EID_C")" "exactly one GAP-CONFLICT-…-process row raised"
echo "$MERGE_OUT_C" | grep -q "conflicts (gaps raised): 1" \
  && ok "merge summary reports 1 conflict" || bad "merge summary did not report 1 conflict"

# Idempotency: a second merge upserts the same conflict row (no duplicate).
"$PY" "$MERGE" merge --engagement "$EID_C" >/dev/null 2>&1
assert_eq "1" "$(count_conflict_gaps "$EID_C")" "conflict row STABLE on re-merge (upsert, no duplicate)"

# =============================================================================
echo "================================================================"
echo "ITEM 3: phantom evidence ref (#L9999) rejected at merge  ($EID_D)"
echo "================================================================"
"$PY" "$SM" init --engagement "$EID_D" --region NA >/dev/null
"$PY" "$INGEST" ingest --engagement "$EID_D" --source "$FIX/close_walkthrough.vtt" >/dev/null
CLOSE_REL_D="$(ingested_close_rel "$EID_D")"
mkdir -p "engagements/$EID_D/classify"

# An artifact whose evidence ref cites a line FAR past the end of the MD.
"$PY" - "engagements/$EID_D/classify" "$CLOSE_REL_D" <<'PY'
import json, sys
from pathlib import Path
outdir, rel = Path(sys.argv[1]), sys.argv[2]
art = {
    "doc": {"source": rel, "doc_type": "transcript",
            "classified_at": "2026-06-21T00:00:00Z"},
    "node_hits": [{
        "node": "record-to-report.close",
        "confidence": "high",
        "rationale": "Close walkthrough with an out-of-range evidence ref.",
        "evidence": [
            {"ref": f"{rel}#L9999",
             "quote": "phantom line that does not exist in the source",
             "note": "out-of-range ref"},
        ],
        "lens_signals": [
            {"lens": "current_state", "value": "present", "confidence": "high",
             "evidence_ref": f"{rel}#L9999", "rationale": "phantom ref"},
        ],
    }],
}
(outdir / "phantom.artifact.json").write_text(json.dumps(art, indent=2))
print("wrote phantom-ref artifact")
PY

# (3a) the standalone validator the merge delegates to rejects the phantom ref.
VOUT="$("$PY" "$VALIDATE" validate --artifact "engagements/$EID_D/classify/phantom.artifact.json" --engagement "$EID_D" 2>&1)"
VRC=$?
assert_eq "1" "$VRC" "validate_artifact rejects the phantom ref (exit 1)"
echo "$VOUT" | grep -q "L9999" && echo "$VOUT" | grep -qi "only .* line" \
  && ok "validator reports the out-of-range line (#L9999 vs file length)" \
  || bad "validator did not report the out-of-range line: $VOUT"

# (3b) the MERGE reports it: the phantom artifact is SKIPPED (not merged) and the
#      out-of-range line is named in the skip reason. The node lens is NOT set
#      from the rejected artifact.
MERGE_OUT_D="$("$PY" "$MERGE" merge --engagement "$EID_D" 2>&1)"
echo "$MERGE_OUT_D" | sed 's/^/    /'
echo "$MERGE_OUT_D" | grep -q "skipped (invalid): 1" \
  && ok "merge skipped the phantom-ref artifact (skipped invalid=1)" \
  || bad "merge did not skip the phantom-ref artifact"
echo "$MERGE_OUT_D" | grep -q "SKIP phantom.artifact.json" \
  && ok "merge reports the rejected artifact by name (SKIP phantom.artifact.json)" \
  || bad "merge did not report the rejected artifact by name"
assert_eq "NULL" "$(node_lens "$EID_D" current_state)" \
  "rejected artifact did NOT leak its lens into state"

# =============================================================================
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
[ "$FAIL" -ne 0 ] && exit 1
echo "ALL T49 CLASSIFY-CONTRACT ASSERTIONS PASS."
exit 0
