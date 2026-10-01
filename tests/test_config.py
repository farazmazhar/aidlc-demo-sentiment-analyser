"""Business logic: configuration and mode resolution.

Covers the ordered resolution rules (BR1.1-BR1.5) and the secret-handling rules:
the committed example carries no secret, the real file is gitignored, and a key
never appears in a rendered setting or a log record.
(FR1.1-FR1.6, BR1.1-BR1.5, BR5.1, NFR2)
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from app.config import DEFAULT_MODEL, ConfigError, load_settings

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CONFIG = REPO_ROOT / "config.example.toml"
LIVE_KEY = "sk-or-v1-0123456789abcdef0123456789abcdef"


def _write_config(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_offline_is_the_default_when_nothing_is_configured(tmp_path):
    """BR1.1: no config file, or no mode in it, resolves to the offline engine."""
    missing = tmp_path / "config.local.toml"
    assert not missing.exists()

    settings = load_settings(config_path=missing, db_path=tmp_path / "sentiment.db")
    assert settings.mode == "offline"
    assert settings.api_key is None
    assert settings.config_path == missing
    assert settings.model == DEFAULT_MODEL

    without_mode = _write_config(tmp_path / "no-mode.toml", f'api_key = "{LIVE_KEY}"\n')
    assert load_settings(config_path=without_mode).mode == "offline"


def test_dummy_mode_ignores_a_key_in_the_file(tmp_path):
    """BR1.1: the offline engine never picks up a key that happens to be present."""
    config = _write_config(tmp_path / "dummy.toml", f'mode = "dummy"\napi_key = "{LIVE_KEY}"\n')

    resolved = load_settings(config_path=config)

    assert resolved.mode == "offline"
    assert resolved.api_key is None
    assert LIVE_KEY not in repr(resolved)


def test_live_mode_with_a_key_resolves_to_the_live_engine(tmp_path):
    """BR1.3: a configured live mode with a usable key selects the live engine."""
    config = _write_config(
        tmp_path / "config.local.toml",
        f'mode = "openrouter"\napi_key = "{LIVE_KEY}"\nmodel = "typesafe/jev-1.13"\n',
    )

    settings = load_settings(config_path=config, db_path=tmp_path / "sentiment.db")

    assert settings.mode == "live"
    assert settings.api_key == LIVE_KEY
    assert settings.model == "typesafe/jev-1.13"


@pytest.mark.parametrize("body", ['mode = "openrouter"\n', 'mode = "openrouter"\napi_key = "  "\n'])
def test_live_mode_without_a_key_warns_and_stays_offline(tmp_path, caplog, body):
    """BR1.4, NFR6.2: live requested with no key warns, naming the config file."""
    config = _write_config(tmp_path / "config.local.toml", body)

    with caplog.at_level(logging.WARNING, logger="app.config"):
        settings = load_settings(config_path=config, db_path=tmp_path / "sentiment.db")

    # The request for live mode is remembered, so a later submission is refused
    # rather than quietly answered by the offline engine.
    assert settings.mode == "live"
    assert settings.api_key is None

    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert warnings, "a requested-but-unusable live mode must be recorded as a warning"
    assert any("config.local.toml" in record.getMessage() for record in warnings)
    assert all(LIVE_KEY not in record.getMessage() for record in warnings)


def test_an_unsupported_mode_is_rejected_naming_the_accepted_values(tmp_path):
    """FR1.1: an unsupported mode is rejected, naming the accepted values."""
    unsupported = _write_config(tmp_path / "unsupported.toml", 'mode = "openai"\n')

    with pytest.raises(ConfigError) as excinfo:
        load_settings(config_path=unsupported)

    assert "'dummy'" in str(excinfo.value)
    assert "'openrouter'" in str(excinfo.value)


def test_invalid_toml_is_rejected_naming_the_config_file(tmp_path):
    """A malformed config file fails loudly instead of being ignored."""
    broken = _write_config(tmp_path / "broken.toml", "mode = [unterminated\n")

    with pytest.raises(ConfigError) as excinfo:
        load_settings(config_path=broken)

    assert "broken.toml" in str(excinfo.value)


def test_the_key_is_never_rendered_or_logged(tmp_path, caplog):
    """BR5.1: the key is used, and never appears in a repr or a log record."""
    config = _write_config(
        tmp_path / "config.local.toml",
        f'mode = "openrouter"\napi_key = "{LIVE_KEY}"\n',
    )

    with caplog.at_level(logging.DEBUG):
        settings = load_settings(config_path=config, db_path=tmp_path / "sentiment.db")
        rendered = f"{settings!r} {settings!s}"
        logging.getLogger("app.config").debug("settings loaded: %s", settings)
        logging.getLogger("app.main").info("startup: mode=%s", settings.mode)

    assert settings.api_key == LIVE_KEY  # it is used...
    assert LIVE_KEY not in rendered  # ...but never rendered
    assert all(LIVE_KEY not in record.getMessage() for record in caplog.records)
    assert all(LIVE_KEY not in str(record.__dict__) for record in caplog.records)
    assert rendered.count("<redacted>") == 2


def test_example_config_parses_with_placeholder_key():
    """NFR2.2: the committed example parses and carries no secret."""
    example_text = EXAMPLE_CONFIG.read_text(encoding="utf-8")
    data = tomllib.loads(example_text)

    assert data["mode"] in {"dummy", "openrouter"}
    assert data.get("api_key", "") == ""
    assert "sk-" not in example_text


def test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools():
    """AC1.1.3, NFR3.1, NFR3.2: two runtime packages; test/coverage/lint under `dev`."""
    manifest = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    runtime = manifest["project"]["dependencies"]
    dev = manifest["project"]["optional-dependencies"]["dev"]

    assert [requirement.split(">=")[0].split("==")[0] for requirement in runtime] == [
        "fastapi",
        "uvicorn",
    ]
    assert any(requirement.startswith("pytest") for requirement in dev)
    assert any(requirement.startswith("pytest-cov") for requirement in dev)
    assert any(requirement.startswith("ruff") for requirement in dev)

    # The lint rule set is pinned explicitly (including the security rules), and
    # the coverage floor is a configured input rather than a per-run flag.
    ruff_config = manifest["tool"]["ruff"]["lint"]
    assert "S" in ruff_config["select"]
    assert manifest["tool"]["coverage"]["report"]["fail_under"] == 80


def test_local_config_is_gitignored():
    """AC8.1.3: the real config file cannot be committed."""
    if shutil.which("git") is None:  # pragma: no cover - environment dependent
        pytest.skip("git is not available on this machine")

    completed = subprocess.run(
        ["git", "check-ignore", "-q", "config.local.toml"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )

    # A zero exit status is what proves the file is ignored; the tracked example
    # is asserted to exist so this test cannot pass against an empty repo.
    assert completed.returncode == 0, (
        "config.local.toml must be ignored, otherwise the API key can be committed"
    )
    assert EXAMPLE_CONFIG.is_file()
