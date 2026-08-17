# Drafting path — a process step (v2, IPO)

**You are reading this because your dispatch's `YOUR UNIT` line says
`process-step`.** This document is one of the two unit paths named by
`agents/consult-drafter.md`; read this one only. Everything in the shared
contract still binds you — evidence discipline, canonical nouns, tone,
uncertainty in callouts, the callout bars, conflicting sources, the
return format, the final-mode read-through. The v1-only rules
(`agents/drafting/activity.md`) do not.

## What you produce — a process step

A process step is one unit of process understanding in the IPO shape: six
parts, in declaration order, and nothing else in the fragment but its
`consult-meta` block.

**LAW vs HOUSE STYLE.** LAW is what `parse_entity` refuses: callout labels
exactly as the type declares them (`CONTROL`, `VALIDATION REQUIRED`,
`PAIN POINT`, `IMPROVEMENT OPPORTUNITY`, `SCREENSHOT PLACEHOLDER`), id grammar
`PREFIX-ALNUM`, prefix↔label agreement, no duplicate id inside one entity, a
well-formed `consult-meta` block. Everything below this paragraph is HOUSE
STYLE: the parser will accept a violation, review and reconcile will not, and
it is binding on you either way.

### The parts

`## <Heading>` is the step, and it matches the manifest title. The parts are
`### <Title>` — **Scope, Inputs, Transformation, Outputs, Controls, Issues**,
in that order, title only: no letters, no numbers, no renaming.

- **Scope** (prose). What the step does end-to-end in one or two sentences,
  then `Owner: <Role>.` and `System(s): <...>.`, the cadence ("Runs Thursday
  and Friday", "as the queue fills"), and the handoffs as `[[slug]]` tokens
  ("Takes its work from `[[receive-invoice]]`, passes clean bills to
  `[[schedule-payment]]`"). Close with **one explicit out-of-scope sentence**
  ("Non-PO invoices are out of scope for this area.") — every Scope has one.
- **Inputs / Outputs** (lists). One artifact per line:
  `- <artifact> — from <origin> (<system>)` and
  `- <artifact> — to <destination> (<system>)`. The origin/destination is a
  `[[slug]]` token when it is another step of THIS area, a named role or actor
  otherwise; the parenthetical names the system or the record. A terminal that
  is not a step gets a prose tail instead — "retained in Ephesoft as the source
  document", "sent back to the supplier by email", "transmitted to the bank
  through Chase Connect". Examples:
  `- Variance hold item — to [[approve-exceptions]] (NetSuite hold queue)`;
  `- Open purchase order line — from the Buyer (NetSuite PO record)`.
  **These lines ARE the dependency arrows** of the area — write them as facts,
  never as intentions, and never name a step that does not exist.
- **Transformation** (prose then list). One narrative paragraph: who works
  what, what the system does on its own, and what stops the line. Then a
  `1.`-numbered list of imperative sub-steps — **same owner and same system
  throughout**; a change of performer is a split signal, not a sub-step (see
  the shared callout bars in `agents/consult-drafter.md`, M42 A5).
  **Sub-steps carry no callouts**: the callout homes are Controls and Issues,
  per the shared callout doctrine.
- **Controls / Issues** — the callout homes. Controls takes CTRL; Issues takes
  GAP, PP and IO. The shared bars govern whether a callout exists at
  all. The CTRL's four declared fields — **Performer, Comparison, Trigger,
  Evidence** — are carried as `> - **<Field>:** <value>` sub-fields where the
  sources support them; a prose CTRL that states the same facts is not a
  defect, silence about them is. **Honest absence is content**: a Controls part
  with no control states what was looked for and **not found**, cited — "No
  system-enforced or supervisory control was identified over exception
  disposition: the reason code is recorded by the same person who releases the
  bill, and NetSuite requires no second approval (SRC-001). Recorded here as
  the current state, not as a recommendation." Never leave the part empty and
  never invent a control to fill it.
- **`consult-meta`** last, after Issues: `systems:` and `roles:` as registry
  slug lists, exactly the registry spellings.
