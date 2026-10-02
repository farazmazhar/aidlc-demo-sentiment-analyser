# Constraint Register

| ID | Type | Constraint | Source |
|----|------|------------|--------|
| C-1 | Technical | Reuse the existing SQLite database and its access code; analytics adds tables/indexes only, via an additive, idempotent migration, never a destructive change | [Q1] [desc] |
| C-2 | Technical | Reuse the `SentimentClient` interface and service layer; analytics reads stored rows and does not call the engine | [Q1] [desc] |
| C-3 | Technical | The analytics view is added to the existing single-page UI and static asset serving | [Q1] [desc] |
| C-4 | Technical | The new endpoints follow the existing `/v1` JSON API conventions and the single error envelope | [Q1] [desc] |
| C-5 | Technical | No new external service; analytics is computed in-process from stored rows | [desc] |
| C-6 | Technical | Prefer the Python standard library; the project caps runtime dependencies at two | [Q3] |
| C-7 | Organizational | One developer; no second human reviewer in this project, so stage reviews are advisory and review-before-land is self-review plus agent review | [Q3] [Q5] |
| C-8 | Organizational | No change freeze, no competing priorities, and no external budget | [Q4] [Q5] |
| C-9 | Regulatory | Privacy obligations apply: submitted/imported text may be personal data, stored locally, and sent to OpenRouter in live mode | [Q2] |
| C-10 | Regulatory | Keep the app localhost-only; any non-loopback bind, hosted deploy, or change to the authentication posture needs a fresh threat model (project `## Mandated`) | [Q6] |
| C-11 | Regulatory | Never commit, log, print, or paste a real credential; the only permitted locations are the gitignored `config.local.toml` and process memory (project `## Forbidden`) | (project rule) |
| C-12 | Schedule | Soft target to land the work in one short work session; no fixed deadline | [Q4] |
