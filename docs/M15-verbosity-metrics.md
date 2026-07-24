# M15 — Verbosity: measured, not capped

> **Status: DESIGNED.** Smallest of the four; deliberately does less than the
> original proposal (hard word caps + reconcile warnings), for the reasons below.

## Goal

Make document bloat **visible and actionable** without governing prose by word
budgets — so the human can point at the one procedure that is 3× its neighbours
and tell that drafter to tighten, instead of every drafter writing to a cap.

## Why

An earlier proposal was measurable caps (step body ≤ N words, impact ≤ 1
sentence, reconcile warns on excess). The reasoning was right — "be brief" is
not reproducible — but the instrument was wrong for the main case:

- The real bloat drivers are **structural**, and are already governed: restating
  a fact in several sections ("say it once, in its home section") and mechanical
  over-tagging ("inline tags by judgment"). Those rules are about a section's
  *role*, which is why they work.
- A cap on step bodies buys little and costs real things: artificial
  step-splitting to duck the limit, drafters spending judgment on compliance
  instead of clarity, gameable compliance (three short sentences, same words),
  and a stream of warnings to triage.
- Bloat is **relative**. The signal is not "step > 60 words", it is "this
  procedure is far heavier than its peers in the same area".
- Much of *perceived* verbosity is presentation: the same content as tagged
  bullets reads tight. Rendering already fixed a good part of this.

So: measure and report; cap only where a number is a **definition** rather than
a limit.

## Design

### 1. Metrics (report only — no gate, no warning)

`python3 scripts/stats.py <area>` (also folded into the `render` handler's
summary so the human sees it without asking):

Per procedure: total words; longest step (words); words per A–H section; callout
counts by kind; inline-tag density (tags per step). Per area: the **median** of
each, and **outliers flagged at ≥2× the area median** (and, for total words,
≥2× or ≤0.4× — a suspiciously thin procedure is as interesting as a fat one).

Output is a compact table, plus one line per outlier naming the metric and the
ratio. No exit-code consequence, ever — this never blocks a render.

### 2. Bounded field caps (definitions, kept in the drafter contract)

These stay prose-level rules in the drafter prompt, not machine checks, because
they define a field's job:

- `A. Process Overview` — 3–5 sentences (already present and working: it defines
  A as *orient, don't inform*).
- `Impact:` — one sentence.
- `Severity:` — enum (already mechanically validated).
- Never restate the section title as the first clause of its body.

### 3. What is deliberately NOT built

- Word caps on step bodies.
- Reconcile warnings for length. Reconcile stays the correctness gate; making it
  a style gate dilutes the signal that currently means "something is broken".

### Optional: a structural `brief | standard | full` knob

If a verbosity setting is wanted later, define it **structurally** in the M14
profile — which inline tags are in play, whether `H` is callouts-only — never as
a word budget. Mechanically enforceable, and it cannot degrade prose quality.

## Acceptance

- `stats.py` on the live area prints per-procedure and area-median metrics and
  flags the known-heaviest procedure as an outlier.
- Exit code is 0 on every input that parses; a malformed fragment is reported
  and skipped, never fatal.
- Adding it changes no fragment, no derived view, and no advisor decision.
- The render handler's summary includes the outlier lines (and nothing else new).

## Out of scope

- Any enforcement, gating, or automatic drafter dispatch from metrics.
- Cross-area comparison (medians are only meaningful within an area's subject
  matter).
- Readability scores — no evidence they track what a preparer needs.
