#!/usr/bin/env bash
# =============================================================================
# test_ingest_robustness.sh — T52 ingest robustness / graceful-degradation.
#
# Cross-links to tests/test_ingest_hardening.sh (T43/T52 Test 4b), which owns
# the headline per-file-isolation regression (unsupported-by-path SystemExit
# hole). This file covers the rest of the T52 surface:
#
#   Tier 1
#     - collision-refusal is per-file (IngestError), not a fatal SystemExit.
#     - a bad path among many doesn't abort the batch; all-bad still prints
#       "No supported source files found." and exits non-zero.
#     - an explicitly-passed unsupported file is skipped, not crashed.
#     - symlink guard: a symlink into an ingested/ tree is not followed.
#   Tier 2
#     - .docx omission marker (image + numbered list) is stable; re-ingesting
#       the same bytes is still a dedup skip (marker didn't break immutability).
#     - empty-body guard: all-blank CSV -> FAILED, no hollow MD; sticky on re-run.
#     - encoding fallback: a cp1252 smart-quote file decodes without U+FFFD and
#       is reported as a non-utf-8 fallback; a clean utf-8 file and a UTF-8-BOM
#       CSV are byte-identical to pre-ticket output (immutability preserved).
#
# Scratch engagement uses a __t52__ id and is removed at the end. No git commit.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t52__"
EDIR="engagements/$EID"
INGEST="scripts/ingest_normalize.py"
WORK="$EDIR/.t52_src"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT

echo "T52 ingest robustness tests  (engagement=$EID)"
cleanup
mkdir -p "$WORK"

# =============================================================================
# Tier 1 #2: a bad (missing) path among many — good files written, missing path
# reported, non-zero exit. Then the all-bad case keeps the existing contract.
# =============================================================================
A="$WORK/alpha.txt"; printf 'Alpha note about the close.\n' > "$A"
B="$WORK/bravo.txt"; printf 'Bravo note about reconciliations.\n' > "$B"
OUT="$("$PY" "$INGEST" ingest --engagement "$EID" \
       --source "$A" "$WORK/does-not-exist.txt" "$B" 2>&1)" ; RC=$?
AMD="$(ls "$EDIR"/ingested/*alpha*.md 2>/dev/null | head -1)"
BMD="$(ls "$EDIR"/ingested/*bravo*.md 2>/dev/null | head -1)"
if [ -n "$AMD" ] && [ -n "$BMD" ]; then
  ok "bad path among many: both good files still written"
else
  bad "bad path among many: both good files still written (A=$AMD B=$BMD)"
fi
if echo "$OUT" | grep -qi "does-not-exist.txt" && echo "$OUT" | grep -qi "not found"; then
  ok "missing path reported as not-found"
else
  bad "missing path reported as not-found (output: $OUT)"
fi
if [ "$RC" -ne 0 ]; then
  ok "batch with a missing source exits non-zero"
else
  bad "batch with a missing source exits non-zero (rc=$RC)"
fi

# all-bad: every source missing -> "No supported source files found.", non-zero.
OUT_ALLBAD="$("$PY" "$INGEST" ingest --engagement "$EID" \
              --source "$WORK/nope1.txt" "$WORK/nope2.txt" 2>&1)" ; RC_AB=$?
if echo "$OUT_ALLBAD" | grep -q "No supported source files found." && [ "$RC_AB" -ne 0 ]; then
  ok "all-bad case prints 'No supported source files found.' and exits non-zero"
else
  bad "all-bad case contract (output: $OUT_ALLBAD rc=$RC_AB)"
fi

# =============================================================================
# Tier 1 #2: an explicitly-passed unsupported file is skipped, not crashed
# (mirrors the dir-scan filter; does not reach dispatch).
# =============================================================================
UNSUP="$WORK/data.bin"; printf 'binary-ish payload\n' > "$UNSUP"
GOODC="$WORK/charlie.txt"; printf 'Charlie note.\n' > "$GOODC"
OUTU="$("$PY" "$INGEST" ingest --engagement "$EID" \
        --source "$UNSUP" "$GOODC" 2>&1)" ; RCU=$?
CMD="$(ls "$EDIR"/ingested/*charlie*.md 2>/dev/null | head -1)"
if echo "$OUTU" | grep -qi "data.bin" && echo "$OUTU" | grep -qi -e "unsupported" -e "skip"; then
  ok "explicit unsupported file is skipped (not crashed)"
else
  bad "explicit unsupported file is skipped (output: $OUTU)"
fi
if [ -n "$CMD" ] && [ "$RCU" -ne 0 ]; then
  ok "good file alongside an unsupported file still written; exit non-zero"
