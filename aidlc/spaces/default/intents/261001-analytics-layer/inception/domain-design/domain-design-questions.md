# Domain Design — Boundary Questions

> The plan questions for this stage. Every option carries the drafted answer, so
> the choice is between reasoned positions. `component-inventory.md` lists the
> twelve components that exist today; this stage decides which **new** building
> blocks the analytics layer adds and whether any existing boundary moves.

## Q1 — How many new components does this feature add?

Reversing Engineering found that `repository.py` is "the natural and uncontested
home for aggregate SQL and is currently clean", and the team already ruled that
aggregate reads live in a **dedicated read module beside `repository`** rather than
in `repository` itself. Candidates: one analytics module, a separate tokenizer
module, a small HTTP read layer, and the page script.

A. **Three** — an analytics read/aggregate component, a term-extraction component,
   and the analytics view script as a component of the Web UI. The smallest set
   that matches the team's stated boundaries
B. **Two** — fold term extraction into the analytics component; it is one function
   and its own module may be over-decomposition at this size
C. **Four** — the three above plus a `v2` router component, so the new HTTP surface
   is its own building block rather than an addition to `routes.py`
D. Other (please specify)

[Answer]: A. Three new components: an analytics read/aggregate component, a term-extraction component, and the analytics view as a component of the Web UI.

## Q2 — Where does the tokenizer live, and does it own anything?

`_WORD = re.compile(r"[a-z']+")` is at `app/dummy_client.py:68` — underscore-private,
inside the offline engine, and the only tokenizer in the repository. The team ruled
that the promoted tokenizer must expose **two distinct operations** (tokenize, and
filter to significant terms) so the engine's scoring is unchanged, and that
`app/sentiment.py` is the natural home because it is a fan-out-0 leaf that already
owns `LABELS`.

A. **A new `TermExtraction` component in its own module**, not `sentiment.py`, so
   the engine's vocabulary contract stays separate from a text-processing utility
B. **Add it to `app/sentiment.py`**, which becomes the owner of the label
   vocabulary *and* the term extraction
C. **A new `TermExtraction` component whose module is `app/terms.py`**, with
   `dummy_client` and the analytics component both calling it
D. Other (please specify)

[Answer]: A. A new `TermExtraction` component in its own module, not folded into `app/sentiment.py`, exposing the two operations the team ruled on: tokenize, and filter to significant terms.

## Q3 — Does the HTTP read layer move out of `routes.py`?

`routes.py` is 387 lines, the largest file and the highest fan-out in the system,
and it is where every new endpoint lands by default. The new endpoints are two
reads on a new `/v2` prefix, and the team ruled that reads call the query layer
directly rather than through `service`.

A. **Add the two handlers to `routes.py`** behind a new `v2_router`, keeping one
   HTTP surface file. Matches how `v1_router` already works there
B. **A new `AnalyticsRoutes` component in its own module**, mounted by `main.py`,
   so the new surface does not grow the largest file further
C. Other (please specify)

[Answer]: A. The two handlers join `routes.py` behind a new `v2_router`; no new HTTP component.

## Q4 — Who owns the index and migration change?

The migration and the three indexes live in `db.py`, which already owns all DDL and
the in-place migration, and which carries TD-1 — the rebuild silently drops every
index. The team ruled that `_rebuild_analyses` must re-create the indexes
explicitly as statements after the copy.

A. **`db.py` keeps ownership**, and the fix is a change inside an existing
   component rather than a new one. The three indexes have no separate owner
B. **A new `SchemaMigration` component**, splitting DDL out of `db.py`
C. Other (please specify)

[Answer]: A. `db.py` keeps ownership of the migration and the three indexes; the TD-1 fix is a change inside an existing component.

## Q5 — Does the view script become a component of `WebUI`, or its own?

`app.js` is 201 lines and will gain the analytics view, the nav, view switching and
the two fetches. The existing `WebUI` component owns `index.html` and `app.js`
together.

A. **`app.js` stays inside `WebUI`**, which grows. No new component; the Web UI
   remains "the page and its one script"
B. **A separate `AnalyticsView` component** for the analytics markup and behaviour,
   as a second script file, with `WebUI` owning the shell
C. **`AnalyticsView` as a logical component of the same `app.js` file** — the
   boundary is drawn in the catalogue and the code stays one file
