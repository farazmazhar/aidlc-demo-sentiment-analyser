"""Shared test harness for very-cool-sentiment-analysis.

Three things live here, and nothing else:

1. :func:`asgi_request` - a tiny in-process ASGI caller. `fastapi.testclient`
   is deliberately NOT used: it requires `httpx`, which the dependency cap
   forbids (NFR3.1). This harness drives the real application object instead,
   so route and page tests exercise the real routing, validation, handler and
   persistence path.
2. The `tmp_settings` fixture - settings pointing at a per-test temporary
   database, so no test ever reads or writes the real `config.local.toml` or
   `data/sentiment.db` (NFR2).
3. The session-wide `offline_guard` - an autouse guard that makes every socket
   connection raise, so accidental network use fails loudly instead of
   silently reaching OpenRouter (NFR1.2, BR7.2).
"""

from __future__ import annotations

import asyncio
import json
import socket
from typing import Any, NamedTuple

import pytest

# Scope version of the ASGI spec we advertise to the application.
_ASGI = {"version": "3.0", "spec_version": "2.3"}


class AsgiResponse(NamedTuple):
    """The observable result of one in-process HTTP request."""

    status_code: int
    body: Any  # parsed JSON for JSON responses, decoded text otherwise
    headers: dict[str, str]

    @property
    def text(self) -> str:
        """The response body as text (empty string for JSON bodies)."""
        return self.body if isinstance(self.body, str) else ""


def _build_scope(
    method: str, path: str, query: str, body: bytes, content_type: str | None
) -> dict[str, Any]:
    headers = [(b"host", b"testserver")]
    if content_type is not None:
        headers.append((b"content-type", content_type.encode("latin-1")))
    if body:
        headers.append((b"content-length", str(len(body)).encode()))
    return {
        "type": "http",
        "asgi": _ASGI,
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query.encode("utf-8"),
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 51234),
        "server": ("127.0.0.1", 8000),
    }


async def _request(
    application: Any,
    method: str,
    path: str,
    json_body: Any = None,
    query: str = "",
    body: bytes | None = None,
    content_type: str | None = None,
) -> AsgiResponse:
    if body is None:
        if json_body is None:
            body = b""
        else:
            body = json.dumps(json_body).encode("utf-8")
            content_type = "application/json"
    scope = _build_scope(method, path, query, body, content_type)

    sent = False

    async def receive() -> dict[str, Any]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    messages: list[dict[str, Any]] = []

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    # Entering the lifespan context runs the application's startup, which is
    # where settings are loaded, the schema is created and an older store is
    # migrated (BR3.1, BR3.3).
    async with application.router.lifespan_context(application):
        await application(scope, receive, send)

    start = next(m for m in messages if m["type"] == "http.response.start")
    raw = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    headers = {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    content_type = headers.get("content-type", "")
    if "application/json" in content_type:
        parsed: Any = json.loads(raw.decode("utf-8")) if raw else None
    else:
        parsed = raw.decode("utf-8")
    return AsgiResponse(start["status"], parsed, headers)


def asgi_request(
    application: Any,
    method: str,
    path: str,
    json_body: Any = None,
    query: str = "",
    body: bytes | None = None,
    content_type: str | None = None,
) -> AsgiResponse:
    """Call `application` in-process and return its observable response.

    `path` is the bare path; use `query` for the raw query string so tests can
    send deliberately malformed values such as `limit=abc` (BR3.6). A JSON body
    is passed as `json_body`; a raw body (for example the `text/csv` bulk-import
    payload) is passed as `body` with its `content_type`, so the same harness
    drives both without adding `httpx`.
    """
    return asyncio.run(_request(application, method, path, json_body, query, body, content_type))


@pytest.fixture(scope="session", autouse=True)
def offline_guard() -> Any:
    """Fail the suite loudly if any test code opens a network connection.

    This is the enforcement mechanism behind NFR1.2 and BR7.2: with the guard
    armed, a passing analysis proves no network access was attempted, rather
    than merely assuming it.
    """
    original_connect = socket.socket.connect

    def _blocked_connect(self: socket.socket, address: Any) -> None:
        raise AssertionError(f"network access attempted by a test: {address!r}")

    socket.socket.connect = _blocked_connect  # type: ignore[method-assign]
    try:
        yield
    finally:
        socket.socket.connect = original_connect  # type: ignore[method-assign]


@pytest.fixture
def tmp_settings(tmp_path: Any) -> Any:
    """Offline settings whose database lives in this test's `tmp_path`."""
    from app.config import Settings

    return Settings(
        mode="offline",
        api_key=None,
        model="typesafe/jev-1.13",
        db_path=tmp_path / "sentiment.db",
        config_path=tmp_path / "config.local.toml",
    )


@pytest.fixture
def tmp_db_path(tmp_path: Any) -> Any:
    """A path to a temporary SQLite file that does not exist yet."""
    return tmp_path / "data" / "sentiment.db"
