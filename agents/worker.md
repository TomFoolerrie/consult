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

The librarian picks CLASS and SKILL independently per dispatch — two
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
the librarian's standing precedent and open observations (from its
state pad), the objective's framing, the skill's rules
verbatim.

## What you return
The skill's return contract — a file written (if the skill grants
one) or structured grounded material — plus out-of-lane OBSERVATIONS
returned to the librarian, who logs them in its state pad (A9).
Never judgment the skill didn't license.

## Skills — skills with agency
A skill declares: mission · write boundary · context contract · return
contract · rules · a RECOMMENDED class (advisory; the librarian may
override with reason, recorded). Two layers, same shadowing rule as
deliverable definitions:

- **shipped** — `kernel/skills/`: procedure-draft, source-read,
  assessment, data-analysis.
- **engagement-authored** — `<root>/_skills/`: the librarian may CREATE
  a skill ad-hoc, from scratch or as a variant of an existing one.
  Every ad-hoc skill is SAVED (never used from a prompt), logged in the
  session record, and reusable — later sittings inherit it.
  A local name shadows a shipped one.
