# Security Test Instructions — intent `261001-analytics-layer`, Unit `u1-analytics-slice`

> **Stage:** `build-and-test` (construction) · **Test strategy:** `standard`
> (this file exists because measurable security NFRs exist —
> `nfr-requirements/security-requirements.md` defines `NFR2.1`–`NFR2.6`, and
> `observability-requirements.md` defines the log-side `NFR8.3`) · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer`
>
> **Inputs this file was derived from** (the stage's declared `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`, plus
> `construction/u1-analytics-slice/nfr-requirements/security-requirements.md`,
> `…/observability-requirements.md` and `construction/u1-analytics-slice/nfr-design/security-design.md`,
> `…/observability-design.md`, `…/reliability-design.md`.

## 1. Framework and configuration

`pytest` for the test-level checks, `ruff` for the static gate, and a small `ast`
walker plus a live `uvicorn` probe for the checks no tool in this repository
performs. Nothing new is installed.

| Layer | Tool | Configuration |
|---|---|---|
| Static (SAST) | `ruff` 0.16.9 with the **pinned, reviewed rule set** in `pyproject.toml`: `select = ["E","F","W","I","N","UP","S","B","C4","SIM"]`, `line-length = 100`, `target-version = "py311"`. `S` is the security set and it applies **in full to `app/`** (`tests/*` is exempted from `S101`, `S105`, `S106`, `S603`, `S607` only) | already configured |
| Static (targeted) | a stdlib `ast` walker — §3.1. It exists because `ruff`'s `S` set does **not** cover the two properties this Unit's security requirements actually assert (zero egress from the read path; statement text as a compile-time constant) | inline, §3.1 |
| Dynamic (DAST) | real `uvicorn` on `127.0.0.1`, injection payloads through the HTTP surface | inline, §3.2 |
| Test-level | `pytest`, real SQLite, real served markup, zero mocks | `pyproject.toml` |

### 1.1 Two facts about the lint set that must not be mistaken for coverage

`team.md` § Code Style records both, and they are repeated here because a security
file that overstates its tooling is worse than one that admits its limits.

* Selecting `S` is a real selection, but **13 of ruff's 73 `S` rules are
  preview-gated and therefore inactive** under a plain `select`, and all 13 are
  *import-side* blacklist checks (`S401` telnetlib, `S403` pickle, `S404` subprocess,
  the XML parsers, `S411` xmlrpc, `S412` httpoxy, `S413` pycrypto, `S415` pyghmi).
  The net catches the dangerous **call**, not the dangerous **import**.
* For secrets it is narrower than it sounds: **`S105` fires on `SECRET = "…"` and does
  not fire on `API_KEY = "…"`** — `API_KEY` is not among ruff's credential-shaped
  identifiers, and it is the most likely name for this project's one secret. §3.1's
  check 6 covers that hole.
* `TID251` `banned-api` layer boundaries are **not** configured. The affirmative rule
  that asks for them (`FR7.5`, project rule "express the layer boundaries as `ruff`
  `TID251` `banned-api` entries") is a `u4-platform-packaging` obligation
  (`AC7.5.1`–`AC7.5.3` are absent from this Unit's traceability). So the boundary is
  **not** lint-enforced today; §3.1's check 1 is the instrument that exists instead,
  and this file does not pretend otherwise.
* Not selected, therefore not caught: `BLE001` (broad `except Exception:`), `T20`
  (`print()`), `T10` (`breakpoint()`), `DTZ` (naive `datetime.now()`). §3.1 checks 5
  and the `print()` rule cover the two that matter here.

### 1.2 `env -u APPIMAGE` is mandatory on this host

The shell exports `APPIMAGE=…opencode-desktop-linux-x86_64.AppImage`, which makes
CPython report the AppImage as `sys.executable`. Any command that spawns a
subprocess — including the offline-guard instrument — fails for that reason alone.
Proof and remedy: `build-instructions.md` §6.

## 2. How to run the whole security suite

```bash
# 2.1 Lint gate (the `S` security set applies in full to app/).
env -u APPIMAGE python -m ruff check app tests

# 2.2 Static targeted checks (§3.1).
env -u APPIMAGE python /path/to/security_static_checks.py          # see §3.1

# 2.3 Dynamic probe against real uvicorn (§3.2).
env -u APPIMAGE PYTHONPATH=. python /path/to/security_dast_probe.py   # see §3.2

# 2.4 Test-level security assertions.
env -u APPIMAGE python -m pytest --no-cov -q \
  tests/test_config.py \
  tests/test_auth_routes.py \
  tests/test_session_auth.py \
  tests/test_analytics_routes.py \
  tests/test_migration_indexes.py \
  tests/test_page.py

# 2.5 The whole suite, with the affirmed coverage floor applied.
env -u APPIMAGE python -m pytest -q
```

## 3. The checks, with their targets

### 3.1 Static (SAST) — zero egress, parameter-bound SQL, no credential

Run from the repository root. It is stdlib-only, takes an optional repository root as
`argv[1]` (used below to prove the checks have teeth), and exits non-zero on any
finding.

```bash
cat > /tmp/security_static_checks.py <<'PY'
import ast, pathlib, re, sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
APP = ROOT / "app"
READ_PATH = ["analytics.py", "terms.py", "models.py"]
FORBIDDEN_IMPORTS = {
    "socket", "ssl", "http", "urllib", "httpx", "requests", "aiohttp",
    "ftplib", "smtplib", "telnetlib", "xmlrpc", "subprocess",
}
NO_PARAMETER_FORMS = ("BEGIN", "COMMIT", "ROLLBACK", "CREATE", "DROP", "ALTER", "PRAGMA", "VACUUM")
DML = re.compile(r"\A\s*(SELECT|INSERT|UPDATE|DELETE|REPLACE)\b", re.IGNORECASE)
FORBIDDEN_IN_STATEMENT = (ast.BinOp, ast.Call, ast.BoolOp, ast.Compare, ast.IfExp, ast.Await)
failures, notes = [], []


def tree_of(path):
    return ast.parse(path.read_text(), filename=str(path))


def is_docstring(node):
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)


print("== 1. zero egress from the analytics read path (NFR2.2) ==")
for name in READ_PATH:
    for node in ast.walk(tree_of(APP / name)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_IMPORTS or alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
                    failures.append(f"{name}:{node.lineno} forbidden import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module in FORBIDDEN_IMPORTS or node.module.split(".")[0] in FORBIDDEN_IMPORTS:
                failures.append(f"{name}:{node.lineno} forbidden import {node.module}")

print("== 2+3. statement text is a constant and every value is bound (NFR2.3, BR2.9) ==")
execute_calls = parameterless_read_path = 0
for path in sorted(APP.glob("*.py")):
    for node in ast.walk(tree_of(path)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in {"execute", "executemany", "executescript"}:
            continue
        execute_calls += 1
        in_read_path = path.name in READ_PATH
        if node.func.attr == "executescript":
            failures.append(f"{path}:{node.lineno} executescript takes no bound parameters")
            continue
        statement = node.args[0] if node.args else None
        for inner in ast.walk(statement) if statement is not None else ():
            if isinstance(inner, ast.JoinedStr):
                for part in inner.values:
                    if isinstance(part, ast.FormattedValue) and not isinstance(part.value, ast.Name):
                        failures.append(
                            f"{path}:{node.lineno} statement f-string interpolates "
                            f"{type(part.value).__name__}, not a module constant"
                        )
            elif isinstance(inner, FORBIDDEN_IN_STATEMENT):
                failures.append(
                    f"{path}:{node.lineno} statement text is built by "
                    f"{type(inner).__name__} at call time"
                )
        if len(node.args) >= 2:
            continue
        literal, form = statement, ""
        if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
            form = literal.value.strip().split(maxsplit=1)[0].upper()
        if any(form == k for k in NO_PARAMETER_FORMS):
            notes.append(f"{path}:{node.lineno} parameterless {form} (expected)")
        elif in_read_path:
            parameterless_read_path += 1
            failures.append(f"{path}:{node.lineno} {node.func.attr} with no bound parameters in the read path")
        else:
            notes.append(f"{path}:{node.lineno} parameterless {form or 'statement'} (outside the read path)")

print("== 4. DML statement literals: every value is a placeholder (NFR2.3) ==")
sql_literals = 0
for path in sorted(APP.glob("*.py")):
    for parent in ast.walk(tree_of(path)):
        body = getattr(parent, "body", None)
        if not isinstance(body, list):
            continue
        for statement_node in body:
            if is_docstring(statement_node):
                continue
            for node in ast.walk(statement_node):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and DML.match(node.value):
                    sql_literals += 1
                    if "?" not in node.value:
                        report = f"{path}:{node.lineno} parameterless DML literal"
                        failures.append(report + " in the read path") if path.name in READ_PATH \
                            else notes.append(report + " (outside the read path)")

print("== 5. no print() anywhere in app/ (NFR8.1) ==")
prints = [
    f"{path}:{node.lineno}"
    for path in sorted(APP.glob("*.py"))
    for node in ast.walk(tree_of(path))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
]
failures.extend(f"{where} print() in app/" for where in prints)

print("== 6. no hardcoded credential literal in app/ (NFR2.5, NFR8.3) ==")
NAMES = ("api_key", "apikey", "secret", "password", "passwd", "token", "bearer")
hardcoded = [
    f"{path}:{node.lineno} {node.targets[0].id}"
    for path in sorted(APP.glob("*.py"))
    for node in ast.walk(tree_of(path))
    if isinstance(node, ast.Assign) and len(node.targets) == 1
    and isinstance(node.targets[0], ast.Name) and node.targets[0].id.lower() in NAMES
    and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and node.value.value
]
failures.extend(f"{where} hardcoded credential" for where in hardcoded)

if notes:
    print("\n  informational (not failures):")
    for note in notes:
        print("   -", note)
if failures:
    print("\nSTATIC CHECKS FAILED")
    for line in failures:
        print("  -", line)
    sys.exit(1)
print("\nSTATIC CHECKS PASSED")
PY

env -u APPIMAGE python /tmp/security_static_checks.py
```

**Measured on this repository: `STATIC CHECKS PASSED`, exit 0.** What it reported:

| Check | Target | Measured |
|---|---|---|
| 1. zero egress from `analytics.py` / `terms.py` / `models.py` | `NFR2.2` | 3 modules against 12 forbidden modules — **0 findings**. Their imports are `re`, `sqlite3`, `collections`, `dataclasses`, `datetime`, `decimal`, `json`, `typing` and `app.models` / `app.sentiment` / `app.terms` |
| 2+3. every `execute`/`executemany` passes bound parameters; statement text is a name / literal / f-string of bare module constants | `NFR2.3`, `BR2.9` | 9 call sites; **0** statement texts built at call time; **0** parameterless statements inside the read path |
| 4. every DML literal carries a `?` | `NFR2.3` | 16 DML literals; **0** failures in the read path |
| 5. no `print()` in `app/` | `NFR8.1` | 15 modules, **0** |
| 6. no hardcoded credential literal | `NFR2.5`, `NFR8.3` | 7 credential-shaped identifiers, **0** literal assignments — **this is the `S105`-does-not-fire-on-`API_KEY` hole, covered** |

**Informational, deliberately not failures:** `app/db.py:232` `BEGIN`, `db.py:215` and
`db.py:270` `PRAGMA`, and 9 parameterless statements outside the read path (schema
DDL, `PRAGMA user_version`, `SELECT sql FROM sqlite_master`, and the three
`CREATE INDEX` re-creations after a rebuild). None takes a request value, so none can
carry one.

**These checks have teeth — demonstrated, not asserted.** Against a deliberately
broken copy of `app/` (`import urllib.request` added to `analytics.py`; the grouped
read's statement changed to `statement + " LIMIT " + str(len(rows))`; and
`API_KEY = "sk-or-v1-realsecret"` added to `db.py`), the same script reports
`STATIC CHECKS FAILED` with exactly:

```
  - analytics.py:29 forbidden import urllib.request
  - .../analytics.py:165 statement text is built by BinOp at call time
  - .../analytics.py:165 statement text is built by Call at call time
  - .../analytics.py:165 execute with no bound parameters in the read path
  - .../db.py:61 API_KEY hardcoded credential
```

Reproduce with: `cp -r app /tmp/broken/`, apply those three edits, then
`python /tmp/security_static_checks.py /tmp/broken`.

### 3.2 Dynamic (DAST) — injection and refusal shapes against real `uvicorn`

This is the check that answers threat **T2** (SQL injection through
`from`/`to`/`import_id`/`limit`) with observed behaviour rather than with inspection.

```bash
cat > /tmp/security_dast_probe.py <<'PY'
import json, sqlite3, tempfile, threading, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

import uvicorn

from app import db
from app.config import Settings
from app.main import create_app

PORT = 8142
BASE = f"http://127.0.0.1:{PORT}"
tmp = Path(tempfile.mkdtemp(prefix="dast-"))
settings = Settings(mode="offline", db_path=tmp / "dast.db")
application = create_app(settings=settings)
db.init_db(settings.db_path)
with sqlite3.connect(settings.db_path) as seed:
    seed.execute(
        "INSERT INTO analyses (text, label, probabilities, confidence, model, provider,"
        " created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("a wonderful lovely great day", "positive",
         '{"positive": 0.8, "neutral": 0.1, "negative": 0.1}', 0.8, "dummy", "offline",
         "2026-01-05T09:00:00Z"),
    )
    seed.commit()

threading.Thread(target=uvicorn.run, args=(application,),
                 kwargs={"host": "127.0.0.1", "port": PORT, "log_level": "error"},
                 daemon=True).start()
for _ in range(60):
    try:
        urllib.request.urlopen(f"{BASE}/v1/health", timeout=1).read()
        break
    except Exception:
        time.sleep(0.25)


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


PAYLOADS = [
    "' OR '1'='1",
    "2026-01-01'; DROP TABLE analyses; --",
    "2026-01-01' UNION SELECT sql,1,1,1 FROM sqlite_master --",
    "1; DELETE FROM analyses",
    "%00",
]

print("== injection probes (every one must be 422 or 200, never 500) ==")
for endpoint in ("/v2/analytics/summary", "/v2/analytics/terms"):
    for parameter in ("from", "to", "import_id", "limit"):
        for payload in PAYLOADS:
            query = urllib.parse.urlencode({parameter: payload})
            status, body = get(f"{endpoint}?{query}")
            assert status in (200, 422), (endpoint, parameter, payload, status, body)
            text = json.dumps(body)
            for leak in ("Traceback", "sqlite3.", "OperationalError", "SQLITE_"):
                assert leak not in text, (endpoint, parameter, payload, leak)

print("== refusal shapes (each 422 names its own field, envelope only) ==")
for path, field in [
    ("/v2/analytics/summary?from=nonsense", "query.from"),
    ("/v2/analytics/summary?to=nonsense", "query.to"),
    ("/v2/analytics/summary?from=2026-02-01&to=2026-01-01", "query.from"),
    ("/v2/analytics/terms?limit=0", "query.limit"),
    ("/v2/analytics/terms?limit=abc", "query.limit"),
]:
    status, body = get(path)
    assert status == 422, (path, status, body)
    assert set(body) == {"code", "message"}, (path, body)
    assert field in body["message"], (path, field, body)
    if "&to=" in path:
        assert "query.to" in body["message"], (path, body)

print("== empty success is a 200, never a 404 and never a failure ==")
status, body = get("/v2/analytics/summary?from=2030-01-01&to=2030-01-07")
assert status == 200 and body["total"] == 0 and body["series"] == [], body
status, body = get("/v2/analytics/terms?from=2030-01-01&to=2030-01-07")
assert status == 200 and body == {"positive": [], "negative": []}, body
status, body = get("/v2/analytics/summary?import_id=no-such-import")
assert status == 200 and body["series"] == [], body

print("== read-only: the store survives the whole probe unchanged ==")
with sqlite3.connect(settings.db_path) as check:
    rows = check.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
assert rows == 1, rows

print("== loopback enforcement: a non-loopback host refuses to start ==")
try:
    create_app(settings=settings, host="0.0.0.0")
except Exception as exc:
    print(f"  refused: {type(exc).__name__}: {str(exc)[:70]}...")
else:
    raise AssertionError("a non-loopback bind was accepted")

print("\nDAST PROBE PASSED")
PY

env -u APPIMAGE PYTHONPATH=. python /tmp/security_dast_probe.py
```

**Measured: `DAST PROBE PASSED`, exit 0.** What it observed:

| Probe class | Result |
|---|---|
| 40 injection probes (2 endpoints × 4 parameters × 5 payloads) | `from`/`to` → **422** (unreadable as a UTC date); `limit` on `/terms` → **422**; `import_id` → **200** (opaque, no parse step, matches nothing); `limit` on `/summary` → **200** (the summary declares no `limit`, so it is ignored). **Never a 500.** |
| Stack-trace / error leakage | **0** hits for `Traceback`, `sqlite3.`, `OperationalError`, `SQLITE_` across all 40 bodies |
| Refusal shapes | 5 × **422**, envelope is exactly `{code, message}`, message names `query.from` / `query.to` / `query.limit`; the inverted range names **both** bounds |
| Empty success | summary `200` `total 0` `series []`; terms `200` `{positive: [], negative: []}`; unmatched `import_id` `200` with an empty series — never a `404` |
| Read-only | row count still **1** after 50+ HTTP requests |
| Loopback enforcement | `create_app(host="0.0.0.0")` → `NonLoopbackBindError: Refusing to bind '0.0.0.0': this app is unauthenticated and holds the operator's API key…` |

The `import_id` result is the designed answer, not a gap: contract `UC1` pins
`import_id` as an opaque string with **no parse step**, so its only failure mode is
"matches nothing" → `200` empty. There is no `422` for `query.import_id` to assert,
and `AC2.4.3` is declared unreachable on exactly that ground.

### 3.3 Test-level security assertions

```bash
# NFR2.1 — the posture is unchanged: no auth/authz added, app still loopback-only
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_analytics_routes.py::test_v1_routes_are_untouched_by_the_v2_surface" \
  tests/test_auth_routes.py tests/test_session_auth.py

# NFR2.2 — the offline guard is PROVED armed, not merely present
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_analytics_routes.py::test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard"

# NFR2.4 — the loopback bind is enforced at startup
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_routes.py::test_the_server_binds_loopback_only"

# NFR2.5 / NFR8.3 — no credential in a repr, a log record, or any body
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_config.py::test_the_key_is_never_rendered_or_logged"

# NFR2.6 — the dependency cap: exactly two runtime packages, dev tools in the extra
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_config.py::test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools"

# NFR8.1 / NFR8.2 — a failure is logged through the module logger WITH its machine code
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_analytics_routes.py::test_a_storage_failure_is_logged_through_the_module_logger_with_its_code"
```

**Measured: all green.** `test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard`
was independently verified to have teeth during Code Generation — removing the guard's
`socket.connect` assignment makes it fail on `ConnectionRefusedError`. That matters
because "zero mock objects" must never be promoted to "no substitution", and because
a guard that is present but silently broken would let a network call pass.

**Instrument availability, stated honestly.** The secret-scanning and dependency-audit
gate (`FR7.3`) **does not exist** — it is a `u4-platform-packaging` obligation, and
`tech-stack-decisions.md` records the scanner as such. `NFR2.5` and `NFR8.3` are
therefore verified by the instruments listed above (redaction assertions, the static
credential-literal check, schema inspection, the armed offline guard, the dependency-cap
assertion) and **not** by a scanner. That is recorded in
`nfr-requirements/security-requirements.md` § NFR2.5 and reproduced here rather than
papered over.

## 4. Expected coverage for this strategy level

The security checks contribute to the **whole-application 80 % line floor**; they carry
no separate coverage target. Measured on the whole suite, the two modules the
injection question is about read `app/analytics.py` **100 %** (112 stmts, 0 missed) and
`app/routes.py` **99 %** (172 stmts, 2 missed — lines 257–258, the pre-existing
`/v1` bulk-import `csv.Error` branch, untouched by this Unit).

The coverage floor says **nothing** about injection safety. It cannot see whether a
value was bound or interpolated. That is why §3.1 and §3.2 exist as separate
instruments, and why `team.md` records that line coverage is the weakest signal
available for exactly this kind of feature.

## 5. Test data and environment setup

| Concern | Arrangement |
|---|---|
| Store | A throwaway `tmp_path` database created by `db.init_db()`; the DAST probe seeds exactly one row so the read path has something to aggregate |
| Bind | `127.0.0.1:8142` for the DAST probe (the recorded verification command uses `8141`; keep them distinct if you run both) |
| Credentials | **None.** The DAST probe constructs `Settings(mode="offline", api_key=None)`. Live-mode paths inject a fake transport, because the affirmed dependency cap forbids an HTTP client library |
| Network | Egress from the read path is impossible by construction and forbidden by test. The only loopback socket is the DAST probe's own server |
| Environment variables | None |
| Ports | `8142` (DAST), `8141` (the recorded verification command). Both are loopback-only; a non-loopback bind is refused by `create_app` |

## 6. Threat coverage — the dispositions, checked

| # | Threat | Instrument that checked it here | Result |
|---|---|---|---|
| T1 | New attack surface from `/v2` reads | Two read-only `GET`s; `NFR3.1`/`NFR3.2` tests; `test_v1_routes_are_untouched_by_the_v2_surface` | Accepted, bounded, no write surface |
| T2 | SQL injection via `from`/`to`/`import_id`/`limit` | §3.1 checks 2–4 **and** §3.2's 40 probes | **Closed** at the mechanism level: every value is a bound parameter; no hostile value changed behaviour |
| T3 | Data exposure through the response | Response schema inspection; terms are derived tokens, not stored text; `resolved_range` is deliberately not serialised (`UC3`) | Accepted: aggregates over the operator's own rows on a loopback surface |
| T4 | Data at rest / privacy (`C-9`) | This Unit adds no egress and no retention/delete path; both out of scope | Considered and recorded, not ignored |
| T5 | Non-loopback exposure of the unauthenticated app | §3.2's `create_app(host="0.0.0.0")` refusal **and** `tests/test_routes.py::test_the_server_binds_loopback_only` | **Closed by enforcement at startup**, not by a documented default |
| — | A secret scanner would strengthen the no-credential claim | Not available in this Unit; a `u4-platform-packaging` dependency | **Unverified by a scanner** — §3.1 check 6 and the redaction assertions are what exists |

## 7. Deferred to a later stage

**No security target in this inventory is deferred.** All of `NFR2.1`–`NFR2.6` and
`NFR8.1`–`NFR8.3` were executed here and are recorded `Met` in
`build-and-test-summary.md`, with one exception recorded as a limitation rather than a
deferral: the `FR7.3` secret scanner is a `u4-platform-packaging` obligation, so no
target's verdict depends on it.

Nothing here needs a deployed or production-like environment. A hosted, externally
reachable instance would change the threat model outright, and `NFR2.1` puts that
outside this scope by affirmed decision ("any non-loopback bind, hosted deploy or
change to the authentication posture requires a fresh threat model").