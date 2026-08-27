/**
 * ledger — the source of sources. (Distilled by A9.)
 *
 * Owns/writes: _sources/ entirely; the one SRC-id minter. Doctrine kept
 * verbatim: file position is display; the ledger is truth — no question is
 * ever answered by listing a folder. The intake door is ONE door (D4): a
 * fresh source and a client's response arrive the same way — route() is
 * the only way in (register/route merged, A9). credit() retires a source
 * only when every touch is credited — the balanced ledger that made run 2
 * clean. touches ⊆ existing fragment slugs, validated at write.
 *
 * Ask-answer bookkeeping moved behind asks.respond (A9): one event, one
 * verb — the ledger exposes no recordAnswers.
 *
 * SYNTHESIS SOURCES (A12): the consultant may register its own work
 * products from _synthesis/ through the same one door, with
 * provenance "synthesis" and declared grounds. Citable like any source;
 * never upgrades standing — laundering claimed into evidenced by citing
 * your own summary is structurally impossible.
 */
import type { SrcId, AskId } from "./types.ts";

export interface LedgerEntry {
  id: SrcId; file: string; hash: string;
  touches: readonly string[];              // fragment slugs this source informs
  answers: readonly AskId[]; consumed: ReadonlyMap<string, readonly string[]>;
  provenance?: "client" | "public" | "synthesis";
  /** synthesis sources ONLY (A12): the grounds this work product was built
   * from — required, must resolve. A synthesis source NEVER upgrades
   * standing: a statement citing it inherits the standing of these
   * grounds, resolved through the chain. */
  grounds?: readonly string[];
}

/** the one intake door: tag + one idempotent-by-hash entry; mints SRC-nnn; no copies, no sidecars.
 * opts (A14): provenance (client | public | synthesis); grounds REQUIRED when synthesis — refused by name otherwise */
export function route(root: string, file: string, touches: string[], opts?: { provenance?: "client" | "public" | "synthesis"; grounds?: string[] }): SrcId { throw new Error("mock-out"); }
/** decline a staged file with a durable reason */
export function park(root: string, file: string, reason: string): void { throw new Error("mock-out"); }
/** record consumption; retire fully-read sources; returns how many moved.
 * A14: filled = slugs whose open content this source filled; updated = slugs it
 * corroborated or revised. credit (per-source) and asks.settle (per-ask) are
 * INDEPENDENT debts — both visible, no ordering imposed. */
export function credit(root: string, filled: string[], updated?: string[]): number { throw new Error("mock-out"); }
/** the whole ledger picture: unrouted new/ diff, entries in order, the debt list per source */
export function status(root: string): { unrouted: string[]; entries: LedgerEntry[]; outstanding: Map<SrcId, string[]> } { throw new Error("mock-out"); }
