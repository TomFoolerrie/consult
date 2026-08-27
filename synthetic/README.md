# synthetic — the definition of done (MOCK-OUT)

Charter D8: v2.0 is done when several SYNTHETIC ENGAGEMENTS run
consultant-first and the results hold up under analysis. This directory is
that harness.

A synthetic engagement is cheap to fabricate and fully scripted on the
client side:

```
<name>/
  seed/            the staged sources (fabricated client documents)
  objective.md     what the "client" wants, as the human would relay it
  script.yaml      the client simulator: for each expected ask topic, the
                   response document to "put back in" (or a scripted
                   non-answer, to exercise honest absence)
  questions.md     the human questions the run must answer, with the
                   expected standing of each answer (evidenced / contested /
                   absent) — the question-interface exam
  rubric.md        what done looks like for this engagement: which renders,
                   which asks settled, zero hand-edits, session record complete
```

Each run must exercise, at minimum: the question interface with grounded
answers · one full generated round of client engagement (asks curated →
accepted → rendered → responses put back in → matched → settled) · one
demand-driven render. Nordhaven ports in as the first synthetic; at least
two others differ in domain and in failure texture (a contradiction-heavy
seed; a sparse seed where most answers are honest absences).

Results are analyzed ACROSS runs before v2.0 is called done — the analysis
itself lands in `synthetic/RESULTS.md`, machine-written where possible.
