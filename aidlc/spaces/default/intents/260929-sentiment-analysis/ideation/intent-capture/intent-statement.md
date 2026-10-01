## Problem Statement

The developer has no local way to send a short piece of text to a sentiment engine and read back a typed sentiment label; doing it today would mean standing up an LLM chat app. [Q1] What is wanted instead is a small, self-contained local web app for sentiment analysis, run on the developer's own machine. [desc]

## Target Customer

The developer alone, as the person running and testing the app and the only user of it. [Q2] [Q1]

## Success Metrics

- `dev` and `test` run with no API key and no network access, using the dummy sentiment client. [desc]
- Live mode reads the OpenRouter key from a local, gitignored config file and returns the real Jev label together with per-label probabilities and confidence. [desc]
- Submitted text and the full result persist to SQLite (`data/sentiment.db`) and appear in the history view. [desc]
- Tests cover the dummy path, the SQLite read/write path, and the request handler, with the OpenRouter client behind the `SentimentClient` interface and never exercised by tests. [desc]
- The committed example config carries no secret; the key itself is supplied manually outside version control. [desc]
- These acceptance criteria are the bar for the work. [Q5]

## Initiative Trigger

An upcoming demo or walkthrough needs a small, working local example. [Q3]

## Initial Scope Signal

The workflow-selected scope is `poc` (minimal depth, 8 of 33 stages). [scope]
The user-confirmed product boundary matches it: prove the app end to end with minimal ceremony, judged against the success metrics above. [Q5]

## Assumptions & Open Questions

None.
