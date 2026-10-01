# Contract Summary — `very-cool-sentiment-analysis` v1

One unit, one boundary. The system is a single `service` unit with no inter-unit edges, so the only
formal contract is the HTTP surface that unit exposes to its local consumers (answer Q1 = A). The
in-process handoff between the analysis service and the engines stays an internal interface and is not
a contract (Q2 = A). The JSON API is pinned at `/v1` with additive-only change (Q3 = B). Errors follow
the single envelope, the outbound live call carries a stated timeout, and there is no automatic retry
(Q4 = A). The single unit owns the spec and changes to it are approved at this stage's gate (Q5 = A).

## Contracts

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---|---|---|---|
| 1 | U1 Application | Internal: the page served by the same unit. External: any local HTTP client on the machine (a script, a browser, the test harness) | Synchronous REST/HTTP, JSON, paths under `/v1` | U1 |

The page's own routes (`/` and the static assets) are part of the same HTTP surface but carry no data
contract beyond serving the page; they are not specified here.

## Contract 1 — the `/v1` JSON API

```yaml
openapi: 3.0.3
info:
  title: Very Cool Sentiment Analysis API
  version: "1.0.0"
  description: >
    Localhost-only sentiment analysis. One server process, one user, no authentication on the API
    itself; the only credential anywhere is the OpenRouter key the app uses outbound when live mode
    is active. Paths are versioned under /v1; changes are additive only.
servers:
  - url: http://127.0.0.1:8000
    description: Loopback only; the server binds no other interface.
paths:
  /v1/analyze:
    post:
      summary: Score one piece of text, store the result and return the stored record
      operationId: analyze
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AnalyzeRequest'
      responses:
        '200':
          description: The stored analysis record, exactly as persisted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnalysisRecord'
        '422':
          description: >
            The text was empty or whitespace only (INVALID_TEXT), or the body failed validation
            (VALIDATION_FAILED). Nothing is persisted.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorEnvelope'
        '503':
          description: >
            A live analysis was attempted with no usable key, or the live engine failed. The message
            names the config file to fill in when the cause is a missing key. Nothing is persisted.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorEnvelope'
  /v1/analyses:
    get:
      summary: List stored analyses, newest first
      operationId: listAnalyses
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            minimum: 1
          description: >
            Maximum rows to return. Absent means the documented default; a value below 1 or a
            non-numeric value is rejected rather than clamped.
      responses:
        '200':
          description: Stored records, newest first
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AnalysisRecord'
        '422':
          description: The limit was below 1 or not a number (VALIDATION_FAILED).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorEnvelope'
  /v1/health:
    get:
      summary: Report the active engine and the live connection state
      operationId: health
      responses:
        '200':
          description: The active mode and connection state, with no credential material
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Health'
components:
  schemas:
    AnalyzeRequest:
      type: object
      required: [text]
      properties:
        text:
          type: string
          description: The text to score; empty or whitespace-only is refused.
      additionalProperties: false
    AnalysisRecord:
      type: object
      required: [id, text, label, probabilities, confidence, model, provider, created_at]
      properties:
        id:
          type: integer
          description: Stable identifier of the stored row.
        text:
          type: string
        label:
          type: string
          enum: [positive, negative, neutral]
        probabilities:
          type: object
          description: One probability per label, keyed by label; every label is present.
          required: [positive, negative, neutral]
          properties:
            positive: { type: number, minimum: 0, maximum: 1 }
            negative: { type: number, minimum: 0, maximum: 1 }
            neutral:  { type: number, minimum: 0, maximum: 1 }
        confidence:
          type: number
          minimum: 0
          maximum: 1
        model:
          type: string
          description: The model that produced the record.
        provider:
          type: string
          description: >
            Which engine produced the record. Every record carries this as a string (it is required);
            a row migrated from a store that predates the column carries the recorded sentinel
            `unknown`, because no engine can be named for it and JSON null would satisfy neither this
            type nor the `required` list.
          enum: [offline, openrouter, unknown]
        created_at:
          type: string
          description: ISO 8601 UTC timestamp ending in Z.
      additionalProperties: false
    Health:
      type: object
      required: [mode, connected]
      properties:
        mode:
          type: string
          enum: [offline, live]
        connected:
          type: boolean
        reason:
          type: string
          description: Present when not connected; never contains credential material.
      additionalProperties: false
    ErrorEnvelope:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
          description: >
            One of the app's machine codes. INVALID_TEXT and VALIDATION_FAILED are today's values for
            the refusals above; the code for a live attempt without a usable key is an open question.
        message:
          type: string
          description: Human-readable text; names the config file when the cause is a missing key.
      additionalProperties: false
```

## Contract ownership

- **Owner.** `U1` owns this spec (answer Q5 = A). A change to it is approved at this stage's gate.
- **Additive changes are safe.** A consumer ignores fields it does not know; adding a field or an
  optional parameter needs no version change.
- **Breaking changes get a new version.** Since the paths are versioned at `/v1`, a change that alters
  an existing field's meaning, removes a field, or changes a status code requires a new prefix, not an
  edit in place.
- **The envelope is one shape.** Every app-raised failure returns `ErrorEnvelope`; a framework-level
  failure (an unmatched path, a wrong method) keeps the framework's own shape and is outside this
  contract.
- **One consumer ships with the server.** The page is served by the same unit, so a breaking change
  that lands the page and the API together is allowed; the version prefix exists to keep the shape
  honest, not to support an installed base.

## Open questions

| Contract | Question | Blocks |
|---|---|---|
| `/v1` JSON API | The machine code a live attempt without a usable key returns, and the exact status (this summary proposes `503` and leaves the code open) | Code Generation for the live-attempt refusal |
| `/v1` JSON API | The numeric default for an absent `limit` on `GET /v1/analyses` | Code Generation for the history route |
| `/v1` JSON API | Whether the `/v1` prefix also applies to the health endpoint, or whether health stays unversioned | Code Generation for the health route |
| `/v1` JSON API | The outbound timeout value for the live call (the contract states that a timeout exists, not its duration) | Code Generation for the live client |
