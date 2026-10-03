# Environment Provisioning Questions — intent `261001-analytics-layer`

> **Stage:** `environment-provisioning` (operation), Step 2 · lead
> `aidlc-aws-platform-agent` · support `aidlc-devsecops-agent`,
> `aidlc-compliance-agent` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/environment-provisioning`
>
> **Inputs this artifact was derived from**:
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md`
> · `operation/deployment-pipeline/cd-config.md` ·
> `operation/deployment-pipeline/deployment-strategy.md` ·
> `operation/deployment-pipeline/rollback-runbook.md` ·
> `operation/deployment-pipeline/deployment-pipeline-questions.md` ·
> `construction/build-and-test/build-instructions.md` ·
> `memory/team.md` § Deployment, § Way of Working, § Code Style ·
> `memory/project.md` `## Mandated` / `## Forbidden` ·
> `app/main.py` · `app/config.py` · `app/db.py` · `app/routes.py` ·
> `tests/conftest.py` · `pyproject.toml` · `config.example.toml` ·
> `.aidlc/stages/operation/environment-provisioning.md` Step 2.

---

## 0. Summary — four of four required questions are answered from evidence; none is left open

| # | Question | Status | Answered by |
|---|---|---|---|
| **Q1** | Are all environments provisioned per Infra Design? | **ANSWERED — there are none to provision** | `memory/team.md` § Deployment + `memory/project.md` `## Forbidden` `C-5`; measured: no `aws` on `PATH`, no AWS/CDK/Pulumi credential or config, zero IaC files in the tree |
| **Q2** | Are VPCs, subnets, security groups, NACLs correct? | **ANSWERED — none exist, and the one boundary that does exist is enforced** | `infrastructure-specification.md` §5; `app/main.py:65-80`; measured: 5 non-loopback hosts refused, `create_app(host="0.0.0.0")` refused before the lifespan runs |
| **Q3** | Are secrets in Secrets Manager / Parameter Store correctly injected? | **ANSWERED — no store exists and none is needed** | `infrastructure-specification.md` §5 (`NFR2.5`); `cd-config.md` §6; measured: `config.local.toml` **absent**, mode resolves `offline`, `repr(Settings)` redacts, zero credential literals in the tree |
| **Q4** | Is cross-account / cross-VPC connectivity validated? | **ANSWERED — nothing exists to validate** | one account, one process, zero network hops; `cd-config.md` §2 records exactly one environment and no promotion |

**No question is left open at this stage, and none was manufactured to fill this
file.** Each of the four answers below is settled by an affirmed practice, by
measurement taken in this run, or by both.

**Four genuinely open items already exist upstream and are deliberately not
re-asked here** — see §2. Re-asking a settled question is re-litigating a recorded
decision, which `memory/org.md` § Forbidden names as something agents must never
do; the same is true of an open question another stage already owns.

---

## 1. Q1–Q4 — answered from evidence, with sources

### Q1 — Are all environments provisioned per Infra Design?

**Answer: there are no environments to provision, and the design says so. This
stage provisioned nothing and authored no template.**

| Source | What it settles |
|---|---|
| `memory/team.md` § Deployment | *"Deployment is a localhost checkout, and a commit is the release. No environment tiers, no container, no hosted service, no IaC."* |
| `memory/project.md` `## Forbidden`, affirmed 2026-10-01, `C-5` | *"NEVER introduce a new external service, hosted dependency, cloud component or network call to compute anything for this app."* |
| `infrastructure-specification.md` §1 Environments row | *"**None.** There is no dev/staging/prod tier."* — and its note that the only runtime distinction is the engine *mode*, which is application configuration, not a tier |
| `infrastructure-specification.md` §5 | Enumerates, per element, what is not provisioned and why — a deliberate absence with a named reason |
| `cd-config.md` §2 | *"Promotion: **nothing.** There is exactly one environment."* |
| **measured, this stage** | `command -v aws` → not found; `env \| grep -iE '^AWS_\|^AMAZON_\|^CDK_'` → no match; `~/.aws`, `~/.cdk.json`, `cdk.json`, `~/.pulumi` → all absent; `find` for `*.tf` / `*.tfvars` / `cdk.json` / `*.template` / `Pulumi.yaml` / `serverless.yml` / `*.bicep` / `Dockerfile*` / `docker-compose*` → **zero hits** |

