"""The HTTP surface: one page, two versioned JSON APIs, one health endpoint.

Single responsibility: translate HTTP requests into service calls, read calls and
service failures into one consistent error envelope, and nothing else. No
sentiment logic and no SQL live here — the engine arrives through `app.service`,
the stored rows through the repository and the analytics aggregates through
`app.analytics`. (FR4.1-FR4.7, BR4.1-BR4.4, BR2.10)

The v1 data routes are served under the versioned prefix `/v1` and are frozen
(BR4.2, D3). The read-only analytics surface is served under `/v2` on its own
router, which is additive: `/v1` paths, shapes, envelope and client interface do
not move (BR4.7). The page's own `/`, its `/static/*` assets and the `/auth/*`
support routes carry no data contract, so they stay unversioned. The bulk CSV
surface (`POST /v1/analyses/import`, `GET /v1/analyses/export`) is additive under
the same router (FR1.1, FR2.1).
"""

from __future__ import annotations

import csv
import io
import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from app import db
from app.analytics import (
    DEFAULT_TERM_LIMIT,
    RangeError,
    read_summary,
    read_terms,
    resolve_range,
)
from app.config import Settings
from app.models import AnalyzeRequest, undeclared_body_fields
from app.repository import DEFAULT_LIST_LIMIT, list_analyses, list_analyses_by_import_id
from app.sentiment import SentimentAuthError, SentimentEngineError
from app.service import (
    InvalidTextError,
    LiveKeyMissingError,
    analyze_text,
    effective_connection,
    get_client,
    import_texts,
    require_text,
)
from app.session_auth import AuthExchangeError, SessionAuth

#: Where the page and its assets live.
STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

#: The version prefix every v1 data route is served under (BR4.2, D3).
V1_PREFIX = "/v1"

#: The version prefix the analytics read surface is served under. A named constant
#: on both sides of the wire: `app/static/app.js` holds the second copy and a test
#: asserts the two are equal, so a prefix change cannot silently break every
#: analytics fetch (BR2.13, AC6.2.3).
V2_PREFIX = "/v2"

#: Machine-readable codes used in the error envelope (BR4.3).
VALIDATION_FAILED = "VALIDATION_FAILED"
INVALID_TEXT = "INVALID_TEXT"
LIVE_KEY_MISSING = "LIVE_KEY_MISSING"
SENTIMENT_ENGINE_ERROR = "SENTIMENT_ENGINE_ERROR"
AUTH_EXPIRED = "AUTH_EXPIRED"
IMPORT_NOT_FOUND = "IMPORT_NOT_FOUND"
#: The one addition this feature makes to the envelope's code set: a store that
#: cannot answer is distinguishable from a malformed parameter, so a client can
#: branch on the code rather than on the message (BR4.5, NFR4.2). The same literal
#: is written into the log record as well as onto the wire, so the two agree and an
#: operator can match a server-side line to a response body (BR4.6, NFR8.2).
STORAGE_FAILURE = "STORAGE_FAILURE"

#: The content types the bulk-import body may use (FR1.7). `text/plain` is
#: accepted so the same CSV can be posted without a CSV-specific type.
IMPORT_CONTENT_TYPES = frozenset({"text/csv", "text/plain"})

#: Columns of the bulk-export CSV, pinned by the FR2.2 contract.
EXPORT_COLUMNS = ("id", "text", "label", "confidence", "model", "provider", "created_at")

logger = logging.getLogger("app.routes")


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Build the one error envelope every app-raised failure uses (BR4.3).

    The envelope is exactly `{code, message}` — the contract's `ErrorEnvelope`
    sets `additionalProperties: false`, so no field-level array is added: the
    message itself names the offending field or the file to fill in.
    """
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
    )


def get_settings(request: Request) -> Settings:
    """The settings resolved at startup (FR1.1)."""
    return request.app.state.settings


def get_session_auth(request: Request) -> SessionAuth:
    """The session's in-app OpenRouter connection (in memory only)."""
    return request.app.state.session_auth


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    """Hand this request its own SQLite connection, and close it when it finishes.

    **The connection lifecycle, stated here rather than inherited.** Exactly one
    connection is created per request and closed in this `finally`, so the
    request that opened it is the request that closes it. Nothing is cached,
    pooled, stored on a module global or shared between two concurrent requests.

    **Thread affinity.** The driver is opened by `app.db.connect` with
    `check_same_thread=False`, and that decision is only safe because of the
    invariant above: a synchronous dependency and a synchronous handler run on
    worker threads that are not guaranteed to be the same one, so the driver's
    same-thread default would refuse a connection this application legitimately
    hands between threads of a single request. If a future change pools or shares
    a connection, the guard must be re-enabled or the sharing made thread-safe
    (FR1.6, R-01).
    """
    connection = db.connect(request.app.state.settings.db_path)
    try:
        yield connection
    finally:
        connection.close()


