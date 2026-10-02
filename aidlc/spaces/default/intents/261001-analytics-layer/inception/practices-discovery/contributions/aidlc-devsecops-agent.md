**Collaborator:** aidlc-devsecops-agent

## Contribution

Security and supply-chain review of the lead draft, from my own measurements. Every
claim below is tagged **[measured]** (I ran or read it in this checkout at `beeb587`)
or **[inferred]** (my reading of what the measurement means). I read
`team-practices.md`, `discovered-rules.md`, the four `codekb/sentiment-opencode/`
artifacts, and the repository's dependency manifest, lint configuration, test
configuration, `.gitignore`, and every commit in the history. I wrote nothing into
the repository and ran no scanner that would install anything.

---

### 1. Headline: the security posture is **clean by inspection, unenforced by machine**

This is the one sentence the draft does not currently say, and it is the correct
framing for the whole lens:

> There is **no** SAST, DAST, secret scanning, dependency scanning, licence policy,
> CI, or pre-commit hook in this project — and no scanner of any kind is installed
> on this machine. What exists instead is one linter with an explicitly reviewed
> rule set, one coverage floor, 118 tests, and a small number of hand-written
> assertions that encode security-relevant config facts. Every one of those is
> **opt-in**: it runs only when a person remembers to run it.

The draft is honest about the absence (Code Style: *"an unrun gate is not a gate"*;
Deployment: *"no audit command, no update bot, no remote, no named owner"*). I
endorse that framing and below I make it precise, correct four places where the
draft overstates or omits, and separate what the evidence settles from what only the
human can answer.

---

### 2. Lint and format: real tool, real rule set, real green — and a precise scope limit

**[measured]** `.venv/bin/ruff` is `ruff 0.16.9`, present and declared
(`pyproject.toml:23`, `ruff>=0.6` in the `dev` extra).

```
$ .venv/bin/ruff check --no-cache app tests      →  All checks passed!
$ .venv/bin/ruff format --check app tests        →  24 files already formatted
```

Both green, independently confirmed. The `select = ["E","F","W","I","N","UP","S","B","C4","SIM"]`
selection is explicit and reviewed, exactly as the draft says.

**[measured]** What the `S` selection actually buys. `ruff 0.16.9` ships **73**
`S`-prefixed rules and **zero** removed rules, so selecting `S` is a real selection
and not a silently-dead one. **13 of the 73 are preview-gated** and therefore
inactive under a plain `select = [... "S" ...]` — and all 13 are the *import-side*
blacklist checks: `S401` telnetlib, `S402` ftplib, `S403` pickle, `S404`
subprocess, `S405`–`S409` xml parsers, `S411` xmlrpc, `S412` httpoxy, `S413`
pycrypto, `S415` pyghmi. The *usage-side* counterparts (`S301` pickle.loads,
`S307` eval, `S403`→usage, etc.) are stable and active. **[inferred]** so the
practical statement is: the net catches the dangerous *call*, not the dangerous
*import*. For this codebase that is the right trade — it has no `pickle`/`eval`
imports today — but the draft should not describe `S` as a complete bandit's worth
of coverage.

**[measured]** What fires and what does not, probed with
`ruff check --stdin-filename app/_probe.py -` against the project's *own* config
(so `per-file-ignores` for `tests/*` did not apply; no file was written to the
repo). **Catches:** `S608` SQL injection from both `+` concatenation and f-strings;
`S110` `try/except/pass`; `S324` `hashlib.md5`; `S301` `pickle.loads`; `S307`
`eval`; `S602`/`S605` shell execution; `S607` partial executable path; `S506`
`yaml.load`; `S101` `assert` **in `app/`**; `S105`/`S106` hardcoded credential; `S310`
`urlopen` on a non-literal URL; `S108` insecure temp path; `SIM105`/`SIM115`; `E722`
bare `except:`.

**Does not catch:** `except Exception:` (**`BLE001` is not selected**);
`print()` (**`T20` not selected**); `breakpoint()` (**`T10` not selected**); naive
`datetime.now()` (**`DTZ` not selected**); and any TLS/cipher assertion — ruff has
no analogue of Bandit's weak-TLS or weak-cipher checks at all.

**Two corrections the draft's Code Style section needs.** [measured]

