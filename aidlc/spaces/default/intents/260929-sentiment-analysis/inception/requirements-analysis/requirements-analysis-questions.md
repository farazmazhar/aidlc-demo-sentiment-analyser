# Requirements Analysis — Clarifying Questions

## Q1. Which Python stack should the app use for the web layer, SQLite access, and tests?

The original description preferred TypeScript on Bun/Node; Python is now the choice, so these are open.

A. FastAPI + uvicorn for HTTP, the standard-library `sqlite3` module for storage, pytest for tests (dev: `uvicorn app:app --reload`; test: `pytest`)
B. Flask + the standard-library `sqlite3` module + pytest
C. Standard library only - `http.server` for HTTP, `sqlite3` for storage, `unittest` for tests (no third-party runtime dependencies)
D. FastAPI + SQLAlchemy (or SQLModel) for storage + pytest
E. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. How should the local config file be shaped, and what gets committed?

A. `config.local.toml` (gitignored) holds the key and the mode; `config.example.toml` is committed with a placeholder
B. `.env` (gitignored) holds `OPENROUTER_API_KEY` and the mode; `.env.example` is committed
C. Support both, with the TOML file winning
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. What rule should the dummy client use so its results are deterministic?

A. Keyword lists - a few positive and negative words decide the label, everything else is neutral, with fixed per-label probabilities
B. A hash of the input text picks a stable label and probability triple from a small canned set
C. One fixed canned label/probability triple reused for every input
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q4. Should each analysis also record an intensity score (the optional Score question, -1..1)?

A. Yes - ask Jev for a Score alongside the Choice and store `intensity`; the dummy returns a fixed value
B. Yes - but derive it locally from the chosen label and confidence instead of asking Jev
C. No - store only label, probabilities, and confidence for now
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q5. What should the JSON API return, and how should history be read?

A. `POST /analyze` returns the full stored record (id, text, label, probabilities, confidence, intensity, model, provider, created_at); `GET /analyses` returns newest-first with `?limit=` (default 50)
B. Same record shape; `GET /analyses` returns every row newest-first, with no limit parameter
C. Same record shape; `GET /analyses` returns newest-first with `?limit=` and `?offset=`
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- Q1 - Python with FastAPI + uvicorn for HTTP, the standard-library `sqlite3` module for storage, and pytest for tests; dev and test each stay a single command.
- Q2 - Config lives in a gitignored `config.local.toml`; a placeholder-only `config.example.toml` is committed.
- Q3 - The dummy client decides by keyword lists (a few positive and negative words, neutral otherwise) with fixed per-label probabilities.
- Q4 - Every analysis records an intensity score taken from Jev's Score question alongside the Choice; the dummy returns a fixed value.
- Q5 - `POST /analyze` returns the full stored record; `GET /analyses` returns newest-first with `?limit=` (default 50).
- The stated acceptance criteria from the original request still stand: offline dev/test on the dummy, live mode reading the key from the gitignored config, SQLite persistence shown in history, tests never exercising the OpenRouter client, and no secret in the committed example config.

Does this all look correct before I generate the requirements artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