async def require_declared_fields(request: Request) -> None:
    """Refuse a body carrying a field `AnalyzeRequest` does not declare (BR4.3).

    `AnalyzeRequest` is a plain dataclass, so an unknown key would otherwise be
    dropped silently; the contract's `additionalProperties: false` makes it a
    refusal. The raw body is checked before the body validator runs, and an
    unknown key is reported as the same `422 VALIDATION_FAILED` every other
    rejected body produces. A body that is not valid JSON is left to that
    validator, which already refuses it.
    """
    try:
        body = await request.json()
    except ValueError:  # absent, malformed or non-UTF-8 JSON: the body validator's own refusal
        return
    undeclared = undeclared_body_fields(body)
    if undeclared:
        raise RequestValidationError(
            [
                {
                    "type": "extra_forbidden",
                    "loc": ("body", name),
                    "msg": "Extra inputs are not permitted",
                    "input": None,
                }
                for name in undeclared
            ]
        )


#: Page and support routes: unversioned, because they carry no data contract.
router = APIRouter()

#: The versioned JSON API (BR4.2).
v1_router = APIRouter(prefix=V1_PREFIX)

#: The read-only analytics API, additive under its own prefix (BR4.7).
v2_router = APIRouter(prefix=V2_PREFIX)


@router.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """Serve the single page: submit form, result panel and history (FR4.1, FR4.4)."""
    return HTMLResponse(content=INDEX_HTML.read_text(encoding="utf-8"))


@v1_router.post("/analyze")
def post_analyze(
    request: Request,
    payload: AnalyzeRequest,
    _declared: None = Depends(require_declared_fields),
    settings: Settings = Depends(get_settings),
    connection: sqlite3.Connection = Depends(get_connection),
) -> JSONResponse:
    """Analyse submitted text, store it, and return the stored record (FR4.1).

    The text is validated before the engine is resolved, so an empty submission
    is refused as invalid input even when live mode is also unconfigured (W1
    steps 2-4). A live request with no usable key raises `LiveKeyMissingError`,
    which the handler maps to `503 LIVE_KEY_MISSING` with nothing stored. A body
    carrying a field the contract does not declare is refused by
    `require_declared_fields`, which runs before the body is validated.
    """
    credential = get_session_auth(request).credential()
    cleaned = require_text(payload.text)
    record = analyze_text(get_client(settings, credential), connection, cleaned)
    return JSONResponse(status_code=200, content=record.to_dict())


@v1_router.get("/analyses")
def get_analyses(
    limit: int = Query(DEFAULT_LIST_LIMIT, ge=1),
    connection: sqlite3.Connection = Depends(get_connection),
) -> list[dict[str, object]]:
    """Return stored analyses newest-first as a JSON array, `limit` of them (FR4.2).

    An absent `limit` applies the documented default (`DEFAULT_LIST_LIMIT`, 50);
    a value below one or not a number is refused by the validation handler rather
    than clamped (BR3.5, BR3.6, D2).
    """
    return [record.to_dict() for record in list_analyses(connection, limit=limit)]


@v1_router.post("/analyses/import")
def post_analyses_import(
    request: Request,
    payload: bytes = Body(default=b""),
    settings: Settings = Depends(get_settings),
    connection: sqlite3.Connection = Depends(get_connection),
) -> JSONResponse:
    """Analyse a CSV body in bulk and report the aggregate (FR1.1-FR1.7).

    The body is CSV with one text per row; an exact `text` first row is a header
    and is skipped (FR1.2). Rows are analysed sequentially through the same
    engine seam as single analysis (`get_client` + `analyze_text`), and blank or
    unanalyzable rows are skipped without aborting the request (FR1.3, FR1.4).
    The response carries the shared `import_id`, the imported/skipped counts, the
    per-label breakdown and the mean confidence (FR1.5); zero imported rows are
    still a `200` with zeros and a null mean (FR1.6). A body that is neither
    `text/csv` nor `text/plain`, or that cannot be parsed as CSV, is refused
    through the envelope (FR1.7).

    The raw body arrives as a `bytes` parameter so FastAPI reads it before
    dispatching to this (sync) handler — the same worker-thread path the
    single-analysis route uses for its per-request connection.
    """
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type not in IMPORT_CONTENT_TYPES:
        return error_response(
            422,
            VALIDATION_FAILED,
            "The request body must use Content-Type text/csv (or text/plain).",
        )

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return error_response(422, VALIDATION_FAILED, "The request body must be UTF-8 CSV text.")
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        return error_response(422, VALIDATION_FAILED, f"The request body is not valid CSV: {exc}.")

    if rows and rows[0] == ["text"]:
        rows = rows[1:]
    texts = [row[0] if row else "" for row in rows]

    credential = get_session_auth(request).credential()
    summary = import_texts(get_client(settings, credential), connection, texts)
    return JSONResponse(status_code=200, content=summary.to_dict())


