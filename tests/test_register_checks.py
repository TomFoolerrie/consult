"""M29 Part 2.1 — the register checks (built after M30).

(a) unknown register / entry reference: ERROR (id form `register#entry`,
phrase form `the <Title> register`); (b) a citable entry's distinctive value
restated in a fragment that never references the owning register: WARNING;
(c) a class-context entry (or all-context register) cited by name: ERROR.
Plus the documented boundaries: no-op outside a components/ engagement root,
unstructured pre-M30 files tolerated, mixed-class file-level phrase passes.

Register fixtures are written through registers.py's own verb (cmd_add) —
the one writer — so these tests can never drift from the entry grammar.
"""

import registers

from test_reconcile import make_area, fragment, GOOD_CALLOUTS, run


# --------------------------------------------------------------------------- #
# Fixture: an engagement root with one area + registers
# --------------------------------------------------------------------------- #

def make_engagement_area(tmp_path, body_extra=""):
    """components/cash built by test_reconcile.make_area, so the area is
    clean apart from what body_extra injects."""
    root = tmp_path / "components"
    area = root / "cash"
    area.mkdir(parents=True)
    make_area(area, {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS,
                                          body_extra=body_extra)})
    return root, area


def add_entry(root, register, eid, cls, text, provenance="SRC-004 (p2p)"):
    assert registers.cmd_add(root, register, eid, cls, text, provenance) == 0


# --------------------------------------------------------------------------- #
# (a) unknown register reference — ERROR
# --------------------------------------------------------------------------- #

