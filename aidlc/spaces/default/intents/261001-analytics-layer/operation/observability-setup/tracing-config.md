# Tracing Configuration — intent `261001-analytics-layer`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/observability-setup`
>
> **Upstream inputs consumed by this stage:** `nfr-design/performance-design.md`
> (`performance-design`), `nfr-design/security-design.md` (`security-design`),
> `nfr-design/reliability-design.md` (`reliability-design`),
> `nfr-design/observability-design.md` and
> `infrastructure-design/monitoring-design.md` (`monitoring-design`),
> `infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`).
>
> **Every count and duration below was measured in this stage**, against the pinned
> 10 000-row / 365-day fixture, with no coverage instrumentation.

---

## 1. Distributed tracing does not apply to this system — and the reason is structural, not budgetary

A distributed trace exists to answer *"where did this request's time go, across the
systems it touched?"* That question presupposes more than one system. This request
touches exactly one.

**Measured, this stage:**

| Precondition for a trace | This system | How established |
|---|---|---|
| More than one process in the request path | **One.** One `uvicorn` process, no worker pool, no sidecar, no proxy. | `infrastructure-specification.md` §Deployment. |
| A network hop the request makes | **Zero.** The read path imports nothing network-capable. | `grep -nE "^\s*(import\|from)\s+(socket\|urllib\|http\|requests\|httpx\|ssl\|…)"` over `app/analytics.py`, `app/terms.py`, `app/repository.py`, `app/models.py` → **no matches**. The complete import list of `app/analytics.py` is `re`, `sqlite3`, `collections.Counter`, `dataclasses`, `datetime`, `decimal`, plus three in-repo modules. |
| Any module in the read path that *can* make a network call | **None.** Only `app/openrouter_client.py` and `app/session_auth.py` import a network client, and neither is reachable from a read. | the same grep, project-wide. |
| A downstream dependency whose latency could dominate | **None.** One local file. | `BR2.8`, `reliability-design.md` §5 ("no outbound call in this unit; there is nothing to break a circuit to"). |
| An asynchronous boundary worth spanning | **None.** The request is synchronous in-process from the HTTP edge. | `reliability-design.md` §3.2. |

**So a trace would have exactly one node.** Instrumenting it would produce a
trace with a single span and no children — a picture of a single dot, at the cost of
a new dependency. `observability-design.md` §4 reaches the same conclusion from the
other direction and states it well: *"There is one process and no network hop in the
read path; a request never crosses a process or host boundary, so there is no
distributed trace to correlate and no correlation header to thread."*

**What is genuinely not available without a tracer, stated plainly:** nothing about
*cross-boundary* latency, because there is none. What *is* unavailable is
**per-span duration inside the request** — and §2.3 shows that a stopwatch and a
`sqlite3` trace hook recover exactly that, with more precision than a sampled trace
would give, because the work is small and enumerable.

## 2. What is available instead — four substitutes, each measured

### 2.1 The request line *is* the request-level span

Each request produces exactly one access-log line carrying its identity and outcome —
method, path, query string, status. That is the span envelope a tracer would emit:

```
INFO:     127.0.0.1:43476 - "GET /v2/analytics/summary?from=not-a-date HTTP/1.1" 422 Unprocessable Content
```

**What it lacks, measured:** the line carries **no duration and no span id**.
`uvicorn` emits a duration only under a non-default access-log format; with the
project's configuration it does not. So this span has *when* and *what* but not
*how long* and not *how to join* — the two things §2.3 and §2.4 supply separately.

### 2.2 The store path is fully enumerable — one statement, always

This is the finding that most fully replaces a trace, and it was measured four ways
over the same 10 000-row fixture using `sqlite3`'s `set_trace_callback`:

