# Validation Report — intent `261001-analytics-layer`

> **Stage:** `environment-provisioning` (operation) · lead `aidlc-aws-platform-agent`
> · support `aidlc-devsecops-agent`, `aidlc-compliance-agent` · **Date:** 2026-10-03
> · **Companion to:** `environment-inventory.md` (what exists) and
> `environment-provisioning-questions.md` (what was asked and answered)
> · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/environment-provisioning`
>
> **Upstream inputs validated against:** `infrastructure-specification.md`
> (`infrastructure-specification`, §2.1 loopback bind, §2.2 additive migration,
> §5 the not-provisioned list) · `cd-config.md` (`cd-config`, R1–R8, D1–D7, §5 the
> store hazard) · `deployment-strategy.md` · `rollback-runbook.md` (RB1, RB2, RB3) ·
> `build-instructions.md` (§2.3 the venv remedy, §6 the `APPIMAGE` gotcha) ·
> `verification-command.txt` (the approved three-step command) ·
> `memory/team.md` § Deployment · `memory/project.md` `## Mandated` / `## Forbidden` ·
> `nfr-design/security-design.md` · `nfr-requirements/security-requirements.md`.
>
> **Every row below was executed in this run.** Commands are given so a reader can
> repeat them. Nothing in this report is asserted from an upstream artifact's
> prose without being measured here — where a claim is inherited rather than
> re-measured, the row says so.

---

## 1. Scope of the validation, and the one rule that shaped it

The stage's Step 3 is *"provision target AWS environments using IaC from
Construction."* There is no AWS environment, no account and no IaC to apply —
established by measurement in `environment-inventory.md` §1.1 (M1, M2, M3, M5), and
ruled out by `memory/team.md` § Deployment and `memory/project.md` `## Forbidden`
`C-5`. **Nothing was provisioned.**

So this is a **validation** report in the other sense of the stage's own
condition — *"execute when AWS environments need provisioning **or validation**"* —
of the one environment that exists and that this intent genuinely changed. Two
things in it need validating on their own account, independent of any deployment
question:

1. **`init_db` now mutates the operator's real, durable store on every
   application startup.** `cd-config.md` §1 states this changed the project's
   recovery posture at schema version 4.
2. **The loopback bind became enforced at startup** — a process-exposure
   decision, which is exactly the class of thing an environment stage validates.

And `rollback-runbook.md` is an operation-phase artifact whose RB1/RB2/RB3
procedures have to be true *of this environment* to be usable at all, so those
three are validated here as well.

### 1.1 The self-imposed constraint, and how it was honoured

**No application source, test, configuration or the data store was modified.**
Every store inspection used SQLite's read-only URI (`file:…?mode=ro`); every boot
that would have migrated a file ran against a **copy in a `mktemp -d`
scratch directory**. The real store's sha256 and mtime are identical before and
after the whole validation — measured, V-19.

---

## 2. Result summary

| # | Area | Checks | Result |
|---|---|---|---|
| A | Interpreter, PEP 668, dependency install | V-01 … V-05 | **PASS** (with one pre-existing, documented host constraint) |
| B | Loopback bind enforcement | V-06, V-07 | **PASS** |
| C | Startup migration and store integrity | V-10 … V-16 | **PASS** |
| D | Rollback runbook RB1 / RB2 / RB3 | V-20 … V-27 | **PASS**, with one ambiguity corrected (F-02) |
| E | Security posture | V-28 … V-40 | **PASS**; no STRIDE step reachable |
| F | Gate set and recorded verification command | V-41 … V-44 | **PASS** on steps 2 and 3; **step 1 blocked by the host interpreter**, pre-existing |
| G | AWS surface | M1–M5 (inventory §1.1) | **INAPPLICABLE** — per-element record in inventory §4 |

**Four findings**, none of which is a code defect. All four are corrections to
upstream artifacts — three to recorded counts or wording, one to an ambiguity —
and each is stated in §4 with the measurement that produced it.

---

## 3. Checks, with evidence

### A. Interpreter, PEP 668, dependency install

**V-01 — interpreter.** `env -u APPIMAGE python -V` → `Python 3.14.7`;
`which python` → `/usr/bin/python`. `pyproject.toml` `requires-python = ">=3.11"`.
**PASS.** `memory/project.md` `## Mandated` (affirmed 2026-10-02) also requires
`ruff`'s `target-version` to match `requires-python`; measured
`target-version = "py311"` against `>=3.11` — matched.

**V-02 — the recorded install command fails on this host.**
`env -u APPIMAGE python -m pip install -e ".[dev]"` → **exit 1**,
`error: externally-managed-environment`, `hint: See PEP 668`. Root cause measured
directly: `/usr/lib/python3.14/EXTERNALLY-MANAGED` **exists**. **PASS as a
characterisation, FAIL as a command.** This is step 1 of the approved
`verification-command.txt`, so the approved command does not pass end to end on
this host. `build-instructions.md` §2.2 recorded the same failure and proved it
pre-existing on a pristine clone of `HEAD`; this run re-confirms it on the current
tree. It is a property of Arch's system interpreter, not of this code.

