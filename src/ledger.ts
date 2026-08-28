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
 * FILE LIFECYCLE, pinned: a routed file STAYS in _sources/new/ until
 * retirement moves it to processed/ (at checkpoint, once fully cited);
 * LedgerEntry.file is root-relative and is rewritten on retire, so
 * status() survives the move. A staged duplicate (same hash) returns
 * the existing id and the duplicate file is REMOVED — no copies. The
 * ledger itself is _sources/sources.yaml.
 */
import type { SrcId, AskId } from "./types.ts";

export interface LedgerEntry {
  id: SrcId; file: string; hash: string;
  /** the debt declared at route time: fragment slugs this source is expected to inform (A18: intent, balanced by computed consumption) */
  intent: readonly string[];
  answers: readonly AskId[];
  provenance?: "client" | "public" | "synthesis";
  /** synthesis sources ONLY (A12): grounds this work product was built from — required, must resolve; never upgrades standing */
  grounds?: readonly string[];
  /** intake scan (A17): cheap-model metadata attached at route time by the intake-scan skill. Advisory only: never grounds, never cited. */
  scan?: { summary: string; keyItems: readonly string[] };
}

/** the one intake door: tag + one idempotent-by-hash entry; mints SRC-nnn; no copies, no sidecars.
 * opts (A14): provenance; grounds REQUIRED when synthesis — refused by name otherwise */
export function route(root: string, file: string, intent: string[], opts?: { provenance?: "client" | "public" | "synthesis"; grounds?: string[] }): SrcId { throw new Error("mock-out"); }
/** decline a staged file with a durable reason */
export function park(root: string, file: string, reason: string): void { throw new Error("mock-out"); }
/** the whole ledger picture — consumed/outstanding COMPUTED from capture citations (A18), never stored */
export function status(root: string): { unrouted: string[]; entries: LedgerEntry[]; consumed: Map<SrcId, string[]>; outstanding: Map<SrcId, string[]> } { throw new Error("mock-out"); }
