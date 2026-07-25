# Retrospective — CONSULT v0 (the taxonomy/state-machine engine)

The first CONSULT implementation ran from initial spec through four build slices
before being superseded by the folder-native architecture now on `main`. It is
preserved in this repository's history at commit **`a119d22`**, an ancestor of
`main` — run `git checkout a119d22` to read the v0 tree.

> If you arrived here grepping for the **`v0-taxonomy-engine`** branch: it was
> removed during a branch cleanup. Nothing was lost — the branch only ever
> pointed at `a119d22`, which `main` still reaches.

This document records what v0 got right, what it got wrong, and what the second
attempt must not lose. It is written for whoever asks, six months from now, "why
does CONSULT store procedures as Markdown fragments instead of a database?"

> Also published as a formatted page:
> <https://claude.ai/code/artifact/fdc2f953-d38d-4b32-8dc2-1f9baf0f6294>
> (private to the repo owner unless shared).

---

## What v0 was

A diagnostic engine built around a fixed taxonomy. Every input document was
classified into the CFGI finance work taxonomy (7 L1 cycles / 37 L2 sub-functions
/ 212 L3 activities); L2 was the unit of work. Per-engagement state lived in two
JSON files — `state.json` (one node per L2, carrying coverage, five diagnostic
lenses, evidence, SOP/improvement status) and `register.json` (a flat item
register of improvements, gaps, screenshots, unmapped items, themes) — written
only through Python engines. It produced four deliverables: SOPs, process
improvements, a gap report, and a cross-cutting synthesis with an effort×impact
roadmap.

It worked. The Slice-1 end-to-end regression passed 39/39 assertions and was
idempotent. It ran on real client artifacts. It was not abandoned because it was
broken.

**Scale:** 16 Python engines (~6,300 lines), 14 skills, 5 sub-agent definitions,
a 707-line `spec.md`, 5 stage contract documents, 44 build tickets across 4
slices, 25 test files (~4,200 lines).

---

## The core lesson

> **v0 was right about the product and wrong about the substrate.**

Nothing in the retrospective below is a criticism of the domain model. The
taxonomy, the deliverable set, the evidence discipline, the human review loop —
all of that survived and most of it carried over. What did not survive was the
decision to hold engagement state in two shared mutable JSON files, and that one
decision generated the majority of v0's incidental complexity.

---

## Takeaway 1 — Shared mutable state was the tax, and it compounded

**Slice 3 was, essentially, an entire build slice spent making two JSON files
safe.** Twelve tickets (T40–T51): atomic writes, an engagement-level advisory
lock, rollback and re-entrancy in the merge path, an ID-minting race, dedup keys,
orphan exclusion on sync, malformed-node guards, ISO timestamp comparison.

`scripts/consult_io.py` on the v0 branch is genuinely good code — the note
explaining why the `flock` must live on a separate sidecar inode (because
`os.replace` swaps the inode out from under a lock held on the data file itself)
is exactly right and hard-won. But it is a careful solution to a problem the
current architecture does not have.

**The rule that replaced it:** *one writer per file, no exceptions* — see the
ownership table in `docs/README.md`. Parallel drafters cannot collide because no
two of them write the same file. There is no lock in the current system, and
there is no ticket that could have been written to add one, because there is no
race to guard.

> **Pick a state model where the concurrency bugs cannot be written.** Every hour
> spent hardening a shared blob is an hour not spent on the product.

## Takeaway 2 — A central ID minter forces serialization into every fan-out

v0 minted global sequential IDs (`IMP-…`, `GAP-…`) from the central state
machine. Because consolidation workers had to cite IDs they had just minted, the
minter sat on the critical path of every parallel worker.

The scar tissue is visible in ticket T57. Its first design routed worker output
through JSONL for deferred application; a second adversarial review killed it,
because deferring the write broke the consolidator's *ID-before-citation*
contract. The fallback was "each worker applies inline under the engagement
lock" — that is, re-introducing the serialization point the fan-out was meant to
remove.

**The rule that replaced it:** IDs are **local to their procedure** (`CTRL-01` in
two different procedures are distinct items; global identity is the tuple
`(slug, local-id)`), and the globally-sequential numbering a reader sees is a
**display transform** computed at render time by
`doc_model.callout_display_ids()`. Workers never need to know their place in the
document, so they never need to coordinate.

> **If parallel workers must agree on a number, you have built a lock.** Make the
> number derived and late.

## Takeaway 3 — Storing what you can derive buys you a drift-checker, not correctness

v0 stored the same fact in more than one place and then wrote checkers for the
gap between them. Two tickets exist only because of this:

- **T35** — a `validate` coherence check that node-MD-cited IDs actually exist
  and that front-matter lenses match `state.json`.
- **T36** — make the structural re-scan *preserve* human `review_status` / `owner`
  fields on `GAP-STRUCT` rows, because the scan rewrote a store humans also
  edited.

Both are competent fixes to a self-inflicted problem. A checker that says "these
two representations disagree" is strictly worse than an architecture in which
there is only one representation.

**The rule that replaced it:** *two databases, everything else is a view.*
Procedures (the verbs) and the reference registry (the nouns) are hand-authored;
Roles, Systems, Dependencies, RACI, In-Scope index, and all appendices are
regenerated projections. Drift is not detected — it is unrepresentable.

