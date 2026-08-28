/**
 * findings — where the brain may hold an opinion.
 *
 * Owns/writes: _registers/findings.yaml. The only store of judgment about
 * the client's processes, fed by the analysis license (analyses are SKILLS after A9; candidates arrive via answers.ground). Grounds are
 * mandatory and must RESOLVE (SrcId | slug#LOCAL-ID | entity slug) —
 * refused by name otherwise. Rejection is terminal and KEPT: a rejected
 * finding is case law, not deleted. Only accepted findings render or
 * ground an answer.
 */
import { parse, stringify } from "yaml";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import * as answers from "./answers.ts";
import type { Finding, FindingId, FindingStatus, Ground } from "./types.ts";

const REG = (root: string) => join(root, "_registers", "findings.yaml");
interface MutableFinding { id: FindingId; status: FindingStatus; claim: string; grounds: string[]; theme?: string; rejectedReason?: string; }
function readReg(root: string): MutableFinding[] {
  if (!existsSync(REG(root))) return [];
  return (parse(readFileSync(REG(root), "utf8")) as MutableFinding[] | null) ?? [];
}
function writeReg(root: string, r: MutableFinding[]): void { mkdirSync(join(root, "_registers"), { recursive: true }); writeFileSync(REG(root), stringify(r)); }
function must(r: MutableFinding[], id: FindingId): MutableFinding {
  const f = r.find(f => f.id === id);
  if (!f) throw new Error(`finding: no such finding ${id}`);
  return f;
}

/** mint FIND-nnn; every ground must resolve or the mint refuses by name */
export function propose(root: string, claim: string, grounds: Ground[], theme?: string): FindingId {
  answers.cite(root, grounds); // refuses by name if any ground fails to resolve
  const r = readReg(root);
  const id = `FIND-${String(r.length + 1).padStart(3, "0")}` as FindingId;
  const f: MutableFinding = { id, status: "proposed", claim, grounds: grounds.map(g => typeof g === "string" ? g : g.slug) };
  if (theme !== undefined) f.theme = theme;
  r.push(f); writeReg(root, r);
  return id;
}
/** the human's ruling, in conversation, recorded */
export function accept(root: string, id: FindingId): void {
  const r = readReg(root); must(r, id).status = "accepted"; writeReg(root, r);
}
export function reject(root: string, id: FindingId, reason: string): void {
  const r = readReg(root); const f = must(r, id);
  f.status = "rejected"; f.rejectedReason = reason; writeReg(root, r);
}
/** accepted only — what a deliverable may bind and an answer may cite */
/** the whole register, rejections included — case law is kept */
export function entriesOf(root: string): Finding[] { return readReg(root) as unknown as Finding[]; }
export function renderable(root: string): Finding[] { return readReg(root).filter(f => f.status === "accepted") as unknown as Finding[]; }
