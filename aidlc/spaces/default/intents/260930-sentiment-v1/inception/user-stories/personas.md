# Personas — `very-cool-sentiment-analysis` v1

One persona, per the answered story plan (Q1 = A). The operator and the API-client facets are hats
this same person wears, not separate personas.

## P1 — The local user

**Who they are.** One person working on their own machine. They started this tool because they wanted
sentiment scoring they could run locally without shipping text to a service they do not control, and
they are willing to supply an API key when they want the live model.

**Goals**

- Score a piece of text and get a clear answer: which of `positive` / `negative` / `neutral`, how
  confident, and what the alternatives scored.
- Keep the results around and look back over them.
- Stay offline by default, and switch to the live model deliberately, only when they choose to.
- Know at a glance which engine answered — the offline stand-in or the live model.
- Install, configure, and run the whole thing themselves, with no accounts and nothing hosted.

**Pain points**

- An engine that answers offline while the page implies it is connected — they cannot tell whether a
  result came from the real model.
- A missing or rejected key that surfaces as a stack trace instead of an instruction naming the file
  to fill in.
- Losing stored results to a schema change.
- Being asked to accept a boundary behaviour (an empty result, a bad limit) that nobody defined.

**Context**

- Runs `uvicorn` locally, binds loopback only, opens the page in a browser.
- Owns the key: either in the gitignored `config.local.toml`, or obtained through the in-app
  OpenRouter sign-in, which keeps it in memory for the session.
- Reads and edits the repository; comfort with `pytest` and a config file is assumed.
- **Desktop browser**, one window at a time: the page declares a viewport and no responsive layout,
  so a narrow or mobile viewport is a known gap rather than a supported context.
- **Short texts, mostly English**: there is no length limit and no language handling today, and the
  provider's own text limit is an open question in the requirements.
- **The offline engine is a stand-in, not a model**: in offline mode the label comes from keyword
  rules with fixed probabilities, which is why knowing *which* engine answered matters.
- **First run versus returning use**: the first run has no config and no database, and the page loads
  its history before the user acts — the empty state and the returning state are different moments.

**Priority ranking.** P1 is the only persona, so every story is primarily for them; nothing is
ranked below another persona.

## Relationships

None. One user, no tenancy, no sharing, no second role to hand work to.