| Read | sqlite3 statements | Series / list size | In-process time |
|---|---|---|---|
| `read_summary`, 7-day range | **1** (`SELECT`) | 7 entries | 0.47 ms |
| `read_summary`, 365-day range | **1** (`SELECT`) | 365 entries | 11.21 ms |
| `read_summary`, unbounded | **1** (`SELECT`) | 365 entries | 9.66 ms |
| `read_summary`, 100-year range | **1** (`SELECT`) | **36 525 entries** | **102.40 ms** |
| `read_terms`, unbounded, `limit=10` | **1** (`SELECT`) | 5 + 5 terms | 24.73 ms |

**Read that table the way a trace would be read: the trace is one node, and its cost
is entirely in-process assembly.** Widening the range by 5 200× (7 → 36 525 entries)
adds **zero** statements. This is `NFR1.3`/`NFR9.4`/`BR3.4` — "the statement count is
a function of the query shape, not of the range" — observed directly rather than
inferred, and it independently reproduces the recorded `1 at 7 days, 1 at 365 days`
in `test-results.md` §5.

**Why this is strictly better than a sampled trace here:** a sampled distributed
tracer would give a p50/p99 across many requests; this gives the *exact* statement
set and the *exact* cost attribution, every time, for free, from the stdlib.

**Check it yourself — this is the project's own instrument:**

```bash
.venv/bin/python -m pytest \
  tests/test_analytics_read.py::test_the_statement_count_does_not_grow_with_the_number_of_days \
  tests/test_analytics_read.py::test_the_analytics_read_path_issues_no_mutating_statement -q
```

### 2.3 Latency attribution, obtained by stopwatch rather than by span

Since there is one statement, the whole budget is validation + in-process work +
serialisation. The split is directly measurable, and the measured numbers localise
where the time goes:

| Stage | How measured | Measured |
|---|---|---|
| Total, over HTTP, 365-day fixture | 25 runs, no coverage | `summary` p50 **15.42** / max **20.53** ms · `terms` p50 **30.08** / max **59.28** ms |
| Read module alone, same fixture | `set_trace_callback` + `perf_counter` | `read_summary` **11.21** ms · `read_terms` **24.73** ms |
| Series assembly + serialisation | the difference | `summary` ≈ 4 ms · `terms` ≈ 5 ms |
| Serialisation, wide range | response byte count over HTTP | 36 525 entries → **7 012 976 bytes**; 100-year request **235 ms** |

**The attribution is the actionable part:** the dominant cost at wide ranges is
**building and serialising the series**, not querying. That is exactly the conclusion
a service-map latency breakdown would have produced, reached with one `sqlite3`
callback and one `curl`.

### 2.4 Correlation: the machine code, where it exists, and where it does not

| Failure | Correlator | Verified this stage |
|---|---|---|
| Storage failure (`STORAGE_FAILURE`) | The code appears on the envelope **and** in the `app.routes` record **and** as a `500` on the access line. Three surfaces agree; a reader holding the `500` finds the record. | `NFR8.2`, satisfied — `log-queries.md` §2.1 |
| Validation failure (`VALIDATION_FAILED`) | **The access line's `422` and the response body only.** Measured: 4 × `422` produced **0** application records. | **No join is possible.** `log-queries.md` §4(a) |
| Startup / migration failure | The `sqlite3.IntegrityError` text and `Application startup failed. Exiting.` | Present and unmistakable, but emitted by **`uvicorn.error`**, not an `app.*` logger. `log-queries.md` §2.3 |

**And there is no request id anywhere.** No `X-Request-ID` is generated, propagated
or logged; no span id; no traceparent header. `observability-design.md` §4 declined to
add one precisely because there is no boundary to propagate across — and this stage's
measurement shows that reasoning was right about *tracing* and insufficient about
*correlation*: within a single process, a request id would still have been useful for
joining a client-visible `422` to something. Naming that as a gap rather than
re-litigating the decision.

### 2.5 The migration is the one real multi-step lifecycle — and it is enumerable

The startup migration is the only state machine in this project
(`reliability-design.md` §4). Measured this stage with a `sqlite3.connect` spy that
attaches a trace callback to the connection `init_db` opens:

