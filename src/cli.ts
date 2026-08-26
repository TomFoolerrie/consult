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
 * Verb inventory (each dispatches to exactly one module function):
 *   state · checkpoint · hold/release-hold · budget            → desk
 *   register · route · park · credit                           → ledger
 *   ask propose|accept|send|answer|settle|retire|match|unask   → asks
 *   finding propose|accept|reject                              → findings
 *   flag … · tenure …                                          → journal
 *   scaffold                                                   → engagement
 *   check                                                      → check
 *   render <deliverable>    (self-contained: compile → build views in-memory → emit)
 *   answer "<question>" · needs · coverage · feeds <verb>      → answers, needs, coverage, analysis
 *   brief <template> …                                         → brief.compose
 */
export function main(argv: string[]): Promise<number> {
  // parse one verb, dispatch, return exit code (0 ok, 2 named refusal)
  throw new Error("mock-out");
}
