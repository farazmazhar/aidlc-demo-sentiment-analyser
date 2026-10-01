# External Dependency Map — `very-cool-sentiment-analysis` v1

Gated items are things outside the team that hold up a Bolt: an external API that must exist, a data
window, an approval lead time, or another team's hand-off.

## Gated items

| Item | Owner | Lead time | Blocks | If it slips |
|---|---|---|---|---|
| None | — | — | — | — |

The human's answer (Q5 = A) is that nothing external holds this build up: no approvals, no data
windows, no other team, and the only outside service is OpenRouter, which the app treats as optional.

## The one outside service, and why it is not a gate

OpenRouter is a runtime dependency of live mode, not a gate on the work:

- The offline engine is the default, so the app builds, runs and passes its whole suite with no key
  and no network.
- The live client is exercised in tests through an injected transport, so the suite never depends on
  the service being reachable.
- A live attempt with no usable key is refused with an instruction naming the config file, which means
  an unavailable service degrades to a clear message rather than a blocked Bolt.
- The key is supplied by the user at their convenience; nothing in the plan waits on it.

## What this means for the plan

The single Bolt has no external prerequisites, so it can start immediately and run to its Definition
of Done without waiting on anyone. The manual live smoke run in the verification command is the only
step that touches the outside service, and it is the one step that can be skipped without invalidating
the rest of the verification.
