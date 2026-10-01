"""Frontend behavior: the page and its assets as the browser receives them.

The page is verified at the served-markup and served-asset contract level.
Browser-side execution of `app.js` is not exercised, because no browser-automation
dependency is permitted under the dependency cap (NFR3.1). (FR4.1, FR4.4, BR3.4,
BR4.2, AC2.1.3, AC5.3.2)
"""

from __future__ import annotations

import pytest

from app.main import create_app
from tests.conftest import asgi_request

#: Every interactive element carries a stable automation hook.
REQUIRED_TEST_IDS = (
    "analyze-form",
    "analyze-input",
    "analyze-submit-button",
    "result-panel",
    "result-label",
    "result-confidence",
    "result-engine",
    "result-probabilities",
    "error-panel",
    "history-list",
    "history-item",
    "history-empty",
    "connection-status",
    "connection-status-text",
)


@pytest.fixture
def app(tmp_settings):
    return create_app(tmp_settings)


def test_index_page_renders_the_reachable_states(app):
    """The page ships the form, the result panel, the error panel and history."""
    response = asgi_request(app, "GET", "/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    markup = response.text
    for test_id in REQUIRED_TEST_IDS:
        assert f'data-testid="{test_id}"' in markup, f"missing data-testid {test_id!r}"

    assert "/static/app.js" in markup


def test_the_connection_state_is_announced_not_only_coloured(app):
    """AC5.3.2: the indicator is a live region and spells its state out."""
    markup = asgi_request(app, "GET", "/").text

    assert 'role="status"' in markup
    assert 'aria-live="polite"' in markup
    # The state is written in words, so colour is never the only signal.
    assert "OpenRouter: checking" in markup


def test_the_page_has_no_intensity_affordance(app):
    """BR3.4, AC2.1.3: the retired attribute is gone from the page's presentation."""
    markup = asgi_request(app, "GET", "/").text.lower()

    assert "intensity" not in markup


def test_page_assets_are_served(app):
    """`GET /static/app.js` is served as JavaScript, so the page can run."""
    response = asgi_request(app, "GET", "/static/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert response.text.strip() != ""
