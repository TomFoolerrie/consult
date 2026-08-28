/**
 * ledger — the source of sources.
 *
 * Owns/writes: _sources/ entirely; the one SRC-id minter. Doctrine kept
 * verbatim: file position is display; the ledger is truth — no question is
 * ever answered by listing a folder. The intake door is ONE door (D4): a
 * fresh source, a client's response, and the consultant's own synthesis
 * all arrive through route() — the only way in.
 *
 * CONSUMPTION IS COMPUTED, NEVER DECLARED (A18): a source is consumed at
 * slug S exactly when a statement in fragment S cites its SRC id —
 * corroboration included (adding the SRC to a citation list IS
 * corroboration). There is no credit() verb: status() derives
 * consumed/outstanding from capture citations at read time, and a fully
 * cited source auto-retires to processed/ at checkpoint. `intent`
 * (né touches) is the debt declared at route time, balanced by
 * derivation, retired by the record's own shape.
 *
 * SYNTHESIS SOURCES (A12): provenance "synthesis" requires NON-EMPTY,
 * resolvable grounds — SRC ids or capture addresses (slug#LOCAL-ID or a
 * bare slug). Citable like any source; a statement citing a synthesis
 * inherits the WEAKEST standing among the synthesis's grounds, resolved
 * through the chain — grounded in evidenced material it reads evidenced,
 * grounded in a claimed statement it reads claimed; it never upgrades.
 *
 * FILE LIFECYCLE, pinned: a routed file STAYS in _sources/new/ until
 * retirement moves it to processed/ (at checkpoint, once fully cited);
 * LedgerEntry.file is root-relative and is rewritten on retire, so
 * status() survives the move. A staged duplicate (same hash) returns
 * the existing id and the duplicate file is REMOVED — no copies. The
 * ledger itself is _sources/sources.yaml.
 */
import { parse, stringify } from "yaml";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync, readdirSync, rmSync } from "node:fs";
import { join, basename } from "node:path";
import * as kernel from "./kernel.ts";
import type { SrcId, AskId } from "./types.ts";

const LEDGER = (root: string) => join(root, "_sources", "sources.yaml");

interface Book { entries: MutableEntry[]; parked: { file: string; reason: string }[]; }
interface MutableEntry {
  id: SrcId; file: string; hash: string; intent: string[]; answers: AskId[];
  provenance?: "client" | "public" | "synthesis"; grounds?: string[];
  scan?: { summary: string; keyItems: string[] };
}
export function readBook(root: string): Book {
  if (!existsSync(LEDGER(root))) return { entries: [], parked: [] };
  const b = parse(readFileSync(LEDGER(root), "utf8")) as Book | null;
  return { entries: b?.entries ?? [], parked: b?.parked ?? [] };
}
export function writeBook(root: string, b: Book): void { writeFileSync(LEDGER(root), stringify(b)); }
export function stampAnswer(root: string, src: SrcId, ask: AskId): void {
  const b = readBook(root);
  const e = b.entries.find(e => e.id === src);
  if (!e) throw new Error(`stampAnswer: ${src} not in the ledger`);
  if (!e.answers.includes(ask)) e.answers.push(ask);
  writeBook(root, b);
}

export interface LedgerEntry {
  id: SrcId; file: string; hash: string;
  /** the debt declared at route time: fragment slugs this source is expected to inform (A18: intent, balanced by computed consumption) */
  intent: readonly string[];
  answers: readonly AskId[];
  provenance?: "client" | "public" | "synthesis";
  /** synthesis sources ONLY (A12): grounds this work product was built from — required, must resolve; never upgrades standing */
  grounds?: readonly string[];
  /** intake scan (A17): cheap-model metadata attached at route time by the intake-scan skill. Advisory only: never grounds, never cited. */
  scan?: { summary: string; keyItems: readonly string[] };
}

/** the one intake door: tag + one idempotent-by-hash entry; mints SRC-nnn; no copies, no sidecars.
 * opts (A14): provenance; grounds REQUIRED when synthesis — refused by name otherwise */
export function route(root: string, file: string, intent: string[], opts?: { provenance?: "client" | "public" | "synthesis"; grounds?: string[] }): SrcId {
  if (!existsSync(file)) throw new Error(`route: no such staged file ${file}`);
  if (opts?.provenance === "synthesis" && !(opts.grounds && opts.grounds.length))
    throw new Error(`route: synthesis provenance requires non-empty grounds (${basename(file)})`);
  const hash = createHash("sha256").update(readFileSync(file)).digest("hex");
  const b = readBook(root);
  const dup = b.entries.find(e => e.hash === hash);
  if (dup) { rmSync(file); return dup.id; }  // same content = same source; no copies
  const id = `SRC-${String(b.entries.length + 1).padStart(3, "0")}` as SrcId;
  const entry: MutableEntry = { id, file: join("_sources/new", basename(file)), hash, intent: [...intent], answers: [] };
  if (opts?.provenance) entry.provenance = opts.provenance;
  if (opts?.grounds) entry.grounds = [...opts.grounds];
  b.entries.push(entry);
  writeBook(root, b);
  return id;
}
/** decline a staged file with a durable reason */
export function park(root: string, file: string, reason: string): void {
  const b = readBook(root);
  const dest = join(root, "_sources/parked", basename(file));
  writeFileSync(dest, readFileSync(file)); rmSync(file);
  b.parked.push({ file: join("_sources/parked", basename(file)), reason });
  writeBook(root, b);
}
/** the whole ledger picture — consumed/outstanding COMPUTED from capture citations (A18), never stored */
export function status(root: string): { unrouted: string[]; entries: LedgerEntry[]; consumed: Map<SrcId, string[]>; outstanding: Map<SrcId, string[]> } {
  const b = readBook(root);
  const routedNames = new Set(b.entries.map(e => basename(e.file)));
  const newDir = join(root, "_sources/new");
  const unrouted = (existsSync(newDir) ? readdirSync(newDir) : []).filter(f => !routedNames.has(f));
  const consumed = new Map<SrcId, string[]>(), outstanding = new Map<SrcId, string[]>();
  const ents = kernel.entities(root);
  for (const e of b.entries) {
    const got = ents.filter(en => en.statements.some(st => st.cites.includes(e.id))).map(en => en.slug);
    consumed.set(e.id, got);
    outstanding.set(e.id, e.intent.filter(sl => !got.includes(sl)));
  }
  return { unrouted, entries: b.entries as unknown as LedgerEntry[], consumed, outstanding };
}
