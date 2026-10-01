# Security Design — `u1-application`

## Design solutions

| Requirement | Design solution |
|---|---|
| NFR2.1 | Redaction by construction: every value that can hold a credential renders a fixed redaction marker in its representation, and the error envelope carries no credential field at all. Tests assert over rendered settings, captured logs and response bodies. |
| NFR2.2 | One credential source order: a session credential, then the local config file. The file is gitignored; the tracked example carries a placeholder. Nothing else in the design can hold a key. |
| NFR5.1 | A single bind address constant, set to the loopback address, used by the server start path and asserted by the smoke check. |
| NFR5.2 | No hosted service, no container and no account: the design has one process and one file. The only outbound traffic is the live call and the sign-in exchange, both user-initiated. |
| NFR-S1 | One error builder maps every app-raised failure to the envelope with a machine code and a message; framework-level failures keep the framework's shape and are out of the app's scope by design. |

## Notes

The design has no authentication of its own, and that is deliberate: the surface is loopback-only and
single-user. The one credential in the system belongs to the user's OpenRouter account, and the design
treats it as a borrowed secret — held briefly, rendered never, logged never.

## Accepted local risks

Recorded so they are visible rather than assumed: no transport encryption (loopback), no CSRF defence
on the connection routes (there is no cross-site context), and the submitted text leaving the machine
only when the user chooses live mode.
