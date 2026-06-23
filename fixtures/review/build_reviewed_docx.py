#!/usr/bin/env python3
"""build_reviewed_docx.py — (re)generate the committed Slice-2 reviewed .docx fixture.

The Slice-2 regression (tests/test_slice2_e2e.sh) drives a *committed*, reviewed
Word document through docx_comments.py -> review_ingest.py. To keep the path
deterministic (no live LLM), the .docx itself is checked into the repo as a
binary fixture; this helper exists only to regenerate it byte-for-byte if it ever
needs to change. The bytes — not this script — are what the test consumes.

The package is a minimal-but-real OOXML word document carrying two tracked
comments, each anchored to a span of body text:

  * comment id 0 (Reviewer A) — anchors a sentence about the close automation
    lens; the resolver turns it into a `set-lens` override.
  * comment id 1 (Reviewer B) — anchors a sentence about a missing control;
    the resolver turns it into an `add-evidence` on the same node.

Both comments hang off the `record-to-report.close` node so the test can assert
the dirtied set, the applied substance actions, and the final gate against a
single, well-known node. The resolver actions themselves live in the test (they
stand in for the human/LLM comment-resolver step, exactly like Slice-1's canned
classify/consolidate outputs).

Usage:  build_reviewed_docx.py [--out PATH]   (default: alongside this file)
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

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


def run(t: str) -> str:
    return f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'


def document_xml() -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}"><w:body>'
        f'<w:p>{run("Record to Report — Close — Desktop Procedures (reviewed draft).")}</w:p>'
        # comment 0 anchors the automation-lens sentence.
        f'<w:p>'
        f'<w:commentRangeStart w:id="0"/>'
        f'{run("Accruals are keyed by hand each close; the automation lens should read human, not mixed.")}'
        f'<w:commentRangeEnd w:id="0"/>'
        f'<w:r><w:commentReference w:id="0"/></w:r>'
        f'</w:p>'
        # comment 1 anchors the missing-control sentence.
        f'<w:p>'
        f'<w:commentRangeStart w:id="1"/>'
        f'{run("The dual-review control over reconciliations above $50k is attested verbally but not documented anywhere.")}'
        f'<w:commentRangeEnd w:id="1"/>'
        f'<w:r><w:commentReference w:id="1"/></w:r>'
        f'</w:p>'
        f'</w:body></w:document>'
    )


def comments_xml() -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:comments xmlns:w="{W}">'
        f'<w:comment w:id="0" w:author="Reviewer A" w:date="2026-06-23T00:00:00Z">'
        f'<w:p><w:r><w:t>Automation lens is wrong — accruals are fully manual. Set it to human.</w:t></w:r></w:p>'
        f'</w:comment>'
        f'<w:comment w:id="1" w:author="Reviewer B" w:date="2026-06-23T00:00:00Z">'
        f'<w:p><w:r><w:t>Add the verbal-attestation evidence for this control so it is on the record.</w:t></w:r></w:p>'
        f'</w:comment>'
        f'</w:comments>'
    )


def build(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    # Deterministic bytes: fixed ZipInfo dates so the committed fixture is stable.
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (
            ("[Content_Types].xml", CONTENT_TYPES),
            ("_rels/.rels", RELS),
            ("word/document.xml", document_xml()),
            ("word/comments.xml", comments_xml()),
        ):
            info = zipfile.ZipInfo(name, date_time=(2026, 6, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenerate the committed Slice-2 reviewed .docx fixture.")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent / "rtr_close_reviewed.docx")
    args = ap.parse_args()
    build(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
