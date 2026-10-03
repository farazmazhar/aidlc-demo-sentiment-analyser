"""Shared test harness for very-cool-sentiment-analysis.

Four things live here, and nothing else:

1. :func:`asgi_request` - a tiny in-process ASGI caller. `fastapi.testclient`
   is deliberately NOT used: it requires `httpx`, which the dependency cap
   forbids (NFR3.1). This harness drives the real application object instead,
   so route and page tests exercise the real routing, validation, handler and
   persistence path.
2. :func:`concurrent_requests` - the same caller on **separate threads**, with the
   application lifespan entered **once** for the whole batch. `asgi_request` calls
   `asyncio.run` per request, so every request it makes gets a fresh event loop and
   runs strictly sequentially; no test written against that shape can host two
   genuinely overlapping requests, which is why the cross-thread connection defect
   (R-01) could be recorded for so long without a reproducing test (FR7.7,
   AC7.7.1, AC7.7.2).
3. The `tmp_settings` fixture - settings pointing at a per-test temporary
   database, so no test ever reads or writes the real `config.local.toml` or
   `data/sentiment.db` (NFR2).
4. The session-wide `offline_guard` - an autouse guard that makes every socket
   connection raise, so accidental network use fails loudly instead of silently
   reaching OpenRouter (NFR1.2, BR7.2). It is armed around concurrent requests
   exactly as it is around sequential ones.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
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


class ConcurrentRequest(NamedTuple):
    """One request's outcome, with the evidence that it really overlapped.

    `thread_id` and the monotonic interval are recorded so a test can *assert* the
    overlap rather than assume it: two requests are genuinely concurrent only if they
    ran on different threads and their intervals intersect (AC7.7.1). An exception
    raised inside a request thread is carried here rather than swallowed, so a
    cross-thread failure surfaces as the assertion that was meant to catch it
    (BR6.3).
    """

    response: AsgiResponse | None
    thread_id: int
    started_at: float
    finished_at: float
    error: BaseException | None = None

    def overlaps(self, other: ConcurrentRequest) -> bool:
        """Whether this request was in flight at the same moment as `other`."""
        return (
            self.thread_id != other.thread_id
            and self.started_at < other.finished_at
            and other.started_at < self.finished_at
        )


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


async def _serve(
    application: Any,
    method: str,
    path: str,
    query: str,
    body: bytes,
    content_type: str | None,
) -> AsgiResponse:
    """Drive one request through an application whose lifespan is already running."""
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

    await application(scope, receive, send)

    start = next(m for m in messages if m["type"] == "http.response.start")
    raw = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    headers = {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    response_type = headers.get("content-type", "")
    if "application/json" in response_type:
        parsed: Any = json.loads(raw.decode("utf-8")) if raw else None
    else:
        parsed = raw.decode("utf-8")
    return AsgiResponse(start["status"], parsed, headers)


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

    # Entering the lifespan context runs the application's startup, which is where
    # settings are loaded, the schema is created and an older store is migrated
    # (BR3.1, BR3.3). `concurrent_requests` enters it once for the whole batch
    # instead, which is what keeps two simultaneous migrations - and the
    # "database is locked" they would raise - out of the request path (AC7.7.2).
    async with application.router.lifespan_context(application):
        return await _serve(application, method, path, query, body, content_type)


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

    `path` is the bare path; use `query` for the raw query string so tests can send
    deliberately malformed values such as `limit=abc` (BR3.6). A JSON body is passed
    as `json_body`; a raw body (for example the `text/csv` bulk-import payload) is
    passed as `body` with its `content_type`, so the same harness drives both without
    adding `httpx`.
    """
    return asyncio.run(_request(application, method, path, json_body, query, body, content_type))


@contextmanager
def application_started(application: Any) -> Iterator[Any]:
    """Hold the application lifespan open, entering it exactly once.

    Startup is what creates the schema, so a batch of concurrent requests must not
    each re-enter it: two simultaneous `init_db` calls contend for the same file, and
    the resulting "database is locked" would make a concurrency test go red for a
    reason that has nothing to do with the defect under test (AC7.7.2, BR6.4).

    The lifespan is held open by one background thread running its own event loop,
    because an ASGI lifespan context has to be entered *and* exited on the same loop;
    splitting those two halves across loops raises `RuntimeError: generator didn't
    stop after athrow()`.
    """
    ready = threading.Event()
    release = threading.Event()

    async def hold_lifespan() -> None:
        async with application.router.lifespan_context(application):
            ready.set()
            while not release.is_set():
                await asyncio.sleep(0.005)

    keeper = threading.Thread(target=lambda: asyncio.run(hold_lifespan()), daemon=True)
    keeper.start()
    if not ready.wait(timeout=30):  # pragma: no cover - only on a hung startup
        release.set()
        raise AssertionError("the application lifespan never became ready")
    try:
        yield application
    finally:
        release.set()
        keeper.join(timeout=30)


def concurrent_requests(
    application: Any,
    requests: list[tuple[str, str, str]],
) -> list[ConcurrentRequest]:
    """Issue several requests at once, each on its own thread, and report the evidence.

    `requests` is a list of `(method, path, query)` triples. The application lifespan
    is entered **once**, in the driving loop, and every request is then dispatched to
    a dedicated thread that runs its own event loop - so the requests genuinely
    overlap instead of each getting a fresh loop and running sequentially, and no
    request re-enters startup (AC7.7.1, AC7.7.2). The pool is sized to the batch, so
    two requests really do run at the same moment rather than queueing.
    """

    def run_in_own_loop(spec: tuple[str, str, str]) -> ConcurrentRequest:
        method, path, query = spec
        thread_id = threading.get_ident()
        entered_at = time.monotonic()
        response: AsgiResponse | None = None
        failure: BaseException | None = None
        try:
            response = asyncio.run(_serve(application, method, path, query, b"", None))
        except BaseException as exc:  # reported to the caller, never swallowed
            failure = exc
        return ConcurrentRequest(response, thread_id, entered_at, time.monotonic(), failure)

    async def batch() -> list[ConcurrentRequest]:
        async with application.router.lifespan_context(application):
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor(max_workers=len(requests)) as pool:
                futures = [loop.run_in_executor(pool, run_in_own_loop, spec) for spec in requests]
                return list(await asyncio.gather(*futures))

    outcomes = asyncio.run(batch())
    outcomes.sort(key=lambda outcome: outcome.started_at)
    return outcomes


def serve_started(application: Any, method: str, path: str, query: str = "") -> AsgiResponse:
    """Serve one request against an application whose lifespan is already open.

    Used where a measurement must describe the request and not the startup that
    precedes it: `asgi_request` re-enters the lifespan on every call, so a timing
    taken through it would include a schema step the application performs once per
    process, not once per request (AC8.1.4, AC7.7.5).
    """
    with application_started(application):
        return asyncio.run(_serve(application, method, path, query, b"", None))


@pytest.fixture(scope="session", autouse=True)
def offline_guard() -> Any:
    """Fail the suite loudly if any test code opens a network connection.

    This is the enforcement mechanism behind NFR1.2 and BR7.2: with the guard armed,
    a passing analysis proves no network access was attempted, rather than merely
    assuming it.
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
