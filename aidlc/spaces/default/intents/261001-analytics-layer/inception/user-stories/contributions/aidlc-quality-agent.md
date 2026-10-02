**Collaborator:** aidlc-quality-agent

## Contribution

Round 1 review of the drafted persona and story set **from testability only**:
whether each acceptance criterion can actually decide "done", and whether the
set supports the affirmed ordering (acceptance/API tests before the
implementation, unit tests after). 35 stories, 112 acceptance criteria.

I re-measured every claim I rely on against the working tree rather than taking
either the draft's word or the team memory's. Evidence, all reproduced in this
file so it can be re-run:

| Claim | Evidence |
|---|---|
| The API harness cannot host concurrency | `tests/conftest.py:136` — `asgi_request` is a sync wrapper around `asyncio.run(_request(...))`, so one call = one fresh event loop, single-threaded, strictly sequential |
| The lifespan re-enters on **every** request | `tests/conftest.py:102` — `async with application.router.lifespan_context(application)` inside `_request` |
| No aggregate SQL anywhere | `grep -rniE 'AVG\(|GROUP BY|json_extract' app/ tests/` → zero hits. `strftime(` occurs once, `app/repository.py:41`, for timestamp formatting, not bucketing |
| No index is created or asserted today | `grep -rn 'CREATE INDEX' app/ tests/` → zero hits. `tests/test_db.py:103` is the only `sqlite_master` query and filters `type = 'table'` |
| No concurrency test exists | `grep -rniE 'thread\|concurren\|parallel\|to_thread' tests/` → zero hits |
| No browser execution | `tests/test_page.py:1-6` states it; `app/static/app.js:10` holds an independent `const API = "/v1"` with nothing asserting it matches `app/routes.py:49` |
| `HOST` has no call site | `grep -rn HOST app/` → `app/main.py:36` only |
| Coverage is on for every run | `pyproject.toml:37` — `addopts = "-q --cov=app --cov-report=term-missing --cov-fail-under=80"`, and `filterwarnings = ["error"]` on line 39 |

The INVEST table's `Testable` row claims "Every acceptance criterion is an
observable assertion". **That does not hold.** Twenty-eight of 112 criteria
cannot be decided by a test as written; six of them cannot be decided by *any*
test because the state they describe is unreachable or the instrument is not
permitted; one is a claim about authoring history that this repository
physically destroys the evidence of.

---

### 1. Findings a test cannot decide

Split into three classes, because the fixes differ: **(A)** decidable once the
criterion names the instrument, **(B)** decidable once the fixture is
constructible — these are requirement defects, not wording defects, **(C)**
not automatable under this project's constraints at all and must be restated or
handed to Design.

#### A. Decidable, but the instrument is unstated

| ID | Problem | Decidable rewrite |
|---|---|---|
| `AC1.1.1` | "every statement is issued from the analytics read module and none is issued from the route" is phrased as a runtime observation. A `sqlite3` trace callback (verified available on this interpreter, `set_trace_callback` present) records *that* a statement ran, never *which module* issued it. | Assert the repo's existing static property — no SQL literal in the route module, no aggregate function name in it — in the same style as the already-recorded `no SQL in routes.py` Verified-Working property. Name the instrument in the criterion. |
| `AC1.1.3`, `AC8.2.3` | "every value is parameter-bound and no SQL text is built by interpolation" cannot be a runtime observation: an interpolated literal and a bound one produce the same trace line. Also `AC8.2.3` **duplicates `AC1.1.3`'s substance verbatim** while carrying a different `FR` tag. | State the AST/grep assertion. Collapse `AC8.2.3` into `AC1.1.3` and cross-reference, or keep two criteria and say what makes them different. |
| `AC2.5.2` | "none issues an `INSERT`, `UPDATE`, `DELETE` or DDL statement" is decidable by a statement-set comparison; "**and none records access bookkeeping such as a last-read timestamp**" is an open-world clause a test cannot close. | Assert the exact statement set is unchanged across N calls. The open-world tail becomes a Code Review item, not a criterion. |
| `AC8.8.2` | "no request parameter is interpolated into SQL text" — same blind spot as `AC1.1.3`. This one has a genuinely strong form available and the criterion does not use it. | Capture every statement through the trace hook and assert no request-supplied value appears in the SQL text. That is the real, load-bearing version. |
| `AC8.1.2` | "When SQL statements are counted" — `FR8.9` correctly names a `sqlite3` trace hook; the criterion dropped it. Worse: **on the current harness the count includes the lifespan**, because `conftest.py:102` re-enters `lifespan_context` on every request, so `init_db`'s DDL and `schema_meta` version write are in the trace alongside the handler's statements. A raw count is non-deterministic between the first request and later ones. | Name the hook, and scope the count to statements issued **after** the lifespan has completed. Add the scope clause or this criterion is flaky. |

#### B. Decidable only if the fixture can be built — and two cannot

