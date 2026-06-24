#!/usr/bin/env bash
# test_consolidator_inline_apply.sh — T57 Part 1 Decision-B mechanics.
#
# Drives the COMMAND PATH the new (inline-apply) consolidator contract prescribes,
# deterministically — no LLM agent is spawned. It exercises exactly the calls the
# inline worker now makes itself:
#
#   1. add-item a confirmed finding  -> asserts it MINTS an IMP-/GAP- id.
#   2. confirm an MD that cites that EXISTING id is COHERENT (validate passes,
#      ID-before-citation holds: the id exists before the MD cites it).
#   3. mark-consolidated stamps consolidated_at (clears diagnosis-dirty).
#   4. a node left WITHOUT mark-consolidated stays diagnosis-dirty
#      (last_evidence_at > consolidated_at) — a failed node is cleanly
#      re-derivable, never half-applied.
#
# Isolated scratch engagement; trap-cleaned on EXIT.
set -u
cd "$(dirname "$0")/.." || exit 2

EID="__t57p1_consol__"
SM="python3 scripts/state_machine.py"
EDIR="engagements/${EID}"
PASS=0
FAIL=0

cleanup() { rm -rf "${EDIR}"; }
trap cleanup EXIT

ok()   { echo "  ok   - $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL - $1"; FAIL=$((FAIL+1)); }

# --- setup: scratch engagement -------------------------------------------------
$SM init --engagement "$EID" --client "T57P1 scratch" --force >/dev/null 2>&1 \
  || { echo "FAIL: init failed"; exit 2; }

# Pick two real taxonomy nodes (deterministic: first two L2 keys).
mapfile -t NODES < <($SM query --engagement "$EID" --l1 record-to-report 2>/dev/null | head -2)
if [ "${#NODES[@]}" -lt 2 ]; then
  # fall back to any two node keys from state
  mapfile -t NODES < <(python3 - "$EDIR/state.json" <<'PY'
import json,sys
st=json.load(open(sys.argv[1]))
for k in list(st["nodes"])[:2]:
    print(k)
PY
)
fi
NODE_APPLIED="${NODES[0]}"
NODE_FAILED="${NODES[1]}"
L1="${NODE_APPLIED%%.*}"
L2="${NODE_APPLIED#*.}"
echo "scratch engagement=$EID  applied-node=$NODE_APPLIED  failed-node=$NODE_FAILED"

# Seed evidence so both nodes are diagnosis-dirty (last_evidence_at set,
# consolidated_at still null -> is_diagnosis_dirty true).
$SM add-evidence --engagement "$EID" --node "$NODE_APPLIED" \
  --source "ingested/seed.md" --loc "L1-2" --note "seed" --tier verbal >/dev/null 2>&1
$SM add-evidence --engagement "$EID" --node "$NODE_FAILED" \
  --source "ingested/seed.md" --loc "L1-2" --note "seed" --tier verbal >/dev/null 2>&1

# --- 1. add-item mints an IMP- id ---------------------------------------------
OUT=$($SM add-item --engagement "$EID" --type improvement --l1 "$L1" --l2 "$L2" \
  --field dedup_key="${NODE_APPLIED}|improvement|manual-accruals" \
  --field tag=automation \
  --field source="ingested/seed.md#L1-2" \
  --field evidence_tier=verbal \
  --field observation_pain_point="Manual accrual uploads" \
  --field recommended_action="Automate accrual upload" 2>&1)
MINTED_ID=$(printf '%s\n' "$OUT" | grep -oE 'IMP-[0-9]{4}' | head -1)
if [ -n "$MINTED_ID" ]; then
  ok "add-item minted a register id ($MINTED_ID)"
else
  bad "add-item did not mint an IMP- id (out: $OUT)"
fi

# Confirm the id is actually a register row (mint is real, not just printed).
if [ -n "$MINTED_ID" ] && grep -q "\"$MINTED_ID\"" "$EDIR/register.json"; then
  ok "minted id $MINTED_ID is a real register row"
else
  bad "minted id not found in register.json"
fi

