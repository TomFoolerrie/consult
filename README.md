# CONSULT

A Claude Code **plugin** that turns messy finance-process source material —
interview transcripts, prior SOPs, working notes — into governed,
evidence-backed **desktop-procedure Word deliverables**, one per L1 finance
area (e.g. Record-to-Report, Procure-to-Pay). You feed it raw sources; it
produces a CFGI-branded `.docx` whose every claim traces back to a source, with
the cross-cutting sections (Roles, Systems, Dependencies, RACI, Appendices)
kept mechanically consistent rather than hand-maintained.

> **v1 is built and tested** — the deterministic engine, the four skills, and
> the seven subagents are all in place, exercised by 800+ passing tests. See
> [`docs/`](docs/) for the full architecture and the per-milestone design
> tickets (M0–M32).

## The core idea — two databases, everything else is a view

CONSULT keeps exactly **two hand-authored databases** per area:

1. **Procedures — the verbs.** One Markdown fragment per L3 activity
   (`10_<slug>.md`), each an A–H desktop procedure. This is the **source of
   truth** for what happens, in what order, with which controls, gaps, and
   screenshots.
2. **Reference registry — the nouns.** A human-confirmed dictionary of
   canonical **systems** and **functional roles** (plus aliases, glossary,
   sources) under `_reference/*.yaml`. Its primary job is *intake grounding*:
   normalizing "the AP lady" / "our system" from transcripts into canonical
   names.

**Everything else is a generated view** — Roles & Responsibilities, Systems &
Data Inputs, Key Dependencies, RACI, the Appendices, the In-Scope index. None
of it is hand-maintained; it is projected from the two databases and
regenerated.

Three rules keep the views drift-free:

- **Numbers exist only at render.** Display numbers (`1.1`, `1.2`) are derived
  from the manifest at docx-build time by a single helper — never baked into
  content, so reordering never rewrites a file.
- **Procedure cross-references are `[[slug]]` tokens** — never a copied number
  or title. Slugs are stable, assigned once at creation.
- **Nouns bind via an explicit `consult-meta` slug block** at the bottom of
  each procedure (the registry slugs it used). Python reads that list directly
  — no fuzzy prose-scraping, no silent misses. An unknown slug is a warning
  that drives a human registry top-up, never a dropped mention.

The assembled single-file document is **not** an artifact — it exists only
transiently inside the docx build. Humans edit procedures and the registry;
reviewers read the Word document.

## How you use it

You invoke **one** skill: **`consult-orchestrate`** — "build `<area>`" or
"continue `<area>`". You never run Python by hand.

The orchestrator is a thin coordinator. On each turn it consults a read-only
Python state advisor, performs the single next action it returns, and
loops:

- runs **deterministic Python** itself (scaffold, aggregate, render,
  reconcile, scope-delta),
- **dispatches isolated subagents**, each in its own context returning only a
  compact result — `consult-taxonomy` (scope), one `consult-drafter`
  **per procedure** (parallel fan-out), `consult-dependencies`, and
  `consult-raci`,
- moves consumed sources `_sources/new/` → `_sources/processed/`,
- and **stops at three human gates**: (1) confirm the proposed scope/registry,
  (2) top up the registry when views flag unmatched nouns, (3) review the
  rendered Word document.

Reviewers mark up the `.docx` with **tracked changes and comments**;
`review_extract.py` feeds those edits back into `_review/` per procedure, and
the orchestrator re-dispatches only the affected drafters. Context stays flat
no matter how large the engagement grows, because the orchestrator never pulls
transcripts or draft text into its own context.

## The pipeline

1. **Taxonomy + scaffold** — `consult-taxonomy` proposes the L3 procedure set,
   the noun registry, and source→procedure tags; after the human confirm gate,
   Python scaffolds the A–H skeletons.
2. **Parallel fill** — one `consult-drafter` per procedure fills its skeleton
   from just its tagged sources + the registry.
3. **Aggregate** — Python builds the mechanical views (In-Scope index, Systems,
   Role Dictionary, Appendix A/B/C) by joining callouts and `consult-meta`.
4. **Synthesize** — `consult-dependencies` and `consult-raci` author the two
   judgment views (Key Dependencies, RACI matrix).
5. **Render** — the docx builder assembles everything into a CFGI-branded
   `.docx`, prefixing numbers and resolving `[[slug]]` tokens at render time.
6. **Review loop** — Python emits per-owner **review kits** (`kits.py`: the
   reviewable `.docx`, gap workbooks, screenshot templates); reviewer markup and
   returned kits flow back through `review_extract.py` / `review_apply.py` /
   `gaps_ingest.py` / `screens_ingest.py` onto the M6 notes bus, and the
   orchestrator re-dispatches only the owning drafters before re-rendering.

