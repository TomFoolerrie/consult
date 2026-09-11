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
 * THE SCAN (A17 → A20): a source may carry ONE durable scout report,
 * _sources/scans/SRC-nnn.yaml, written only through scan(); the ledger
 * entry keeps a root-relative POINTER, never the content. The report
 * describes the DOCUMENT (summary + keyItems required — the default
 * template); a local intake-scan variant may add fields, which ride
 * along. A scan is NOT a source: route() refuses anything under
 * _sources/scans/, so a précis can never become grounding material.
 * Advisory only — never grounds, never cited; a re-scan overwrites.
 *
 * FILE LIFECYCLE, pinned: a routed file STAYS in _sources/new/ until
 * retirement moves it to processed/ (at checkpoint, once fully cited);
 * LedgerEntry.file is root-relative and is rewritten on retire, so
 * status() survives the move. A staged duplicate (same hash) returns
 * the existing id and the duplicate file is REMOVED — no copies. The
 * ledger itself is _sources/sources.yaml.
 */
import { parse, stringify } from "yaml";
import { parse as parseCsv } from "csv-parse/sync";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync, readdirSync, rmSync, mkdirSync, renameSync, realpathSync, statSync, openSync, closeSync } from "node:fs";
import { join, basename, dirname, relative, isAbsolute, resolve } from "node:path";
import * as kernel from "./kernel.ts";
import type { SrcId, AskId } from "./types.ts";

const LEDGER = (root: string) => join(root, "_sources", "sources.yaml");
/** THE CITATION GRAMMAR (A27): a source reference is `SRC-nnn`, `SRC-nnn:Lx-Ly` (text lines), or `SRC-nnn:Rn` (CSV data record).
 *  srcOf() gives the bare id standing is computed from; resolveRef() verifies the locator against the bytes on file. */
export const SRC_REF = /^(SRC-\d+)(?::L(\d+)-L(\d+)|:R(\d+))?$/;
export function isSrcRef(s: string): boolean { return SRC_REF.test(s); }
export function srcOf(ref: string): SrcId {
  const m = SRC_REF.exec(ref);
  if (!m) throw new Error(`citation ${ref} is not SRC-nnn, SRC-nnn:Lx-Ly, or SRC-nnn:Rn`);
  return m[1] as SrcId;
}
/** verify a reference resolves on file — the id exists; a line range is within the text; a record is within the table. Throws by name. */
export function resolveRef(root: string, ref: string): SrcId {
  const m = SRC_REF.exec(ref);
  if (!m) throw new Error(`citation ${ref} is not SRC-nnn, SRC-nnn:Lx-Ly, or SRC-nnn:Rn`);
  const id = m[1] as SrcId;
  if (m[2] !== undefined) sourceExcerpt(root, id, { start: Number(m[2]), end: Number(m[3]) });
  else if (m[4] !== undefined) sourceRecord(root, id, Number(m[4]));
  else if (!readBook(root).entries.some(e => e.id === id)) throw new Error(`cite: ${id} resolves to no source on file`);
  return id;
}
/** ids are minted as max+1, never length+1 — a hand-deleted entry must not free a live id (review) */
export function nextId<P extends string>(ids: readonly string[], prefix: P): `${P}-${number}` {
  const max = ids.reduce((m, id) => Math.max(m, Number(id.split("-")[1] ?? 0)), 0);
  return `${prefix}-${String(max + 1).padStart(3, "0")}` as `${P}-${number}`;
}
/** the ONE sidecar-path rule (A22): <dir>/<stem>.card.yaml, stem taken from the basename — a dot in the root path never matters */
export function sidecarPath(file: string): string {
  const b = basename(file);
  const stem = b.includes(".") ? b.slice(0, b.lastIndexOf(".")) : b;
  return join(dirname(file), `${stem}.card.yaml`);
}

interface Book { entries: MutableEntry[]; parked: { file: string; reason: string }[]; }
interface MutableEntry {
  id: SrcId; file: string; hash: string; intent: string[]; answers: AskId[];
  provenance?: "client" | "public" | "synthesis"; grounds?: string[];
  scan?: string;
}
export function readBook(root: string): Book {
  if (!existsSync(LEDGER(root))) return { entries: [], parked: [] };
  const b = parse(readFileSync(LEDGER(root), "utf8")) as Book | null;
  return { entries: b?.entries ?? [], parked: b?.parked ?? [] };
}
export function writeBook(root: string, b: Book): void { mkdirSync(join(root, "_sources"), { recursive: true }); writeFileSync(LEDGER(root), stringify(b)); }
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
  /** the durable scout report (A20): root-relative path of _sources/scans/SRC-nnn.yaml. Advisory only: never grounds, never cited. */
  scan?: string;
}

