"""M62 gate — loader vocabulary honesty: the kernel validates what it claims.

Repros F-08, F-19, F-18. docs/v2/M62-loader-vocabulary-honesty.md is the spec.
"""

import json
import textwrap
from pathlib import Path

import pytest

import definitions
import doc_model
import kernel
import ledger

RISK_TYPE = """\
type: risk-log

parts:
  - slug: summary
    title: Summary
    kind: prose
  - slug: issues
    title: Issues
    kind: prose

callouts:
  - {label: RISK, prefix: RSK, home: issues}
"""

RISK_FRAGMENT = """\
## Vendor Risk

### A. Summary

Concentration risk on the sole logistics vendor.

### B. Issues

> **RISK — RSK-001:** Sole-source dependency with no fallback contract.
"""


class TestPartAIdGrammarFromDeclarations:
    def _tdecl(self, tmp_path):
        f = tmp_path / "risk-log.yaml"
        f.write_text(RISK_TYPE, encoding="utf-8")
        return kernel.load_type_file(f)

    def test_declared_prefix_parses_with_its_kind(self, tmp_path):
        tdecl = self._tdecl(tmp_path)
        entity = kernel.parse_entity(RISK_FRAGMENT, tdecl, slug="vendor-risk")
        callouts = entity.callout_dicts()
        assert any(c.get("id") == "RSK-001" for c in callouts), (
            "the documented extension path must be usable")

    def test_undeclared_prefix_refused_listing_declared(self, tmp_path):
        tdecl = self._tdecl(tmp_path)
        bad = RISK_FRAGMENT.replace("RSK-001", "ZZZ-001")
        with pytest.raises(kernel.FragmentError) as exc:
            kernel.parse_entity(bad, tdecl, slug="vendor-risk")
        msg = str(exc.value)
        assert "ZZZ-001" in msg
        assert "declared prefixes" in msg and "RSK" in msg
        assert "e.g. RSK-001" not in msg, (
            "the error must not quote the rejected id as the example of "
            "correctness")

    def test_shipped_five_still_parse(self):
        tdecl = kernel.load_type("process-step")
        text = ("## S\n\n### A. Scope\n\nBody.\n\n### F. Issues\n\n"
                "> **PAIN POINT — PP-01:** Slow. (Severity: Low)\n")
        entity = kernel.parse_entity(text, tdecl, slug="s")
        assert any(c.get("id") == "PP-01" for c in entity.callout_dicts())


class TestPartBRepeatOverValidated:
    def _definition(self, tmp_path, over):
        f = tmp_path / "custom-doc.yaml"
        f.write_text(textwrap.dedent(f"""\
            deliverable: custom-doc
            shape:
              - id: body
                title: Body
                kind: entity-part
                binding: parts
                repeat: {{over: {over}, order: manifest}}
            bindings:
              parts:
                entities: activity
                parts: [scope]
            skin:
              format: docx
            """), encoding="utf-8")
        return f

    def test_undeclared_over_refused_at_stage2(self, tmp_path):
        f = self._definition(tmp_path, "widget")
        with pytest.raises(definitions.DefinitionError) as exc:
            definitions.load_definition_file(f)
        msg = str(exc.value)
        assert "custom-doc" in msg and "body" in msg and "widget" in msg

    def test_declared_over_still_compiles(self, tmp_path):
        f = self._definition(tmp_path, "activity")
        defn = definitions.load_definition_file(f)
        assert defn.name == "custom-doc"

    def test_shipped_definitions_still_load(self):
        root = Path(__file__).resolve().parent.parent
        for path in sorted((root / "kernel" / "deliverables").glob("*.yaml")):
            definitions.load_definition_file(path)


class TestPartCOneOrderRule:
    def _area(self, tmp_path):
        area = tmp_path / "components" / "ap"
        area.mkdir(parents=True)
        manifest = {
            "schema": "consult-mvp-manifest/v1",
            "area": "ap", "l1": "finance", "title": "AP",
            "l2_order": ["main"],
            "components": [
                {"file": "10_a.md", "heading": "A", "role": "procedure",
                 "slug": "a", "l2": "main", "order": None},
                {"file": "20_b.md", "heading": "B", "role": "procedure",
                 "slug": "b", "l2": "main", "order": 20},
            ],
        }
        (area / "manifest.json").write_text(json.dumps(manifest),
                                            encoding="utf-8")
        for name in ("10_a.md", "20_b.md"):
            (area / name).write_text(f"## {name}\n\nBody.\n",
                                     encoding="utf-8")
        return tmp_path, area

    def test_procedures_and_assemble_never_typeerror(self, tmp_path):
        _root, area = self._area(tmp_path)
        manifest = doc_model.load_manifest(area)
        procs = doc_model.procedures(manifest)
        assert [c["slug"] for c in procs] == ["a", "b"], (
            "the display_numbers rule: non-int order sorts as 0")
        doc = doc_model.assemble(area)
        assert doc is not None

    def test_validate_manifest_still_reports_the_defect(self, tmp_path):
        _root, area = self._area(tmp_path)
        manifest = doc_model.load_manifest(area)
        errors = doc_model.validate_manifest(manifest)
        assert any("order" in e for e in errors)

    def test_ledger_register_never_leaks_typeerror(self, tmp_path):
        root, area = self._area(tmp_path)
        new = root / "_sources" / "new"
        new.mkdir(parents=True)
        (new / "t.md").write_text("bytes\n", encoding="utf-8")
        try:
            sid = ledger.register(root, "t.md", {"ap": ["a"]})
            assert sid.startswith("SRC-")
            ledger.credit(root, "ap", filled=["a"])
        except ledger.LedgerError:
            pass  # a NAMED refusal is acceptable; a raw TypeError is not
        except TypeError as exc:  # pragma: no cover
            pytest.fail(f"raw TypeError escaped a named-error contract: {exc}")