1. The draft's summary table describes `S` as *"the security set: secrets in code,
   unsafe calls, weak hashing"* — that is the `pyproject.toml` comment's own claim,
   and for secrets it is **narrower than it sounds**. `S105` fires on
   `SECRET = "…"` and `PASSWORD = "…"` but **does not fire on `API_KEY = "…"`**,
   because `API_KEY` is not among the identifiers ruff's `S105` treats as
   credential-shaped. `API_KEY` is the single most likely name for the one secret
   this project has. **[inferred]** the secret-in-code net has a name-shaped hole
   exactly where this repo's own secret would go. Nothing catches it today because
   the real key is gitignored and held in memory — the hole is latent, not open.
2. The draft's Conventions bullet *"Error handling in code: no bare `except`"* is
   presented as an observed convention. It is half-enforced: bare `except:` **is**
   caught, by `E722` (pycodestyle `E`, which *is* selected). But `except Exception:`
   — the far more common mistake — is **not caught by anything**. **[inferred]** the
   draft should say the bare-`except` half is mechanical and the
   `except Exception:` half is convention, so nobody later mistakes the second for
   a gate.

**[measured]** The `S`-rule suppressions: exactly **4** `# noqa: S310` on the two
`urllib` call sites (`app/openrouter_client.py:89,93`; `app/session_auth.py:88,96`),
each on a hardcoded `https` constant, each carrying a justifying comment. Zero
file-level `# ruff: noqa`. Four is the **entire** security-suppression budget in the
repository. **[inferred]** that is worth turning from a fact into a rule — see §6.

**[measured]** A positive finding the draft omits: neither outbound call installs a
custom `ssl` context, so both use Python's default certificate verification. There
is no TLS-verification bypass anywhere in `app/`. Worth stating, because "stdlib
`urllib` instead of `requests`" reads as a downgrade until you check that it is not.

**[measured]** The only automated security control that exists is
`tests/test_config.py::test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools`,
which asserts `"S" in ruff_config["select"]` and
`fail_under == 80`. It asserts that the config *string contains a letter*. It does
not run ruff, does not assert which `S` rules, and cannot fail on a code defect. It
is a useful tripwire against silent rule-set erosion; it is not a security gate, and
the draft should not let it read as one.

---

### 3. Scanning and policy: stating the absence plainly, and separating it from the risk

**[measured]** I searched the whole tree for every plausible automation surface:
`.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci`, `buildkite.yml`,
`azure-pipelines.yml`, `.pre-commit-config.yaml`, `Makefile`, `tox.ini`,
`noxfile.py`, `Taskfile*`, `justfile`, `.semgrep*`, `.bandit`, `.gitleaks.toml`,
`.trivy*`, `.snyk`, `.checkov*`, `.cfn*`, `renovate.json`, `.dependabot/`,
`requirements*.txt`, `*constraints*.txt`, `poetry.lock`, `uv.lock`, `Pipfile`,
`pdm.lock`. **Zero hits.** No active git hooks (`ls .git/hooks` shows only
`.sample`). No git remote.

- **SAST** — none, beyond `ruff`'s `S` set described above. No Bandit, no Semgrep,
  no CodeGuru, no SonarQube.
- **DAST** — none. No ZAP, no Burp, no runtime scan of any kind.
- **Secret scanning** — no gitleaks, detect-secrets, git-secrets, or trufflehog, and
  no config for any.
- **Dependency scanning** — no `pip-audit`, `safety`, Snyk, Dependabot or Renovate,
  no audit cadence, no named owner.
- **SBOM** — none generated, none stored.
- **Licence policy** — no `LICENSE` or `COPYING` file in the repository, no `license`
  field in `pyproject.toml`, and the project's own installed distribution
  (`very-cool-sentiment-analysis 0.1.0`) carries an empty licence expression.

**[measured]** The absence of scanners on the machine:
`pip-audit`, `bandit`, `semgrep`, `gitleaks`, `detect-secrets`, `safety`, `trivy`,
`syft`, `cdk-nag`, `checkov` — **all absent**. **[measured]** PyPI *is* reachable
from this machine. **[inferred]** so the gap is a decision, not a capability
limitation, and that distinction matters for the interview: nobody can answer "we
can't afford that here".

