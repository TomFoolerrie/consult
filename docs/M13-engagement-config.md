# M13 — Engagement-level config (parent folder resolution)

> **Status: DESIGNED.** Small, self-contained; pays off at the second area.

## Goal

Let client context and engagement settings live **once per engagement** instead
of once per area, with per-area override where it genuinely differs:

```
components/
  _client/              engagement-wide (human-owned)
    org-chart.yaml
    taxonomy.yaml
    profile.yaml        (M14)
    conventions/        (optional engagement-wide phrasing digest)
  accounts-payable/
    _client/            optional per-area override, same file names
  record-to-report/
```

## Why

An engagement with six areas duplicates the same org chart six times today, and
copies drift — so the name-leak check and the person→role mapping quietly differ
per area, which is worse than having no shared file at all. Client context is
human-authored ground truth; it is exactly the thing that should be shared.

Terminology should also be consistent across all six documents the client
receives, so an engagement-wide `conventions/` is strictly more useful than a
per-area one.

## Design

### Resolution rule (one helper, used everywhere)

`client_config.load(area) -> dict` walks **area `_client/` first, then the parent
`components/_client/`**, merging per top-level key:

- A key present in the area file **wins entirely** for that key (no deep merge
  of nested structures — deep merging YAML the human hand-edits is how silent
  surprises happen).
- Keys absent from the area file come from the parent.
- Neither present → the current "no client context" behavior, unchanged.

`conventions/` merges by **file**: an area's `conventions/{slug}.md` shadows a
parent file of the same name; all other parent files are read too.

Every consumer switches to this one helper: `people.py` (org chart), the
taxonomy agent (client taxonomy as L1 boundary authority), `reconcile.py` (name
check), drafters (conventions), and M14's profile.

### What is NOT shared

`_reference/` stays strictly per-area — `systems.yaml`, `roles.yaml`,
`sources.yaml`, `glossary.yaml`. Those carry `confidence`, are proposed by an
agent, and are confirmed at a per-area human gate; sharing them would let one
area's low-confidence guess become another area's fact. The line is
**human-authored ground truth is shareable; agent-proposed registry is not.**

(`roles.yaml` `people:` lists remain per-area, but they are *grounded* by the
shared org chart — which is where the duplication actually hurt.)

### Reporting

Any stage that reads client config prints which layer it resolved from
(`_client/ (area)`, `_client/ (engagement)`, or `none`), so a surprising
name-check result is one line of output away from being explained.

## Acceptance

- Parent-only config: both areas resolve the same org chart; reconcile's name
  check fires identically in each.
- Area override of `org-chart.yaml`: that area uses its own file, the other
  still uses the parent, and both report which layer they used.
- No `_client/` anywhere: behavior byte-identical to today.
- `conventions/`: a drafter sees parent files plus its area's, with same-name
  area files shadowing.

## Out of scope

- Sharing `_reference/` (deliberate — see above).
- A config schema/validator (these are small hand-written files; fail loudly on
  malformed YAML and stop).
- Repo-root config above `components/` (one level of sharing is enough).
