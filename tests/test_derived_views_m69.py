"""M69 — the derived-view readers read the capture type.

`aggregate`, `kits` and `consolidate` all key their part reads on ACTIVITY
slugs today, so on a process-step area each one goes quietly empty. What
these pin:

* aggregate's index / role-dictionary / RACI inputs carry the TRANSFORMATION
  substance of a process-step fragment (and the CONTROL callout's declared
  `Performer` where v1 read a Quick Reference table);
* kits resolves a review-kit preparer from that same declared `Performer`,
  and falls back to the `consult-meta` roles channel when a fragment
  declares no control;
* consolidate's cross-bucket digest carries transformation text;
* nothing the three verbs write on a process-step area is silently empty
  where the same content in activity form would have been filled;
* a v1 activity area is byte-identical through all three verbs.

Fixture conventions per the house characterization files: everything under
`tmp_path`, observable results only, no repo-tracked writes.
"""
import json
from pathlib import Path

import aggregate
import client_config
import consolidate
import doc_model
import kits


SYSTEMS_YAML = """\
systems:
  - slug: netsuite
    name: NetSuite
    description: ERP of record
"""

ROLES_YAML = """\
roles:
  - slug: controller
    name: Controller
    reports_to: CFO
    responsibilities: Owns the monthly close
  - slug: ap-clerk
    name: AP Clerk
    reports_to: controller
    responsibilities: Keys and matches supplier invoices
"""


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

def _process_step_fragment(title, *, control=True, roles=("ap-clerk",),
                           performer="AP Clerk"):
    ctrl = ""
    if control:
        ctrl = f"""\
> **CONTROL — CTRL-001:** Three-way match before the invoice posts.
> - **Performer:** {performer}
> - **Comparison:** invoice against purchase order and receipt
> - **Trigger:** every supplier invoice
> - **Evidence:** the NetSuite match log
"""
    meta_roles = "".join(f"  - {r}\n" for r in roles)
    return f"""## {title}

### Scope

Supplier invoices from receipt through to posting in NetSuite.

### Inputs

- The vendor invoice PDF

### Transformation

The AP Clerk keys the invoice into NetSuite and matches it against the
purchase order the Controller approved.

> **SCREENSHOT PLACEHOLDER — SC-001:** The NetSuite invoice entry screen.

### Outputs

- A posted invoice

### Controls

{ctrl}
### Issues

> **VALIDATION REQUIRED — GAP-001:** Confirm the match tolerance threshold.
> - **Owner to confirm:** Controller

```consult-meta
systems:
  - netsuite
roles:
{meta_roles}```
"""


def _activity_fragment(title):
    return f"""## {title}

### A. Purpose & Scope

Supplier invoices from receipt through to posting in NetSuite.

### B. Quick Reference

- **Frequency:** Monthly
- **Primary Owner:** Controller
- **Preparer:** AP Clerk
- **Reviewer:** Controller

### E. Step-by-Step Procedure

#### Step 1 — Key the invoice

The AP Clerk keys the invoice into NetSuite and matches it against the
purchase order the Controller approved.

> **SCREENSHOT PLACEHOLDER — SC-001:** The NetSuite invoice entry screen.

### F. Key Controls

> **CONTROL — CTRL-001:** Three-way match before the invoice posts.

### H. Known Issues & Improvement Opportunities

> **VALIDATION REQUIRED — GAP-001:** Confirm the match tolerance threshold.
> - **Owner to confirm:** Controller

```consult-meta
systems:
  - netsuite
roles:
  - ap-clerk
```
"""


DERIVED_COMPONENTS = [
    {"file": "06_procedure-index.md", "heading": "Procedure Index", "order": 6,
     "role": "derived", "derived_kind": "procedure-index", "writer": "python"},
    {"file": "07_role-dictionary.md", "heading": "Role Dictionary", "order": 7,
     "role": "derived", "derived_kind": "role-dictionary", "writer": "python"},
]


