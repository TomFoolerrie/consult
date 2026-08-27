# the worker classes — model shells that load a skill (CONTRACT STUB)

**The distinction, ruled 2026-08-26: AGENTS pin model (and skills);
what we called templates ARE SKILLS — skills with agency.** A worker class is a thin shell that
pins exactly one thing — its model — and loads the skill it is handed.
All behavior, boundary, and license come from the skill. Three classes:

| class | model | for |
|---|---|---|
| `worker-haiku`  | cheap    | bounded reads, mechanical edits, small drafts |
| `worker-sonnet` | mid      | first drafts, structured analysis of modest feeds |
| `worker-opus`   | strong   | assessment under license, hard synthesis, review-with-edits passes |

The consultant picks CLASS and SKILL independently per dispatch — two
dials, not one: the same `procedure-draft` skill may run on haiku for a
mechanical update and on opus for a hard first draft; the same class may
run any skill. Cost estimates price the pair.

## Mission (all classes)
Execute exactly one skilled unit of work against the material the brief
resolves, and return exactly what the skill's return contract names.
Nothing outside the skill's write boundary, ever.

## What you need
One skill + parameters, composed into a brief by `brief.compose`.
Reading the brief is always the first action.

## Context provided (by the brief, never hunted for)
The resolved facts for this unit: files/sources in scope, register slices,
the consultant's standing precedent and open observations (from its
state pad), the objective's framing, the skill's rules
verbatim.

## What you return
The skill's return contract — a file written (if the skill grants
one) or structured grounded material — plus out-of-lane OBSERVATIONS
returned to the consultant, who logs them in its state pad (A9).
Never judgment the skill didn't license.

## Skills — skills with agency
A skill declares: mission · write boundary · context contract · return
contract · rules · a RECOMMENDED class (advisory; the consultant may
override with reason, recorded). Two layers, same shadowing rule as
deliverable definitions:

- **shipped** — `kernel/skills/`: procedure-draft, source-read,
  assessment, data-analysis, data-clean (normalize one messy artifact
  into a clean, referenced working file in _synthesis/). A capture
  template is not new machinery — a capture shape IS a skill
  (procedure-draft variant), authored per engagement.
- **engagement-authored** — `<root>/_skills/`: the consultant may CREATE
  a skill ad-hoc, from scratch or as a variant of an existing one.
  Every ad-hoc skill is SAVED (never used from a prompt), logged in the
  session record, and reusable — later sittings inherit it.
  A local name shadows a shipped one.

## How dispatch runs on the substrate (no hot-loading)
The three classes are three tiny STATIC agent definitions (model + tool
surface pinned; system prompt: "read the brief, do exactly what it says,
return what its return contract names"). The skill is NOT delivered
through the harness — agent-frontmatter `skills:` is deliberately unused
(it welds skill to agent, the v1 shape). The composed brief IS the skill
delivery: plain prompt text, resolved by `brief.compose` and handed at
dispatch. This is why an ad-hoc skill saved mid-sitting works instantly
(harness skills are discovered only at session start), why local-shadows-
shipped is our resolution logic, and why the library is portable beyond
Claude Code. Per-dispatch model choice is first-class in the Agent call;
tools can't be granted per-dispatch and don't need to be — the class's
tool surface is fixed, and the skill's write boundary narrows it as an
instruction that check.run and the one-writer law verify mechanically.
