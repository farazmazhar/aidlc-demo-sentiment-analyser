# Personas — sentiment-opencode v2 analytics layer

> **One persona.** Intent capture settled that the developer is simultaneously the
> only user, the only operator and the only decision-maker in this project, and the
> User Stories plan questions confirmed one persona rather than a split. This
> artifact records what that means for the story set: **every story is written from
> the same "I", and no story may imply a reader, reviewer or audience that does not
> exist.**

## P1 — The Solo Maintainer

> A handle, not a name. This project has one author identity and one human. The
> persona exists to make the "so that" clause of each story answerable, not to
> invent a second reader.

### Role

The only person who runs, uses, verifies and changes this application. They submit
text for analysis, bulk-import CSV files, read the resulting history, and — with
this change — read aggregate analytics over it. They are simultaneously the
developer, the operator, the reviewer and the person who decides whether a change
is done.

### Goals

| # | Goal | Why it matters here |
|---|---|---|
| G1 | See how much has been analysed, in what mix, and how that mix moves over time — without reading rows by hand | The stated problem: the app stores everything and summarises nothing |
| G2 | See what the positive and negative text actually says, as ranked words | The stated goal of the terms endpoint |
| G3 | Trust that reading analytics cannot lose, corrupt or silently alter stored data | The change adds a migration to a store that holds real rows |
| G4 | Trust that a number shown on screen came from a real, complete calculation | The retired `intensity` column and the `NULL`-on-every-row trap make a plausible-looking wrong aggregate possible |
| G5 | Install the same way every time, so a working setup does not stop working | Floating dependency floors mean today's install and tomorrow's differ. *Scoped to "every time" rather than "on any machine": there is one machine and no remote, and pretending otherwise would describe a portability goal this project has not chosen* |
| G6 | Trust that the app stays on the loopback and cannot be reached from elsewhere | The app is unauthenticated and holds an API key in live mode |
| G7 | Have the documentation match the code | The README's HTTP surface table is this project's contract of record |
| G8 | See the shape of the trend at a glance, not as a table of numbers | **Added by the mob round.** No goal in the original set asked for a chart, yet a chart is the view's central commitment — the persona should be the reason for it, not a silent assumption in the story set |

### Status quo and trigger

**Added by the mob round.** The persona originally listed desires with no starting
point, which is why one of the strongest objections in the review — that nothing
challenges the unbounded default range — went unnoticed. It is not that the default
is wrong; it is that nobody had stated what the person does today instead.

- **Status quo:** I submit text one item at a time, or import a CSV in bulk. When I
  want to know what I have, I read the history list newest-first and count by eye,
  or I ask the database directly. I cannot answer "how did this month trend?" at
  all, because nothing in the app aggregates anything.
- **Trigger:** my stored history grew past the point where reading it by hand is
  reasonable — the same trigger intent capture recorded, now with the specific pain
  attached to it.
- **What "better" looks like:** one view that answers volume, mix, confidence,
  trend and vocabulary for a date range I choose, and that never shows me a
  confident-looking number derived from nothing.

### Pain points

Pain ids are `PN<n>`, not `P<n>`. The original draft used `P1` for both the
persona and the first pain point — **corrected by the mob round**, because a reader
resolving "P1" could not tell which they had.

| # | Pain | Consequence if unaddressed |
|---|---|---|
| PN1 | There is no summary of any kind | Every question about volume, mix or trend is answered by hand, or not at all |
| PN2 | The `intensity` column was retired in v1 but still invites an aggregate | `AVG(intensity)` returns `null` forever; a UI would show a confident empty number |
| PN3 | `_rebuild_analyses` performs `RENAME` → `CREATE TABLE` → `COPY` → `DROP TABLE` and the table DDL declares **no index**, so any index is destroyed on a migrating store | Analytics indexes could vanish silently, with no warning possible |
| PN4 | Dependencies are floors, not pins, and there is no lockfile | A working install can stop working with no code change; the suite's pass/fail depends on the resolved dependency set |
| PN5 | Nothing runs the gates — no CI, no hook, no script | 96 % coverage and a clean `ruff` run are only as real as the developer's memory |
| PN6 | R-01, the cross-thread connection defect, is recorded and accepted, and no test reproduces it | Overlapping requests can fail unpredictably. **Corrected:** the original wording justified this by "a page that polls on a date range". No story in the set performs polling — the view fetches on load and on an explicit range change — so that justification described a behaviour the change does not build. The fix is justified instead by the fact that overlapping requests are a normal way to use a local HTTP app |
| PN7 | A live client failure and an empty result can look alike on screen | A failure would be read as "no data" |
| PN8 | The `HOST` constant has no call site in the run path | `--host 0.0.0.0` would expose an unauthenticated app holding the API key, and every test would still pass |

### Context

- **Environment:** one machine, one local checkout, `uvicorn app:app`, SQLite file
  at `data/sentiment.db`, no container, no hosted service, no git remote.
- **Engines:** a dummy client and a live OpenRouter client behind one
  `SentimentClient` interface. Analytics never calls either — it reads stored rows.
- **Working rhythm:** milestone-shaped, one squashed commit per finished scope,
  tagged with the scope name. No second human reviewer; stage reviews are advisory
  and review-before-land is self-review plus agent review (`C-7`).
- **Money, time and pressure:** none. No change freeze, no competing priorities, no
  external budget, no fixed deadline (`C-8`, `C-12`).

### Persona relationships and priority ranking

**There are none, and that is the finding.** No operator persona, no reviewer
persona, no stakeholder persona, no reporting relationship. The plan questions
offered exactly those splits and the answer was one persona.

Two consequences the story set must respect:

1. **There is no "someone else" to defer to.** A story whose "so that" clause would
   need a second reader — "so that reviewers can see the trend", "so that operators
   can monitor the pipeline" — is a story in this project with no audience, and must
   be cut or re-pitched to P1.
2. **P1 is both the beneficiary and the only verifier.** Where a story is phrased
   around trust rather than capability (`US1.2`, `US5.1`, `US5.2`, `US7.6`), the
   acceptance criteria are the deliverable, because there is no second pair of eyes
   to catch their absence.

## What this persona does *not* want

Recorded so the story set can be checked against it, because a persona artifact
that only lists desires produces a feature nobody asked for:

- A new front-end dependency or a chart library — the runtime cap admits none, and
  P1 did not ask for one.
- A hosted dashboard, a scheduled report, or anything that leaves the machine.
- A write endpoint, a delete endpoint, or any way to "clean up" stored text — all
  explicitly out of scope.
- An `import_id` filter on the page. P1 ruled the filter API-only, so the view
  never presents a population it cannot label.