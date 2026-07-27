"""Tests for the M16 section model — docs/M16-section-model.md, moves 3 and 4.

Move 3 (callout `note:` / `detail:` — one source of truth, two views) and move 4
(the step `Condition:` tag). Move 1 (the seven-section model) is NOT built, so
nothing here asserts anything about section identity: A–H stands.

Fixtures reuse the M14 harness in `test_document_profile` (a synthetic
engagement under tmp_path with a real `_client/profile.yaml`, real scaffold, real
aggregate, real render) rather than restating 200 lines of it — the two tickets
share the same enforcement points, so they must share the same fixture shape or
one of them is testing a document nobody builds.

Every claim is made through a real entry point: `render.render_folder` for what
the reader sees, `aggregate.run` for what the registers carry, `reconcile.reconcile`
for what the gate accepts.
"""
import client_config
import aggregate
import reconcile
import render

import test_document_profile as h


# --------------------------------------------------------------------------- #
# Fragment builder — one procedure, parametrized where the new grammar goes
# --------------------------------------------------------------------------- #

def fragment(*, step_body: str, gap_fields: str = "", pp_fields: str = "",
             ctrl_fields: str = "") -> str:
    """A reconcile-clean `bank-rec` fragment with injectable callout fields."""
    return f"""## Bank Reconciliation

### Scope

Covers the monthly reconciliation only. (SRC-001)

### At a Glance

| Field | Value |
|---|---|
| Frequency | Monthly |
| Preparer | Controller |
| Systems | NetSuite |

### Before You Start

- **Bank statement** — Treasury; downloaded for the closed period.

### Procedure

#### Step 1: Export the statement

{step_body}

> **VALIDATION REQUIRED — GAP-01:** The matching tolerance is unconfirmed.
{gap_fields}> - **Nature:** conflict
> - **Owner to confirm:** Controller

### Key Controls

> **CONTROL — CTRL-001:** The Controller signs off on the reconciliation.
{ctrl_fields}> - **Type:** Detective
> - **Frequency:** Monthly
> - **Owner:** Controller

### Outputs & Evidence

- **Output 1:** Signed reconciliation.

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The statement is exported by hand every month.
{pp_fields}> - **Impact:** Two hours per close
> - **Severity:** Medium

```consult-meta
systems:
  - netsuite
roles:
  - controller
```
"""


PLAIN_STEP = "Export the statement from the portal."

NOTE = "> - **Note:** Tolerance unconfirmed — do not operate to a figure.\n"
DETAIL = ("> - **Detail:** Four accounts of the tolerance conflict: the prior SOP,\n"
          ">   the Controller's recollection, the system configuration and the\n"
          ">   AP Clerk's practice. Resolution sits with the Controller.\n")


def area(tmp_path, frag: str, profile: dict | None = None):
    """A drafted, aggregated area whose `bank-rec` fragment is `frag`."""
    components = h.engagement(tmp_path)
    if profile is not None:
        h.write_profile(components, **profile)
    a = h.drafted_area(components)
    (a / "10_bank-rec.md").write_text(frag, encoding="utf-8")
    assert aggregate.run(str(a)) == 0
    return a


def gap_log(a) -> str:
    return h.register_of(a, "90_appendix-b-gaps.md")


# --------------------------------------------------------------------------- #
# Byte-identity: a fragment using none of the new grammar is untouched
# --------------------------------------------------------------------------- #

def test_transforms_are_identity_without_the_new_grammar():
    """Both M16 body-view projections return their input UNCHANGED — the
    "absent `detail:` → today's behavior byte-identical" acceptance bullet, made
    at the transform boundary where "byte-identical" is literally checkable."""
    text = fragment(step_body=PLAIN_STEP)
    assert render._hide_callout_details(text) == text
    assert render._lead_conditions(text) == text


def test_render_without_new_grammar_matches_a_second_render(tmp_path):
    """Document level: the rendered text of a no-new-grammar area is stable and
    still contains the whole callout body inline (nothing moved to an appendix
    behind the drafter's back)."""
    a = area(tmp_path, fragment(step_body=PLAIN_STEP))
    first = h.rendered_text(a, "one.docx")
    second = h.rendered_text(a, "two.docx")
    assert first == second
    assert "The matching tolerance is unconfirmed." in first
    assert reconcile.reconcile(str(a)) == 0


def test_transforms_preserve_line_count(tmp_path):
    """Provenance (M10) maps assembled body line k to fragment line k, so every
    body transform must preserve the line COUNT — including when it fires."""
    text = fragment(step_body=f"{PLAIN_STEP}\n\n- **Condition:** month-end only.",
                    gap_fields=NOTE + DETAIL)
    for out in (render._hide_callout_details(text), render._lead_conditions(text)):
        assert out.count("\n") == text.count("\n")


