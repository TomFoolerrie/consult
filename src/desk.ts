/**
 * desk — the ONE derived picture, now PURE (A18 split, M3).
 *
 * Owns: NOTHING. The A9/A15 merges welded the system's purest reads to
 * its only machine-writes; A18 split them back along the store line —
 * the machinery's hand (git, sessions, budget, gates) lives in
 * record.ts. This module writes nothing, caches nothing, ever: the
 * module now matches its own doctrine.
 *
 * state() DESCRIBES, never commands — one snapshot the consultant
 * consults; report() is its printable form. locate/health is snapshot
 * material (A18, absorbing engagement.locate): the root is the
 * directory holding _sources/; an engagement-shaped tree without the
 * marker is a named CONTRADICTION whose `repair` field names the one
 * verb allowed to run. "All quiet" requires positive evidence —
 * quiet-by-damage is a contradiction, never done.
 *
 * After a fold-in the consultant edits capture, checks, checkpoints —
 * and state() already shows which sources retired and which asks
 * settled, because the capture diff IS the credit (A18).
 *
 * BARE-ENGAGEMENT DEFAULTS, pinned: budget before budgetSet is
 * {limit: 0, spent: 0, remaining: 0} (nothing auto-proceeds until a
 * budget is set); a root that is not a git repo reports git.clean:
 * false with a note naming it; pinnedShapes lists ONLY definitions the
 * engagement has pinned — shipped definitions are NOT auto-pinned.
 *
 * Holds do not exist as machinery (ROT-4): "ask first" is a state-pad
 * commitment the consultant obeys.
 */
import { existsSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { execSync } from "node:child_process";
import * as kernel from "./kernel.ts";
import * as ledger from "./ledger.ts";
import * as asksMod from "./asks.ts";
import * as definitions from "./definitions.ts";
import * as record from "./record.ts";
import type { CoverageStatus, EngagementHealth, Standing } from "./types.ts";

export interface Snapshot {
  health: EngagementHealth;
  unrouted: string[];
  coverage: NodeCoverage[];        // per taxonomy node, recomputed
  needs: Need[];                   // what each pinned shape still lacks
  askDebts: { unsettled: number };
  pinnedShapes: { name: string; serviceable: boolean }[];
  git: { clean: boolean; note?: string };
  budget: { limit: number; spent: number; remaining: number };
}
export interface NodeCoverage { slug: string; status: CoverageStatus; conflicts: string[]; }
export interface Need { shape: string; part: string; standing: Standing; }

/** walk up to the _sources/ marker; absence and contradiction are named results (A18, from engagement.ts) */
export function locate(path: string): { root: string; health: EngagementHealth } {
  let dir = resolve(path);
  while (true) {
    if (existsSync(join(dir, "_sources"))) return { root: dir, health: { kind: "ok" } };
    const up = dirname(dir);
    if (up === dir) break;
    dir = up;
  }
  const looksLike = ["capture", "_registers", "STATE.md"].some(m => existsSync(join(resolve(path), m)));
  return { root: resolve(path), health: { kind: "contradiction",
    what: looksLike ? "engagement-shaped tree without the _sources/ marker" : "no engagement here: no _sources/ marker on this path or above",
    repair: "route" } };
}
/** the engagement snapshot — describes, never commands */
export function state(root: string): Snapshot {
  const health = locate(root).health;
  const st = health.kind === "ok" ? ledger.status(root) : { unrouted: [], entries: [], consumed: new Map(), outstanding: new Map() };
  let git: Snapshot["git"];
  try {
    const dirty = execSync("git status --porcelain", { cwd: root, stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
    git = dirty ? { clean: false, note: "uncommitted changes" } : { clean: true };
  } catch { git = { clean: false, note: "not a git repository" }; }
  const pinnedShapes = health.kind === "ok"
    ? definitions.pinned(root).map(d => ({ name: d.name, serviceable: definitions.serviceability(d, root).length === 0 }))
    : [];
  return {
    health, unrouted: st.unrouted,
    coverage: health.kind === "ok" ? coverage(root) : [],
    needs: health.kind === "ok" ? needs(root) : [],
    askDebts: { unsettled: health.kind === "ok" ? asksMod.unsettled(root).length : 0 },
    pinnedShapes, git,
    budget: health.kind === "ok" ? record.budget(root) : { limit: 0, spent: 0, remaining: 0 },
  };
}
/** the printable form — the consultant's sitting picture */
export function report(root: string): string {
  const s = state(root);
  const lines = [
    `health: ${s.health.kind}${s.health.kind === "contradiction" ? ` — ${s.health.what} (repair: ${s.health.repair})` : ""}`,
    `unrouted: ${s.unrouted.length}`,
    `coverage: ${s.coverage.map(c => `${c.slug}:${c.status}`).join(" ") || "(no taxonomy yet)"}`,
    `needs: ${s.needs.length}`, `unsettled asks: ${s.askDebts.unsettled}`,
    `pinned: ${s.pinnedShapes.map(p => `${p.name}${p.serviceable ? "" : " (not serviceable)"}`).join(", ") || "none"}`,
    `git: ${s.git.clean ? "clean" : s.git.note}`,
    `budget: ${s.budget.remaining}/${s.budget.limit} remaining`,
  ];
  return lines.join("\n");
}
/** pure read: per-node coverage status + lens conflicts, recomputed every call */
export function coverage(root: string): NodeCoverage[] {
  const ents = kernel.entities(root);
  return kernel.taxonomy(root).map(n => {
    const matching = ents.filter(e => e.slug === n.slug || e.slug.startsWith(n.slug + "-"));
    const conflicts: string[] = [];
    let status: CoverageStatus = "outstanding";
    for (const e of matching) {
      for (const q of kernel.openQuestions(e)) {
        const srcs = (q.fields.get("sources") ?? "").split(",").filter(x => x.trim()).length;
        if (srcs >= 2) conflicts.push(q.addr);
      }
    }
    if (conflicts.length) status = "contested";
    else if (matching.some(e => e.statements.some(st => st.cites.length > 0))) status = "evidenced";
    else if (matching.some(e => e.statements.length > 0)) status = "claimed";
    return { slug: n.slug, status, conflicts };
  });
}
/** pure read: what a pinned shape (or all) still lacks — standing state as a read */
export function needs(root: string, deliverable?: string): Need[] {
  const shapes = definitions.pinned(root).filter(d => !deliverable || d.name === deliverable);
  const out: Need[] = [];
  for (const d of shapes) for (const g of definitions.serviceability(d, root)) {
    const standing: Standing = { kind: "absent", question: `${d.name}#${g.binding}` };
    out.push({ shape: d.name, part: g.binding, standing });
  }
  return out;
}
