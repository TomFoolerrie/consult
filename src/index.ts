/**
 * index — progressive disclosure (A22). PURE.
 *
 * Owns: nothing. Writes nothing, caches nothing. Three tiers, every
 * store: INDEX (one line per item — what exists) → CARD (one fixed
 * shape — what it is) → CONTENT (opened only when the card says yes).
 * An agent may stop at any tier; a brief carries the first two and
 * names the third by path.
 *
 * ONE CARD SCHEMA everywhere — the A20 scan template (title, kind,
 * summary, keyItems, then kind-specific sections). WHERE it lives
 * depends on whether we authored the file:
 *   client sources          → _sources/scans/SRC-nnn.yaml (the scan)
 *   markdown we authored    → the file's frontmatter
 *   yaml we authored        → the file's top-level `card:` key — NEVER its
 *                             top-level keys (the body is content, and a body
 *                             with a `summary` key is not a card)
 *   anything else we made   → a sidecar beside it: <stem>.card.yaml
 *   capture fragments       → the `scope:` head key (what it is ABOUT — intent,
 *                             not summary, so it cannot go stale)
 *   skills                  → the skill file already is one
 * The registers are small enough that the whole file is its own card;
 * STATE.md and OBJECTIVE.md are read whole every sitting. Neither is
 * indexed.
 *
 * INDEX FILES ARE NEVER STORED (a capture manifest is outlawed, A14):
 * this module walks the folder on every call. The ledgers are truth,
 * not cache, and are read as such.
 *
 * NOTHING IS HIDDEN: an item without a card is listed with "(no card)";
 * an orphan sidecar is listed as kind orphan-card; a lineage note as
 * kind lineage; a registered synthesis artifact shows ONE card on both
 * its lines (source and artifact), cross-referenced by SRC id. Dotfiles
 * are not artifacts. card() refuses an ambiguous ref by name rather
 * than silently shadowing.
 */
import { parse } from "yaml";
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, basename, extname, relative, normalize, sep } from "node:path";
import * as ledger from "./ledger.ts";
import * as kernel from "./kernel.ts";
import * as brief from "./brief.ts";
import type { Card, SrcId } from "./types.ts";

export type Store = "_sources" | "_synthesis" | "capture" | "_skills";
export const STORES: readonly Store[] = ["_sources", "_synthesis", "capture", "_skills"];
export interface IndexLine { store: Store; ref: string; title: string; kind: string; summary: string; content?: string; src?: SrcId; }

const NO_CARD = "(no card)";
const isSidecar = (f: string) => f.endsWith(".card.yaml");
const isLineage = (f: string) => /-lineage\.md$/.test(f);

function readYaml(p: string): Record<string, unknown> | undefined {
  try { const r = parse(readFileSync(p, "utf8")); return r && typeof r === "object" ? r as Record<string, unknown> : undefined; }
  catch { return undefined; }
}
const asCard = (raw: unknown): Card | undefined =>
  raw && typeof raw === "object" && typeof (raw as Card).summary === "string" ? raw as Card : undefined;
/** a card from an authored file's head: md frontmatter, or a yaml file's `card:` key */
function headCard(p: string): Card | undefined {
  const ext = extname(p);
  if (ext === ".md") {
    const m = /^---\n([\s\S]*?)\n---/.exec(readFileSync(p, "utf8"));
    if (!m) return undefined;
    try { return asCard(parse(m[1]!)); } catch { return undefined; }
  }
  if (ext === ".yaml" || ext === ".yml") return asCard(readYaml(p)?.card);
  return undefined;
}
/** the card for one synthesis artifact: sidecar first, then the file's own head */
export function synthesisCard(root: string, file: string): Card | undefined {
  const side = ledger.sidecarPath(join(root, file));
  if (existsSync(side)) return asCard(readYaml(side));
  return asCard(headCard(join(root, file)));
}
/** every file under _synthesis/ (root-relative, sorted), dotfiles excluded */
function synthesisFiles(root: string): string[] {
  const dir = join(root, "_synthesis");
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  const walk = (d: string) => { for (const f of readdirSync(d)) {
    if (f.startsWith(".")) continue;
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p); else out.push(relative(root, p));
  } };
  walk(dir);
  return out.sort();
}
/** every synthesis ARTIFACT — sidecars and lineage notes are not artifacts (they are about one) */
export function synthesisArtifacts(root: string): string[] {
  return synthesisFiles(root).filter(f => !isSidecar(f) && !isLineage(f));
}
/** a sidecar whose stem owns no artifact — listed, never hidden */
function orphanSidecars(root: string): string[] {
  const all = synthesisFiles(root);
  const owned = new Set(all.filter(f => !isSidecar(f)).map(f => ledger.sidecarPath(f)));
  return all.filter(f => isSidecar(f) && !owned.has(f));
}

