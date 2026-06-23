#!/usr/bin/env bash
# =============================================================================
# test_xlsx_snapshot.sh — T49 item 5: xlsx snapshot path
#
# T50 removed pandas; build_xlsx is now openpyxl-based. This is a minimal
# assertion that `improvement_log.py build-xlsx` produces a VALID, openable
# workbook: build a register (init -> a couple of add-item rows), build the XLSX,
# then round-trip it through openpyxl.load_workbook and assert structure:
#   * the workbook opens (no corruption),
#   * it has the "Item Register" sheet,
#   * the header row carries the register field columns (incl. id/type),
#   * there is exactly one data row per active register record,
#   * the cell values round-trip (a known id appears in column A).
#
# Scratch engagement __t49e__ is removed at the end. Exits 0 only if every
# assertion passes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t49e__"
EDIR="engagements/$EID"
SM="scripts/state_machine.py"
ILOG="skills/consult-improvement-log/scripts/improvement_log.py"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi; }

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT
cleanup

echo "T49 item 5 — xlsx snapshot (openpyxl build_xlsx)  (engagement=$EID)"

# --- build a small register --------------------------------------------------
"$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
"$PY" "$SM" add-item --engagement "$EID" --type improvement \
  --l1 record-to-report --l2 close --id IMP-XLSX-1 \
  --field "dedup_key=IMP-XLSX-1" --field "tag=automation" \
  --field "observation_pain_point=Manual accruals." \
  --field "recommended_action=Automate." >/dev/null
"$PY" "$SM" add-item --engagement "$EID" --type gap \
  --l1 record-to-report --l2 close --id GAP-XLSX-1 \
  --field "dedup_key=GAP-XLSX-1" \
  --field "observation_pain_point=Undocumented control." >/dev/null

XLSX="$EDIR/.t49e_register.xlsx"
BUILD_OUT="$("$PY" "$ILOG" build-xlsx --json "$EDIR/register.json" --xlsx "$XLSX" 2>&1)"
BRC=$?
echo "$BUILD_OUT" | sed 's/^/    /'
assert_eq "0" "$BRC" "build-xlsx exits 0"
assert_eq "0" "$([ -s "$XLSX" ] && echo 0 || echo 1)" "xlsx file produced and non-empty"

# --- round-trip the workbook through openpyxl --------------------------------
RESULT="$("$PY" - "$XLSX" "$EDIR/register.json" <<'PY'
import json, sys
from openpyxl import load_workbook

xlsx, regjson = sys.argv[1], sys.argv[2]
errs = []

# (1) opens without corruption.
wb = load_workbook(xlsx)

# (2) has the Item Register sheet.
if "Item Register" not in wb.sheetnames:
    errs.append(f"missing 'Item Register' sheet (got {wb.sheetnames})")
ws = wb["Item Register"]

# (3) header row carries id + type columns.
header = [c.value for c in ws[1]]
for col in ("id", "type"):
    if col not in header:
        errs.append(f"header missing '{col}' column (header={header})")

# (4) one data row per active register record.
reg = json.load(open(regjson))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
ARCHIVED = {"archived", "inactive", "deleted_candidate", "deleted"}
active = [r for r in rows
          if str(r.get("record_status", "active") or "active").lower() not in ARCHIVED]
n_data = ws.max_row - 1  # minus header
if n_data != len(active):
    errs.append(f"data rows {n_data} != active records {len(active)}")

# (5) a known id round-trips into column A.
id_idx = header.index("id") + 1
col_ids = {ws.cell(row=r, column=id_idx).value for r in range(2, ws.max_row + 1)}
for want in ("IMP-XLSX-1", "GAP-XLSX-1"):
    if want not in col_ids:
        errs.append(f"id {want} not found in workbook (got {sorted(col_ids)})")

if errs:
    print("FAIL: " + " | ".join(errs))
else:
    print(f"OK rows={n_data}")
PY
)"
echo "    $RESULT"
case "$RESULT" in
  OK\ rows=*) ok "workbook round-trips (opens, Item Register sheet, header, rows, ids)";;
  *)          bad "workbook round-trip failed: $RESULT";;
esac

echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
[ "$FAIL" -ne 0 ] && exit 1
echo "ALL T49 XLSX SNAPSHOT ASSERTIONS PASS."
exit 0
