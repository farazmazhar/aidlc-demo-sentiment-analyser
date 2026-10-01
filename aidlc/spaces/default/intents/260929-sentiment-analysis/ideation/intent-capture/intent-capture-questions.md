## Sources

- [desc] Initial description: "Build \"very-cool-sentiment-analysis\": a small, self-contained local web app for sentiment analysis.\n\nEngine — Jev on OpenRouter (only sentiment engine; no LLM/chat model, no prose step):\n- Model ID: typesafe/jev-1.13 (alias ~typesafe/jev-latest), called via the OpenRouter Decisions API:\n  POST https://openrouter.ai/api/alpha/decisions with Authorization: Bearer <OPENROUTER_API_KEY>.\n- Ask a Choice question with options [\"positive\",\"negative\",\"neutral\"]; read back the selected label, the\n  per-option probabilities, and the confidence. Optionally add a Score question for intensity (-1..1).\n- Branch on the typed result only; never parse free text.\n\nStorage: SQLite in a single local file (data/sentiment.db). Store input text, chosen label, per-label\nprobabilities (JSON), confidence, intensity/score if used, model id, provider, created_at. Include an\ninit/migration step that creates the DB on first run.\n\nTwo modes (important):\n- One interface SentimentClient with two implementations:\n  1) DummySentimentClient — deterministic canned results, NO network, NO API key; DEFAULT for dev and ALL tests.\n  2) OpenRouterJevSentimentClient — the real Jev call.\n- Mode is chosen by a local config file. Default to dummy when no key/config is present; make the active\n  mode visible in logs and a health endpoint.\n- All tests must run fully offline against the dummy; no test may hit OpenRouter or need a key; `dev` must\n  work with zero credentials.\n\nConfig/secrets: I supply the OpenRouter API key MANUALLY in a local config file outside version control\n(e.g., config.local.toml / .env-style). Add it to .gitignore and commit only config.example.toml with a\nplaceholder. Never hardcode, print, log, or store the key. In live mode, if the key file is missing, fail\nwith a clear message naming the file to fill in.\n\nWeb app: minimal — one page (submit text; show label, confidence, probabilities) plus a small history view,\nand a JSON API (POST /analyze, GET /analyses). Localhost only; no auth, no cloud, no Docker.\n\nStack/run: dependency-light, small; prefer TypeScript on Bun/Node. One command to run dev, one to run tests.\nNo external services except OpenRouter in live mode.\n\nAcceptance criteria: dev/test run with no key and no network using the dummy; live mode reads the key from the\ngitignored config file and returns real Jev label+probabilities+confidence; text and full result persist to\nSQLite and show in history; tests cover the dummy path, the DB read/write path, and the request handler, with\nthe OpenRouter client behind the interface and never exercised by tests; committed example config has no secret."
- [scope] Workflow-selected scope: `poc`.

## Q1. What is the core problem this app solves, and what does it let you do that you cannot do today?

A. Nothing comparable exists locally - I want to send short text to a sentiment engine and get a typed label without standing up an LLM chat app.
B. Existing tools are heavyweight or cloud-only - I want a self-contained app that works offline by default and only reaches out when I opt in.
C. I mainly want a reference implementation of the `SentimentClient` interface, with a dummy and a real implementation side by side.
D. I want a reusable local service other tools can POST text to (`POST /analyze`) and read history from (`GET /analyses`).
E. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. Who is the customer, and what pain are they experiencing today?

A. Me alone, as the developer running and testing it.
B. My team's developers, who need a small local example of one interface with a dummy and a live implementation.
C. Whoever reviews or evaluates this exercise, who needs to see both the offline path and the live path work.
D. A team that will use it to tag short pieces of text (feedback, reviews, messages) as they arrive.
E. Not identified
X. Other (please specify)

[Answer]: A

## Q3. Why now - what triggered this piece of work?

A. A planned evaluation exercise (this run is the exercise itself).
B. Wanting to try the Jev decisions API (typed Choice plus probabilities) before committing to it elsewhere.
C. A manual sentiment-tagging chore became frequent enough to be worth automating.
D. An upcoming demo or walkthrough needs a small working local example.
E. Not applicable
X. Other (please specify)

[Answer]: D

## Q4. Who are the stakeholders - who decides scope and priority, who influences it, and is any reporting cadence needed?

A. Only me: I decide everything, and no reporting cadence is needed.
B. I decide; reviewers or evaluators of this work influence the direction.
C. A small group (2-5 people) uses it, and one person sets priority.
D. Not identified
X. Other (please specify)

[Answer]: A

## Q5. The workflow was started with the `poc` scope (minimal depth, 8 of 33 stages). Does that match the product boundary you have in mind?

A. Yes - prove it end to end with minimal ceremony; the stated acceptance criteria are the bar.
B. Narrower - this is only an API-and-storage spike; the web page and history view matter less.
C. Broader - this is the first slice of a product we intend to extend and keep using.
D. Not sure - let's discuss the boundary.
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
