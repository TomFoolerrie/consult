/**
 * cli — `consult <verb>`, the one entry point.
 *
 * Owns: nothing on disk. LIBRARY FIRST (R5): every verb is a thin wrapper
 * over an exported module function — tests and the synthetic-engagement
 * harness drive the library in-process and assert on typed results
 * (Standing, Defect, Snapshot), never on parsed stdout. One command tree;
 * every verb in the system is a subcommand here; no module has its own
 * entry. Refuses any state-changing
 * verb while a contradiction from desk.state() stands, except the verbs
 * that repair it.
 *
 * Verb inventory after the A9 distillation (each dispatches to exactly
 * one module function; every verb guards an invariant or expands context):
 *   state · checkpoint · budget · coverage · needs      → desk (the one derived picture)
 *   route · park · credit                               → ledger (one intake door)
 *   ask propose|accept|sent|respond|close               → asks (respond = one atomic motion)
 *   finding propose|accept|reject                       → findings
 *   check                                               → check (six mechanical checks)
 *   render <deliverable>   (self-contained: compile → build views in-memory → emit)
 *   answer "<question>"                                 → answers.ground
 *   brief <skill> …                                     → brief.compose
 * Gone (A9): register (merged into route) · new (no scaffolding) ·
 * flag/tenure (state-pad sections) · feeds (analysis is a skill; its
 * retrieval is answers.ground).
 */
export function main(argv: string[]): Promise<number> {
  // parse one verb, dispatch, return exit code (0 ok, 2 named refusal)
  throw new Error("mock-out");
}
