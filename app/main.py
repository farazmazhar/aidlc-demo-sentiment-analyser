"""ASGI entry point and application factory.

Single responsibility: assemble the application — resolve settings, bring the
database schema to v1 on startup, log the active mode exactly once, mount the
versioned API, the page and the static assets — and expose it as `app:app` for
`uvicorn`. (FR1.4, FR1.5, FR3.1, FR3.3, FR4.7, FR5.1, NFR4, NFR6)
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
)
from app.sentiment import SentimentAuthError, SentimentEngineError
from app.service import InvalidTextError, LiveKeyMissingError, effective_connection
from app.session_auth import SessionAuth

#: The only bind address this app is ever served on (BR5.2, FR4.7, NFR5.1).
HOST = "127.0.0.1"
PORT = 8000

logger = logging.getLogger("app.main")


def _configure_logging() -> None:
    """Ensure the app's own log lines are visible in the process output (FR1.4).

    uvicorn configures only its own loggers, so without this the startup line
    naming the active mode would be dropped by the last-resort handler.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")


def create_app(
    settings: Settings | None = None, session_auth: SessionAuth | None = None
) -> FastAPI:
    """Build the application.

    `settings` lets tests inject a temporary database, and `session_auth` lets
    them inject a session store whose code exchange is a double, so no test ever
    reaches OpenRouter.
    """
    _configure_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resolved = settings if settings is not None else load_settings()
        application.state.settings = resolved
        # The connection store is process memory: a restart starts disconnected,
        # and no key obtained in-app is ever written anywhere (BR6.1, NFR2).
        store = application.state.session_auth
        # First-run readiness: the database is created here if it does not exist,
        # and brought to the v1 shape in place if it predates the contract, so a
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
    application.include_router(router)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(InvalidTextError, handle_invalid_text)
    application.add_exception_handler(LiveKeyMissingError, handle_live_key_missing)
    application.add_exception_handler(SentimentAuthError, handle_auth_error)
    application.add_exception_handler(SentimentEngineError, handle_engine_error)

    return application


app = create_app()