/** Read-only evidence bridge. Integrity is byte identity, NOT truth, semantic
 * support, standing, or recursive verification of synthesis grounds. */
export interface VerifiedSource {
  id: SrcId;
  file: string;
  hash: string;
  integrity: "sha256-matched";
  provenance?: "client" | "public" | "synthesis";
  grounds?: readonly string[];
}
export interface LineRange { start: number; end: number; }
export interface SourceExcerpt extends VerifiedSource {
  locator: { kind: "lines"; start: number; end: number };
  totalLines: number;
  text: string;
}
function allowedSourcePath(path: string): boolean {
  return !isAbsolute(path) && ["_sources/new/", "_sources/processed/", "_synthesis/"].some(p => path.startsWith(p))
    && !path.endsWith(".card.yaml");
}
/** Resolve the ledger on every use (retirement changes location, not identity).
 * Hash and excerpt use the SAME read. Real-path checks prevent accidental
 * traversal/symlink escapes; this is not a sandbox against concurrent hostile
 * filesystem mutation. No cached integrity or line counts are trusted. */
function verifiedBytes(root: string, id: string): { source: VerifiedSource; bytes: Buffer } {
  if (!/^SRC-\d+$/.test(id)) throw new Error(`source: invalid source id ${id}`);
  const matches = readBook(root).entries.filter(e => e?.id === id);
  if (!matches.length) throw new Error(`source: unknown source ${id}`);
  if (matches.length !== 1) throw new Error(`source: duplicate source ${id}`);
  const e = matches[0]!;
  if (typeof e.hash !== "string" || !/^[a-f0-9]{64}$/.test(e.hash)) throw new Error(`source ${id}: missing or malformed registered hash`);
  const base = resolve(root);
  if (typeof e.file !== "string" || !allowedSourcePath(e.file) || !allowedSourcePath(relative(base, resolve(base, e.file)).split("\\").join("/")))
    throw new Error(`source ${id}: path outside allowed source stores: ${e.file}`);
  let actual: string;
  try { actual = realpathSync(join(base, e.file)); }
  catch { throw new Error(`source ${id}: unreadable source ${e.file}`); }
  const realRoot = realpathSync(base);
  if (!allowedSourcePath(relative(realRoot, actual).split("\\").join("/")))
    throw new Error(`source ${id}: path outside allowed source stores: ${e.file}`);
  let bytes: Buffer;
  try {
    if (!statSync(actual).isFile()) throw new Error("not a regular file");
    bytes = readFileSync(actual);
  } catch { throw new Error(`source ${id}: unreadable source ${e.file}`); }
  if (createHash("sha256").update(bytes).digest("hex") !== e.hash)
    throw new Error(`source ${id}: content changed since registration: ${e.file}`);
  return { bytes, source: { id: e.id, file: e.file, hash: e.hash, integrity: "sha256-matched",
    ...(e.provenance ? { provenance: e.provenance } : {}), ...(e.grounds ? { grounds: [...e.grounds] } : {}) } };
}
/** Verify a registered artifact of any format, without mutation. */
export function verifySource(root: string, id: string): VerifiedSource { return verifiedBytes(root, id).source; }
/** UTF-8 text only. Positive inclusive lines; CRLF normalized for display;
 * terminal newline creates no extra line. Bare CR and binary controls refused.
 * No implicit whole-file dump: callers must request an explicit range. */
export function sourceExcerpt(root: string, id: string, range: LineRange): SourceExcerpt {
  if (!range || !Number.isSafeInteger(range.start) || !Number.isSafeInteger(range.end) || range.start < 1 || range.end < range.start)
    throw new Error(`source ${id}: invalid line range`);
  const { source, bytes } = verifiedBytes(root, id);
  let text: string;
  try { text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes); }
  catch { throw new Error(`source ${id}: unsupported text encoding (requires UTF-8)`); }
  text = text.replace(/\r\n/g, "\n");
  if (/[\x00-\x08\x0b-\x1f\x7f]/.test(text)) throw new Error(`source ${id}: unsupported text (binary controls or bare CR)`);
  const lines = text === "" ? [] : text.split("\n");
  if (text.endsWith("\n")) lines.pop();
  if (range.end > lines.length) throw new Error(`source ${id}: line range ${range.start}:${range.end} exceeds ${lines.length} lines`);
  return { ...source, locator: { kind: "lines", ...range }, totalLines: lines.length,
    text: lines.slice(range.start - 1, range.end).join("\n") };
}