Two capabilities sit **above** a single area, run on the user's word:

- **Intake** (`consult-intake`) classifies a batch of documents staged at the
  engagement root and routes each to the area(s) it informs.
- **Knowledge placement** (`consult-placement`) is one judgment pass over the
  whole engagement enforcing "one fact, one home" across areas.

A **consolidation** pass (`consult-consolidator`) can also run over a single
drafted area for cross-procedure consistency (naming, sequencing, duplication),
emitting review notes without touching fragments.

## Plugin layout

```
consult/
  .claude-plugin/plugin.json     plugin manifest
  agents/                        7 isolated subagent definitions
    consult-taxonomy.md          scope one L1 area + stand up the registry
    consult-drafter.md           own ONE procedure (first draft + updates)
    consult-dependencies.md      author the Key Dependencies view
    consult-raci.md              author the RACI matrix
    consult-consolidator.md      cross-procedure consistency pass (M12)
    consult-intake.md            classify + route an engagement doc batch (M25)
    consult-placement.md         one-fact-one-home placement pass (M24)
  skills/
    consult-orchestrate/         the single entry point (drives everything)
    consult-taxonomy/            scoping brief
    consult-drafter/             procedure-fill brief
    consult-docx-builder/        CFGI Word render brief
  scripts/                       the deterministic engine
    doc_model.py                 shared spine (manifest, slugs, display numbers, sections)
    orchestrate.py               read-only state advisor (next action)
    scaffold.py                  section skeletons from confirmed taxonomy
    aggregate.py                 mechanical views (Systems, Roles, Appendices…)
    reconcile.py                 ID / token / marker integrity gate
    scope_delta.py               per-kind change signal for re-derivation
    render.py                    assemble + build the CFGI .docx
    sources.py                   SRC- registry + new→processed lifecycle
    callouts.py                  callout grammar parsing
    notes_util.py                the _review/{slug}.notes.yaml notes bus
    client_config.py             engagement config + document-profile resolution
    engagement.py                cross-area knowledge-placement + register verbs
    registers.py                 engagement-wide register machinery (M30)
    brief.py                     deterministic per-area work order for a subagent
    people.py                    person → role → rank resolution (review kits)
    consolidate.py               plan/mark the cross-procedure consistency pass
    kits.py                      per-procedure review-kit emitter (docx + workbooks)
    review_extract.py            Word tracked-changes/comments → notes bus
    review_apply.py              deterministic tracked-changes apply
    gaps_ingest.py               gap-workbook return trip → notes bus
    screens_ingest.py            screenshot-template return trip → notes bus
    xlsx_min.py                  dependency-free .xlsx writer/reader for kits
    migrate_sections.py          one-time mechanical section-heading migration
    split_doc.py                 legacy single-file .md → folder import
    console_compat.py            narrow-console stdout shim
  docs/                          design tickets M0–M32 + architecture README
  tests/                         800+ pytest cases across the engine
  requirements.txt
```

Per-area **data** lives in the **user's project**, not in the plugin, under
`components/<area>/` — its `_sources/`, `_reference/`, procedure fragments,
derived views, and `manifest.json`. One area = one document = its own git
history. (Client data can be gitignored or kept in a private repo.)

## Requirements

```bash
pip install -r requirements.txt   # python-docx, pyyaml
```

## Status

**v1 complete and under test.** The two-database model, the one-writer-per-file
rule, and the fail-loud parsing contract were hardened across three adversarial
passes and thirty-plus milestones (M0–M32); the deterministic engine, the four
skills, and the seven subagents are all built and exercised by **800+ passing
tests** (`python3 -m pytest`). See [`docs/README.md`](docs/README.md) for the
authoritative architecture, contracts, and build order, and
[`docs/known-risks.md`](docs/known-risks.md) for the open edges.

## History

This is CONSULT's second architecture. The first — a taxonomy-driven diagnostic
engine built on a shared `state.json` / `register.json` state machine — is
preserved in this repository's history at commit **`a119d22`**, an ancestor of
`main` (`git checkout a119d22` to read the v0 tree). It worked, but its shared
mutable state cost an entire hardening slice, and its central ID minter forced
serialization into every parallel fan-out.

[`docs/retrospective-v0.md`](docs/retrospective-v0.md) records what carried
forward, what the one-writer-per-file rule replaced, and the three capabilities
v0 had that this system still owes — most importantly its lens-conflict rule
(when two sources disagree, raise a gap rather than guess).