function line(store: Store, ref: string, c: Card | undefined, fallbackTitle: string, fallbackKind: string, content?: string): IndexLine {
  const l: IndexLine = { store, ref,
    title: (c?.title as string | undefined) ?? fallbackTitle,
    kind: (c?.kind as string | undefined) ?? fallbackKind,
    summary: c?.summary ?? NO_CARD };
  if (content) l.content = content;
  return l;
}
function sourceCard(root: string, e: ledger.LedgerEntry): Card | undefined {
  if (e.scan && existsSync(join(root, e.scan))) return asCard(readYaml(join(root, e.scan)));
  // a registered synthesis artifact: ONE card — fall back to the producer's, so the two lines never disagree
  if (e.file.startsWith("_synthesis/")) return synthesisCard(root, e.file);
  return undefined;
}
/** the index: one line per item, every store (or one), read from cards — recomputed on every call */
export function cards(root: string, store?: Store): IndexLine[] {
  if (store && !STORES.includes(store)) throw new Error(`index: no store named ${store} (stores: ${STORES.join(", ")})`);
  const out: IndexLine[] = [];
  const want = (s: Store) => !store || store === s;
  const entries = ledger.status(root).entries;
  if (want("_sources")) for (const e of entries)
    out.push(line("_sources", e.id, sourceCard(root, e), basename(e.file), e.provenance ?? "client", e.file));
  if (want("_synthesis")) {
    for (const f of synthesisArtifacts(root)) {
      const l = line("_synthesis", f, synthesisCard(root, f), basename(f), "artifact", f);
      const reg = entries.find(e => e.file === f); if (reg) l.src = reg.id;
      out.push(l);
    }
    for (const f of orphanSidecars(root)) out.push(line("_synthesis", f, undefined, basename(f), "orphan-card", f));
    for (const f of synthesisFiles(root).filter(isLineage)) out.push(line("_synthesis", f, asCard(headCard(join(root, f))), basename(f), "lineage", f));
  }
  if (want("capture")) {
    for (const n of kernel.taxonomy(root)) out.push(line("capture", n.slug, n.scope ? { title: n.slug, kind: "taxonomy-node", summary: n.scope, keyItems: [] } : undefined, n.slug, "taxonomy-node", join("capture/_taxonomy", `${n.slug}.yaml`)));
    for (const e of kernel.entities(root)) out.push(line("capture", e.slug, e.scope ? { title: e.slug, kind: "process-step", summary: e.scope, keyItems: [] } : undefined, e.slug, "process-step", join("capture", `${e.slug}.yaml`)));
  }
  if (want("_skills")) for (const s of brief.skills(root))
    out.push(line("_skills", s.name, { title: s.name, kind: "skill", summary: s.mission, keyItems: [] }, s.name, "skill"));
  return out;
}
/** the printable index — what a brief or a fresh sitting reads before opening anything */
export function render(root: string, store?: Store): string {
  return cards(root, store).map(l => `${l.store}  ${l.ref}  ·  ${l.title}  ·  ${l.kind}  —  ${l.summary}${l.src ? `  (${l.src})` : ""}`).join("\n");
}
/** open one full card by ref: SRC id · synthesis path · capture slug · skill name — unknown or ambiguous is a named refusal */
export function card(root: string, ref: string): Card {
  if (ref.startsWith("_synthesis/")) {
    const norm = normalize(ref).split(sep).join("/");
    if (!norm.startsWith("_synthesis/") || norm.includes("..")) throw new Error(`card: ${ref} is outside the store`);
    ref = norm;
  }
  const hits = cards(root).filter(l => l.ref === ref);
  if (hits.length === 0) throw new Error(`card: no item named ${ref} in any store`);
  if (hits.length > 1) throw new Error(`card: ${ref} is ambiguous — it names an item in ${hits.map(h => h.store).join(" and ")}`);
  const l = hits[0]!;
  let c: Card | undefined;
  switch (l.store) {
    case "_sources": c = sourceCard(root, ledger.status(root).entries.find(e => e.id === ref)!); break;
    case "_synthesis": c = synthesisCard(root, ref); break;
    case "capture": c = l.summary === NO_CARD ? undefined : { title: l.title, kind: l.kind, summary: l.summary, keyItems: [] }; break;
    case "_skills": { const s = brief.skill(root, ref); c = { title: s.name, kind: "skill", summary: s.mission, keyItems: s.rules }; break; }
  }
  if (!c) throw new Error(`card: ${ref} has no card — ${l.store === "capture" ? "no scope line" : l.store === "_sources" ? "run intake-scan and land it with scan" : "no sidecar, no head card"}`);
  return c;
}
