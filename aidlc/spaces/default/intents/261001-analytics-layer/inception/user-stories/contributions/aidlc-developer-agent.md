**Collaborator:** aidlc-developer-agent

## Contribution

Lens: **implementability and story sizing only.** I read `personas.md`,
`stories.md`, `user-stories-questions.md`, `requirements.md`, the application
under `./app`, the suite under `./tests`, and the CodeKB artifacts, and I
verified the load-bearing claims by running the shipped code and the pinned
tooling (Python 3.14.7, `ruff` 0.16.9, `sqlite3`). I did not read either
sibling contribution.

**Verdict up front.** The story set is honest about its obligations and mostly
right about its edges. But it has one broken slice, two criteria that cannot be
built as written, two that are already satisfied, one wrong count, seven missing
dependency edges, one not-real edge, and nine platform stories that are really
five. Details below, separated into *cannot be built*, *sizing*, *edges*,
*thin slice*, and *wrong altitude*.

---

## A. Cannot be built as written

### A1 — `AC5.2.2` (and `FR5.3`) specify an index declaration SQLite cannot hold

`AC5.2.2` says the three index declarations "live in the table DDL and not only
in the migration". **SQLite has no in-table-DDL index declaration** — unlike
MySQL, `CREATE TABLE` takes no secondary-index clause. `CREATE_ANALYSES_TABLE`
(`app/db.py:40-53`) is a single `CREATE TABLE IF NOT EXISTS analyses (...)`
string; there is nowhere in it to put an index.

Appending the index DDL to that constant does not work either, and I verified
both failure modes:

- `sqlite3.Cursor.execute()` **refuses a multi-statement string**:
  `ProgrammingError: You can only execute one statement at a time.` So
  `CREATE TABLE ...; CREATE INDEX ...; CREATE INDEX ...;` in one constant
  raises at `app/db.py:160` and `app/db.py:241`.
