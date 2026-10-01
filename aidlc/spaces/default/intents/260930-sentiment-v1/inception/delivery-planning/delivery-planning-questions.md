# Delivery Planning — Clarifying Questions

Context: this stage chooses the path through the dependency graph that Units Generation produced. The
sequence is expressed as Bolts — a Bolt is one build pass over a piece of the work, ending in
something that runs. (The word comes back throughout the next phase, so it is worth knowing now.)

Everything is one unit (`U1`, the whole application), so the topology gives no ordering pressure: the
unit is a single node with no edges. What remains is economic — what to build first and how much to
do in one pass.

---

## Q1. What should we build first?

- A. The riskiest parts first — the live engine call, the migration against the existing database, and the in-place changes to running code
- B. The most valuable parts first — the submit-and-see-a-label journey end to end, then the rest
- C. A thin end-to-end slice that proves the whole thing hangs together, then fill it out
- D. A mix — name which approach applies where
- X. Other (please specify)

[Answer]: A. The riskiest parts first — the live engine call, the migration against the existing database, and the in-place changes to running code

## Q2. Should the work be scored with a formal model?

A WSJF-style score is (value + urgency + risk reduction) divided by size; the higher score ships first.

- A. Yes — score the work with a WSJF-style model, weighting risk reduction and value evenly and penalising size
- B. Yes — but weight risk reduction most heavily, since the unknowns are in the engine and the migration
- C. No — keep the ordering judgement-based and record the reasoning in prose
- X. Other (please specify)

[Answer]: A. Yes — score the work with a WSJF-style model, weighting risk reduction and value evenly and penalising size

## Q3. How big should one Bolt be?

- A. One Bolt for the whole unit — it is one deployable, so it lands in one pass
- B. Several thin Bolts that each cut across the unit (for example: the storage contract, then the engine contract, then the page states)
- C. One Bolt per component inside the unit (five Bolts)
- X. Other (please specify)

[Answer]: A. One Bolt for the whole unit — it is one deployable, so it lands in one pass

## Q4. Can anything run in parallel?

With one unit and one sequence, there is no cross-unit parallelism to be had.

- A. Strictly serial — one Bolt after another
- B. Parallel where the work inside a Bolt does not touch the same files
- C. Decide per Bolt when we get there
- X. Other (please specify)

[Answer]: B. Parallel where the work inside a Bolt does not touch the same files

## Q5. What could hold this up from outside the team, and what worries you most?

- A. Nothing external — no approvals, no data windows, no other team; the only outside service is OpenRouter, which we already treat as optional
- B. The OpenRouter live path is the external dependency worth naming (an API key, the model's availability), and it worries me most
- C. The existing database and its rows are the main worry — the migration has to keep them
- D. Something else holds us up or worries me (say what)
- X. Other (please specify)

[Answer]: A. Nothing external — no approvals, no data windows, no other team; the only outside service is OpenRouter, which we already treat as optional
