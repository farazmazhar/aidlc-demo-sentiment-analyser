"""In-app OpenRouter authorization, held for the session only.

Single responsibility: run OpenRouter's PKCE authorization flow and hold the
resulting credential in this process's memory, so the app can reach OpenRouter
without the key ever touching disk. Nothing in this module reads or writes the
config file, the database, or any other file: a restart starts disconnected.

The flow is the one OpenRouter documents for local apps:

1. `start(callback_url)` mints a `code_verifier`, derives its S256
   `code_challenge`, remembers the pair, and returns the authorization URL the
   browser should visit.
2. The user authorizes on OpenRouter, which redirects back to `callback_url`
   with a single-use `code` (valid for 10 minutes).
3. `complete(code)` exchanges that code at `/api/v1/auth/keys` for a
   user-controlled API key and keeps it in memory.

The exchanged key is an ordinary OpenRouter key, so it is used exactly like the
config-file key: `Authorization: Bearer <key>`. When OpenRouter later rejects it
(HTTP 401/403), `expire()` drops it so the app falls back to the offline dummy
engine and the page shows the connection as red again.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

#: Where the browser is sent to authorize, and where the code is exchanged.
AUTHORIZE_ENDPOINT = "https://openrouter.ai/auth"
EXCHANGE_ENDPOINT = "https://openrouter.ai/api/v1/auth/keys"

#: PKCE method OpenRouter recommends (S256).
PKCE_METHOD = "S256"

#: Prefills the label of the key OpenRouter creates for this app.
KEY_LABEL = "very-cool-sentiment-analysis (local)"

#: Authorization codes expire 10 minutes after issuance; pending verifiers are
#: dropped on the same schedule so a stale tab cannot pin memory.
PENDING_TTL_SECONDS = 600.0

EXCHANGE_TIMEOUT_SECONDS = 30.0

#: What the page shows while nothing is connected.
NOT_CONNECTED = "Not connected to OpenRouter."


class AuthExchangeError(RuntimeError):
    """Raised when an authorization code cannot be exchanged for a key.

    Covers a missing or already-spent code, a rejected verifier, an expired
    code, a network failure, and a response carrying no `key`.
    """


def create_code_verifier() -> str:
    """Return a fresh high-entropy PKCE code verifier."""
    return secrets.token_urlsafe(64)


def code_challenge_for(verifier: str) -> str:
    """Return the S256 challenge for `verifier`: base64url(sha256(verifier))."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def exchange_code_at_openrouter(code: str, code_verifier: str, method: str = PKCE_METHOD) -> str:
    """Trade an authorization code for an API key, over HTTPS, with the stdlib.

    This is the only outbound call the authorization flow makes, and it is the
    one function the tests replace with a double so no test touches the network.
    """
    body = json.dumps(
        {"code": code, "code_verifier": code_verifier, "code_challenge_method": method}
    ).encode("utf-8")
    # The endpoint is a hardcoded https constant, never caller-supplied.
    request = urllib.request.Request(  # noqa: S310
        EXCHANGE_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(  # noqa: S310
            request, timeout=EXCHANGE_TIMEOUT_SECONDS
        ) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise AuthExchangeError(
            f"OpenRouter refused the authorization code (HTTP {exc.code}). "
            "Start the connection again."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AuthExchangeError(
            f"OpenRouter could not be reached to exchange the code: {exc}."
        ) from exc

    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AuthExchangeError(
            "OpenRouter returned a body that is not JSON while exchanging the code."
        ) from exc

    key = decoded.get("key") if isinstance(decoded, dict) else None
    if not isinstance(key, str) or not key.strip():
        raise AuthExchangeError("OpenRouter returned no key for the authorization code.")
    return key.strip()


@dataclass(frozen=True, repr=False)
class SessionCredential:
    """An OpenRouter credential obtained in this session (never persisted)."""

    api_key: str
    obtained_at: datetime

    def __repr__(self) -> str:
        """Render the credential with the key redacted (FR1.5, NFR2)."""
        return (
            f"SessionCredential(api_key=<redacted>, obtained_at={self.obtained_at.isoformat()!r})"
        )

    __str__ = __repr__


class SessionAuth:
    """The session's OpenRouter connection: pending verifiers plus the credential.

    Every operation is guarded by one lock, so the store is safe to touch from
    the thread-pool workers FastAPI uses for synchronous endpoints.
    """

    def __init__(
        self,
        exchanger: Callable[[str, str, str], str] = exchange_code_at_openrouter,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._exchanger = exchanger
        self._clock = clock
        self._lock = threading.Lock()
        #: challenge -> (verifier, started at, monotonic seconds)
        self._pending: dict[str, tuple[str, float]] = {}
        self._credential: SessionCredential | None = None
        self._reason: str = NOT_CONNECTED

    # -- the authorization flow -------------------------------------------

    def start(self, callback_url: str) -> str:
        """Remember a fresh PKCE pair and return the URL the browser visits."""
        verifier = create_code_verifier()
        challenge = code_challenge_for(verifier)
        now = self._clock()
        with self._lock:
            self._drop_expired_pending(now)
            self._pending[challenge] = (verifier, now)

        query = urllib.parse.urlencode(
            {
                "callback_url": callback_url,
                "code_challenge": challenge,
                "code_challenge_method": PKCE_METHOD,
                "key_label": KEY_LABEL,
            }
        )
        return f"{AUTHORIZE_ENDPOINT}?{query}"

    def complete(self, code: str) -> SessionCredential:
        """Exchange `code` for a key and keep it for this session.

        OpenRouter's redirect carries only the code, so each pending verifier is
        tried newest-first; a code that belongs to an earlier tab still works.
        """
        if not isinstance(code, str) or not code.strip():
            message = "OpenRouter redirected back without an authorization code."
            self.expire(message)
            raise AuthExchangeError(message)

        with self._lock:
            self._drop_expired_pending(self._clock())
            pending = list(self._pending.items())

        if not pending:
            message = (
                "No OpenRouter authorization is in progress. Click the connection "
                "indicator to start one."
            )
            self.expire(message)
            raise AuthExchangeError(message)

        last_error: AuthExchangeError | None = None
        for _challenge, (verifier, _started) in reversed(pending):
            try:
                key = self._exchanger(code.strip(), verifier, PKCE_METHOD)
            except AuthExchangeError as exc:
                last_error = exc
                continue

            credential = SessionCredential(api_key=key, obtained_at=datetime.now(UTC))
            with self._lock:
                self._credential = credential
                self._pending.clear()
                self._reason = NOT_CONNECTED
            return credential

        message = str(last_error) if last_error is not None else "Authorization failed."
        self.expire(message)
        raise AuthExchangeError(message)

    # -- state ------------------------------------------------------------

    def credential(self) -> SessionCredential | None:
        """The session credential, or `None` when nothing is connected."""
        with self._lock:
            return self._credential

    def reason(self) -> str:
        """Why the app is not connected (or the neutral message when it is)."""
        with self._lock:
            if self._credential is not None:
                return NOT_CONNECTED
            return self._reason

    def expire(self, reason: str) -> None:
        """Drop the credential because OpenRouter no longer accepts it."""
        with self._lock:
            self._credential = None
            self._reason = reason

    def disconnect(self) -> None:
        """Drop the credential on the user's instruction (and any pending flow)."""
        with self._lock:
            self._credential = None
            self._pending.clear()
            self._reason = "Disconnected."

    # -- internals --------------------------------------------------------

    def _drop_expired_pending(self, now: float) -> None:
        """Forget pending verifiers whose authorization code window has closed."""
        stale = [
            challenge
            for challenge, (_verifier, started) in self._pending.items()
            if now - started > PENDING_TTL_SECONDS
        ]
        for challenge in stale:
            del self._pending[challenge]