## Takeaway 4 — When you need prose to stop an agent misbehaving, the architecture is wrong

v0's Slice 4 arose from a field run (3 real client artifacts, ~$10) and was
almost entirely about context and cost. The tickets tell the story:

- **T54** — "orchestrator delegation enforcement: blocking prose + explicit
  content prohibition," described in the ticket itself as *"a nudge, not a gate."*
- **T59** — drop `indent=2` from transport bundles to trim input tokens.
- **T55** — drop a redundant `quote` field from the classify artifact.

These are real savings, but T54 is the tell: the orchestrator's context was
growing because nothing structurally prevented it from reading document content,
so the mitigation was to *ask it not to*.

**The rule that replaced it:** the orchestrator is a thin coordinator that
consults a read-only advisor, performs one action, and loops. It dispatches
isolated subagents that return compact results. It cannot pull transcripts or
draft text into its own context because it never opens them. Context stays flat
as the engagement grows — by construction, not by instruction.

> **Cost and context discipline are architecture, not a late optimization pass.**

## Takeaway 5 — One big end-to-end test tells you *that* something broke

v0's regression was `tests/test_slice1_e2e.sh`: 39 assertions, idempotent, green.
It is a good test. It is also a bash script that exercises the whole pipeline,
which means a failure localizes to "somewhere in ingest→render," and it needs a
full engagement fixture to run at all. Coverage arrived retroactively as **T49,
"test coverage hardening."**

The current suite is 258 pytest cases across 19 modules, at essentially the same
line count (~4,200 vs ~4,300). Same budget, far better failure localization, and
unit tests can be written *before* there is a pipeline to run them through.

> **Keep the end-to-end test. Do not let it be the only one.**

## Takeaway 6 — Prose duplication generates its own ticket class

v0 carried a 707-line `spec.md` plus five separate stage contract documents
(`classify`, `ingest`, `consolidate`, `generation_review`, `orchestration`).
Facts were restated across them, and they drifted from the code. This produced
**T39** ("register engine doc-debt"), **T48** ("documentation & schema drift
reconciliation"), and eventually a `DOC-DRIFT LINT` stage inside the end-to-end
test — a lint asserting that no contract still claimed a feature was unbuilt.

The current design consolidates into one architecture document plus per-milestone
tickets that reference it rather than restating it. Worth watching: this is a
failure mode that recurs quietly.

---

## What earned its keep — carry these forward

These were right in v0 and are right now. Do not relitigate them.

| Idea | Where it lives now |
|---|---|
| **Deterministic Python for anything mechanical; LLM only for judgment** | Ownership table — Python owns index/roles/systems/appendices, agents own dependencies/RACI/procedures |
| **A read-only "what is the next action" advisor** | `scripts/orchestrate.py` — survived the rewrite nearly intact, and is the reason the orchestrator can stay thin |
| **Evidence traceability on every claim** | `SRC-` ids in the registry + Source Materials sections; v0's `path#Lstart-Lend` refs were the stricter form |
| **Explicit human gates, not autonomous completion** | Three gates: confirm scope/registry, top up registry, review the Word document |
| **Fail loud on unrecognized input, never silently drop** | Unknown `consult-meta` slugs warn and drive a registry top-up |
| **Synthetic fixture corpora** | The R2R and P2P fixture engagements — a rewrite is only cheap if you can re-run something |
| **Adversarial review passes before building** | Three passes on the two-database model; on v0 a second pass killed T57's original design before it shipped |

---

## What was lost and should come back

Being honest about the trade: the rewrite is a better *engine* and currently a
narrower *product*. v0 shipped four deliverables; the current system ships one
(desktop procedures per L1 area). Specifically missing:

1. **The synthesis / decision layer.** Executive summary, cross-cutting themes,
   effort×impact roadmap, per-L1 current→future state. This is the deliverable a
   partner actually presents, and it has no home in the current architecture.
   Natural fit: an agent-owned derived view alongside `82_dependencies` and
   `84_raci`, plus an engagement-level rollup across areas.
2. **Coverage measurement.** v0's fixed taxonomy gave "37 L2s, N diagnosed, M
   gaps" for free. Per-area proposed scope is more flexible but not measurable.
   Consider grounding proposed scope against the reference taxonomy so coverage
   remains reportable.
3. **The lens-conflict rule.** v0's discipline was explicit: when two documents
   disagree on a diagnostic lens, leave it null and raise a `GAP-CONFLICT` rather
   than guess. There is no current equivalent, and a drafter reconciling two
   contradictory transcripts will quietly pick a winner. This is the single most
   valuable thing to port back.

Most of the improvement/gap reporting is *nearly* recoverable already — `PP`,
`IO`, and `GAP` callouts feed Appendix A/B, so the improvement register and gap
report are closer to a view than to a rebuild.

---

## Meta-lesson: the first attempt was not wasted

The rewrite was fast (59 commits, roughly a month) because v0 had already
answered the expensive questions: what the taxonomy is, what the deliverables
are, what the review loop must do, where the human gates belong, what "done"
means. The second attempt reused all of that thinking and discarded only the
implementation.

Treat v0 as the spec-generating exercise it turned out to be. The mistake would
have been shipping it because it worked.
