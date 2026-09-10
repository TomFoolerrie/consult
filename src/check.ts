/**
 * check — the QC gate over capture.
 *
 * Owns: NOTHING (ROT-5 — signal files were the dead guard table's stage
 * markers; the session record logs that a check ran). Runs over the whole
 * engagement (no area parameter — ROT-3). Seven checks, all MECHANICAL —
 * the hedges check is gone (A9): word-list policing of prose style is a
 * skill rule that binds whoever drafts, not an engine invariant.
 *
 *   grammar        per-fragment parse through the declaration, plus the
 *                  names enumeration would silently skip (a .yml file, a
 *                  nested directory under capture/)
 *   citations      every cited SRC resolves. An UNCITED capture
 *                  statement is NOT an error — it is the claimed
 *                  standing, legitimate by design; the cites-required
 *                  rule binds synthesis/deliverable DRAFTS only
 *   consumption    a retired (processed/) source is actually fully cited
 *                  (ERROR); an intent slug with no fragment YET is a
 *                  WARNING — declaring intent at route time and writing
 *                  the fragment after is the normal mid-fold-in state
 *   mentions       a slug mentioned in prose exists (warning)
 *   ask-coverage   every question id in the ask register exactly once
 *   registers      the shape of both registers and the ledger: findings
 *                  (status, id/claim/grounds, grounds resolve) · asks
 *                  (status, id/text, questions and answeredBy lists,
 *                  questions resolve) · sources (id/file/intent present,
 *                  no duplicate ids, the file on disk, its content still
 *                  matching its hash, scan pointers resolving, synthesis
 *                  grounds resolving with no cycle and no chain deeper
 *                  than 8 hops)
 *   cards          every synthesis ARTIFACT carries a card (sidecar or head) —
 *                  WARNING only; accuracy is the consultant's (A22)
 *
 * Errors exit nonzero; warnings print; every message names the offender —
 * file, id, field — and, where a statement is at fault, its FILE LINE.
 */
import { parse } from "yaml";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import * as kernel from "./kernel.ts";
import * as ledger from "./ledger.ts";
import * as index from "./index.ts";

export interface Defect { check: string; severity: "error" | "warning"; file: string; line?: number; message: string; }
export type Check = (root: string) => Defect[];
function grammar(root: string): Defect[] {
  const out: Defect[] = [];
  for (const [sub, type] of [["capture", "process-step"], ["capture/_taxonomy", "taxonomy-node"]] as const) {
    const dir = join(root, sub);
    if (!existsSync(dir)) continue;
    const tdecl = kernel.loadType(root, type);
    for (const f of readdirSync(dir).filter(f => f.endsWith(".yaml"))) {
      try { kernel.parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, "")); }
      catch (e) { out.push({ check: "grammar", severity: "error", file: join(sub, f), message: (e as Error).message }); }
    }
  }
  for (const a of kernel.captureAnomalies(root))
    out.push({ check: "grammar", severity: "error", file: a.path, message: a.message });
  return out;
}
/** the ledger picture that survives a hand-broken entry — a malformed ledger is the registers check's
 *  defect, never a crash of the other checks (same discipline as safeEntities, review B5) */
function safeStatus(root: string): ReturnType<typeof ledger.status> {
  try { return ledger.status(root); }
  catch { return { unrouted: [], entries: ledger.readBook(root).entries as any, consumed: new Map(), outstanding: new Map() }; }
}
/** the parseable subset — a malformed file is the grammar check's defect, never a crash of the other checks (review B5) */
function safeEntities(root: string) { return kernel.entitiesLenient(root); }
/** the FILE line of each `- text:` entry, in document order — the Defect's
 *  `line` is a line in the file, never a statement ordinal (review A/F3) */
