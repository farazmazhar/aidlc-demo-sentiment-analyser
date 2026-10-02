# Feasibility Assessment

## Technical Viability

The work is a brownfield extension of an existing, working app, and every integration surface already exists. The analytics layer reuses four existing parts without rewriting them: the SQLite database and its access code (analytics adds tables/indexes only, via an additive, idempotent migration), the `SentimentClient` interface and service layer (analytics reads stored rows and does not call the engine), the single-page UI and static asset serving, and the `/v1` JSON API conventions and single error envelope. [Q1] [desc]

The two new endpoints and the second page are computable entirely in-process from stored rows, with no new external service, which keeps the change inside the existing localhost-only posture. [desc] There is no cloud component to validate. [Q6]

**Verdict: feasible.** No blocker was identified. The two watch items are the migration mechanism (the app has none today) and the soft timeline.

## AWS Landscape Assessment

Not applicable. The app is localhost-only by project rule; there are no AWS services, accounts, deployment tiers, or IaC, and none are proposed. [Q6] The AWS Well-Architected lens adds nothing to a single-process loopback workload, so no infrastructure assessment is recorded here.

## Compliance Scan

Privacy obligations are in scope: raw submitted/imported text may contain personal data, it is stored locally, and in live mode the same text is sent to OpenRouter. [Q2] PCI-DSS, HIPAA, SOC 2, and data-residency regimes were not identified as applicable. [Q2]

Relevant facts from the existing system:

- The app is single-user, unauthenticated, and bound to loopback by rule, so the trust boundary is the local machine. [Q6] (project.md **## Mandated**: ALWAYS keep the app localhost-only)
- Raw text is stored unencrypted in the gitignored local SQLite file, and there is no retention or delete endpoint today. [Q2]
- The analytics endpoints only read stored rows and compute in-process; they add **no new egress path** and no new external transmission. [Q2] [desc]
- The credential rule stands unchanged: no real credential may be committed, logged, printed, or pasted anywhere under the repository or `aidlc/`; the only permitted locations are the gitignored `config.local.toml` and process memory. (project.md **## Forbidden**)

No compliance blocker is recorded. Any retention/delete work is pre-existing and out of scope for this change unless the user elects to include it.

## Risk Analysis

- **Migration mechanism**: the project has no migration mechanism today, and a schema change is currently handled by recreating the local database; an additive, idempotent migration is therefore net-new work rather than a pattern to copy. [Q7] [desc]
- **Timeline vs scope**: the user set a soft target of one short work session against the full `feature` scope; this is a schedule risk, not a feasibility risk. [Q4]
- **Technical uncertainty**: the user answered "not yet defined" for the biggest technical uncertainty, so the migration, term extraction, and offline rendering remain named unknowns to be pinned in Requirements Analysis and Design rather than assumed settled. [Q7]
- **Test posture**: every new test must run offline with no network and no key, and the existing suite must stay green. [desc]