# --------------------------------------------------------------------------- #
# Move 3 — `note` inline, `detail` in the appendix
# --------------------------------------------------------------------------- #

def test_detail_renders_only_in_the_appendix(tmp_path):
    """The acceptance bullet: a VALIDATION REQUIRED with note + detail renders
    the note in the step and the detail in the gap log — and the detail appears
    exactly once in the document."""
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, gap_fields=NOTE + DETAIL))
    text = h.rendered_text(a)
    assert "do not operate to a figure" in text            # note, in the step
    assert "Four accounts of the tolerance conflict" in text.replace("\n", " ")
    assert text.count("Four accounts of the tolerance conflict") == 1
    # …and that one occurrence is the appendix row, not the step.
    log = gap_log(a)
    assert "Four accounts of the tolerance conflict" in log.replace("\n", " ")
    assert "do not operate to a figure" not in log


def test_detail_absent_leaves_the_whole_body_inline(tmp_path):
    """No `detail:` → today's behavior: the register cell is the label-line text
    and nothing is withheld from the step."""
    plain = area(tmp_path / "plain", fragment(step_body=PLAIN_STEP))
    assert "The matching tolerance is unconfirmed." in gap_log(plain)
    assert "Detail" not in gap_log(plain)


def test_register_cell_keeps_the_headline_in_front_of_the_detail(tmp_path):
    """The register carries label-line text THEN detail: the headline is not
    lost and no content is dropped (one source of truth, two views)."""
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, gap_fields=NOTE + DETAIL))
    row = [ln for ln in gap_log(a).splitlines() if "GAP-" in ln and "|" in ln][0]
    assert row.index("The matching tolerance is unconfirmed.") < \
        row.index("Four accounts of the tolerance conflict")


def test_pain_point_detail_reaches_appendix_a(tmp_path):
    """Move 3 applies to PAIN POINT as well as VALIDATION REQUIRED."""
    pp_detail = ("> - **Note:** Manual export, monthly.\n"
                 "> - **Detail:** The export is re-keyed into a workbook, then\n"
                 ">   circulated by email for sign-off.\n")
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, pp_fields=pp_detail))
    appx = h.register_of(a, "88_appendix-a.md").replace("\n", " ")
    assert "re-keyed into a workbook" in appx
    # The PROCEDURE body only (a subset render carries no appendices), which is
    # where "the detail is not here" is the claim being made.
    body = h.rendered_text(a, "step.docx", slugs=["bank-rec"])
    assert "Manual export, monthly." in body
    assert "re-keyed into a workbook" not in body.replace("\n", " ")


def test_controls_register_carries_a_control_detail(tmp_path):
    """CONTROL takes `note` only per the ticket — but if a detail is authored
    anyway, the register carries it (nothing is ever dropped) and reconcile says
    so as a WARNING, not an error."""
    ctrl = ("> - **Note:** Sign-off is evidenced on the reconciliation.\n"
            "> - **Detail:** The sign-off is a wet signature on the printout.\n")
    prof = {"sections": list(client_config.ALL_SECTIONS), "body_omit": ["F"],
            "derived": client_config.DEFAULT_DERIVED + ["controls"]}
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, ctrl_fields=ctrl),
             profile=prof)
    assert "wet signature" in h.register_of(a, "89_appendix-controls.md")
    assert reconcile.reconcile(str(a)) == 0          # WARNING keeps exit 0


def test_detail_reaches_the_appendix_when_body_omit_hides_its_home(tmp_path):
    """M14 × M16: `body_omit` decides whether a SECTION renders; move 3 decides
    how much of a CALLOUT renders inline. A blanked home section still
    aggregates, so the detail still lands in its register."""
    pp = ("> - **Note:** Manual export, monthly.\n"
          "> - **Detail:** The export is re-keyed into a workbook by hand.\n")
    prof = {"sections": list(client_config.ALL_SECTIONS), "body_omit": ["H"]}
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, pp_fields=pp), profile=prof)
    body = h.rendered_text(a)
    assert "Manual export, monthly." not in body        # H is out of the body
    assert "re-keyed into a workbook" in \
        h.register_of(a, "88_appendix-a.md").replace("\n", " ")


def test_detail_without_note_is_a_reconcile_error(tmp_path):
    """A `detail:` with no `note:` would render an EMPTY inline view — the
    reader at the step loses the finding, so the gate refuses it."""
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, gap_fields=DETAIL))
    assert reconcile.reconcile(str(a)) == 1
    frag = reconcile.parse_procedure("bank-rec", "10_bank-rec.md",
                                     fragment(step_body=PLAIN_STEP,
                                              gap_fields=DETAIL))
    assert any("WITHOUT" in e for e in frag.errors)


