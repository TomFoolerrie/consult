#!/usr/bin/env python3
"""Validate ledgers against schema, taxonomy, and layering rules.

  validate.py --ledger-dir D --taxonomy T [--registry R | --sources-dir S] [--citation-pattern RE] [--gate LAYER]

--registry R   : consult-lint's registry.yaml. Cited ids must be active entries;
                 a cited file whose hash has drifted since registration is an error
                 (its line numbers can no longer be trusted); a cited line past the
                 file's length is an error.
--sources-dir S: legacy fallback - cited id must exist as S/src-NNN.* .
Exit 1 on any error. Warnings do not fail.
--gate themes|recommendations|initiatives|story : additionally fail if any
  proposal targeting a lower layer is still open (the "no building on
  unresolved findings" rule).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (CITES, DEFAULT_CITATION, EVIDENCE_BASIS, FINDING_TYPES, LAYERS,  # noqa: E402
                    REF_FIELD, SCHEMA, axes, current, ledger_dir, load_taxonomy)

GATE_ORDER = ["findings", "themes", "recommendations", "initiatives", "story"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ledger-dir")
    p.add_argument("--taxonomy", required=True)
    p.add_argument("--sources-dir")
    p.add_argument("--registry", help="consult-lint registry.yaml (preferred over --sources-dir)")
    p.add_argument("--consult-root", help="explicit integrated mode: CONSULT owns source integrity")
    p.add_argument("--citation-pattern", default=DEFAULT_CITATION)
    p.add_argument("--gate", choices=GATE_ORDER[1:])
    a = p.parse_args()
    if a.consult_root:
        if a.registry or a.sources_dir:
            p.error("--consult-root cannot be combined with a standalone registry or sources directory")
        a.citation_pattern = r"^SRC-\d+(:(L\d+(-L?\d+)?|R\d+))?$"

    ldir = ledger_dir(a.ledger_dir)
    tax = load_taxonomy(a.taxonomy)
    cite_re = re.compile(a.citation_pattern)
    errors, warns = [], []
    err = lambda m: errors.append(m)  # noqa: E731
    warn = lambda m: warns.append(m)  # noqa: E731

    if a.consult_root:
        from consult_bridge import review
        try:
            checked = review(a.consult_root, ldir)
            errors.extend(checked["errors"])
            warns.extend(checked["warnings"])
        except (ValueError, OSError) as exc:
            err(f"CONSULT evidence check: {exc}")

    known_sources, reg_entries, drifted = None, {}, set()
    if a.registry:
        import hashlib
        import yaml
        reg_path = Path(a.registry)
        for e in (yaml.safe_load(open(reg_path, encoding="utf-8")) or {}).get("sources", []):
            reg_entries[e["id"]] = e
            if e.get("status") == "active":
                f = reg_path.parent / e["file"]
                if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()[:16] != e["sha"]:
                    drifted.add(e["id"])
        known_sources = {i for i, e in reg_entries.items() if e.get("status") == "active"}
    elif a.sources_dir:
        known_sources = {f.stem.split(".")[0] for f in Path(a.sources_dir).iterdir()}

    data = {layer: current(ldir, layer) for layer in LAYERS}

    # --- schema + enums -------------------------------------------------
    for layer, spec in SCHEMA.items():
        if layer == "proposals":
            continue
        for id_, r in data[layer].items():
            for k in spec["required"]:
                if r.get(k) in (None, "", []):
                    err(f"{id_}: missing required field '{k}'")
            for k in spec["lists"]:
                if k in r and not isinstance(r[k], list):
                    err(f"{id_}: field '{k}' must be a list")

    def in_list(id_, field, value, allowed, what):
        if value not in (None, "", []) and value not in allowed:
            err(f"{id_}: {field}='{value}' not in {what}")

    def scale(id_, field, value, key):
        allowed = {int(k) for k in (tax.get("scales") or {}).get(key, {})}
        if value is not None and allowed and value not in allowed:
            err(f"{id_}: {field}={value!r} not in scales.{key} {sorted(allowed)}")

    def check_axes(id_, r, which):
        """Validate classification axes on a finding (which='findings') or theme (which='themes')."""
        for name, ax in axes(tax, on_theme=True if which == "themes" else None).items():
            v = r.get(name)
            req = ax.get("required", False)
            if ax.get("required_when"):
                k, want = next(iter(ax["required_when"].items()))
                req = r.get(k) == want
            if which == "themes":
                req = True  # a theme must carry every on_theme axis
            if req and v in (None, "", []):
                err(f"{id_}: axis '{name}' is required" + (f" when {ax['required_when']}" if ax.get("required_when") else ""))
                continue
            if v in (None, "", []):
                continue
            if ax.get("multi"):
                if not isinstance(v, list):
                    err(f"{id_}: axis '{name}' must be a list"); continue
                for x in v:
                    in_list(id_, name, x, ax["values"], f"axes.{name}")
            else:
                if isinstance(v, list):
                    err(f"{id_}: axis '{name}' is single-valued"); continue
                in_list(id_, name, v, ax["values"], f"axes.{name}")
            if ax.get("secondary"):
                sv = r.get(f"secondary_{name}")
                in_list(id_, f"secondary_{name}", sv, ax["values"], f"axes.{name}")
                if sv and sv == v:
                    warn(f"{id_}: secondary_{name} duplicates {name}")
            elif r.get(f"secondary_{name}"):
                warn(f"{id_}: secondary_{name} given but axis has no `secondary: true`")

    for id_, r in data["findings"].items():
        in_list(id_, "type", r.get("type"), FINDING_TYPES, "finding types")
        in_list(id_, "evidence_basis", r.get("evidence_basis"), EVIDENCE_BASIS, "evidence basis")
        scale(id_, "severity", r.get("severity"), "severity")
        check_axes(id_, r, "findings")
        # citations
        for s in r.get("sources", []):
            if not cite_re.match(s):
                err(f"{id_}: source '{s}' does not match citation pattern")
            elif known_sources is not None and s.split(":")[0] not in known_sources:
                sid = s.split(":")[0]
                st = reg_entries.get(sid, {}).get("status")
                hint = f" (registry status: {st}, superseded_by {reg_entries[sid].get('superseded_by')})" if st else ""
                err(f"{id_}: source '{sid}' is not an active source{hint}")
            elif s.split(":")[0] in drifted:
                err(f"{id_}: source '{s}' file has changed since registration; line numbers unverifiable")
            elif ":" not in s:
                warn(f"{id_}: source '{s}' has no line pinpoint")
            else:
                sid, rng = s.split(":", 1)
                nums = [int(x) for x in re.findall(r"\d+", rng)]
                n = reg_entries.get(sid, {}).get("lines")
                if n and max(nums) > n:
                    err(f"{id_}: source '{s}' cites line {max(nums)} but file has {n} lines")
        for rel in r.get("related", []):
            if rel not in data["findings"]:
                warn(f"{id_}: related '{rel}' is not an active finding")
        obs = r.get("observation", "")
        if len(obs) > 600:
            warn(f"{id_}: observation is {len(obs)} chars - probably two findings; split or tighten (no need to explain, just fix or move on)")
        if r.get("type") == "open_item" and r.get("evidence_basis") == "observed":
            warn(f"{id_}: open_item with evidence_basis=observed - nothing was observed if the topic didn't come up; use stated or inferred")

    for id_, t in data["themes"].items():
        check_axes(id_, t, "themes")
        for name in axes(tax, on_theme=True):
            fvals = set()
            for fid in t.get("findings", []):
                f = data["findings"].get(fid, {})
                v = f.get(name)
                fvals |= set(v) if isinstance(v, list) else {v}
                fvals.add(f.get(f"secondary_{name}"))
            if t.get(name) and fvals and t[name] not in fvals:
                warn(f"{id_}: theme {name} '{t[name]}' matches none of its findings' provisional values "
                     f"{sorted(x for x in fvals if x)} - re-check the root cause or propose retags")

    for id_, r in data["initiatives"].items():
        scale(id_, "impact", r.get("impact"), "impact")
        scale(id_, "effort", r.get("effort"), "effort")
        for d in r.get("dependencies", []):
            if d not in data["initiatives"]:
                err(f"{id_}: dependency '{d}' is not an active initiative")

    # --- layer-below rule ---------------------------------------------------
    for layer, below in CITES.items():
        field = REF_FIELD[layer]
        prefix = LAYERS[below]["prefix"]
        for id_, r in data[layer].items():
            refs = r.get(field, [])
            if not refs:
                err(f"{id_}: must cite at least one {below[:-1]}")
            for ref in refs:
                if cite_re.match(ref):
                    err(f"{id_}: cites raw source '{ref}'; {layer} may only cite {below}")
                elif not ref.startswith(prefix + "-"):
                    err(f"{id_}: '{ref}' is not a {below[:-1]} id")
                elif ref not in data[below]:
                    err(f"{id_}: '{ref}' is not an active {below[:-1]}")
            # recommendations may additionally cite findings directly
            if layer == "recommendations":
                for f in r.get("findings", []):
                    if f not in data["findings"]:
                        err(f"{id_}: finding '{f}' is not active")

    # --- proposal gate ------------------------------------------------------
    if a.gate:
        lower = GATE_ORDER[:GATE_ORDER.index(a.gate)]
        lower_prefixes = {LAYERS[l]["prefix"] for l in lower if l in LAYERS}
        for id_, pr in current(ldir, "proposals", include_retired=True).items():
            if pr.get("status") == "open" and pr["target"].split("-")[0] in lower_prefixes:
                err(f"GATE {a.gate}: proposal {id_} on {pr['target']} is still open "
                    f"(owner {pr.get('target_author')})")

    for w in warns:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    summary = {k: len(v) for k, v in data.items()}
    print(f"\n{summary} | {len(errors)} errors, {len(warns)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
