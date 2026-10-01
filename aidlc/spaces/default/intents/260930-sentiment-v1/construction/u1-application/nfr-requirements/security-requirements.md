# Security Requirements — `u1-application`

## Requirements

```yaml
requirements:
  - id: NFR2.1
    category: security
    statement: The credential never appears in a rendered setting, a log record or a response body.
    rationale: The key is the only secret the app holds; a leak through a repr, a log line or an error body is the realistic exposure path.
    verification: asserted by the suite over rendered settings, captured logs and response bodies
  - id: NFR2.2
    category: security
    statement: The credential lives only in the gitignored local config file or in process memory.
    rationale: The affirmed project rule forbids committing or pasting a real credential anywhere, including the workflow's own record files.
    verification: the example config is the only tracked credential-bearing file, and it carries a placeholder
  - id: NFR5.1
    category: security
    statement: The server binds the loopback address only.
    rationale: The app has no authentication of its own; binding anywhere else would expose it to the network.
    verification: asserted by the smoke run and by the server's bind configuration
  - id: NFR5.2
    category: security
    statement: No cloud component, container requirement or account system is introduced.
    rationale: The intent's constraints; anything hosted would contradict the local-only promise.
    verification: reviewed at the unit checkpoint
  - id: NFR-S1
    category: security
    statement: Application-raised failures carry a machine code and a message, never a stack trace or an internal path.
    rationale: Error bodies are the other place implementation detail escapes.
    verification: asserted by the suite over the error envelope
```

## Threat notes for a localhost tool

The realistic exposures are: the key leaking into a log or a committed file; the server accidentally
binding a public interface; and text the user submits leaving the machine — which is exactly what live
mode does, by design, and only when the user asks for it.

## Out of scope, deliberately

Authentication of the app's own API, transport encryption, CSRF defences and multi-user authorisation
are out of v1 scope because the surface is loopback-only and single-user. They are recorded here so a
later reader does not mistake their absence for an oversight.
