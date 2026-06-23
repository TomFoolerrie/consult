#!/usr/bin/env bash
# =============================================================================
# test_ingest_hardening.sh — T43 ingest_normalize.py hardening tests.
#
# Asserts the 6 hardening fixes:
#   1. transcript ingest reuses clean_vtt.clean_text() (imported, no exec):
#      the ingested MD body equals the imported clean()'s output.
#   3. ingesting a dir that already contains ingested/ does NOT re-ingest its
#      own MD (output excluded from the source sweep).
#   4. one malformed file in a batch is reported but the batch completes the
#      rest (per-file error isolation). T52 extends this with Test 4b: an
#      unsupported file passed *by path* (the SystemExit hole T43 missed) is
#      now quarantined as IngestError, not allowed to kill the batch.
#   5. a CSV cell with an embedded newline renders a valid 1-row Markdown table
#      (newline collapsed to <br>, not a broken multiline row).
#
# Scratch engagement uses a __t43__ id and is removed at the end. No git commit.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t43__"
EDIR="engagements/$EID"
INGEST="scripts/ingest_normalize.py"
WORK="$EDIR/.t43_src"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT

echo "T43 ingest hardening tests  (engagement=$EID)"
cleanup
mkdir -p "$WORK"

# --- fixtures ---------------------------------------------------------------
VTT="$WORK/sample.vtt"
cat > "$VTT" <<'VTT'
WEBVTT

00:00:00.000 --> 00:00:05.000
<v Alice>Hello, this is the kickoff for the close walkthrough.</v>

00:00:05.000 --> 00:00:07.000
<v Bob>Okay</v>

00:00:07.000 --> 00:00:12.000
<v Bob>The accruals are keyed by hand into the ERP every month.</v>
VTT

# CSV whose second column contains an embedded newline.
CSV="$WORK/notes.csv"
printf 'name,detail\n' > "$CSV"
printf 'Accruals,"line one\nline two"\n' >> "$CSV"

# A malformed file: an empty .docx (not a valid zip) — handler will raise.
BADDOCX="$WORK/broken.docx"
printf 'not a real docx' > "$BADDOCX"

# -----------------------------------------------------------------------------
# Test 1: transcript body == imported clean_vtt.clean_text() output (no exec).
# -----------------------------------------------------------------------------
"$PY" "$INGEST" ingest --engagement "$EID" --source "$VTT" >/dev/null 2>&1

MD="$(ls "$EDIR"/ingested/*.transcript.*.md 2>/dev/null | head -1)"
if [ -z "$MD" ]; then
  bad "transcript ingest produced an MD"
else
  ok "transcript ingest produced an MD"
  MATCH="$("$PY" - "$VTT" "$MD" <<'PY'
import sys, re
sys.path.insert(0, "skills/consult-transcript-cleaner/scripts")
import clean_vtt
raw = open(sys.argv[1], encoding="utf-8").read()
expected = clean_vtt.clean_text(raw).strip()
md = open(sys.argv[2], encoding="utf-8").read()
# strip YAML front matter + the leading "# Title" heading to isolate the body.
m = re.match(r"^---\n.*?\n---\n+# .*?\n\n(.*)$", md, re.DOTALL)
body = (m.group(1) if m else md).strip()
print("YES" if body == expected else "NO")
# also assert filler ("Okay") was stripped — proves the cleaning behavior ran.
print("FILLER_GONE" if "Okay" not in body else "FILLER_PRESENT")
PY
)"
  case "$MATCH" in
    *YES*) ok "ingested body equals imported clean_text() output" ;;
    *)     bad "ingested body equals imported clean_text() output" ;;
  esac
  case "$MATCH" in
    *FILLER_GONE*) ok "filler turn stripped (cleaning behavior preserved)" ;;
    *)             bad "filler turn stripped (cleaning behavior preserved)" ;;
  esac
fi

# -----------------------------------------------------------------------------
# Test 5: CSV cell with embedded newline -> valid single-row Markdown table.
# -----------------------------------------------------------------------------
"$PY" "$INGEST" ingest --engagement "$EID" --source "$CSV" >/dev/null 2>&1
CSVMD="$(ls "$EDIR"/ingested/*.csv.*.md 2>/dev/null | head -1)"
if [ -z "$CSVMD" ]; then
  bad "csv ingest produced an MD"
else
  ok "csv ingest produced an MD"
  TBL_OK="$("$PY" - "$CSVMD" <<'PY'
import sys
md = open(sys.argv[1], encoding="utf-8").read()
rows = [l for l in md.splitlines() if l.startswith("|")]
# header + separator + exactly one data row (newline collapsed, not split).
data = [r for r in rows if "---" not in r]
ok = (len(rows) == 3 and len(data) == 2 and "<br>" in md
      and all(r.count("|") == 3 for r in rows))
