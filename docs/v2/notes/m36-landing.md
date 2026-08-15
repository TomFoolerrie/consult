# M36 landing note — the compatibility gate, as built

Build record for [`M36-compatibility-gate.md`](../M36-compatibility-gate.md),
work packages G0 (golden harness) → G1 (plan assembly) → G2 (deterministic
layer) → **G3 (retirement + audits, this note)**. Companion:
[`M36-build-plan.md`](../M36-build-plan.md).

Suite: **1005 passed, 0 failed** (999 at the G2 baseline, +6 from
`tests/test_shape_audit_m36.py`). **Zero v1 tests edited; zero v1 tests
deleted** — see "The shim-existence test exception was not used", below.

---

## 1. The shim question, reconciled

M36's spec says *"the back-compat shims (`doc_model.SECTION_TITLES`
re-exports etc.) are removed — this ticket is their planned retirement."*
M33's amendment A3 says the opposite-sounding thing: *"in M33
`doc_model`/`callouts` remain the tables' home, the kernel loads its
declarations from YAML, and the parity tests are the anti-drift bond between
the two (**re-export shims therefore unnecessary this ticket**)."*

The two reconcile cleanly once you notice what A3 decided: **the re-export
shims M36 planned to retire were never built.** A3 chose the parity-bond
design instead, precisely so that no second import path would exist to
retire later. Grepping for the named shim confirms it: no module re-exports
`SECTION_TITLES`, and `kernel.py` defines no back-compat aliases at all.

So WP-G3's retirement work is not "delete the shims" (there are none). It is
the harder, more honest version of the same job, and the end-state this gate
actually needs:

1. **The kernel is the declared-data authority for TYPES.** Unchanged by G3;
   established in M33, made load-bearing by G1/G2.
2. **`doc_model`/`callouts` tables remain as the V1 ENGINE's internal
   implementation** — A3's home ruling stands. They are *not* shims: nothing
   imports them *for compatibility*, the v1 parsers are *written on* them,
   and `tests/test_kernel_m33.py`'s parity assertion fails the moment they
   disagree with the declaration. Moving them is M37+ work (it moves the
   parsers), not a compatibility-gate deletion.
3. **Anything that existed only as a duplicate or a re-export retires**, and
   any constant that duplicates declared data gets re-pointed at the
   declaration with a documented fallback — or is kept with a written
   justification, named below.
4. **The absence audit** makes (1)–(3) permanent rather than a one-day state.

---

## 2. The retirement table

### Retired (deleted; each verified read by no module and no test first)

| Symbol | What it was | Why it went |
|---|---|---|
| `aggregate.SUBSECTION_RE` | Bare re-export: `= doc_model.SECTION_HEADING_RE` | A second name for the shared `###` pattern. Read by **nothing** in `scripts/`, `tests/`, or the skills — a textbook re-export shim. Sub-sections are parsed through `split_subsections`, which resolves a heading to a *slug*. |
| `aggregate.ISSUES_SECTION` | `= "issues"` | A duplicate of the callout's **declared home** (`activity.yaml`'s `home:`, surfaced by `callouts.home_section`). Read by **nothing** — a dormant private side channel, exactly the shape the audit polices. |
| `aggregate.CONTROLS_SECTION` | `= "controls"` | Same. |

Pinned against return by
`test_shape_audit_m36.py::test_the_retired_symbols_stay_retired`.

### Re-pointed at the declaration (with a documented fallback)

All four in `scripts/client_config.py`, via three new readers
(`_declared_part_slugs`, `_declared_callout_labels`, `_declared_home`) that
read `kernel.load_type("activity")` and fall back to the v1 tables *only* on
a load failure (a stripped install — where a silently different vocabulary
would be worse than a visible one). The `import kernel` is lazy, mirroring
`scaffold.declared_parts()`.

