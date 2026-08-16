# M47 — The research pass: public sources in, first PBC list out

**Status: SPEC** — from the 2026-08-16 architecture review, decision D5
(ruled DISCUSS, then settled in chat: **staged multi-file `_client/`
writes with a human review gate** — the human's shape, ratified over the
single-file draft). Fourth of the review's five tickets.

## Why (the ruling)

The lifecycle's phase 1 — "you start with the company, what's available
online, and some PBCs" — scored ABSENT: the system meets a client cold. A
day-zero pass over public material (10-K/annual report, site, org
announcements, industry norms for the in-scope cycles) should arrive
BEFORE the kickoff, so the first PBC request list and the seeded taxonomy
already reflect the actual company.

The human's rulings, verbatim in spirit: research "should be able to add to
more than just one file… the `_client/` folder can have a
`company_profile.md` maybe… a review step here would be good though to
confirm the research is accurate before it is filtered in."

## The shape

- **Propose-only, staged.** The research pass writes to
  **`_client/.proposed/`** — `company_profile.md` plus whatever else the
  material supports (`systems-landscape.md`, `org-notes.md`; files, not a
  fixed list). Nothing under live `_client/` is touched. The M41
  seed/promote pattern is reused: a **promote verb** moves reviewed files
  live at the human's explicit go, refusing live collisions by name.
- **Public provenance is first-class.** Every researched source lands in
  the engagement ledger with a `provenance: public` tag. The hard rule the
  review ratified: **public sources inform the needs view; they never
  discharge it.** A need is discharged only by client-provided material —
  concretely, the needs view (M44) and the coverage map treat
  public-provenance evidence as context, never as coverage.
- **The day-zero PBC list.** With the profile staged and the objective
  configured, the information-request definition renders a first PBC list
  whose asks are company-shaped ("your NetSuite three-way-match
  configuration") instead of generic. No new definition — this is the
  existing request list benefiting.

## Parts

- **Part A — machinery.** `scaffold.py` (or a sibling) gains
  `promote_client(root)` mirroring `promote_taxonomy`; `ledger`/`sources`
  admit the `provenance` field; the coverage/needs read-side rule (public
  never discharges) lands where coverage is computed, with a test proving a
  public-only node stays unclaimed.
- **Part B — the agent surface.** A research task needs web access, which
  agents in this plugin do not assume: the pass is specified as a
  **dispatch recipe** in the orchestrate skill (what to research, what
  files to stage, the provenance discipline, the review handoff), runnable
  by any web-capable session — not a new resident agent. (Roster pressure
  goes DOWN per D3/D6, not up.)
- **Part C — prose.** The taxonomist (M45) admits staged `_client/`
  research as an input to seeding/refinement; the objective block's brief
  mentions the profile when present.

## Open question for the spec review

Whether `company_profile.md` should be a typed entity (parseable, citable
by slug) or freeform reviewed prose. Lean: freeform in M47; typing it is a
follow-up once something needs to bind it.

## Acceptance gate

`tests/test_research_m47.py` — written before the build: staging writes
only under `_client/.proposed/`; promote moves reviewed files live, refuses
collisions by name, touches nothing else; ledger entries carry
`provenance: public` and the needs/coverage read-side proves public-only
evidence never discharges a need; the orchestrate skill documents the
recipe and the review gate (mechanical grep).
