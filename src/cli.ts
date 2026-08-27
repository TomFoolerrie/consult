/**
 * cli — `consult <verb>`, the one entry point.
 *
 * Owns: nothing on disk. LIBRARY FIRST (R5): every verb is a thin wrapper
 * over an exported module function — tests and the synthetic-engagement
 * harness drive the library in-process and assert on typed results
 * (Standing, Defect, Snapshot), never on parsed stdout. One command tree;
 * every verb in the system is a subcommand here; no module has its own
 * entry. Refuses any state-changing
 * verb while a contradiction from desk.state() stands — the contradiction's
 * own `repair` field NAMES the verb that may run (A14).
 *
 * Verb inventory after the A9 distillation (each dispatches to exactly
 * one module function; every verb guards an invariant or expands context):
 *   state · coverage · needs                            → desk (PURE — the one derived picture)
 *   checkpoint · budget · spend · gate                  → record (the machinery's hand)
 *   route · park                                        → ledger (one intake door; consumption COMPUTED)
 *   ask propose|accept|sent|respond|close               → asks (answered/settled DERIVED)
 *   finding propose|accept|reject                       → findings
 *   check                                               → check (six mechanical checks)
 *   render <deliverable>   (self-contained: compile → build views in-memory → emit)
 *   answer "<question>"                                 → answers.ground
 *   brief <skill> …                                     → brief.compose
 * Gone: register (A9) · new (A9) · flag/tenure (A9) · feeds (A9) ·
 * credit and ask settle (A18 — consumption and settlement are computed
 * from capture citations, never declared).
 */
export function main(argv: string[]): Promise<number> {
  // parse one verb, dispatch, return exit code (0 ok, 2 named refusal)
  throw new Error("mock-out");
}
