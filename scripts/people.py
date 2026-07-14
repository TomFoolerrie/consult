"""people.py — person → role → rank resolution for the review-kit machinery (M9).

Combines the two optional people sources:
  - `_reference/roles.yaml`  — each role's `people:` list (who holds the role)
  - `_client/org-chart.yaml` — person → title (+ reports_to), the rank authority

Rank = depth in the org chart's `reports_to` tree (root = 0). DEEPER = LOWER
rank = the PREFERRED contact — the person closest to the work answers process
questions; their manager is the natural escalation.

Everything degrades gracefully: no org chart → rank ties (first-listed wins);
no `people:` list → a role resolves to no person (callers fall back to a
role-named bucket / `unassigned`).

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def person_slug(name: str) -> str:
    """Kebab-case a person's name for folder/file naming."""
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _load_yaml(path: Path) -> dict:
    if yaml is None or not path.is_file():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


class People:
    """Resolved people model for one area folder."""

    def __init__(self, folder):
        folder = Path(folder)
        self.org: dict[str, dict] = {}        # name.lower() -> {name,title,reports_to}
        self.role_people: dict[str, list[str]] = {}   # role slug -> [names]
        self.role_names: dict[str, str] = {}          # role slug -> canonical name
        self.role_aliases: dict[str, list[str]] = {}  # role slug -> aliases

        for entry in _load_yaml(folder / "_client" / "org-chart.yaml").get("people") or []:
            if isinstance(entry, dict) and entry.get("name"):
                nm = str(entry["name"]).strip()
                self.org[nm.lower()] = {
                    "name": nm,
                    "title": str(entry.get("title") or "").strip(),
                    "reports_to": str(entry.get("reports_to") or "").strip(),
                }

        for entry in _load_yaml(folder / "_reference" / "roles.yaml").get("roles") or []:
            if not isinstance(entry, dict) or not entry.get("slug"):
                continue
            slug = str(entry["slug"])
            self.role_names[slug] = str(entry.get("name") or slug)
            self.role_aliases[slug] = [str(a) for a in (entry.get("aliases") or [])]
            self.role_people[slug] = [
                str(p).strip() for p in (entry.get("people") or []) if str(p).strip()
            ]

    # ------------------------------------------------------------------ rank
    def rank(self, name: str) -> int:
        """Depth in the reports_to tree (root=0). Unknown person → 0.

        Cycles / dangling managers terminate the walk (defensive: the org
        chart is hand-authored)."""
        depth, seen = 0, set()
        cur = self.org.get(name.strip().lower())
        while cur and cur.get("reports_to"):
            key = cur["name"].lower()
            if key in seen:
                break
            seen.add(key)
            nxt = self.org.get(cur["reports_to"].strip().lower())
            if nxt is None:
                depth += 1   # manager named but not charted: still one level up
                break
            depth += 1
            cur = nxt
        return depth

    def manager_of(self, name: str) -> str:
        entry = self.org.get(name.strip().lower())
        return (entry or {}).get("reports_to", "")

    def title_of(self, name: str) -> str:
        entry = self.org.get(name.strip().lower())
        return (entry or {}).get("title", "")

    # --------------------------------------------------------------- resolve
    def contact_for_role(self, role_slug: str) -> str:
        """The preferred contact for a role: its LOWEST-ranked (deepest) person.

        Tie → first listed in roles.yaml. Role with no people → ''."""
        candidates = self.role_people.get(role_slug) or []
        if not candidates:
            return ""
        return max(candidates, key=lambda nm: (self.rank(nm),
                                               -candidates.index(nm)))

    def match_role(self, text: str) -> str:
        """Best-effort match of free prose (a Preparer line, an Owner field)
        to a role slug via canonical names + aliases (longest match wins).
        Deterministic string work — no judgment. '' when nothing matches."""
        if not text:
            return ""
        low = text.lower()
        best, best_len = "", 0
        for slug, name in self.role_names.items():
            for label in [name] + self.role_aliases.get(slug, []):
                lab = label.lower().strip()
                if lab and lab in low and len(lab) > best_len:
                    best, best_len = slug, len(lab)
        return best

    def contact_for_text(self, text: str) -> tuple[str, str]:
        """(person, role_slug) for a free-prose role mention; ('','') if
        unresolvable, (‘’, slug) if the role matched but has no people."""
        slug = self.match_role(text)
        if not slug:
            return "", ""
        return self.contact_for_role(slug), slug