- `executescript()` **silently commits any open transaction**. Inside
  `init_db`'s `BEGIN` (`app/db.py:155`), a single `executescript` left
  `in_transaction == False`, and a following `rollback()` did **not** undo the
  row inserted before it. That destroys exactly what `AC5.1.5` ("the version bump
  landed in the same transaction as the migration") and `AC5.1.3` ("fails loudly
  and rolls back") assert.

**The buildable form** is a second module constant, `CREATE_ANALYSES_INDEXES`,
executed with a second `connection.execute(...)` immediately after every
`CREATE TABLE analyses` — at **both** call sites, `app/db.py:160` (fresh create)
and `app/db.py:241` (`_rebuild_analyses`). `AC5.2.2` should say that, and
`AC5.1.4` should extend to the index constant's placement, not only the table's.

Note this cuts against the persona artifact: `personas.md` P3 states the symptom
correctly ("the table DDL declares no index, so any index is destroyed on a
migrating store") and the cure wrongly. The rebuild path is already covered by
`tests/test_db.py::test_migration_rebuilds_a_pre_v1_store_and_keeps_every_row`,
which is exactly the test that would go red if only `init_db` gained the index.

### A2 — `AC8.3.2` asks a lint rule to do something `ruff TID251` cannot do

`AC8.3.2`: "Given the boundary rules, when a write is attempted from the
analytics layer, then the lint fails rather than the write reaching the store."

`TID251` `banned-api` is an **import** rule. Verified against the pinned `ruff`
(`pyproject.toml:22` floors it at `>=0.6`; the venv holds 0.16.9), in a scratch
project:

| banned path | site under test | result |
|---|---|---|
| `sqlite3` | `import sqlite3` | `bad2.py:1:8: TID251 'sqlite3' is banned` |
| `sqlite3.Connection.execute` | `conn.execute("DELETE FROM analyses")` | **no diagnostic** |
| `sqlite3.Connection.execute` + `sqlite3.Cursor.execute` | `cur.execute("DELETE FROM analyses")` | **no diagnostic** |

So a write attempted from the analytics layer cannot be caught by lint. The two
mechanisms that *would* work both collide with a criterion already in the set:

- a **read-only connection** (`sqlite3.connect("file:...?mode=ro", uri=True)` or
  `PRAGMA query_only = ON`) contradicts `AC1.1.2` / `FR1.3` — the read module
  must use "the connection the HTTP layer already owns", which for
  `POST /v1/analyze` is the same writable per-request connection
  (`app/routes.py:92-98`);
- a **source-level assertion** already exists as `AC2.5.2`, and that is a
  *test*, not a lint.

This is a one-word fix, and it is the fix I recommend: change `AC8.3.2` from
"the lint fails" to "**a test fails**", and let `US7.5` own import boundaries
only (which `TID251` does enforce — see E5 below). Introducing an
analytics-specific read-only connection is the alternative, and that is a
**design choice** with a real cost, because it splits connection ownership that
`FR1.3` and the affirmed team rule currently place at the HTTP edge.

### A3 — `AC2.3.1` and `AC8.1.2` are **not** in conflict — but the set is one sentence from making them so

Answering the question directly: they can both hold, and easily. One
`GROUP BY date(created_at)` query carrying `count(*)`, per-label counts,
`sum(confidence)` and `count(confidence)`, plus one `MIN(created_at)` for the
unbounded default span (`FR2.6`) — **two statements, constant in day count**,
with the gaps materialised in Python from the already-resolved day list.
`set_trace_callback` exists on the pinned interpreter, so `FR8.9`'s statement
counter is buildable.

**But** neither criterion says *where* the zero-fill happens. A per-day query
loop satisfies `AC2.3.1` verbatim and breaks `AC8.1.2`, and that is the reading a
developer reaches for first. Fix `AC2.3.1` by naming the mechanism: *"the series
rows come from one grouped query over the range; the missing days are filled in
Python from the resolved day range."*

### A4 — `AC7.3.2`'s "four known fake-key fixtures" is the wrong number

There are **six** distinct fake-key literals in `tests/*.py`:

```
sk-or-v1-0123456789abcdef0123456789abcdef   tests/test_config.py:23
sk-or-v1-from-config                        tests/test_auth_routes.py:26, tests/test_service.py:181,277
sk-or-v1-live-key                           tests/test_live_client.py:27
sk-or-v1-not-used-here                      tests/test_routes.py:268
sk-or-v1-session                            tests/test_service.py:95
sk-or-v1-session-key                        tests/test_auth_routes.py:25, tests/test_session_auth.py:26
```

An allowlist written to `AC7.3.2` leaves two unallowlisted, so the first scan
run reports exactly the known-fake noise the criterion exists to prevent — and
`AC7.3.1` ("part of verification rather than a separate manual step") then fails
on the first run. Change "four" to "every fake-key literal in `tests/`", or
better: define the allowlist by prefix/pattern (`sk-or-v1-*` under `tests/`) so
it does not have to be counted at all.

### A5 — `AC8.7.3` is unverifiable in this repository

"acceptance- and API-level tests were written against the requirement **before**
the implementation" is a process ordering rule, and `personas.md` records the
working rhythm as "one squashed commit per finished scope". A squashed commit
carries no ordering evidence, so no suite assertion and no git query can check
this after the fact. It is `FR8.7` restated as an AC. It belongs in the team
Testing Contract (`memory/team.md` `## Testing Posture`) and in Code
Generation's ordering input, not in a story's acceptance criteria.

### A6 — `US7.8` is already true; there is nothing to build

`pyproject.toml:10` `requires-python = ">=3.11"`; `pyproject.toml:51`
`target-version = "py311"`. They already match, and `ruff check app` exits
`All checks passed!`. `AC7.8.1` and `AC7.8.2` are both satisfied by the shipped
file. Either drop the story or restate it as an invariant the verification script
asserts — do not carry it as nine platform obligations including one that needs
zero lines.

### A7 — `US6.2`'s `AC6.2.1` cannot be met by `US2.1`, so **the affirmed thin slice is not demonstrable**

This is the headline finding and it answers the thin-slice question.

`AC6.2.1` requires the view to render "**the per-day time series**". The series
is produced by **`US2.3`** (`AC2.3.1`, continuous zero-filled per-day entries),
and `US2.3` depends on **`US2.2`** (date-range resolution). `US6.2` declares
`Depends on: US2.1, US3.1`. So on the declared graph, at the moment `US6.2`
becomes available, `/v2/analytics/summary` returns `total` / `counts` / `shares`
/ `mean_confidence` and **no `series` key** — the first section of the three
readouts has nothing to render.

`US1.1 → US2.1 → US6.2` is therefore *not* "the smallest set that demonstrates
the whole way through"; it is the smallest set that demonstrates route → SQL →
**two** of three readouts, with the slice's headline feature missing. The fix is
one line in two places: add `US2.2` to `US6.2`'s declared dependencies (which
brings `US2.3` with it) and draw `US2.3` inside the slice box in the dependency
map at `stories.md:39-48`.

Two neighbours have the same defect:

- `US6.3` declares `Depends on: US6.2` only, but `AC6.3.1` ("no range chosen →
  requests both endpoints with no bounds and shows all stored history") needs
  `AC2.2.4`, i.e. `US2.2`'s unbounded default span.
- `US6.4` declares `Depends on: US6.2` only, but `AC6.4.2` ("a 422 and a 500
  are visibly different … from a genuine empty result") needs `US2.4`'s refusal
  shapes.

### A8 — Two `US7` criteria are manual-only and are written as suite assertions

`US7.2`'s `AC7.2.3` already accepts that this project has "no git remote" and so
cannot run provider CI — good, that is honest. But `AC7.1.2` ("compare two
installs on different machines") and `AC7.3.3` ("a known-vulnerable resolved
version is reported") are **not runnable inside this suite**:
`tests/conftest.py:139-156` patches `socket.socket.connect` for the whole
session, so no install or resolution can happen under the guard. Both are
buildable, but only as a documented manual procedure. Label them the way
`AC7.2.3` already is, so the verification script does not grow a step that fails
by construction.

---

## B. Sizing

### B1 — `US6.2` is the largest risk, and the proposed split is the wrong one

The lead's flag is right. `app/static/app.js` is 201 lines and `index.html` 193
today; `AC6.4.4` forbids a chart library and a new front-end dependency, so the
series is hand-rolled DOM; `AC6.2.3` adds page contract tests on top. That is
two or three stories' worth of work, and it is the tail of the thin slice.

But the INVEST note's remedy — "splitting it per section" — would break the
slice's meaning, because each section needs the other two fetched to know it is
rendering a complete picture. The split I would make:

- **`US6.2a`** shell wiring (absorb `US6.1`) + `US2` breakdown + both `US3`
  term lists, range-free first render. **This is the demonstrable slice**, and it
  needs only `US2.1` + `US3.1` as declared.
- **`US6.2b`** the per-day series section, which then legitimately depends on
  `US2.2`/`US2.3`.

Either way `US2.2`/`US2.3` must join the slice (A7).

### B2 — `US6.1` is too small to be worth its own overhead, and not deliverable alone

Its three criteria add a nav entry, extend an existing test constant
(`REQUIRED_TEST_IDS`, verified at `tests/test_page.py:17`), and reuse
`/static`. On its own it produces a third top-level entry pointing at an
analytics section that does not exist until `US6.2` — a dead entry, and a demo
that shows nothing. It is the natural first half of `US6.2a`. Merge it.

### B3 — `US5.1` and `US5.2` are one edit to one constant, and `US5.2` misses its own benefit

`AC5.1.4` is about the placement of the DDL constant; `AC5.2.2` says the index
declarations live in that same constant. `AC5.2.1` ("exactly three indexes exist
after migration") is unprovable until `US5.1` exists. And two of `US5.1`'s five
criteria are **already covered** by existing tests — `test_init_is_idempotent`
covers `AC5.1.2`, `test_a_migration_that_cannot_preserve_every_row_fails_loudly`
covers `AC5.1.3`. The genuinely new content across both stories is: bump
`SCHEMA_VERSION` to 4, add the index constant, execute it at both call sites.

**And `US5.2` asserts the wrong thing.** Its stated benefit is "so that a slow
query cannot silently reappear". None of its three criteria asserts that the
index is ever *used* — only that it exists. An index nothing consults passes all
three and delivers no benefit. Merge `US5.1`+`US5.2`, and replace `AC5.2.1` with
the assertion that earns the story: an `EXPLAIN QUERY PLAN` check that the
summary's and terms' predicates actually resolve through
`idx_analyses_label_created_at` / `idx_analyses_created_at`. That also gives
`US8.1` something real to lean on.

### B4 — `US7.1`–`US7.9` are not nine independent stories; they are about five

Answering the independence question directly. Verified groupings:

| Shared surface | Stories | Evidence |
|---|---|---|
| One verification script | `US7.2` + `US7.3` | `AC7.3.1`: "part of **verification**" |
| One file, two one-line edits | `US7.4` + `US7.8` | both `[project]` / `[tool.ruff]` metadata in `pyproject.toml`; `US7.8` already true (A6) |
| One ruff-config block | `US7.5` + `AC8.3.2` | same `[tool.ruff.lint.flake8-tidy-imports]` table — and `AC8.3.2` is unbuildable (A2) |
| One install path across doc + script | `US7.1` + `US7.2`'s install step + `US7.9` | README `## Setup` (README.md:15) and `## Test it, lint it` (README.md:51) |
| **Genuinely standalone** | `US7.6` (loopback in `app/main.py`), `US7.7` (harness in `tests/conftest.py`) | separate files, separate concerns |

So `stories.md:47`'s "US7.* independent of each other" is **false for at least
three pairs**. That does not invalidate the set — the human chose the overhead at
Q2/Q5 knowingly and `stories.md:7-9` says so. But the graph should stop
asserting independence it does not have, and the nine-way group is what makes
the whole set read as larger than it is.

### B5 — `US7.7` is under-estimated, and its two criteria contradict each other

Verified mechanics:

- `tests/conftest.py:136` — `asgi_request` calls `asyncio.run(_request(...))` per
  invocation. Two calls can never overlap. `AC7.7.1` names this precisely and is
  well-formed.
- `tests/conftest.py:102` — `_request` enters
  `application.router.lifespan_context(application)` **per request**, so
  `db.init_db` runs on every single call.

Two consequences the story does not name:

1. **Blast radius.** There are **69 `asgi_request(...)` call sites** across
   `tests/test_auth_routes.py` (28), `tests/test_routes.py` (30),
   `tests/test_bulk_import.py` (6) and `tests/test_page.py` (4). A harness that
   can overlap must stop calling `asyncio.run` per call, so its contract changes
   and all 69 sites must keep working. This is a refactor with a 69-site blast
   radius, not a swap.
2. **The concurrency test would go red for the wrong reason.** I ran four
   concurrent `db.init_db` calls against one file: three raised
   `sqlite3.OperationalError: database is locked`. With the lifespan still
   entered per request, an overlapping pair both runs `init_db` inside a
   transaction, and the test fails on lock contention rather than on R-01. A
   genuine-concurrency harness **must** hoist the lifespan into a fixture.
   `AC7.7.1` says nothing about this, and without it `FR8.4` cannot be trusted.

And the two criteria contradict each other: `AC7.7.1` requires genuine overlap
(harness **replaced**) while `AC7.7.3` says "the harness is replaced, not
extended around" and existing tests pass (which requires callers **unchanged**).
Both cannot be true of a change that removes `asyncio.run` from the call path.
Restate `AC7.7.3` as "every existing test module is migrated to the new harness
and still passes", and add the lifespan hoist to `AC7.7.1`.

### B6 — `US4.2` is fine, and its direction is genuinely right

`US4.2 → US4.1` (promote the tokenizer before applying the analytics filter) is
the correct and non-obvious order, and I endorse it. Two size notes:
`US4.2` alone is a verbatim code move with no user-visible behaviour — a
refactor-plus-guard, correctly ordered after `FR8.7` puts the guard test first.
`US4.1` is small: ~15 lines plus a stopword constant, because `FR4.1`'s token
rule is **already the engine's behaviour** (`AC4.1.3`'s digit/punctuation/
non-Latin rule is `[a-z']+` semantics verbatim). The only real work is the
stopword list, which `FR4.4` correctly defers to Design.

---

## C. Dependencies

### Missing edges

| Edge | Why it is real | Evidence |
|---|---|---|
| `US2.2` (⇒ `US2.3`) → **`US6.2`** | `AC6.2.1` renders the per-day series | A7 |
| `US2.2` → **`US6.3`** | `AC6.3.1` needs `AC2.2.4`'s unbounded default span | — |
| `US2.4` → **`US6.4`** | `AC6.4.2` renders 422 vs 500 vs empty distinctly | — |
| `US3.1` → **`US2.5`** | `AC2.5.1` calls "**either** analytics endpoint" | `US2.5` declares only `US2.1` |
| `US5.1`/`US5.2` → **`US7.9`** | `AC7.9.3`: README "describes the new indexes and the schema step" | declared: `US2.1, US3.1, US6.1` |
| `US4.2` → **`US7.9`** | `AC7.9.2`: "every new module is listed" — the tokenizer is new | — |
| `US7.3` → **`US8.2`** | `AC8.2.2` is a credential-scanner claim (`C-11`) | `US8.2` declares only `US1.1` |

`US7.9` is really a **terminal sweep** over almost every module-producing story
(`US1.1`, `US2.1`, `US3.1`, `US4.2`, `US5.1`, `US6.1`, `US7.1`, `US7.2`,
`US7.7`). Either declare all of them, or drop the declared list and mark it
"last, by construction" — the current partial list reads as a complete one and
will let `US7.9` land while the tokenizer is undocumented.

### Declared edge that is not real

- **`US7.2 → US7.5`.** `AC7.5.1` ("the lint fails") and `AC7.5.2` ("the
  application is clean") are both satisfied by running `ruff check` directly.
  Nothing in `US7.5` needs the verification script. Keeping `US7.2 → US7.3`
  (correct — `AC7.3.1` says "part of verification") and dropping
  `US7.2 → US7.5` restores an independence `US7.5` genuinely has.

### Declared edges that are real and correctly drawn

`US7.7 → US1.2` (harness, then the R-01 fix), `US5.1 → US5.2`, `US4.2 → US4.1`,
`US1.1 → US2.1`, `US2.2 → US2.3`, `US2.2 → US2.4`, `US1.1 → US8.2`, `US8.3`,
`US2.4 → US8.4` / `US8.8`, `US2.3 → US8.9`, `US6.2 → US6.3` / `US6.4`,
`US4.1 → US3.1`. Endorse all of these.

### One declared edge that is real but under-specified

`US7.7 → US1.2`. I confirmed the defect and its fix are both real: `db.connect`
calls `sqlite3.connect(path)` with no `check_same_thread=False`
(`app/db.py:139`), and reusing such a connection from another thread raises
exactly `sqlite3.ProgrammingError: SQLite objects created in a thread can only be
used in that same thread`. `AC1.2.1` names the right exception. But `US1.2`'s
`AC1.2.3` says the decision is stated in "the module that owns the connection" —
that is `db.py`, and `AC1.2.1`'s fix therefore lands in `app/db.py`, **not** in
the new analytics read module. Worth saying, because a developer following the
new-module framing would put the docstring in the wrong file.

### Duplicated criteria

`AC8.2.3` ("every SQL statement is parameter-bound"), `AC1.1.3` (same) and
`AC8.8.2` ("no request parameter is interpolated into SQL text") are the same
assertion in three stories. Three stories means three chances to write three
slightly different checks. Keep one owner and cross-reference the others.

---

## D. The four claims I was asked to check, answered

### `AC4.2.2` — the dummy engine's scoring is *identical*: **verifiable, and cheap**

The engine's entire tokenizer is `_WORD = re.compile(r"[a-z']+")`
(`app/dummy_client.py:68`), consumed once at `:83` as
`_WORD.findall(text.lower())` and compared only against `POSITIVE_WORDS` /
`NEGATIVE_WORDS` (`:16-53`). `tests/test_dummy_client.py` already pins labels,
the fixed probability triples, the model and the provider across 7 tests.

So the honest form of `AC4.2.2` is **"the existing dummy-client suite is
unchanged and green"**, not a bespoke before/after comparison — the
characterisation test already exists. That is much cheaper to build and much
harder to fool.

**What would break it**, in order of likelihood:

1. **Rewriting the regex while promoting it.** This is the real risk, and
   `AC4.2.1` does not catch it — that criterion forbids *duplicating* the
   pattern, not *rewriting* it. A developer who "improves" it to
   `[a-z]+(?:'[a-z]+)*` splits `"it's"` into `["it", "s"]`. Scoring survives by
   luck (neither fragment is a keyword), so `AC4.2.2` stays green while
   **analytics term extraction silently changes**. Add a criterion pinning the
   moved pattern: a fixture containing apostrophes, digits and a non-Latin run,
   with a hand-written expected token list. `AC4.1.3` already asserts the
   *behaviour* of the character class; what is missing is the assertion that the
   engine's tokens did not move.
2. **Folding the 3-character minimum or the stopword list into the tokenizer**
   rather than the filter. `AC4.2.3` guards this by *shape* ("two distinct
   operations") only — a docstring-level check, which inspection cannot really
   enforce. Pair it with a behavioural assertion: engine output on a
   keyword-free, stopword-heavy string is still `neutral`.
3. Any change to `.lower()`.

`AC4.2.1`'s claim that `_WORD` is "the private regex inside the offline engine"
is accurate, and `FR4.5`'s "beside `app/sentiment.py`" points at the obvious
home (`app/sentiment.py` holds the interface today, so a sibling
`app/tokenizer.py`).

### `AC2.3.1` vs `AC8.1.2` — **not in conflict**; see A3.

### `AC5.2.2` — **placement as declared is not sufficient**; see A1.

### `AC8.3.1` — **inspection-only, and inspection cannot carry it**

`AC8.3.1` says the read module "exposes no mutating operation", checked "when it
is inspected". The module is a set of module-level functions that receive the
live `sqlite3.Connection` — **the same object `insert_analysis` uses in the write
path** (`app/repository.py:44`). So the module is handed full write capability;
whether it exposes "a mutating operation" is a statement about its *function
names*, not its *capability*. Three functions named `select_*` pass by
inspection while being one refactor away from `INSERT`.

So `AC8.3.1` is a naming convention, and it is checkable only as a source scan —
which is exactly what `AC2.5.2` already says, and better, because it looks at
the SQL text rather than the names. `AC8.3.1` adds nothing a reviewer cannot
check by eye in five seconds and nothing a test cannot check by reading the same
file. **Recommend `AC8.3.1` be merged into `AC2.5.2`** (one owner, one
assertion), and that `NFR3`'s real content be the *capability* question — which
belongs to Design, not to this stage.

---

## E. Wrong altitude

### Pinned here that belongs to Design

1. **`AC7.5.1`'s mechanism.** "Given `ruff TID251` (`banned-api`) entries for the
   layer boundaries" names the rule and the mechanism. On this `ruff`,
   `banned-api`'s schema is a dot-key map — `{ "path".msg = "..." }` (I had to
   discover this by trial; `banned-api = { "sqlite3" = "msg" }` is rejected
   outright with *"invalid type: string … expected struct ApiBan"*). That is a
   one-line config detail, and guessing it costs a build cycle. Leave the rule
   id, drop the parenthetical.
2. **`AC5.2.2`'s placement rationale** — the wrong mechanism, so it must move
   anyway (A1); getting it right is Design's, but the story must not assert the
   wrong one.
3. **`AC6.1.3`'s asset shape.** "the analytics view's **script and styles** are
   requested … served by the same mechanism" implies per-view asset files. The
   page today has exactly one `app.js` and one `index.html`. Decide: extend the
   two existing files, or add new files under `/static` (which `StaticFiles`
   will serve). `AC6.4.4`'s "existing class names" constrains it but does not
   decide it.
4. **`US4.1`'s stopword contents** — `FR4.4` correctly defers this. No objection.

### Left vague that Code Generation will have to guess

1. **The key set of `counts` and `shares`.** `AC2.1.1` reads "each label's count
   equals its seeded occurrence" (implying only present labels); `AC2.3.1` reads
   "**all** counts 0, **all** shares `null`" for an empty day (implying the
   closed set). The house convention already settles it — `architecture.md` A3:
   "`label_counts` is pre-seeded from `LABELS` so zeros are present rather than
   absent" — so the project has an answer, and the stories do not. Pin it:
   `counts` and `shares` always carry all three labels from `app.sentiment.LABELS`.
2. **`AC2.4.3` / `AC2.4.4` cannot be built from the existing handler.** The
   envelope is exactly `{code, message}` — no `field` member
   (`app/routes.py:52-79`, with `ErrorEnvelope.additionalProperties: false`
   documented in its docstring). So `field == "query.from"` means a substring of
   `message`. Worse, `handle_validation_error` (`app/routes.py:342-355`) reports
   **only `errors[0]`** — it structurally cannot name *both* `query.from` and
   `query.to`, which is what `AC2.4.4` requires. So the inversion case needs a
   hand-built message path that `AC8.5.2` ("the code set gains exactly one
   member") does not obviously authorise. Name the construction; otherwise
   Design will discover the conflict late.
3. **`AC6.1.2`'s "pinned test-id constant".** It is `REQUIRED_TEST_IDS` in
   **`tests/test_page.py:17`**, and `app/static/app.js` uses inline string
   literals (`:14-27`) with **no** constant in `app/` to extend. The criterion's
   intent is right; its noun is wrong. (`FR6.9`'s "the page module's existing
   pinned test-id constant" is wrong on location for the same reason — worth a
   correction in `requirements.md` at the next revision, though the story text
   itself is actionable.)
4. **`personas.md` P6 understates current exposure.** It says "a page that polls
   on a date range is exactly the trigger pattern". Verified:
   `app/static/app.js:201` already runs `setInterval(refreshConnection, 20000)`,
   so the shipped page **already polls today**, before analytics exists — and a
   20-second health poll overlapping a user-initiated
   `refreshHistory`/`submitAnalysis` is the same R-01 race. The persona's
   framing makes the R-01 fix sound analytics-blocked; it is not, which the
   stories correctly say elsewhere ("Nothing in `US7` blocks the analytics
   feature itself"). Fix the persona, not the graph.

### Belongs to a later stage, not to this one

1. **`AC8.7.3`** (test-before-implementation ordering) → the team Testing
   Contract and Code Generation's ordering input. See A5.
2. **Whether the unbounded series needs a cap** (`NFR9`) → Delivery Planning as a
   policy call. The draft is right to leave it open; just do not let it become a
   story.
3. **The lockfile format** (`US7.1`) → Contract Design / a design decision. The
   requirements already list it as an open question, and `AC7.1.3` ("the
   documented install command consumes it") has no pass/fail until it is fixed.
   The story is right to exist; it is not yet Estimable.
4. **The scanner and audit tool choice** (`US7.3`) → same. Also open upstream.
5. **The `sqlite3` connection-ownership decision** behind `AC8.3.2` (A2) → Design.
   It is a genuine architecture question — shared per-request writable connection
   versus a read-only analytics connection — and it is the one place where
   `FR1.3`'s affirmed team rule and `NFR3`'s capability guarantee pull against
   each other.

### One substantive gap in `NFR1`'s verification

`AC8.1.2` pins **statement count**, which is constant and easy. The terms path,
however, must read every in-range positive/negative `text` into Python and
tokenize it there — `FR4.3` forbids an external service and there is no SQLite
tokenizer. So `/v2/analytics/terms` over 10,000 rows does an unbounded amount of
row-fetching work, and **nothing in `AC8.1.1` or `AC8.1.2` measures it**. The
story set verifies the easy half of `NFR1` and leaves the half that could
actually miss the 200 ms budget unverified. Add an assertion that pins the rows
fetched (bounded by rows-in-range, not by distinct terms) and states the
measurement explicitly, or say in the story that the budget is measured on the
summary endpoint only and terms is bounded-by-construction instead.

---

## Positions

- AGREE: **`US4.2 → US4.1` ordering** — promoting the tokenizer before applying the analytics filter is correct and non-obvious; it is the one edge in the graph that a less careful plan would have reversed.
- AGREE: **"Nothing in `US7` blocks the analytics feature itself"** — verified true, and reinforced by `app/static/app.js:201`: the page already polls, so R-01 is reachable before analytics lands.
- AGREE: **`US7.2`/`US7.3`/`US7.5` platform-neutrality rationale** — `AC7.2.3`'s "no provider CI job, which cannot run here because there is no git remote" is the right call and correctly stated.
- AGREE: **`US5.1 → US5.2` direction** — right, though the two are one edit (see B3).
- AGREE: **`FR8` deliberately not mapped to `US8`** — the header's call-out that `US8.x` implements `NFR1`–`NFR9` and not `FR8.x` prevents a real misreading.
- OBJECT: **`US6.2`'s dependency list** — `AC6.2.1` renders the per-day series, which is `US2.3`'s output behind `US2.2`; neither is declared. **The affirmed thin slice `US1.1 → US2.1 → US6.2` is therefore not demonstrable end to end.**
- OBJECT: **`AC5.2.2`** — "declarations live in the table DDL" specifies a SQLite capability that does not exist, and neither escape (multi-statement `execute`, `executescript`) works without breaking `AC5.1.5`/`AC5.1.3`.
- OBJECT: **`AC8.3.2`** — `ruff TID251` is an import rule and provably does not fire on `conn.execute(...)` under any banned-path form; the criterion cannot be built, and its two workable substitutes both collide with `AC1.1.2`.
- OBJECT: **`AC7.3.2`'s "four known fake-key fixtures"** — there are six distinct fake-key literals in `tests/`; an allowlist written to four makes `AC7.3.1` fail on the first scan run.
- OBJECT: **`AC8.7.3`** — test-before-implementation ordering is unverifiable in a repo whose recorded rhythm is one squashed commit per scope; it is a team Testing Contract rule, not an acceptance criterion.
- OBJECT: **`US7.8`** — `requires-python = ">=3.11"` and `target-version = "py311"` already match and `ruff check app` passes; both criteria are satisfied by the shipped file.
- OBJECT: **`AC8.1.1`/`AC8.1.2` measure the wrong half of `NFR1`** — statement count is constant and easy; the terms endpoint's in-range row volume is unbounded and is the half that could miss the 200 ms budget.
- OBJECT: **The `US7.*` independence claim** — `US7.2`+`US7.3`, `US7.4`+`US7.8` and `US7.5`+`AC8.3.2` each share one file or one sitting; only `US7.6` and `US7.7` are genuinely standalone.
- OBJECT: **`US7.7`'s sizing and its two contradictory criteria** — 69 `asgi_request` call sites must migrate, and the per-request lifespan must be hoisted (concurrent `init_db` raises `database is locked`, verified) or `FR8.4` fails on the wrong exception.
- OBJECT: **`US6.1` as a separate story** — it delivers a nav entry with no content until `US6.2`; merge it into the first half of `US6.2`.
- OBJECT: **`US5.2`'s criteria** — none asserts the index is ever *used*, which is the entire stated benefit; an `EXPLAIN QUERY PLAN` assertion is the missing criterion.
- OBJECT: **The declared `US7.2 → US7.5` edge** — `AC7.5.1`/`AC7.5.2` are satisfied by running `ruff check` directly; the edge is not real.
- OBJECT: **The `counts`/`shares` key set** — `AC2.1.1` and `AC2.3.1` imply different answers, and `architecture.md` A3 already settles it in favour of pre-seeding from `LABELS`.
- OBJECT: **`AC2.4.4`** — the existing `handle_validation_error` reports only `errors[0]` and the envelope has no `field` member, so naming both `query.from` and `query.to` needs a construction path the story does not authorise.