| Path | Statements | Shape |
|---|---|---|
| Fresh store (**create**) | **10** | `PRAGMA` 1 · `BEGIN` 1 · `SELECT` 1 · `CREATE` 5 · `INSERT` 1 · `COMMIT` 1 |
| v3 store (**migrate**) | **11** | `PRAGMA` 2 · `BEGIN` 1 · `SELECT` 2 · `CREATE` 4 · `INSERT` 1 · `COMMIT` 1 |
| v4 store (**re-run**) | **11** | identical to the migrate path |

**And the crucial detail, measured rather than assumed:** the v4 re-run executes 11
statements — including the `CREATE INDEX IF NOT EXISTS` no-ops and an
`ON CONFLICT … DO UPDATE` upsert of `'version'` to the value it already holds — and
still leaves the file **byte-identical, mtime unchanged**:

```
before: ('9829bcf6efcc5ec8', 1791042896930173918, 32768)
after:  ('9829bcf6efcc5ec8', 1791042896930173918, 32768)
IDENTICAL sha same mtime same
```

No page becomes dirty, so no journal is created and the file is never written. This is
the mechanism behind finding **F-01** in `validation-report.md` §4 — "the startup
migration writes the store **if and only if** that store is behind `SCHEMA_VERSION`" —
now explained at the statement level rather than only at the file level.

**The failure branch is equally enumerable**, and it is the loudest signal in the
system (`log-queries.md` §2.3): `BEGIN` → work → `except BaseException:` →
`rollback()` → `raise`. Measured: `sqlite3.IntegrityError: CHECK constraint failed:
label IN ('positive','negative','neutral')`, **exit status 3**, port never opened,
and the store read back afterwards still at `version=3` **with the offending row
intact** — the rollback held.

## 3. What is not provisioned, and the rule that rules it out

| Element | Status | Ruling rule |
|---|---|---|
| AWS X-Ray daemon / SDK / service map | **Not provisioned** | No AWS account, no `aws` CLI, no `~/.aws`, no `CDK_*`/`AWS_*` variable, no IaC file — **measured this stage**. `C-5` forbids introducing a cloud component. |
| OpenTelemetry SDK + exporter | **Not provisioned** | `C-6` caps declared runtime dependencies at exactly `fastapi` + `uvicorn`. No SDK and no exporter is installed. |
| CloudWatch Embedded Metric Format | **Not provisioned** | No metric is emitted; EMF needs an agent or library, both of which `C-5`/`C-6` exclude. |
| Correlation-ID header contract | **Not provisioned** | Would widen the frozen `{code, message}` envelope contract (§2 C1) — and, per `observability-design.md` §4, would need a mechanism to propagate. **Recorded as a gap, not endorsed.** |

**The transitively-installed package is not tracing and must not be read as such.**
`opentelemetry-api 1.45.0` is present because `fastapi` hard-requires it
(`memory/team.md` §Deployment records this precisely, calling out the 14-vs-2
distinction). Measured: nothing in `app/` imports `opentelemetry` or `otel`; the API
package alone emits nothing; there is no SDK, no processor, no exporter and no
collector. `monitoring-design.md` §1 records the same conclusion.

## 4. Honest summary of the tracing posture

**Genuinely available:** one access line per request carrying identity and outcome;
an exactly enumerable store path (one `SELECT` per read, four widths measured); a
direct latency attribution between query, assembly and serialisation; a three-surface
correlation for `STORAGE_FAILURE`; and one fully enumerable lifecycle with a
verified rollback.

**Genuinely absent:** span durations recorded by the system; any span or trace id;
any correlation for `VALIDATION_FAILED`; any application-authored record for a failed
startup; any trace store, sampler, or exporter.

**The one sentence worth keeping:** tracing is absent because there is nothing to
trace *across* — and the substitute that exists is not a poor-man's tracer, it is a
*complete* account of a one-node request, obtained more precisely than sampling would
give it, at zero dependency cost. What it cannot do is record itself over time, and
that limit is the same one `alarms.md` §1 and `slo-config.md` §4 name: **this system
observes itself when asked, and never on its own.**