else
  bad "good file alongside an unsupported file still written (C=$CMD rc=$RCU)"
fi

# =============================================================================
# Tier 1 #1 (collision-refusal is per-file, not fatal):
#   ingest A (writes A.md) -> mutate that MD's header source_hash to a different
#   value (so find_existing_for_hash no longer matches but output_name still
#   collides) -> re-ingest A together with a sibling good file B2.
#   Assert: A -> FAILED (collision), B2 -> written, batch not aborted.
# =============================================================================
COL="$WORK/collide.txt"; printf 'Collision recipe source body.\n' > "$COL"
"$PY" "$INGEST" ingest --engagement "$EID" --source "$COL" >/dev/null 2>&1
COLMD="$(ls "$EDIR"/ingested/*collide*.md 2>/dev/null | head -1)"
if [ -z "$COLMD" ]; then
  bad "collision recipe: initial ingest of A produced an MD"
else
  ok "collision recipe: initial ingest of A produced an MD"
  # Mutate the stored source_hash so the dir-dedup no longer matches, but the
  # output_name (date_slug.doctype.<short>.md) is still computed from the real
  # bytes -> the same filename collides on re-ingest.
  "$PY" - "$COLMD" <<'PY'
import re, sys
p = sys.argv[1]
t = open(p, encoding="utf-8").read()
t = re.sub(r"(source_hash: sha256:)[0-9a-f]+", r"\g<1>" + "0" * 64, t, count=1)
open(p, "w", encoding="utf-8").write(t)
PY
  B2="$WORK/sibling.txt"; printf 'Sibling good file for collision test.\n' > "$B2"
  OUTC="$("$PY" "$INGEST" ingest --engagement "$EID" \
          --source "$COL" "$B2" 2>&1)" ; RCC=$?
  SIBMD="$(ls "$EDIR"/ingested/*sibling*.md 2>/dev/null | head -1)"
  if echo "$OUTC" | grep -qi "FAILED" && echo "$OUTC" | grep -qi -e "overwrite" -e "Refusing"; then
    ok "collision-refusal reported as a per-file FAILED (not a fatal abort)"
  else
    bad "collision-refusal reported as a per-file FAILED (output: $OUTC)"
  fi
  if [ -n "$SIBMD" ]; then
    ok "sibling good file written despite the collision (batch not aborted)"
  else
    bad "sibling good file written despite the collision (batch not aborted)"
  fi
  if [ "$RCC" -ne 0 ]; then
    ok "collision batch exits non-zero"
  else
    bad "collision batch exits non-zero (rc=$RCC)"
  fi
fi

# =============================================================================
# Tier 1 #3 (symlink guard): a symlink under the source dir pointing into an
# ingested/ tree is not followed/ingested.
# =============================================================================
SYMDIR="$WORK/symdir"; mkdir -p "$SYMDIR"
printf 'Real file in the symdir.\n' > "$SYMDIR/real.txt"
# point a symlink at our own ingested/ dir (full of *.md the guard must not sweep)
ln -s "$REPO_ROOT/$EDIR/ingested" "$SYMDIR/sneaky" 2>/dev/null
OUTS="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$SYMDIR" 2>&1)"
# no swept source path may sit under a 'sneaky/' (the symlink) — i.e. not followed.
if echo "$OUTS" | sed 's/ ->.*//' | grep -q "sneaky/"; then
  bad "symlink into ingested/ was followed during dir recursion"
else
  ok "symlink into ingested/ not followed during dir recursion"
fi
# an explicitly-passed symlink is skipped with a warning, not followed.
SYMFILE="$WORK/link.txt"; ln -s "$SYMDIR/real.txt" "$SYMFILE" 2>/dev/null
OUTSF="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$SYMFILE" 2>&1)"
if echo "$OUTSF" | grep -qi "symlink"; then
  ok "explicitly-passed symlink source is skipped (not followed)"
else
  bad "explicitly-passed symlink source is skipped (output: $OUTSF)"
fi

# =============================================================================
# Tier 2 #4 (docx omission marker) — fixture built deterministically with
# python-docx (no committed binary): a paragraph, a numbered-list item, and an
# inline image. MD must carry the stable trailing marker; re-ingest is a skip.
# =============================================================================
DOCX="$WORK/omit.docx"
"$PY" - "$DOCX" <<'PY'
import sys, struct, zlib
from docx import Document
from docx.shared import Inches
import io

