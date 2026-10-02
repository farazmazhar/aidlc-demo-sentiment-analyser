**Collaborator:** aidlc-developer-agent

## Contribution

Code-craft review of the lead's Practices Discovery draft, against the source as
written. Lens: naming, module and file organisation, layer boundaries, error-handling
shape, and the difference between a convention this codebase *follows* and one it only
*claims*.

### What I read, and what I inferred

**Read in full:** `app/routes.py` (387), `app/service.py` (214), `app/repository.py`
(102), `app/db.py` (243), `app/models.py` (144), `app/main.py` (103),
`app/sentiment.py` (84), `app/dummy_client.py` (101), `app/static/app.js` (201),
`tests/test_page.py` (77), `tests/conftest.py` (176), `pyproject.toml`,
`README.md` §Storage/§HTTP surface/§File layout, `data/sentiment.db`.

**Read partially:** `app/config.py`, `app/session_auth.py`, `app/openrouter_client.py`
(grep-level: every `except`, every `noqa`, every `#:` line, the `urllib` bodies).

**Read as context:** `code-structure.md`, `architecture.md`, the lead's
`team-practices.md` and `discovered-rules.md`, `scope-document.md`,
`constraint-register.md`, `project-description.json`, `intent-statement.md`.

**Ran:** `grep`/`wc` sweeps for `except`, `noqa`, `pragma: no cover`, `#:`,
`from __future__ import annotations`, `Single responsibility`, `TODO|FIXME|HACK`,
`print(`, `/v2`, `ensure_page_state`, `intensity`, `query=`, `monkeypatch`;
`.venv/bin/ruff rule TID251`; a read-only query against `data/sentiment.db`.

Everything below is measured, not inferred, unless it says *inferred*.

---

### 1. Four lines in the draft do not match the code

The draft is careful and its drift accounting is mostly right — I checked the
counts I could check and the `#:` figure (71 across 10 modules), the
`Single responsibility:` figure (11 of 12), the four `# noqa: S310`, the four
`# pragma: no cover`, the zero `TODO`/`FIXME`, and the zero `print()` in `app/`
all reproduce exactly. Four things do not.

**(a) "no broad catch anywhere" is false as written.** The draft says
*"`grep -E 'except\s*:' app/` returns nothing" — every handler names a specific
type.* The command is true and the conclusion it supports is not:
`app/db.py:163` catches **`BaseException`** in `init_db`, inside the
`BEGIN` / `try` / `rollback()` / `raise` / `commit()` block
(`app/db.py:155-166`). It is the right construct — rollback-and-re-raise, not a
swallow — but it *is* the one broad handler in `app/`, and it is the one a reader
should be pointed at. Sharper and still true: *no bare `except:`, no
`except Exception`, and exactly one `except BaseException` — the rollback-and-reraise
in `db.init_db`.* As drafted, a future author who greps for the stated rule finds
a violation in the module that owns the schema, and learns the docstring is
unreliable. Also unremarked: `app/service.py:180` catches a two-type tuple mid-loop
to *skip and continue*, which is a third error-handling idiom (refuse / rollback /
skip) with no stated rule for which to use.

**(b) The layer chain is stated more cleanly than the code runs it.** The draft
writes the boundary as `… → repository, db, clients → service → routes → main`
and calls the graph "acyclic and descending". The *graph* is that. The *policy*
implied is not what the code does: `app/routes.py:31` imports
`DEFAULT_LIST_LIMIT, list_analyses, list_analyses_by_import_id` from
`app.repository` and calls them directly at `app/routes.py:177` and
`app/routes.py:242`. There is **no read or query function in `app/service.py` at
all** — its public surface is `effective_connection`, `get_client`, `require_text`,
`import_texts`, `analyze_text`, `ImportSummary`, `new_import_id`. So the observed
rule is: *writes and engine calls go through `service`; reads go straight from the
route to the repository.* `architecture.md`'s coupling table is honest about this
(`app/repository.py` fan-in `2 (routes, service)`), but the Code Style section
tells a cleaner story than the code tells, and this is the single most consequential
thing it gets wrong for the next change (see §3).

