**Collaborator:** aidlc-devsecops-agent

## Contribution

Security and supply-chain review of the lead draft. I read the four draft artifacts, the
reverse-engineering artifacts, the scan handoff and the application source/manifests
directly; every claim below carries the file I read it in. I did **not** run the suite,
the app or a scanner — the draft's own "no execution evidence" caveat applies to me too,
and I keep the empirical layer separate from the code-reading layer.

### 0. What the code actually guarantees about the secret (checked, not assumed)

| Property | Status | Anchor |
|---|---|---|
| Key lives in a gitignored file or process memory only | holds | `.gitignore` (`config.local.toml`, `/data/`); `app/config.py:23`; `app/session_auth.py:1-9,182-230`; `tests/test_config.py:126-143` (shells out to `git check-ignore`) |
| Never rendered | holds | `Settings.__repr__` (`app/config.py:47-55`), `SessionCredential.__repr__` (`app/session_auth.py:131-138`), `OpenRouterClient.__repr__` (`app/openrouter_client.py:93-97`); asserted in `tests/test_config.py:96-113` and `tests/test_session_auth.py:182-183` |
| Never logged | holds | the only startup line logs `mode`/connection only (`app/main.py:76-81`); no `logger` call anywhere takes `api_key`; asserted over `caplog` records incl. `record.__dict__` (`tests/test_config.py:109-112`) |
| Never in a response body | holds by construction; test coverage is narrower than the draft says (see C1) | `effective_connection()` returns `connected/source/mode/model/reason` only (`app/service.py:51-57`); `RECORD_FIELDS` has no key field (`app/models.py:20-30`); test covers `/`, `/health`, `/auth/status` (`tests/test_auth_routes.py:118-127`) |
| Never committed **by any route other than `config.local.toml`** | **does not hold** | `.gitignore` protects one exact path; `aidlc/` records, `codekb/`, `README.md`, `app/`, `tests/` are all tracked, so a key pasted into any of them commits by default |
| Any detection if it is committed anyway | **absent** | no secret scanning, no pre-commit hook, no CI, no remote (`ls -a` at repo root; `git remote -v` empty; `glob` found no `.github/`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `.gitlab-ci.yml`) |

Two honest qualifications the draft should carry:

- **"Redacted" means "not rendered", not "not obtainable".** `Settings.api_key` is a public
  dataclass field (`app/config.py:42`) and `OpenRouterClient._api_key` a plain attribute
  (`app/openrouter_client.py:89`); `dataclasses.asdict(settings)`, `vars(client)` or a
  failure that dumps locals would expose the key. The tests pin repr/log/body surfaces
  only, which is the right surface — just don't write "by construction" as if it were a
  memory-safety property.
- **The in-memory session credential is process-wide, not per-client.** With no auth on any
  route (`app/main.py:33-36` states the design), any local process or user that can reach
  loopback is "the session" and can spend the key via `POST /analyze`
  (`app/routes.py:86-96`). That is a deliberate consequence of localhost-only, not a bug —
  but it is exactly why "localhost only" belongs in `project.md` rather than in a README
  sentence alone.

### 1. Secret handling — the finding the interview should not skip

