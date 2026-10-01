# Requirements Analysis — Clarifying Questions

Context for every question below: this intent hardens the existing app in `./app` (FastAPI + SQLite,
Python) into v1. The code scan found that the v1 core already exists — engine interface with two
implementations, SQLite persistence, page plus history, `POST /analyze` and `GET /analyses`, an
offline default — and that the open questions are drift, not missing features.

Known constraints already settled elsewhere: the OpenRouter API key is supplied manually in the
gitignored `config.local.toml`; the app stays localhost-only (no cloud, no Docker); the team's
affirmed testing posture is acceptance/API tests first with lower-level unit tests after, an 80% line
coverage floor over the whole application, and `ruff` for formatting and linting.

---

## Q1. What happens to the in-app OpenRouter sign-in flow?

The app currently ships an in-app OpenRouter authorization flow (PKCE with S256) that stores the
credential in process memory: `app/session_auth.py` (263 lines), four `/auth/*` routes, the page's
connection indicator, and 24 of the 52 tests. Your v1 description says the key is supplied manually
in `config.local.toml` and that there is no auth.

- A. Remove it — the key comes only from `config.local.toml`, and the page just shows whether the live engine is connected
- B. Keep it as the primary way to connect, with the config-file key as a fallback
- C. Keep it alongside the config-file key, both supported and documented
- D. Remove the routes but keep the session-credential plumbing for a later version
- X. Other (please specify)

[Answer]: B. Keep it as the primary way to connect, with the config-file key as a fallback

## Q2. What should live mode do when no key is configured?

Today, choosing live mode with no key available is not a failure: the app starts, reports itself
unconnected, and runs the offline engine (`app/config.py:111-123`, asserted in
`tests/test_config.py:70-85`). Your v1 description asks for a clear error naming the config file to
fill in.

- A. Fail fast at startup with an error naming `config.local.toml`, as the v1 description says
- B. Keep today's behaviour: start on the offline engine and say so in the page and `/health`
- C. Start on the offline engine but log a warning, and fail only when a live analysis is attempted
- X. Other (please specify)

[Answer]: C. Start on the offline engine but log a warning, and fail only when a live analysis is attempted

## Q3. Is the intensity score required or best-effort?

The engine is called with a Choice question (label plus per-option probabilities and a confidence)
and a Score question for intensity in −1..1. Today the live client clamps the score and the offline
client uses fixed per-label values.

- A. Intensity is required — every analysis stores a signed −1..1 value
- B. Intensity is best-effort — absent scores are stored as null rather than guessed
- C. Drop intensity from v1 entirely
- X. Other (please specify)

[Answer]: C. Drop intensity from v1 entirely

## Q4. Which model id ships as the default?

The description names the model `typesafe/jev-1.13` with an alias `~typesafe/jev-latest`. The example
config currently pins `typesafe/jev-1.13`.

- A. Pin `typesafe/jev-1.13` as the default (configurable in the config file)
- B. Default to the alias `~typesafe/jev-latest` so the app follows the newest version
- C. No default — the model id must be set explicitly in the config file
- X. Other (please specify)

[Answer]: A. Pin `typesafe/jev-1.13` as the default (configurable in the config file)

## Q5. How should the stored record change, and how does an existing database migrate?

v1 must store text, chosen label, per-label probabilities, confidence, model id, provider and
created_at. Today's table has every field except `provider`, and `data/sentiment.db` already exists
on this machine with rows in it. The confirmed recovery rule is that deleting the local database is
acceptable.

- A. Add the missing column(s) with an in-place migration that runs on startup and keeps existing rows
- B. Keep the current schema and drop `provider`
- C. Recreate the database on a schema change — existing local rows are discarded
- X. Other (please specify)

[Answer]: A. Add the missing column(s) with an in-place migration that runs on startup and keeps existing rows

## Q6. How is the live OpenRouter client covered by tests, given the 80% coverage floor?

No test exercises `app/openrouter_client.py` today; it is 250 lines and the only untested module,
which is why whole-application coverage measures ~70%. The floor you affirmed counts the whole app.

- A. Test it offline: build the request, parse a recorded/synthetic Decisions-API response, and inject the transport so no network is used
- B. As A, plus an opt-in smoke test that hits the real API only when a key and an explicit flag are present
- C. Leave it covered by review plus a manual live run, and do not count it in the floor
- X. Other (please specify)

[Answer]: A. Test it offline: build the request, parse a recorded/synthetic Decisions-API response, and inject the transport so no network is used

## Q7. Do the engine class names change to the names in the description?

The description names the two implementations `DummySentimentClient` and
`OpenRouterJevSentimentClient`; the code calls them `DummyClient` and `OpenRouterClient`, and
`app/main.py:33-34` carries a comment saying no authentication exists at all, which is no longer true.

- A. Rename both classes as the description says and fix the stale comment (touches tests and imports)
- B. Keep the current names and fix only the stale comment
- C. Keep the current names and leave the comment for a later cleanup
- X. Other (please specify)

[Answer]: A. Rename both classes as the description says and fix the stale comment (touches tests and imports)

## Q8. Does v1 keep analysis history forever, or does it need a way to clear it?

Every analysis is stored in the local database and the history view lists it; live mode also sends
the submitted text to OpenRouter. There is no delete, retention or export path today.

- A. Keep everything; no retention or deletion path is needed for v1
- B. Add a way to delete individual rows or clear the history
- C. Add a retention rule (say, keep the newest N) or a documented manual step
- X. Other (please specify)

[Answer]: A. Keep everything; no retention or deletion path is needed for v1

---

## Q9. What happens to the existing intensity column, now that intensity is dropped from v1?

Answer 3 on Q3 removes intensity from the v1 contract, but the table already has an `intensity`
column, the app writes a clamped −1..1 value into it, and existing rows in `data/sentiment.db` hold
values. Answer 1 on Q5 keeps existing rows through an in-place migration. This is the one point where
those two answers touch.

- A. Keep the column and stop writing to it — new rows leave it null, existing rows keep their values
- B. Drop the column in the same in-place migration — existing rows lose their stored intensity
- C. Keep computing and storing it, but stop exposing it in the API and the page
- X. Other (please specify)

[Answer]: A. Keep the column and stop writing to it — new rows leave it null, existing rows keep their values