**(c) The test-naming convention is understated, and it is a real one.** The draft
says tests are `tests/test_<module>.py` with `test_<behaviour>` names. The file half
is exact. The function half is materially different: the convention is a full prose
sentence stating the expected outcome, prefixed by the route where one applies —
`test_v1_analyze_returns_the_stored_record_field_set`,
`test_v1_analyses_is_a_bare_array_newest_first`,
`test_a_body_that_is_not_the_declared_object_is_refused`,
`test_pre_v1_data_paths_are_no_longer_served`. This line is a candidate for
affirmation, so it should be affirmed in its actual shape.

**(d) A codekb convention row is wrong, and team-practices draws on codekb.**
`code-structure.md:208` records `from __future__ import annotations` as applying to
**"All 12 modules"**. It applies to 11; `app/__init__.py` does not have it. The
draft's own count is right, so no correction is needed in the draft — but the stale
row should not be allowed to reach a later stage as an authoritative convention.

One more, not in Code Style: `architecture.md:502` names
`ensure_page_state/connection ownership`. **`ensure_page_state` does not exist
anywhere in this repository.** The connection owner is `get_connection`
(`app/routes.py:92`). Any stage that reads that improvement opportunity verbatim
will look for a function that is not there.

---

### 2. The boundaries are real today and prose-only — and one line would enforce them

The draft calls the module docstring "the codebase's own boundary mechanism and the
code agrees with it". The code agrees; nothing *checks*. The "no SQL in `routes.py`",
"no HTTP in `service.py`", "no runtime engine dependency in `repository.py`" rules are
stated in prose and in `architecture.md`, and the only mechanical gates in the project
are `filterwarnings = ["error"]`, the 80 % coverage floor, and the curated `ruff`
rule set. `pyproject.toml`'s `select = ["E","F","W","I","N","UP","S","B","C4","SIM"]`
contains **no `TID`**, and I confirmed against the pinned tool (ruff 0.16.9) that
`ruff rule TID251` is available and driven by
`lint.flake8-tidy-imports.banned-api`. A per-file `banned-api` entry banning
`sqlite3` for `app/routes.py` and `fastapi` for `app/service.py` is a config-only
change, and it is *consistent with the stance the team already took* — an explicitly
reviewed rule selection rather than a drifting default, with a written reason beside
each entry. The draft's own framing of `lint.select` as "explicit and reviewed, not a
drifting default" is the argument for adding the rule, not against it.

This matters more after this intent than before it. Today the boundaries hold by
author discipline on a 12-module package. The analytics layer adds a query module, a
third router, and a page that polls — the first work in this project that a future
change will plausibly copy from rather than merely inherit.

---

### 3. The three forks this intent actually hits, and where each one breaks

The draft names two pressures (the tokenizer and the version prefix). I found four,
and the two it misses are more expensive than the two it caught.