D. Other (please specify)

[Answer]: A. `app.js` stays inside the Web UI component, which grows. No second script file.

## Q6 — What does the analytics component own as entities?

Domain Design captures entities at **ownership plus shape** level only. The
analytics aggregate is computed, never stored, so the question is whether it has
entities at all.

A. **No stored entities.** The component owns computed value shapes only
   (`AnalyticsSummary`, `AnalyticsSeries`, `TermList`), and every *persisted* entity
   stays owned by `Persistence and Schema`. The catalogue records these as the
   component's entities with a computed, not persisted, lifecycle
B. **No entity entries at all** — the component owns nothing persisted, so its
   `entities:` list is empty and the value shapes are named in its `behaviour`
C. Other (please specify)

[Answer]: A. No stored entities; computed value shapes with a computed lifecycle, every persisted entity staying with Persistence and Schema.

## Q7 — Where does the R-01 fix belong?

Q5 at Practices Discovery ruled this feature **fixes R-01**, deciding the
connection's thread affinity and lifecycle explicitly. `get_connection`
(`app/routes.py:92`) is the only place the `sqlite3` driver and the connection
lifecycle are touched anywhere.

A. **The HTTP API Surface component owns it**, because that is where the connection
   is created and closed — the fix is local to that component and no boundary moves
B. **Persistence and Schema owns it**, moving connection lifecycle down to where
   the driver lives
C. Other (please specify)

[Answer]: A. The HTTP API Surface component owns the R-01 fix, because `get_connection` is the only place the `sqlite3` driver and connection lifecycle are touched.

## Q8 — Does any existing component boundary move?

`service.py` holds no read function at all, and the team ruled that reads go
`route → read module` and never through `service`. That is an existing boundary
becoming explicit rather than moving.

A. **No boundary moves.** `service` keeps writes and engine calls; reads never
   entered it, so nothing changes shape — the arrangement is simply recorded
B. **Formalize `service` as write-only** and record the read path as its own edge,
   which makes the acyclic property checkable rather than assumed
C. Other (please specify)

[Answer]: A. No existing boundary moves; the route-to-read-module edge is recorded in the catalogue.

## Consolidated Summary Confirmation

- **Three new components**: `AnalyticsRead` (aggregate reads and the response shapes), `TermExtraction` (the tokenizer and the significant-term filter), and the analytics view as a growth of the existing Web UI component rather than a new name.
- **`TermExtraction` is its own stdlib leaf in its own module**, not folded into `app/sentiment.py`. It exposes two distinct operations, so the offline engine's scoring is unchanged by the analytics stopword list.
- **The two HTTP handlers join `routes.py` behind a new `v2_router`.** No new HTTP component, and the file's existing size caveat is recorded rather than relieved.
- **`db.py` keeps ownership** of the migration and the three indexes; the index-drop defect is fixed inside an existing component.
- **`app.js` stays inside Web UI.** No second script file.
- **The analytics component owns no stored entities** — computed value shapes only, with a computed lifecycle. Every persisted entity stays with Persistence and Schema.
- **The HTTP API Surface component owns the R-01 fix**, because that is where the connection is created and closed. No boundary moves to accommodate it.
- **No existing component boundary moves.** `service` keeps writes and engine calls; the route-to-read-module edge is recorded as an edge rather than a restructure.
- **The twelve existing components are listed alongside the two new ones**, using the names `component-inventory.md` already established so the two artifacts agree.
- **Nine ADRs**, each with Context, Decision, Consequences and Alternatives Rejected, with the rejected options drawn from this file's own option blocks.
- **Seven platform-obligation stories are not components.** The lockfile, verification script, scanning, LICENSE, `ruff` rule set, `target-version` and README are repository-level tooling and documentation, so a component model is the wrong instrument; they are marked `N/A` with a named destination and remain owned by the story set.
- **`US5.2` is declared `N/A` with a dated reason** — the User Stories triage merged it into `US5.1`, so it carries no story heading, but the sensor still reads its id from the merge note and its acceptance criteria.
- **Entity capture is ownership plus shape only**, with that limitation stated in the artifact so no later stage reads the catalogue as a schema.
- **The three indexes are schema artifacts, not entities**, recorded where they are owned.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
