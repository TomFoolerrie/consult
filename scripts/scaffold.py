#!/usr/bin/env python3
"""
scaffold.py — M0 confirm-gate scaffolder for the CONSULT MVP.

This is the deterministic Python half of M0. The `consult-taxonomy` agent has
already written proposals to `{area}/_reference/.proposed/` (procedures.yaml,
systems.yaml, roles.yaml, sources.yaml, optional new_buckets.yaml / glossary.yaml)
and a human has reviewed/edited them in place. Running

    python3 scripts/scaffold.py --confirm --area components/<area> [--l1 <slug>] \
        [--taxonomy skills/consult-taxonomy/reference/reference_taxonomy.yaml] \
        [--title "..."] [--subtitle "..."]

promotes `.proposed/` into the live `_reference/` (a MERGE, never a wipe), then
scaffolds `manifest.json` (v1) + one A–H skeleton per confirmed procedure + the
static front-matter files + empty derived stubs.

Nothing touches the live folder until `--confirm` is passed. The step is
idempotent: re-running with the same confirmed set is a no-op; adding one
procedure creates only its file and a manifest entry with a sparse `order`
*between* its neighbours, touching no existing file.

Ownership boundaries (see tickets/README.md):
  - `doc_model.py` is owned by M2 — imported here, only to validate what we write.
  - `procedure_skeleton.md` is owned by M1 — read if present, else fall back.

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

# doc_model.py lives beside this script (top-level scripts/). Import it to
# validate the manifest we write. It is M2-owned; we only consume its API.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import doc_model  # type: ignore
except Exception:  # pragma: no cover - doc_model is a hard dependency in practice
    doc_model = None


REPO_ROOT = Path(__file__).resolve().parent.parent

PROCEDURE_SKELETON = (
    REPO_ROOT / "skills" / "consult-drafter" / "reference" / "procedure_skeleton.md"
)
DEFAULT_TAXONOMY = (
    REPO_ROOT / "skills" / "consult-taxonomy" / "reference" / "reference_taxonomy.yaml"
)

# Registry yaml files promoted from .proposed/ -> live _reference/. procedures.yaml
# and new_buckets.yaml are CONSUMED to build the manifest but are NOT live registry
# files, so they are never promoted.
REGISTRY_FILES = ("systems.yaml", "roles.yaml", "sources.yaml", "glossary.yaml")
REGISTRY_KEYS = {
    "systems.yaml": "systems",
    "roles.yaml": "roles",
    "sources.yaml": "sources",
    "glossary.yaml": "glossary",
}

# Static, human-owned front matter (band 00–09). Kept minimal: the two files the
# folder model names explicitly. order values sit below the procedure band.
STATIC_FILES = [
    {"file": "00_document-profile.md", "heading": "Document Profile", "order": 0},
    {"file": "04_process-overview.md", "heading": "Process Overview", "order": 5},
]

# Derived stubs (band 70–99). Each is empty content + the required derived marker;
# M3 (python) and M5 (agent) own the actual generation. order == filename prefix,
# matching the manifest schema example (81 -> 81, 82 -> 82, ...).
DERIVED_FILES = [
    {"file": "70_procedure-index.md", "kind": "procedure-index", "writer": "python",
     "heading": "In-Scope Procedures", "order": 70},
    {"file": "80_role-dictionary.md", "kind": "role-dictionary", "writer": "python",
     "heading": "Role Dictionary", "order": 80},
    {"file": "81_systems.md", "kind": "systems", "writer": "python",
     "heading": "Systems & Data Inputs", "order": 81},
    {"file": "82_dependencies.md", "kind": "dependencies", "writer": "agent",
     "heading": "Key Dependencies", "order": 82},
    {"file": "84_raci.md", "kind": "raci", "writer": "agent",
     "heading": "RACI Matrix", "order": 84},
    {"file": "88_appendix-a.md", "kind": "appendix-a", "writer": "python",
     "heading": "Appendix A — Risks, Pain Points & Improvement Opportunities",
     "order": 88},
    {"file": "90_appendix-b-gaps.md", "kind": "gaps", "writer": "python",
     "heading": "Appendix B — Gap / Validation Log", "order": 90},
    {"file": "91_appendix-c-screens.md", "kind": "screens", "writer": "python",
     "heading": "Appendix C — Screenshot / Evidence Index", "order": 91},
]

PROC_BASE = 10   # first procedure order
PROC_GAP = 10    # sparse gap between procedure orders


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _dump_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def _titleize(area_slug: str) -> str:
    return " ".join(w.capitalize() for w in area_slug.replace("_", "-").split("-") if w)


def _entry_key(entry: dict) -> str | None:
    """Merge key for a registry entry: slug, else id (sources), else term."""
    for k in ("slug", "id", "term"):
        if entry.get(k):
            return str(entry[k])
    return None


def _merge_by_key(existing: list, proposed: list) -> list:
    """Merge proposed entries into existing, keyed by slug/id/term.

    New entries are appended; an entry the delta re-emits overrides the existing
    one; existing entries the delta did NOT re-emit are preserved (never wiped).
    Order: existing order first, then new entries in proposed order.
    """
    out = list(existing or [])
    index = {}
    for i, e in enumerate(out):
        k = _entry_key(e) if isinstance(e, dict) else None
        if k is not None:
            index[k] = i
    for e in (proposed or []):
        if not isinstance(e, dict):
            continue
        k = _entry_key(e)
        if k is not None and k in index:
            out[index[k]] = e          # delta re-emitted this entry -> it wins
        else:
            if k is not None:
                index[k] = len(out)
            out.append(e)
    return out


# --------------------------------------------------------------------------- #
# taxonomy
# --------------------------------------------------------------------------- #

def load_l1_buckets(taxonomy_path: Path, l1_slug: str) -> list[str]:
    """Return the L2 bucket slugs for the given L1, in taxonomy order."""
    tax = _load_yaml(taxonomy_path)
    cats = (tax.get("taxonomy") or {}).get("categories") or []
    for cat in cats:
        if cat.get("slug") == l1_slug:
            return [sc.get("slug") for sc in (cat.get("subcategories") or []) if sc.get("slug")]
    raise SystemExit(
        f"error: L1 slug {l1_slug!r} not found in taxonomy {taxonomy_path}"
    )


def compute_l2_order(procedures: list[dict], tax_buckets: list[str],
                     existing_l2_order: list[str]) -> list[str]:
    """The area's ordered L2 buckets = the ordering authority display_numbers reads.

    - Preserve any existing l2_order verbatim (ordinals must not drift on merge).
    - Append taxonomy-order buckets actually used by a procedure.
    - Append approved NEW buckets (an l2 used by a procedure but absent from the
      taxonomy) in first-seen order — the taxonomy itself is never mutated.
    """
    used: list[str] = []
    for p in procedures:
        l2 = p.get("l2")
        if l2 and l2 not in used:
            used.append(l2)

    order = list(existing_l2_order or [])
    for b in tax_buckets:                     # known buckets, taxonomy order
        if b in used and b not in order:
            order.append(b)
    for l2 in used:                           # approved new buckets, first-seen
        if l2 not in order:
            order.append(l2)
    return order


# --------------------------------------------------------------------------- #
# order assignment (sparse, insert-in-gap, renormalize only if a gap is full)
# --------------------------------------------------------------------------- #

def assign_procedure_orders(procedures: list[dict], l2_order: list[str],
                            existing_orders: dict[str, int]) -> dict[str, int]:
    """Assign a sparse global `order` to every procedure.

    Existing procedures keep their order unchanged. New procedures are inserted
    at their position (grouped by l2 in l2_order, then within bucket after the
    existing members) and given an order *between* their neighbours. If a gap is
    too tight to hold the run, the whole procedure sequence is renormalized
    (touches only the manifest, never a file) — the README-sanctioned fallback.
    """
    # Build the desired full sequence.
    seq: list[dict] = []
    by_l2: dict[str, list[dict]] = {}
    for p in procedures:
        by_l2.setdefault(p.get("l2"), []).append(p)
    ordered_l2 = list(l2_order) + [k for k in by_l2 if k not in l2_order]
    for l2 in ordered_l2:
        bucket = by_l2.get(l2, [])
        known = sorted(
            [p for p in bucket if p["slug"] in existing_orders],
            key=lambda p: existing_orders[p["slug"]],
        )
        fresh = [p for p in bucket if p["slug"] not in existing_orders]
        seq.extend(known + fresh)

    result: dict[str, int] = {}
    n = len(seq)
    i = 0
    last = 0
    while i < n:
        p = seq[i]
        if p["slug"] in existing_orders:
            result[p["slug"]] = existing_orders[p["slug"]]
            last = existing_orders[p["slug"]]
            i += 1
            continue
        j = i
        while j < n and seq[j]["slug"] not in existing_orders:
            j += 1
        run = seq[i:j]
        k = len(run)
        high = existing_orders[seq[j]["slug"]] if j < n else None
        low = last
        if high is None:
            for m, p2 in enumerate(run, start=1):
                result[p2["slug"]] = low + PROC_GAP * m
            last = low + PROC_GAP * k
        else:
            span = high - low
            if span >= k + 1:
                step = span // (k + 1)
                for m, p2 in enumerate(run, start=1):
                    result[p2["slug"]] = low + step * m
            else:
                return _renormalize(seq)   # gap exhausted
        i = j
    return result


def _renormalize(seq: list[dict]) -> dict[str, int]:
    return {p["slug"]: PROC_BASE + PROC_GAP * idx for idx, p in enumerate(seq)}


# --------------------------------------------------------------------------- #
# skeleton + stub rendering
# --------------------------------------------------------------------------- #

_FALLBACK_SKELETON = """## {heading}

