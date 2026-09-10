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
 *   authored text           → the file's own head (yaml top keys; md frontmatter)
 *   anything else we made   → a sidecar beside it: <stem>.card.yaml
 *   capture fragments       → the `scope:` head key (what it is ABOUT — intent,
 *                             not summary, so it cannot go stale)
 *   skills                  → the skill file already is one
 * INDEX FILES ARE NEVER STORED (a capture manifest is outlawed, A14):
 * this module walks the folder on every call. The ledgers are truth,
 * not cache, and are read as such.
 *
 * An item without a card is LISTED with "(no card)" — the walk is
 * honest; the missing card is visible debt, never a hidden item.
 */
import { parse } from "yaml";
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, basename, extname, relative } from "node:path";
import * as ledger from "./ledger.ts";
import * as kernel from "./kernel.ts";
import * as brief from "./brief.ts";
import type { Card } from "./types.ts";

export type Store = "_sources" | "_synthesis" | "capture" | "_skills";
export const STORES: readonly Store[] = ["_sources", "_synthesis", "capture", "_skills"];
export interface IndexLine { store: Store; ref: string; title: string; kind: string; summary: string; content?: string; }

const NO_CARD = "(no card)";
const isSidecar = (f: string) => f.endsWith(".card.yaml");
const isLineage = (f: string) => /-lineage\.md$/.test(f);
const sidecarFor = (file: string) => file.replace(/\.[^.]+$/, "") + ".card.yaml";

function readYaml(p: string): Record<string, unknown> | undefined {
  try { const r = parse(readFileSync(p, "utf8")); return r && typeof r === "object" ? r as Record<string, unknown> : undefined; }
  catch { return undefined; }
}
/** a card from a file's head: md frontmatter, or the yaml file's own top keys */
function headCard(p: string): Record<string, unknown> | undefined {
  const ext = extname(p);
  if (ext === ".md") {
    const t = readFileSync(p, "utf8");
    const m = /^---\n([\s\S]*?)\n---/.exec(t);
    if (!m) return undefined;
    try { const r = parse(m[1]!); return r && typeof r === "object" ? r : undefined; } catch { return undefined; }
  }
  if (ext === ".yaml" || ext === ".yml") return readYaml(p);
  return undefined;
}
const asCard = (raw: Record<string, unknown> | undefined): Card | undefined =>
  raw && typeof raw.summary === "string" ? raw as unknown as Card : undefined;

/** the card for one synthesis artifact: sidecar first, then the file's own head */
export function synthesisCard(root: string, file: string): Card | undefined {
  const abs = join(root, file);
  const side = sidecarFor(abs);
  if (existsSync(side)) return asCard(readYaml(side));
  return asCard(headCard(abs));
}
/** every synthesis ARTIFACT (sidecars and lineage notes are not artifacts), root-relative */
export function synthesisArtifacts(root: string): string[] {
  const dir = join(root, "_synthesis");
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  const walk = (d: string) => { for (const f of readdirSync(d)) {
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (!isSidecar(f) && !isLineage(f)) out.push(relative(root, p));
  } };
  walk(dir);
  return out.sort();
}

function line(store: Store, ref: string, c: Card | undefined, fallbackTitle: string, fallbackKind: string, content?: string): IndexLine {
  const l: IndexLine = { store, ref,
    title: (c?.title as string | undefined) ?? fallbackTitle,
    kind: (c?.kind as string | undefined) ?? fallbackKind,
    summary: c?.summary ?? NO_CARD };
  if (content) l.content = content;
  return l;
}
/** the index: one line per item, every store (or one), read from cards — recomputed on every call */
export function cards(root: string, store?: Store): IndexLine[] {
  const out: IndexLine[] = [];
  const want = (s: Store) => !store || store === s;
  if (want("_sources")) for (const e of ledger.status(root).entries) {
    const c = e.scan && existsSync(join(root, e.scan)) ? asCard(readYaml(join(root, e.scan))) : undefined;
    out.push(line("_sources", e.id, c, basename(e.file), e.provenance ?? "client", e.file));
  }
  if (want("_synthesis")) for (const f of synthesisArtifacts(root))
    out.push(line("_synthesis", f, synthesisCard(root, f), basename(f), "artifact", f));
  if (want("capture")) {
    for (const n of kernel.taxonomy(root)) out.push(line("capture", n.slug, n.scope ? { summary: n.scope, keyItems: [] } : undefined, n.slug, "taxonomy-node", join("capture/_taxonomy", `${n.slug}.yaml`)));
    for (const e of kernel.entities(root)) out.push(line("capture", e.slug, e.scope ? { summary: e.scope, keyItems: [] } : undefined, e.slug, "process-step", join("capture", `${e.slug}.yaml`)));
  }
  if (want("_skills")) for (const s of brief.skills(root))
    out.push(line("_skills", s.name, { title: s.name, kind: "skill", summary: s.mission, keyItems: [] }, s.name, "skill"));
  return out;
}
/** the printable index — what a brief or a fresh sitting reads before opening anything */
export function render(root: string, store?: Store): string {
  return cards(root, store).map(l => `${l.store}  ${l.ref}  ·  ${l.title}  ·  ${l.kind}  —  ${l.summary}`).join("\n");
}
/** open one full card by ref: SRC id · synthesis path · capture slug · skill name — unknown is a named refusal */
export function card(root: string, ref: string): Card {
  if (/^SRC-\d+$/.test(ref)) {
    const e = ledger.status(root).entries.find(e => e.id === ref);
    if (!e) throw new Error(`card: no source ${ref}`);
    const c = e.scan && existsSync(join(root, e.scan)) ? asCard(readYaml(join(root, e.scan))) : undefined;
    if (!c) throw new Error(`card: ${ref} has no scan — run intake-scan and land it with scan`);
    return c;
  }
  if (ref.startsWith("_synthesis/")) {
    const c = synthesisCard(root, ref);
    if (!c) throw new Error(`card: ${ref} has no card (no sidecar, no frontmatter)`);
    return c;
  }
  const ent = [...kernel.taxonomy(root), ...kernel.entities(root)].find(e => e.slug === ref);
  if (ent) {
    if (!ent.scope) throw new Error(`card: ${ref} has no scope line`);
    return { title: ref, kind: "capture", summary: ent.scope, keyItems: [] };
  }
  try { const s = brief.skill(root, ref); return { title: s.name, kind: "skill", summary: s.mission, keyItems: s.rules }; } catch { /* fallthrough */ }
  throw new Error(`card: no item named ${ref} in any store`);
}