def _write_area(folder: Path, fragments: dict) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    comps = []
    for i, slug in enumerate(fragments):
        comps.append({
            "file": f"{10 + 10 * i}_{slug}.md",
            "heading": slug.replace("-", " ").title(),
            "order": 10 + 10 * i,
            "role": "procedure", "slug": slug, "l2": "invoices",
        })
    comps += list(DERIVED_COMPONENTS)
    manifest = {
        "schema": "consult-mvp-manifest/v1",
        "area": "p2p", "l1": "Purchase to Pay",
        "title": "Purchase to Pay Processes",
        "l2_order": ["invoices"],
        "components": comps,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest),
                                          encoding="utf-8")
    for comp in comps:
        if comp["role"] == "procedure":
            (folder / comp["file"]).write_text(fragments[comp["slug"]],
                                               encoding="utf-8")
    ref = folder / "_reference"
    ref.mkdir(exist_ok=True)
    (ref / "systems.yaml").write_text(SYSTEMS_YAML, encoding="utf-8")
    (ref / "roles.yaml").write_text(ROLES_YAML, encoding="utf-8")
    return folder


def process_step_area(tmp_path: Path) -> Path:
    """A central-mode (process-step) area: the M34 ledger up the tree IS the
    mode marker `client_config.capture_type` reads."""
    root = tmp_path / "engagement"
    (root / "_sources").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text(
        "sources: []\n", encoding="utf-8")
    area = _write_area(root / "components" / "p2p", {
        "receive-invoice": _process_step_fragment("Receive Invoice"),
        "pay-invoice": _process_step_fragment(
            "Pay Invoice", control=True, performer="Controller",
            roles=("controller",)),
        "close-period": _process_step_fragment(
            "Close Period", control=False, roles=("controller",)),
    })
    assert client_config.capture_type(area) == "process-step"
    return area


def activity_area(tmp_path: Path) -> Path:
    area = _write_area(tmp_path / "cash", {
        "receive-invoice": _activity_fragment("Receive Invoice"),
    })
    assert client_config.capture_type(area) == "activity"
    return area