print("OK" if ok else f"BAD rows={rows}")
PY
)"
  case "$TBL_OK" in
    OK) ok "embedded-newline CSV renders one valid table row (<br>-collapsed)" ;;
    *)  bad "embedded-newline CSV renders one valid table row ($TBL_OK)" ;;
  esac
fi

# -----------------------------------------------------------------------------
# Test 3: ingesting the engagement dir does NOT re-ingest its own ingested/*.md.
# -----------------------------------------------------------------------------
BEFORE="$(ls "$EDIR"/ingested/*.md 2>/dev/null | wc -l | tr -d ' ')"
OUT="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$EDIR" 2>&1)"
AFTER="$(ls "$EDIR"/ingested/*.md 2>/dev/null | wc -l | tr -d ' ')"
# a swept source is the left-hand side of "-> "; assert none is under ingested/.
if echo "$OUT" | sed 's/ ->.*//' | grep -q "ingested/"; then
  bad "engagement-dir ingest did not sweep ingested/*.md (it did)"
else
  ok "engagement-dir ingest skipped its own ingested/ subtree"
fi
# the .vtt/.csv under .t43_src are re-seen but dedup'd (skipped), no new MDs.
if [ "$BEFORE" = "$AFTER" ]; then
  ok "no new MDs written when re-ingesting the engagement dir (dedup holds)"
else
  bad "no new MDs written when re-ingesting the engagement dir (before=$BEFORE after=$AFTER)"
fi

# -----------------------------------------------------------------------------
# Test 4: one malformed file in a batch is reported, batch completes the rest.
# -----------------------------------------------------------------------------
TXT="$WORK/plain.txt"
printf 'Just a plain note about the process.\n' > "$TXT"
OUT2="$("$PY" "$INGEST" ingest --engagement "$EID" \
        --source "$BADDOCX" "$TXT" 2>&1)" ; RC=$?
TXTMD="$(ls "$EDIR"/ingested/*.text.*.md 2>/dev/null | head -1)"
if echo "$OUT2" | grep -qi "failed"; then
  ok "malformed file reported as a failure"
else
  bad "malformed file reported as a failure (output: $OUT2)"
fi
if [ -n "$TXTMD" ]; then
  ok "good file in the same batch still ingested (per-file isolation)"
else
  bad "good file in the same batch still ingested (per-file isolation)"
fi
if [ "$RC" -ne 0 ]; then
  ok "batch with a failure exits non-zero"
else
  bad "batch with a failure exits non-zero (rc=$RC)"
fi

# -----------------------------------------------------------------------------
# Test 4b (T52): the SystemExit path T43's corrupt-docx test missed. An
# unsupported file passed *by path* used to make dispatch() raise SystemExit
# (a BaseException), which escaped the loop's `except Exception` and KILLED the
# whole batch. It must now quarantine that one file (IngestError) and write the
# good ones. `--source good.txt weird.pdf good2.txt` => both good files written,
# weird.pdf reported FAILED/unsupported, batch not aborted, non-zero exit.
# -----------------------------------------------------------------------------
GOOD1="$WORK/iso_good1.txt"; printf 'First good note for isolation.\n' > "$GOOD1"
GOOD2="$WORK/iso_good2.txt"; printf 'Second good note for isolation.\n' > "$GOOD2"
WEIRD="$WORK/weird.pdf";     printf '%%PDF-1.4 fake\n' > "$WEIRD"
OUT3="$("$PY" "$INGEST" ingest --engagement "$EID" \
        --source "$GOOD1" "$WEIRD" "$GOOD2" 2>&1)" ; RC3=$?
G1MD="$(ls "$EDIR"/ingested/*iso-good1*.md 2>/dev/null | head -1)"
G2MD="$(ls "$EDIR"/ingested/*iso-good2*.md 2>/dev/null | head -1)"
if [ -n "$G1MD" ] && [ -n "$G2MD" ]; then
  ok "both good files written despite an unsupported-by-path file (SystemExit hole closed)"
else
  bad "both good files written despite an unsupported-by-path file (G1=$G1MD G2=$G2MD)"
fi
if echo "$OUT3" | grep -qi "weird.pdf" && echo "$OUT3" | grep -qi -e "unsupported" -e "FAILED"; then
  ok "unsupported-by-path file reported (FAILED/unsupported), batch not aborted"
else
  bad "unsupported-by-path file reported (output: $OUT3)"
fi
if [ "$RC3" -ne 0 ]; then
  ok "batch with an unsupported-by-path file exits non-zero"
else
  bad "batch with an unsupported-by-path file exits non-zero (rc=$RC3)"
fi

# --- summary ----------------------------------------------------------------
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
if [ "$FAIL" -ne 0 ]; then exit 1; fi
echo "ALL T43 ASSERTIONS PASS."
exit 0