**V-03 — the venv remedy works.** `.venv/bin/python -m pip install -e ".[dev]"`
→ **exit 0**, `Successfully installed very-cool-sentiment-analysis-0.1.0`. This is
`cd-config.md` **R2**. **PASS.** `git status --short` unchanged afterwards.

**V-04 — `APPIMAGE` corrupts `sys.executable`.** Two commands, opposite results:

```
python -c "import sys; print(sys.executable)"                    -> /home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage
env -u APPIMAGE python -c "import sys; print(sys.executable)"   -> /usr/bin/python
```

**PASS** — and load-bearing, proven in V-42 rather than asserted here.

**V-05 — resolved toolchain and the two-package cap.**
`pyproject.toml` declares exactly `["fastapi>=0.110", "uvicorn>=0.27"]` at
runtime, dev tools in the extra. `pip list --freeze` in the venv returns **24
distributions**: `fastapi 0.142.2`, `uvicorn 0.54.0`, `starlette 1.7.0`,
`pydantic 2.13.5`, `pytest 9.1.1`, `pytest-cov 7.1.0`, `ruff 0.16.9`,
`coverage 7.16.2`, `sqlite3` library **3.53.4**, plus `opentelemetry-api 1.45.0`,
which FastAPI hard-requires. **PASS** on `C-6` — the cap is on the *declared*
list, and nothing imports `opentelemetry` in `app/`. **No lockfile**: the floors
resolve to whatever is newest, which is the affirmed gap behind `FR7.1`.

### B. Loopback bind enforcement

**V-06 — the constant exists and is consumed.** `app/main.py:45-46` `HOST =
"127.0.0.1"`, `PORT = 8000`; `LOOPBACK_HOSTS` at `:51`; `resolve_bind_host` at
`:65`; `NonLoopbackBindError` at `:56`. **The `HOST` constant now has call
sites in the run path** — `run()` at `:93` and `create_app()` at `:120` — which is
precisely what `memory/team.md` § Deployment said was missing before: *"a
documented default is documentation, not enforcement."* **PASS.**

**V-07 — eight hosts probed through the real functions.**

| Host | `resolve_bind_host` | `create_app(host=…)` |
|---|---|---|
| `127.0.0.1` | accepted | — |
| `::1` | accepted | — |
| `localhost` | accepted | — |
| `0.0.0.0` | **refused** | **`create_app(host="0.0.0.0")` refused, before any lifespan ran** |
| `::` | refused | — |
| `192.168.1.10` | refused | — |
| `example.com` | refused | — |
| `""` (empty) | refused | — |

The refusal message names the reason and the allowlist: *"Refusing to bind
'0.0.0.0': this app is unauthenticated and holds the operator's API key, so it
is served on loopback only. Allowed hosts: 127.0.0.1, ::1, localhost."*
**PASS** — and the enforcement happens **before** the lifespan, so a refused bind
cannot have already opened or migrated a store. This is `NFR2.4` / `BR6.5` /
`FR7.6` / gate `G12`, validated against a real function rather than against a
constant.

### C. Startup migration and store integrity

**V-10 — the default path is relative.** `load_settings()` resolves
`DEFAULT_DB_PATH = Path("data/sentiment.db")`; `.is_absolute()` → **`False`**.
`DEFAULT_CONFIG_PATH = Path("config.local.toml")`, `.exists()` → **`False`**.
**Confirmed: the whole of §3's hazard in the inventory is this one property.**

**V-11 — the real store, opened read-only.**

```
sha256   c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
size     32768 bytes
tables   ['analyses', 'schema_meta', 'sqlite_sequence']
version  schema_meta.version = '4'
indexes  idx_analyses_created_at, idx_analyses_import_id, idx_analyses_label_created_at
         (+ sqlite_autoindex_schema_meta_1 — the autoindex)
columns  id, text, label, probabilities, confidence, intensity, model, provider, created_at, import_id
rows    0
```

**PASS** — at the current version, with all three named indexes, matching
`app/db.py:112-116`. The autoindex's presence is why *"exactly three indexes"*
is false against a real store, exactly as `BR5.3` and the R-08 review recorded.

