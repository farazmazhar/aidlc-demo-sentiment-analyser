# Entities — `u1-application` (Functional Design)

## Entity model

The entity model for the unit, at ownership-plus-shape depth extended to attribute level. Types are
logical, not language-specific; no storage or framework detail appears here.

```yaml
entities:
  - name: AnalysisRecord
    description: One scored piece of text, as persisted and as returned to a client.
    owner: Persistence
    attributes:
      - name: id
        type: identifier
        required: true
        unique: true
        description: Stable identifier of the stored row.
      - name: text
        type: text
        required: true
        constraints: [not empty after trimming whitespace]
        description: The submitted text, stored as given (trimmed for validation, not for storage).
      - name: label
        type: enumeration
        required: true
        allowed_values: [positive, negative, neutral]
        description: The chosen sentiment label.
      - name: probabilities
        type: map
        required: true
        constraints: [every allowed label present, each value between 0 and 1 inclusive]
        description: Probability per label, keyed by label.
      - name: confidence
        type: number
        required: true
        constraints: [between 0 and 1 inclusive]
        description: The engine's confidence in the chosen label.
      - name: model
        type: text
        required: true
        description: The model that produced the record.
      - name: provider
        type: enumeration
        required: true
        allowed_values: [offline, openrouter, unknown]
        description: >
          Which engine produced the record. `unknown` is the recorded sentinel for a row migrated
          from a store written before the column existed: no engine can be named for it, and the
          value stays a schema-conformant string rather than JSON null or a fabricated engine name.
      - name: created_at
        type: timestamp
        required: true
        constraints: [ISO 8601 in UTC, ending in Z]
        description: When the record was created.
      - name: intensity
        type: number
        required: false
        description: >
          Legacy attribute. The v1 contract no longer produces it; rows written before v1 keep
          whatever value they hold and new rows leave it unset. Never back-filled with an invented
          value.
    constraints:
      - A record exists only for text that passed validation; a refused submission writes nothing.
      - The label is always one of the three allowed values, and probabilities carries all three.
    relationships:
      - target: SessionCredential
        cardinality: none
        direction: n/a
        description: Records carry no reference to the credential used; which engine answered is captured by provider.

  - name: EngineSettings
    description: The resolved engine configuration for the running process.
    owner: Configuration
    attributes:
      - name: mode
        type: enumeration
        required: true
        allowed_values: [offline, live]
        default: offline
        description: The engine the app intends to use.
      - name: model
        type: text
        required: true
        default: typesafe/jev-1.13
        description: The model id used by the live engine.
      - name: api_key
        type: secret
        required: false
        description: The OpenRouter credential. Never rendered, logged or persisted; every form that could hold it renders a redaction marker.
    constraints:
      - A key never appears in a rendered setting, a log record or a response body.
      - With no key available the resolved mode is offline, whatever the file requests.
    relationships:
      - target: SessionCredential
        cardinality: one-to-zero-or-one
        direction: SessionCredential overrides the file's key when present
        description: A session credential takes precedence over the configured key.

  - name: SessionCredential
    description: A credential obtained through the in-app sign-in, held for the session only.
    owner: WebSurface
    attributes:
      - name: token
        type: secret
        required: true
        unique: true
        description: The credential value; never written to disk and never rendered.
      - name: obtained_at
        type: timestamp
        required: true
        description: When the credential was obtained.
      - name: expires_at
        type: timestamp
        required: false
        description: When the credential stops being usable, when the provider states it.
    constraints:
      - Lives in process memory only; it does not survive a restart.
      - A credential the provider rejects is discarded rather than retried.
    relationships:
      - target: EngineSettings
        cardinality: one-to-zero-or-one
        direction: overrides
        description: While present, the session credential is the engine's key.
```

## Summary

Three entities. `AnalysisRecord` is the only durable one and the only one with a legacy attribute
(`intensity`) whose removal is deliberately partial: existing rows keep their value, new rows do not
set it. `EngineSettings` is resolved at startup and carries the one secret the app may hold from the
file. `SessionCredential` is the in-memory alternative that outranks the file key while it exists.

Probabilities are a map keyed by label rather than a list, so a reader cannot confuse position with
meaning; the label set is closed at three values.
