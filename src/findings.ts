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
import type { Finding, FindingId, Ground } from "./types.ts";

/** mint FIND-nnn; every ground must resolve or the mint refuses by name */
export function propose(root: string, claim: string, grounds: Ground[], theme?: string): FindingId { throw new Error("mock-out"); }
/** the human's ruling, in conversation, recorded */
export function accept(root: string, id: FindingId): void { throw new Error("mock-out"); }
export function reject(root: string, id: FindingId, reason: string): void { throw new Error("mock-out"); }
/** accepted only — what a deliverable may bind and an answer may cite */
export function renderable(root: string): Finding[] { throw new Error("mock-out"); }
export function byTheme(root: string): Map<string, Finding[]> { throw new Error("mock-out"); }
