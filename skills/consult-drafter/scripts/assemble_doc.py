#!/usr/bin/env python3
"""
assemble_doc.py — stitch component .md files back into one process document.

Reads manifest.json (written by split_doc.py) for component order. If no manifest
is present, falls back to sorting files by name, which works because split_doc.py
prefixes every file with a zero-padded index.

Usage:
    python3 assemble_doc.py IN_DIR REBUILT.md
"""

import json
import os
import sys


def ordered_files(in_dir):
    manifest_path = os.path.join(in_dir, "manifest.json")
    if os.path.exists(manifest_path):
        data = json.load(open(manifest_path, encoding="utf-8"))
        return [c["file"] for c in data["components"]]
    # Fallback: every .md sorted by name (numeric prefixes keep order).
    out = []
    for root, _, files in os.walk(in_dir):
        for fn in files:
            if fn.endswith(".md"):
                out.append(os.path.relpath(os.path.join(root, fn), in_dir))
    return sorted(out)


def main(in_dir, out_path):
    parts = []
    for rel in ordered_files(in_dir):
        path = os.path.join(in_dir, rel)
        if not os.path.exists(path):
            print(f"  [warn] missing component listed in manifest: {rel}")
            continue
        parts.append(open(path, encoding="utf-8").read().strip("\n"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")
    print(f"Assembled {len(parts)} component(s) -> {out_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