**V-12 — at rest.** File header `SQLite format 3`; **zero** SQLCipher markers in
the first 4 KiB; mode **644**, owner `faraz:faraz`, `umask` **022`.
**Confirms** `memory/team.md` § Deployment: *"stores submitted text unencrypted."*
Also worth stating plainly: **644 means the store is world-readable on this
host.** There is no other user and no network reach, but "unauthenticated by
design" extends to the file.

**V-13 — boot from a throwaway CWD leaves the real store untouched.**
`PYTHONPATH` set, then `os.chdir('$(mktemp -d)')`, real `app.main:app` through
real `uvicorn` on `127.0.0.1:8143`:

```
GET /v1/health -> {"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
throwaway store created : <scratch>/data/sentiment.db
real store sha256 before/after : c8be1361… / c8be1361…   (identical)
real store mtime  before/after : identical
```

**PASS.** This is `cd-config.md` **R6**, reproduced independently.

**V-14 — the hazard itself, reproduced.** A copy of the real store was forced to
`version 3` with its three indexes dropped — the shape a pre-release or
rolled-back store has — and the real app was booted with that directory as CWD:

```
pre  sha256 fad24557…   (version 3, no named indexes)
     GET /v1/health -> 200, {"mode":"offline",…}
post sha256 f7196270…   → THE FILE WAS MIGRATED IN PLACE
post-state: version 4, all three indexes present, 0 rows
```

**PASS as a reproduction of the hazard** — this is `cd-config.md` §5's claim,
confirmed by measurement. A second identical boot on the now-v4 store left the
file **byte-identical**. So: **the mutation is conditional on the store being
behind the code.**

**V-15 — the recorded verification command's step 3, on a store already at v4.**
Run verbatim except for CWD, against a byte-identical **clone** of the real store
(`cmp` reported byte-identical first):

```
sha256 before = c8be1361…    mtime before = 16:37:59.766079924
GET /v1/health -> {"mode":"offline","connected":false,…}     exit 0
sha256 after  = c8be1361…    mtime after  = 16:37:59.766079924
→ content unchanged AND mtime unchanged: the file is not opened for write
```

**PASS, and this is the refinement behind finding F-01.**

**V-16 — configuration and the offline default.** `config.local.toml` **does not
exist** in this checkout. `load_settings()` resolves
`Settings(mode='offline', api_key=None, model='typesafe/jev-1.13',
db_path='data/sentiment.db', config_path='config.local.toml')`.
`config.example.toml` is present, committed, `mode = "dummy"`, `api_key = ""`.
**PASS** — the offline default is the *measured* state of this machine, not a
branch nobody took.

**V-18 — no TLS-verification bypass.** `grep -rniE 'ssl\.|_create_unverified|
CERT_NONE|verify *= *false|check_hostname' app/` → **no match at all**: no `ssl`
import, no unverified context, no verify toggle. Both outbound calls
(`app/openrouter_client.py:89-96`, `app/session_auth.py:88-96`) therefore use
Python's default certificate verification. **PASS** — this re-confirms the one
positive security finding `memory/team.md` records, and it matters here because
there is no TLS terminator in the environment to do it for the app (§4 row 4).

### D. Rollback runbook RB1 / RB2 / RB3

**V-20 — RB1: the migration fails at startup.** Built the one store shape the step
cannot preserve (a v3 row with `label = 'ecstatic'`, outside the `CHECK` domain
at `app/db.py:69`), then booted the **real** `app.main:app` through real
`uvicorn` in a subprocess:

```
sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')
client: urllib.error.URLError: <urlopen error [Errno 111] Connection refused>
store sha256 before = eb0b5776…   after = eb0b5776…     → byte-identical
after: tables ['analyses','schema_meta','sqlite_sequence']   (no analyses_pre_v1)
       rows 1, labels ['ecstatic']                          (the row is intact)
       schema_meta.version = '3'                            (no version bump)
```

**PASS.** Every symptom RB1 predicts is reproduced: the port never opens, the
exception is not swallowed, the rollback is complete, and the store is back in its
pre-release state. The `IntegrityError` line **is** present in the recorded
command's own output, so RB1's instruction to grep for it is correct.

**V-21 — the RB1 exit code, pinned down.** Measured across three invocation
shapes:

| Shape | Exit code |
|---|---|
| `python -m uvicorn app.main:app …` (uvicorn in the foreground) | **3** |
| `python -c "…uvicorn.run(app, …)"` (uvicorn in the foreground) | **3** |
| `cd-config.md` **R6**'s one-liner (uvicorn in a **daemon thread**, `urllib` in the foreground) | **1** |

`rollback-runbook.md` §2 records *"uvicorn process exit code: 1"*. The measured
truth is that **1 is the foreground script's** exit code — it is the uncaught
`URLError` from the `urllib` call — and **uvicorn's own** is **3**. The
consequence is small and worth stating because the runbook tells an operator to
grep the console: both processes print the same `IntegrityError`, so the
diagnostic is unaffected. See **F-02**.

**V-22 — RB2: roll the code back against a v4 store.** The `express` release's own
`app/db.py` was recovered from local history with `git show beeb587:app/db.py`
(no remote needed) — 243 lines, `SCHEMA_VERSION = 3`. A real v4 store was built by
the current code and seeded with **two rows**, then the old `init_db` was run over
it:

```
old SCHEMA_VERSION 3
old init_db: SUCCEEDED on a v4 store
  version after : 3        ← downgraded, exactly as RB2 warns
  rows after    : 2        ← preserved
  indexes after : all three preserved
  relation      : column order, types and NOT NULL flags unchanged
```

**PASS** — rolling back the commit costs **no data recovery**, which is the claim
RB2 exists to establish.

**V-23 — RB2 second half: re-upgrade.**

```
before : version 3 | 2 rows | 3 named indexes
after  : version 4 | 2 rows | 3 named indexes
rows survived / all indexes survived / idempotent re-upgrade : True
```

**PASS.** Confirms *"re-running the new `init_db` restores 4 idempotently"* and
means the rollback-then-re-release state is benign.

**V-24 — RB2 diagnostic step 2, verified by construction.** A store carrying
`analyses_pre_v1` would mean the rollback did not run. V-20's post-state lists
tables and **`analyses_pre_v1` is absent**, so the runbook's diagnostic has a
distinguishable outcome rather than an ambiguous one.

**V-25 — RB3: the recovery surface, enumerated rather than assumed.**

| Recovery route | Measured |
|---|---|
| `git log --all -- data/` | **0 commits.** No commit in this repository's history has ever contained a copy of the store. |
| `*.bak*` / `*.backup` / `*.dump` / `sentiment.db.*` anywhere in the tree | **0** |
| A migration / backup / restore tool outside `app/` and `tests/` | **0** |
| `POST /v1/analyses/export` | **present** (`app/routes.py:269`) — recovers the rows, not the database |

**PASS as a confirmation of the named gap.** RB3 is correct that there is no
backup path, and `cd-config.md` **R5** (`cp data/sentiment.db
data/sentiment.db.bak-$(git rev-parse --short HEAD)`) is therefore not a nicety.
**This validation did not create that copy** — the real store was never opened for
write, so no `.bak-` exists after this stage, and an operator about to run R5
should note the release step has not yet been performed for this commit.

**V-26 — the one absence that would make a rollback impossible.** `git remote -v`
returns **empty**; `git tag -l` returns `express` and `v1-classic`; HEAD is
`aa0b1e4` with 8 commits. A rollback target outside the local history is
unrecoverable. **PASS** — RB2's *"If the target commit is not in the local
history, it is gone"* is accurate.

**V-27 — no artifact or promotion rollback exists, and none is claimed.** Nothing
is published, so there is no previous image to redeploy, and there is one
environment, so nothing was promoted. RB4–RB6 in the runbook's "what this does
not cover" list are accurate as written.

### E. Security posture

The data flow is **browser → loopback process → SQLite file**. It has no IAM
principal, no KMS key, no network boundary and no TLS terminator — and saying so
is the finding, not a gap in the analysis. `infrastructure-specification.md` §5
records the absence of each. STRIDE over the flow that actually exists:

| STRIDE | Reachable? | What bounds it — measured |
|---|---|---|
| **Spoofing** | **No** | The listener is loopback-only and the bind is enforced (V-07). There is no remote peer to spoof and no authentication to defeat. |
| **Tampering** | **No** | Two independent bounds. (a) **Zero interpolated SQL** — V-29: an AST walk of every `execute()` / `executemany()` / `executescript()` call in `app/` finds **19 sites**, and *every first argument is a `Constant` or a module-level constant*; not one is an f-string, a `%`-format or a `+` concatenation. (b) **Parameter binding throughout** — `?` placeholders with a bound tuple at every value-carrying site (`app/repository.py:61, 76, 84, 99`; `app/db.py:240, 336`). |
| **Repudiation** | **Limited, and limited by design** | The store records `created_at` and `provider` per row but no actor: there is one human and no account. Import grouping is a server-generated `uuid4().hex` (`app/service.py:150`), not a user-supplied id. |
| **Information disclosure** | **No** on the response path | The envelope is exactly `{code, message}` (`app/routes.py:89-97`, `additionalProperties: false`). V-31 probed six failure paths: three app-raised → `{"code","message"}`; three framework-generated → `{"detail"}`. **Zero** internal-detail markers (`Traceback`, `File "`, `sqlite3.`, `line 3`, `0x7f`) in any body. At rest the file is world-readable and unencrypted (V-12) — a property of the host filesystem, recorded rather than presented as protected. |
| **Denial of service** | **Bounded** | The analytics path is a read of one local file with **no outbound call and no background work** (V-28), so there is no remote party to flood. The offline default means even live mode is off unless the operator turns it on. |
| **Elevation of privilege** | **No** | The process runs as the operator, with the operator's own permissions. There is no privilege boundary to cross: no `sudo`, no setuid, no service account. |

**V-28 — zero egress in the analytics read path, structurally.**
`app/routes.py` v2 handlers depend only on `Query(...)` and
`Depends(get_connection)`. An AST walk of the read-path closure — `app/terms.py`,
`app/repository.py`, `app/db.py`, `app/models.py`, `app/sentiment.py` — gives
top-level imports `{__future__, app, collections, dataclasses, datetime, json,
pathlib, re, sqlite3, typing}`. **Network-capable imports: NONE.** There is no
`urllib`, `socket`, `http`, `ssl`, `requests` or `httpx` reachable from the read
path at all. The repository's only two HTTP call sites are
`app/openrouter_client.py:89-96` (the opt-in live engine) and
`app/session_auth.py:88-96` (the in-app OAuth code exchange) — neither is on the
analytics path. **PASS.** This is stronger than "no call is made": the module
**cannot** make one.

**V-30 — the offline guard is armed, and it can fail a test.** The session-scoped
autouse `offline_guard` (`tests/conftest.py:278-295`) replaces
`socket.socket.connect` with a raiser. Two independent confirmations:

- the repository's own `tests/test_dummy_client.py::test_dummy_result_names_the_offline_engine`
  — which asserts `pytest.raises(AssertionError)` on a deliberate
  `probe.connect(("127.0.0.1", 9))` **and** then completes a real analysis while
  the guard is armed — **passes**;
- an independent probe test written for this stage, run and then removed
  (`git status --short tests/` clean afterwards), also passes.

**PASS, with teeth.** A silently-broken guard cannot make the suite pass while it
reaches the network: the suite contains a test that requires the guard to fire.

**V-32 — injection probes against the live v2 endpoints.** A store was seeded with
**four** rows, two carrying SQL metacharacters
(`Robert'); DROP TABLE analyses;--` and
`'; DELETE FROM schema_meta WHERE key='version'; --`), then the real app was
booted through real `uvicorn` and probed over real HTTP:

| Probe | Result |
|---|---|
| Read the injected text back through `/v2/analytics/summary` | **200**, `total: 4` — counted as data |
| `/v2/analytics/terms` over the same store | **200** — `analyses`, `drop`, `table` appear as **terms**, i.e. tokenised data |
| `import_id = '; DROP TABLE analyses;--` | **200**, `total: 0` — matched nothing |
| `import_id = ' OR '1'='1` | **200**, empty term lists |
| `from = 2026-01-01' OR 1=1--` | **422** `VALIDATION_FAILED`, `"query.from: expected a UTC calendar date written YYYY-MM-DD."` |
| `to = '; DELETE FROM schema_meta;--` | **422** `VALIDATION_FAILED`, same shape |

**Store integrity after all six probes: `tables ['analyses','schema_meta','sqlite_sequence']`,
`rows 4`, `version 4`. Nothing dropped, deleted or altered. PASS.** The
distinction is the point: a syntactically valid date reaches the query layer as a
**bound parameter**, and one that is not is **refused before any read**.

**V-33 — no credential literals.** Every real key shape scanned across the whole
tree (excluding `.git`, `.venv`, `__pycache__`):
`sk-or-v1-<16+>`, `AKIA[0-9A-Z]{16}`, `BEGIN … PRIVATE KEY`, `ghp_…`,
`github_pat_…`, `xox[baprs]-…`, `AIza…`. Exactly **one** file matches a real
shape — `tests/test_config.py:23`, `sk-or-v1-0123456789abcdef0123456789abcdef`,
a sequential-hex placeholder. **Seven distinct `sk-or-v1-*` literals exist in the
tree**, all placeholders; `README.md:121` carries the truncated `sk-or-v1-…`. Zero
`api_key`/`secret`/`password`/`token = <24+ chars>` hits. **PASS** — and see
**F-03** for the count correction.

**V-34 — redaction.** `repr(Settings(mode="live", api_key="sk-or-v1-"+"x"*40))`
renders `api_key=<redacted>`; `"sk-or-v1-" in repr` → **False**. **PASS**
(`BR5.1`, `NFR2`).

**V-35 — key transport.** The live key travels as
`"Authorization": f"Bearer {self._api_key}"` in a request **header** to a
hardcoded `https` endpoint — never in a URL, never in a body, never in a log
line. **PASS.**

**V-36 — the read path never sees the credential.** `grep -nE
'api_key|credential|Authorization'` over `app/terms.py`, `app/repository.py`,
`app/db.py`, `app/models.py` returns exactly one line: a **comment** on
`app/terms.py:27`'s `# noqa: S105` explaining why a regex is not a credential. No
credential reference of any kind in the read path. **PASS** — `NFR2.5` measured
rather than repeated.

**V-37 — the suppression census.** 15 suppressions repo-wide: **7 ×**
`# pragma: no cover` (3 in `app/`, 4 in `tests/`), **4 ×** `# noqa: S310` (all in
`app/`, all on the two `urllib` calls, each beside a "hardcoded https constant"
justification), **1 ×** `# noqa: S105` in `app/terms.py:27`, **1 ×** `# noqa:
S104` in `tests/test_routes.py:355` (the loopback-refusal host list), **2 ×**
`# type: ignore[method-assign]` in `tests/conftest.py`, **0** file-level
`# ruff: noqa`. **PASS** — all narrow and justified, and the security budget in
`app/` is **5**, not the 4 recorded upstream. See **F-04**.

**V-38 — TLS.** No bypass anywhere in `app/` (V-18). **PASS.**

### F. Gate set and the recorded verification command

**V-41 — gate set, measured.** `ruff check app tests` → **"All checks passed!"**
`ruff format --check app tests` → **"30 files already formatted"**
`compileall -q app tests` → **exit 0**. These are `cd-config.md` R3/R4 (G2, G3)
and `build-instructions.md` §4. **PASS.**

**V-42 — the suite, both invocations.**

| Invocation | Result |
|---|---|
| `env -u APPIMAGE .venv/bin/python -m pytest` | **192 passed in 1.82 s**, `TOTAL 884 stmts / 26 missed / 97.06 %`, floor 80 % reached, **exit 0** |
| `.venv/bin/python -m pytest` (prefix omitted) | **1 failed, 191 passed, exit 1** — `test_each_analytics_endpoint_answers_inside_the_budget`, the spawned-interpreter budget test |

**PASS** for `cd-config.md` **D3** — the `env -u APPIMAGE` requirement is
load-bearing and re-measured here, not inherited.

**V-43 — the whole suite never touches the real store.** sha256 of
`data/sentiment.db` before and after a full `pytest` run: **identical**. **PASS.**
The `tmp_settings` / `tmp_db_path` scoping in `tests/conftest.py:298-315` holds.

**V-44 — the recorded verification command, step by step.**

| Step | Command | Measured |
|---|---|---|
| 1 | `python -m pip install -e ".[dev]"` | **exit 1 — PEP 668.** Pre-existing; two remedies proven in V-03 and in `build-instructions.md` §2.3. |
| 2 | `python -m pytest -q` | **exit 0** — 192 passed, 97.06 % |
| 3 | boot real `uvicorn` on `127.0.0.1:8141`, read `/v1/health` | **exit 0** — `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` |

Steps 2 and 3 executed **verbatim**. Step 1 executed verbatim and failed on the
host interpreter; the documented venv substitute exits 0. **Same conclusion
`build-instructions.md` §5 reached, independently re-measured on the current
tree.** And per V-15, step 3's boot **does not** write to the store while the
store is at v4 — so the hazard `cd-config.md` §5 describes is real but currently
inert. See **F-01**.

### G. Data classification and regulatory scope

`aidlc-compliance-agent`. Classification is by **what the code writes**, read from
`app/repository.py:32-73` (`_INSERT_SQL`, a fully bound `INSERT`) and the DDL at
`app/db.py:65-77`.

| Column | Class | Measured origin |
|---|---|---|
| `text` | **Free text, operator-supplied — the only field that can carry anything** | The submitted body, stored verbatim. |
| `label` | **Closed vocabulary** — `CHECK (label IN ('positive','negative','neutral'))`, enforced at the schema level | Derived by the engine. |
| `probabilities`, `confidence` | **Derived numerics** | `json.dumps(dict(result.probabilities))`, a float; both outputs of the engine. |
| `intensity` | **Retired**; nullable and `NULL` on every row the application has ever written | Kept only so a pre-v1 row survives a rebuild. |
| `model`, `provider` | **Fixed vocabulary** | The resolved model id and engine name. |
| `created_at` | **Timestamp**, `%Y-%m-%dT%H:%M:%SZ`, UTC | `format_timestamp` (`app/repository.py:39-41`). |
| `import_id` | **Server-generated grouping key** — `uuid.uuid4().hex`, `NULL` for a single analysis | `app/service.py:150`. **Not an operator-supplied identifier.** |

**The store therefore holds exactly four classes of value: free text, a three-value
label, derived numbers, and provenance.** No identity document, no account number,
no contact detail, no credential.

**Regulatory scope — none of the four major frameworks applies, and the reasons
are structural:**

| Framework | In scope? | Why, measured rather than asserted |
|---|---|---|
| **GDPR** | **No** | Art. 4 needs personal data relating to an identified or identifiable natural person. There is **no subject**: the operator is the only actor, no user account exists, the app is unauthenticated by design, and no identifier column exists — `import_id` is a server-generated `uuid4().hex`, not something the operator supplies. It also would not apply to a household-only processing activity (Art. 2(2)(c)), which a single-operator localhost tool is. The store holds **0 rows** in any case. |
| **CCPA / CPRA** | **No** | "Consumer" and "personal information" both require information relating to an identified or identifiable natural person **in California or for a commercial purpose**. No commercial purpose exists: nothing is sold, shared or monetised, and there is no service provider relationship. |
| **HIPAA** | **No** | The **scope condition** — a covered entity or business associate handling ePHI — is not met. There is no PHI in the store, no covered entity, and no BAA. The encryption-at-rest mandate is therefore not merely unmet, it is beside the point. |
| **PCI DSS** | **No** | The **scope condition** — merchant, service provider or issuer holding, processing or transmitting cardholder data — is not met. No PAN, no expiry, no CVV, no track data, and nothing resembling a payment identifier is stored or processed. |

**What would change the answer — stated precisely, because "none apply" is only
honest alongside its own falsifiers:**

1. **The operator pastes third-party personal data into `text`.** The schema does
   not stop it: `text` is `TEXT NOT NULL` with no length limit and no content
   constraint, and `POST /v1/analyses/import` accepts a whole CSV. The moment the
   store holds another person's identifiable data and the app is used on their
   behalf, GDPR/CCPA scope questions become real — **through the operator's
   input, not through any code change.**
2. **`mode = "openrouter"` is turned on.** The same free text then leaves the
   machine: `app/openrouter_client.py:89-96` POSTs it to a hardcoded third-party
   `https` endpoint. That creates a **transfer** and a **processor relationship**,
   and it is the single change that would move this system from "no external
   service" to "external data processing." Currently `config.local.toml` does not
   exist and the measured mode is `offline` (V-16).
3. **The app is bound to a non-loopback interface or hosted.** Already foreclosed
   by enforcement (V-07) and by `memory/project.md` `## Mandated`, which requires
   a fresh threat model for any such change.

**At-rest posture, stated without softening:** the store is **unencrypted**
(plain SQLite format 3, zero SQLCipher markers) and **world-readable** (mode 644)
(V-12). For this data on a single-user localhost host with no backup, that is a
deliberate, recorded posture — `memory/team.md` § Deployment already says the
text *"is stored unencrypted in the gitignored database"* — not an oversight, and
not a claim of protection.

**Retention:** there is **no retention policy and no delete endpoint**. The rows
live until the operator deletes the file or uses CSV export/import. That is a
recorded property, not a compliance gap, because no framework in scope imposes
one; it would become one under the change in item 1 above.

---

## 4. Findings

Four. None is a code defect; none was fixed here, because fixing any of them
would mean modifying application source, tests, configuration or the store, which
this stage did not do.

### F-01 — `cd-config.md` §5 over-generalises the store hazard; the mutation is conditional

**Severity: informational — the mitigation (R5, R6) is unaffected.**
`cd-config.md` §5 states that *"any `uvicorn app:app` from the repository root …
migrates `data/sentiment.db`"* and *"that is why the local store moved from
version 2 to 4 during this project's own Bolt-1 verification."* Both halves are
correct about what happened — the store **was** at v2 then. Measured now: booting
the recorded step 3 against a byte-identical clone of a v4 store leaves both the
**sha256 and the mtime unchanged** (V-15), and a second boot after a forced v3
downgrade **does** rewrite the file (V-14). So the accurate statement is:

> The startup migration writes the store **if and only if** that store is behind
> `SCHEMA_VERSION`. On a store already at v4 it is provably write-neutral, down to
> the mtime. The operator's store is at v4 (V-11), so the approved verification
> command's step 3 is currently inert.

**Why it is worth recording:** the current wording reads as though every boot
writes, which would push an operator toward treating R5 as mandatory-every-boot
habit rather than the release step it actually is — or, read the other way, to
assume the hazard has gone away. Neither reading is right. **R5 and R6 stand.**
R5's protection is needed exactly when a v3 store reappears, and the `beeb587`
rollback path in RB2 is how that happens.

### F-02 — the rollback runbook's RB1 exit code is ambiguous about which process it names

**Severity: informational — the diagnostic instruction is correct.**
`rollback-runbook.md` §2 records *"uvicorn process exit code: 1."* Measured across
three invocation shapes: **uvicorn's own** exit is **3** (both foreground forms);
**1** is the exit code of the *foreground script* in R6's shape, where uvicorn
runs in a daemon thread and the uncaught `URLError` from `urllib` propagates
(V-21). Both processes print the same `sqlite3.IntegrityError`, and that line
**is** present in the recorded command's output (V-20), so RB1's instruction to
grep for it works. The one-line correction is that the code to look for is
**either 1 or 3 depending on the invocation**, and the `IntegrityError` line is the
reliable signal.

### F-03 — the fake-key fixture count recorded upstream is wrong; the measured number is seven

**Severity: informational.** `memory/team.md` § Deployment and `FR7.3` both say
*"the four known fake-key fixtures"*; the advisory review over `user-stories`
counted **six**. Measured across the tree: **seven** distinct `sk-or-v1-*`
literals — `tests/test_config.py:23` (`0123456789abcdef0123456789abcdef`),
`test_auth_routes.py:25-26` (`session-key`, `from-config`),
`test_live_client.py:27` (`live-key`), `test_routes.py:268` (`not-used-here`),
`test_service.py:95` (`session`), `test_service.py:181, 277` (`from-config`) —
plus the truncated `sk-or-v1-…` in `README.md:121`. **All are placeholders; zero
real credentials** (V-33). The count matters for exactly one purpose: the
allowlist a future secret scanner needs (`FR7.3`), and an allowlist built from
"four" would leave three fixtures as false positives on the first run.

---

### F-04 — the recorded suppression census is stale: 15 total, and 5 security suppressions in `app/`

**Severity: informational.** `memory/team.md` § Code Style records *"nine in
total, all narrow and justified — 4 × `# pragma: no cover` … 4 × `# noqa: S310` …
2 × `# type: ignore[method-assign]`"* and calls the four `S310`s *"the entire
security-suppression budget in the repository."* Measured (V-37): **15**
suppressions — **7** `pragma: no cover`, **4** `S310`, **1** `S105`
(`app/terms.py:27`, a regex misreading as a credential), **1** `S104`
(`tests/test_routes.py:355`, the non-loopback host list), **2** `type: ignore`,
**0** file-level. The security budget **in `app/` is 5, not 4**, because
`app/terms.py` — this intent's own module — added one after that snapshot. The
characterisation ("narrow and justified") still holds; only the census is stale.

---

## 5. What was **not** validated, and why absence is not coverage

| Not validated | Why |
|---|---|
| Anything on AWS | No account, no CLI, no credential, no IaC — M1, M2, M3, M5. Nothing was provisioned, so there is nothing to validate and **no stack-deployment log**, which Step 4 nominally asks for. |
| Any environment **tier** | There is one environment. `cd-config.md` §2. |
| **Concurrency** under a real server load | The harness that can host it (`tests/conftest.py:266-315`) exists, but R-01's reproducing test is `u3`'s work, and this stage ran no load. `rollback-runbook.md` §5 correctly excludes connection-level faults from its coverage. |
| **R-01** (cross-thread SQLite connection defect) | Out of scope for an environment validation, and it remains accepted with no reproducing test against the in-process harness. Not re-litigated here. |
| **Live-mode behaviour** | `config.local.toml` does not exist and the measured mode is `offline` (V-16). Exercising live mode needs a real credential, which `memory/project.md` `## Forbidden` forbids putting into any artifact, and this stage has no authority to spend the operator's key. |
| **The `u4-platform-packaging` verification script** | Does not exist yet (`FR7.2`). R3/R4 above are the command form of the same gates; when the script lands they become arguments to it. |
| **Cross-machine reproducibility** | One machine, no remote, no second host. This is precisely the claim the lockfile (`FR7.1`) is meant to close, and it cannot be closed today. |
| **A Well-Architected review, as a review** | Its six pillars are cloud constructs — multi-AZ, IAM, KMS, autoscaling, Cost Explorer, Graviton — and **none has a counterpart in a single loopback process over one local file.** The Security pillar's relevant questions are answered above (V-28 … V-40) and the Reliability pillar's by RB1/RB2/RB3; the other four have **nothing to assess**, and listing them as "not applicable" would be padding rather than rigour. |

---

## 6. Reproducing this report

Every check above is a plain command against the current tree. Nothing needs a
remote, a second environment, a registry or a credential. The two preconditions
`cd-config.md` §4 lists are the two that matter here:

| # | Precondition | State in this run |
|---|---|---|
| **D1** | Source is a git working tree | **met** — `.git` present, so `tests/test_config.py`'s `git check-ignore` assertion holds |
| **D2** | `git` on `PATH` | **met** — `git version 2.56.0` |
| **D3** | `env -u APPIMAGE` on every interpreter invocation | **met**, and load-bearing (V-42) |
| **D4** | CPython ≥ 3.11 | **met** — 3.14.7 |
| **D5** | Install is a **venv** | **met** — `.venv/bin/python`, exit 0 (V-03) |
| **D6** | The bind stays loopback | **met and enforced** — V-07 |
| **D7** | No release step reaches the network except the install | **met** — V-28, V-30; PyPI was not contacted during validation beyond the already-installed venv |

**Zero application source, test, configuration or data-store file was modified by
this stage.** Final `git status --short` differs from the baseline only in the
AI-DLC record tree this stage's own artifacts live in, and
`git diff --stat app tests pyproject.toml config.example.toml README.md` is
**empty**. The real store's sha256 and mtime are unchanged from the first
measurement to the last (V-19).