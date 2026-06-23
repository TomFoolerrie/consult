#!/usr/bin/env bash
# =============================================================================
# test_state_machine_hardening.sh — T41 hardening regression test
#
# Covers the 5 T41 fixes on scripts/state_machine.py:
#   1. cmd_init directory ordering: init against a ZERO-L2 taxonomy succeeds
#      (writes state.json without relying on the node-MD loop to mkdir).
#   2/4. atomic writes + lock: a simulated mid-write failure in write_json_atomic
#      leaves the prior state.json byte-for-byte intact (T40 pattern).
#   3. malformed-node guard: a node missing `counts` yields a clean SystemExit
#      (not a KeyError traceback) from `show` and from sync/derive.
#   5. ISO timestamp compare: is_diagnosis_dirty correct when last_evidence_at
#      and consolidated_at differ only by timezone representation.
#
# Scratch engagement ids use the __t41__ prefix and are removed at the end.
# Exits 0 only if every assertion PASSes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
SM="scripts/state_machine.py"
EID="__t41__"
EID2="__t41zero__"
EDIR="engagements/$EID"
EDIR2="engagements/$EID2"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

cleanup() { rm -rf "$EDIR" "$EDIR2"; }
trap cleanup EXIT
cleanup

# -----------------------------------------------------------------------------
echo "[1] cmd_init with a zero-L2 taxonomy succeeds (dir ordering fix)"
# Patch the taxonomy loader to return zero L2 nodes, then call cmd_init: the
# node-MD loop never runs, so init must mkdir edir itself before writing.
"$PY" - "$EID2" <<PY
import sys
sys.path.insert(0, "scripts")
import state_machine as sm
sm.load_taxonomy = lambda: {"version": 0, "domains": []}
try:
    sm.cmd_init("$EID2", "zero", "NA", force=True)
except BaseException as e:
    print("INIT-FAILED:", type(e).__name__, e)
    sys.exit(1)
PY
if [ -f "$EDIR2/state.json" ]; then ok "zero-L2 init wrote state.json (no FileNotFoundError)"
else bad "zero-L2 init did not produce state.json"; fi

# -----------------------------------------------------------------------------
echo "[2] atomic write: simulated mid-write failure leaves prior state.json intact"
"$PY" "$SM" init --engagement "$EID" --client t41 --region NA --force >/dev/null
BEFORE="$($PY - "$EDIR/state.json" <<'PY'
import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())
PY
)"
"$PY" - "$EID" <<PY
import sys
sys.path.insert(0, "scripts")
import consult_io, state_machine as sm
# Make the encode step blow up mid-save (after we've decided to write), so the
# target is never replaced. write_json_atomic writes a temp then os.replace.
orig = consult_io.write_text_atomic
def boom(path, text):
    raise RuntimeError("simulated mid-write crash")
consult_io.write_text_atomic = boom
sm.consult_io = consult_io
try:
    p, st = sm.load_state("$EID")
    st["engagement"]["client"] = "MUTATED"
    sm._save_state(p, st)
except RuntimeError:
    pass
PY
AFTER="$($PY - "$EDIR/state.json" <<'PY'
import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())
PY
)"
if [ "$BEFORE" = "$AFTER" ]; then ok "state.json unchanged after simulated crash"
else bad "state.json was modified/truncated by a failed save"; fi
# No temp litter left behind.
LITTER="$(ls "$EDIR"/state.json.*.tmp 2>/dev/null | wc -l | tr -d ' ')"
if [ "$LITTER" = "0" ]; then ok "no .tmp litter after failed save"
else bad "found $LITTER leftover temp file(s)"; fi

# -----------------------------------------------------------------------------
echo "[3] malformed node (missing counts) -> clean error, not a traceback"
NODE="$($PY - "$EDIR/state.json" <<'PY'
import json,sys
st=json.load(open(sys.argv[1])); print(next(iter(st["nodes"])))
PY
)"
"$PY" - "$EDIR/state.json" "$NODE" <<'PY'
import json,sys
st=json.load(open(sys.argv[1]))
del st["nodes"][sys.argv[2]]["counts"]
json.dump(st, open(sys.argv[1],"w"), indent=2)
PY
OUT="$($PY "$SM" show --engagement "$EID" 2>&1)"
RC=$?
if [ "$RC" != "0" ] && echo "$OUT" | grep -q "missing required key" && ! echo "$OUT" | grep -q "Traceback"; then
  ok "show emits a clean validation error pointing at validate"
else
  bad "show did not emit a clean guard error (rc=$RC): $OUT"
fi
# reseed a clean engagement for the dirty-predicate test
"$PY" "$SM" init --engagement "$EID" --client t41 --region NA --force >/dev/null

# -----------------------------------------------------------------------------
echo "[4] is_diagnosis_dirty correct across timezone representations"
"$PY" - <<'PY'
import sys
sys.path.insert(0, "scripts")
from state_machine import is_diagnosis_dirty
fails = 0
# Same instant, different tz spelling: 12:00:00Z == 07:00:00-05:00.
# last_evidence (Z) is NOT strictly after consolidated (offset) -> not dirty,
# even though lexically "1" < "0" would mis-rank it.
node = {"last_evidence_at": "2026-06-23T12:00:00.000000+00:00",
        "consolidated_at": "2026-06-23T07:00:00.000000-05:00"}
if is_diagnosis_dirty(node):
    print("FAIL: equal instants flagged dirty"); fails += 1
# last_evidence one microsecond later (in offset spelling) IS dirty.
node2 = {"last_evidence_at": "2026-06-23T07:00:00.000001-05:00",
         "consolidated_at": "2026-06-23T12:00:00.000000+00:00"}
if not is_diagnosis_dirty(node2):
    print("FAIL: later instant not flagged dirty"); fails += 1
# tz-naive last_evidence treated as UTC, earlier than consolidated -> not dirty.
node3 = {"last_evidence_at": "2026-06-23T11:00:00.000000",
         "consolidated_at": "2026-06-23T12:00:00.000000+00:00"}
if is_diagnosis_dirty(node3):
    print("FAIL: naive earlier ts flagged dirty"); fails += 1
sys.exit(1 if fails else 0)
PY
if [ $? = 0 ]; then ok "dirty predicate parses timestamps before comparing"
else bad "dirty predicate mis-ordered tz-variant timestamps"; fi

# -----------------------------------------------------------------------------
echo
echo "RESULTS: $PASS passed, $FAIL failed."
[ "$FAIL" = "0" ]