**[measured]** Secret hygiene is nevertheless clean, and I checked it thoroughly
rather than assuming it. I scanned **every blob in every commit** in this history
for: `sk-[A-Za-z0-9]{20,}`, `AKIA[0-9A-Z]{16}`, `BEGIN [A-Z ]*PRIVATE KEY`,
`ghp_[A-Za-z0-9]{20,}`, `github_pat_…`, Slack `xox[baprs]-…`, `AIza…`,
JWT-shaped `eyJ…`, and `api_key/secret/password/passwd/token = <24+ chars>`.
**Zero hits on all nine.** The 22 raw `sk-or-v1-` matches resolve to six distinct
placeholders: `0123456789abcdef0123456789abcdef`, `from-config`, `live-key`,
`not-used-here`, `session`, `session-key`. `config.local.toml` is gitignored
(`.gitignore:90`) and `tests/test_config.py` proves it two ways — it shells out to
`git check-ignore -q config.local.toml`, and `test_example_config_parses_with_placeholder_key`
asserts the committed example has `api_key == ""` and no `"sk-"` anywhere in it.

**[inferred]** This is the finding I most want the draft to carry in this exact
form: **the practice is clean and the tooling is absent.** Those are different
statements, and only the second one is a process gap. Reporting "low secret risk"
without the tooling clause would let a future scope add a real key to a file and
have nothing notice; reporting "no secret scanning" without the clean-practice
clause would misrepresent a project that has thought about this seriously.

**[measured]** Licence risk is nil and licence practice is nil. Offline licence
inventory from the 21 installed third-party distributions' own metadata: MIT ×12,
BSD-3-Clause ×4, BSD-2-Clause ×1, Apache-2.0 ×2, PSF-2.0 ×1, and `packaging` as
`Apache-2.0 OR BSD-2-Clause`. Every one permissive; no copyleft, no unknown, no
custom licence. **[inferred]** so there is no licence *finding* to report — only a
licence *absence* (no `LICENSE`, no policy, no attribution file) that only the human
can say is intentional.

---

### 4. Supply chain: measured posture

**[measured]** Floors, not pins — confirmed. Declared `fastapi>=0.110`,
`uvicorn>=0.27`, `pytest>=8`, `pytest-cov>=5`, `ruff>=0.6`,
`setuptools>=68`. No lockfile, no constraints file, no hash pinning, anywhere.

**[measured]** Declared vs installed in `.venv`, and what the float has already
absorbed:

| Declared floor | Installed | What the floor admitted |
|---|---|---|
| `fastapi>=0.110` | 0.142.2 | — |
| `uvicorn>=0.27` | 0.54.0 | — |
| `pytest>=8` | **9.1.1** | **a major version** |
| `pytest-cov>=5` | **7.1.0** | **two major versions** |
| `ruff>=0.6` | 0.16.9 | — |
| `setuptools>=68` | **not installed** | see below |

**[measured]** The sharpest supply-chain fact in this repository, which the draft
does not state: **`setuptools` is not an installed distribution in `.venv`.** PEP 517
build isolation means every `pip install -e ".[dev]"` — the project's single
documented install command — downloads `setuptools>=68` fresh, unpinned and
unhashed, into a temporary isolated environment and **executes
`setuptools.build_meta` as code**. Combined with the absent lockfile, the project's
install path is: *resolve the newest compatible version of ~12 runtime transitives
plus a build backend from PyPI, then run the build backend's code.* That is a real,
specific, measurable statement, and it is stronger than the draft's *"roughly a
dozen transitive packages"* without being alarmist.