**Why this is an answer and not a deferral.** The stage's Step 3 says to provision
*"target AWS environments using IaC from Construction"*. There is no target — no
account, no region, no toolchain, no template — so there is nothing to provision
*from* or *into*. The measured facts confirm that `infrastructure-specification.md`
§5's not-provisioned list is current rather than aspirational: the files it says do
not exist still do not exist. **A CloudFormation template written here would be a
document that has never been applied and cannot be**, which `cd-config.md` §6
already names as the failure mode for a provider workflow file and calls *"a
Tier-1 artifact that has never executed."* None was produced.

**What the stage did instead, narrowly.** It validated the one environment that
exists — the local checkout, its interpreter, its dependency install, its enforced
loopback bind, its store and its rollback procedure. The judgement is the same one
`memory/project.md` `## Interpretations` records from the immediately preceding
stage: *"read the CONDITIONAL skip test against the current schema version rather
than the deployment model"* — the AWS half of this stage's condition is unmet
because the environments it assumes do not exist; the validation half is met
because `init_db` now runs an additive step against the operator's real store on
every startup.

### Q2 — Are VPCs, subnets, security groups, NACLs correct?

**Answer: none exist. The only network boundary in this system is the loopback
bind, and it is enforced rather than configured — which is the strongest form
"correct" can take here.**

| Source | What it settles |
|---|---|
| `infrastructure-specification.md` §5 Network boundary row | *"The process binds loopback only; there is no public surface, no east-west traffic and no TLS hop."* |
| `memory/project.md` `## Mandated`, affirmed 2026-09-30, reaffirmed 2026-10-02 | *"ALWAYS keep the app localhost-only: bound to loopback (127.0.0.1) and unauthenticated by design; any non-loopback bind, hosted deploy or change to the authentication posture requires a fresh threat model."* |
| `memory/project.md` `## Mandated`, affirmed 2026-10-02, Q11 | *"ALWAYS enforce that loopback bind at startup so a non-loopback host fails loudly; a documented uvicorn default is documentation, not enforcement, and the `HOST` constant must be the thing the run path actually consumes."* |
| `app/main.py:45, 51, 56, 65-80, 93, 120` | `HOST`, `LOOPBACK_HOSTS = {127.0.0.1, ::1, localhost}`, `NonLoopbackBindError`, `resolve_bind_host`, consumed by **both** `run()` and `create_app()` |
| **measured, this stage** | `resolve_bind_host` **accepts** `127.0.0.1`, `::1`, `localhost`; **refuses** `0.0.0.0`, `::`, `192.168.1.10`, `example.com`, `""`. `create_app(host="0.0.0.0")` **raises before the lifespan runs**, so a refused bind cannot have already opened or migrated a store |

**The one measurement worth stating plainly.** `memory/team.md` § Deployment
records the position this replaced: the bind was "documentation, not
enforcement", because `uvicorn app:app --host 0.0.0.0` would expose an
unauthenticated app holding the operator's key **while every test still passed**.
**That is no longer true.** The refusal is measured through the real function, not
asserted from a constant, and the message names both the reason and the allowlist.
There is no NACL, security group or route table to be misconfigured here, and no
TLS terminator: measured, `app/` contains **no `ssl` import at all**, so both
outbound calls use Python's default certificate verification and there is no
in-app terminator to weaken them.

### Q3 — Are secrets in Secrets Manager / Parameter Store correctly injected?

**Answer: no secret store exists, none is needed, and there is nothing to inject.
The one credential this project has has a recorded location, and in this checkout
there is not even that.**

