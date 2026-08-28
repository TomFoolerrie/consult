# Cross-run analysis — synthetics #1–#3 (D8) · 2026-08-28

Three engagements, three failure textures, all consultant-first, all
driven through the library in-process (R5). Machine-written where the
numbers are; judgment where marked.

## The numbers
| run | domain | sittings | spent / budget | check errors | engine defects found | exam |
|---|---|---|---|---|---|---|
| 1 Meridian | AP, seeded conflict | 2 | 20.8k / 200k | 0 | **4 (fixed)** | 6/6 |
| 2 Halvard | contradiction-heavy | 2 + repair | 12.5k / 150k | 1 (consultant damage, check-caught, repaired) | 0 | 6/6 |
| 3 Corvus | sparse / absences | 2 | 7.9k / 100k | 0 | 0 | 6/6 |

## What held across all three (judgment)
- **The honesty contract computed correctly in every texture**: conflicts
  held both readings; absences survived non-answers and partial answers;
  a "resolving" response that created a new conflict landed as a new
  question record, not a quiet overwrite.
- **Settlement/consumption derivation never mis-fired**: every settled
  ask was settled by a capture edit; every retirement was earned; the one
  integrity violation (run 2) was the CONSULTANT's, and the check caught
  it by name — the A18 design working exactly as argued.
- **Capture-as-compression held**: after intake, no source was re-read to
  answer any exam question. Token spend per run fell as the harness
  driver matured (20.8k → 12.5k → 7.9k), and estimates ran ~10% high.
- **All four engine defects came from run #1** and were seams no unit
  test crossed (definitions↔render join, git-recovery of empty dirs,
  synthesis file location, silent-ask visibility). Runs #2 and #3 found
  none: the engine hardened after one live-ish engagement — the same
  pattern the v1 evidence showed, now at 1/100th the cost.

## Residual (what D8 leaves open)
- The docx seam (py/render_worker) is the one unexercised leg: render
  compiles, views build, and the emit refuses by name in run #1. v2.0
  proper waits on the worker + a re-run of the render leg.
- The consultant in these runs was scripted-by-the-builder, not a live
  model in the harness loop; the contracts it exercised are the same
  ones agents/consultant.md binds, but a live-consultant run is the
  natural #4.

**D8 status: satisfied for the engine.** Three runs, three textures,
cross-run analysis on the record. Remaining for v2.0: the render worker.
