"""The HTTP surface: one page, one versioned JSON API, one health endpoint.

Single responsibility: translate HTTP requests into service calls and service
failures into one consistent error envelope, and nothing else. No sentiment
logic and no SQL live here — the engine arrives through `app.service` and the
data through the repository. (FR4.1-FR4.7, BR4.1-BR4.4)

The data routes are served under the versioned prefix `/v1` (BR4.2, D3). The
page's own `/`, its `/static/*` assets and the `/auth/*` support routes carry no
data contract, so they stay unversioned.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app import db
from app.config import Settings
from app.models import AnalyzeRequest, undeclared_body_fields
from app.repository import DEFAULT_LIST_LIMIT, list_analyses
from app.sentiment import SentimentAuthError, SentimentEngineError
from app.service import (
    InvalidTextError,
    LiveKeyMissingError,
    analyze_text,
    effective_connection,
    get_client,
    require_text,
)
from app.session_auth import AuthExchangeError, SessionAuth

#: Where the page and its assets live.
STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

#: The version prefix every data route is served under (BR4.2, D3).
V1_PREFIX = "/v1"

#: Machine-readable codes used in the error envelope (BR4.3).
VALIDATION_FAILED = "VALIDATION_FAILED"
INVALID_TEXT = "INVALID_TEXT"
LIVE_KEY_MISSING = "LIVE_KEY_MISSING"
SENTIMENT_ENGINE_ERROR = "SENTIMENT_ENGINE_ERROR"
AUTH_EXPIRED = "AUTH_EXPIRED"

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
    """One short-lived SQLite connection per request, closed when it finishes."""
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