**`AC2.1.3`, `AC2.1.4`, `AC2.3.3` and the mean half of `AC2.3.2` describe a store
state the schema forbids.** Verified in the working tree:

- `app/db.py:46` — `confidence REAL NOT NULL` in `CREATE_ANALYSES_TABLE`.
- `app/db.py:79-81` — `_V1_NOT_NULL_COLUMNS` includes `"confidence"`, and
  `_is_v1_shape` (`db.py:206-208`) compares each column's NOT NULL flag, so a
  store with nullable `confidence` is **not** the canonical shape.
- `db.py:226-230` — such a store is rebuilt: the nullable column is added, then
  `_rebuild_analyses` copies every row into the NOT NULL table. A NULL
  `confidence` makes that copy raise `IntegrityError`, which the `except
  BaseException` at `db.py:163` rolls back and re-raises. I confirmed SQLite
  rejects the insert outright (`NOT NULL constraint failed:
  analyses.confidence`).
- `db.py:90-92` says the nullable staging state "never survives startup".

So **no NULL-confidence row is reachable in any store the application will
start on.** That is not a wording problem in the criteria; it is a contradiction
between `FR2.8` / `AC2.1.3` / `AC2.1.4` / `AC2.3.3` and the shipped schema, in
the same family as the retired-`intensity` conflict the requirements already
caught (TD-4). Three consequences, and they are the expensive ones:

1. `FR8.2`'s `mean_confidence` and `mean_confidence_row_count` — named explicitly
   in the enumerated set — **cannot be pinned by any test**. `AC2.1.4` in
   particular is the criterion that carries the project's own "refuse, never
   substitute" convention for these two fields (`null` rather than `0.0`), and it
   is the one criterion whose fixture is impossible. The convention is real and
   the test that would prove it is unwritable.