@v1_router.get("/analyses/export")
def get_analyses_export(
    import_id: str = Query(...),
    connection: sqlite3.Connection = Depends(get_connection),
) -> Response:
    """Return the rows persisted under one `import_id` as a CSV attachment (FR2).

    The columns are pinned by `EXPORT_COLUMNS` and the rows come back newest-first
    (FR2.2); the response is `text/csv` with an attachment filename (FR2.3). An
    `import_id` with no matching rows is a `404` through the envelope (FR2.4),
    the query parameter is required (FR2.5), and rows written by single analysis
    (null `import_id`) are never included (FR2.6).
    """
    records = list_analyses_by_import_id(connection, import_id)
    if not records:
        return error_response(
            404,
            IMPORT_NOT_FOUND,
            f"No analyses were found for import_id {import_id!r}.",
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for record in records:
        writer.writerow(
            [
                record.id,
                record.text,
                record.label,
                record.confidence,
                record.model,
                record.provider,
                record.created_at,
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="analyses-{import_id}.csv"'},
    )


@v1_router.get("/health")
def health(request: Request, settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Report the active engine and the live connection state (FR1.6, BR4.4).

    The payload is exactly the contract's `Health` — active mode, connected flag
    and a reason present only when the app is not connected — and never carries
    credential material (AC5.3.1).
    """
    store = get_session_auth(request)
    connection = effective_connection(settings, store.credential(), store.reason())
    payload: dict[str, object] = {
        "mode": connection["mode"],
        "connected": connection["connected"],
    }
    if not connection["connected"]:
        payload["reason"] = connection["reason"]
    return payload


# -- the read-only /v2 analytics surface ---------------------------------------
#
# Both handlers hold no statement text and no query helper: validation and range
# resolution happen here, and every aggregate is computed by `app.analytics` from
# the connection this module owns (BR2.10). Reads go route -> read module; the
# service layer is not inserted into the analytics path.


@v2_router.get("/analytics/summary")
def get_analytics_summary(
    from_bound: str | None = Query(None, alias="from"),
    to_bound: str | None = Query(None, alias="to"),
    import_id: str | None = Query(None),
    connection: sqlite3.Connection = Depends(get_connection),
) -> JSONResponse:
    """Aggregate the resolved range into the six-field summary (FR2.1-FR2.10).

    `from`, `to` and `import_id` are all optional and no parameter is ever
    silently defaulted or clamped. Validation and the inverted-range refusal
    happen **before** anything is computed, so a refused request pays no read cost
    and returns no aggregate at all (BR1.4, BR4.2, BR4.3). A range matching no row
    is a `200` with `total` 0 and an empty series, never a `404` (BR4.4); a store
    that cannot answer is a `500 STORAGE_FAILURE`, which is distinct from every
    validation code (BR4.5).
    """
    try:
        resolved = resolve_range(from_bound, to_bound)
    except RangeError as exc:
        return error_response(422, VALIDATION_FAILED, str(exc))

    try:
        summary = read_summary(connection, resolved, import_id)
    except sqlite3.Error as exc:
        logger.error("analytics summary read failed (%s): %s", STORAGE_FAILURE, exc)
        return error_response(
            500, STORAGE_FAILURE, "The analytics store could not answer the request."
        )

    return JSONResponse(status_code=200, content=summary.to_dict())


@v2_router.get("/analytics/terms")
def get_analytics_terms(
    from_bound: str | None = Query(None, alias="from"),
    to_bound: str | None = Query(None, alias="to"),
    import_id: str | None = Query(None),
    limit: int = Query(DEFAULT_TERM_LIMIT, ge=1),
    connection: sqlite3.Connection = Depends(get_connection),
) -> JSONResponse:
    """Rank the leading terms of the resolved range, per label (FR3.2-FR3.7).

    The bounds resolve exactly as they do on the summary endpoint, so the two
    always describe one population (BR1.5). `limit` is `Query(..., ge=1)`, so a
    value below one or a non-numeric one is refused by the shared validation
    handler through the same envelope `limit` uses on `/v1` — never clamped — and
    an oversized value returns every available term instead (BR2.6). The payload is
    exactly `{positive, negative}`; a no-match range yields two empty arrays
    (BR4.4).
    """
    try:
        resolved = resolve_range(from_bound, to_bound)
    except RangeError as exc:
        return error_response(422, VALIDATION_FAILED, str(exc))

    try:
        terms = read_terms(connection, resolved, import_id, limit)
    except sqlite3.Error as exc:
        logger.error("analytics terms read failed (%s): %s", STORAGE_FAILURE, exc)
        return error_response(
            500, STORAGE_FAILURE, "The analytics store could not answer the request."
        )

    return JSONResponse(status_code=200, content=terms.to_dict())


# -- in-app OpenRouter authorization (page support, no data contract) ---------


@router.get("/auth/status")
def auth_status(request: Request, settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Report whether the app is connected and from where, for the page (FR5.3)."""
    store = get_session_auth(request)
    return effective_connection(settings, store.credential(), store.reason())


@router.get("/auth/openrouter/start")
def auth_start(request: Request) -> RedirectResponse:
    """Send the browser to OpenRouter to authorize this app (PKCE, S256)."""
    store = get_session_auth(request)
    callback_url = str(request.url_for("auth_callback"))
    return RedirectResponse(store.start(callback_url), status_code=302)


@router.get("/auth/callback")
def auth_callback(request: Request, code: str | None = None) -> RedirectResponse:
    """Exchange the returned code for a key and keep it for this session only.

    Every failure path records its reason in the session store, so the page can
    report it after the redirect; the app stays usable on the offline engine
    (BR6.1, BR6.2, AC6.1.5).
    """
    store = get_session_auth(request)
    if not code:
        store.expire("OpenRouter redirected back without an authorization code.")
        return RedirectResponse("/?auth=failed", status_code=302)
    try:
        store.complete(code)
    except AuthExchangeError as exc:
        logger.warning("OpenRouter authorization failed: %s", exc)
        return RedirectResponse("/?auth=failed", status_code=302)
    return RedirectResponse("/?auth=connected", status_code=302)


@router.post("/auth/disconnect")
def auth_disconnect(
    request: Request, settings: Settings = Depends(get_settings)
) -> dict[str, object]:
    """Forget the session credential and fall back to the offline engine."""
    store = get_session_auth(request)
    store.disconnect()
    return effective_connection(settings, store.credential(), store.reason())


# -- error envelope wiring ---------------------------------------------------


def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Map a rejected request body or query parameter onto the envelope (BR4.3).

    The envelope has no field array, so the message names the offending field
    itself.
    """
    errors = exc.errors()
    if errors:
        first = errors[0]
        field = ".".join(str(part) for part in first.get("loc", ())) or "request"
        message = f"{field}: {first.get('msg', 'Invalid value.')}"
    else:  # pragma: no cover - FastAPI always reports at least one error
        message = "One or more request fields failed validation."
    return error_response(422, VALIDATION_FAILED, message)


def handle_invalid_text(request: Request, exc: InvalidTextError) -> JSONResponse:
    """Reject empty or whitespace-only text with 422 and no row written (BR4.1)."""
    return error_response(422, INVALID_TEXT, str(exc))


def handle_live_key_missing(request: Request, exc: LiveKeyMissingError) -> JSONResponse:
    """Refuse a live attempt with no usable key, naming the config file (BR1.4, D1)."""
    return error_response(503, LIVE_KEY_MISSING, str(exc))


def handle_engine_error(request: Request, exc: SentimentEngineError) -> JSONResponse:
    """Map a live-engine failure onto the envelope instead of a bare 500 (BR4.3)."""
    return error_response(
        503,
        SENTIMENT_ENGINE_ERROR,
        "The sentiment engine could not produce a decision.",
    )


def handle_auth_error(request: Request, exc: SentimentAuthError) -> JSONResponse:
    """Drop a credential OpenRouter has rejected, and say so (BR6.2).

    Dropping the credential here is what turns the page's indicator red again
    after an expiry: the next request runs the offline engine and the status
    endpoint reports the reason.
    """
    store = getattr(request.app.state, "session_auth", None)
    if store is not None:
        store.expire(str(exc))
    return error_response(503, AUTH_EXPIRED, str(exc))
