/**
 * returns — the RETURN port (A27), the one door for what a skill produces.
 *
 * Owns/writes: nothing of its own. It mints finding proposals through
 * findings.propose and appends ONE line to the session record through
 * record.sessionAppend — both stores keep their single writer.
 *
 * The ruling it encodes: `route` is the one door for what comes in from
 * the world; `return` is the one door for what skills produce. It
 * VALIDATES everything first (all-or-nothing: a refusal mints nothing
 * and writes nothing), MINTS the finding proposals, RECORDS the run,
 * and HANDS the rest back. It decides nothing — asks are the
 * consultant's judgment and capture is written by hand, so asks and
 * statements are NEVER minted or written here; they come back in the
 * result so the consultant sees them.
 *
 * GROUNDS, and the one compromise (stated, not hidden): the read port's
 * currency is a LOCATOR — `SRC-002:L4-L9`, `SRC-002:R7`, `slug#Q-1`, a
 * bare slug. `findings.propose` takes `Ground = SrcId | CalloutAddr |
 * { slug }` and resolves through `answers.cite`, which accepts a bare
 * SRC id or a capture address and refuses anything carrying a `:`
 * locator. So a located ground is VALIDATED here at full precision
 * (sourceExcerpt for lines — it refuses out of range; sourceRecord for
 * CSV records), minted with the bare SRC id findings accepts, and the
 * exact locator is kept VISIBLE in the finding's claim rather than
 * dropped. Nothing derived is stored: the locator is the skill's own
 * words about what it stood on.
 */
import { parse } from "yaml";
import { readFileSync, existsSync } from "node:fs";
import * as answers from "./answers.ts";
import * as ledger from "./ledger.ts";
import * as kernel from "./kernel.ts";
import * as findings from "./findings.ts";
import * as record from "./record.ts";
import type { CalloutAddr, FindingId, Ground, SrcId,
  ReturnAsk, ReturnResult, ReturnStatement, SkillReturn } from "./types.ts";

const KEYS = ["skill", "run", "findings", "asks", "statements", "artifacts", "flags"] as const;
const LINES = /^(SRC-\d+):L(\d+)-L(\d+)$/;
const RECORD = /^(SRC-\d+):R(\d+)$/;
const BARE_SRC = /^SRC-\d+$/;

function text(v: unknown, what: string): string {
  if (typeof v !== "string" || !v.trim()) throw new Error(`return: ${what} must be a non-empty string`);
  return v;
}
function list(v: unknown, what: string): unknown[] {
  if (v === undefined || v === null) return [];
  if (!Array.isArray(v)) throw new Error(`return: ${what} must be a list`);
  return v;
}

/** read one return file into its typed shape; any other top-level key is refused BY NAME */
export function read(file: string): SkillReturn {
  if (!existsSync(file)) throw new Error(`return: no such return file ${file}`);
  let raw: unknown;
  try { raw = parse(readFileSync(file, "utf8")); }
  catch (e) { throw new Error(`return: ${file} is not readable YAML — ${(e as Error).message}`); }
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error(`return: ${file} is not a return — a return is a mapping with skill and run`);
  const r = raw as Record<string, unknown>;
  for (const k of Object.keys(r))
    if (!(KEYS as readonly string[]).includes(k))
      throw new Error(`return: unknown key "${k}" — a return carries ${KEYS.join(", ")} and nothing else`);
  const out: SkillReturn = {
    skill: text(r.skill, "skill"), run: text(r.run, "run"),
    findings: [], asks: [], statements: [], artifacts: [], flags: [],
  };
  list(r.findings, "findings").forEach((f, i) => {
    const n = `finding ${i + 1}`;
    if (!f || typeof f !== "object") throw new Error(`return: ${n} is not a mapping`);
    const o = f as Record<string, unknown>;
    const grounds = list(o.grounds, `${n} grounds`).map((g, j) => text(g, `${n} ground ${j + 1}`));
    if (!grounds.length) throw new Error(`return: ${n} stands on no ground — a finding names at least one`);
    const entry: SkillReturn["findings"][number] = { claim: text(o.claim, `${n} claim`), grounds };
    if (o.theme !== undefined) entry.theme = text(o.theme, `${n} theme`);
    out.findings.push(entry);
  });
  list(r.asks, "asks").forEach((a, i) => {
    const n = `ask ${i + 1}`;
    if (!a || typeof a !== "object") throw new Error(`return: ${n} is not a mapping`);
    const o = a as Record<string, unknown>;
    const questions = list(o.questions, `${n} questions`).map((q, j) => text(q, `${n} question ${j + 1}`) as CalloutAddr);
    if (!questions.length) throw new Error(`return: ${n} names no question record — an ask is minted against questions`);
    out.asks.push({ text: text(o.text, `${n} text`), questions });
  });
  list(r.statements, "statements").forEach((s, i) => {
    const n = `statement ${i + 1}`;
    if (!s || typeof s !== "object") throw new Error(`return: ${n} is not a mapping`);
    const o = s as Record<string, unknown>;
    out.statements.push({ slug: text(o.slug, `${n} slug`), text: text(o.text, `${n} text`),
      cites: list(o.cites, `${n} cites`).map((c, j) => text(c, `${n} cite ${j + 1}`)) });
  });
  out.artifacts = list(r.artifacts, "artifacts").map((a, i) => text(a, `artifact ${i + 1}`) as SrcId);
  out.flags = list(r.flags, "flags").map((f, i) => text(f, `flag ${i + 1}`));
  return out;
}

