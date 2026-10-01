# Discovered Rules

<!-- Affirmed at the practices-discovery interview on 2026-09-30 for intent 260930-sentiment-v1. -->
<!-- Exactly three constraints were stated by the human; behaviour the scan merely observed is not promoted to a rule, and stays a convention in team-practices.md. -->
<!-- Each non-blank line below that is not a comment or a heading is a rule, and is promoted verbatim under the matching heading in aidlc/spaces/default/memory/project.md at the affirmation gate. -->

## Mandated

ALWAYS keep the app localhost-only: bound to loopback (127.0.0.1) and unauthenticated by design; any non-loopback bind, hosted deploy or change to the authentication posture requires a fresh threat model.
ALWAYS route every failure the application code raises through the single error envelope; framework-generated routing errors (unknown path, wrong method, missing static asset) keep FastAPI's `{"detail": …}` shape.

## Forbidden

NEVER commit, log, print, paste, or attach a real credential (the OpenRouter key or any future secret) into the repository or any artifact under `aidlc/`; the only permitted locations are the gitignored `config.local.toml` and process memory.
