"""consult <verb> — the one entry point.

Owns: nothing on disk. One argparse tree, one interpreter-floor check, one
console-compat shim. Every verb in the system is a subcommand here; no module
has its own __main__. This kills the oracle's four competing CLI styles.

The verb inventory (each dispatches to exactly one module function):

  state                       desk.state          where the engagement stands
  checkpoint                  desk.checkpoint     git-commit the engagement
  hold / release-hold         desk.edit_hold      record a gate answer
  budget                      desk.budget         show/set the sitting's spend budget
  register / route / park     ledger.*            source intake
  credit                      ledger.credit       record consumption
  ask propose|accept|send|answer|settle|retire|match|list
                              asks.*              the ask lifecycle
  finding propose|accept|reject|list
                              findings.*          the findings register
  flag add|actioned|declined|list                 journal.*
  tenure add|supersede|resolve|list               journal.*
  scaffold                    engagement.scaffold the confirm gate's deterministic half
  aggregate                   views.aggregate     rebuild derived views
  check                       check.run           the QC gate
  render <deliverable>        render.deliverable  any definition -> docx
  answer "<question>"         answers.ground      a grounded answer (the product)
  needs                       needs.standing      what the shapes still lack
  coverage                    coverage.report     the map, printed
  feeds <verb>                analysis.feeds      analyst candidate feeds
  brief <role> ...            brief.*             a dispatch work order

Refuses: any verb against a folder that fails engagement.locate (a named
refusal, never a guess); any state-changing verb while a contradiction from
desk.state stands, except the verbs that repair it.
"""

from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    """Parse one verb, dispatch it, return its exit code (0 ok, 2 refusal)."""
    raise NotImplementedError