2. `mean_confidence_row_count` exists for one reason (`FR2.8`: "so a subset mean
   can never be read as a whole-range mean"), and that reason is unreachable.
   Either the requirement retires the field, or the schema change admits a NULL
   confidence and a named fixture carries one. That is a human decision — it
   belongs in triage, not in a rewrite.
3. `AC2.3.2` asserts the per-day mean fields are **present**, not what they
   **hold**. Presence is cheap; value is where `FR8.2` lives.

**`AC5.2.2` requires an implementation SQLite cannot express.** It says the
three index declarations "live in the table DDL and not only in the migration".
SQLite's `CREATE TABLE` grammar has no index declaration — I tried both the
in-table form and the trailing form and both are rejected (`near "CREATE":
syntax error`). So `FR5.3`'s wording and `AC5.2.2` are unimplementable as
written. The substance is right and I verified the shape that works: run
`CREATE INDEX IF NOT EXISTS` **after** the migrate-or-create branch in
`init_db`, exactly as the CodeKB's TD-1 recommends, and the index survives
`RENAME` → `CREATE` → `COPY` → `DROP` (verified). Restate `AC5.2.2` as: *given
the rebuild path, when it runs, then all three indexes exist afterwards, because
they are created idempotently after the branch on every startup, not only inside
the migration.*

**`AC5.2.1`'s "exactly three indexes exist" is false as written.** The assertion
the criterion names is over `sqlite_master`, and a bare `WHERE type = 'index'`
returns **four** rows on a real store: the three `idx_analyses_*` plus
`sqlite_autoindex_schema_meta_1`, auto-created by the `schema_meta` table the
same `init_db` creates (verified). Scoped to `tbl_name = 'analyses'` it returns
exactly three — `analyses.id` is `INTEGER PRIMARY KEY AUTOINCREMENT`, the rowid
alias, so it generates no autoindex of its own (verified). Say
"**three indexes on `analyses`**, named `idx_analyses_created_at`,
`idx_analyses_import_id`, `idx_analyses_label_created_at`".

**`AC5.1.4` has nothing to satisfy.** It is about "a new table's DDL" sitting
after the migrate-or-create branch. `FR5.1` is additive and this change adds **no
table** — only indexes and a version bump. Either the criterion is about the
index statements (in which case merge it into `AC5.2.2`) or it describes an
obligation with no object.

#### C. Not automatable under this project's constraints

- **`AC7.1.2` — "compare two installs on different machines".** There is no
  second machine, no container, no CI provider and no git remote (Deployment,
  `C-7`). A test can hash the lockfile or run `pip install --dry-run` twice in
  the same interpreter, which is not the stated claim. Restate as the checkable
  property — *every distribution in the lockfile carries an exact version and a
  hash, and the documented install command resolves from it* — and record the
  two-machine comparison as a manual line in the standing verification command.
- **`AC8.7.3` (`FR8.7`, the ordering requirement) cannot be demonstrated, by
  anyone, ever, in this repository.** It asserts that acceptance tests were
  written *before* the implementation. The team memory already records the
  honest reading: two squashed commits, no surviving branch, no intra-commit
  ordering — "the history physically destroys the evidence of which test was
  written first." No test and no `git log` query can recover it. Restate as the
  **artefact** of the discipline that *is* checkable: *the analytics acceptance
  tests reach the endpoints through the ASGI route and do not import the read
  module's internals.* That is decidable and it is the property that actually
  distinguishes acceptance-first from unit-first. As a process constraint the
  ordering belongs on the implementation stage's plan, not in this set.
- **`AC6.4.5`'s third clause is not automatable at all.** "Status changes are
  announced" describes what a screen reader does. Split the criterion: the first
  two clauses are markup assertions in the established `test_page.py:54-62`
  style (a labelled control; `role="status"` + `aria-live="polite"`), and the
  announce-it-in-practice claim goes to the manual verification line. The middle
  clause, "the series is exposed rather than drawn only visually", is a
  *rendering-method* claim that no markup assertion can decide — but it has a
  decidable static form the criterion does not use: **no `canvas` element in the
  analytics markup**, consistent with `AC6.4.4`'s native-elements rule.
- **`AC8.6.1`'s "where they are semantic".** The other two thirds of the
  criterion (`Single responsibility:` line, full annotations) are trivially
  automatable. "Semantic" has no decidable boundary — it is the judgement team
  memory records in prose. Restate as the mechanical rule the test applies:
  *every public module-level constant in the new modules carries a `#:` line.*
  (Scope it to the new modules — `app/service.py` carries none today, so a
  whole-repo rule is red on arrival.)

---

### 2. Six criteria are statements about tests, not about the system

`AC1.2.2`, `AC5.2.3`, `AC6.1.2`, `AC6.2.3`, `AC8.7.1`, `AC8.7.3` are all of the
form "Given the test …, When it runs, Then it …". A criterion in that shape
cannot fail for a system reason. Each duplicates a behavioural criterion that
already carries the real obligation (`AC1.2.1`, `AC5.2.1`, `AC8.7.4`), so the
set pays for meta-criteria that add no signal. Collapse each into the
behavioural criterion it shadows, or restate as "the suite contains a test that …"
and accept that the only automatable form is "the suite is green", which is
vacuous.

Two of them also lose the substance in the collapse:

- **`AC6.1.2` and `AC6.2.3` name no hook.** "its hooks are added to that same
  constant" passes for any hook name, any number of hooks, or none.
  `tests/test_page.py:17-32` pins 14 named `data-testid`s; the analytics view's
  equivalents are named **nowhere** in the set. `FR8.6` cannot be demonstrated
  by a criterion that names nothing. This is the single cheapest fix in the
  whole review: list the hooks, exactly as `REQUIRED_TEST_IDS` does.
- **`AC1.2.2`'s failure clause is a hypothetical.** "if the thread-affinity
  decision is reverted, it fails" is conditional on a future act nobody performs,
  so the criterion cannot fail. `FR8.4` states the real obligation — *a test
  reproduces R-01 against the `FR7.7` harness and fails if the defect returns.*
  The automatable form is a **revert check**: the implementer reverts the fix,
  observes the test go red, and records it as evidence. That is an obligation on
  the implementer, not a clause inside a criterion. See §7.

---

### 3. `FR8.2`'s enumerated aggregates — verified ledger

The `Testable` row claims the list is "carried inside `AC2.1.1`, `AC2.3.*` and
`AC3.1.*`". Checked item by item:

| # | `FR8.2` aggregate | Where it is pinned | Verdict |
|---|---|---|---|
| 1 | `total` | `AC2.1.1` | ✅ |
| 2 | every per-label `count` | `AC2.1.1` | ✅ |
| 3 | every `shares` value **including the zero-denominator `null`** | `AC2.1.2` (unit + rounding); `AC2.3.1` (null, for a **series day**) | ⚠️ **The summary-level zero-denominator null is pinned by nothing** — see below |
| 4 | `mean_confidence`, `mean_confidence_row_count` | `AC2.1.3`, `AC2.1.4`, `AC2.3.3` | ❌ **Fixture impossible** (§1B) |
| 5 | every series entry's `date`, `total`, `counts`, `shares` | `AC2.3.1`, `AC2.3.2` | ✅ |
| 6 | both mean fields per series entry | `AC2.3.2` (presence only), `AC2.3.3` | ❌ presence, not value; and see #4 |
| 7 | zero-fill of a day with no rows | `AC2.3.1` | ✅ strongest criterion in the set — names total 0, counts 0, shares null, both means null |
| 8 | resolved bounds, unbounded and single-bound | `AC2.2.3`, `AC2.2.4`, with `AC2.3.1` | ✅ `AC2.3.1`'s five entries over rows on two days is what pins the leading/trailing zero-fill days, so the bound is inferable even though the response carries no bounds field |
| 9 | alphabetical tie-break | `AC3.1.2` | ✅ |
| 10 | per-list application of `limit` | `AC3.1.1`, `AC3.1.3` | ✅ `AC3.1.3`'s "exactly one entry **each**" is what distinguishes per-list from total |
| 11 | refusal shapes for **every** 422 in `FR2.11` | `AC2.4.3` (malformed `from`/`to`/`import_id`), `AC2.4.4` (inverted), `AC3.1.3` (`limit`) | ✅ all four kinds, none missed — with the caveat in §6 |

**The one that is missing, and it is the expensive one.** `FR8.2` names "every
`shares` value **including the zero-denominator `null`**". `AC2.3.1` pins that
null for a *series day*. Nothing pins it for the **summary's top level**.
`AC2.4.1` — a range matching no rows — asserts only `total` 0 and an empty
series; `AC2.4.2` says an unmatched `import_id` is "identical to an empty range"
and inherits the gap. So this response would pass **every criterion in the set**:

```json
{"total": 0, "counts": {"positive": 0, "negative": 0, "neutral": 0},
 "shares": {"positive": 0.0, "negative": 0.0, "neutral": 0.0}, ...}
```

A zero denominator presented as a fabricated `0.0` — the exact failure the
persona's **G4** ("a number shown on screen came from a real, complete
calculation") and **P2** exist to prevent, and the exact thing the "refuse,
never substitute" convention forbids. The same applies to the top-level
`counts` key set: `AC2.1.1` implies keys for labels that have rows; `AC2.3.1`
pins three keys for a series day; **the top-level `counts` for an empty range is
unpinned**, so `{}` and three zeros both pass. Add to `AC2.4.1`: given an empty
range, then `counts` carries all three label keys at 0 and every `shares` value
is `null` — never `0.0`, never `0`.

Second gap, same family: nothing states that all three label keys are **always**
present, so a summary for a store holding only positive rows could omit
`negative` and `neutral`. `AC2.3.1` pins it per day; the top level needs it.

---

### 4. `FR8` ownership — the fold did not land for five of nine

The header's claim that the nine test requirements are "carried as acceptance
criteria inside the stories they protect" holds for four:

- **`FR8.1`** ✅ tagged on `AC1.1.5`, `AC2.4.1`, `AC3.1.5`, `AC4.1.*`, and each
  of the four situations it names (empty range, populated range, `import_id`
  filter, term extraction) does have a criterion.
- **`FR8.3`** ✅ substance lands in `AC5.2.1` (the exact three-name set). The
  *tag* sits on `AC5.2.3`, which is the meta-criterion (§2) — retag it.
- **`FR8.5`** ✅ `AC8.7.1` + `AC8.7.2` match the affirmed posture exactly.
- **`FR8.8`** ✅ `AC8.7.4`, and it is already enforced twice over by `addopts`.

The five that did not:

- **`FR8.2`** — partial. The mean fields are unpinnable and the summary-level
  zero-denominator `shares` null has no criterion at all (§3).
- **`FR8.4`** — lands only as `AC1.2.2`, a meta-criterion whose failure clause
  is a hypothetical (§2, §7).
- **`FR8.6`** — lands, but names no hook, so it cannot fail (§2).
- **`FR8.7`** — lands as `AC8.7.3`, which no test and no `git` query can decide
  in this repository (§1C).
- **`FR8.9`** — lands degraded. `AC8.1.1` drops the threshold to "within the
  stated budget" (the budget is 200 ms in `NFR1`; a criterion that does not
  state its threshold is not a criterion), and neither criterion names the trace
  hook or scopes the count past the per-request lifespan (`AC8.1.2`, §1A).

