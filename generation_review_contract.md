# CONSULT — Generation & Review Contract (Stages 5–6)

> Status: **DESIGN DRAFT** (no code yet). See `spec.md` §5 Stages 5–6 & "Deliverables & DoD".
> Reuses existing skills: `consult-drafter`, `consult-docx-builder`,
> `consult-review-comment-resolver`, `consult-evidence-auditor`.

## 1. Stage 5 — Draft (two streams, per L1 bundle)

Both streams draft per **L1 cycle** (the review unit) by reading state/register — never raw
docs. They write deliverable MDs and update status.

### 5A — SOP / Desktop Procedures (`consult-drafter` ✅, needs wiring)
The drafter already has an **L1-Level mode** (one doc per cycle). Wiring = how it sources from
state/register instead of ad-hoc input:
- **Inputs:** the L1's node MDs (narrative), the node lenses, and the register rows for those
  L2s — improvements → **Appendix B**, gaps → **Appendix C**, screenshots → **Appendix D**,
  pain points (process lens) → **Appendix A**.
- **Output:** canonical SOP MD per the drafter's **Quality Checklist** DoD, under
  `deliverables/sop/{l1}.md`. Evidence refs render inline; gap tags reflect register IDs.
- **Writes back:** `sop.status` / `sop.path` / `sop.rev` per node (via `set-sop`).

### 5B — Improvement Opportunities (`consult-improvement-drafter` ◻, new)
- **Inputs:** register `type:improvement` rows for the L1, grouped by **lens**
  (`process`/`automation`/`operating_model`/`capability`), plus the lens scores.
- **Output:** the improvements deliverable under `deliverables/improvements/{l1}.md` — each
  item **Finding → Recommendation → Effort × Impact → Owner** (the Stream-B DoD), traceable to
  its register ID and evidence ref.
- Items missing Effort×Impact×Owner are surfaced as needing input, not invented.

## 2. Stage 6 — Render → Review → Ingest → Output

### Render (Python)
`consult-docx-builder` renders each deliverable MD → CFGI-branded Word **per L1**, carrying
**evidence refs inline** and a **change log** (what moved since the last round, reviewer-
attributed). Provenance markers let a reviewer trace a claim back through the ingested MD to
the source.

### Human review (gate)
Reviewers edit + add tracked comments in the Word docs. The orchestrator **stops here** and
reports; it never self-finalizes.

### Ingest the review (LLM)
1. **docx comment extraction** (helper, ◻) — pull tracked comments *and* the revised body out
   of the reviewed Word (Word stores comments in the docx XML).
2. `consult-review-comment-resolver` classifies each comment (its existing categories:
   factual correction, clarification, evidence request, control/compliance, scope, SME-
   required, …) and proposes a structured action.
3. The **orchestrator applies** each action via commands, attributed to the reviewer:
   - finding correction → register row update; new finding → `add-item`
   - lens / diagnosis change → `set-lens` (or a contradiction gap if it conflicts)
   - SOP status / scope → `set-sop`
   - prose-only edit → node MD update (and, if it implies a state change, that change too)
   - `SME VALIDATION REQUIRED` → register row flagged `requires_human_review`, routed, and
     **blocks `final`** until closed.
4. Changes that alter a node's substance mark it **dirty** → re-consolidate/redraft on the next
   `consult-run` loop. This is how review folds back in without a CSV round-trip.

### Versioning & traceability
- Each review round increments a deliverable **rev** and appends to a **review log**
  (`deliverables/review_log.md` or register `change_notes`): reviewer, item, before→after.
- Re-runs don't silently overwrite human work: consolidate only touches dirty nodes; review
  edits live in state; the change log surfaces every move.

### Output (gates, then assemble)
Before `final`, the **DoD gates** must pass: `consult-evidence-auditor` ✅ (procedural claims
supported), zero open `requires_human_review` / SME items, every `unmapped` row owned, all
evidence refs resolve. Then assemble the final Word — **one document per work stream + the gap
report** — and set deliverable statuses to `final`.

## 3. Decisions locked here

- **Review unit = per L1** (decoupled from per-L2 storage; the drafter's L1-Level mode).
- **Comment → action mapping** is owned by the resolver + orchestrator; the agent applies, the
  reviewer's intent is attributed and logged.
- **Gates are hard**: evidence-auditor + open SME/`requires_human_review` + unowned unmapped
  block `final`.
- **No CSV** anywhere — Word in, commands out.

## 4. To validate during the vertical slice

- Does docx comment extraction reliably recover anchored comments + revisions from a real
  reviewed Word file?
- Is the comment→command mapping unambiguous enough to auto-apply, or do some classes always
  need a human confirm?
- Is one final doc per stream the right packaging, or per-L1 finals + an exec summary?
- Exercise a **second review round** to prove versioning and no-silent-overwrite.
