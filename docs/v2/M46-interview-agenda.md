# M46 — The interview agenda: a deliverable definition over the needs view

**Status: SPEC** — from the 2026-08-16 architecture review, decision D4
(ruled LOOKS RIGHT, with the human's note: **"I would like to be in charge
of when this generates. It will be an ad hoc item."**). Third of the
review's five tickets.

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

## Acceptance gate

`tests/test_agenda_m46.py` — written before the build: the definition loads
through the four-stage loader with zero shape-audit entries; renders over
the IPO fixture for a fixture role; the ledger join suppresses held items;
unknown role refuses by name; nothing in any agent contract or skill
triggers generation automatically (mechanical grep).
