# Run manifest

The orchestrator writes it; the skill reads it. **The orchestrator names every location and every agent.** The skill ships defaults so a manifest can be short, but nothing in the skill assumes a folder name or an agent name — `run.py`, `render.py`, and the prompts all resolve through the manifest.

```yaml
run: assess-2026-09-01
skill: /path/to/consult-assessment            # defaults to the skill that's running
taxonomy: _client/taxonomy.yaml               # defaults to <skill>/assets/taxonomy.yaml
lint_skill: /path/to/consult-lint             # defaults to sibling of skill; only used for the cite command in prompts
registry: _client/registry.yaml               # consult-lint registry: src-NNN -> file, hash, lines
context: _client/profile.md                   # context-profile; required by themes and above
citation_pattern: '^src-\d{3}(:L\d+(-L?\d+)?)?$'

paths:                                        # all optional; relative paths are relative to this file
  ledger_dir: _synthesis/assessment/ledgers   # the deliverable; must be inside git
  workdir:    _workspace/assessment           # agent scratch; disposable
  out:        _synthesis/assessment/out
  prompts:    "{workdir}/prompts"             # where run.py render writes spawn-ready agent files
  gates:      "{ledger_dir}/gates.json"       # human decisions
  tables:     "{out}/tables"
  figures:    "{out}/figures"
  story:      "{out}/story.md"
  bundle:     "{out}/assessment-output.json"
  review_pack: "{workdir}/review-{group}.md"
  shim:       "{workdir}/assess.py"           # command shim run.py render writes; agents call this instead of skill paths
  digest:     "{workdir}/context-digest.md"   # written once by the digest op; readers load it instead of raw pre-reads
  analysis:   "{out}/analysis"                # data.py outputs; registered as sources, so keep them on the deliverable side, in git
  retro:      "{workdir}/retro-{phase}.md"     # post-phase reports

agents:                                       # all optional; reader is a pattern
  reader:    "reader-{group}"
  normalize: normalizer
  themes:    themer
  recommend: recommender
  plan:      planner
  story:     storyteller
  digest:    digester
  retro:     retrospector

groups:                                       # spawnable now
  - id: G1
    agent: reader-G1                          # optional; defaults to agents.reader with {group}=G1
    pre_read: [engagement_objective, notes, _client/org-chart.md]   # always read (context, not sources); replaced by the digest once it exists
    reference: [_client/systems-inventory.md]                        # consult only if relevant
    sources: [src-004, src-005, src-006]
    note: "Read for control ownership gaps; the org chart shows a 3-person finance team."
deferred_groups:                              # held back until the findings gate passes; next tells you when to restore
  - id: G2
    pre_read: [engagement_objective, notes]
    sources: [src-002, src-003]
    builds_on: [G1]                           # optional: this reader gets G1's findings AFTER its own blind pass, to link/corroborate/contradict
    note: "Artifacts; prefer observed evidence_basis. Test what the G1 interviews claimed about the close."
  - id: G3
    sources: [src-014]                        # the JE listing
    builds_on: all                            # every complete group at spawn time
    note: "Data. Test the control claims made in every interview."

story_note: "Client believes it has a systems problem. Lead with fig-dimensions."
```

Top-level `ledger_dir`, `workdir`, `out` are accepted as shorthand for `paths.*`. Templates may reference other path keys with `{key}`; `{group}` is filled per group where it appears.

What is *not* configurable: the file names inside the ledger dir (`findings.jsonl` etc. — that's the ledger format, like the layout inside `.git/`), the `.assessment-ledger` marker, and the layer ids (`F-`, `T-`, `R-`, `I-`, `P-`). Everything outside the ledger dir is the orchestrator's to name.

Agent identity is the `agent` value. Ownership in the ledger is keyed to it, so a re-spawned agent with the same name is the same author. Change agent names before extract, not after.

The `context:` file is read by every reader first; do not also list it under `pre_read`.

`manifest.py draft --registry ... --out ... [--ledger-dir --workdir --out-dir] [--all-groups]` emits this structure with defaults filled and TODOs where judgment is needed. ## Grouping — fewer, larger, coherent

A group is a question a reader can answer, not a bucket of size N. The design pays off when one reader sees the sources that bear on the same thing: that is where cross-source corroboration and contradiction get logged, and a reader who has the controller's transcript, the close checklist, and the JE listing together will find what three separate readers cannot. Split a group only when it would not fit in one context.

Rules of thumb:
- **One group per question**, named in its `note`: "how does the close actually run and who controls it?", "is commission revenue complete and cut off correctly?" Put every source that bears on the question in it — interviews, the artifacts they mention, the data that tests what they claim, the summary of the transcript.
- **Size by budget, not by count.** ~35k source words (~50k tokens) per group is comfortable; a reader also needs room for pre-reads, tool output, and its own findings. Transcripts count fully; tabular sources count little (they are profiled and tested, not read).
- **Keep a summary with its transcript**, and keep a data file with the interview that describes the process it records.
- **Overlap on purpose** when two questions share a source: the same transcript can be in two groups. Two readers logging the same fact from different angles is what the normalizer's `link` proposals are for; it is far cheaper than one reader missing a contradiction.
- A typical mid-size engagement is four to eight groups. Fourteen is a sign of splitting by size. The drafter warns above eight.

## Building on earlier groups — `builds_on`

Readers extract blind by default; that independence is what makes a contradiction between two readers mean something. But a later reader often *should* know what earlier ones found — to test a stated claim against the artifact or data it now holds, to link rather than re-log, to answer an open question. `builds_on: [G1, G4]` (or `all`) gives the reader a compact index of those groups' findings — id, type, severity, evidence basis, category, first line, sources — plus open items and the categories nothing has been logged on yet. It lands in the brief *after* the sources, and the reader prompt enforces two passes: extract blind, then situate (link, corroborate, contradict, answer). The reader never sees prior findings before it has logged its own.

`next` sequences the fan-out in waves: a group is spawnable only when everything it builds on is complete. A natural shape is interviews first (blind, in parallel), then the artifact and data groups with `builds_on: all` — the readers who can test what people said get to see what people said.

Anchoring is the risk. Don't set `builds_on` on the interview groups themselves; do set it on anything whose job is to verify.

The drafter follows this when the registry carries `topic:` on sources (set it during annotation — it is the single most useful field the human fills) and `summary_of: src-NNN` on summaries. Untagged sources fall back to interviews-by-interviewee and artifacts-by-kind, which is the "too many groups" outcome; tag topics instead.
