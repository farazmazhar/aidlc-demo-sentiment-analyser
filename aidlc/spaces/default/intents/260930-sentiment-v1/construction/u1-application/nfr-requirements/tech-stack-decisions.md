# Tech Stack Decisions — `u1-application`

## Decisions

```yaml
decisions:
  - id: NFR3.1
    decision: The runtime stays on two declared dependencies plus the standard library.
    rationale: >
      Two packages (the web framework and the server) plus the standard library's SQLite is the
      project's stated weight budget; every capability v1 adds is expressible within it.
    consequences: >
      No ORM, no migration framework and no HTTP client library: the store is driven directly, the
      schema change is hand-written, and the outbound call uses the standard library. That is more
      explicit code and fewer moving parts.
  - id: NFR3.2
    decision: Test, coverage and lint tooling live under the development extra, never in the runtime list.
    rationale: The story that corrects the documentation requires the runtime count to stay true while these tools are added.
    consequences: Installing for use never pulls a linter; installing for development does.
  - id: NFR-TS1
    decision: Coverage is measured over the whole application with a floor of eighty percent of lines.
    rationale: The affirmed posture; measuring only part of the app would make the floor meaningless.
    consequences: The live client must be covered, which is only possible because its transport is injectable.
  - id: NFR-TS2
    decision: The test runner is the project's existing one, and the lint rules are pinned explicitly rather than left to a tool default.
    rationale: A default rule set drifts between tool versions; an explicit selection is reproducible.
    consequences: The rule set is a reviewed file, and adding a rule is a deliberate change.
```

## Stack, as it stands

| Layer | Choice | Note |
|---|---|---|
| Language | Python | Project-level decision, recorded in the space's memory |
| Web framework | FastAPI | Runtime dependency one |
| Server | Uvicorn | Runtime dependency two, used directly for the local run |
| Storage | the standard library's SQLite | One local file; no ORM, no migration tool |
| Outbound calls | the standard library's HTTP client | Used only by the live engine |
| Tests | pytest | Development extra |
| Coverage | a coverage plugin for the test runner | Development extra |
| Lint and format | ruff, with an explicit rule set including the security rules | Development extra; the affirmed team practice |

## Rejected alternatives

- **An ORM or migration framework**: adds a runtime dependency and hides the in-place migration the
  stories deliberately expose as behaviour.
- **An HTTP client library**: the outbound surface is one POST with a bearer header; the standard
  library covers it without adding weight.
- **A frontend framework**: the page is one document with a handful of states; a framework would add a
  build step and a second toolchain for no behavioural gain.
- **A default lint rule set**: reproducible only until the tool updates; the explicit set is the
  cheaper long-term choice.
