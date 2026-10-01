# CI/CD Pipeline — `u1-application`

## Status: none, by scope

This workflow's scope does not run the CI pipeline stage. There is no pipeline file, no build server
and no deployment job, and this artifact records that state rather than inventing a pipeline the run
will not maintain.

## What stands in for it

| Pipeline concern | What exists instead |
|---|---|
| Build | The install step the README documents, run by hand |
| Test | The suite, run by the checkpoint verification command |
| Coverage gate | The same command, with the whole-application floor applied |
| Lint gate | The configured rules, run alongside the check |
| Deploy | None: the app is run from a checkout |

## The gap, stated plainly

The team's affirmed practice expects the suite and the coverage floor to run before a merge, in a
pipeline. Nothing in the scope delivers that, so today the floor runs only when a checkpoint runs it.
This is the one practice this intent knowingly does not satisfy, and it is recorded here, in the NFR
requirements and in the NFR design rather than being left for a later reader to discover.

## What a minimal pipeline would be

A single job on push: install the development extra, run the linter, run the suite with coverage and
fail below the floor. No deployment step, no environment, no secrets — the app is not deployed
anywhere. Adding it does not change this unit's code.