def _bundle(area: Path) -> dict:
    return json.loads((area / "p2p.extract.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# 1. aggregate reads the type's parts
# --------------------------------------------------------------------------- #

class TestAggregateReadsTheType:

    def test_raci_steps_text_is_the_transformation(self, tmp_path):
        area = process_step_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        raci = _bundle(area)["raci_inputs"]["receive-invoice"]
        assert raci["steps_text"].strip(), "the transformation was never read"
        assert "AP Clerk" in raci["steps_text"]
        assert "NetSuite" in raci["steps_text"]

    def test_raci_preparer_is_the_declared_performer(self, tmp_path):
        area = process_step_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        raci = _bundle(area)["raci_inputs"]
        assert raci["receive-invoice"]["preparer"] == "AP Clerk"
        assert raci["pay-invoice"]["preparer"] == "Controller"

    def test_raw_dependencies_carry_the_scope(self, tmp_path):
        area = process_step_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        dep = _bundle(area)["raw_dependencies"]["receive-invoice"]
        assert "Supplier invoices" in dep

    def test_procedure_index_owner_column_is_filled(self, tmp_path):
        area = process_step_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        index = (area / "06_procedure-index.md").read_text(encoding="utf-8")
        assert "AP Clerk" in index
        assert "Controller" in index

    def test_role_dictionary_names_the_procedures(self, tmp_path):
        area = process_step_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        roles = (area / "07_role-dictionary.md").read_text(encoding="utf-8")
        assert "[[#receive-invoice]]" in roles
        assert "AP Clerk" in roles


# --------------------------------------------------------------------------- #
# 2. kits resolves the preparer from declared data
# --------------------------------------------------------------------------- #

class TestKitsPreparer:

    def test_preparer_is_the_control_performer(self, tmp_path):
        area = process_step_area(tmp_path)
        procs, _gaps, _screens = kits.collect(area)
        assert procs["receive-invoice"]["preparer_text"] == "AP Clerk"
        assert procs["pay-invoice"]["preparer_text"] == "Controller"

    def test_preparer_falls_back_to_the_roles_channel(self, tmp_path):
        area = process_step_area(tmp_path)
        procs, _gaps, _screens = kits.collect(area)
        # close-period declares no CONTROL: the roles channel is the fallback.
        assert procs["close-period"]["preparer_text"] == "Controller"

    def test_screenshot_step_degrades_to_the_part(self, tmp_path):
        area = process_step_area(tmp_path)
        _procs, _gaps, screens = kits.collect(area)
        assert screens, "no screenshot placeholders collected"
        for s in screens:
            assert s["step"].strip(), "the screenshot has no located step"


# --------------------------------------------------------------------------- #
# 3. consolidate digests the type's parts
# --------------------------------------------------------------------------- #

class TestConsolidateDigest:

    def test_digest_carries_the_transformation(self, tmp_path):
        area = process_step_area(tmp_path)
        manifest = doc_model.load_manifest(area)
        text = consolidate.cross_brief(area, manifest)
        assert "Transformation" in text
        assert "keys the invoice into NetSuite" in text

    def test_digest_still_carries_the_scope(self, tmp_path):
        area = process_step_area(tmp_path)
        manifest = doc_model.load_manifest(area)
        text = consolidate.cross_brief(area, manifest)
        assert "Supplier invoices from receipt" in text


# --------------------------------------------------------------------------- #
# 4. the empty-read regression
# --------------------------------------------------------------------------- #

class TestNoSilentlyEmptyView:
    """The specific reads that came up empty before M69, per fragment."""

    def test_no_verb_returns_an_empty_read(self, tmp_path):
        area = process_step_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        bundle = _bundle(area)
        for slug in ("receive-invoice", "pay-invoice", "close-period"):
            assert bundle["raw_dependencies"][slug].strip(), slug
            assert bundle["raci_inputs"][slug]["steps_text"].strip(), slug
            assert bundle["raci_inputs"][slug]["preparer"].strip(), slug
        procs, _gaps, screens = kits.collect(area)
        for slug, p in procs.items():
            assert p["preparer_text"].strip(), slug
        for s in screens:
            assert s["step"].strip(), s["local"]
        manifest = doc_model.load_manifest(area)
        digest = consolidate.cross_brief(area, manifest)
        for slug in ("receive-invoice", "pay-invoice", "close-period"):
            assert f"[[{slug}]]" in digest


# --------------------------------------------------------------------------- #
# 5. v1 is byte-identical
# --------------------------------------------------------------------------- #

V1_INDEX = """\
## Procedure Index

<!-- derived: procedure-index; writer: python -->

_In-scope procedures, grouped by sub-process. Numbers are rendered late from \
the cross-reference tokens in the Ref column._

### Invoices

| Ref | Procedure | Frequency | Primary Owner |
|---|---|---|---|
| [[#receive-invoice]] | Receive Invoice | Monthly | Controller |
"""

V1_RACI = {
    "preparer": "AP Clerk",
    "reviewer": "Controller",
    "roles": ["ap-clerk"],
    "steps_text": (
        "#### Step 1 — Key the invoice\n\nThe AP Clerk keys the invoice "
        "into NetSuite and matches it against the\npurchase order the "
        "Controller approved.\n\n> **SCREENSHOT PLACEHOLDER — SC-001:** The "
        "NetSuite invoice entry screen."
    ),
}


class TestV1Unchanged:

    def test_aggregate_index_and_bundle(self, tmp_path):
        area = activity_area(tmp_path)
        assert aggregate.run(str(area)) == 0
        index = (area / "06_procedure-index.md").read_text(encoding="utf-8")
        assert index.startswith(V1_INDEX)
        bundle = json.loads(
            (area / "p2p.extract.json").read_text(encoding="utf-8"))
        assert bundle["raci_inputs"]["receive-invoice"] == V1_RACI
        assert bundle["raw_dependencies"]["receive-invoice"] == (
            "Supplier invoices from receipt through to posting in "
            "NetSuite.")

    def test_kits_collect(self, tmp_path):
        area = activity_area(tmp_path)
        procs, _gaps, screens = kits.collect(area)
        assert procs["receive-invoice"]["preparer_text"] == "AP Clerk"
        assert [s["step"] for s in screens] == ["Step 1 — Key the invoice"]

    def test_consolidate_digest(self, tmp_path):
        area = activity_area(tmp_path)
        manifest = doc_model.load_manifest(area)
        text = consolidate.cross_brief(area, manifest)
        assert "A. Purpose & Scope:" in text
        assert "B. Quick Reference:" in text
        assert "      Step 1 — Key the invoice" not in text
        assert "    Step 1 — Key the invoice" in text
        assert "      The AP Clerk keys the invoice into NetSuite and" in text
