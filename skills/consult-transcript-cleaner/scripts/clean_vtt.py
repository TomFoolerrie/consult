import re
import sys

input_path = "/mnt/user-data/uploads/PharmaEssentia___Financial_Reporting_Package_Walkthrough_.vtt"
output_path = "/mnt/user-data/outputs/2026-06-18_pharmaessentia-financial-reporting-package-walkthrough.cleaned.md"

with open(input_path, "r", encoding="utf-8") as f:
    raw = f.read()

lines = raw.splitlines()

TIMESTAMP_RE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?\s*-->\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?.*$")
HASH_RE = re.compile(r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}/\d+-\d+\s*$")
ARTIFACT_RE = re.compile(r"^\s*(WEBVTT|Kind:\s*captions|Language:.*|\d+)\s*$")
SPEAKER_TAG_RE = re.compile(r"<v ([^>]+)>(.*?)</v>", re.DOTALL)
OPEN_TAG_RE = re.compile(r"<v ([^>]+)>")
CLOSE_TAG_RE = re.compile(r"</v>")

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
        remainder = line[m2.end():].replace("</v>","").strip()
        if remainder:
            current_text.append(remainder)
        continue

    # Close tag
    cleaned = CLOSE_TAG_RE.sub("", line).strip()
    if cleaned:
        current_text.append(cleaned)

if current_text:
    segments.append((current_speaker, " ".join(current_text).strip()))

# Second pass: merge consecutive lines from same speaker, remove very short filler
def is_filler(text):
    return text.lower().strip(" .") in {"so", "sure thing", "okay", "ok", "yeah", "yes", "right", "great", "uh", "um", "alright", "all right", "sure", "yep", ""}

merged = []
for speaker, text in segments:
    if is_filler(text):
        continue
    if merged and merged[-1][0] == speaker:
        merged[-1] = (speaker, merged[-1][1] + " " + text)
    else:
        merged.append([speaker, text])

# Build markdown
front_matter = """---
source_file: "PharmaEssentia___Financial_Reporting_Package_Walkthrough_.vtt"
meeting_date: "TBD"
title: "PharmaEssentia Financial Reporting Package Walkthrough"
topics:
  - "financial reporting package"
  - "HQ reporting"
  - "month-end close"
  - "financial statement deliverables"
people:
  - "Robin Tornatore"
  - "Askew, Pete"
systems:
  - "TBD"
---

"""

lines_out = [front_matter]
for speaker, text in merged:
    lines_out.append(f"**{speaker}:** {text}\n")

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out))

print(f"Done. {len(merged)} segments written.")
