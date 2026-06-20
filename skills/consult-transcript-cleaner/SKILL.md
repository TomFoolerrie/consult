---
name: consult-transcript-cleaner
description: Clean raw transcripts and walkthrough notes into structured Markdown source files for SOP drafting.
---

# Transcript Cleaner Skill

description: Token-light Python skill that converts transcript input files into clean Markdown with YAML front matter and descriptive dated filenames.

## Purpose

Use Python to clean raw transcripts / walkthrough notes into concise, source-preserving Markdown files for SOP drafting.

## Use When

Input contains transcript artifacts such as timestamps, cue IDs, hashes, meeting-platform text, repeated speakers, caption line breaks, filler, or raw walkthrough notes.

Do not use for SOP drafting, audit evidence drafting, or comment resolution.

## Required Behavior

When invoked, run a Python script that:

1. Reads each input file.
2. Extracts text from supported formats: `.txt`, `.vtt`, `.srt`, `.md`, `.csv`, `.docx`, `.tsv`.
3. Removes transcript noise.
5. Writes a clean `.md` file.

## Cleaning Rules

Remove / normalize:

- WEBVTT/SRT headers, sequence numbers, cue IDs
- timestamps: `00:01:23 --> 00:01:27`, `[00:01:23]`, `(00:01:23)`, transcript-only time markers
- caption metadata: `align:start`, `position:`, `line:`
- hashes / generated IDs: long hex strings, UUIDs, MD5/SHA-like strings, random 40+ char tokens
- meeting artifacts: joined/left, recording started/stopped, reactions, auto-caption notices
- excessive repeated speaker labels
- line wrapping inside sentences
- excess whitespace / blank lines

## Recommended Python Patterns

```python
TIMESTAMP_PATTERNS = [
    r"^\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?\s*-->\s*\d{1,2}:\d{2}:\d{2}(?:[.,]\d{1,3})?.*$",
    r"^\s*\d{1,2}:\d{2}(?:[.,]\d{1,3})?\s*-->\s*\d{1,2}:\d{2}(?:[.,]\d{1,3})?.*$",
    r"\[\s*\d{1,2}:\d{2}(?::\d{2})?\s*\]",
    r"\(\s*\d{1,2}:\d{2}(?::\d{2})?\s*\)",
]
HASH_PATTERNS = [
    r"\b[a-fA-F0-9]{32,128}\b",
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
    r"\b[A-Za-z0-9_-]{40,}\b",
]
ARTIFACT_PATTERNS = [
    r"^\s*WEBVTT\s*$",
    r"^\s*Kind:\s*captions\s*$",
    r"^\s*Language:\s*.*$",
    r"^\s*\d+\s*$",
    r"^\s*(recording started|recording stopped|joined the meeting|left the meeting).*$",
]
```

## Output Filename

Name each output file:

```text
YYYY-MM-DD_descriptive-topic.cleaned.md
```

Rules:

- Use the meeting / transcript date if found.
- If no date is found, use the file modified date or current date.
- Build `descriptive-topic` from likely process / topic words, limited to 3-7 lowercase slug words.
- Remove stopwords and unsafe filename characters.
- Example: `2026-06-18_month-end-close-walkthrough.cleaned.md`

## YAML Front Matter

Each Markdown file must start with YAML front matter:

```yaml
---
source_file: "original filename.ext"
meeting_date: "YYYY-MM-DD or TBD"
title: "Short descriptive title"
topics:
  - "topic 1"
people:
  - "Name or Speaker"
systems:
  - "System name or TBD"
---
```

Keep YAML values brief. Use `TBD` when uncertain. Do not invent details. You generate this from the python cleaned Markdown file. 

## Final Instruction

After cleaning, present each dated Markdown file with YAML front matter.