# A tiny deterministic 1x1 PNG (bytes fixed so the .docx zip content is stable).
def _png_1x1():
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00\xff\xff\xff"  # one white pixel, filter byte 0
    idat = zlib.compress(raw, 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")

doc = Document()
doc.add_paragraph("A plain body paragraph that survives ingest.")
doc.add_paragraph("First numbered item", style="List Number")
doc.add_paragraph("Second numbered item", style="List Number")
doc.add_picture(io.BytesIO(_png_1x1()), width=Inches(1))
doc.save(sys.argv[1])
PY
"$PY" "$INGEST" ingest --engagement "$EID" --source "$DOCX" >/dev/null 2>&1
DMD="$(ls "$EDIR"/ingested/*omit*.docx.*.md 2>/dev/null | head -1)"
if [ -z "$DMD" ]; then
  bad "docx omission: fixture ingested to an MD"
else
  ok "docx omission: fixture ingested to an MD"
  MK="$("$PY" - "$DMD" <<'PY'
import re, sys
md = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"<!-- ingest: (\d+) image\(s\), (\d+) list\(s\) flattened, (\d+) nested table\(s\) omitted -->", md)
if not m:
    print("NO_MARKER"); raise SystemExit
img, lst, nt = (int(x) for x in m.groups())
# expect >=1 image and >=2 flattened list paragraphs.
print("OK" if img >= 1 and lst >= 2 else f"COUNTS img={img} lst={lst} nt={nt}")
PY
)"
  case "$MK" in
    OK) ok "docx MD carries the stable omission marker (image + flattened lists)" ;;
    *)  bad "docx omission marker counts ($MK)" ;;
  esac
  # re-ingest the SAME bytes -> dedup skip (marker didn't break immutability).
  OUTRE="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$DOCX" 2>&1)"
  NMD="$(ls "$EDIR"/ingested/*omit*.docx.*.md 2>/dev/null | wc -l | tr -d ' ')"
  if echo "$OUTRE" | grep -qi "skipped" && [ "$NMD" = "1" ]; then
    ok "re-ingesting the same docx bytes is a dedup skip (immutability holds)"
  else
    bad "re-ingesting the same docx bytes is a dedup skip (out=$OUTRE n=$NMD)"
  fi
fi

# =============================================================================
# Tier 2 #5 (empty-body guard, sticky): an all-blank CSV -> FAILED, no hollow
# MD; a re-run reports it FAILED again (sticky behavior, not a regression).
# =============================================================================
EMPTY="$WORK/blank.csv"; printf ',,\n , ,\n,,\n' > "$EMPTY"
OUTE="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$EMPTY" 2>&1)" ; RCE=$?
EMD="$(ls "$EDIR"/ingested/*blank*.md 2>/dev/null | head -1)"
if echo "$OUTE" | grep -qi "FAILED" && echo "$OUTE" | grep -qi "no extractable text"; then
  ok "empty-body source reported FAILED ('no extractable text')"
else
  bad "empty-body source reported FAILED (output: $OUTE)"
fi
if [ -z "$EMD" ] && [ "$RCE" -ne 0 ]; then
  ok "no hollow MD written for an empty-body source; exit non-zero"
else
  bad "no hollow MD written for an empty-body source (MD=$EMD rc=$RCE)"
fi
# sticky: re-run still FAILED (nothing was written, so dir-dedup can't skip it).
OUTE2="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$EMPTY" 2>&1)" ; RCE2=$?
if echo "$OUTE2" | grep -qi "FAILED" && [ "$RCE2" -ne 0 ]; then
  ok "empty-body guard is sticky: re-run reports FAILED again (by design)"
else
  bad "empty-body guard is sticky (output: $OUTE2 rc=$RCE2)"
fi

# image-only docx (no extractable text): the omission marker must NOT rescue it
# into a hollow marker-only MD. It is an empty-extraction input -> FAILED with an
# actionable reason (needs separate preprocessing), no MD written.
IMGDOCX="$WORK/imgonly.docx"
"$PY" - "$IMGDOCX" <<'PY'
import sys, struct, zlib, io
from docx import Document
from docx.shared import Inches
def _png():
    sig=b"\x89PNG\r\n\x1a\n"
    def ch(t,d): c=t+d; return struct.pack(">I",len(d))+c+struct.pack(">I",zlib.crc32(c)&0xffffffff)
    ihdr=struct.pack(">IIBBBBB",1,1,8,2,0,0,0); idat=zlib.compress(b"\x00\xff\xff\xff",9)
    return sig+ch(b"IHDR",ihdr)+ch(b"IDAT",idat)+ch(b"IEND",b"")
