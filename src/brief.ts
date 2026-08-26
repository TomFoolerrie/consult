/**
 * brief — work orders for delegates, and only delegates.
 *
 * Owns: nothing. A brief exists to resolve facts once for a
 * context-limited delegate; the librarian working directly already holds
 * the picture (R2 — the sitting brief merged into desk.state, which has a
 * printable form). A brief is issued when, and only when, delegation
 * happens; the audit trail for direct work is the session record, written
 * by the machinery. Every brief carries standing tenure + open flags so a
 * delegate never re-derives paid-for judgment. The brief decides nothing
 * about content: facts arrive resolved, judgment stays with the worker.
 */
export function drafter(root: string, area: string, slug: string, mode: "first-draft" | "update"): string { throw new Error("mock-out"); }
/** the bounded "go find out" work order: one question, named sources */
export function reader(root: string, question: string, srcIds: string[]): string { throw new Error("mock-out"); }
/** the assessment work order: license text, the candidate feed, register state */
export function analyst(root: string, verb: string): string { throw new Error("mock-out"); }