# --- 2. author node MD citing the EXISTING id, then validate coherence ---------
# ID-before-citation: the id already exists (step 1) before the MD cites it.
NODE_MD=$(python3 - "$EDIR/state.json" "$NODE_APPLIED" <<'PY'
import json,sys
st=json.load(open(sys.argv[1])); print(st["nodes"][sys.argv[2]]["node_md"])
PY
)
LENSES_BLOCK=$(python3 - "$EDIR/state.json" "$NODE_APPLIED" <<'PY'
import json,sys
st=json.load(open(sys.argv[1])); n=st["nodes"][sys.argv[2]]
for lens in ["current_state","process","automation","capability","operating_model"]:
    v=n["lenses"].get(lens)
    if v is not None:
        print(f"- **{lens}:** {v}")
PY
)
mkdir -p "$(dirname "$EDIR/$NODE_MD")"
cat > "$EDIR/$NODE_MD" <<EOF
---
node: ${NODE_APPLIED}
---

# ${NODE_APPLIED}

## What we learned
Accrual processing on this node is manual and worth automating.

## Evidence digest
See ingested/seed.md#L1-2.

## Diagnosis (5 lenses)
${LENSES_BLOCK}

## Open items
- ${MINTED_ID} — automate the manual accrual upload.
EOF

# Coherence: validate must report ZERO dangling citations (the cited id exists).
VAL=$($SM validate --engagement "$EID" --coherence-only 2>&1)
# The cited id must NOT appear in a "<id> not in register" dangling line.
if printf '%s\n' "$VAL" | grep -qE "${MINTED_ID} not in register"; then
  bad "coherence flagged the cited (existing) id $MINTED_ID as dangling: $VAL"
elif printf '%s\n' "$VAL" | grep -qE "0 dangling citation"; then
  ok "MD cites existing id $MINTED_ID; coherence reports 0 dangling citations"
else
  bad "coherence reported dangling citations with the id present: $VAL"
fi

# Negative control: an MD citing a NON-existent id should be flagged. This proves
# the coherence check is actually live (so the positive result above is meaningful).
cat >> "$EDIR/$NODE_MD" <<EOF
- IMP-9999 — bogus, never minted.
EOF
VAL2=$($SM validate --engagement "$EID" --coherence-only 2>&1)
if printf '%s\n' "$VAL2" | grep -qE "IMP-9999"; then
  ok "coherence check is live (flags the bogus IMP-9999)"
else
  bad "coherence did not flag a clearly-invented id IMP-9999 (check may be inert): $VAL2"
fi
# restore the clean MD (drop the bogus line) for the mark-consolidated step.
sed -i '/IMP-9999/d' "$EDIR/$NODE_MD"

# --- 3. mark-consolidated stamps consolidated_at ------------------------------
$SM mark-consolidated --engagement "$EID" --node "$NODE_APPLIED" >/dev/null 2>&1
DIRTY_APPLIED=$(python3 - "$EDIR/state.json" "$NODE_APPLIED" <<'PY'
import json,sys
st=json.load(open(sys.argv[1])); n=st["nodes"][sys.argv[2]]
le=n.get("last_evidence_at"); ca=n.get("consolidated_at")
# diagnosis-dirty iff last_evidence_at > consolidated_at (or ca is None).
dirty = ca is None or (le is not None and le > ca)
print("dirty" if dirty else "clean")
print(f"  last_evidence_at={le} consolidated_at={ca}")
PY
)
if printf '%s\n' "$DIRTY_APPLIED" | head -1 | grep -q "^clean$"; then
  ok "applied node: mark-consolidated cleared diagnosis-dirty (consolidated_at >= last_evidence_at)"
else
  bad "applied node still diagnosis-dirty after mark-consolidated:"
  printf '%s\n' "$DIRTY_APPLIED" | tail -1
fi

# --- 4. failed node (no mark-consolidated) stays dirty / re-derivable ----------
# NODE_FAILED was seeded dirty and never mark-consolidated -> simulates a worker
# that died mid-apply. It must remain diagnosis-dirty (re-fans next round),
# never half-applied.
DIRTY_FAILED=$(python3 - "$EDIR/state.json" "$NODE_FAILED" <<'PY'
import json,sys
st=json.load(open(sys.argv[1])); n=st["nodes"][sys.argv[2]]
le=n.get("last_evidence_at"); ca=n.get("consolidated_at")
dirty = ca is None or (le is not None and le > ca)
print("dirty" if dirty else "clean")
PY
)
if printf '%s\n' "$DIRTY_FAILED" | grep -q "^dirty$"; then
  ok "failed node (no mark-consolidated): stays diagnosis-dirty -> cleanly re-derivable, not half-applied"
else
  bad "failed node is not diagnosis-dirty though never mark-consolidated"
fi

# --- summary -------------------------------------------------------------------
echo "----"
echo "consolidator inline-apply: PASS=$PASS FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then echo "FAIL"; exit 1; fi
echo "PASS"; exit 0