Two `FR8` criteria are worth noting as correctly folded: **`FR8.9`'s
day-independence claim** is genuinely load-bearing — a query-per-day
implementation shows 5 statements on a 5-day range and 500 on a 500-day range, so
`AC8.1.2` catches it. That is the criterion doing exactly what `FR8.9` was
written to do. And **`FR8.1`'s offline-guard clause** is decidable today:
`offline_guard` replaces `socket.socket.connect` with a raiser, so
`AC1.1.5` fails loudly if either endpoint reaches the network.

---

### 5. Sad paths

The team's own learning is that a story pins its error and edge behaviour.
`US6.2` and `US6.3` are thin, as flagged — and thinner than "no sad path",
because the specific behaviours they omit are the likely defects:

- **`US6.2`** (three criteria, all "when it loads, then it renders"): no
  empty-store case, no case where one endpoint answers and the other fails, and
  **nothing about `total = 0` with every share `null`**. Rendering a `null` share
  as `0`, or as `NaN`, is the most likely UI defect in this feature — the API
  pins the null and the view pins nothing, so a divergence between the two
  halves passes the whole suite. This is `FR6.7`'s exact concern and it is
  absent.
- **`US6.3`** (three criteria, all happy-path): no inverted range selected in
  the control. `FR2.11` makes that a 422; `FR6.7` requires the view not to render
  a 422 as empty; **no criterion joins them.** Also no cleared control, no range
  narrowed to a day with no rows, no out-of-range value.