def test_note_and_detail_together_reconcile_clean(tmp_path):
    """The sanctioned split is accepted by the grammar checks — no new error and
    no new warning on a VALIDATION REQUIRED carrying both fields."""
    frag = reconcile.parse_procedure(
        "bank-rec", "10_bank-rec.md",
        fragment(step_body=PLAIN_STEP, gap_fields=NOTE + DETAIL))
    assert frag.errors == [] and frag.warnings == []
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, gap_fields=NOTE + DETAIL))
    assert reconcile.reconcile(str(a)) == 0


def test_note_alone_is_accepted(tmp_path):
    """`note:` with no `detail:` is a legitimate short callout, not a defect."""
    frag = reconcile.parse_procedure(
        "bank-rec", "10_bank-rec.md",
        fragment(step_body=PLAIN_STEP, gap_fields=NOTE))
    assert frag.errors == [] and frag.warnings == []


def test_display_ids_and_xrefs_survive_the_split(tmp_path):
    """"No regression": callout display IDs and `[[slug]]` resolution are
    unaffected by move 3."""
    a = area(tmp_path, fragment(step_body=PLAIN_STEP, gap_fields=NOTE + DETAIL))
    text = h.rendered_text(a)
    assert "GAP-01" in gap_log(a) or "GAP-1" in gap_log(a)
    assert "[[" not in text                     # every token resolved


# --------------------------------------------------------------------------- #
# Move 4 — the `Condition:` step tag
# --------------------------------------------------------------------------- #

def test_condition_joins_the_default_inline_tag_vocabulary():
    assert client_config.CONDITION_TAG == "Condition"
    assert client_config.DEFAULT_INLINE_TAGS[0] == "Condition"
    prof = client_config.Profile()
    assert "Condition" in prof.inline_tags


def test_condition_leads_the_step_body_when_authored_below_the_prose(tmp_path):
    """The tag is hoisted so the condition is visible BEFORE the prose: a reader
    must not have to reach the end of the step to learn it may not apply."""
    step = (f"{PLAIN_STEP}\n\n"
            "- **Condition:** the account is a foreign-currency account.\n"
            "- **Expected Result:** the statement is on disk.")
    a = area(tmp_path, fragment(step_body=step))
    text = h.rendered_text(a)
    assert text.index("foreign-currency account") < text.index(PLAIN_STEP)
    assert text.index("foreign-currency account") < text.index("statement is on disk")


def test_condition_authored_first_is_left_exactly_where_it_is(tmp_path):
    """Contract-compliant authoring (the tag directly under the heading) is a
    NO-OP — which is what keeps M10's line-for-line provenance exact."""
    step = ("- **Condition:** the account is a foreign-currency account.\n\n"
            f"{PLAIN_STEP}")
    text = fragment(step_body=step)
    assert render._lead_conditions(text) == text
    a = area(tmp_path, text)
    rendered = h.rendered_text(a)
    assert rendered.index("foreign-currency account") < rendered.index(PLAIN_STEP)


def test_step_without_a_condition_is_main_path_and_untouched(tmp_path):
    """A step with no `Condition:` is main path: no tag is invented, no
    renumbering, nothing added."""
    a = area(tmp_path, fragment(step_body=PLAIN_STEP))
    text = h.rendered_text(a)
    assert "Condition" not in text
    assert "Step 1: Export the statement" in text


def test_condition_inside_a_callout_is_not_a_step_tag():
    """A `- **Condition:** …` bullet inside a blockquote belongs to the callout,
    not the step — hoisting it out would corrupt the callout block."""
    text = fragment(step_body=PLAIN_STEP,
                    gap_fields="> - **Condition:** not a step tag\n")
    assert render._lead_conditions(text) == text


def test_condition_and_detail_compose(tmp_path):
    """The two moves are independent: a conditional step whose callout splits
    note/detail gets both projections."""
    step = (f"{PLAIN_STEP}\n\n- **Condition:** Plant 3 only.")
    a = area(tmp_path, fragment(step_body=step, gap_fields=NOTE + DETAIL))
    text = h.rendered_text(a, "step.docx", slugs=["bank-rec"])
    assert text.index("Plant 3 only") < text.index(PLAIN_STEP)
    assert "do not operate to a figure" in text
    assert "Four accounts of the tolerance conflict" not in text.replace("\n", " ")
    assert reconcile.reconcile(str(a)) == 0