**[measured]** Resolution is wider than "two packages" at the install layer. The
14 installed runtime distributions are `fastapi`, `uvicorn`, `starlette`, `pydantic`,
`pydantic-core`, `annotated-types`, `annotated-doc`, `typing-extensions`,
`typing-inspection`, `opentelemetry-api`, `anyio`, `idna`, `click`, `h11`. The
codekb's count of **12 transitive** packages is **correct** (the other two are the
direct dependencies). But `fastapi 0.142.2` declares a **hard, non-extra** dependency
on `opentelemetry-api>=1.44.0` — I read this from the installed metadata, not from
the docs. **[measured]** Nothing in `app/` imports it (zero hits for
`opentelemetry`/`otel` across `app/*.py`), and with no OTel SDK or exporter
installed there is no automatic egress. **[inferred]** so this is not an active
finding — but it is the kind of transitive the "exactly two packages" rationale
never contemplated, and it sits uncomfortably next to affirmed constraint `C-5`
(*"NEVER introduce a new external service, hosted dependency, cloud component or
network call"*, 2026-10-01). **[inferred]** that tension is a question for the
human, not a judgement for me: `C-5` is about what *we* choose to depend on, and
nobody chose this one.

**[measured]** Two smaller items the draft does not mention:

- `target-version = "py311"` in the ruff config, but the interpreter that actually
  runs the code and holds the API key is **CPython 3.14.7**. **[inferred]** the
  project's only static security analysis is aimed at a Python version the
  application never runs.
- `codekb/…/technology-stack.md:57` records `opentelemetry-api | 1.45.1`, reached
  "through `anyio`". The installed distribution is **1.45.0**, and it is required by
  `fastapi` directly (`starlette` requires it only under its `full` extra).
  **[inferred]** small, but it is the cleanest available proof that the "Installed"
  columns are a one-time snapshot that nothing keeps honest — the same class of
  problem as the unpinned resolution that produced them.

---

### 5. What the deployment topology implies — the sentence the draft is missing

**[measured]** Topology, all confirmed: single-operator localhost process,
unauthenticated by design, one gitignored SQLite file, no container, no IaC, no
hosted service, no remote, no telemetry export. Documented run path is
`python -m pip install -e ".[dev]"` then `uvicorn app:app --reload`, with no
`--host` argument.

**[inferred]** This is the *most* favourable topology that could carry an unpinned
dependency set, and the draft's Supply chain paragraph reads as a defect list
without ever saying what the topology buys — which leaves the reader unable to
rank the items. The rankable version is:

- **No remote attack surface exists.** There is nothing listening off-loopback, no
  hosted component, no container to pull, no CI to exfiltrate from. A
  remote-exploitable CVE in any of the 14 runtime distributions is largely
  theoretical *for this topology*. The residual exposure is **local, at install
  time** (a malicious or compromised release in an unhashed, unpinned resolution
  set) and **local, in-process** (any code in those distributions runs beside a live
  OpenRouter key).
- **[inferred]** That is an argument for *keeping the topology*, not for leaving
  the resolution unpinned — the install-time exposure applies the instant anyone
  clones this repository and runs the documented command, on any machine, including
  one that is not localhost-only.
- **[measured]** One topology control is asserted but not load-bearing. `HOST =
  "127.0.0.1"` (`app/main.py:36`) is asserted by
  `tests/test_routes.py:334-338`, but `HOST` has **no call site in the run path**:
  the documented invocation is `uvicorn app:app --reload`, so the bind is uvicorn's
  own default, not this constant. The test proves a constant says loopback; it
  cannot prove the process bound loopback. `uvicorn app:app --host 0.0.0.0` would
  expose an unauthenticated app holding the operator's API key, and **every test
  would still pass**. **[inferred]** the draft's *"Localhost-only is binding"* and
  the affirmed `ALWAYS` rule therefore rest on a documented default, not on an
  enforcement. The cheapest possible fix costs no dependency at all: have the run
  path take the host from `HOST` (or document `--host "$HOST"` in the single
  verification command).

---

### 6. Rules — what I propose, and what I deliberately do not

`discovered-rules.md` is promoted verbatim into `memory/project.md` and may only
carry constraints a human stated. So I separate **evidence-supported candidates
for the interview** from **things I am not inventing rules for**.

**Candidate `NEVER` rule — the strongest thing I can support, because the repo
already does it consistently:**

> NEVER add or widen a security-rule suppression outside `tests/` — no `# noqa: S…`,
> no `# ruff: noqa`, and no `per-file-ignores` entry naming an `S` rule for a path
> other than `tests/*`.

Evidence that the repo supports this as a practice, not just as an aspiration
**[measured]**: zero file-level `# ruff: noqa` in the repository; exactly four
`# noqa: S310`, each on a hardcoded `https` constant and each carrying a written
justification comment; `per-file-ignores` scoped to `tests/*` alone, with a comment
explaining why, and an explicit statement in it that *"the security rules still
apply in full to `app/`"*; and `B008` silenced by configuration
(`flake8-bugbear.extend-immutable-calls`) rather than by suppression. That is a
consistent, four-for-four applied convention across two completed scopes. **[inferred]**
it deserves `NEVER` form precisely because a future scope adding analytics, or a
future hosted-deploy pivot, is exactly when someone would be tempted to widen it —
and because a suppression is the one change that silently disables a control the
team currently believes is on.

**Candidate `ALWAYS` rule:**

> ALWAYS pair any change to the selected lint rule set — adding or removing a prefix,
> or narrowing a `per-file-ignores` entry — with the matching assertion in
> `tests/test_config.py`.

Weak precedent, honestly labelled **[measured]**: `tests/test_config.py` already
asserts `"S" in select` and `fail_under == 80`, so the *shape* of this already
exists in the repo. It is an extension of an existing practice, not a new one.

**Already covered — no new rule needed.** The `NEVER commit, log, print, paste, or
attach a real credential…` rule (affirmed 2026-09-30) is the only entry in
`discovered-rules.md` that has **executable enforcement behind it**
(`test_local_config_is_gitignored` + `test_example_config_parses_with_placeholder_key`, both verified green in my scan). I endorse it unchanged
and note that a secret scanner would strengthen it, but the rule does not depend on
one.

**On dependency pinning — I want to be careful here.** The evidence settles the
*current state* (unpinned, and the float has already absorbed two major-version
jumps plus a fresh build-backend download per install). It does **not** settle
whether the team wants that changed. So I am **not** proposing a pinning rule; I am
proposing it as the single highest-value interview question (§7.1). One fact that
should travel with it **[measured]**: a `requirements.lock` or `constraints.txt`
would **not** conflict with affirmed `C-6`, because
`tests/test_config.py` asserts the `project.dependencies` *list*, not the resolution
— the cap is a declaration-level rule and a lockfile is not a declaration.

**What I am deliberately not proposing.** No rule about DAST or SAST adoption; no
rule about an SBOM; no rule about `py311` vs 3.14; no rule about `opentelemetry-api`
and `C-5`. Each is either a human budget decision or an unresolved question, and
inventing a rule the human has not agreed to would violate the stage's own rule that
observed behaviour stays a convention in `team-practices.md`, not a promoted
constraint.

---

### 7. Evidence settles these; no need to ask

1. The lint tool, its version, its rule selection, and its green status.
2. The security rules apply in full to `app/`, with the preview-gate caveat (§2).
3. The coverage floor and warnings-as-errors gate are configured in two places so a
   forgotten flag cannot skip them.
4. Secret hygiene is clean across every blob in every commit (§3).
5. No CI, no hook, no scanner, no licence policy, no lockfile, no remote (§3).
6. The transitive closure, including `opentelemetry-api`, and the fact that
   `setuptools` is resolved and executed at every install (§4).

### 8. Questions only the human can settle

1. **Is floating dependency resolution an accepted risk or a gap to close?** The
   evidence proves the state; only the human can say whether a lockfile, a
   hash-pinned install, or "documented and accepted" is the answer. Note the C-6
   non-interference above.
2. **Does `C-5` reach a transitively-pulled telemetry API?** Nobody chose
   `opentelemetry-api`; it arrives with FastAPI. If the answer is yes, the team needs
   to know, because the next FastAPI minor could add another. If no, `C-5`'s wording
   should say "declared".
3. **Is `target-version = "py311"` deliberate**, given the runtime is 3.14.7? This is
   a one-character-scale fix that changes what the only security analysis in the
   project is actually analysing.
4. **Should the loopback rule be made load-bearing** — the run path taking its host
   from `HOST` — or is "a documented uvicorn default" an accepted control for a
   single-operator tool? A real judgement call about where to spend scope, not a
   defect I can rule on.
5. **Does any scanning get adopted in this scope now that `ci-pipeline` executes?**
   Nothing is installed and PyPI is reachable, so this is purely a choice. The
   relevant security constraint for the interview is *what the CI job may do*: a
   code-only job (install → lint → `pytest`) cannot break the affirmed localhost-only
   rule, whereas anything that boots uvicorn on a non-loopback interface, or that
   needs a live credential, would.
6. **Is the absence of a `LICENSE` file and any licence policy intentional** for a
   solo non-published project, or an omission? Every dependency is permissive, so
   there is no risk either way — only an unanswered intent question.

---

## Positions

- AGREE: the Supply chain paragraph's factual core — floors not pins, no lockfile, no hash pinning, no constraints file, no audit command, no update bot, no remote, no named owner — every element of which I verified independently.
- AGREE: `ruff` is adopted for lint *and* format with an explicit reviewed `select`, and the draft is right that this closes the prior adoption question and is no longer drift.
- AGREE: the draft's warning that *"a `ruff` binary that happens to sit on this machine's PATH is not a gate; the tool must be declared in the project"* — and the correct extension of it: the tool *is* now declared, and the remaining risk is that nobody runs it.
- AGREE: the Code Style section's own conclusion that the three mechanical gates are opt-in and that *"an unrun gate is not a gate"* — this is the load-bearing sentence for the whole stage and should survive into the integration.
- AGREE: the Deployment section's framing that deployment is a localhost checkout and a commit is the release, with no container, no IaC and no hosted service.
- AGREE: the claim that no SAST, DAST, secret scanning or dependency scanning is in effect — stated more plainly and without qualification in the integration, because "no coverage" is the finding.
- AGREE: routing the `/v2` prefix and the tokenizer-home questions to the interview instead of asserting them; both are outside my lens and neither is settled by scan evidence.
- OBJECT: **the "localhost-only is binding" sentence overstates enforcement** — `HOST` has no call site in the run path, the documented command relies on uvicorn's default, and `uvicorn app:app --host 0.0.0.0` would pass the entire suite, so either correct the sentence or make the run path consume the constant.
- OBJECT: **"Runtime dependencies are exactly two" is true at the declaration level and misleading at the resolution level** — 14 runtime distributions install today, one of them an OpenTelemetry API surface pulled in by FastAPI itself; say "two declared, fourteen resolved", or route the `C-5` question to the human.
- OBJECT: **the Supply chain section lists risks without stating the topology's effect, so the reader cannot rank them** — add the one sentence that makes it rankable: no remote attack surface exists, so residual exposure is local at install time and local in-process.
- OBJECT: **"Where the gate lives is still undecided" is framed as a tooling-placement question and misses the security-relevant part** — the draft should state the constraint that actually decides it: a code-only CI job is topology-neutral and safe under the affirmed localhost-only rule, while any job that binds a non-loopback interface or needs a live credential is not.
- OBJECT: **the Code Style blurb implies `S` gives broader coverage than it does** — 13 of ruff's 73 `S` rules are preview-gated (all the import-side blacklists), `BLE001` is not selected so `except Exception:` is caught by nothing, no TLS/cipher rule exists, and `S105` does not fire on the name `API_KEY`, which is the most likely name for this project's one secret.
- OBJECT: **the "`S` is the security set: secrets in code" framing is not backed by an executable control** — the only automated security assertion in the repository is a test checking that the config string contains the letter `"S"`; it never runs ruff and cannot fail on a code defect, and the draft should not let it read as a gate.
- OBJECT: **`target-version = "py311"` against a CPython 3.14.7 runtime is unmentioned anywhere in the draft** — the project's only static security analysis is aimed at a Python the application never runs.
- OBJECT: **the secret-hygiene story needs both halves stated** — I scanned every blob in every commit and found zero real credentials (all six `sk-or-v1-` values are obvious placeholders), *and* there is no secret scanner, no gitleaks, no detect-secrets anywhere; reporting only the first would hide a process gap, and reporting only the second would misrepresent a project whose practice is genuinely clean.
- OBJECT: **the codekb's `opentelemetry-api 1.45.1 / reached through anyio` is wrong on both counts** (installed is 1.45.0; `fastapi` requires it directly, not `anyio`) — a small but useful proof that the "Installed" columns are a snapshot nothing keeps honest.
- OBJECT: **the four `# noqa: S310` suppressions are described as a count rather than as a budget** — four is the entire security-suppression budget in the repository, consistently applied with written justifications across two scopes, which is the strongest evidence-backed candidate for a `NEVER`-form rule in `discovered-rules.md`, and the integration should surface it as an interview candidate rather than a convention bullet.
- OBJECT: **the draft never says that `setuptools` is absent from the venv**, which means every `pip install -e ".[dev]"` downloads and executes a fresh, unpinned build backend — the most concrete install-path supply-chain fact available, and stronger evidence for the same concern than "roughly a dozen transitive packages".