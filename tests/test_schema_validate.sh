#!/usr/bin/env bash
# =============================================================================
# test_schema_validate.sh — T49 item 1: schema-validation assertion
#
# The Slice-1 e2e never ran `state_machine.py validate`, so produced state.json /
# register.json were never asserted schema-conformant. This drives the
# deterministic classify spine on the synthesized R2R fixture (init -> ingest ->
# canned classify artifacts -> merge -> a confirmed improvement carrying the
# fixture's intentionally OFF-VOCAB values: effort=medium, priority=high,
# impact_type=cycle_time) and then asserts schema conformance.
#
# DESIGN NOTE (the fixture-vocab issue T50 warned about):
#   `state_machine.py validate` schema-checks STATE.json (against
#   engagement_state.schema.json) — that is clean and we assert it passes
#   --strict. It does NOT schema-check REGISTER.json. The register schema is
#   *intentionally* permissive: it says "the script flags unknown enum values for
#   human review rather than rejecting them." The Slice-1 fixture uses the
#   ergonomic-but-off-vocab values effort=medium / priority=high /
#   impact_type=cycle_time, which ARE register-schema violations. The correct,
#   contract-faithful behavior is therefore the SOFT one: improvement_log flags
#   the row requires_human_review, surfaced in `status.needs_human`. So rather
#   than mutate the canonical fixture to be schema-clean (which would hide the
#   soft-validation path), we ASSERT the soft-validation behavior:
#     * state.json validates --strict (hard gate),
#     * register.json's off-vocab row is flagged requires_human_review (soft gate),
#     * that same row IS a register-schema violation (proving the soft path is
#       doing real work, not a vacuous pass).
#
# Scratch engagement __t49a__ is removed at the end. Exits 0 only if every
# assertion passes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t49a__"
EDIR="engagements/$EID"
FIX="fixtures/r2r"
SM="scripts/state_machine.py"
INGEST="scripts/ingest_normalize.py"
MERGE="scripts/classify_merge.py"
BUILD_CANNED="$FIX/canned/build_canned.py"
OFFVOCAB_ID="IMP-RTR-CLOSE-ACCRUALS"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi; }

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT
cleanup

echo "T49 item 1 — schema-validation assertion  (engagement=$EID)"

# --- drive the deterministic classify spine ----------------------------------
"$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
"$PY" "$INGEST" ingest --engagement "$EID" \
  --source "$FIX/close_walkthrough.vtt" "$FIX/recon_walkthrough.txt" >/dev/null
"$PY" "$BUILD_CANNED" --engagement "$EID" >/dev/null
"$PY" "$MERGE" merge --engagement "$EID" >/dev/null

# A confirmed improvement carrying the fixture's OFF-VOCAB values (same triple the
# Slice-1 e2e uses). These are register-schema violations on purpose.
"$PY" "$SM" add-item --engagement "$EID" --type improvement \
  --l1 record-to-report --l2 close \
  --id "$OFFVOCAB_ID" \
  --field "dedup_key=$OFFVOCAB_ID" \
  --field "tag=automation" \
  --field "observation_pain_point=Accruals are re-keyed every close." \
  --field "recommended_action=Automate recurring accrual journals." \
  --field "impact_type=cycle_time" \
  --field "effort=medium" \
  --field "priority=high" \
  --field "owner=Controller" \
  >/dev/null

# =============================================================================
echo "----------------------------------------------------------------"
echo "1. state.json is schema-conformant (validate --strict, HARD gate)"
echo "----------------------------------------------------------------"
VOUT="$("$PY" "$SM" validate --engagement "$EID" --strict 2>&1)"
VRC=$?
echo "$VOUT" | sed 's/^/    /'
assert_eq "0" "$VRC" "state_machine.py validate --strict exits 0 (state.json schema-clean + coherent)"
echo "$VOUT" | grep -q "Schema: OK" && ok "validate confirms state.json validates against schema" \
  || bad "validate did not confirm state.json schema OK"
echo "$VOUT" | grep -q "all citations resolve" && ok "validate confirms coherence (citations + lenses)" \
  || bad "validate did not confirm coherence"

# =============================================================================
echo "----------------------------------------------------------------"
echo "2. register.json off-vocab row IS a schema violation (proves soft path)"
echo "----------------------------------------------------------------"
REG_ERRS="$("$PY" - "$EDIR/register.json" "schemas/item_register.schema.json" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import state_machine as sm
errs = sm.schema_check(json.load(open(sys.argv[1])), Path(sys.argv[2]))
# Print only the off-vocab enum errors (skip the informational "(skipped …)" note).
hits = [e for e in errs if "not one of" in e and
        any(f in e for f in ("effort", "priority", "impact_type"))]
print(len(hits))
for h in hits:
    print("   ", h, file=sys.stderr)
PY
2>/tmp/reg_errs_$$ )"
sed 's/^/    /' "/tmp/reg_errs_$$" 2>/dev/null; rm -f "/tmp/reg_errs_$$"
# The fixture vocab DOES violate the register schema (effort/priority/impact_type).
if [ "$REG_ERRS" -ge 3 ] 2>/dev/null; then
  ok "register off-vocab values violate item_register.schema.json (effort/priority/impact_type; =$REG_ERRS)"
else
  bad "expected >=3 register schema violations from the off-vocab row, got $REG_ERRS"
fi

# =============================================================================
echo "----------------------------------------------------------------"
echo "3. soft-validation: the off-vocab row is flagged requires_human_review"
echo "----------------------------------------------------------------"
# Contract: unknown/invalid enum values are NON-FATAL — the row is flagged for
# human review (improvement_log) and surfaced by status.needs_human, NOT rejected.
RHR_FLAGGED="$("$PY" - "$EDIR/register.json" "$OFFVOCAB_ID" <<'PY'
import json, sys
sys.path.insert(0, "scripts")
import state_machine as sm
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
r = next((x for x in rows if x.get("id") == sys.argv[2]), None)
print("FLAGGED" if (r is not None and sm._is_truthy_flag(r.get("requires_human_review"))) else "NOT")
PY
)"
assert_eq "FLAGGED" "$RHR_FLAGGED" "off-vocab improvement row flagged requires_human_review (soft, not rejected)"

# the same row is surfaced by status.needs_human (the orchestrator's human-loop signal).
IN_STATUS="$("$PY" - "$EID" "$OFFVOCAB_ID" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
      "status", "--engagement", sys.argv[1], "--json"])
ids = json.loads(out)["needs_human"]["requires_human_review"]["ids"]
print("YES" if sys.argv[2] in ids else "NO")
PY
)"
assert_eq "YES" "$IN_STATUS" "off-vocab row surfaced in status.needs_human.requires_human_review"

# =============================================================================
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
[ "$FAIL" -ne 0 ] && exit 1
echo "ALL T49 SCHEMA-VALIDATE ASSERTIONS PASS."
exit 0
