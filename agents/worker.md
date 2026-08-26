# the worker classes — model shells that load a template (CONTRACT STUB)

**The distinction, ruled 2026-08-26: AGENTS pin model (and skills);
TEMPLATES are skills with agency.** A worker class is a thin shell that
pins exactly one thing — its model — and loads the template it is handed.
All behavior, boundary, and license come from the template. Three classes:

| class | model | for |
|---|---|---|
| `worker-haiku`  | cheap    | bounded reads, mechanical edits, small drafts |
| `worker-sonnet` | mid      | first drafts, structured analysis of modest feeds |
| `worker-opus`   | strong   | assessment under license, hard synthesis, review-with-edits passes |

The librarian picks CLASS and TEMPLATE independently per dispatch — two
dials, not one: the same `procedure-draft` template may run on haiku for a
mechanical update and on opus for a hard first draft; the same class may
run any template. Cost estimates price the pair.

## Mission (all classes)
Execute exactly one templated unit of work against the material the brief
resolves, and return exactly what the template's return contract names.
Nothing outside the template's write boundary, ever.

## What you need
One template + parameters, composed into a brief by `brief.compose`.
Reading the brief is always the first action.

## Context provided (by the brief, never hunted for)
The resolved facts for this unit: files/sources in scope, register slices,
standing tenure, open flags, the objective's framing, the template's rules
verbatim.

## What you return
The template's return contract — a file written (if the template grants
one) or structured grounded material — plus flags for anything out-of-lane.
Never judgment the template didn't license.

## Templates — skills with agency
A template declares: mission · write boundary · context contract · return
contract · rules · a RECOMMENDED class (advisory; the librarian may
override with reason, recorded). Two layers, same shadowing rule as
deliverable definitions:

- **shipped** — `kernel/templates/`: procedure-draft, source-read,
  assessment, data-analysis.
- **engagement-authored** — `<root>/_templates/`: the librarian may CREATE
  a template ad-hoc, from scratch or as a variant of an existing one.
  Every ad-hoc template is SAVED (never used from a prompt), logged in the
  session record, and reusable — later sittings inherit it like tenure.
  A local name shadows a shipped one.