function statementLines(root: string, slug: string): number[] {
  const p = join(root, "capture", `${slug}.yaml`);
  if (!existsSync(p)) return [];
  const out: number[] = [];
  readFileSync(p, "utf8").split("\n").forEach((l, i) => { if (/^\s*-\s+text\s*:/.test(l)) out.push(i + 1); });
  return out;
}
/** a defect on statement n of a fragment: the file line when we can find it, `statement n` in the message when we cannot */
function atStatement(root: string, slug: string, i: number, check: string, severity: "error" | "warning", message: string): Defect {
  const line = statementLines(root, slug)[i];
  const d: Defect = { check, severity, file: join("capture", `${slug}.yaml`), message: line === undefined ? `statement ${i + 1}: ${message}` : message };
  if (line !== undefined) d.line = line;
  return d;
}
function citations(root: string): Defect[] {
  const out: Defect[] = [];
  const ids = new Set(safeStatus(root).entries.map(e => e.id as string));
  for (const e of safeEntities(root)) {
    e.statements.forEach((st, i) => {
      for (const c of st.cites) if (!ids.has(c))
        out.push(atStatement(root, e.slug, i, "citations", "error", `${c} resolves to no source on file`));
    });
  }
  return out;
}
function consumption(root: string): Defect[] {
  const out: Defect[] = [];
  const st = safeStatus(root);
  const slugs = new Set(safeEntities(root).map(e => e.slug));
  for (const e of st.entries) {
    // RULING (review A/F2): intent declared at route time before the fragment
    // is written is the NORMAL mid-fold-in state — a warning, never an error.
    for (const sl of Array.isArray(e.intent) ? e.intent : []) if (!slugs.has(sl))
      out.push({ check: "consumption", severity: "warning", file: "_sources/sources.yaml",
        message: `${e.id} declares intent for ${sl}, which is no capture fragment yet` });
    if (typeof e.file === "string" && e.file.startsWith("_sources/processed/") && (st.outstanding.get(e.id)?.length ?? 0) > 0)
      out.push({ check: "consumption", severity: "error", file: "_sources/sources.yaml",
        message: `${e.id} is retired but not fully cited (${st.outstanding.get(e.id)!.join(", ")} outstanding)` });
  }
  return out;
}
function mentions(root: string): Defect[] {
  const out: Defect[] = [];
  const slugs = new Set(safeEntities(root).map(e => e.slug));
  for (const e of safeEntities(root)) e.statements.forEach((st, i) => {
    for (const m of st.text.matchAll(/\[\[([a-z0-9-]+)\]\]/g)) {
      if (!slugs.has(m[1]!)) out.push(atStatement(root, e.slug, i, "mentions", "warning", `mentions [[${m[1]}]], which is no fragment`));
    }
  });
  return out;
}
function askCoverage(root: string): Defect[] {
  const out: Defect[] = [];
  const p = join(root, "_registers", "asks.yaml");
  if (!existsSync(p)) return out;
  const raw = parse(readFileSync(p, "utf8"));
  const asksList: { id?: string; status?: string; questions?: string[]; answeredBy?: string[] }[] = Array.isArray(raw) ? raw : raw?.asks ?? [];
  const seen = new Map<string, string>();
  // a phantom address (a question record that does not exist) is the REGISTERS check's defect (asksShape) — not repeated here
  for (const a of asksList) for (const q of Array.isArray(a.questions) ? a.questions : []) {
    if (seen.has(q)) out.push({ check: "ask-coverage", severity: "error", file: "_registers/asks.yaml",
      message: `question ${q.split("#")[1] ?? q} (${q}) appears in both ${seen.get(q)} and ${a.id} — exactly once, asked or closed` });
    else seen.set(q, a.id ?? "?");
  }
  return out;
}
/**
 * registers — the SHAPE of the machine-parsed bookkeeping, read directly off
 * disk (the A14 world hand-edits these files, so the check reads the YAML,
 * not the modules' tolerant views). Findings, asks, the ledger. Every defect
 * is an ERROR naming the file and the offending id or field.
 */