- **`US4.1` / `US4.2`** — the pair is all "when I inspect / compare / read". The
  one behaviour that matters is missing from both: **text whose tokens are
  entirely stopwords or entirely under three characters**. That is the case that
  makes both term lists empty, and it is where the `[]`-versus-`null` bug lives
  downstream of `FR3.7`. `AC4.1.1`–`AC4.1.4` cover the token floor and the
  boundaries and stop at "one token survives".
- **`US6.1`** — structural only; nothing says what the third entry does when the
  analytics endpoints are unreachable.
- **`US6.4`** — the one `US6` story that *is* a sad path, and it has no criterion
  for the fetch itself rejecting, which is the more likely local failure mode
  (see §6 on why none of it is observable anyway).
- **`US7.3`** — `AC7.2.2` covers the verification script's exit code, but nothing
  covers the **scanner's red state**: a scanner that reports nothing on everything
  satisfies `AC7.3.1` ("it is part of verification"). The red case is the only
  one that proves the scanner works.
- **`US7.7`** — nothing pins that the replaced harness preserves **per-test
  isolation** (the `tmp_settings` / `tmp_path` database, no test reading the real
  store). Replacing the harness is exactly where shared state creeps back in, and
  `AC8.7.2` covers guard-armed globally but not isolation. Independence is
  non-negotiable in the affirmed posture; nothing enforces it under the new
  harness.
- **`US1.1`** — five criteria, none of which is a sad path for the read module:
  nothing for the connection being closed mid-read, or for the table being absent
  on a store that never went through `init_db`.

---

### 6. Ordering discipline

**The set supports it, in one direction and with one exception.** The criteria
are written as observable behaviour with named refusal shapes, which is exactly
what a test can be written from before any code exists — `AC2.4.1`–`AC2.4.5` and
`AC3.1.3` are model acceptance-first criteria, and the thin slice
`US1.1 → US2.1 → US6.2` can have its tests written first. The dependency graph is
honest about the two legitimate test-after cases: `US8.1` (the budget, which needs
an endpoint to measure) and `US7.7` (the harness, which needs to exist before
concurrency can be asserted). Worth saying so explicitly in the `Testable` row,
because a reader of "acceptance tests first" would expect `US8.1`'s test first.
`AC8.1.2`'s statement-count assertion is the one that *could* have been written
first as a red test — and would have been valuable, since no test in the
repository exercises `GROUP BY` or any aggregate today.

