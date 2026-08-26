/**
 * ledger — the source of sources.
 *
 * Owns/writes: _sources/ entirely; the one SRC-id minter. Doctrine kept
 * verbatim: file position is display; the ledger is truth — no question is
 * ever answered by listing a folder. The intake door is ONE door (D4): a
 * fresh source and a client's response arrive the same way. credit()
 * retires a source only when every touch is credited — the balanced ledger
 * that made run 2 clean. touches ⊆ existing fragment slugs, validated at write (no manifest — ROT-2).
 */
import type { SrcId, AskId } from "./types.ts";

export interface LedgerEntry {
  id: SrcId; file: string; hash: string;
  touches: readonly string[];              // fragment slugs this source informs
  answers: readonly AskId[]; consumed: ReadonlyMap<string, readonly string[]>;
  provenance?: "client" | "public";
}

/** register a staged file, tag what it informs; mints SRC-nnn */
export function register(root: string, file: string, touches: string[]): SrcId { throw new Error("mock-out"); }
/** intake routing: tag + one idempotent-by-hash entry; no copies, no sidecars */
export function route(root: string, file: string, touches: string[]): SrcId { throw new Error("mock-out"); }
/** decline a staged file with a durable reason */
export function park(root: string, file: string, reason: string): void { throw new Error("mock-out"); }
/** record consumption; retire fully-read sources; returns how many moved */
export function credit(root: string, filled: string[], updated?: string[]): number { throw new Error("mock-out"); }
/** stamp which asks this source answers (called by asks.match) */
export function recordAnswers(root: string, src: SrcId, asks: AskId[]): void { throw new Error("mock-out"); }
/** the ledger in registration order — read-only */
export function entries(root: string): LedgerEntry[] { throw new Error("mock-out"); }
/** the librarian's debt list: the slugs each source is still owed */
export function outstanding(root: string): Map<SrcId, string[]> { throw new Error("mock-out"); }
/** the loud-until-empty new/ vs ledger diff */
export function status(root: string): { unrouted: string[]; assessed: LedgerEntry[] } { throw new Error("mock-out"); }