| Source | What it settles |
|---|---|
| `infrastructure-specification.md` §5 Secrets manager row | *"`NFR2.5`: the analytics path carries no credential… this unit adds no secret and no secret store."* |
| `cd-config.md` §6 | *"No step in R1–R8 needs a credential… **A pipeline that declares no secret cannot leak one.**"* |
| `memory/project.md` `## Forbidden`, affirmed 2026-09-30, reaffirmed 2026-10-02 | *"NEVER commit, log, print, paste, or attach a real credential (the OpenRouter key or any future secret) into the repository or any artifact under `aidlc/`; the only permitted locations are the gitignored `config.local.toml` and process memory."* |
| `app/config.py:38, 54-77` | `DEFAULT_CONFIG_PATH`; `Settings.__repr__` renders `api_key=<redacted>` |
| `app/openrouter_client.py:164` | The key travels as `"Authorization": f"Bearer {self._api_key}"` — a header to a hardcoded `https` endpoint, never a URL, a body or a log line |
| **measured, this stage** | `config.local.toml` **does not exist**; `load_settings()` → `Settings(mode='offline', api_key=None, …)`, so the **offline default is the measured state of this machine**; `repr()` of a live-key `Settings` contains `<redacted>` and **not** the key; `grep` across the tree finds **seven distinct `sk-or-v1-*` literals, every one an obvious placeholder**, and **zero** real credential shapes; the analytics read-path modules contain **no** reference to `api_key`, `credential` or `Authorization` |

**Why the absence is not a gap.** A secrets store would hold a credential the
analytics path never reads (measured: `app/terms.py`, `app/repository.py`,
`app/db.py`, `app/models.py` have no credential reference at all). Creating one
would provision the very tier `C-5` forbids, and — with no lockfile and no
provider — there would be no rotation, no audit trail and no revocation path to
build it on. The project's stated alternative is stronger than a store would be:
the key lives in a **gitignored** file and in process memory, is **redacted in
every repr**, is **never logged**, and the offline default means it is not even
used unless the operator asks for live mode.

**One half of this claim must not be reported alone**, and it is stated in full in
`validation-report.md` §3 F-03 / V-33: the practice is genuinely clean
(zero real credentials, measured), **and** the tooling that would enforce it does
not exist (no `gitleaks`, `detect-secrets`, `bandit`, no `.pre-commit-config.yaml`,
no CI). Reporting only the first would let a future scope add a real key with
nothing to notice. That gap is already owned by `FR7.3` / `u4-platform-packaging`;
it is not re-asked here.

### Q4 — Is cross-account / cross-VPC connectivity validated?

**Answer: there is nothing to validate. One account (this machine), one process, one
file, and zero network hops between them.**

| Source | What it settles |
|---|---|
| `cd-config.md` §2 | Trigger: **a human at a terminal** — *"No automatic trigger is possible: a pipeline is a program that runs on an event, and there is no event source."* Target: **one loopback process.** Promotion: **nothing.** |
| `infrastructure-specification.md` §4 | *"No shared infrastructure is introduced… this unit provisions no resource another unit consumes."* |
| **measured, this stage** | No `aws` binary, so no account can even be named, let alone a second one; `git remote -v` → **empty**; `grep` over `app/` finds HTTP call sites in exactly two modules — `openrouter_client.py:89-96` and `session_auth.py:88-96` — **neither on the analytics path**; an AST walk of the read-path closure finds **no network-capable import at all** |

**The strongest form of this answer is structural, not procedural.** The analytics
read path (`app/routes.py` v2 handlers → `app/terms.py` → `app/repository.py` →
`app/db.py`) has **no `urllib`, `socket`, `http`, `ssl`, `requests` or `httpx`
reachable from it**. It cannot make a network call, so it cannot be a
cross-account or cross-VPC concern even in principle. The session-scoped
`offline_guard` in `tests/conftest.py` — which replaces `socket.socket.connect`
with a raiser and is **proven armed** by a test that asserts the raiser fires —
turns any attempt elsewhere into a suite failure rather than a silent egress.

---

## 2. What is deliberately not asked

Four items are genuinely open — and **all four are already open somewhere else**.
Re-asking them here would be re-litigating a recorded decision, which
`memory/org.md` § Forbidden names as a thing agents must never do.