d=Document(); d.add_picture(io.BytesIO(_png()), width=Inches(1)); d.save(sys.argv[1])  # no text
PY
OUTIM="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$IMGDOCX" 2>&1)" ; RCIM=$?
IMMD="$(ls "$EDIR"/ingested/*imgonly*.md 2>/dev/null | head -1)"
if echo "$OUTIM" | grep -qi "FAILED" && echo "$OUTIM" | grep -qi "no extractable text" \
   && [ -z "$IMMD" ] && [ "$RCIM" -ne 0 ]; then
  ok "image-only docx fails loudly (no hollow marker-only MD written)"
else
  bad "image-only docx fails loudly (out=$OUTIM md=$IMMD rc=$RCIM)"
fi

# =============================================================================
# Tier 2 #6 (encoding fallback): a cp1252 file with smart quotes / em dash
# decodes without U+FFFD and is reported as a non-utf-8 fallback.
# =============================================================================
CP="$WORK/smart.txt"
"$PY" - "$CP" <<'PY'
import sys
# “smart quotes”, an em — dash, and a bullet •, encoded as cp1252 (not utf-8).
s = "“Smart quotes” and an em — dash, bullet • done.\n"
open(sys.argv[1], "wb").write(s.encode("cp1252"))
PY
OUTCP="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$CP" 2>&1)"
CPMD="$(ls "$EDIR"/ingested/*smart*.md 2>/dev/null | head -1)"
if [ -z "$CPMD" ]; then
  bad "cp1252 encoding: file ingested to an MD"
else
  ok "cp1252 encoding: file ingested to an MD"
  NOREPL="$("$PY" - "$CPMD" <<'PY'
import sys
md = open(sys.argv[1], encoding="utf-8").read()
print("CLEAN" if "�" not in md and "“" in md and "—" in md else "DIRTY")
PY
)"
  case "$NOREPL" in
    CLEAN) ok "cp1252 smart quotes decoded without U+FFFD (no silent corruption)" ;;
    *)     bad "cp1252 smart quotes decoded without U+FFFD ($NOREPL)" ;;
  esac
  if echo "$OUTCP" | grep -qi "non-utf-8"; then
    ok "non-utf-8 fallback surfaced as a warning"
  else
    bad "non-utf-8 fallback surfaced as a warning (output: $OUTCP)"
  fi
fi

# =============================================================================
# Tier 2 #6 (byte-identity): a clean utf-8 file and a UTF-8-BOM CSV produce the
# SAME body the pre-ticket decode path would (no marker, no spurious warning,
# BOM stripped). We assert: utf-8 file has no fallback warning + no marker; the
# BOM-CSV's first cell has no leading BOM char.
# =============================================================================
CLEANTXT="$WORK/clean.txt"; printf 'Just clean ascii text, nothing fancy.\n' > "$CLEANTXT"
OUTCL="$("$PY" "$INGEST" ingest --engagement "$EID" --source "$CLEANTXT" 2>&1)"
CLMD="$(ls "$EDIR"/ingested/*clean*.md 2>/dev/null | head -1)"
if [ -n "$CLMD" ] && ! echo "$OUTCL" | grep -qi "non-utf-8" && ! grep -q "<!-- ingest:" "$CLMD"; then
  ok "clean utf-8 file: no fallback warning, no omission marker (unchanged output)"
else
  bad "clean utf-8 file unchanged-output check (out=$OUTCL md=$CLMD)"
fi

BOMCSV="$WORK/bom.csv"
"$PY" - "$BOMCSV" <<'PY'
import sys
open(sys.argv[1], "wb").write("﻿name,detail\nAlpha,first\n".encode("utf-8"))
PY
"$PY" "$INGEST" ingest --engagement "$EID" --source "$BOMCSV" >/dev/null 2>&1
BOMMD="$(ls "$EDIR"/ingested/*bom*.csv.*.md 2>/dev/null | head -1)"
if [ -z "$BOMMD" ]; then
  bad "UTF-8-BOM CSV ingested to an MD"
else
  NOBOM="$("$PY" - "$BOMMD" <<'PY'
import re, sys
md = open(sys.argv[1], encoding="utf-8").read()
# first table cell must be "name", NOT "﻿name" (BOM stripped via utf-8-sig).
first = next((l for l in md.splitlines() if l.startswith("|")), "")
print("OK" if "﻿" not in md and first.split("|")[1].strip() == "name" else f"BAD first={first!r}")
PY
)"
  case "$NOBOM" in
    OK) ok "UTF-8-BOM CSV: BOM stripped (cell[0][0] is 'name', not '\\ufeffname')" ;;
    *)  bad "UTF-8-BOM CSV BOM stripping ($NOBOM)" ;;
  esac
fi

# --- summary ----------------------------------------------------------------
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
if [ "$FAIL" -ne 0 ]; then exit 1; fi
echo "ALL T52 ASSERTIONS PASS."
exit 0
