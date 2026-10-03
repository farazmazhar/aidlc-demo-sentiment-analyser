# Environment Inventory — intent `261001-analytics-layer`

> **Stage:** `environment-provisioning` (operation) · lead `aidlc-aws-platform-agent`
> · support `aidlc-devsecops-agent`, `aidlc-compliance-agent` · **Scope:** `feature`
> · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer`
> · **Date:** 2026-10-03
>
> **Upstream inputs this file is derived from** (the stage's declared `consumes`,
> in full, plus what had to be read to answer them honestly):
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`) · `operation/deployment-pipeline/cd-config.md`
> (`cd-config`) · `operation/deployment-pipeline/deployment-strategy.md` ·
> `operation/deployment-pipeline/rollback-runbook.md` ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `construction/build-and-test/build-instructions.md` ·
> `construction/u1-analytics-slice/nfr-requirements/security-requirements.md` ·
> `construction/u1-analytics-slice/nfr-design/security-design.md` ·
> `memory/team.md` § Deployment, § Way of Working, § Code Style ·
> `memory/project.md` `## Forbidden` / `## Mandated` ·
> `app/main.py` · `app/config.py` · `app/db.py` · `app/routes.py` ·
> `tests/conftest.py` · `pyproject.toml` · `config.example.toml` ·
> `.aidlc/stages/operation/environment-provisioning.md` Steps 1–6.
>
> **This file provisions nothing.** It records what the environment *is*, measured
> in this run, and records what is deliberately **not** provisioned with the rule
> that rules each element out. No AWS account, VPC, subnet, security group, secret
> or stack was created, because none exists and the affirmed practice forbids
> creating one.

---

## 1. The decision this inventory records, and the rule behind it

The stage's execution condition is **CONDITIONAL** — *"execute when AWS
environments need provisioning or validation"* — and its Step 3 says to
*"provision target AWS environments using IaC from Construction."* **That has no
counterpart in this project.** `infrastructure-specification.md` §5 already
enumerates, per element, what is not provisioned and why; this inventory does not
re-decide those lines, it **confirms each one against the working tree and the
running host** and adds the two the upstream artifacts did not have to check —
whether an AWS account or IaC toolchain even exists here, and what the one real
environment is.

**The rule that rules out the AWS half, verbatim** — `memory/team.md`
§ Deployment:

> *"Deployment is a localhost checkout, and a commit is the release. No
> environment tiers, no container, no hosted service, no IaC. The only documented
> run path is `python -m pip install -e ".[dev]"` then `uvicorn app:app --reload`,
> one process bound to `127.0.0.1:8000`."*

Reinforced by `memory/project.md` `## Forbidden`, affirmed 2026-10-01,
constraint `C-5`:

> *"NEVER introduce a new external service, hosted dependency, cloud component or
> network call to compute anything for this app."*

So the stage applies **narrowly**: the AWS half is recorded inapplicable per
element (§4), and the local half is validated as a real environment (§2–§3).

### 1.1 What "there is no AWS environment" means, measured

These are the three facts that make the AWS half inapplicable rather than merely
undescribed. Each was measured in this run, not read off an absence.

| # | Check | Command | Measured result |
|---|---|---|---|
| M1 | Is there an AWS CLI to query an account with? | `command -v aws` | **`aws` is not on `PATH`** (`command -v` exit 1). Nothing on this host can call `sts get-caller-identity`. |
| M2 | Is there a credential in the environment? | `env \| grep -iE '^AWS_\|^AMAZON_\|^CDK_'` | **No match.** No `AWS_ACCESS_KEY_ID`, no `AWS_PROFILE`, no `AWS_DEFAULT_REGION`, no `CDK_*`. |
| M3 | Is there a credential on disk? | `ls ~/.aws ~/.cdk.json cdk.json ~/.pulumi` | **All four absent.** No shared credentials file, no CDK context, no Pulumi stack. |
| M5 | Is there any IaC to apply? | `find` for `*.tf`, `*.tfvars`, `cdk.json`, `*.template`, `Pulumi.yaml`, `serverless.yml`, `*.bicep`, `Dockerfile*`, `docker-compose*` | **Zero hits** anywhere in the project tree. `infrastructure-specification.md` §5 is not a claim that went stale — the files it says do not exist still do not exist. |