/** Verified comma-delimited UTF-8 table. Header names must be nonempty and
 * unique after trimming. Blank physical lines are skipped; empty cells/records
 * are retained. Record IDs count data records after the header, not file lines. */
export interface SourceTable extends VerifiedSource { header: string[]; records: string[][]; }
export interface SourceRecord extends VerifiedSource { header: string[]; values: string[]; locator: { kind: "csv-record"; record: number }; totalRecords: number; }
export function sourceTable(root: string, id: string): SourceTable {
  const { source, bytes } = verifiedBytes(root, id);
  if (!source.file.toLowerCase().endsWith(".csv")) throw new Error(`source ${id}: CSV requires a .csv artifact (comma-delimited UTF-8)`);
  let rows: string[][];
  try {
    const text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
    if (/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(text)) throw new Error("binary controls");
    rows = parseCsv(text, { bom: true, skip_empty_lines: true, delimiter: ",", record_delimiter: ["\r\n", "\n"], relax_column_count: false }) as string[][];
  } catch { throw new Error(`source ${id}: invalid CSV (UTF-8, quoting and consistent column counts required)`); }
  const header = rows.shift()?.map(c => c.trim());
  if (!header?.length || header.some(c => !c) || new Set(header).size !== header.length)
    throw new Error(`source ${id}: invalid CSV header (nonempty unique names required)`);
  return { ...source, header, records: rows };
}
export function sourceRecord(root: string, id: string, record: number): SourceRecord {
  if (!Number.isSafeInteger(record) || record < 1) throw new Error(`source ${id}: invalid CSV record number`);
  const { records, ...source } = sourceTable(root, id);
  const values = records[record - 1];
  if (!values) throw new Error(`source ${id}: CSV record ${record} exceeds ${records.length} records`);
  return { ...source, locator: { kind: "csv-record", record }, values, totalRecords: records.length };
}

/** A22 at the write port: a work product carries a card — sidecar, md frontmatter with summary, or a yaml `card:` key */
function hasCard(file: string): boolean {
  if (existsSync(sidecarPath(file))) return true;
  try {
    const text = readFileSync(file, "utf8");
    if (file.endsWith(".md")) { const m = /^---\n([\s\S]*?)\n---/.exec(text); return !!m && /\bsummary:/.test(m[1]!); }
    if (/\.ya?ml$/.test(file)) { const raw = parse(text); return !!raw && typeof raw === "object" && !!(raw as { card?: unknown }).card; }
  } catch { /* binary or unreadable: needs a sidecar */ }
  return false;
}
/** Serialize source-ID allocation across integrated worker publications and
 * ordinary intake. Busy/stale locks are named refusals, never silently stolen.
 * Other ledger editing must not run concurrently with intake (single steward). */
function intakeLock<T>(root: string, work: () => T): T {
  const lock = join(root, "_sources", ".intake.lock");
  let fd: number;
  try { fd = openSync(lock, "wx", 0o600); }
  catch { throw new Error("source intake busy or unavailable: retry after the active writer finishes; inspect a stale .intake.lock rather than deleting it blindly"); }
  try { return work(); } finally { closeSync(fd); rmSync(lock); }
}
export interface SourceVersion { id: SrcId; hash: string; }
/** Register an immutable skill-produced artifact against EXACT input versions.
 * Synthesis-only, all-source grounds in this first publication contract. No
 * implicit replacement/supersession; retry with identical provenance is safe. */
