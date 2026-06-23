#!/usr/bin/env bash
# =============================================================================
# test_docx_comments_edge.sh — T47 edge-case tests for scripts/docx_comments.py
#
# Builds minimal .docx packages (stdlib zip) and asserts:
#   1. An UNBALANCED comment range (a commentRangeStart with no matching
#      commentRangeEnd) does NOT vacuum the trailing body text into that
#      comment's anchored_text (the unbalanced-range guard, fix 5).
#   2. A comment anchored only in a HEADER part (word/header1.xml) is NOT
#      extracted — the documented headers/footers/footnotes limitation (fix 6).
#
# No engagement state is touched; scratch .docx files use __t47__ ids and are
# removed at the end.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
DOCX="scripts/docx_comments.py"
WORK="$(mktemp -d -t __t47__docx.XXXXXX)"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "T47 docx_comments edge tests (work=$WORK)"

# --- build the two scratch .docx packages via a stdlib python helper ---------
"$PY" - "$WORK" <<'PY'
import sys, zipfile
from pathlib import Path

work = Path(sys.argv[1])
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
    '</Types>'
)
RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)

def comments_xml(*, cid, author, text):
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:comments xmlns:w="{W}">'
        f'<w:comment w:id="{cid}" w:author="{author}" w:date="2026-06-23T00:00:00Z">'
        f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>'
        f'</w:comment></w:comments>'
    )

def run(t):
    return f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'

def write_docx(path, document_xml, comments, extra=None):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/comments.xml", comments)
        for name, data in (extra or {}).items():
            z.writestr(name, data)

# --- (1) unbalanced range: start id=0, NO end. A second balanced comment id=1
#         exists later so we can prove the guard is per-id (1 still works).
doc_unbalanced = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:document xmlns:w="{W}"><w:body><w:p>'
    f'<w:commentRangeStart w:id="0"/>'
    f'{run("ANCHOR-ZERO")}'
    # note: NO commentRangeEnd for id 0 (unbalanced)
    f'{run("TRAILING-LEAK-SENTINEL")}'
    f'<w:commentRangeStart w:id="1"/>'
    f'{run("ANCHOR-ONE")}'
    f'<w:commentRangeEnd w:id="1"/>'
    f'<w:r><w:commentReference w:id="1"/></w:r>'
    f'{run("AFTER-ALL")}'
    f'</w:p></w:body></w:document>'
)
comments_two = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:comments xmlns:w="{W}">'
    f'<w:comment w:id="0" w:author="R" w:date="2026-06-23T00:00:00Z"><w:p><w:r><w:t>c0</w:t></w:r></w:p></w:comment>'
    f'<w:comment w:id="1" w:author="R" w:date="2026-06-23T00:00:00Z"><w:p><w:r><w:t>c1</w:t></w:r></w:p></w:comment>'
    f'</w:comments>'
)
write_docx(work / "unbalanced.docx", doc_unbalanced, comments_two)

# --- (2) header-anchored comment. The comment range/reference for id=0 lives
#         only in word/header1.xml; document.xml body has no anchor for it.
doc_no_anchor = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:document xmlns:w="{W}"><w:body><w:p>{run("PLAIN BODY TEXT")}</w:p></w:body></w:document>'
)
header_xml = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:hdr xmlns:w="{W}"><w:p>'
    f'<w:commentRangeStart w:id="0"/>'
    f'{run("HEADER-ANCHOR-TEXT")}'
    f'<w:commentRangeEnd w:id="0"/>'
    f'<w:r><w:commentReference w:id="0"/></w:r>'
    f'</w:p></w:hdr>'
)
write_docx(work / "header.docx",
           doc_no_anchor,
           comments_xml(cid="0", author="R", text="header comment"),
           extra={"word/header1.xml": header_xml})
print("built")
PY

# --- assertions: drive extract --json and inspect the output -----------------
UNB_JSON="$("$PY" "$DOCX" extract --docx "$WORK/unbalanced.docx" --json 2>/dev/null)"
HDR_JSON="$("$PY" "$DOCX" extract --docx "$WORK/header.docx" --json 2>/dev/null)"

# (1a) the unbalanced id 0 must NOT have vacuumed the trailing sentinel.
LEAK="$("$PY" - <<PY
import json
data = json.loads('''$UNB_JSON''')
rows = data["comments"] if isinstance(data, dict) else data
c0 = next((c for c in rows if c["id"] == "0"), None)
print("MISSING" if c0 is None else c0.get("anchored_text",""))
PY
)"
case "$LEAK" in
  *TRAILING-LEAK-SENTINEL*) bad "unbalanced range leaked trailing text into id 0 (got: $LEAK)";;
  *) ok "unbalanced range did NOT mis-attribute trailing text to id 0 (anchored=$LEAK)";;
esac

# (1b) the balanced id 1 still extracts its own anchor correctly.
ONE="$("$PY" - <<PY
import json
data = json.loads('''$UNB_JSON''')
rows = data["comments"] if isinstance(data, dict) else data
c1 = next((c for c in rows if c["id"] == "1"), None)
print("MISSING" if c1 is None else c1.get("anchored_text",""))
PY
)"
case "$ONE" in
  ANCHOR-ONE) ok "balanced comment id 1 still anchored correctly (=$ONE)";;
  *) bad "balanced comment id 1 anchor wrong (expected ANCHOR-ONE, got: $ONE)";;
esac

# (2) header-anchored comment id 0 is extracted as a comment (it's in
#     comments.xml) but its anchored_text must be EMPTY — the header anchor is
#     out of scope, so no header text leaks in.
HDR_ANCHOR="$("$PY" - <<PY
import json
data = json.loads('''$HDR_JSON''')
rows = data["comments"] if isinstance(data, dict) else data
c0 = next((c for c in rows if c["id"] == "0"), None)
print("MISSING" if c0 is None else repr(c0.get("anchored_text","")))
PY
)"
case "$HDR_ANCHOR" in
  *HEADER-ANCHOR-TEXT*) bad "header-anchored text WAS extracted (out-of-scope violated): $HDR_ANCHOR";;
  "''"|"\"\"") ok "header-anchored comment NOT extracted (anchored_text empty, limitation holds)";;
  *) ok "header-anchored comment NOT extracted (no header text in anchor: $HDR_ANCHOR)";;
esac

echo "----------------------------------------------------------------"
echo "RESULT: $PASS passed, $FAIL failed."
echo "----------------------------------------------------------------"
[ "$FAIL" -eq 0 ] || exit 1
echo "ALL DOCX EDGE ASSERTIONS PASS."
exit 0