**Consequence.** "Provision an AWS environment" has no target: no account, no
region, no toolchain, no template. An `aws` invocation cannot be written, let
alone a CloudFormation template. Producing one anyway would be a document that
has never been applied and cannot be — the exact failure mode
`cd-config.md` §6 names for a provider workflow file and calls *"a Tier-1 artifact
that has never executed."* **None was produced.**

### 1.2 What the AWS-facing parts of the stage's own Step 2 become

Step 2 asks four questions. Each is answered, and the answers are the reason the
questions file records no open items.

| Step 2 question | Answer, with source |
|---|---|
| "Are all environments provisioned per Infra Design?" | **There are no environments to provision.** `infrastructure-specification.md` §1 Environments row: *"None."* Confirmed by M1–M5 and by `cd-config.md` §2, which records exactly one environment. |
| "Are VPCs, subnets, security groups, NACLs correct?" | **None exist.** `infrastructure-specification.md` §5 records the absence with its reason. The loopback bind is the whole network surface, and it is now *enforced* rather than documented — measured in `validation-report.md` §3 V-07. |
| "Are secrets in Secrets Manager / Parameter Store correctly injected?" | **No secret store exists and none is needed.** `infrastructure-specification.md` §5: `NFR2.5` — the analytics path carries no credential. `cd-config.md` §6: *"No step in R1–R8 needs a credential… A pipeline that declares no secret cannot leak one."* The one credential this project has lives in the gitignored `config.local.toml` and process memory, and in this checkout that file **does not exist at all** (measured, V-16). |
| "Is cross-account / cross-VPC connectivity validated?" | **Nothing to validate.** There is no second account, no second VPC, no east-west traffic and no network hop. `cd-config.md` §2 records *"Promotion: nothing. There is exactly one environment."* |

---

## 2. The environment that does exist: a local checkout

One environment. It has no name, no tier, and no counterpart in the framework's
dev/staging/prod model — `cd-config.md` §2 records that the deploy-on-merge
default *"has no counterpart here, because the environments it assumes do not
exist."* The table below is the inventory of that one environment, every value
measured in this run.

### 2.1 The process

| Facet | Value | Measured how |
|---|---|---|
| Compute model | **One** `uvicorn` process serving the ASGI app `app.main:app`. No container, no second process, no supervisor, no init system. | `app/main.py:163` `app = create_app()` at module scope; `run()` at `:93` calls `uvicorn.run("app.main:app", …)`. A real boot confirmed a single process (`validation-report.md` §3 V-08). |
| Bind address | `HOST = "127.0.0.1"`, `PORT = 8000`, **enforced at startup** | `app/main.py:45-46`; `resolve_bind_host` at `:65-80` raises `NonLoopbackBindError` (`:56`) for anything outside `{127.0.0.1, ::1, localhost}`. Six hosts probed; see V-07. |
| Application object | `very-cool-sentiment-analysis`, routers `/v1`, `/v2`, page router, `/static` mount | `app/main.py:143-152`. |
| Reachable surface | `/v1/*` data + auth + health · `/v2/analytics/summary` · `/v2/analytics/terms` · `/` page · `/static/*` · `/auth/*` | Route table read from the live app; V-09 lists the endpoints probed. |
| Authentication | **None, by design** | `memory/project.md` `## Mandated`: *"ALWAYS keep the app localhost-only: bound to loopback (127.0.0.1) and unauthenticated by design."* |

### 2.2 The interpreter and the dependency install

This is the part of the environment that actually bites an operator, and both
halves of it were re-measured in this run rather than inherited from
`build-instructions.md`.

