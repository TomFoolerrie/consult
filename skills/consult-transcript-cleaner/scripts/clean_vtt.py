#!/usr/bin/env python3
"""clean_vtt.py — VTT/SRT transcript cleaner (CONSULT transcript-cleaner skill).

Strips caption artifacts (WEBVTT header, timestamps, cue ids, hash cue keys),
collapses `<v Speaker>` tags into `**Speaker:** text` segments, merges
consecutive same-speaker lines, and drops very short filler turns.

`clean_text(raw: str) -> str` is the pure entry point (in-memory, no temp files):
it returns ONLY the cleaned `**Speaker:** text` body — no front matter. The
ingest pipeline (ingest_normalize.handle_transcript) imports this directly and
adds its own YAML header, so emitting front matter here would only be stripped.

Standalone CLI (kept usable): `clean_vtt.py INPUT [OUTPUT]` reads INPUT and
writes the cleaned body to OUTPUT (or stdout).
"""
import re
import sys

TIMESTAMP_RE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?\s*-->\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?.*$")
HASH_RE = re.compile(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}/\d+-\d+\s*$")
ARTIFACT_RE = re.compile(r"^\s*(WEBVTT|Kind:\s*captions|Language:.*|\d+)\s*$")
SPEAKER_TAG_RE = re.compile(r"<v ([^>]+)>(.*?)</v>", re.DOTALL)
OPEN_TAG_RE = re.compile(r"<v ([^>]+)>")
CLOSE_TAG_RE = re.compile(r"</v>")


def is_filler(text):
    return text.lower().strip(" .") in {"so", "sure thing", "okay", "ok", "yeah", "yes", "right", "great", "uh", "um", "alright", "all right", "sure", "yep", ""}


def clean_text(raw: str) -> str:
    """Clean a raw VTT/SRT transcript string into a `**Speaker:** text` body.

    Pure: no file I/O, no front matter. Returns the cleaned body (no trailing
    newline guaranteed; callers strip/wrap as needed)."""
    lines = raw.splitlines()

    # First pass: extract (speaker, text) segments, joining split lines
    segments = []
    current_speaker = None
    current_text = []

    for line in lines:
        line = line.rstrip()

        # Skip WEBVTT header, timestamps, cue IDs, blank lines
        if not line:
            continue
        if ARTIFACT_RE.match(line):
            continue
        if TIMESTAMP_RE.match(line):
            continue
        if HASH_RE.match(line):
            continue

        # Check for speaker tag
        m = SPEAKER_TAG_RE.match(line)
        if m:
            # Flush previous
            if current_text:
                segments.append((current_speaker, " ".join(current_text).strip()))
                current_text = []
            current_speaker = m.group(1).strip()
            text = m.group(2).strip()
            if text:
                current_text.append(text)
            continue

        # Opening tag only (text wraps to next line)
        m2 = OPEN_TAG_RE.match(line)
        if m2:
            if current_text:
                segments.append((current_speaker, " ".join(current_text).strip()))
                current_text = []
            current_speaker = m2.group(1).strip()
            remainder = line[m2.end():].replace("</v>", "").strip()
            if remainder:
                current_text.append(remainder)
            continue

        # Close tag
        cleaned = CLOSE_TAG_RE.sub("", line).strip()
        if cleaned:
            current_text.append(cleaned)

    if current_text:
        segments.append((current_speaker, " ".join(current_text).strip()))

    # Second pass: merge consecutive lines from same speaker, remove short filler
    merged = []
    for speaker, text in segments:
        if is_filler(text):
            continue
        if merged and merged[-1][0] == speaker:
            merged[-1] = (speaker, merged[-1][1] + " " + text)
        else:
            merged.append([speaker, text])

    lines_out = [f"**{speaker}:** {text}" for speaker, text in merged]
    return "\n\n".join(lines_out)


def clean_file(input_path: str, output_path: str = None) -> str:
    """Read a transcript file, clean it, and write the body to output_path (or
    return it if output_path is None)."""
    with open(input_path, "r", encoding="utf-8") as f:
        raw = f.read()
    body = clean_text(raw)
    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(body + "\n")
    return body


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        sys.stderr.write("usage: clean_vtt.py INPUT [OUTPUT]\n")
        return 2
    input_path = argv[0]
    output_path = argv[1] if len(argv) > 1 else None
    body = clean_file(input_path, output_path)
    if output_path is None:
        sys.stdout.write(body + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