/**
 * resolve ONE ground or cite at full locator precision, or refuse by name.
 * Returns the bare reference findings.propose/answers.cite accept.
 */
function resolve(root: string, ref: string, where: string): Ground {
  const fail = (m: string): never => { throw new Error(`return: ${where} ${ref} — ${m}`); };
  const lines = LINES.exec(ref);
  if (lines) {
    const [, id, start, end] = lines as unknown as [string, SrcId, string, string];
    try { ledger.sourceExcerpt(root, id, { start: Number(start), end: Number(end) }); }
    catch (e) { fail((e as Error).message); }
    return ref as Ground;   // verified; the locator itself is the ground (A27)
  }
  const rec = RECORD.exec(ref);
  if (rec) {
    const [, id, num] = rec as unknown as [string, SrcId, string];
    try { ledger.sourceRecord(root, id, Number(num)); }
    catch (e) { fail((e as Error).message); }
    return ref as Ground;   // verified; the locator itself is the ground (A27)
  }
  if (ref.includes(":")) fail("malformed locator — use SRC-nnn:Lx-Ly (lines) or SRC-nnn:Rn (CSV record)");
  try { answers.cite(root, [ref as Ground]); }
  catch (e) { fail((e as Error).message); }
  return ref as Ground;
}

/** a cite on a returned statement is a SOURCE, bare or located — never a capture address */
function resolveCite(root: string, ref: string, where: string): void {
  if (!BARE_SRC.test(ref) && !LINES.test(ref) && !RECORD.test(ref))
    throw new Error(`return: ${where} ${ref} — a statement cites a source: SRC-nnn, SRC-nnn:Lx-Ly or SRC-nnn:Rn`);
  resolve(root, ref, where);
}

/** the run's fingerprint in the session record — landed exactly once */
const stamp = (r: { skill: string; run: string }) => `${r.skill}/${r.run}`;

/**
 * land a return: VALIDATE everything, then mint, record, and hand over.
 * Every refusal happens before the first mint — a refused return mints
 * nothing and writes nothing.
 */
export function land(root: string, file: string): ReturnResult {
  const r = read(file);

  // idempotence: one (skill, run) lands once — a re-run never mints duplicate findings
  const id = stamp(r);
  if (record.sessionLines(root).some(l => l.verb === "return" && l.detail.startsWith(`${id}: `)))
    throw new Error(`return ${id} was already landed`);

  // --- validate, all of it, before anything is minted or written ---
  const grounds: Ground[][] = r.findings.map((f, i) =>
    f.grounds.map(g => resolve(root, g, `finding ${i + 1} ground`)));

  const ents = kernel.entitiesLenient(root);
  r.asks.forEach((a, i) => {
    for (const q of a.questions) {
      const [slug, local] = q.split("#") as [string, string | undefined];
      const e = ents.find(e => e.slug === slug);
      if (!e || !local || !kernel.openQuestions(e).some(c => c.id === local))
        throw new Error(`return: ask ${i + 1} names ${q}, which is not an open question record`);
    }
  });

  r.statements.forEach((s, i) => {
    if (!ents.some(e => e.slug === s.slug))
      throw new Error(`return: statement ${i + 1} names the fragment ${s.slug}, which does not exist — return does not create fragments`);
    for (const c of s.cites) resolveCite(root, c, `statement ${i + 1} cite`);
  });

  for (const a of r.artifacts) {
    let entry;
    try { entry = ledger.verifySource(root, a); }
    catch (e) { throw new Error(`return: artifact ${a} — ${(e as Error).message}`); }
    if (entry.provenance !== "synthesis")
      throw new Error(`return: ${a} is not a published work product — an artifact on a return is registered synthesis`);
  }

  // --- land ---
  // locators are first-class grounds (A27): they pass straight through and stay visible in the register
  const minted: FindingId[] = r.findings.map((f, i) => findings.propose(root, f.claim, [...new Set(grounds[i]!)] as Ground[], f.theme));

  record.sessionAppend(root, { at: new Date().toISOString(), verb: "return",
    detail: `${id}: ${r.findings.length} findings, ${r.asks.length} asks, ${r.statements.length} statements, ${r.artifacts.length} artifacts, ${r.flags.length} flags` });

  const handed: { asks: ReturnAsk[]; statements: ReturnStatement[]; flags: string[] } =
    { asks: r.asks, statements: r.statements, flags: r.flags };
  return { minted, handed, artifacts: r.artifacts };
}