| Constant | Was | Now |
|---|---|---|
| `ALL_SECTIONS` | `list(doc_model.SECTION_SLUGS)` | declared part slugs, declared order |
| `ALL_CALLOUTS` | a hand-written copy of `callouts.LABEL_TO_PREFIX`'s keys | declared callout labels, declared (reading) order |
| `CONTROLS_SECTION` | `"controls"` | the `CONTROL` callout's declared `home` |
| `ISSUES_SECTION` | `"issues"` | the `PAIN POINT` callout's declared `home` |

`BODY_OMIT_REGISTERS` is keyed on the last two, so the profile rule
"a section may not leave the body with no register to catch its callouts"
now *follows* a reshape instead of silently un-pointing.
`test_the_repointed_constants_track_the_declaration` proves the re-pointing
is real by reshaping the declaration (adding a part, re-homing `CONTROL`)
and reimporting: the constants move. A hard-coded copy would not.

### Kept, with justification (the v1 fallback path, by design)

| Kept | Why it stays |
|---|---|
| `doc_model.SECTION_TITLES`, `SECTION_SLUGS`, `SECTION_LETTER_ALIASES`, `SECTION_TITLE_ALIASES`, `SECTION_SLUG_ALIASES`, `SECTION_MERGE_SOURCES` | M33 A3's home ruling; the v1 parsers are written on them; the M33 parity test is the anti-drift bond. Also the *documented fallback* for every re-pointed reader above. |
| `callouts.LABEL_TO_PREFIX`, `LABEL_TO_HOME_SECTION`, `SEVERITY_ENUM`, `PREFIXES`, `ID_STRICT_RE` | Same ruling, callout half. `PREFIXES`/the regexes are derived from the map, not typed. |
| **`callouts.LABEL_PREFIX`** (a genuine back-compat alias: *"reconcile historically used this name"*) | **The one true shim in the codebase — and it is kept, deliberately.** Retiring it means re-pointing `reconcile.py`'s import *and* dropping the assertion `callouts.LABEL_PREFIX is LABEL_TO_PREFIX` in `tests/test_callouts.py::test_label_map_and_enum`. That assertion sits **inside a test that also asserts real behavior** (the full label→prefix map and the severity enum). The gate permits *deleting* a shim-existence test, never *editing* one — and deleting this one would delete live coverage of the callout contract. Retiring an alias is not worth losing that. Flagged for M37, where the test may be split. See §4. |
| `client_config.MANDATORY_SECTIONS` | A **policy** subset (which sections no profile may drop). The declaration says what parts exist, not which are droppable; there is nothing to derive this from. |
| `client_config.DEFAULT_DERIVED` / `ALL_DERIVED` / `DERIVED_ALIASES` | The v1 **manifest** vocabulary — the fallback path WP-G2 kept for when no definition resolves. |
| `scope_delta.AGENT_DERIVED_KINDS` | WP-G2 re-pointed the reader at the plan's agent-writer kinds and kept this tuple as the **documented fallback**, so a missing definition never turns the work-order CLI into a refusal. |
| `aggregate.PY_BUILDERS` | A **registry** (kind → the shipped python writer), not shape authority. WP-G2 made the plan the build *list*; `PY_BUILDERS` answers "is there a writer for this?" and refuses by name when there is not. |
| `scaffold.DERIVED_FILES` / `SPECIAL_FILES` | The v1 manifest's derived set — same fallback carve-out. |
| `scaffold._FALLBACK_PART_BODIES` | Per-part placeholder **prose**. The declaration says a procedure has an `outputs` part titled "Outputs & Evidence"; it does not say what a blank one should suggest to a drafter. Content, not shape. |
| **`scaffold._FALLBACK_SKELETON`** (G2's flagged retirement candidate) | **KEEP.** G3 evaluated the two v1 reads: `tests/test_document_profile.py:1015` and `:1025` both feed the template into `keep_sections(...)` and assert on the **filtering behavior** (a dropped section leaves, an unfiltered call returns the same object). Those are behavior tests, not shim-existence assertions — so the deletion exception does not apply and the attribute stays. It is derived from the declaration (`_fallback_skeleton()`), so no ordered section list is written twice. |

---

## 3. The absence audit — `tests/test_shape_audit_m36.py`

The acceptance's grep-level absence proof, mechanized as **6 tests**:

- `test_every_shape_literal_in_scripts_is_allowlisted` — the audit proper.
- `test_the_allowlist_has_no_stale_entries` — the list must shrink as the
  migration continues; an unmatched entry is a fiction that would hide the
  next real occurrence. (It earned its keep on day one: four
  first-draft `aggregate.py` entries were written from a substring-noisy
  scan and this test rejected all four.)
- `test_every_allowlist_entry_carries_a_reason` — an allowlist without
  reasons always passes.
- `test_no_new_shape_table_outside_its_declared_home` — the structural
  tripwire: **`SECTION_TITLES = {...}` in a new module fails here**, under
  any name, because the check is on the *literal table*, not the identifier.
- `test_the_retired_symbols_stay_retired` — §2's deletions pinned.
- `test_the_repointed_constants_track_the_declaration` — §2's re-pointings
  proven live.

**Vocabulary** is read from the declaration, never typed in the test: part
slugs, part titles, callout labels, callout prefixes (from
`kernel.load_type("activity")`), plus the two agent-written derived kinds. A
new declared part widens the audit automatically.

**Allowlist size: 21 entries** over 12 modules, keyed
`(module, category) -> ({literals}, why)`, naming **67 distinct literals** and covering **104 literal
occurrences**. Every entry carries a prose reason; the reasons are the
review record.

**Wholesale module exemptions (3):** `kernel.py`, `definitions.py`,
`render_glue.py`. `render.py` — which the acceptance bullet also exempts as
the docx adapter — is **deliberately not exempted**, and is allowlisted
entry by entry instead (one entry, `derived-kind: raci`), because it is the
module most able to hide a side channel.

**Precision rules, stated in the test's own docstring so no one mistakes the
audit for more than it is:**

- **R1** Only string literals in the parsed AST are audited. `#` comments
  never reach the AST; module/class/function **docstrings are skipped
  explicitly**. Prose cannot decide document shape.
- **R2** **Exact full-value equality, never substring.** `"IO"` inside
  `"VERSION"` is not a callout prefix; `"scope"` inside `"--scope-delta"` is
  not a part slug. This is what makes the audit enforceable rather than
  noisy — and it is also its limit: a slug assembled at runtime
  (`"quick" + "-reference"`) is invisible to it. Recorded as a limit, not
  closed: the reviewer reads diffs.
- **R3** The allowlist is **line-agnostic**. Moving code does not churn it;
  introducing a *new* audited literal into a module does fail.
- **R4** The three exemptions above (and render.py's non-exemption).
- **R5** The structural check is stricter than the literal check: a literal
  dict/list/tuple/set collecting ≥3 part slugs, ≥2 part titles, ≥3 callout
  labels or ≥3 callout prefixes is banned outside four enumerated
  `TABLE_HOMES` (`doc_model.py`, `callouts.py`, `client_config.py`'s
  `MANDATORY_SECTIONS`, `scaffold.py`'s `_FALLBACK_PART_BODIES`), each named
  with its table and its reason.

One entry is on the list as an honest **false positive** rather than being
special-cased away: `kits.py`'s `GAP_HEADER` spreadsheet column header
`"Procedure"` happens to equal a part title. Listing it keeps the rule
simple and the exception visible.

---

## 4. The shim-existence test exception was not used

The gate admits exactly one test change: **deleting** a test that asserts a
shim's existence. **G3 deleted no test, and edited no test.** The full
inventory of candidates and the ruling on each:

| Candidate | Assertion | Ruling |
|---|---|---|
| `tests/test_callouts.py::test_label_map_and_enum` | `assert callouts.LABEL_PREFIX is LABEL_TO_PREFIX` | **Existence assertion — but not deletable.** It is one line inside a test whose other assertions are behavior (the label→prefix contract, the severity enum, `PREFIXES` derivation). Deleting the test to retire an alias would trade real coverage for cosmetics; editing it is forbidden. **Kept, alias kept**, handed to close-out. |
| `tests/test_document_profile.py` (`_FALLBACK_SKELETON` reads, lines 1015 & 1025) | Feeds the template into `keep_sections` and asserts filtering behavior | **Behavior tests.** Exception does not apply; attribute kept (§2). |
| `tests/test_deterministic_layer_m36.py:246`, `:318` | Read `_FALLBACK_SKELETON` / `AGENT_DERIVED_KINDS` | **Behavior tests** (G2's own, asserting the documented fallback *works*). Kept. |

**Import-path fixes forced by a retirement: none.** Every retired symbol was
verified unreferenced before deletion (repo-wide grep including `tests/` and
the skills), so no import moved and no test needed a mechanical fix. The
spec's "list them" obligation is discharged with an empty list — which is
the expected outcome of A3's no-shims design.

---

## 5. The four proof obligations, confirmed

| # | Obligation | Evidence |
|---|---|---|
| 1 | **v1 suite green, zero edits** | `1005 passed, 0 failed`. Zero test files edited or deleted across G0–G3; G3's diff to `tests/` is one new file. |
| 2 | **Semantically identical render (A1)** | `tests/test_render_golden_m36.py::TestGolden::test_v1_render_matches_committed_golden` (empty normalized diff vs the committed golden, all three A1 parts per `test_golden_covers_all_three_a1_parts`), harness self-validated by `TestHarnessCatchesCorruption` (changed word / reordered sections / renumbered item / dropped element). Golden **not regenerated** in G3. |
| 3 | **Advisor equivalence** | `tests/test_deterministic_layer_m36.py::TestAdvisorReplayEquivalence::test_the_ladder_over_the_fixture_returns_v1s_actions_at_every_step` (aggregate → reconcile → draft_ready → render → review → done). |
| 4 | **Plan equivalence** | Central: `tests/test_plan_assembly_m36.py::TestCentralProof::test_definition_assembly_matches_the_committed_golden` + `test_the_plan_really_drove_the_assembly`. Aggregate: `tests/test_deterministic_layer_m36.py::TestAggregateFollowsThePlan::test_fixture_plan_names_exactly_v1s_python_view_set` + `test_plan_driven_run_writes_the_same_files_with_the_same_bytes_as_v1`. |

---

## 6. Open items handed to the close-out

1. **`appendix-controls` optionality.** WP-G2's opt-in register carve-out
   stands: a manifest-listed kind the plan cannot yet name still builds, and
   the manifest is that register's authority. The definition language has no
   way to express "this view exists only when the profile opts in", so the
   carve-out is the honest bridge. Closing it means an optionality concept
   in the definition (M37/M38 work, and a real language addition — it must
   not ride this gate).
2. **The skin regions no block can name.** The cover card and the M30
   appendix skin are produced by the docx adapter without a plan block
   naming them; the plan therefore does not fully describe the rendered
   artifact. Byte-neutral today (one skin, one deliverable), but a second
   skin will need them expressed as regions.
3. **`callouts.LABEL_PREFIX`.** Retire when `test_label_map_and_enum` is
   split into an existence half and a behavior half — a test edit, so it
   belongs to a ticket that is allowed to make one, not to this gate.
4. **The v1 registry's home.** A3's ruling holds through 2.0.0:
   `doc_model`/`callouts` keep the tables, parity-bonded. Moving them into
   the kernel moves the v1 parsers with them; that is a post-gate ticket.
5. **The audit's blind spot (R2).** A shape literal assembled at runtime, or
   read from a non-`scripts/` python file, is invisible to the audit.
   Recorded rather than papered over.
6. **Deferred by the spec, unchanged:** retiring the v1 per-area source
   layout (and M34's adapter) after one real centralized engagement;
   dropping the M14 profile alias (not before a major version beyond 2.0).
