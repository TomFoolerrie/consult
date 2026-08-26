/**
 * cli — `consult <verb>`, the one entry point.
 *
 * Owns: nothing on disk. One command tree; every verb in the system is a
 * subcommand here; no module has its own entry. Refuses any state-changing
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
 *   aggregate · check                                          → views, check
 *   render <deliverable>                                       → render
 *   answer "<question>" · needs · coverage · feeds <verb>      → answers, needs, coverage, analysis
 *   brief <role> …                                             → brief
 */
export function main(argv: string[]): Promise<number> {
  // parse one verb, dispatch, return exit code (0 ok, 2 named refusal)
  throw new Error("mock-out");
}
