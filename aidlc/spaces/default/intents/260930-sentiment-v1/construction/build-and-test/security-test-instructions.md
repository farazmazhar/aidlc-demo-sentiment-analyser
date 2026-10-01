# Security Test Instructions — `u1-application`

Security NFRs exist for this unit, so security checks are recorded at the Standard strategy. The
surface is loopback-only and single-user; the checks below target the realistic exposures named in
`nfr-requirements/security-requirements.md` and `nfr-design/security-design.md`.

## Static analysis

```bash
.venv/bin/python -m ruff check app tests
```

The pinned `[tool.ruff]` rule set includes the `S` (flake8-bandit) security rules. Findings are
treated as build failures.

## Secret containment (NFR2.1, NFR2.2, NFR6.3)

| Check | Where | Method |
|---|---|---|
| Credential never rendered | rendered settings, `repr`, `/`, `/v1/health`, `/auth/status` bodies | suite assertions over the rendered output |
| Credential never logged | captured log records (including `record.__dict__`) | suite assertions |
| Credential lives only in the gitignored file or memory | `config.example.toml` is placeholder-only; `config.local.toml` is gitignored | `git check-ignore` asserted in `tests/test_config.py` |
| Rejected credential is dropped | session credential holder | suite assertions over the discard-and-fall-back path |

## Network boundary (NFR1.2, NFR5.1)

- The session autouse `offline_guard` replaces `socket.socket.connect` with a raiser; any outbound
  use fails the run.
- The server binds loopback only through one constant; asserted by the smoke run's `/v1/health`
  probe on `127.0.0.1` and by the bind constant.

## Error-body hygiene (NFR-S1)

- Every app-raised failure uses the single `{code, message}` envelope; no stack trace or internal
  path is returned. Asserted over the error envelope in `tests/test_routes.py`.

## Out of scope, deliberately

Authentication of the app's own API, transport encryption, CSRF defences, and multi-user
authorisation are out of v1 scope because the surface is loopback-only and single-user (C3 / A4).

## How to run

```bash
.venv/bin/python -m ruff check app tests
.venv/bin/python -m pytest -q tests/test_config.py tests/test_routes.py tests/test_session_auth.py tests/test_auth_routes.py
```