**The break is not ordering, it is observability, and the draft does not name
it.** `US6.2`, `US6.3` and `US6.4` are not "only testable once the whole feature
exists" — they are **not testable at all** under the affirmed posture. Their
subject is client-side behaviour in `app/static/app.js`, and no browser
execution is permitted (the two-runtime-dependency cap; `test_page.py:1-6`;
TD-11: "a wrong fetch URL, a broken `textContent` write, a date-filter handler
that never fires — would pass the whole suite"). So these six criteria cannot be
decided:

`AC6.2.2` (each section populated from its own response), `AC6.3.1` (first load
issues both endpoints with no bounds), `AC6.3.2` (refetch applies the same bounds
to all three readouts), `AC6.4.1` (failure rendered inline), `AC6.4.2` (422 vs
500 vs empty, visibly different), `AC6.4.3` (no request other than to its own
two endpoints).

All six need the same two-part treatment, and it is available at zero
dependency cost:

- **Static, and cheap.** `app.js` is a served asset; `test_page.py:71-77` already
  fetches it. Assert the served script names `/v2/analytics/summary` and
  `/v2/analytics/terms` as literals and does **not** build them from the `/v1`
  constant. This matters more than it looks: the frontend holds an independent
  second copy of the version prefix (`app/static/app.js:10` vs
  `app/routes.py:49`) and nothing in the repository asserts the two copies match.
  A view that fetched `/v1/analytics/summary` would 404 and render as "no data" —
  which is `FR6.5` and `FR6.7` failing silently, with the suite green. **There
  is no criterion anywhere in the set that touches this**, and it is the highest
  value-per-word addition available.
- **Manual, and recorded.** Boot `uvicorn app:app` on loopback per the affirmed
  verification command, open the view, narrow the range, force a 422 and a 500,
  and read the rendered result. That is where the behaviour genuinely gets
  demonstrated, and the standing command already exists for exactly this.

**The constraint stories are sequenced wrongly.** `AC8.7.1` (every new test
asserts out of real SQLite), `AC8.7.3` (ordering) and `AC8.7.4` (the floor)
constrain **every test in the set**, yet `US8.7` is sequenced after seven other
stories. A constraint that binds from the first test written does not belong in a
story that comes after the work. Move `AC8.7.1` and `AC8.7.3` to a
cross-cutting "definition of done for every criterion in this document" block at
the top of `stories.md`, or fold them into the `Testable` INVEST row where they
apply to all 112 criteria. `AC8.7.4` is not a story at all — `addopts` already
enforces it on every run.

**`US7.7` is correctly placed and is the ordering keystone** — but `AC7.7.1`'s
"they genuinely overlap rather than running sequentially" is unmeasured. See §7.

---

### 7. The concurrency pair — `US7.7` → `US1.2`

The ordering is right and the set understands the constraint: today's harness
cannot host the test, so the harness lands first. `AC1.2.1`'s observable is the
right one. Three gaps stop the pair from demonstrating the fix.

**1. Overlap is not the same as cross-thread, and R-01 is a cross-thread defect.**
`get_connection` creates a `sqlite3.Connection` on one anyio worker thread and
closes it on another; `sqlite3`'s default `check_same_thread` is what raises. But
two overlapping sync handlers dispatched through a single ASGI app **may both
run on one thread**, in which case the defect never fires and `AC1.2.1`'s green
is vacuous — a test that passes because it did not provoke anything. So
`AC7.7.1` must require the overlap to be **provably cross-thread**: each request
records `threading.get_ident()` and the test asserts the set has at least two
distinct idents. That is decidable, cheap, and it is the difference between a
demonstration and a coincidence. "Genuinely overlap" as written is satisfied by a
`time.sleep` and proves nothing about threads.

**2. `AC1.2.2`'s failure clause is not a criterion.** Restated in §2. The real
obligation is a **revert check**: revert the thread-affinity decision, watch the
test go red, record it. Make that an explicit step on `US1.2`, not a conditional
clause inside a criterion.

**3. No criterion pins the decision itself, only that it is documented.**
`AC1.2.3` requires the docstring to state the chosen thread-affinity decision.
`check_same_thread=False` with a lock and per-thread connections via
`threading.local` both satisfy every criterion in `US1.2`, and they behave
differently under the analytics page's polling pattern — which is the access
pattern that exposed R-01. That is acceptable for a user story (the mechanism is
Design's), but it means the only evidence that the *right* decision was made is
the revert check in (2). That is why (2) is load-bearing rather than
belt-and-braces.

The one thing to protect: do not let the harness replacement quietly shrink the
scope. `AC7.7.3` says the existing tests still pass, which is correct, but
`AC7.7.2`'s guard-armed check must extend to **a socket call made from a worker
thread**, since the new harness is the one shape where that is reachable.

---

### 8. Belongs to a later stage, not to this one

Recording these so they are not written into the story set as if they were
criteria:

- **The literal storage-failure machine code.** `FR2.12` already defers it to
  Contract Design, and `AC2.4.5`'s only testable property is distinctness from
  every validation code. Leave it there. Note that `sqlite3.Error` has **no**
  registered exception handler today (`app/main.py:94-98` registers five
  app-specific handlers, none for `sqlite3`), so a storage error currently
  escapes as a bare FastAPI 500 with no envelope — that is Code Generation's
  work, not a story.
- **The inverted-range refusal shape.** `AC2.4.4` and `AC8.5.2` together force
  the inverted range to reuse `VALIDATION_FAILED` (the code set gains exactly one
  member, and it is the storage-failure one) and to encode both field names in
  freeform message prose — because `handle_validation_error`
  (`app/routes.py:342-355`) builds `f"{field}: {msg}"` from `errors[0]` **only**,
  and an inverted range is a cross-field check FastAPI's per-field validation
  never raises. The envelope is exactly `{code, message}`; there is no `field`
  key. So `AC2.4.3`'s and `AC2.4.4`'s "naming `field == \"query.from\"`" reads
  like a structured assertion the shape forbids, and the substring convention is
  unspecified — the suite's established form is
  `assert "extra" in response.body["message"]`. **Fix the message convention at
  Contract Design, then state the exact asserted substring in the criteria.**
  This is a real tension between two criteria in the same set.
- **Which secret scanner and which audit tool.** `FR7.3`'s open question is
  genuinely open. `AC7.3.3` cannot be written as a test until it is answered,
  and its fixture — a deliberately vulnerable pinned version — is a test-design
  decision nobody has made.
- **Which licence.** `AC7.4.1` needs a name before it can be asserted; that is a
  project decision, already open in the requirements.
- **The specific stopword list.** `FR4.4` bounds it and Design fixes it, as the
  requirements say. `AC4.1.2` is correctly written to survive that.
- **The `mean_confidence` / NULL-confidence contradiction (§1B).** This is a
  requirement-level decision with three possible answers — retire the field,
  admit a NULL confidence in the schema, or drop the subset-mean guarantee —
  and it is the same shape as the retired-`intensity` conflict (TD-4) that
  Requirements Analysis already caught once. It should go to triage as a
  human judgement call, not be resolved by rewording a criterion.
- **The 200 ms measurement environment.** Whether `NFR1`'s budget is measured
  inside the standing `pytest` run (where `addopts` forces `--cov=app`, so the
  timing is coverage-instrumented) or in a marked performance test outside the
  floor gate is a Build-and-Test / pipeline decision. **But the criterion must
  state the threshold as a literal, state the tolerance and the environment, and
  state which of the two it is** — a wall-clock assertion in the ordinary suite is
  a flaky gate, and "within the stated budget" with no stated budget is not a
  criterion at all.

### Ready-to-integrate criterion text

Offered so the lead can lift rather than reconstruct:

- **Replace `AC2.4.1`:** *Given a range matching no rows, when I request the
  summary, then I get a **200** with `total` 0, a `counts` object carrying all
  three label keys at 0, a `shares` object whose every value is `null` — never
  `0.0`, never `0` — an empty series, and both mean fields `null`. Never a 404.*
- **Add to `AC2.1.2`:** *Given `total` 0, when I read `shares`, then every value
  is `null` and the three label keys are all present.*
- **Add to `AC6.2`:** *Given a response in which `total` is 0 or a share is
  `null`, when the view renders the breakdown, then the cell reads as "no data"
  and never as `0` or `NaN`.*
- **Add to `US6.4`:** *Given the view's script as a served asset, when the served
  markup is inspected, then `/v2/analytics/summary` and `/v2/analytics/terms`
  appear as literals and are not built from the `/v1` prefix constant, and no
  third-party host appears anywhere in it.*
- **Replace `AC5.2.1`:** *Given a migrating store, when the migration completes,
  then exactly three indexes exist **on `analyses`** — `idx_analyses_created_at`,
  `idx_analyses_import_id`, `idx_analyses_label_created_at` — asserted by name
  from `sqlite_master` filtered to `tbl_name = 'analyses'`, so an autoindex on
  another table cannot be counted and an index silently dropped by a future
  rebuild fails the test.*
- **Replace `AC5.2.2`:** *Given the table-rebuild path (`RENAME` → `CREATE TABLE`
  → `COPY` → `DROP TABLE`), when it runs, then all three indexes exist
  afterwards, because they are created idempotently after the
  migrate-or-create branch on every startup rather than only inside the
  migration.*
- **Replace `AC7.7.1`:** *Given the replaced harness, when a test issues two
  overlapping requests, then both record their `threading.get_ident()`, the set of
  recorded idents has at least two members, and the overlap is observed in time as
  well as in thread — a same-thread pass is not concurrency.*
- **Add to `US1.2`:** *Given the thread-affinity decision, when it is temporarily
  reverted, then the concurrency test fails with `sqlite3.ProgrammingError`; the
  revert check is performed and its result recorded before this story is done.*
- **Add to `US7.7`:** *Given the new harness, when the suite runs, then per-test
  isolation holds — no test reads `config.local.toml` or `data/sentiment.db`, and
  every test's database lives under its own `tmp_path`.*
- **Add to `US4.1`:** *Given text whose tokens are all stopwords or all shorter
  than three characters, when terms are extracted, then the result is empty — not
  a fabricated entry and not an error.*
- **Replace `AC8.1.1`:** *Given 10,000 stored analyses in the shared fixture,
  when either endpoint is exercised, then it answers in under **200 ms**
  (`NFR1`'s figure, stated literally) on the machine named in the verification
  notes, measured with coverage disabled — and this assertion runs in a marked
  performance test outside the 80 % floor gate, not in the ordinary suite run.*
- **Replace `AC8.6.1`:** *…and every public module-level constant in the new
  modules carries a `#:` prose line.* (drops "where they are semantic")
- **Replace `AC6.4.5`:** *Given the analytics markup, when it is inspected, then
  the range control has an associated label, the series is expressed in native
  elements with no `canvas` anywhere in it, and the status region carries
  `role="status"` and `aria-live="polite"`. What a screen reader actually
  announces is verified by the standing end-to-end command, not by the suite.*

## Positions

- **OBJECT: the INVEST `Testable` row's claim that "every acceptance criterion is
  an observable assertion"** — 28 of 112 criteria cannot be decided by a test as
  written, and six cannot be decided by any test under this project's
  constraints; the mean-confidence fixture and the summary-level zero-denominator
  `shares` null are the two that would let a real defect through.
- **OBJECT: "`FR8.2`'s hand-pinned aggregate list is carried inside `AC2.1.1`,
  `AC2.3.*` and `AC3.1.*`"** — eleven of the enumerated aggregates are carried;
  `mean_confidence` and `mean_confidence_row_count` at both levels are not
  pinnable because `confidence` is `NOT NULL` in the shipped schema, and the
  **summary-level zero-denominator `shares` `null` is named by `FR8.2` and pinned
  by no criterion anywhere in the set**.
- **OBJECT: "the nine test requirements are carried as acceptance criteria inside
  the stories they protect"** — four land solidly (`FR8.1`, `FR8.3`, `FR8.5`,
  `FR8.8`); five do not (`FR8.2` partial, `FR8.4` meta-only, `FR8.6` names no
  hook, `FR8.7` not demonstrable in this repository, `FR8.9` dropped the
  threshold and the instrument).
- **OBJECT: `AC5.2.2`'s "their declarations live in the table DDL"** —
  SQLite's `CREATE TABLE` grammar has no index declaration, so the criterion is
  unimplementable as written; the verified shape is `CREATE INDEX IF NOT EXISTS`
  after the migrate-or-create branch.
- **OBJECT: `AC5.2.1`'s "exactly three indexes exist"** — a bare
  `WHERE type = 'index'` query over `sqlite_master` returns four rows on a real
  store, because `init_db` also creates `schema_meta` and its `TEXT PRIMARY KEY`
  auto-creates `sqlite_autoindex_schema_meta_1`.
- **OBJECT: `AC5.1.4`** — it is about a new table's DDL, and this change adds no
  table; either it describes an obligation with no object or it belongs folded
  into `AC5.2.2`.
- **OBJECT: `AC8.1.1`'s "within the stated budget"** — the criterion states no
  threshold, no tolerance and no environment, and `addopts` forces `--cov=app` on
  every run, so a wall-clock assertion here measures coverage-instrumented
  execution inside a gate that already owns the 80 % floor.
- **OBJECT: `AC8.6.1`'s "where they are semantic"** — no decidable boundary
  exists; the rest of that criterion is trivially automatable, which is what makes
  the qualifier look safer than it is.
- **OBJECT: `AC6.4.5`'s assistive-technology clause** — the first two clauses are
  markup-assertable in the established `test_page.py` style and the middle one
  has a decidable static form (no `canvas`), but "status changes are announced"
  is not automatable at all under the dependency cap and belongs in the manual
  verification line.
- **OBJECT: the `US6.2` / `US6.3` / `US6.4` criteria as unobservable rather than
  merely thin** — six criteria describe client-side behaviour in a script nothing
  executes, so they cannot be decided regardless of how the stories are sliced;
  the `/v2` prefix second-copy check is the cheap static assertion that covers the
  most likely failure and is absent from the set.
- **OBJECT: `AC7.1.2`'s "two installs on different machines"** — no second
  machine, container, CI provider or remote exists in this deployment, so the
  criterion cannot be demonstrated; restate it as the lockfile's checkable
  property.
- **OBJECT: `AC8.7.3` (`FR8.7`) as an acceptance criterion** — it asserts
  authoring order, and the team memory records that this repository's squashed
  history physically destroys that evidence; restate it as the checkable artefact
  of the discipline (analytics tests reach the route and never import the read
  module's internals).
- **OBJECT: the sequencing of `US8.7`** — `AC8.7.1` and `AC8.7.3` constrain every
  test in the set but sit in a story scheduled after seven others; they belong in
  a cross-cutting definition-of-done block. `AC8.7.4` is not a story — `addopts`
  already enforces it.
- **OBJECT: `AC1.2.2` and `AC5.2.3` as meta-criteria** — each is a statement
  about a test that duplicates a behavioural criterion already carrying the real
  obligation (`AC1.2.1`, `AC5.2.1`); `AC1.2.2`'s "if the decision is reverted, it
  fails" is conditional on a future act nobody performs, so it cannot fail.
- **OBJECT: `AC2.4.3` / `AC2.4.4` as written against a frozen envelope** — the
  envelope is exactly `{code, message}`, `handle_validation_error` reports
  `errors[0]` only, and `AC8.5.2` freezes the shape, so both field names must
  live in freeform prose; the asserted substring convention is unspecified and
  belongs to Contract Design before these criteria can be written testably.
- **OBJECT: `AC8.1.2` without a scope clause** — the current harness re-enters
  the lifespan on every request (`tests/conftest.py:102`), so an unscoped trace
  count includes `init_db`'s DDL and schema-version write and is non-deterministic
  between the first request and later ones.
- **AGREE: the one-persona framing and its two stated consequences** — the
  artifact is right that a story whose "so that" clause needs a second reader has
  no audience, and right that acceptance criteria are the deliverable wherever a
  story is pitched around trust (`US1.2`, `US5.1`, `US5.2`, `US7.6`) because
  there is no second pair of eyes. That is exactly why the unwritable criteria
  above are expensive rather than cosmetic.
- **AGREE: the thin slice `US1.1 → US2.1 → US6.2` as the affirmed slicing
  decision, and the dependency order as a whole** — the graph is honest, it names
  its two legitimate test-after cases (`US8.1`, `US7.7`), and putting the harness
  before the R-01 fix is the only ordering under which the fix is demonstrable.
- **AGREE: `US2.4` as the model story for this set** — it is the one place where
  empty, refused and failed answers are each pinned distinctly, with the status
  code, the named field and the "computes nothing" clause together. `US2.3`'s
  `AC2.3.1` is the model criterion: it names every field of the zero-fill, not
  just that a zero-fill happened. More of `US2` and `US3` should read like those
  two.
- **AGREE: keeping `FR8` out of the story groups** — the mismatch is called out
  in the header rather than left for a reader to assume away, which is the right
  handling even though the fold itself is incomplete.