| Upstream open item | Where it is already owned | Why this stage does not re-ask it |
|---|---|---|
| *"Should the standing verification command's step 3 stop migrating the real store?"* | `deployment-pipeline-questions.md` **Q6** — the human's | This stage **measured** it (V-14, V-15) and narrowed it: the migration writes the store **iff** the store is behind `SCHEMA_VERSION`, and the operator's is at v4. That is an input to Q6, not a replacement for it. The decision — whether to change the recorded command — is still the human's. |
| *"Should copying `data/sentiment.db` before a release be a documented step?"* | `deployment-pipeline-questions.md` **Q7** | This stage re-confirmed RB3 (V-25: 0 commits touch `data/`, 0 backups, 0 tools) and noted the absence of a `.bak-` copy for this commit. That is evidence for Q7; it is not a reason to open it twice. |
| *"Should the recorded schema version be guarded against moving backwards?"* | `deployment-pipeline-questions.md` **Q8** — Code Generation's | Measured as part of RB2 (V-22: the old `init_db` does downgrade `4` → `3` on the store it finds, harmlessly). The owner is unchanged. |
| *"The lockfile (`FR7.1`) and the verification script (`FR7.2`)"* | `memory/project.md` `## Mandated`; `u4-platform-packaging`; `cd-config.md` §6 | Measured and confirmed from here: **no lockfile**, **no lockfile-resolved pins**, 24 distributions resolved against floors (`cd-config.md` §4 step 4 already names this as a rollback risk). The build belongs to another unit. |

**Also not asked, and why — three things this stage could have turned into
questions and deliberately did not:**

| Candidate question | Why it is not a question |
|---|---|
| *"Should `data/sentiment.db` be `chmod 600`?"* (measured: mode **644**, unencrypted, 0 SQLCipher markers) | The mode is a consequence of the process's `umask` (measured **022**), not a decision anyone made — and there is **no mechanism** to change it: no IaC, no provisioning step, no setup script. Asking a question whose answer could not be acted on manufactures work rather than surfacing it. **It is recorded in `environment-inventory.md` §2.4 and `validation-report.md` §3 V-12**, together with the honest framing that it is a deliberate, already-recorded posture rather than an oversight. |
| *"Should `cd-config.md` §5 be edited to reflect the conditional migration?"* (finding **F-01**) | This stage may write only under its own record directory. The correction is **recorded with its measurement**, and the owner of `cd-config.md` is the conductor and the human at that stage's gate. |
| *"Which regulatory framework should this app be assessed against?"* | Not a judgement call, and not the human's to make by preference. The classification is measured from `_INSERT_SQL` and the DDL, and the scope conclusions follow structurally: **no personal data on behalf of a data subject, no ePHI, no cardholder data** → GDPR, CCPA/CPRA, HIPAA and PCI DSS are all out of scope, each with its **scope condition** named. The falsifiers are stated precisely in `validation-report.md` §3 G — the operator pasting third-party personal data into `text`, or enabling live mode. |

---

## 3. One question this stage **does** put to the human

None. Every required question is answered from an affirmed practice or from a
measurement taken in this run, and the genuinely open items already have owners.
Recording an open question here would misrepresent the state of the record: the
stage has no decision of its own to escalate, because it provisioned nothing and
validated what exists.

**What a reader should take from this file is the narrowness of the claim.** The
stage's condition has two halves. The **provisioning** half is unmet, per element,
with the rule that rules each element out (`environment-inventory.md` §4). The
**validation** half is met, and it produced 44 measured checks, four corrections
to upstream artifacts (**F-01** `cd-config.md` §5, **F-02** `rollback-runbook.md`
RB1's exit code, **F-03** the fake-key fixture count, **F-04** the suppression
census) and a compliance position that names its own falsifiers. The strongest
single fact in it is not any of those: it is that **the operator's real, durable,
unencrypted, unbacked-up store is migrated in place on every application
startup**, and that today, on this machine, it is at version 4 — so the hazard is
real, currently inert, and returns the moment a v3 store reappears through the
`beeb587` rollback path.