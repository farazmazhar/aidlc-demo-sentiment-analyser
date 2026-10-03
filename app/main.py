"""ASGI entry point and application factory.

Single responsibility: assemble the application — resolve settings, bring the
database schema to the current version on startup, log the active mode exactly
once, mount the versioned APIs, the page and the static assets — enforce the
loopback bind, and expose it as `app:app` for `uvicorn`. (FR1.4, FR1.5, FR3.1,
FR3.3, FR4.7, FR5.1, FR7.6, NFR4, NFR5, NFR6)

**The loopback bind is enforced, not documented.** `HOST` is the value the run
path actually consumes: `run()` resolves it through `resolve_bind_host` before
starting the server, and `create_app` applies the same check to whatever host it
is given, so a non-loopback host stops startup with an explanation on every path
rather than serving an unauthenticated app holding the operator's key
(FR7.6, AC7.6.1-AC7.6.3).
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app import db
from app.config import Settings, load_settings
from app.routes import (
    STATIC_DIR,
    handle_auth_error,
    handle_engine_error,
    handle_invalid_text,
    handle_live_key_missing,
    handle_validation_error,
    router,
    v1_router,
    v2_router,
)
from app.sentiment import SentimentAuthError, SentimentEngineError
from app.service import InvalidTextError, LiveKeyMissingError, effective_connection
from app.session_auth import SessionAuth

#: The only bind address this app is ever served on (BR5.2, FR4.7, NFR5.1).
HOST = "127.0.0.1"
PORT = 8000

#: The hostnames and addresses that count as loopback. The app is unauthenticated
#: by design and holds the operator's key, so anything outside this set is refused
#: at startup rather than served (FR7.6, NFR5.1).
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

logger = logging.getLogger("app.main")


class NonLoopbackBindError(RuntimeError):
    """Raised when the run path is asked to bind a non-loopback host.

    Serving this app on an exposed interface would put the operator's OpenRouter
    key behind an unauthenticated page, so the refusal is loud and immediate: the
    app does not start rather than start unsafe (FR7.6, AC7.6.1).
    """


def resolve_bind_host(host: str = HOST) -> str:
    """Return `host` if it is loopback, and refuse it loudly otherwise.

    This is the enforcement the documented `uvicorn app:app` invocation never had:
    uvicorn's own default is not our constant, so `uvicorn app:app --host 0.0.0.0`
    used to expose the app while every test still passed. The run path now
    consumes `HOST` through here, and a non-loopback host stops startup with an
    explanation instead of serving (FR7.6, AC7.6.1, AC7.6.2).
    """
    if host not in LOOPBACK_HOSTS:
        raise NonLoopbackBindError(
            f"Refusing to bind {host!r}: this app is unauthenticated and holds the "
            f"operator's API key, so it is served on loopback only. Allowed hosts: "
            f"{', '.join(sorted(LOOPBACK_HOSTS))}."
        )
    return host


def run() -> None:
    """Serve the application on the loopback bind this module pins.

    The bind is resolved **before** the server starts, so a non-loopback host is
    a startup failure rather than a running exposure (FR7.6). `uvicorn` is imported
    here rather than at module scope so importing the application never loads the
    server, which is the same one-construction-site rule `app.service` follows.
    """
    import uvicorn

    uvicorn.run("app.main:app", host=resolve_bind_host(), port=PORT)


def _configure_logging() -> None:
    """Ensure the app's own log lines are visible in the process output (FR1.4).

    uvicorn configures only its own loggers, so without this the startup line
    naming the active mode would be dropped by the last-resort handler.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")


def create_app(
    settings: Settings | None = None,
    session_auth: SessionAuth | None = None,
    host: str = HOST,
) -> FastAPI:
    """Build the application.

    `settings` lets tests inject a temporary database, and `session_auth` lets
    them inject a session store whose code exchange is a double, so no test ever
    reaches OpenRouter. `host` defaults to the pinned loopback bind and is
    validated by the same `resolve_bind_host` the run path uses, so **no** startup
    path can serve on a non-loopback interface (FR7.6, AC7.6.1, AC7.6.3).
    """
    _configure_logging()
    resolve_bind_host(host)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resolved = settings if settings is not None else load_settings()
        application.state.settings = resolved
        # The connection store is process memory: a restart starts disconnected,
        # and no key obtained in-app is ever written anywhere (BR6.1, NFR2).
        store = application.state.session_auth
        # First-run readiness: the database is created here if it does not exist,
        # and brought to the current schema in place if it predates it, so a
        # fresh checkout needs no manual setup step (BR3.1, BR3.3).
        db.init_db(resolved.db_path)
        connection = effective_connection(resolved, store.credential(), store.reason())
        # Exactly one startup line, naming the engine in use and never the key
        # (NFR6.2, BR5.1).
        logger.info(
            "Sentiment analysis app ready in %s mode%s",
            connection["mode"],
            "" if connection["connected"] else " (OpenRouter not connected)",
        )
        yield

    application = FastAPI(
        title="very-cool-sentiment-analysis",
        description="A small local sentiment analysis app (localhost only).",
        lifespan=lifespan,
    )
    application.state.session_auth = session_auth if session_auth is not None else SessionAuth()
    application.include_router(v1_router)
    application.include_router(v2_router)
    application.include_router(router)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(InvalidTextError, handle_invalid_text)
    application.add_exception_handler(LiveKeyMissingError, handle_live_key_missing)
    application.add_exception_handler(SentimentAuthError, handle_auth_error)
    application.add_exception_handler(SentimentEngineError, handle_engine_error)

    return application


app = create_app()
