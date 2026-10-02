## Q1. Which existing parts must the analytics layer integrate with, without rewriting them? (select all that apply)

A. The existing SQLite database and its schema/access code (analytics adds tables/indexes only, via an additive, idempotent migration).
B. The existing SentimentClient interface and service layer (analytics reads stored rows; it does not call the engine).
C. The existing single-page UI and static asset serving (the analytics view is added alongside it).
D. The existing /v1 JSON API conventions and the single error envelope (the new endpoints follow them).
E. All of the above
X. Other (please specify)

[Answer]: E

## Q2. Are there regulatory or compliance requirements in scope (PCI-DSS, HIPAA, SOC 2, GDPR, data residency)?

A. None identified — the app is localhost-only, single-user, and holds only the text the operator submits or imports.
B. Privacy obligations apply because raw submitted/imported text may contain personal data and is stored locally (and sent to OpenRouter in live mode).
C. Not applicable
D. Not identified
X. Other (please specify)

[Answer]: B

## Q3. What is the team's current tech stack and skill profile?

A. One developer working in Python with FastAPI + SQLite, preferring the standard library and a two-runtime-dependency cap.
B. A small Python team; FastAPI is familiar; SQLite is the only datastore.
C. Not identified
X. Other (please specify)

[Answer]: A

## Q4. What budget and timeline constraints apply?

A. No external budget (everything runs locally); no fixed deadline.
B. No budget, but a soft target to land it in one short work session.
C. Not yet defined
X. Other (please specify)

[Answer]: B

## Q5. Are there organizational blockers (change freeze, competing priorities, review requirements)?

A. None — one developer, no change freeze, no competing priorities, and no second human reviewer in this project.
B. The repository has a pending branch merge (v1-classic) that must be considered before this work lands.
C. Not identified
X. Other (please specify)

[Answer]: A

## Q6. What AWS services or accounts are currently in use (or is this fully non-cloud)?

A. None — the app is localhost-only by rule; no cloud services, accounts, or deployment tiers.
B. Not applicable
C. Not identified
X. Other (please specify)

[Answer]: A

## Q7. What is the biggest technical uncertainty in this work?

A. Making the SQLite migration additive and idempotent against the existing schema without touching existing rows.
B. Extracting "significant terms" in-process with a simple tokenizer and no external service.
C. Rendering the time series and top-term lists in the existing page offline, without adding a front-end library.
D. Keeping every new test offline (no network, no key) while the existing suite stays green.
E. Not yet defined
X. Other (please specify)

[Answer]: E

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