def test_id_form_unknown_register_is_error(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Escalate per capex-limits#CL-1 before posting.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "UNKNOWN REGISTER 'capex-limits#CL-1'" in out
    assert "known: approval-matrix" in out


def test_id_form_unknown_entry_is_error(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Escalate per approval-matrix#AM-9 before posting.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "UNKNOWN REGISTER ENTRY approval-matrix#AM-9" in out
    assert "has entries: AM-1" in out


def test_id_form_known_entry_passes_clean(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Escalate per approval-matrix#AM-1 before posting.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 0
    assert "No blocking errors" in out


def test_phrase_form_unknown_register_is_error(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Thresholds live in the Capex Limits register.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "UNKNOWN REGISTER" in out
    assert "known: approval-matrix" in out


def test_phrase_form_normalizes_title_to_stem(tmp_path, capsys):
    """'the Approval Matrix register' passes when approval-matrix.md exists
    (case-insensitive, non-alnum → hyphens)."""
    root, area = make_engagement_area(
        tmp_path, "Thresholds live in the Approval Matrix register.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 0


def test_lowercase_business_register_phrase_never_errors(tmp_path, capsys):
    """'a post-hoc review of the payment register' is prose about a
    subsidiary ledger (the run-4 fixture's real phrasing), not a register
    reference: an UNRESOLVED all-lowercase phrase is skipped. Resolution to
    a known register stays case-insensitive (see the normalization test)."""
    root, area = make_engagement_area(
        tmp_path, "Post-hoc review of the payment register follows.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 0
    assert "UNKNOWN REGISTER" not in out


def test_markdown_anchor_is_not_a_register_reference(tmp_path, capsys):
    """A dotted link target like file.md#anchor never flags — the unknown-stem
    arm only fires on names shaped like register stems (word chars/hyphens)."""
    root, area = make_engagement_area(
        tmp_path, "See notes.md#appendix for the export layout.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 0


# --------------------------------------------------------------------------- #
# (b) restated distinctive value — WARNING
# --------------------------------------------------------------------------- #

def test_restated_dollar_value_warns_with_entry(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Anything above $25,000 needs CFO sign-off.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 0  # WARNING, not blocking
    assert "RESTATED REGISTER VALUE '$25000'" in out
    assert "restates approval-matrix#AM-1" in out
    assert "reference the register, don't restate" in out


def test_dollar_match_normalizes_comma_variants(tmp_path, capsys):
    """Entry says $25,000; prose says $25000 — still caught."""
    root, area = make_engagement_area(
        tmp_path, "Anything above $25000 needs CFO sign-off.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert "restates approval-matrix#AM-1" in out


def test_quoted_string_restated_warns(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Post them to Pending Final Review each month-end.")
    add_entry(root, "cutoffs", "CO-1", "citable",
              'Late invoices park in "Pending Final Review" until close.')
    rc, out = run(area, capsys)
    assert "RESTATED REGISTER VALUE 'Pending Final Review'" in out
    assert "restates cutoffs#CO-1" in out


def test_referencing_fragment_may_carry_the_value(tmp_path, capsys):
    """A fragment that references the owning register anywhere keeps the
    value without a warning (essential-to-execute: the human judges)."""
    root, area = make_engagement_area(
        tmp_path, "Anything above $25,000 needs CFO sign-off per "
                  "approval-matrix#AM-1.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    rc, out = run(area, capsys)
    assert rc == 0
    assert "RESTATED" not in out


def test_context_entry_values_never_warn(tmp_path, capsys):
    """Restatement guards CITABLE entries only — context values don't warn
    (their rule is (c): never cited by name at all)."""
    root, area = make_engagement_area(
        tmp_path, "Anything above $25,000 needs CFO sign-off.")
    add_entry(root, "disputes", "D-1", "context",
              "Ownership of the $25,000 threshold is disputed.")
    rc, out = run(area, capsys)
    assert "RESTATED" not in out


def test_short_and_pure_numeric_values_never_match(tmp_path, capsys):
    """Noise discipline: quoted values under 4 chars or purely numeric
    (no $) are never distinctive."""
    root, area = make_engagement_area(
        tmp_path, "Use code 42 and batch 2024 for the export.")
    add_entry(root, "codes", "C-1", "citable",
              'Export uses code "42" in batch "2024".')
    rc, out = run(area, capsys)
    assert rc == 0
    assert "RESTATED" not in out


# --------------------------------------------------------------------------- #
# (c) context entry cited by name — ERROR
# --------------------------------------------------------------------------- #

CONTEXT_MSG = "context entries are never cited by name"


def test_context_entry_cited_by_id_form_is_error(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Ownership is settled per disputes#D-1.")
    add_entry(root, "disputes", "D-1", "context",
              "Callback ownership is disputed between AP and Treasury.")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "CONTEXT ENTRY CITED" in out
    assert CONTEXT_MSG in out
    assert "cite the provenance source" in out


def test_all_context_register_phrase_reference_is_error(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Background is kept in the Disputes register.")
    add_entry(root, "disputes", "D-1", "context",
              "Callback ownership is disputed between AP and Treasury.")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "CONTEXT REGISTER CITED" in out
    assert CONTEXT_MSG in out


def test_mixed_class_register_file_level_reference_passes(tmp_path, capsys):
    """A phrase reference (no #entry) to a register holding BOTH classes is
    not (c) — only entry-level context refs and all-context files error."""
    root, area = make_engagement_area(
        tmp_path, "Thresholds live in the Approval Matrix register.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    add_entry(root, "approval-matrix", "AM-2", "context",
              "The delegation chain above VP is disputed.")
    rc, out = run(area, capsys)
    assert rc == 0


def test_citable_entry_in_mixed_register_cited_by_id_passes(tmp_path, capsys):
    root, area = make_engagement_area(
        tmp_path, "Escalate per approval-matrix#AM-1.")
    add_entry(root, "approval-matrix", "AM-1", "citable",
              "Approvals above $25,000 go to the CFO.")
    add_entry(root, "approval-matrix", "AM-2", "context",
              "The delegation chain above VP is disputed.")
    rc, out = run(area, capsys)
    assert rc == 0


# --------------------------------------------------------------------------- #
# Boundaries
# --------------------------------------------------------------------------- #

def test_checks_noop_outside_components_root(tmp_path, capsys):
    """The documented boundary: a standalone area (parent not components/)
    gets no register checks — the same prose that errors inside an
    engagement root passes here."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        "Bank Rec", GOOD_CALLOUTS,
        body_extra="Escalate per capex-limits#CL-1, see the Capex register.")})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "UNKNOWN REGISTER" not in out


def test_unstructured_register_file_is_tolerated(tmp_path, capsys):
    """A pre-M30 freeform register file resolves by NAME: a phrase reference
    to it passes (a) and never triggers (c); an id-form entry reference into
    it is tolerated (entries are unknowable until migration)."""
    root, area = make_engagement_area(
        tmp_path, "Thresholds live in the Approvals register, e.g. "
                  "approvals#anything.")
    reg = root / "_client" / "registers"
    reg.mkdir(parents=True)
    (reg / "approvals.md").write_text(
        "# Approvals\n\nFreeform pre-M30 notes, no entry headings.\n",
        encoding="utf-8")
    rc, out = run(area, capsys)
    assert rc == 0
    assert "UNKNOWN REGISTER" not in out
    assert CONTEXT_MSG not in out