export function publishSynthesis(root: string, file: string, intent: string[], inputs: readonly SourceVersion[]): VerifiedSource {
  return intakeLock(root, () => {
    if (!inputs.length) throw new Error("publish synthesis: nonempty inputs required");
    if (!intent.length || intent.some(s => typeof s !== "string" || !s.trim())) throw new Error("publish synthesis: nonempty capture intent required");
    const grounds = [...new Set(inputs.map(input => {
      const current = verifySource(root, input.id);
      if (current.hash !== input.hash) throw new Error(`publish synthesis: input version changed for ${input.id}`);
      return current.id;
    }))].sort();
    const base = realpathSync(root);
    const rel = relative(base, resolve(file)).split("\\").join("/");
    const actual = realpathSync(file);
    if (!rel.startsWith("_synthesis/") || !relative(base, actual).split("\\").join("/").startsWith("_synthesis/") || rel.endsWith(".card.yaml") || actual.endsWith(".card.yaml"))
      throw new Error("publish synthesis: output must be a work product under _synthesis");
    if (!statSync(actual).isFile()) throw new Error("publish synthesis: output is not a regular file");
    const hash = createHash("sha256").update(readFileSync(actual)).digest("hex");
    const book = readBook(root);
    const existing = book.entries.find(e => e.file === rel) ?? book.entries.find(e => e.hash === hash);
    if (existing) {
      const current = verifySource(root, existing.id);
      if (current.hash !== hash) throw new Error("publish synthesis: registered output changed; use a new versioned path");
      if (existing.provenance !== "synthesis" || JSON.stringify([...(existing.grounds ?? [])].sort()) !== JSON.stringify(grounds)
        || JSON.stringify([...existing.intent].sort()) !== JSON.stringify([...intent].sort()))
        throw new Error(`publish synthesis: provenance collision with ${existing.id}; no implicit relabeling`);
      return current;
    }
    if (!hasCard(actual)) throw new Error(`publish synthesis: ${basename(actual)} has no card — a sidecar ${basename(sidecarPath(actual))} beside it, or a head card (md frontmatter / yaml card: key) (A22)`);
    const id = routeUnlocked(root, actual, intent, { provenance: "synthesis", grounds });
    return verifySource(root, id);
  });
}

/** the one intake door: tag + one idempotent-by-hash entry; mints SRC-nnn; no copies, no sidecars.
 * opts (A14): provenance; grounds REQUIRED when synthesis — refused by name otherwise */
export function route(root: string, file: string, intent: string[], opts?: { provenance?: "client" | "public" | "synthesis"; grounds?: string[] }): SrcId {
  return intakeLock(root, () => routeUnlocked(root, file, intent, opts));
}
function routeUnlocked(root: string, file: string, intent: string[], opts?: { provenance?: "client" | "public" | "synthesis"; grounds?: string[] }): SrcId {
  if (!existsSync(file)) throw new Error(`route: no such staged file ${file}`);
  if (opts?.provenance === "synthesis" && !(opts.grounds && opts.grounds.length))
    throw new Error(`route: synthesis provenance requires non-empty grounds (${basename(file)})`);
  // the ledger records the file WHERE IT LIVES, root-relative: staged files in
  // _sources/new/, synthesis in _synthesis/ (it is the store — never moved).
  // Every refusal comes BEFORE any filesystem change (review B3: no deletions, ever).
  const rel = relative(root, file);
  if (rel.startsWith("..") || isAbsolute(rel)) throw new Error(`route: ${file} is outside the engagement`);
  if (rel.startsWith(join("_sources", "scans"))) throw new Error(`route: ${rel} is a scan — a scout report is never a source (A20)`);
  if (rel.endsWith(".card.yaml")) throw new Error(`route: ${rel} is a card — a card is never a source (A22)`);
  const inNew = rel.startsWith(join("_sources", "new") + "/"), inSynth = rel.startsWith("_synthesis/");
  if (!inNew && !inSynth) throw new Error(`route: ${rel} is not a staged file (_sources/new/) or a work product (_synthesis/) — nothing else is a source`);
  if (!intent.length) throw new Error(`route: ${rel} declares no intent — name the capture slugs this source is expected to inform`);
  const b = readBook(root);
  const already = b.entries.find(e => e.file === rel);
  if (already) throw new Error(`route: ${rel} is already registered as ${already.id}`);
  const hash = createHash("sha256").update(readFileSync(file)).digest("hex");
  const dup = b.entries.find(e => e.hash === hash);
  if (dup) {
    // same content = same source; a FRESH copy in new/ is removed (no copies) — anything else is left exactly where it is
    if (inNew) rmSync(file);
    return dup.id;
  }
  const id = nextId(b.entries.map(e => e.id), "SRC");
  const entry: MutableEntry = { id, file: rel, hash, intent: [...intent], answers: [] };
  if (opts?.provenance) entry.provenance = opts.provenance;
  if (opts?.grounds) entry.grounds = [...opts.grounds];
  b.entries.push(entry);
  writeBook(root, b);
  return id;
}
/** the one scan writer (A20): validate the report against the default template, land it as
 * _sources/scans/SRC-nnn.yaml (overwriting any earlier scan), point the ledger entry at it */