**Fork 1 — where do the analytics queries live, and does the route call them
directly?** Following the code as written, `routes → repository` is the precedent
for every read, and the analytics layer is *entirely* reads. So the cheap,
precedented shape is a new query function called straight from the handler. The
alternative — a service-layer function for reads — has **zero** precedent, and would
be the first time `service.py` orchestrates something that does not touch the engine
(which is what its own docstring says it is for: *"turn submitted text into a
persisted analysis"*). `app/repository.py` is 102 lines; the aggregate queries take
it to roughly 170, still inside the size band this codebase treats as normal. This
is a fork a snapshot genuinely cannot settle, and the draft does not surface it.

**Fork 2 — the migration entry point cannot grow to a second table as written.**
`init_db` (`app/db.py:145-168`) is a two-arm branch: `if _table_exists("analyses") →
_migrate_analyses(...)` / `else → CREATE_ANALYSES_TABLE`, then
`CREATE_SCHEMA_META_TABLE` *after* the branch. The scope wants "tables/indexes for
analytics". A new table's `CREATE TABLE IF NOT EXISTS` therefore has to be added in
**two** places, or the branch refactored — and this codebase already solved exactly
this problem once: `schema_meta` is created *after* the branch, on every path, which
is the placement to copy. Stating that as the established pattern turns a trap into a
one-liner.

**Fork 3 — the index the analytics layer most wants is the one the migration
destroys.** I queried the actual store: `data/sentiment.db` has
`schema_meta.version = 2`, 9 columns (no `import_id`), 0 rows, and **no index on
`analyses` at all** (only `sqlite_autoindex_schema_meta_1`). The natural analytics
index is on `analyses(created_at)`, and `created_at` is ISO-8601 UTC ending in `Z`,
so it is directly `BETWEEN`-comparable as a string. But `_rebuild_analyses`
(`app/db.py:233-243`) does `RENAME … RENAME TO analyses_pre_v1` → `CREATE TABLE` →
`INSERT…SELECT` → `DROP TABLE`, and `CREATE_ANALYSES_TABLE` (`app/db.py:40-53`)
declares no index — so an index added to that DDL is silently destroyed on any
migrating store. `architecture.md` (TD-1) verified this empirically and the draft
never mentions it. The safe, idempotent, constraint-satisfying placement is
`CREATE INDEX IF NOT EXISTS` **after** the branch, on every startup — which is free
here, because `asgi_request` re-enters the lifespan on every call
(`tests/conftest.py:102`), so the suite exercises the migration path on every single
in-process request. That is a free idempotency test the design should be told to lean
on.

**Fork 4 — a new column on `analyses` is a seven-place edit, and the codebase has
already recommended against it.** Adding one column touches: `ANALYSES_COLUMNS`
(`app/db.py:63`), `_ADD_COLUMN_SQL` (`app/db.py:94`), `CREATE_ANALYSES_TABLE`
(`app/db.py:40`), `SCHEMA_VERSION` (`app/db.py:35`), plus `RECORD_FIELDS`
(`app/models.py:25`), `to_dict` (`app/models.py:103`), `from_row`
(`app/models.py:117`) and the positional export writer (`app/routes.py:252-263`) —
eight, in three modules and the README. `_is_v1_shape` (`app/db.py:195`) also
compares column **order** exactly (`tuple(info) != ANALYSES_COLUMNS`), so a column
appended anywhere but the end forces a full rebuild of the table. `architecture.md`'s
TD-2 already concludes a **separate table** is the one-place alternative. The
scoping decision to put analytics aggregates in their own table is therefore
*justified by the code*, and that justification belongs in the Code Style section as
an observed cost — it is the difference between a one-statement migration and a
rebuild of the user's data.

Naming drift compounds this: `SCHEMA_VERSION = 3` coexists with a function called
`_is_v1_shape` (`app/db.py:195`), an `init_db` docstring that says "bring its schema
to v1" (`app/db.py:146`), a `CREATE_ANALYSES_TABLE` comment saying "the v1 physical
schema", and a `main.py:71` comment saying "brought to the v1 shape". The draft
repeats "v1" as the current shape without noticing. For a v3 → v4 step the names are
actively misleading, and this is a one-off accident, not a convention (§6).

---

### 4. Two requirement-versus-code collisions the draft does not raise

These are outside Code Style proper, but they are decided by code shape, and both
will be expensive to discover at Build.

**(a) The version prefix is not an even question — the human has already answered it
once, in writing, in one direction.** The draft frames `/v2` as "two different
extension shapes" that "a snapshot cannot choose between". The evidence is stronger
than that. `project-description.json` — the human's own words, the `[desc]` source
every `[desc]` tag in the register points at — says:

> "single-page UI + **/v1 JSON API**" *(describing what exists)*
> "Add **GET /v2/analytics/summary**?from=&to=&import_id= …"
> "Add **GET /v2/analytics/terms**?from=&to=&limit= …"

and the same text asks to "reuse the existing … **error envelope**". So the human
named `/v1` only to describe the status quo and typed `/v2` for both new endpoints.
The draft's framing is right that this needs the human; it is wrong that the code
is 50/50. What is genuinely undecided is narrower: whether the literal string `/v2`
is binding or was loose shorthand for "a new versioned data surface".

Meanwhile `constraint-register.md` `C-4` reads *"The new endpoints follow the existing
`/v1` JSON API conventions and the single error envelope"* — sourced to `[Q1] [desc]`,
i.e. to the same human text that says `/v2`. **`C-4`'s paraphrase contradicts the
source it cites.** That is a defect in the register, not merely an open question, and
it should be surfaced to the human as such.

The craft consequences differ materially, which is why this needs a ruling rather
than a default:

| | literal `/v2` | `/v1` (C-4 as written) |
|---|---|---|
| router | new `APIRouter(prefix=…)` + one `include_router` (`app/main.py:90-91` is the insertion point) | analytics on the existing `v1_router` |
| constant | `V2_PREFIX` beside `V1_PREFIX` (`app/routes.py:49`) | none |
| contract | a new surface: its own error codes, its own README table rows | grows a frozen contract that already pins `RECORD_FIELDS`, `EXPORT_COLUMNS` and 6 error codes |
| frontend | second constant beside `const API = "/v1"` (`app/static/app.js:10`) | unchanged |
| 404 code | needs a decision on whether `IMPORT_NOT_FOUND` is reused across versions | reuses it |

Note the frontend already holds an **independent second copy** of the prefix
(`app/static/app.js:10`, with fetch sites at `:87`, `:97`, `:157`, `:185`) and
nothing asserts the two copies match. One assertion in `tests/test_page.py` closes
that, in the codebase's own idiom.

Whichever way the human rules, the codebase already owns the instrument for closing
the other path: `test_pre_v1_data_paths_are_no_longer_served`
(`tests/test_routes.py:342`). A retired route gets a test that asserts it is gone.

**(b) `mean intensity` asks for a column this codebase deliberately retired.**
The human's request says the summary endpoint returns "mean confidence, **mean
intensity**". `intensity` is retired, deliberately and on the record:
`RECORD_FIELDS` (`app/models.py:25`) omits it; `_INSERT_SQL`
(`app/repository.py:32-36`) never writes it; `app/repository.py:28-31` says "a new
row leaves it unset rather than writing a value the v1 contract no longer produces";
`tests/test_page.py:64-68` asserts the page must not even contain the word; BR3.4 /
AC2.1.3 record the decision. The column is still physically present and nullable
(`app/db.py:47`), so `AVG(intensity)` does not error — it returns `NULL`, because
**every row the application has ever written has `intensity = NULL`**. I confirmed
this on the actual store: 0 rows, 0 non-null intensities.

So the requirement is satisfiable only as a permanent `null`, or by resurrecting a
retired attribute. There *is* an in-repo precedent for the answer — `A3` in
`architecture.md`: an aggregate over an empty input answers `null`, never a
fabricated zero — but a precedent is not a decision, and the requirement itself has
to be corrected or explicitly re-scoped. **Nothing in the lead's 425-line draft
mentions this.** It is the kind of collision that is cheap at interview and expensive
at Build.

---

### 5. What should become an explicit team practice, and why

The draft presents observed patterns in one undifferentiated list, which makes it
hard for the human to tell a practice from an accident. Here is the split. Each
"yes" is something a future change can follow *and a reviewer can check*.

**Should be codified — distinctive, consistent, and load-bearing:**

1. **Module docstring carrying an explicit `Single responsibility:` negative claim.**
   11 of 12 modules (all but the 10-line `__init__.py` shim), and the negative half —
   *"No sentiment logic and no SQL live here"* (`app/routes.py:3-6`),
   *"Depends on nothing from the sentiment engine at runtime"*
   (`app/repository.py:4-11`) — is what makes a flat by-layer package auditable
   without an architecture document. This is the codebase's best idea.
2. **One construction site per external dependency, plus a function-local import to
   keep a module unloaded.** `get_client` (`app/service.py:76`) is the only place a
   client is built; `from app.openrouter_client import …` sits *inside* `_live_client`
   (`app/service.py:103`) so the offline path never loads the module that performs
   HTTP. Cheap, unusual, and worth writing down.
3. **Refuse, never substitute.** `limit: int = Query(50, ge=1)` — no silent clamp;
   `mean_confidence is None` when nothing was imported — no division by zero and no
   fabricated `0.0`; `UNKNOWN_PROVIDER = "unknown"` — never `null`, never `"None"`;
   `intensity` never back-filled with an invented number. This spans `db.py`,
   `repository.py`, `models.py` and `service.py` and is the most consistent thing in
   the repository. It is also the answer to §4(b).
4. **Read back after write.** `insert_analysis` returns the row it re-`SELECT`ed
   (`app/repository.py:76-77`), never the in-memory payload, so the returned object
   is the persisted object.
5. **Injectable seams instead of doubles; assert against the real store and the real
   served markup.** `settings` / `session_auth` into `create_app`, `now` into
   `insert_analysis`, `client` into `analyze_text`, `connection` into every
   repository call, `transport` / `exchanger` into the adapters. `socket.socket.connect`
   is replaced by a raiser, and `tests/test_dummy_client.py` actively proves the guard
   is armed. This is the strongest thing about the suite and it is worth naming as a
   practice, not just a fact.
6. **Substitute at the consumer's import name, not the definition.** Three sites
   patch the route module's name: `monkeypatch.setattr("app.routes.get_client", …)`
   (`tests/test_routes.py:322`, `tests/test_bulk_import.py:151`,
   `tests/test_auth_routes.py:236`). No `unittest.mock`, but `monkeypatch` *is* the
   sanctioned substitution instrument — "zero mock objects" must not be promoted to
   "no substitution", or the analytics tests will be written against a rule that does
   not exist.
7. **The hand-written constant in the test module *is* the contract.** Each test
   module pins what it protects at the top with a `#:` comment — `RECORD_FIELDS`,
   `ENVELOPE_FIELDS` (`{"code", "message"}`), `ISO_8601_UTC`, `REQUIRED_TEST_IDS`.
   This is the codebase's stated substitute for response models (`architecture.md`
   A1: no `/openapi.json` can describe the real shapes, "contracts are pinned only by
   hand-written constants in the tests"). It is a real practice with a real cost —
   the nine-field record now lives in `models.py`, `test_routes.py`, the README prose
   *and* a positional list in `app/routes.py:252-263` — and the analytics endpoints
   must follow it rather than invent a new pinning style.
8. **A retired path gets a test asserting it is gone**
   (`test_pre_v1_data_paths_are_no_longer_served`, `test_the_page_has_no_intensity_affordance`).
   Small, real, and the right instrument for the `/v2` ruling in §4(a).
9. **The README is part of the change.** `code-structure.md` and `architecture.md`
   both call the README's §HTTP surface table "the contract of record". A new router,
   endpoint, module or test module means editing `## HTTP surface` (19 hand-kept rows),
   `## File layout` (every module listed by hand) and usually `## Storage`. The draft
   never mentions this, and it is the reason a "one-line" prefix change is not one line.
10. **`ruff` with an explicitly reviewed rule set, and B008 silenced by
    configuration rather than `# noqa`.** `extend-immutable-calls =
    ["fastapi.Depends", "fastapi.Query"]` is the rule's own documented escape hatch,
    used correctly and explained in place. Worth affirming as a stance.

**Should be codified as a rule *about* the boundary, since prose is not enforcement:**
add `TID251` `banned-api` entries (§2). One config block, and it converts three
docstring promises into three gate failures.

---

### 6. What is a one-off accident and must not be codified

The draft's "Conventions the code holds today" list mixes genuine conventions with
things that just happened. These four should be kept out of `memory/team.md`, because
a team practice is a licence to copy:

1. **The duplicated `urllib` bodies in `session_auth.py:88-120` and
   `openrouter_client.py:89-96`.** `architecture.md` calls this "cohesion chosen
   over DRY". It reads as a principle; it is the residue of a boundary that forbade
   the two modules importing each other. Its fingerprints are still in the tree: all
   four `# noqa: S310` suppressions exist *only* because of the duplication. Codified
   as a practice, the next author duplicates a third time. The honest statement is
   *"a known duplication, not a pattern"* — and the analytics layer adds no third
   outbound call, so nothing forces the decision this run.
2. **`_WORD` in `app/dummy_client.py:68`.** The draft calls this a deadlock: a
   tokenizer owned by two consumers has no home under a no-`utils.py` rule. It is not
   a deadlock. `_WORD = re.compile(r"[a-z']+")` is a one-line compiled pattern, and
   it is **not the thing the analytics layer needs** — "significant terms" requires a
   stopword set, a minimum length and probably case handling, none of which the
   offline engine's engine-grade splitter has any opinion about. The reachable options
   are three, and the third is missing from the draft: (a) leave `_WORD` alone and
   let the new term-extraction module own its own pattern; (b) promote it to a public
   `WORD_PATTERN` in **`app/sentiment.py`** — a leaf with fan-out 0 that already owns
   `LABELS`, the closed vocabulary every analytics aggregate is bucketed over, and is
   already imported by `service.py` and `repository.py`; (c) a new named module. (b)
   costs one line and breaks neither the no-junk-drawer rule nor any layer, because
   the concept it owns is the same one `sentiment.py` already owns. What *should* be
   codified is the refusal: **do not import `_WORD` from another module, and do not
   copy the regex.**
3. **`SCHEMA_VERSION = 3` next to `_is_v1_shape` and "bring its schema to v1".**
   Stale naming, not a convention. Harmless at v3, actively misleading at v4.
4. **`service.py` carrying no `#:` line at all** while every other contract-bearing
   module has one. `ImportSummary` is covered by a class docstring instead. That is a
   convention *variant*, not a counterexample — and `#:` at 71 lines across 10 modules
   is otherwise a genuinely consistent convention worth keeping.

---

### 7. What the evidence settles, and what only the human can settle

**The evidence settles these; do not spend interview time on them.**

- The counts in the draft's Code Style section reproduce exactly (verified above).
- `data/sentiment.db` really is at `schema_meta.version = 2` with 9 columns and 0
  rows, so the v2 → v3 path has never run against this file, and the next `init_db`
  will rebuild the table.
- `intensity` is `NULL` for every row the application writes, and the analytics
  `mean intensity` is therefore `null` unless the requirement changes.
- There is no `/v2` string anywhere in `app/` or the README.
- A date-range index on `analyses` is destroyed by `_rebuild_analyses` unless it is
  created after the branch.
- The tokenizer deadlock is not a deadlock; `app/sentiment.py` is a valid home.
- Adding a column to `analyses` is an eight-place edit across three modules plus the
  README; a separate table is one statement. The code has already recommended the
  latter.

**Only the human can settle these four.** The first two are judgment calls about
intent; the second two are about a boundary the code does not currently state.

1. **Is the literal `/v2` binding, or shorthand for "a new versioned data surface"?**
   (The human typed `/v2` twice; `C-4` in the register says `/v1`, sourced to the
   same text. One of the two is a paraphrase error, and the human should say which.)
2. **Is `mean intensity` still wanted, given the column is retired and null on every
   row the app writes?** The alternatives the code supports: report `null` with a
   stated reason, drop the field, or re-scope to something the store still holds.
3. **Do read paths go straight from route to repository, or through a service layer?**
   Every existing read does the former and `service.py` has never held a query. But
   the analytics layer is the first place where "reads bypass the service" becomes a
   *rule* rather than an accident, and only the human can say whether that is the
   boundary they want written down.
4. **Should the layer boundaries get a mechanical gate?** `ruff` `TID251`
   `banned-api` is available in the pinned tool and is a config-only change, but
   turning three prose promises into three failing checks is a decision about how
   much the team wants tools to enforce rather than reviewers to notice.

Two smaller ones the human can settle in a word each, and the draft should not decide
by omission: whether the new term-extraction module is a by-layer sibling of
`repository.py` (consistent with the flat by-layer package) or a feature folder (a
change of layout, which nothing in the codebase has ever done); and whether the
second view is a second page or a section on the existing one — the human's own
`intent-statement.md` leaves that open, and `app/static/app.js` plus the single
`INDEX_HTML` constant read from disk per request (`app/routes.py:140`) make the two
shapes cost differently.

## Positions

- AGREE: the `## Code Style` measurement as a whole — every count I could reproduce
  (`#:` 71/10 modules, `Single responsibility:` 11/12, four `# noqa: S310`, four
  `# pragma: no cover`, zero `TODO`/`FIXME`, zero `print()`, the `ruff` settings
  table, the 96.02 % / 118-test figures) is exact and the "observed but not yet
  affirmed" discipline is the right one for a re-run.
- AGREE: the module docstring as a boundary declaration is the codebase's most
  valuable convention and deserves affirmation — the negative "what does *not* live
  here" clause is what makes a flat by-layer package auditable.
- AGREE: refusing rather than substituting (`ge=1`, `None` mean, `unknown` sentinel,
  never-backfilled `intensity`) is the most consistent pattern in the repository and
  should be named as a practice, because it is also the answer to the `mean intensity`
  collision.
- AGREE: the boundary is "unchanged and affirmed as the layout we keep" — I verified
  the graph is acyclic and descending and the code agrees with the docstrings. My
  objection is about *enforcement*, not accuracy.
- AGREE: the tokenizer is a real insertion-point problem the design must resolve
  rather than guess at.
- OBJECT: "no bare `except` and no broad catch anywhere" — `app/db.py:163` catches
  `BaseException` (rollback-and-reraise), so the stated invariant is false and the
  grep offered as evidence cannot support it; the corrected form is both true and
  more useful.
- OBJECT: the layer chain is presented as if HTTP reached persistence only through
  `service` — `app/routes.py:31,177,242` call the repository directly and
  `service.py` holds no read function at all; the real rule is "writes through
  `service`, reads straight from the route", and it is the fork this intent most
  needs answered.
- OBJECT: the version prefix is framed as an even 50/50 code-craft choice — the
  human's own words name `/v2` twice, and `C-4`'s `/v1` paraphrase cites that same
  text, so this is a register defect to surface, not a snapshot deadlock.
- OBJECT: the draft is silent on the `mean intensity` collision — the requested
  aggregate is over a column the codebase deliberately retired, and it is `NULL` on
  every row the application writes (verified against the real store).
- OBJECT: the draft is silent on `_rebuild_analyses` destroying any index added to
  `CREATE_ANALYSES_TABLE` — the index this intent most needs is the one the existing
  migration deletes, and `init_db`'s two-arm branch has no place to put a second
  table's DDL.
- OBJECT: the "observed conventions" list does not distinguish a convention from an
  accident — the duplicated `urllib` bodies (which are why all four `S310`
  suppressions exist), `_WORD` in an engine, and the `_is_v1_shape` /
  `SCHEMA_VERSION = 3` naming drift should be explicitly excluded from `team.md`, or
  the next author will copy them.
- OBJECT: the test-naming convention is understated as `test_<behaviour>` — the real
  convention is a full prose sentence stating the expected outcome, route-prefixed
  where applicable, and it is a candidate for affirmation so it should be affirmed
  in its actual shape.
- OBJECT: the boundary is called "the codebase's own boundary mechanism" while
  nothing enforces it — `TID` is absent from the selected rule set and `TID251`
  `banned-api` is available in the pinned ruff, so a config-only gate for the three
  prose promises is available and consistent with the already-affirmed curated
  rule-set stance.
- OBJECT: `architecture.md:502` names `ensure_page_state`, which exists nowhere in
  this repository (the connection owner is `get_connection`, `app/routes.py:92`), and
  `code-structure.md:208` records `from __future__ import annotations` as applying to
  all 12 modules when it applies to 11 — both are stale rows a later stage could
  mistake for authoritative convention.
- OBJECT: the draft never states that the README is part of the change, although two
  codekb artifacts call its §HTTP surface table "the contract of record" and a new
  router, module and test module each require a hand-maintained edit there.
