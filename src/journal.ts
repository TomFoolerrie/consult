/**
 * journal — judgment's homes.
 *
 * Owns/writes: _journal/ (flags.yaml, tenure.yaml, sessions/). The law
 * made concrete: a token spent on judgment lands in a file the machine
 * reads; a transcript is not a home. Flags: any agent's out-of-lane
 * judgment, open until actioned/declined WITH a reference. Tenure: the
 * librarian's precedent record — a new sitting inherits case law instead
 * of re-deriving it. Sessions: written BY THE MACHINERY (every verb and
 * dispatch appends itself) — closing the oracle's named evidence gap of
 * audits living only in transcripts. Engagement-scoped, as the librarian is.
 */
import type { FlagId, FlagState, TenureId, TenureKind } from "./types.ts";

export function flag(root: string, target: string, origin: string, text: string): FlagId { throw new Error("mock-out"); }
/** actioned | declined, always with the actioning reference */
export function flagClose(root: string, id: FlagId, state: Exclude<FlagState, "open">, ref: string): void { throw new Error("mock-out"); }
export function openFlags(root: string): { id: FlagId; target: string; text: string }[] { throw new Error("mock-out"); }
/** file one precedent (ruling | deferred | doubt) */
export function tenure(root: string, kind: TenureKind, text: string): TenureId { throw new Error("mock-out"); }
/** the case law a new sitting inherits */
export function tenureStanding(root: string): { id: TenureId; kind: TenureKind; text: string }[] { throw new Error("mock-out"); }
/** every verb and dispatch appends itself to the sitting's session record */
export function sessionAppend(root: string, event: SessionEvent): void { throw new Error("mock-out"); }
export interface SessionEvent { at: string; verb: string; detail: string; costEstimate?: number; costActual?: number; }
