# M46 — The interview agenda: a deliverable definition over the needs view

**Status: BUILT** (`2.2.0-alpha.3`, gate 9/9, suite 1167) — from the
2026-08-16 architecture review, decision D4 (ruled LOOKS RIGHT, with the
human's note: **"I would like to be in charge of when this generates. It
will be an ad hoc item."**). Third of the review's five tickets. See
Amendment A1 for build friction.

## Why (the ruling)

The engagement lifecycle's phase 2 — "meet with them, get more PBCs, have
interviews (**need agendas**), interview transcripts" — scored ABSENT in
the review: nothing in the system produces the thing you walk into a client
meeting holding. Everything an agenda needs already exists in the brain:
the needs view (M44) knows what is missing and for which deliverable; the
roles registry knows who does what; the ledger knows what was already
provided and what was already asked.

## The shape

**`kernel/deliverables/interview-agenda.yaml`** — a definition like any
other (shape + bindings + skin), no engine special-cases (the M38 bar).

- **Bindings:** the needs view (`engagement-needs`, M44's builder — the
  first definition to bind it), joined with the roles registry (who can
  answer which need — role attribution comes from the needs entries'
  step/node homes and the RACI/roles data, never guessed) and the source
  ledger (what this interviewee already gave us — an agenda that asks for
  what we hold loses the client's patience; the M40 request-view rule,
  reused).
- **Shape:** one agenda per named role (or per named interviewee via
  client config), sections: what we want to confirm (conflicts), what we
  believe is missing (evidenced absences + coverage), what we have not
  asked yet (binding-unserved territory in their area), what you gave us
  that we still owe a read on.
- **Skin:** the docx adapter, client-facing tone.

**Generation is HUMAN-TRIGGERED, always** (the ruling's note). A CLI verb —
`materialize`/render invoked by the human with a role argument — never part
of any agent's loop, never auto-fired by coverage state. No agent may
decide an interview is needed.

## Parts

- **Part A** — the definition file + any missing view writer (expected: the
  role-join view over `engagement-needs`; register through
  `aggregate.PY_BUILDERS`, plan_views idiom).
- **Part B** — the CLI trigger (the existing definitions/materialize verb
  path if it fits; a thin `--agenda <role>` flag where it does not) and its
  refusals (unknown role by name; no needs entries → an honest "nothing to
  ask" agenda, never a crash).
- **Part C** — prose: the taxonomist (M45) MAY cite agenda-worthy clusters
  in its return; it may not generate. The orchestrate skill documents the
  human trigger.

## Test impact

New gate: `tests/test_agenda_m46.py` (committed with this spec, skips until
the definition file exists). **No existing test changes.** The gate pins one
API decision the spec's Part B left open: the render verb is
`scripts/agenda.py` with `render(area, role=...)` (plus its CLI `main`).

## Amendment A1 — build friction (recorded at close-out, 2026-08-17)

1. **One feed → one section** (invented rule, documented in agenda.py):
   the spec's section vocabulary asked for "conflicts" and "evidenced
   absences" separately, but M44 A1 deferred the discriminator on GAP
   callouts — so the mapping is mechanical: `recorded-gap` → confirm,
   `coverage` → missing, `binding-unserved` → not yet asked, ledger →
   owed a read. Any finer split would be new gap judgment, which the
   design rule forbids. Revisit when the discriminator lands.
2. **`binding-unserved` is not role-attributable** (its `where` is a
   binding name): shown only to roles with territory in the area,
   withheld otherwise — attributing area-level ground to someone the
   record never places there would be a guess.
3. **The binding language cannot name the needs view or the ledger**
   (`_ALLOWED_BINDING_KEYS` is closed): the `engagement-needs` binding's
   NAME carries the identity with legal verbs only, and the ledger joins
   on `role-territory`'s step slugs rather than a decorative binding.
   Follow-up (recorded): a definitions.py binding verb for derived-view
   feeds, if a third consumer appears.
4. **Role-less plan path:** `build_interview_agenda(ctx)` without
   `ctx["role"]` renders every registry role with territory, registry
   order — still reachable only when a human asks.
5. **Fixture blind spot (recorded):** all three IPO sources are fully
   consumed, so the owed-a-read section renders `—` for every role; the
   suppression half shows only as the `Already in hand:` line. Wants a
   fixture with an unconsumed source.

## Acceptance gate

`tests/test_agenda_m46.py` — written before the build: the definition loads
through the four-stage loader with zero shape-audit entries; renders over
the IPO fixture for a fixture role; the ledger join suppresses held items;
unknown role refuses by name; nothing in any agent contract or skill
triggers generation automatically (mechanical grep).
