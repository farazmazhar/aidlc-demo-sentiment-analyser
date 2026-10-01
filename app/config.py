"""Settings and mode resolution.

Single responsibility: decide which sentiment engine the app runs and where its
database lives, from one local TOML file, with an offline default. The API key
is held here and nowhere else, and never appears in a repr or a log line.
(FR1.1-FR1.6, BR1.1-BR1.5, BR5.1, NFR2)

Resolution order, narrowest source first (BR1.2, BR1.3, BR1.1):

1. a usable session credential — resolved by `app.service.effective_connection`,
   because it lives in process memory rather than in the file;
2. a configured live mode with a key, resolved here;
3. offline, the default.

`Settings.mode` records what the app *intends* to use, so a file that requests
live mode without a key is remembered as `live` with no key: the app then runs
on the offline engine and refuses a submission with an instruction naming the
config file (BR1.4) rather than pretending the live engine is in use.
"""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

#: The resolved engine mode the app intends to use (entities.md: EngineSettings).
Mode = Literal["offline", "live"]

#: The accepted values of the config file's `mode` key and the mode each one
#: requests. The file keeps its own vocabulary; `Settings.mode` speaks v1's.
FILE_MODES: dict[str, Mode] = {"dummy": "offline", "openrouter": "live"}

DEFAULT_MODE: Mode = "offline"
DEFAULT_MODEL = "typesafe/jev-1.13"
DEFAULT_CONFIG_PATH = Path("config.local.toml")
DEFAULT_DB_PATH = Path("data/sentiment.db")

#: What a rendered `Settings` shows instead of the key (BR5.1).
REDACTED = "<redacted>"

logger = logging.getLogger("app.config")


class ConfigError(RuntimeError):
    """Raised when the local configuration cannot select a usable engine.

    The message always names the config file to fill in (FR1.3).
    """


@dataclass(frozen=True, repr=False)
class Settings:
    """Resolved runtime settings (FR1.1).

    `mode` is the requested engine — `offline`, or `live` when the file asked for
    the live model. `api_key` is `None` for the offline engine and for a live
    request that carries no usable key, which is exactly the state BR1.4 refuses.
    """

    mode: Mode
    api_key: str | None = None
    model: str = DEFAULT_MODEL
    db_path: Path = DEFAULT_DB_PATH
    config_path: Path = DEFAULT_CONFIG_PATH

    def __repr__(self) -> str:
        """Render the settings with the key redacted (BR5.1, NFR2)."""
        key = REDACTED if self.api_key else "None"
        return (
            f"Settings(mode={self.mode!r}, api_key={key}, model={self.model!r}, "
            f"db_path={str(self.db_path)!r}, config_path={str(self.config_path)!r})"
        )

    __str__ = __repr__


def _read_config_file(config_path: Path) -> dict[str, Any] | None:
    """Return the parsed config file, or `None` when it does not exist."""
    try:
        raw = config_path.read_bytes()
    except FileNotFoundError:
        return None
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise ConfigError(
            f"{config_path} is not valid TOML: {exc}. Fix that file, or delete it to run "
            f"with the offline engine."
        ) from exc


def load_settings(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> Settings:
    """Resolve the settings from the config file, offline by default.

    1. No config file -> offline with no key (BR1.1).
    2. Config file without a `mode` -> offline (BR1.1).
    3. `mode = "dummy"` -> offline; any key in the file is ignored (BR1.1).
    4. `mode = "openrouter"` with a non-empty key -> live with that key (BR1.3).
    5. `mode = "openrouter"` with a missing or empty key -> live *requested* with
       no key: the app starts on the offline engine, logs a warning naming the
       config file, and refuses a submission until a credential is supplied,
       either in the file or through the in-app sign-in (BR1.4, FR1.3, AC5.2.1).
    6. Any other `mode` value -> `ConfigError` naming the accepted values (FR1.1).
    """
    path = Path(config_path)
    data = _read_config_file(path)

    if data is None or "mode" not in data:
        return Settings(mode=DEFAULT_MODE, api_key=None, db_path=Path(db_path), config_path=path)

    file_mode = data["mode"]
    if file_mode not in FILE_MODES:
        raise ConfigError(
            f"{path} sets mode = {file_mode!r}, which is not supported. Use one of: "
            f"{', '.join(repr(value) for value in FILE_MODES)}."
        )

    mode = FILE_MODES[file_mode]
    raw_key = data.get("api_key")
    api_key = raw_key.strip() if isinstance(raw_key, str) and raw_key.strip() else None
    raw_model = data.get("model")
    model = raw_model if isinstance(raw_model, str) and raw_model.strip() else DEFAULT_MODEL

    if mode == "offline":
        # A key in the file is ignored by the offline engine (BR1.1).
        return Settings(
            mode="offline", api_key=None, model=model, db_path=Path(db_path), config_path=path
        )

    if api_key is None:
        # Live was requested without a usable key. The app still starts, on the
        # offline engine; the warning names the file to fill in and never any
        # credential material (BR1.4, NFR6.2, AC5.2.1).
        logger.warning(
            "mode = 'openrouter' was requested but no API key is available; running the "
            "offline engine. Put your key in %s or connect from the page.",
            path,
        )
        return Settings(
            mode="live", api_key=None, model=model, db_path=Path(db_path), config_path=path
        )

    return Settings(
        mode="live", api_key=api_key, model=model, db_path=Path(db_path), config_path=path
    )
