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

#: Every interactive element carries a stable automation hook. The analytics
#: hooks are pinned in exactly the same convention, so renaming one fails a page
#: contract test rather than passing silently (FR6.9, AC6.2.4, BR2.14).
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
    "site-nav",
    "nav-analyze",
    "nav-summary",
    "nav-terms",
    "analytics-summary",
    "summary-total",
    "summary-mean-confidence",
    "summary-day-count",
    "summary-series",
    "summary-series-chart",
    "summary-series-line",
    "summary-series-values",
    "summary-breakdown",
    "analytics-empty",
    "analytics-error",
)


@pytest.fixture
def app(tmp_settings):
    return create_app(tmp_settings)


def _body_markup(app) -> str:
    """The served markup's `<body>`, so a stylesheet selector is never mistaken
    for a rendered attribute."""
    markup = asgi_request(app, "GET", "/").text
    return markup[markup.index("<body") :]


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


def test_the_shell_has_a_nav_with_three_links_and_one_current_page(app):
    """FR6.1: the page shell navigates between the three sections it ships."""
    body = _body_markup(app)

    assert body.count("<nav") == 1
    assert 'aria-label="Sections"' in body
    nav = body[body.index("<nav") : body.index("</nav>")]
    assert nav.count("<a ") == 3
    # Exactly one link claims the current page, so the reader is never lost.
    assert nav.count('aria-current="page"') == 1
    assert body.count("<h1>") == 1


def test_the_header_holds_the_heading_the_nav_and_the_connection_indicator(app):
    """FR6.1: the indicator belongs to the header, not to a fixed overlay."""
    markup = asgi_request(app, "GET", "/").text
    header = markup[markup.index("<header") : markup.index("</header>")]

    assert "position: fixed" not in markup
    for hook in ("<h1>", "site-nav", "connection-status"):
        assert hook in header


def test_the_series_region_is_a_native_svg_polyline_with_its_values_as_text(app):
    """FR6.6, AC6.2.1: the series is a native SVG polyline, and its values are text too."""
    markup = asgi_request(app, "GET", "/").text

    assert "<svg" in markup
    assert "<polyline" in markup
    assert 'data-testid="summary-series-line"' in markup
    # The same numbers are written out, so the shape is never the only signal.
    assert 'data-testid="summary-series-values"' in markup


def test_the_analytics_regions_stay_distinct(app):
    """FR6.7, AC6.5.5: summary, empty and error are three regions, not one panel."""
    body = _body_markup(app)

    for hook in ("analytics-summary", "analytics-empty", "analytics-error"):
        assert f'data-testid="{hook}"' in body
    # Both non-default regions ship hidden, so neither can pre-empt a success.
    for hook in ("analytics-empty", "analytics-error"):
        element = body[body.index(f'data-testid="{hook}"') :][:240]
        assert "hidden" in element


def test_the_analytics_script_renders_from_returned_values_only(app):
    """FR6.6, AC6.2.2, AC6.2.5: one fetch, `textContent` writes, an explicit no-share."""
    script = asgi_request(app, "GET", "/static/app.js").text

    # Exactly one fetch to the summary endpoint, on the named `/v2` prefix.
    assert script.count("`${API_V2}/analytics/summary`") == 1
    # No HTML-parsing sink exists anywhere on the page, so a stored text can never
    # become markup however it is rendered.
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert sink not in script
    # Every summary figure is written as text, and the breakdown rows are built
    # from `textContent` and appended as elements.
    assert "summaryTotal.textContent" in script
    assert "summaryMeanConfidence.textContent" in script
    assert "summaryDayCount.textContent" in script
    assert "summarySeriesValues.textContent" in script
    assert "line.textContent" in script
    assert "summaryBreakdown.replaceChildren" in script
    # A null share is an explicit marker, and there is exactly one place that
    # turns a fraction into a percentage.
    assert "NO_SHARE_TEXT" in script
    assert script.count("toFixed(2)}%") == 1