export function scan(root: string, src: SrcId, reportFile?: string): string {
  const b = readBook(root);
  const e = b.entries.find(e => e.id === src);
  if (!e) throw new Error(`scan: ${src} not in the ledger`);
  if (reportFile === undefined) {
    // A22: no report given — land the PRODUCER'S sidecar card beside a registered SYNTHESIS artifact; never for a client source
    if (e.provenance !== "synthesis") throw new Error(`scan: ${src} is not a synthesis artifact — a client source needs a scout report (intake-scan), not a sidecar`);
    const side = sidecarPath(join(root, e.file));
    if (!existsSync(side)) throw new Error(`scan: ${src} has no sidecar card beside ${e.file} and no report was given`);
    reportFile = side;
  }
  if (!existsSync(reportFile)) throw new Error(`scan: no such report ${reportFile}`);
  const report = parse(readFileSync(reportFile, "utf8"));
  for (const k of ["summary", "keyItems"] as const)
    if (report == null || typeof report !== "object" || !(k in report))
      throw new Error(`scan: report for ${src} lacks the default template's field "${k}"`);
  const rel = join("_sources", "scans", `${src}.yaml`);
  mkdirSync(join(root, "_sources", "scans"), { recursive: true });
  writeFileSync(join(root, rel), stringify(report));
  e.scan = rel;
  writeBook(root, b);
  return rel;
}
/** retire one fully-cited source from new/ to processed/, rewriting its entry — the ledger's own hand (review: one writer per store) */
export function retire(root: string, src: SrcId): string {
  const b = readBook(root);
  const e = b.entries.find(e => e.id === src);
  if (!e) throw new Error(`retire: ${src} not in the ledger`);
  if (!e.file.startsWith("_sources/new/")) throw new Error(`retire: ${src} is not in _sources/new/`);
  const to = join("_sources", "processed", basename(e.file));
  if (existsSync(join(root, to))) throw new Error(`retire: ${to} already exists — never overwrite`);
  mkdirSync(join(root, "_sources", "processed"), { recursive: true });
  renameSync(join(root, e.file), join(root, to));
  e.file = to;
  writeBook(root, b);
  return to;
}
/** decline a staged file with a durable reason */
export function park(root: string, file: string, reason: string): void {
  const rel = relative(root, file);
  if (rel.startsWith("..") || isAbsolute(rel) || !rel.startsWith(join("_sources", "new") + "/")) throw new Error(`park: ${file} is not a staged file in _sources/new/`);
  const b = readBook(root);
  if (b.entries.some(e => e.file === rel)) throw new Error(`park: ${rel} is already routed — a registered source is retired at checkpoint, never parked`);
  mkdirSync(join(root, "_sources/parked"), { recursive: true });
  const dest = join(root, "_sources/parked", basename(file));
  writeFileSync(dest, readFileSync(file)); rmSync(file);
  b.parked.push({ file: join("_sources/parked", basename(file)), reason });
  writeBook(root, b);
}
/** the whole ledger picture — consumed/outstanding COMPUTED from capture citations (A18), never stored */
export function status(root: string): { unrouted: string[]; entries: LedgerEntry[]; consumed: Map<SrcId, string[]>; outstanding: Map<SrcId, string[]> } {
  const b = readBook(root);
  // unrouted = files in new/ whose FULL relative path is not registered (review B7: a re-dropped name is never hidden)
  const routedPaths = new Set(b.entries.map(e => e.file));
  const newDir = join(root, "_sources/new");
  const unrouted = (existsSync(newDir) ? readdirSync(newDir) : []).filter(f => !f.startsWith(".") && !routedPaths.has(join("_sources", "new", f)));
  const consumed = new Map<SrcId, string[]>(), outstanding = new Map<SrcId, string[]>();
  const ents = kernel.entitiesLenient(root);
  for (const e of b.entries) {
    const got = ents.filter(en => en.statements.some(st => st.cites.includes(e.id))).map(en => en.slug);
    consumed.set(e.id, got);
    const intent = Array.isArray(e.intent) ? e.intent : [];  // a hand-broken entry is check's defect, never a crash of the read
    outstanding.set(e.id, intent.filter(sl => !got.includes(sl)));
  }
  return { unrouted, entries: b.entries as unknown as LedgerEntry[], consumed, outstanding };
}
