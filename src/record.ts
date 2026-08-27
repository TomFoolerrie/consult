/**
 * record — the machinery's hand. (A18 split, M3/M4.)
 *
 * Owns/writes: git (checkpoint) and _registers/sessions/ — the
 * append-only session record every verb and dispatch appends itself to
 * (closing the oracle's named evidence gap of audits living only in
 * transcripts), the budget line included (A14/A15).
 *
 * gate() is law 6 made auditable (A18, M4): the human's yes and the
 * crossing, recorded — for BOTH gates. asks.accept/sent are its
 * ask-shaped callers; a render leaving the building is gated the same
 * way; a spend over budget records its ruling here. Two gates on the
 * cycle, both now in the record.
 *
 * checkpoint() commits the WHOLE engagement (no curated pathspec) and
 * appends the session record; fully-cited sources retire to processed/
 * here (A18 — consumption is computed, retirement is its side effect).
 *
 * budget is the D9 mechanism: spends are proposed with an estimate
 * (priced with token asymmetry in mind — review-with-edits over
 * regeneration where it wins), auto-proceed under the sitting budget,
 * wait above it or for anything client-facing. spend() records estimate
 * and actual so pricing stays auditable.
 */
export interface SessionEvent { at: string; verb: string; detail: string; costEstimate?: number; costActual?: number; }
export interface Budget { limit: number; spent: number; remaining: number; }

/** commit the whole engagement as consult: <label>; append the session record; retire fully-cited sources */
export function checkpoint(root: string, label: string, dryRun?: boolean): { committed: string[]; retired: string[] } { throw new Error("mock-out"); }
/** every verb and dispatch appends itself to the sitting's session record */
export function sessionAppend(root: string, event: SessionEvent): void { throw new Error("mock-out"); }
/** the human's yes and the crossing, in the session record — law 6, auditable (A18) */
export function gate(root: string, g: { kind: "send" | "spend"; what: string; ruling: string }): void { throw new Error("mock-out"); }
/** appends the budget line to the session record — the budget's one home (A14); remaining is derived */
export function budgetSet(root: string, tokens: number): void { throw new Error("mock-out"); }
export function budget(root: string): Budget { throw new Error("mock-out"); }
/** record one spend's estimate and actual in the session record */
export function spend(root: string, estimate: number, actual: number, what: string): void { throw new Error("mock-out"); }