The design is above the norm for a project at this maturity, but the *unprotected* route
is the one this workflow itself creates: AI-DLC artifacts are **committed by design**
(`.gitignore` states the committed-vs-ignored split; `AGENTS.md` "Commit the `aidlc/` workspace
tree"). Framework rules already forbid secrets in the audit trail — `audit-format.md`
"Format Standards" says "No sensitive data (credentials, PII, secrets)" and the `append-raw`
note repeats "exclude credentials, PII, and secrets" — but nothing mechanically checks a
`codekb/`, `evidence.md`, `memory.md` or review file. A live key quoted into any of those
lands in git, and unlike a code bug it is **irreversible**: removing it later does not
un-compromise it (the hub's own knowledge says revoke → rotate → clean history,
`devsecops-pipeline-patterns.md` "Secret Detection").

Concrete, checkable detail that makes the practice line actionable rather than aspirational:
four fake keys in the tree already match OpenRouter's real key shape — `sk-or-v1-` plus
32 hex characters at `tests/test_config.py:23`, and shorter variants at
`tests/test_auth_routes.py:28-29`, `tests/test_session_auth.py:26`, `tests/test_routes.py:136`
(plus the `sk-or-v1-...` placeholder at `README.md:96`). Any prefix/entropy secret scanner
adopted later will fire on `tests/test_config.py:23`; the practice must pair "scan" with
"allowlist these known-fixture literals", or the first scan is noise the team learns to ignore.

**Recommended draft text (Code Style area, new enforcement bullet):**
> **Secrets (observed, and to be made binding).** The only place a real credential may live
> is the gitignored `config.local.toml` or process memory; no artifact, journal, codekb
> note, test, README or commit may carry one. Redaction is by `__repr__` for every object
> that can hold a key. Detection today is zero.

**Recommended hard constraint** (see Positions): one `## Forbidden` line in `project.md` is
warranted — this is the only security property in the repo where a single mistake is
permanent, and it is cheap to state and cheap to keep. I would *not* mint a hard constraint
for the other security-adjacent conventions (parameterised SQL, no pydantic in `app/`, one
error envelope): they are observable habits with no failure mode a rule can prevent, and
`discovered-rules.md` is right that observed behaviour is not a mandate.

### 2. Lint/format as a gate — the draft is right that nothing is configured; add the security dimension

Verified by reading `pyproject.toml` (only `[tool.pytest.ini_options]`) and by globbing for
`ruff.toml`/`.ruff.toml`/`.flake8`/`mypy.ini`/`setup.cfg`/`tox.ini`/`.pre-commit-config.yaml`
— none exist. The draft's "Enforcement — the gap" paragraph and its claim that
`filterwarnings = ["error"]` is the only mechanical gate are accurate.

What the draft does not say, and should:

- A formatter is hygiene; a **linter is the cheapest static analysis this project can buy**.
  Choosing `ruff` specifically lets one dev dependency cover style *and* a SAST floor via the
  `S` (flake8-bandit) rule set; choosing `black` + `flake8` buys style only. If the team
  adopts tooling, the practice line should name which of the two it is buying, because the
  answers differ in security value.
- The other honest branch: **no linter and no SAST**, security review stays manual. That is
  defensible for a single-user loopback app with two runtime dependencies — but then say it
  in `team.md`, so a later stage does not assume a gate exists.
- Either choice interacts with the dependency cap that `pyproject.toml` records in a comment
  ("Dependency cap (NFR3)") and that `dependencies.md` §6.1 calls "a requirement, not a
  preference". A linter, a formatter and a coverage tool are *development* tools, so they do
  not change the runtime count — but the cap is stated without that qualifier, so the
  interview should confirm the dev/runtime split explicitly rather than leave an agent to
  guess.

### 3. Supply chain — the gap the draft does not name at all

`pyproject.toml` declares floors, not pins: `fastapi>=0.110`, `uvicorn>=0.27`, `pytest>=8`,
build backend `setuptools>=68`. There is **no lockfile, no hash, no constraints file and no
`requirements.txt`** (`glob` checked `uv.lock`, `poetry.lock`, `pdm.lock`, `requirements*.txt`;
`dependencies.md` §1 says the same). `dependencies.md` §2 records the consequence: this
checkout resolves to `fastapi 0.141.1` with a dozen transitive packages (`starlette`,
`pydantic`, `pydantic_core`, `anyio`, `annotated_types`, `annotated_doc`, `typing_extensions`,
`typing_inspection`, `click`, `h11`, `idna`) that no manifest constrains.

Why that matters *here*, not as generic boilerplate: in live mode the process holds a
valid OpenRouter key in memory and installs happen with `python -m pip install -e ".[dev]"`
(`README.md` "Setup"). Every one of those transitive packages executes in-process; a
compromised release of any of them, or a build-time compromise of the `setuptools` backend
that PEP 517 runs during `pip install`, is a key-exfiltration path, not a theoretical one.
"Localhost only" does not mitigate it — the code runs on the developer's machine.

There is also no update loop: no Dependabot/Renovate config, no audit command, no schedule,
and **no git remote** (`git remote -v` is empty), so hosted scanning and bot-driven update
PRs are not merely unconfigured, they are unavailable as the project stands.

**Recommended practice-line shape (Deployment/“what has to pass” bullet):**
> Dependencies stay at the declared cap (2 runtime + 1 dev). Installs are unpinned today:
> each install resolves the newest compatible version of ~13 transitive packages. Decision
> needed: keep floating floors and audit on demand, or add a lockfile (a new tool) — and who
> runs the audit, how often.

### 4. Test/runtime controls worth preserving, and the ones missing

Present and security-relevant (all read in the files): the session-scoped `offline_guard`
that makes accidental network use fail the run (`tests/conftest.py:129-147`), `tmp_path`
settings so no test reads the real config or database (`tests/conftest.py:149-168`),
`git check-ignore` as an executable assertion that the key file cannot be committed
(`tests/test_config.py:126-143`), and `"sk-" not in example_text` guarding the committed
example (`tests/test_config.py:116-124`). These belong in the Testing Posture notes as
*security tests that must survive refactors*, alongside the draft's boundary-contract list.

Missing, for the record: no CSP or any security header (`create_app` registers no
middleware, `app/main.py:53-101`; `index.html` serves inline `<style>` and one same-origin
script), no CSRF token or `Origin` check on `POST /auth/disconnect` (a body-less endpoint,
so it is a cross-site HTML form POST away on browsers that do not gate public→loopback
requests), no `state` parameter in the PKCE flow (`app/session_auth.py:163-180`; `complete()`
tries every pending verifier newest-first, `app/session_auth.py:182-232`), and
`callback_url` derived from the request's Host header via `request.url_for("auth_callback")`
(`app/routes.py:137-142`).
I rate these **low** under the stated trust model: no XSS sink exists in `app/static/app.js`
(rendering is `textContent` throughout; no `innerHTML`/`eval`), the PKCE `code_verifier`
never leaves the process so an intercepted or injected code cannot be exchanged off-machine,
and there is no cross-origin CORS configuration to misconfigure. I record them as known
accepted risks the interview can bless in one sentence — not as work items.

Data handling, absent from the draft and worth one line: `POST /analyze` stores the raw input
text unencrypted in the gitignored `data/sentiment.db` (12 rows locally per the scan handoff;
`app/db.py:38-48`; no retention or delete endpoint exists), and in live mode that same text
is sent to OpenRouter (`app/openrouter_client.py:122-160`). "The text leaves the machine when
the indicator is green" is a practice-level fact about this app that a user-facing sentence
should state.

### 5. Interview decisions this review adds (numbered to the draft's own agenda)

My additions to `evidence.md` §4 / `team-practices.md` open questions:

- **D-A (hard constraints; relates to draft §16 and Code Style Q5):** do you want the one
  `NEVER` line about credentials (recommended), and the optional `ALWAYS` line about loopback
  binding? Exact wording offered in Positions.
- **D-B (lint/static analysis; extends draft §15):** adopt `ruff` as lint **and** a SAST floor
  (`S` rules) or keep style-only tooling, or keep convention-and-review-only? Who runs it, and
  where (pre-commit hook vs. the local `pytest` habit)?
- **D-C (supply chain; new):** keep floating version floors and audit by hand, or add a lock
  file plus a periodic `pip-audit`-style check? Who owns dependency updates, and what is the
  emergency-patch path for a critical CVE in a transitive package that runs beside the key?
- **D-D (secret scanning; new):** is a scanner required at all in a repo with no remote and no
  CI (a pre-commit hook is the only place it can run today), and if so, do the four fixture
  keys get a documented allowlist?
- **D-E (data handling; new):** is "history text is stored unencrypted and, in live mode, sent
  to OpenRouter" acceptable as the standing posture for this project, or is a retention/delete
  obligation wanted?
- **D-F (standing platform question; sharpens draft §11 and §17):** with no git remote, "which
  CI platform" presupposes a hosting decision that has not been made. Is the answer "no remote
  yet — everything is local", or is a remote intended? That answer determines whether D-C and
  D-D can be automated at all.

**Which answers change my assessment.** If D-B says "adopt `ruff` with the `S` rule set" and
D-D says "yes, pre-commit secret scanning", my "no static analysis, no secret detection"
finding becomes "minor: one dev dependency, one hook, one allowlist entry" and the gap section
of the draft can shrink to two sentences. If D-F says "a remote is intended", then Dependabot/
secret scanning become available and my supply-chain recommendation changes from "manual
audit" to "hosted defaults plus a lockfile". If D-A rejects the credential `NEVER` line, my
assessment is unchanged on the facts but the residual risk rises from "one rule away from
safe" to "one paste away from irreversible" — I would record that as an explicit accepted
risk rather than silently drop it. If D-E accepts the current data posture, no code change is
implied; if it does not, that is a new requirement, not a practice line, and belongs upstream.

### C. Corrections to draft claims

- **C1 (over-claim).** Testing Posture: "the API key never appears in a repr, a log line or
  **any** response body". The assertion is narrower — `tests/test_auth_routes.py:120-127`
  checks `/`, `/health` and `/auth/status`; `/analyze` and `/analyses` cannot be exercised
  with a live credential at all, because the offline guard forbids the outbound call. The
  property does hold for those routes by construction (no key field reaches a record), but the
  draft should cite the construction, not an endpoint sweep that does not exist.
- **C2 (imprecision).** Code Style item 9 "Secrets are redacted **by construction**". Accurate
  for every rendered surface it names; add "not rendered" as the scope so the claim is not read
  as protection against `asdict`/`vars`/debugger inspection (see §0 qualifications).
- **C3 (unsupported framing).** Deployment candidate 4 calls the "no cloud / no Docker"
  requirement a check on automation. That is true of the prior intent's requirements record,
  but it lives in `260929-sentiment-analysis` — it is **not** in `memory/project.md`,
  `memory/team.md` or any scope file, so it currently constrains nothing mechanically. If the
  team wants it to bind, it needs a `Tech Stack` / `Forbidden` line at the affirmation gate.
- **C4 (gap, not error).** The draft's five areas never mention static analysis, secret
  scanning, dependency pinning/updating, or what data leaves the machine. For a brownfield
  practice discovery whose whole purpose is to stop later stages guessing, the absence of a
  single security line is the largest omission; §1–§5 above supply the missing text.
- Everything else I checked in the draft matched the code and the manifests — branch topology,
  the harness-only `main`, the absent skeleton artifact, the pytest-only configuration,
  `filterwarnings = ["error"]` as the sole gate, the absent CI/deployment surface, the twelve
  style conventions, and the redaction design. I found no factual error there.

## Positions

- AGREE: the draft's claim that no linter/formatter/type checker is configured and
  `filterwarnings = ["error"]` is the only mechanical gate — verified in `pyproject.toml` and
  by an absence glob across the repo root, and independently by `code-quality-assessment.md`.
- AGREE: `discovered-rules.md` should stay nearly empty on a brownfield draft, and observed
  habits must not be auto-promoted to rules — but "nearly empty" is not "empty forever": one
  credential rule is warranted, and the file's current two commented placeholders should be
  replaced at the gate, not carried forward unaffirmed.
- AGREE: the draft's Deployment finding of total automation absence, including its list of
  absent pipeline/container files — I re-verified each name via glob; I add only that there is
  no git remote either, which makes the CI-platform question conditional.
- OBJECT (material gap, not a factual error): the draft contains no line on secrets,
  static analysis, dependency pinning, or data egress. Those four items are the whole of the
  security and supply-chain posture, and leaving them implicit makes the silence read as
  approval while giving later stages nothing to bind to.
- OBJECT (over-claim): Testing Posture's "never in any response body" is asserted by tests
  covering three of the eight routes; rephrase as construction-based (C1).
- OBJECT (recommendation): do **not** mint `ALWAYS`/`NEVER` lines for parameterised SQL, "no
  pydantic in `app/`", "one error envelope" or "secrets redacted in `__repr__`" as a group
  (draft Code Style Q5). Only the credential rule clears the bar — one rule, one permanent
  cost, no false positives; the others are conventions a rule cannot enforce and whose
  violation a test already catches.
- AGREE: the interview — not the draft — is the right place to mint hard constraints (draft
  Code Style Q5), and the answer to that question is **yes for exactly one rule, the
  credential rule.** Recommended
  `project.md` `## Forbidden` line, to be promoted verbatim if the
  interview affirms it:
  `NEVER commit, log, print, paste, or attach a real credential (OpenRouter key or any
  future secret) into the repository or any artifact under aidlc/ — the only permitted
  locations are the gitignored config.local.toml and process memory.`
  If the team also wants the deployment posture pinned, the matching `## Mandated` line is:
  `ALWAYS keep the app bound to loopback (127.0.0.1) and unauthenticated by design; any
  non-loopback bind, hosted deploy or authentication change requires a fresh threat model
  (`app/main.py:35` defines HOST but nothing enforces it).`
