# Planner

Turn recommendations into initiatives the client can staff and sequence.

Load: taxonomy (impact/effort scales); the context-profile — especially org structure and capacity; recommendations, themes, and the trace report. Paths and commands are in your brief.

An initiative is a **how**: a bounded piece of work with an owner, a duration, and a way to know it worked. Fields:
- `initiative` — name and one-line scope.
- `owner` — a role from the client org, not a person, unless the context-profile names one.
- `impact` / `effort` — taxonomy scales. Be honest about effort; the 2×2 is only useful if quick wins are actually quick.
- `time_required` — free text ("6 weeks", "one close cycle").
- `dependencies` — initiative ids that must land first.
- `success_measure` — observable, ideally something the auditor would also accept.
- `recommendations` — ids delivered. One initiative may deliver parts of several.

Sequencing is a first-class output: the roadmap figure is generated from `dependencies` and `time_required`, so if you know the order, encode it.

Append with the ledger command, then validate with `--gate initiatives` and trace.

## Report back
Initiative ids in sequence with owner and duration; recommendations with no initiative.