| Facet | Value | Measured how |
|---|---|---|
| Interpreter | **CPython 3.14.7** at `/usr/bin/python`; `requires-python = ">=3.11"` | V-01. |
| **The recorded install command fails on this host** | `python -m pip install -e ".[dev]"` → **exit 1**, `error: externally-managed-environment`, PEP 668 | V-02. Confirmed environmental: `/usr/lib/python3.14/EXTERNALLY-MANAGED` **exists**. This is step 1 of the recorded `verification-command.txt`, so the recorded verification command does not pass end to end here. |
| **The venv remedy works** | `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` → **exit 0**, `Successfully installed very-cool-sentiment-analysis-0.1.0` | V-03, against the repository's own `.venv`. This is R2 of `cd-config.md` §3. |
| **`APPIMAGE` corrupts `sys.executable`** | With `APPIMAGE` exported, `sys.executable` = `/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage`. With `env -u APPIMAGE`, `/usr/bin/python`. | V-04. The consequence is a hard requirement, not a nicety — see §2.3. |
| Resolved toolchain | 24 distributions. Runtime declared: **exactly two** — `fastapi>=0.110`, `uvicorn>=0.27`. Dev extra: `pytest>=8`, `pytest-cov>=5`, `ruff>=0.6`. | V-05. Resolved: `fastapi 0.142.2`, `uvicorn 0.54.0`, `starlette 1.7.0`, `pydantic 2.13.5`, `pytest 9.1.1`, `pytest-cov 7.1.0`, `ruff 0.16.9`, plus `opentelemetry-api 1.45.0` hard-required by FastAPI. No lockfile: **floors, not pins** (`memory/team.md` § Deployment). |
| `sqlite3` library | **3.53.4** (the stdlib module's own version, distinct from the file-format version 3 in the file header) | V-05. |

### 2.3 The one environmental requirement that fails a gate if ignored

`env -u APPIMAGE` is on every command in `build-instructions.md` §6 and
`cd-config.md` §3. **Re-measured as load-bearing in this run**, not quoted:

| Invocation | Result |
|---|---|
| `env -u APPIMAGE .venv/bin/python -m pytest` | **192 passed in 1.82 s**, coverage 97.06 %, floor 80 % reached, **exit 0** |
| `.venv/bin/python -m pytest` (prefix omitted) | **1 failed, 191 passed, exit 1** — `tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget`, the spawned-interpreter budget test |

The single failure is an **environmental artifact wearing the costume of a
performance regression**: the test spawns `[sys.executable, "-c", …]` to measure
the latency budget without coverage instrumentation, and the AppImage rejects
`-c`. Recorded here as `cd-config.md` precondition **D3**, confirmed rather than
restated.

### 2.4 The store

| Facet | Value | Measured how |
|---|---|---|
| Path | `data/sentiment.db`, **relative** — `DEFAULT_DB_PATH.is_absolute()` is **`False`** | `app/config.py:39`; V-10. The relative path is the whole of §3's hazard. |
| Gitignored | **Yes.** `git check-ignore -v` → `.gitignore:94:/data/` | V-11. Commits touching `data/`: **0**. |
| Schema version | **`schema_meta.version = 4`** | V-11, opened **read-only** (`file:…?mode=ro`) so the validation could not itself mutate the store. |
| Indexes | All three present: `idx_analyses_created_at`, `idx_analyses_import_id`, `idx_analyses_label_created_at`. Plus `sqlite_autoindex_schema_meta_1` — which is why *"exactly three indexes"* is false against a real store. | V-11; matches `app/db.py:112-116` and the `BR5.3` correction. |
| Columns | `id, text, label, probabilities, confidence, intensity, model, provider, created_at, import_id` | V-11; matches `ANALYSES_COLUMNS`. |
| Rows | **0** | V-11. |
| At rest | Plain SQLite, file-format header `SQLite format 3`, **0 SQLCipher markers**. File mode **644**, owner `faraz:faraz`; `umask` **022**. | V-12. |
| Backup | **None.** No `.bak-*` sibling, no dump, no replication, no commit containing a copy. | V-13; this is RB3 in `rollback-runbook.md` §4, confirmed rather than re-derived. |

### 2.5 Configuration and credentials

| Facet | Value | Measured how |
|---|---|---|
| `config.example.toml` | **Present**, committed, `mode = "dummy"`, `api_key = ""`, `model = "typesafe/jev-1.13"`. Carries no secret and says so in its own header. | Direct read. |
| `config.local.toml` | **Does not exist in this checkout.** Gitignored (`.gitignore:90`). | V-16. |
| Resolved settings | `Settings(mode='offline', api_key=None, model='typesafe/jev-1.13', db_path='data/sentiment.db', …)` | V-16, via the real `load_settings()`. **The offline default is not a default branch nobody took — it is what this machine resolves.** |
| The one credential | An OpenRouter key. Permitted locations are the gitignored `config.local.toml` and process memory, per `memory/project.md` `## Forbidden` (affirmed 2026-09-30, reaffirmed 2026-10-02). In this checkout **there is none**. | `memory/project.md`; V-16. |
| Redaction | `repr(Settings)` renders `api_key=<redacted>`; a live key does **not** appear in the repr | V-17. |
| Credential literals in the tree | **Zero real credentials.** Seven distinct `sk-or-v1-*` literals exist and every one is an obvious placeholder (`0123456789abcdef0123456789abcdef`, `from-config`, `live-key`, `not-used-here`, `session`, `session-key`); `README.md:121` carries the truncated `sk-or-v1-…`. Zero `api_key`/`secret`/`password`/`token = <24+ chars>` hits. | V-17. **This corrects the counts recorded upstream:** `FR7.3` and `memory/team.md` say *"the four known fake-key fixtures"*; the advisory review counted six; the measured number is **seven**. See `validation-report.md` §4 F-03. |
| Secret **scanner** | **Does not exist.** No `gitleaks`, `detect-secrets`, `trufflehog`, `bandit`, `semgrep`, no `.pre-commit-config.yaml`, no CI. | `quality-gates.md` §2 G9; re-confirmed by `find` this run. **The clean practice is real; nothing enforces it.** Both halves must be stated together or the first misrepresents the second. |

### 2.6 What is absent that an environment inventory normally lists

| Normally present | Here | Why |
|---|---|---|
| dev / staging / prod tiers | **None** | `memory/team.md` § Deployment. `cd-config.md` §2 records exactly one environment. |
| Container / image | **None** | `infrastructure-specification.md` §5. |
| IaC | **None** | `infrastructure-specification.md` §5; measured, M5. |
| Remote / registry / runner | **None.** `git remote -v` → empty. `git tag -l` → `express`, `v1-classic`; HEAD is `aa0b1e4`, `git describe --tags` → `express-6-gaa0b1e4`. 8 commits. | `memory/team.md` § Way of Working: one commit per scope, squashed, tagged. The release *is* the tag. |
| Monitoring / alerting tier | **None** | `infrastructure-specification.md` §5. There is nothing to alert on and no instrument to alert with. |
| Service registry / discovery | **None** | One process, addressed by a literal `127.0.0.1:8000`. |
| Secrets manager | **None, and none needed** | §1.2 above. |

---

## 3. The one live hazard in this environment

**`DEFAULT_DB_PATH` is CWD-relative, and `init_db` runs on every application
startup.** So *any* `uvicorn app:app` **launched from the repository root** —
including step 3 of the approved verification command in
`verification-command.txt`, which boots the real `app.main:app` — opens and
migrates `data/sentiment.db` in place. `cd-config.md` §5 measured this and named
R5 (`cp` before release) and R6 (smoke against a throwaway store) as the
mitigation.

This stage re-measured the hazard, and **refines `cd-config.md`'s statement with
one measured nuance that matters operationally**:

| Measured | Result |
|---|---|
| Is the path relative? | **Yes.** `Path("data/sentiment.db").is_absolute()` → `False` (V-10). |
| Does a boot from the repo root really rewrite that file? | **Yes, when the file is behind.** Booting the real app with CWD = a scratch root holding a store forced to v3 with its indexes dropped: the file's **sha256 changed**, and it came back at **version 4 with all three indexes** (V-14). That is the hazard, reproduced. |
| …and when the file is *already* at v4? | **It does not touch it at all.** Booting the recorded verification command's step 3 verbatim against a byte-identical clone left both the **sha256 and the mtime unchanged** (V-15). Not merely content-identical — the file is not opened for write. |
| Does booting from a throwaway CWD protect the real store? | **Yes.** With `PYTHONPATH` set and `os.chdir` into a fresh `mktemp -d`, the app created `<scratch>/data/sentiment.db` and the real store's sha256 **and mtime** were unchanged (V-13). |

**So the hazard is real but conditional, and the condition is measurable.** The
operator's store is at v4 today (V-11), so step 3 of the approved verification
command is currently *inert*. `cd-config.md` §5's phrase *"migrates
`data/sentiment.db`"* is correct about the mechanism and about what happened
during Bolt 1 — the store was at v2 then — but **over-generalised as a
statement about every boot**: the mutation happens only when the store is behind
the code. `validation-report.md` §4 F-01 records the correction. **R5 and R6
remain correct** and this measurement does not weaken them: R5 protects against
the case that is not currently true and becomes true the moment a v3 store is
restored, and the `beeb587` rollback path (`rollback-runbook.md` §3) is exactly
how a v3 store comes back.

**Nothing in this validation opened the real store for write.** Every store
inspection used `file:…?mode=ro`, and every boot that would have migrated a file
ran against a copy in a scratch directory. Final state: sha256 and mtime of
`data/sentiment.db` identical to the values recorded before the first command
(V-19).

---

## 4. AWS elements recorded as NOT provisioned, per element, with the rule

This is `infrastructure-specification.md` §5 confirmed rather than re-decided,
plus the two rows this stage adds because the upstream artifacts had no reason to
list them. Each row names the rule that rules the element out.

| # | Not provisioned | The rule that rules it out | Confirmed by |
|---|---|---|---|
| 1 | **AWS account / subscription** | `memory/team.md` § Deployment — no hosted service; `memory/project.md` `## Forbidden` `C-5` | M1, M2, M3: no CLI, no credential, no config |
| 2 | **VPC, subnets, route tables** | `infrastructure-specification.md` §5 Network boundary; `NFR2.1` / `C-10`; the process binds loopback only | V-07: a non-loopback bind **fails at startup** |
| 3 | **Security groups, NACLs** | Same row. There is no network to filter; the loopback bind is the boundary and it is enforced | V-07 |
| 4 | **Load balancer, TLS terminator, ingress** | Same row. No TLS hop exists. Measured: **no `ssl` import anywhere in `app/`**, so Python's default certificate verification is used unmodified — there is no in-app terminator to misconfigure | V-18 |
| 5 | **Secrets Manager secret / SSM Parameter** | `infrastructure-specification.md` §5 — `NFR2.5`: the analytics path carries no credential. `cd-config.md` §6: no R1–R8 step needs one | §2.5; V-16, V-17 |
| 6 | **IAM role / policy** | There is no principal to grant anything to: one process, one human, one machine. The nearest analogue is file permissions, measured: store mode **644**, owner-only-write is not enforced | V-12 |
| 7 | **KMS key / encryption at rest** | `infrastructure-specification.md` §5. Measured: the store is **plain SQLite format 3, zero SQLCipher markers** — unencrypted at rest, exactly as the project records for `POST /v1/analyze` | V-12 |
| 8 | **CloudWatch / monitoring / alerting** | `infrastructure-specification.md` §5; `C-5` and `C-6` forbid adding a tier. There is no process supervisor and no metric to alert on | `monitoring-design.md` |
| 9 | **Environment tiers (dev/staging/prod)** | `memory/team.md` § Deployment; `cd-config.md` §2. The only runtime distinction is the engine *mode*, which is application configuration, not a tier | §2.1 |
| 10 | **IaC — CDK / Terraform / CloudFormation / Pulumi** | `infrastructure-specification.md` §5: *"Authoring IaC would provision the tiers the practices forbid."* Measured: no toolchain and no template exist | M1, M3, M5 |
| 11 | **Container image / registry** | `memory/team.md` § Deployment — no container, no published image; `C-5` | M5: zero `Dockerfile*` / `docker-compose*` |
| 12 | **Backup / replication / failover** | `infrastructure-specification.md` §5; `reliability-design.md` §5 | V-13: 0 commits touch `data/`, 0 backups, 0 tools |
| 13 | **CDK / cloud CI runner** | No git remote (measured, empty), no provider. A hosted workflow file would be *"a Tier-1 artifact that has never executed"* — `cd-config.md` §6 | `git remote -v` → empty |
| 14 | **Cross-account / cross-VPC connectivity** *(added by this stage)* | There is one account (this machine), one process, and no network hop. Nothing to validate | M1–M3, V-07 |
| 15 | **A second, non-loopback interface** *(added by this stage)* | `memory/project.md` `## Mandated`: any non-loopback bind *"requires a fresh threat model."* The bind is now enforced, so the element cannot be created by accident — only by a deliberate code change, which the rule catches | V-07: five non-loopback hosts probed, all refused |

**The AWS half of this stage is therefore recorded inapplicable per element, and
nothing was provisioned.** No CloudFormation template, CDK app, Terraform module,
security-group rule, secret or environment tier was authored. There is no
artifact here that has never been applied, because there is nothing that could be
applied.

---

## 5. Support-agent conclusions

Two lines, with the evidence in `validation-report.md` §5.

**Security posture — `aidlc-devsecops-agent`.** Over the actual data flow
**browser → loopback process → SQLite file**: no IAM, no KMS and no network
boundary exist to assess, and saying so is the finding rather than a gap in it.
STRIDE over that flow is **falsified at every reachable step**: spoofing and
tampering are bounded by the enforced loopback bind and by zero interpolated SQL;
information disclosure is bounded by the `{code, message}` envelope, which
returned **zero** internal-detail markers across six error paths; denial of
service is bounded by the read-only aggregate path, which has no outbound call;
and the armed offline guard makes egress a **test failure** rather than a hope.
Four facts are the load-bearing ones: the offline guard is **armed and proven
armed**; the analytics read path's import closure contains **no network-capable
module at all**; **every** `execute()` first argument in `app/` is a literal or a
module constant — **zero** interpolated statements; and **zero** credential
literals in the tree.

**Data classification and regulatory scope — `aidlc-compliance-agent`.** The
`analyses` table holds exactly four classes of value: operator-supplied **free
text** (`text`), a **closed three-value label**, three **probabilities plus a
confidence** (floats, all derived), and **provenance** (`model`, `provider`,
`created_at`, optional server-generated `import_id` = `uuid4().hex`). **No
framework is in scope, and the reasons are structural rather than convenient:**
there is **no personal data processed on behalf of a data subject** — no
identifier, no account, no subject, and the operator is the only actor, so GDPR
Art. 4 and CCPA/CPRA's "consumer" are both unmet; the store is **not at rest
encrypted** (measured: 0 SQLCipher markers) and holds **no PHI** and **no
cardholder data**, so HIPAA's and PCI DSS's encryption mandates are not merely
unmet but irrelevant — their **scope conditions** (covered entity / ePHI;
merchant or cardholder data) are not met. **What would change the answer**, and it
is worth stating precisely: pasting third-party personal data into `text`, or
turning on `mode = "openrouter"`, which sends the same free text to a processor
and creates a transfer and a processor relationship. Both are operator decisions
this project cannot make for them.

---

## 6. What is deliberately **not** in this inventory

| Not recorded | Why |
|---|---|
| Stack deployment logs | **There is no stack.** No CloudFormation, no CDK, no Terraform; nothing was deployed, so there is no log. Inventing a plausible one would be the worst possible filler in this stage. |
| Secrets & parameter store audit (Step 4) | **There is no store to audit.** The audit that *can* be done — credential literals in the tree, redaction, where the key lives, whether a store exists — is done in §2.5 and evidenced at V-16/V-17. |
| Environment health-check *results* | Results live in `validation-report.md` §3, with commands and exit codes, rather than duplicated here. |
| An IaC template "for completeness" | **No.** `infrastructure-specification.md` §5 gives the reason, and M5 confirms the absence is real. A template written for a project that will never apply one is padding that a later stage would have to classify. |
| A cost estimate | **Zero cost, measured by construction**: one local process, one local file, two declared packages, no hosted resource. There is nothing to right-size, no Savings Plan to buy and no tag to allocate. The FinOps pillar's honest answer for this workload is that it has no cloud cost surface. |
| A Well-Architected review | Not applicable as written. Its six pillars are cloud constructs — multi-AZ, IAM, KMS, autoscaling, Cost Explorer, Graviton — and none has a counterpart in a single loopback process over one file. What *does* map is stated in `validation-report.md` §5: the Security and Reliability pillars translate; the other four have nothing to assess. Naming them all as "not applicable" would be padding; naming only two would be honest. |