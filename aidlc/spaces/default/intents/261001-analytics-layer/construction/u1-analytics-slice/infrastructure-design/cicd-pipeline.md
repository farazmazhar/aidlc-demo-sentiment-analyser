# CI/CD Pipeline — `u1-analytics-slice`
> **Upstream inputs.** This unit's `contract-summary.md` (the pinned boundaries whose
> verification the eventual script must cover), the six NFR Design artifacts, the
> Domain Design `components.md`, this unit's `functional-spec.md`, and the affirmed
> `## Deployment` practice. `contract-summary.md` is named here because the pipeline
> this stage does *not* build would be the thing that verifies those contracts.

> **Intent:** `261001-analytics-layer` · stage `infrastructure-design`
> (construction) · unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** The accepted infrastructure-design assessment
> (`infrastructure-design-questions.md` Q1 option A), the affirmed practices in
> `memory/team.md` §Deployment ("Where the gates run — decided 2026-10-02", "no CI,
> no git remote", "our secret practice") and §Way of Working (a commit is the
> release), and `memory/project.md` mandates Q3 (the platform-neutral verification
> script), Q12 (secret scanning / dependency audit) and Q6 (the lockfile). Unit
> context: `unit-of-work.md` places the verification script and the packaging
> obligations in `u4-platform-packaging`.
>
> **This is a design artifact.** It states plainly that this unit introduces no
> pipeline, where the project's delivery work actually belongs, and why designing a
> pipeline here would be wrong.

## 1. This unit introduces no pipeline

**This unit introduces no CI/CD pipeline, no build job, no deployment job and no
pipeline infrastructure of any kind.** There is nothing for a pipeline to build,
package or deploy: the released artifact is a squashed commit, a commit *is* the
release, and the "deployment" is a developer running `uvicorn app:app --reload`
from a checkout (`memory/team.md` §Deployment). This stage records that fact and
routes the pipeline work to where it belongs, rather than inventing a pipeline the
project cannot use.

| Pipeline concern | This unit |
|---|---|
| Build stages | **None.** Nothing is compiled, bundled or packaged; the run path is an editable install plus `uvicorn`. |
| Test-automation integration | **None from this stage.** The suite exists and runs, but wiring it into a pipeline is a CI-stage concern (§3). |
| Deployment strategy (blue-green / canary / rolling) | **None.** There is no deployment to strategy: one local process, one file, a commit for a release. |
| Rollback procedures | **None to write.** `memory/team.md` §Deployment: recovery is stop the process, delete or restore the local file, check out the previous commit — there is no deployment to roll back. |
| Environment promotion | **None.** There are no environment tiers to promote between (§1 of `infrastructure-specification.md`). |
| Secrets in CI/CD | **None.** No CI runs, so no CI secret is stored, injected or scoped. |
| Artifact management / registry | **None.** No package or image is ever published (`memory/team.md` §Deployment). |

## 2. Why no pipeline here — the two facts that settle it

**Fact 1 — the project has no CI and no git remote.** `git remote -v` is empty;
there is no CI provider of any kind (`memory/team.md` §Way of Working and
§Deployment "Scanning"). A provider workflow file written here would be a file that
has **never executed and cannot execute until a remote exists** — the exact
argument the team used on 2026-10-02 when it decided where the gates run. Designing
a pipeline stage in this artifact would either duplicate a decision already made or
invent a hosted runner the project cannot use.

**Fact 2 — the pipeline work is owned elsewhere by design.** The `feature` scope
marks `ci-pipeline` and `deployment-pipeline` `EXECUTE` for the first time in this
project (`memory/team.md` §Deployment); where the gates run was already decided — a
**platform-neutral verification script the developer runs**, neither a pre-commit
hook nor a provider CI job. That script, and the packaging obligations around it,
are `u4-platform-packaging` deliverables. The CI Pipeline stage owns the pipeline
territory itself.

## 3. Where the pipeline work actually belongs

| Work | Owner | Why not this unit |
|---|---|---|
| **The verification script** (install → lint → `pytest` with the 80 % coverage floor, the `filterwarnings = ["error"]` filter and the pinned `ruff` rule set) | **`u4-platform-packaging`** (per `unit-of-work.md`; `FR7.2`) | It is repository-level tooling, not a runtime behaviour of the analytics slice. `memory/team.md` §Deployment names it a packaging deliverable; this unit's stage owns infrastructure design for a unit that adds none. |
| **Secret scanning + dependency audit** (`FR7.3`, with the known fake-key fixtures allowlisted) | **`u4-platform-packaging`** | Repository-level supply-chain tooling; named as a cross-unit dependency in `security-design.md` §5 and `security-design.md`, **not** as an instrument this unit can run now. |
| **Lockfile with hashes** (`FR7.1`; project mandate Q6) | **`u4-platform-packaging`** | Repository-level dependency pinning, not a per-unit runtime surface. |
| **The full build → test → security-scan → deploy pipeline** | **The CI Pipeline stage** (`ci-pipeline`) and the deployment pipeline stage | The stage that owns pipeline design is where a pipeline belongs; duplicating it here would create two sources of truth for one pipeline. The `feature` scope runs those stages. |
| **A code-only job** (install → lint → `pytest`), if one is ever wanted | **A future CI job** | The team's constraint (`memory/team.md` §Deployment): a code-only job is topology-neutral and safe under the localhost-only rule; anything that binds a non-loopback interface or needs a live credential is not. This is a CI-stage decision, not this unit's. |

## 4. What this unit *does* contribute to verification (not a pipeline)

This unit adds no pipeline, but it does ship the **instruments** the eventual
verification script runs against. Recording them keeps the boundary honest: this
unit builds the thing being verified; `u4` and the CI stage build the running of it.

| Instrument shipped by this unit | Purpose |
|---|---|
| The replaced concurrency harness (`FR7.7`, `US7.7`) | Lets the R-01 concurrency test fail on the connection defect rather than on a "database is locked" error. |
| The startup-enforcement test (`FR7.6`) | Proves the loopback bind is enforced, not merely documented. |
| The migration / index-survival tests (`BR5`) | Prove the additive v3 → v4 step preserves every row and every index. |
| The aggregate-pinning and statement-count tests (`FR8.1`, `FR8.2`, `FR8.9`) | Pin the computed aggregates and the range-independent statement count. |
| The session-scoped offline guard + the test that proves it armed (`FR8.5`) | Proves the suite never reaches the network. |

These run under the existing `pytest` suite (install → `pytest`, `memory/team.md`
§Testing Posture). Wiring them into a pipeline is not this stage's work.

## 5. Traceability

| Concern | Where recorded | Pipeline dimension? |
|---|---|---|
| Verification script (`FR7.2`) | `u4-platform-packaging` deliverable; §3 | **N/A here** — owned by `u4`, not this unit. |
| Secret scanning / dependency audit (`FR7.3`, `NFR2.5`, `NFR2.5`) | `u4-platform-packaging`; `security-design.md` §5 | **N/A here** — a cross-unit dependency, not this unit's instrument. |
| Lockfile (`FR7.1`) | `u4-platform-packaging`; project mandate Q6 | **N/A here** — repository-level packaging. |
| The pipeline itself | The CI Pipeline stage; §3 | **N/A here** — the CI stage owns it. |

No `NFRx.y` for this unit has a CI/CD-pipeline dimension; the enumeration and the
`N/A` justifications are in `traceability.json`.
