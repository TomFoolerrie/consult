/**
 * journal — the machinery's own audit. (Shrunk by A9.)
 *
 * Owns/writes: _journal/sessions/ only. Every verb and dispatch appends
 * itself — closing the oracle's named evidence gap of audits living only
 * in transcripts. Flags and tenure no longer exist as machinery (A9,
 * extending A8): the engine never computed on them — they were agent
 * memory in YAML. Precedent, doubts, and out-of-lane observations live as
 * sections of the librarian's STATE.md, under pad discipline (an
 * observation is closed by noting what actioned it). Workers return
 * observations to the librarian, who logs them.
 */
/** every verb and dispatch appends itself to the sitting's session record */
export function sessionAppend(root: string, event: SessionEvent): void { throw new Error("mock-out"); }
export interface SessionEvent { at: string; verb: string; detail: string; costEstimate?: number; costActual?: number; }
