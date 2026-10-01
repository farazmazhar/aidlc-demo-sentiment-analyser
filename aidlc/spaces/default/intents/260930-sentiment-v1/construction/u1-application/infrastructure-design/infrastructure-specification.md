# Infrastructure Specification — `u1-application`

## What this unit's infrastructure is

Nothing is provisioned. The deployment target is the developer's own machine, and the unit's
"infrastructure" is the local runtime it depends on: an interpreter, two installed packages, and one
writable file.

| Element | Provisioned by | Notes |
|---|---|---|
| Interpreter | The user's machine | The project declares a minimum version in its manifest |
| Two runtime packages | The project's own install step | No container, no virtual machine, no host configuration |
| The store file | The application, on first run | Created under a local `data/` directory that the repository ignores |
| Loopback port | The application at start | One fixed local port; nothing exposes it beyond the machine |
| Outbound network | The user's machine, only when live mode is used | The one external dependency |

## Decisions

- **No container and no orchestrator.** The constraints rule them out, and a single local process has
  nothing for them to schedule.
- **No environment tiers.** There is one environment: the machine the app runs on. The distinction
  between staging and production does not exist here, so neither does the configuration that would
  express it.
- **No secrets infrastructure.** The one credential lives in a local ignored file or in memory; there
  is no vault, no injected environment variable and no CI secret.
- **The store is not backed up by the platform.** The user owns the file; the accepted recovery is to
  delete it and start again, which is recorded in the project's practices.

## What would be added at a shared deployment

For orientation only: a host, a credential store, a managed database with real migration tooling, and
a network boundary with authentication. None of it is v1, and this unit's design does not pretend to
prepare for it.