<!-- unfilled -->

### A. Process Overview

TBD — What this procedure accomplishes, when it occurs, who performs it, what it
excludes, and how it connects to upstream / downstream activities.

### B. Quick Reference

- **Trigger:** TBD
- **Frequency:** TBD
- **Preparer:** TBD
- **Reviewer:** TBD
- **Primary systems / tools:** TBD
- **Key outputs:** TBD

### C. Pre-Requisites

- TBD — what must be true before the procedure begins.

### D. Inputs

- **Input 1:** TBD — source / owner.

### E. Step-by-Step Procedure

#### Step 1: TBD

TBD — Describe the step in neutral current-state procedural language.

### F. Key Controls

> **CONTROL — CTRL-001:** TBD — what is checked / reconciled / approved.
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** TBD
> - **Owner:** TBD

### G. Outputs

- **Output 1:** TBD
- **Evidence retained:** TBD

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** TBD — observed current-state friction, source-grounded.
> - **Impact:** TBD
> - **Severity:** High | Medium | Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** TBD — the proposed improvement.
> - **Addresses:** PP-001

```consult-meta
systems: []
roles:   []
```
"""


def render_skeleton(heading: str) -> str:
    """Stamp one A–H skeleton for a procedure.

    Prefers M1's `procedure_skeleton.md` (the single definition of procedure
    SHAPE): take from its first `##` line onward (dropping the doc-comment header)
    and substitute the title. Falls back to a minimal A–H shell if M1's file is
    absent. Either way the `<!-- unfilled -->` sentinel is present.
    """
    if PROCEDURE_SKELETON.is_file():
        raw = PROCEDURE_SKELETON.read_text(encoding="utf-8")
        lines = raw.splitlines(keepends=True)
        start = next((i for i, ln in enumerate(lines) if ln.startswith("## ")), None)
        if start is not None:
            body = "".join(lines[start:])
            body = body.replace("<Procedure Title>", heading)
            if not body.endswith("\n"):
                body += "\n"
            if "<!-- unfilled -->" not in body:
                # Guarantee the sentinel even if a future skeleton drops it.
                body = body.replace(
                    f"## {heading}\n", f"## {heading}\n\n<!-- unfilled -->\n", 1
                )
            return body
    return _FALLBACK_SKELETON.format(heading=heading)


def render_static(heading: str) -> str:
    return (
        f"## {heading}\n\n"
        "TBD — human-owned section. Populate before sign-off.\n"
    )


def render_derived(kind: str, writer: str, heading: str) -> str:
    return (
        f"## {heading}\n\n"
        f"<!-- derived: {kind}; writer: {writer} -->\n\n"
        "> _Pending generation._\n"
    )


# --------------------------------------------------------------------------- #
# promotion (merge) + sources stamping
# --------------------------------------------------------------------------- #

def promote_reference(area: Path) -> None:
    """MERGE `_reference/.proposed/` registry files into live `_reference/`.

    Initial run: live is empty, so this is effectively a copy. Incremental run:
    new entries are added, re-emitted entries updated, and entries the delta did
    NOT re-emit are left intact. procedures.yaml / new_buckets.yaml are NOT
    registry files and are never promoted (they only drive the manifest).
    """
    proposed = area / "_reference" / ".proposed"
    live = area / "_reference"
    live.mkdir(parents=True, exist_ok=True)

    for fname in REGISTRY_FILES:
        pfile = proposed / fname
        if not pfile.is_file():
            continue
        key = REGISTRY_KEYS[fname]
        proposed_data = _load_yaml(pfile)
        live_file = live / fname
        live_data = _load_yaml(live_file)
        merged = _merge_by_key(live_data.get(key, []), proposed_data.get(key, []))
        out = dict(live_data)
        out[key] = merged
        _dump_yaml(live_file, out)


def stamp_sources(area: Path) -> None:
    """Stamp `hash` + `state` on every source in the live sources.yaml.

    Hashing is deterministic byte-work, so it belongs here (not in the agent).
    A source with no hash yet gets sha256 of its file bytes and state `new`;
    an already-stamped source keeps its state (the orchestrator flips it to
    `processed` later, not us).
    """
    sfile = area / "_reference" / "sources.yaml"
    if not sfile.is_file():
        return
    data = _load_yaml(sfile)
    changed = False
    for src in data.get("sources", []) or []:
        if not isinstance(src, dict):
            continue
        rel = src.get("file")
        if rel:
            fpath = area / rel
            if fpath.is_file():
                digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
                if src.get("hash") != digest:
                    # Content changed (or first stamp): refresh hash. Only reset
                    # to `new` when there is no state yet — never un-process.
                    src["hash"] = digest
                    changed = True
            elif "hash" not in src:
                src["hash"] = ""
                changed = True
        if not src.get("state"):
            src["state"] = "new"
            changed = True
    if changed:
        _dump_yaml(sfile, data)


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #

def build_manifest(area: Path, l1: str, title: str, subtitle: str,
                   procedures: list[dict], l2_order: list[str],
                   proc_orders: dict[str, int]) -> dict:
    components: list[dict] = []

    for sf in STATIC_FILES:
        components.append({
            "file": sf["file"], "role": "static",
            "heading": sf["heading"], "order": sf["order"],
        })

    for p in procedures:
        slug = p["slug"]
        components.append({
            "file": f"10_{slug}.md", "role": "procedure",
            "slug": slug, "heading": p["title"], "l2": p["l2"],
            "order": proc_orders[slug],
        })

    for d in DERIVED_FILES:
        components.append({
            "file": d["file"], "role": "derived", "derived_kind": d["kind"],
            "writer": d["writer"], "heading": d["heading"], "order": d["order"],
        })

    components.sort(key=lambda c: (c["order"], c["file"]))

    return {
        "schema": "consult-mvp-manifest/v1",
        "area": area.name,
        "l1": l1,
        "l2_order": l2_order,
        "title": title,
        "subtitle": subtitle,
        "components": components,
    }


# --------------------------------------------------------------------------- #
# main confirm flow
# --------------------------------------------------------------------------- #

def resolve_l1(area: Path, arg_l1: str | None) -> str:
    if arg_l1:
        return arg_l1
    manifest_path = area / "manifest.json"
    if manifest_path.is_file():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8")).get("l1") or ""
        except Exception:
            pass
    meta = _load_yaml(area / "_reference" / ".proposed" / "area.yaml")
    if meta.get("l1"):
        return meta["l1"]
    raise SystemExit(
        "error: could not determine L1. Pass --l1 <slug> "
        "(or set l1 in _reference/.proposed/area.yaml)."
    )


def confirm(area: Path, l1_arg: str | None, taxonomy: Path,
            title_arg: str | None, subtitle_arg: str | None) -> int:
    proposed = area / "_reference" / ".proposed"
    if not proposed.is_dir():
        raise SystemExit(f"error: no proposals at {proposed} (run consult-taxonomy first)")

    procedures = _load_yaml(proposed / "procedures.yaml").get("procedures", []) or []
    if not procedures:
        raise SystemExit(f"error: no procedures in {proposed / 'procedures.yaml'}")

    # Basic proposal sanity: unique kebab slugs, every proc has an l2.
    seen = set()
    for p in procedures:
        slug = p.get("slug")
        if not slug or not p.get("l2") or not p.get("title"):
            raise SystemExit(f"error: procedure entry missing slug/l2/title: {p!r}")
        if slug in seen:
            raise SystemExit(f"error: duplicate procedure slug {slug!r}")
        seen.add(slug)

    l1 = resolve_l1(area, l1_arg)

    # 1) Promote (MERGE) the registry, then stamp deterministic byte-work.
    promote_reference(area)
    stamp_sources(area)

    # 2) Compute ordering authorities.
    tax_buckets = load_l1_buckets(taxonomy, l1)
    existing_manifest = {}
    manifest_path = area / "manifest.json"
    if manifest_path.is_file():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            existing_manifest = {}
    existing_l2_order = existing_manifest.get("l2_order", []) or []
    existing_orders = {
        c["slug"]: c["order"]
        for c in existing_manifest.get("components", [])
        if c.get("role") == "procedure" and isinstance(c.get("order"), int)
    }

    l2_order = compute_l2_order(procedures, tax_buckets, existing_l2_order)
    proc_orders = assign_procedure_orders(procedures, l2_order, existing_orders)

    # 3) Title / subtitle (arg > existing manifest > derived default).
    title = (title_arg or existing_manifest.get("title")
             or f"{_titleize(area.name)} — Desktop Procedures")
    subtitle = (subtitle_arg if subtitle_arg is not None
                else existing_manifest.get("subtitle", "Current-state desktop procedures"))

    # 4) Build + validate the manifest.
    manifest = build_manifest(area, l1, title, subtitle, procedures, l2_order, proc_orders)
    if doc_model is not None:
        errors = doc_model.validate_manifest(manifest)
        if errors:
            raise SystemExit(
                "error: scaffolded manifest failed validation:\n  - "
                + "\n  - ".join(errors)
            )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 5) Write files (idempotent: never overwrite an existing component file).
    created, skipped = [], []

    def _write_if_absent(name: str, content: str):
        fp = area / name
        if fp.exists():
            skipped.append(name)
        else:
            fp.write_text(content, encoding="utf-8")
            created.append(name)

    for sf in STATIC_FILES:
        _write_if_absent(sf["file"], render_static(sf["heading"]))
    for p in procedures:
        _write_if_absent(f"10_{p['slug']}.md", render_skeleton(p["title"]))
    for d in DERIVED_FILES:
        _write_if_absent(d["file"], render_derived(d["kind"], d["writer"], d["heading"]))

    print(f"scaffolded {area}")
    print(f"  l1={l1}  l2_order={l2_order}")
    print(f"  procedures={len(procedures)}  created={len(created)}  skipped(existing)={len(skipped)}")
    if created:
        print("  created: " + ", ".join(created))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M0 confirm-gate scaffolder")
    ap.add_argument("--confirm", action="store_true",
                    help="promote _reference/.proposed/ and scaffold the area")
    ap.add_argument("--area", required=True, help="path to the area folder")
    ap.add_argument("--l1", default=None, help="L1 taxonomy slug (else read from manifest/area.yaml)")
    ap.add_argument("--taxonomy", default=str(DEFAULT_TAXONOMY), help="path to the reference taxonomy")
    ap.add_argument("--title", default=None, help="document title override")
    ap.add_argument("--subtitle", default=None, help="document subtitle override")
    args = ap.parse_args(argv)

    if not args.confirm:
        raise SystemExit(
            "refusing to run without --confirm: this is the human confirm gate. "
            "Review _reference/.proposed/ first, then re-run with --confirm."
        )

    area = Path(args.area).resolve()
    if not area.is_dir():
        raise SystemExit(f"error: area folder not found: {area}")
    return confirm(area, args.l1, Path(args.taxonomy), args.title, args.subtitle)


if __name__ == "__main__":
    sys.exit(main())
