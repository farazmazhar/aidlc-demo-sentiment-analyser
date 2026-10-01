# Business Rules — `u1-application` (Functional Design)

## Rules

The decision logic of the unit, as numbered rules. Each rule is stated once and referenced by id; the
`BR{group}.{seq}` ids are the targets acceptance criteria trace to.

```yaml
rules:
  - id: BR1.1
    statement: With no configuration and no key, the app resolves to the offline engine.
    category: policy
    applies_to: EngineSettings
    trigger: process start
    logic: IF no config file exists OR neither a config key nor a session credential is usable, THEN mode = offline.
    violation_behaviour: none — this is the default path
    source: FR1.1
  - id: BR1.2
    statement: A session credential activates the live engine regardless of the file's mode.
    category: policy
    applies_to: EngineSettings
    trigger: engine resolution while a session credential exists
    logic: IF a session credential is present and usable, THEN mode = live and the credential is the key.
    violation_behaviour: none
    source: FR1.2, FR5.1
  - id: BR1.3
    statement: With no session credential, a configured live mode with a key activates the live engine.
    category: policy
    applies_to: EngineSettings
    trigger: engine resolution
    logic: IF no session credential exists AND the file sets live mode AND it carries a key, THEN mode = live.
    violation_behaviour: none
    source: FR1.2
  - id: BR1.4
    statement: A live attempt with no usable key is refused with an instruction naming the config file.
    category: validation
    applies_to: a submission
    trigger: an analysis submitted while live was requested and no key is usable
    logic: >
      IF live mode was requested AND no usable key exists, THEN refuse the submission with an error
      naming the config file to fill in, using the single error envelope; nothing is stored.
    violation_behaviour: the request fails; the app keeps running on the offline engine
    source: FR1.3
  - id: BR1.5
    statement: The default model id is typesafe/jev-1.13 unless configured otherwise.
    category: policy
    applies_to: EngineSettings
    trigger: configuration load
    logic: IF the config file names no model, THEN model = typesafe/jev-1.13.
    violation_behaviour: none
    source: FR1.4

  - id: BR2.1
    statement: The engine is asked a choice question whose options are exactly positive, negative and neutral.
    category: constraint
    applies_to: the live engine call
    trigger: a live analysis
    logic: IF the live engine is called, THEN the question carries exactly the three allowed labels as its options.
    violation_behaviour: the response cannot be read; the attempt fails rather than guessing
    source: FR2.2
  - id: BR2.2
    statement: A result is read only from the typed answer, never parsed from free text.
    category: constraint
    applies_to: the engine result
    trigger: reading an engine response
    logic: >
      IF the answer cannot be read as a selected label plus a probability per label plus a confidence,
      THEN the attempt fails; no label is ever inferred from prose.
    violation_behaviour: the attempt fails and nothing is stored
    source: FR2.3
  - id: BR2.3
    statement: Probabilities are a value per label and the chosen label is one of the three.
    category: validation
    applies_to: a result
    trigger: a result is produced
    logic: IF a result lacks a value for any of the three labels OR its label is not one of them, THEN the result is invalid.
    violation_behaviour: the attempt fails
    source: FR2.4

  - id: BR3.1
    statement: The store is created on first run.
    category: constraint
    applies_to: the local store
    trigger: process start with no store
    logic: IF no store file exists, THEN create it with its schema before serving any request.
    violation_behaviour: startup fails loudly
    source: FR3.1
  - id: BR3.2
    statement: A stored row carries text, label, probabilities, confidence, model, provider and timestamp.
    category: constraint
    applies_to: AnalysisRecord
    trigger: a successful analysis
    logic: IF an analysis succeeds, THEN persist exactly those attributes.
    violation_behaviour: the write fails and the error surfaces
    source: FR3.2, FR3.5
  - id: BR3.3
    statement: A schema change is applied in place and existing rows survive it.
    category: constraint
    applies_to: the local store
    trigger: process start against an older store
    logic: IF the store lacks an attribute the contract requires, THEN add it in place without discarding rows.
    violation_behaviour: startup fails loudly rather than silently discarding data
    source: FR3.3, US7.1
  - id: BR3.4
    statement: A value the contract no longer produces is never invented for an existing row.
    category: constraint
    applies_to: AnalysisRecord.intensity
    trigger: reading or writing a row
    logic: IF an attribute is no longer produced, THEN leave it unset on new rows and unchanged on old ones; never default it.
    violation_behaviour: the write fails rather than fabricating data
    source: FR3.6
  - id: BR3.5
    statement: History is read newest-first, limited by the caller.
    category: policy
    applies_to: the history read
    trigger: a history request
    logic: IF a limit is given, THEN return at most that many rows, newest first; IF none is given, THEN apply the documented default.
    violation_behaviour: none
    source: FR3.4, FR4.2
  - id: BR3.6
    statement: A limit below one, or not a number, is rejected rather than clamped.
    category: validation
    applies_to: the history request
    trigger: a history request with a limit
    logic: IF limit < 1 OR limit is not numeric, THEN refuse with the validation code; never silently change the value.
    violation_behaviour: the request fails; nothing is read
    source: FR4.6

  - id: BR4.1
    statement: Empty or whitespace-only text is refused and nothing is stored.
    category: validation
    applies_to: a submission
    trigger: a submission whose text is empty after trimming
    logic: IF the text is empty after trimming, THEN refuse with the invalid-text code and store nothing.
    violation_behaviour: the request fails and no row exists afterwards
    source: FR4.5
  - id: BR4.2
    statement: The data routes are served under the versioned prefix.
    category: constraint
    applies_to: the HTTP surface
    trigger: any request
    logic: IF a data route is requested, THEN it is served under the versioned prefix the contract pins.
    violation_behaviour: an unversioned path is not found
    source: contract-summary.md
  - id: BR4.3
    statement: Every app-raised failure uses the single error envelope.
    category: constraint
    applies_to: every response the app raises
    trigger: an app-raised failure
    logic: >
      IF the app refuses a request, THEN the body carries the contract's envelope — exactly the
      machine code and the human-readable message, with no field-level array (the contract's
      ErrorEnvelope sets additionalProperties: false, so the message itself names the offending
      field).
    violation_behaviour: the response is a defect regardless of status code
    source: FR4.5, FR4.6, FR1.3
  - id: BR4.4
    statement: Health reports the active mode and connection state without credential material.
    category: constraint
    applies_to: the health response
    trigger: a health request
    logic: IF health is requested, THEN report the active engine and whether the live engine is connected, with no credential material.
    violation_behaviour: none
    source: FR4.3, FR1.6

  - id: BR5.1
    statement: The credential never appears in a rendered setting, a log record or a response body.
    category: authorization
    applies_to: every surface
    trigger: rendering, logging or responding
    logic: IF a value that can hold a credential is rendered or logged, THEN it renders the redaction marker.
    violation_behaviour: a leak is a defect; the value is never emitted
    source: FR1.5, NFR2
  - id: BR5.2
    statement: The server binds loopback only.
    category: constraint
    applies_to: the server
    trigger: server start
    logic: IF the server starts, THEN it listens on the loopback address only.
    violation_behaviour: startup fails rather than binding a public interface
    source: FR4.7, NFR5

  - id: BR6.1
    statement: A credential obtained through the sign-in flow is held in memory for the session only.
    category: constraint
    applies_to: SessionCredential
    trigger: a completed sign-in
    logic: IF sign-in completes, THEN hold the credential in memory; nothing is written to disk.
    violation_behaviour: none
    source: FR5.2
  - id: BR6.2
    statement: A credential the provider rejects is discarded and the app falls back to the offline engine.
    category: policy
    applies_to: SessionCredential
    trigger: a rejected credential
    logic: IF the provider rejects the credential, THEN discard it and resolve to the offline engine; never retry it.
    violation_behaviour: none
    source: FR5.4

  - id: BR7.1
    statement: Line coverage of the whole application is at least the affirmed floor.
    category: constraint
    applies_to: the test run
    trigger: a test run with coverage enabled
    logic: IF measured line coverage is below the floor, THEN the run fails.
    violation_behaviour: the check fails
    source: NFR4
  - id: BR7.2
    statement: The live engine is exercised without network access.
    category: constraint
    applies_to: the live engine
    trigger: a test that exercises the live path
    logic: IF the live path is tested, THEN its transport is injected so no network call is made.
    violation_behaviour: the test fails loudly
    source: NFR4, NFR1

  - id: BR8.1
    statement: The project's own descriptions match what the project does, corrected in the change that alters it.
    category: policy
    applies_to: the README and the dependency manifest
    trigger: a change to the dependencies, the behaviour they describe, or the authentication story
    logic: >
      IF a change makes a documented statement false — the dependency list, the runtime package
      count, the authentication description — THEN correct the statement in the same change.
    violation_behaviour: the statement is stale and misleading; the change is incomplete
    source: NFR3, FR6.2
  - id: BR8.2
    statement: The two engine implementations carry their v1 names.
    category: constraint
    applies_to: the engine implementations
    trigger: any reference to them
    logic: IF an engine implementation is named, THEN it is named DummySentimentClient or OpenRouterJevSentimentClient.
    violation_behaviour: none functionally; the naming requirement is unmet
    source: FR6.1
  - id: BR8.3
    statement: The code passes the configured formatting and linting rules, including the security set.
    category: constraint
    applies_to: the code
    trigger: a check run
    logic: IF the configured rules report a violation, THEN the check fails.
    violation_behaviour: the check fails
    source: C4
```

## Rules summary

| Group | Rules | Area |
|---|---|---|
| BR1 | BR1.1 – BR1.5 | Configuration and engine resolution, including the live-attempt refusal |
| BR2 | BR2.1 – BR2.3 | The engine contract: typed answers only |
| BR3 | BR3.1 – BR3.6 | Persistence, migration and the history boundary |
| BR4 | BR4.1 – BR4.4 | The HTTP boundary and its envelope |
| BR5 | BR5.1 – BR5.2 | Secret containment and loopback-only operation |
| BR6 | BR6.1 – BR6.2 | The session credential's lifecycle |
| BR7 | BR7.1 – BR7.2 | The quality floor and the offline live-client test |
