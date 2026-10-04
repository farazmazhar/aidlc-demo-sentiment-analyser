# The platform-neutral verification entry point (FR2.1).
#
# `make verify` runs the standing gates in the order the requirement names them:
# install, lint, format check, the whole test suite with its 80 % whole-
# application coverage floor, the secret scan, and the dependency audit.
#
# It is deliberately neither a pre-commit hook nor a provider CI job: there is no
# remote, so a script a human (or a future CI job) can call on any host is the
# only gate that is true today. Override the interpreter with, for example,
# `make verify PYTHON=.venv/bin/python`.

# Prefer the project's documented virtual environment when it exists, so
# `make verify` works from the repository root without an explicit override.
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)

# The paths the secret scan covers: the code and configuration this project
# authors. The AI-DLC harness tree under `aidlc/` is framework-owned and is not
# scanned here. The repository's fake-key fixtures are recorded as reviewed
# findings in `.secrets.baseline`, so a new secret still fails the target.
SECRET_SCAN_PATHS := app tests config.example.toml pyproject.toml README.md Makefile docs

.PHONY: verify install lint format test secrets audit lock

# FR2.1: every gate, in the order the requirement pins.
verify:
	$(PYTHON) -m pip install -e ".[dev]"
	$(PYTHON) -m ruff check app tests
	$(PYTHON) -m ruff format --check app tests
	$(PYTHON) -m pytest
	$(PYTHON) -m detect_secrets.pre_commit_hook --baseline .secrets.baseline $(SECRET_SCAN_PATHS)
	$(PYTHON) -m pip_audit -r requirements.lock

# The individual gates, for a developer who wants one of them.
install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check app tests

format:
	$(PYTHON) -m ruff format --check app tests

test:
	$(PYTHON) -m pytest

secrets:
	$(PYTHON) -m detect_secrets.pre_commit_hook --baseline .secrets.baseline $(SECRET_SCAN_PATHS)

audit:
	$(PYTHON) -m pip_audit -r requirements.lock

# Regenerate the hashed lockfile (FR2.4). Needs network; the committed file is
# what a reproducible install consumes.
lock:
	uv pip compile --generate-hashes --extra dev --output-file requirements.lock pyproject.toml
