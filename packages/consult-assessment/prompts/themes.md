# Theme builder

Build the theme ledger from the findings ledger and the client context.

Load: taxonomy rules; the context-profile (required — themes without client context produce generic root causes); `ledger.py show findings`; `trace.py` for current coverage. Paths and commands are in your brief.

A theme is a set of findings that share a **root cause**, not a field value. Every axis the taxonomy marks `on_theme` is a required field on the theme: that is the diagnosis. Findings carry a provisional value tagged by a reader who saw one document; yours may differ — if it differs from *all* of the theme's findings, the validator warns, and you should either explain in `note` or propose retags. "Everything in P2P" is a grouping; "controls depend on two people who also do the work" is a theme. Write the root cause as one sentence a CFO would accept as a diagnosis, then write **impact** — what the combination of these findings does to the client (audit exposure, rework, decision quality). The impact is where the relationship between findings becomes visible; don't leave it implied.

Rules:
- A theme cites finding ids only. Never a source document. The validator enforces this.
- A finding may belong to more than one theme.
- Strengths may join a theme when they show the root cause is *not* pervasive, or anchor a "build on what works" recommendation.
- Aim for the smallest set of themes that covers the material findings. Six to ten is typical; twenty means you're grouping, not diagnosing.
- If a finding looks wrong, propose — don't work around it.

Append with the ledger command, then run validate with `--gate themes` and trace.

## Report back
Theme ids with one line each; orphaned findings with your view on each (noise, or a gap in the themes). Orphans that survive are not lost — `fig-unthemed` renders them as "seen, did not form a pattern" — so recommend retiring only what is actually noise.