function readList(root: string, rel: string, key: string): any[] | null {
  const p = join(root, rel);
  if (!existsSync(p)) return null;
  let raw: unknown;
  try { raw = parse(readFileSync(p, "utf8")); } catch { return null; }
  if (Array.isArray(raw)) return raw;
  const inner = (raw as any)?.[key];
  return Array.isArray(inner) ? inner : [];
}
const FINDING_STATUS = ["proposed", "accepted", "rejected"];
const ASK_STATUS = ["proposed", "accepted", "sent", "closed"];

function findingsShape(root: string, srcIds: Set<string>, addrs: Set<string>, slugs: Set<string>): Defect[] {
  const file = "_registers/findings.yaml";
  const list = readList(root, file, "findings");
  if (!list) return [];
  const out: Defect[] = [];
  const err = (message: string) => out.push({ check: "registers", severity: "error", file, message });
  list.forEach((f, i) => {
    const id = typeof f?.id === "string" && f.id ? f.id : null;
    const who = id ?? `entry ${i + 1}`;
    if (!id) err(`finding entry ${i + 1} has no id`);
    if (typeof f?.claim !== "string" || !f.claim) err(`${who} has no claim`);
    if (!Array.isArray(f?.grounds)) err(`${who} has no grounds list`);
    if (typeof f?.status !== "string" || !FINDING_STATUS.includes(f.status))
      err(`${who} status "${String(f?.status)}" is not one of ${FINDING_STATUS.join("|")}`);
    for (const g of Array.isArray(f?.grounds) ? f.grounds : []) {
      const ref = typeof g === "string" ? g : String(g?.slug);
      if (/^SRC-\d+$/.test(ref)) { if (!srcIds.has(ref)) err(`${who} grounds ${ref}, which resolves to no source on file`); continue; }
      if (ref.includes("#")) { if (!addrs.has(ref)) err(`${who} grounds ${ref}, which resolves to no question record in capture`); continue; }
      if (!slugs.has(ref)) err(`${who} grounds ${ref}, which is no capture fragment`);
    }
  });
  return out;
}
function asksShape(root: string, addrs: Set<string>): Defect[] {
  const file = "_registers/asks.yaml";
  const list = readList(root, file, "asks");
  if (!list) return [];
  const out: Defect[] = [];
  const err = (message: string) => out.push({ check: "registers", severity: "error", file, message });
  list.forEach((a, i) => {
    const id = typeof a?.id === "string" && a.id ? a.id : null;
    const who = id ?? `entry ${i + 1}`;
    if (!id) err(`ask entry ${i + 1} has no id`);
    if (typeof a?.text !== "string" || !a.text) err(`${who} has no text`);
    if (typeof a?.status !== "string" || !ASK_STATUS.includes(a.status))
      err(`${who} status "${String(a?.status)}" is not one of ${ASK_STATUS.join("|")}`);
    if (!Array.isArray(a?.questions)) err(`${who} questions must be a list`);
    if (!Array.isArray(a?.answeredBy)) err(`${who} has no answeredBy list`);
    const couldSettle = (Array.isArray(a?.answeredBy) && a.answeredBy.length > 0) || a?.status === "closed";
    for (const q of Array.isArray(a?.questions) ? a.questions : [])
      if (!addrs.has(String(q)) && !couldSettle) err(`${who} names ${String(q)}, which resolves to no question record in capture`);
  });
  return out;
}
/** the ledger's own shape: ids, files, hashes, scans, synthesis grounds and their chains */
function sourcesShape(root: string, slugs: Set<string>, addrs: Set<string>): Defect[] {
  const file = "_sources/sources.yaml";
  if (!existsSync(join(root, file))) return [];
  const entries = ledger.readBook(root).entries;
  const out: Defect[] = [];
  const err = (message: string) => out.push({ check: "registers", severity: "error", file, message });
  const seen = new Set<string>();
  const ids = new Set(entries.map(e => e.id as string));
  entries.forEach((e, i) => {
    const id = typeof e?.id === "string" && e.id ? e.id : null;
    const who = id ?? `entry ${i + 1}`;
    if (!id) err(`source entry ${i + 1} has no id`);
    else if (seen.has(id)) err(`duplicate source id ${id}`);
    else seen.add(id);
    if (!Array.isArray(e?.intent)) err(`${who} declares no intent list — name the capture slugs this source is expected to inform`);
    if (typeof e?.file !== "string" || !e.file) err(`${who} has no file`);
    else if (!existsSync(join(root, e.file))) err(`${who} file ${e.file} does not exist on disk`);
    else if (typeof e.hash === "string" && createHash("sha256").update(readFileSync(join(root, e.file))).digest("hex") !== e.hash)
      err(`${who} content no longer matches its hash — ${e.file} was modified outside the one intake door`);
    if (e?.scan && !existsSync(join(root, e.scan)))
      err(`${who} scan pointer ${e.scan} does not resolve to a file`);
    if (e?.provenance === "synthesis") {
      if (!e.grounds?.length) err(`${who} is synthesis with no declared grounds`);
      for (const g of e.grounds ?? []) {
        const ok = /^SRC-\d+$/.test(g) ? ids.has(g) : (g.includes("#") ? addrs.has(g) : slugs.has(g));
        if (!ok) err(`${who} ground ${g} does not resolve`);
      }
    }
  });
  // the synthesis chain: a cycle, or a chain deeper than the 8-hop cap
  // answers.citeStanding gives up at — named here so the cause is visible (A12)
  const groundsOf = new Map<string, string[]>();
  for (const e of entries)
    if (e.provenance === "synthesis") groundsOf.set(e.id as string, (e.grounds ?? []).filter(g => /^SRC-\d+$/.test(g) && ids.has(g)));
  const depth = new Map<string, number>();
  const walk = (id: string, path: string[]): number => {
    const at = path.indexOf(id);
    if (at >= 0) { err(`${id} grounds a cycle: ${[...path.slice(at), id].join(" → ")}`); return Number.POSITIVE_INFINITY; }
    if (depth.has(id)) return depth.get(id)!;
    let d = 0;
    for (const g of groundsOf.get(id) ?? []) d = Math.max(d, 1 + walk(g, [...path, id]));
    if (Number.isFinite(d)) depth.set(id, d);
    return d;
  };
  const reported = new Set<string>();
  for (const id of groundsOf.keys()) {
    const d = walk(id, []);
    if (Number.isFinite(d) && d > 8 && !reported.has(id)) {
      reported.add(id);
      err(`${id} grounds a synthesis chain ${d} hops deep — deeper than 8 hops, past the depth cap standing resolution gives up at`);
    }
  }
  return out;
}
function registers(root: string): Defect[] {
  const ents = safeEntities(root);
  const slugs = new Set([...ents, ...kernel.taxonomyLenient(root)].map(e => e.slug));
  const addrs = new Set([...ents, ...kernel.taxonomyLenient(root)].flatMap(e => kernel.openQuestions(e).map(c => c.addr as string)));
  const srcIds = new Set(ledger.readBook(root).entries.map(e => e.id as string));
  return [...findingsShape(root, srcIds, addrs, slugs), ...asksShape(root, addrs), ...sourcesShape(root, slugs, addrs)];
}
/** A22: every synthesis ARTIFACT carries a card (sidecar or head) — presence only; accuracy is the consultant's */
function cardsCheck(root: string): Defect[] {
  return index.synthesisArtifacts(root).filter(f => !index.synthesisCard(root, f))
    .map(f => ({ check: "cards", severity: "warning" as const, file: f, message: `synthesis artifact ${f} has no card — an agent must open it to learn what it is` }));
}
export const CHECKS: readonly Check[] = [grammar, citations, consumption, mentions, askCoverage, registers, cardsCheck];

/** the whole gate; empty error list = clean */
export function run(root: string): Defect[] { return CHECKS.flatMap(c => c(root)); }
