# Risk and Sequencing Rationale — `very-cool-sentiment-analysis` v1

## The heuristic

**WSJF** — Weighted Shortest Job First: score = (user/business value + time criticality + risk-reduction
value) ÷ job size, and the higher score ships first.

The human's answer (Q2 = A) was to score the work with a WSJF-style model, weighting **risk reduction
and value evenly** and penalising size. That is the heuristic behind the order recorded in
`bolt-plan.md`.

## The scoring, as applied

There is one Bolt, so the score decided the **order inside the Bolt** rather than a sequence of Bolts.
With risk reduction and value weighted evenly, the candidates score as follows.

| Work | Value | Risk reduction | Size (larger = more work) | Order |
|---|---|---|---|---|
| Engine path: the typed contract and the two implementations, live client under an injected transport | High — it is the product's whole reason to exist | High — the live call, the answer-reading and the injected seam are the intent's biggest unknowns | Medium | 1 |
| Storage path: `provider` column, in-place migration, v1 record shape | High — history is what makes results worth keeping | High — a schema change against a database that already holds rows is the second unknown | Medium | 2 |
| Failure paths: the live-attempt refusal, envelope codes, boundary validation | Medium | Medium — the review already named the gaps, so little is unknown | Small | 3 |
| Interface: page states, indicator, accessibility fixes, documentation and manifest corrections | High — it is what the user actually uses | Low — the mockups and the checklist already pin it | Large | 4 |

Ties between the first two were broken toward the engine, because the storage shape can only be
finalised once the record the engine produces is settled.

## Risk-first argument (Q1 = A)

The human chose the riskiest parts first. The two genuine unknowns are (a) whether the typed engine
contract can be read from the live answer without ever guessing a label, and (b) whether a schema
change can keep the rows already in `data/sentiment.db`. Both are attacked first, so a wrong
assumption surfaces while the work is small rather than after the interface is polished.

## Alternatives rejected

- **Value-first (option B on Q1):** the submit-and-see-a-label journey is already working, so shipping
  it first would prove nothing the repository does not already demonstrate, and it would leave the two
  unknowns to the end.
- **Thin end-to-end slice first (option C):** the walking-skeleton idea inverts here — the app already
  runs end to end, so a thin slice would duplicate existing behaviour instead of reducing risk. The
  scope's skeleton flag is off for the same reason.
- **Risk-weighted scoring (option B on Q2):** would have pushed the interface further down and the
  failure paths further up; the human chose even weighting, and the resulting order differs only in
  the middle, where the failure paths and the interface are both already pinned by the review and the
  mockups.
- **Judgement-only sequencing (option C on Q2):** cheaper to produce, but it would leave the ordering
  reasoning unstated, and the ordering is the one thing this stage exists to record.

## Deviation from topological order

None. With a single unit there is no topological constraint to deviate from, so nothing needs
justifying against the DAG.
