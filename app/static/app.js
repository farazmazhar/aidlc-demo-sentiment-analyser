// Page behaviour for very-cool-sentiment-analysis.
//
// This script only *displays* what the API returns: it never decides a label,
// a probability, a confidence or a share of its own, so the sentiment engine
// stays swappable behind the HTTP contract (FR2.1, NFR5). Every data call goes to
// a versioned surface; the page's own support routes stay unversioned.
//
// `API_V2` is this page's own copy of the analytics version prefix. The backend
// holds an independent copy in `app/routes.py` as `V2_PREFIX`, and a test asserts
// the two are equal, so a prefix change cannot silently break every analytics
// fetch (FR6.9, AC6.2.3).

const LABEL_ORDER = ["positive", "negative", "neutral"];
const API = "/v1";
const API_V2 = "/v2";
// The two `/v2` reads are addressed through named constants so a prefix or path
// change is one edit and the range query is appended in exactly one place.
const ANALYTICS_SUMMARY_PATH = `${API_V2}/analytics/summary`;
const ANALYTICS_TERMS_PATH = `${API_V2}/analytics/terms`;
const FALLBACK_AUTH_FAILURE =
  "Connecting the live model did not complete. You can keep using the offline engine.";

// A `null` share has no percentage; the view says so rather than printing a 0%
// the API deliberately refused to state (FR2.7, AC6.2.5).
const NO_SHARE_TEXT = "no share (nothing analysed in range)";

const form = document.querySelector('[data-testid="analyze-form"]');
const input = document.querySelector('[data-testid="analyze-input"]');
const submitButton = document.querySelector('[data-testid="analyze-submit-button"]');
const resultPanel = document.querySelector('[data-testid="result-panel"]');
const resultLabel = document.querySelector('[data-testid="result-label"]');
const resultConfidence = document.querySelector('[data-testid="result-confidence"]');
const resultEngine = document.querySelector('[data-testid="result-engine"]');
const resultProbabilities = document.querySelector('[data-testid="result-probabilities"]');
const errorPanel = document.querySelector('[data-testid="error-panel"]');
const historyList = document.querySelector('[data-testid="history-list"]');
const historyEmpty = document.querySelector('[data-testid="history-empty"]');
const historyItemTemplate = document.querySelector('[data-testid="history-item"]');
const connectionIndicator = document.querySelector('[data-testid="connection-status"]');
const connectionText = document.querySelector('[data-testid="connection-status-text"]');

const analyticsSummary = document.querySelector('[data-testid="analytics-summary"]');
const analyticsEmpty = document.querySelector('[data-testid="analytics-empty"]');
const analyticsError = document.querySelector('[data-testid="analytics-error"]');
const summaryTotal = document.querySelector('[data-testid="summary-total"]');
const summaryMeanConfidence = document.querySelector('[data-testid="summary-mean-confidence"]');
const summaryDayCount = document.querySelector('[data-testid="summary-day-count"]');
const summarySeriesValues = document.querySelector('[data-testid="summary-series-values"]');
const summarySeriesLine = document.querySelector('[data-testid="summary-series-line"]');
const summaryBreakdown = document.querySelector('[data-testid="summary-breakdown"]');
const summaryPartial = document.querySelector('[data-testid="summary-partial"]');

const analyticsRange = document.querySelector('[data-testid="analytics-range"]');
const rangeFrom = document.querySelector('[data-testid="range-from"]');
const rangeTo = document.querySelector('[data-testid="range-to"]');
const rangeStatus = document.querySelector('[data-testid="range-status"]');
const termsPositive = document.querySelector('[data-testid="terms-positive"]');
const termsNegative = document.querySelector('[data-testid="terms-negative"]');
const termsEmpty = document.querySelector('[data-testid="terms-empty"]');
const termsError = document.querySelector('[data-testid="terms-error"]');
const termsPartial = document.querySelector('[data-testid="terms-partial"]');

/** Read the app's error envelope (`{code, message}`) from a non-2xx response. */
async function readErrorMessage(response) {
  try {
    const payload = await response.json();
    if (payload && payload.message) {
      return payload.code ? `${payload.code}: ${payload.message}` : payload.message;
    }
  } catch (error) {
    // Fall through to the generic message below.
  }
  return `Request failed with status ${response.status}`;
}

function showError(message) {
  errorPanel.textContent = message;
  errorPanel.hidden = false;
}

function clearError() {
  errorPanel.textContent = "";
  errorPanel.hidden = true;
}

/** Render one stored record, using only values the API returned. */
function renderResult(record) {
  resultLabel.textContent = record.label;
  resultConfidence.textContent = Number(record.confidence).toFixed(3);
  // Which engine answered is part of the result: an offline stand-in must never
  // be mistaken for the live model (AC2.1.3).
  resultEngine.textContent = `${record.provider} · ${record.model}`;

  resultProbabilities.replaceChildren();
  for (const label of LABEL_ORDER) {
    const value = record.probabilities[label];
    const item = document.createElement("li");
    item.textContent = `${label}: ${Number(value).toFixed(3)}`;
    resultProbabilities.append(item);
  }

  resultPanel.hidden = false;
}

/** Render the stored history, newest first, one clone of the item template each. */
function renderHistory(records) {
  historyList.replaceChildren();
  historyEmpty.hidden = records.length > 0;

  for (const record of records) {
    const row = historyItemTemplate.content.firstElementChild.cloneNode(true);
    row.querySelector('[data-testid="history-item-text"]').textContent = record.text;
    row.querySelector('[data-testid="history-item-meta"]').textContent =
      `${record.label} · confidence ${Number(record.confidence).toFixed(3)} · ` +
      `${record.provider} · ${record.created_at}`;
    historyList.append(row);
  }
}

async function refreshHistory() {
  const response = await fetch(`${API}/analyses?limit=50`);
  if (!response.ok) {
    showError(await readErrorMessage(response));
    return;
  }
  // The versioned contract returns a bare array, newest first.
  renderHistory(await response.json());
}

async function submitAnalysis(text) {
  const response = await fetch(`${API}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    showError(await readErrorMessage(response));
    // A refused live attempt or a rejected credential changes the connection
    // state server-side, so the indicator has to be re-read rather than assumed.
    await refreshConnection();
    return;
  }

  clearError();
  renderResult(await response.json());
  await refreshHistory();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();

  if (text === "") {
    // Invalid input stays on the page: no request is sent and no row is created
    // (AC2.2.3).
    showError("Enter some text to analyse.");
    return;
  }

  submitButton.disabled = true;
  try {
    await submitAnalysis(text);
  } catch (error) {
    showError(`Could not reach the server: ${error.message}`);
  } finally {
    submitButton.disabled = false;
  }
});

// -- the analytics view: range, summary and terms ----------------------------
//
// One range control drives two independent reads, so the summary and the term
// lists always describe one population (FR1.4). Each section renders its own
// outcome, so one failed request never blanks the other (FR1.10, NFR4.6). A
// refresh takes a token and aborts the previous request, so a late response from
// an earlier range can never overwrite a newer one (FR1.11, NFR4.7); the view
// never re-sends a failed request on its own.

let analyticsRequestToken = 0;
let analyticsAbortController = null;

/** The query string for the current range; both bounds empty means all history. */
function rangeQuery() {
  const params = new URLSearchParams();
  if (rangeFrom.value) {
    params.set("from", rangeFrom.value);
  }
  if (rangeTo.value) {
    params.set("to", rangeTo.value);
  }
  const query = params.toString();
  return query === "" ? "" : `?${query}`;
}

/** Write the current range into the page's live region, so a change is announced. */
function announceRange() {
  const from = rangeFrom.value || "the beginning of history";
  const to = rangeTo.value || "today";
  rangeStatus.textContent = `Showing analyses from ${from} to ${to}.`;
}

/** Hide every summary region; each is revealed only by its own outcome. */
function resetAnalyticsRegions() {
  analyticsSummary.hidden = true;
  analyticsEmpty.hidden = true;
  analyticsError.hidden = true;
  analyticsError.textContent = "";
  summaryPartial.hidden = true;
  summaryPartial.textContent = "";
}

/** Hide every terms region; each is revealed only by its own outcome. */
function resetTermsRegions() {
  termsEmpty.hidden = true;
  termsError.hidden = true;
  termsError.textContent = "";
  termsPartial.hidden = true;
  termsPartial.textContent = "";
}

/** Read the app's envelope from a failed response, without the machine code. */
async function readAnalyticsError(response) {
  try {
    const payload = await response.json();
    if (payload && payload.message) {
      // The code stays in the server log; the page shows the message (FR6.7).
      return payload.message;
    }
  } catch (error) {
    // Fall through to the generic message below.
  }
  return `The analytics request failed with status ${response.status}.`;
}

/** Render the label breakdown, one row per label of the closed vocabulary. */
function renderBreakdown(summary) {
  summaryBreakdown.replaceChildren();
  for (const label of LABEL_ORDER) {
    const item = document.createElement("li");
    const count = summary.counts[label];
    const share = summary.shares[label];
    const shareText =
      share === null || share === undefined ? NO_SHARE_TEXT : `${(Number(share) * 100).toFixed(2)}%`;
    const line = document.createElement("span");
    line.textContent = `${label}: ${count} (${shareText})`;
    item.append(line);
    summaryBreakdown.append(item);
  }
}

/** Draw the per-day series as a native SVG polyline, values also written as text. */
function renderSeries(series) {
  const totals = series.map((entry) => Number(entry.total));
  const highest = totals.length > 0 ? Math.max(...totals) : 0;

  // The polyline is the shape; the text below it is the data, so neither is the
  // only way the series is conveyed.
  const points = totals
    .map((total, index) => {
      const step = totals.length > 1 ? 600 / (totals.length - 1) : 600;
      const y = highest > 0 ? 120 - (total / highest) * 100 : 120;
      return `${(index * step).toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
  summarySeriesLine.setAttribute("points", points);
  summarySeriesValues.textContent = series
    .map((entry) => `${entry.date}: ${entry.total}`)
    .join(", ");
}

/** Paint the summary region from the endpoint's own fields. */
function renderSummary(summary) {
  summaryTotal.textContent = String(summary.total);
  summaryMeanConfidence.textContent =
    summary.mean_confidence === null || summary.mean_confidence === undefined
      ? NO_SHARE_TEXT
      : Number(summary.mean_confidence).toFixed(4);
  summaryDayCount.textContent = String(summary.series.length);

  renderSeries(summary.series);
  renderBreakdown(summary);

  analyticsSummary.hidden = summary.total === 0;
  analyticsEmpty.hidden = summary.total !== 0;
}

/** Render one ranked term list from the endpoint's own `{term, count}` entries. */
function renderTermList(list, entries) {
  list.replaceChildren();
  for (const entry of entries) {
    const item = document.createElement("li");
    item.className = "term-item";
    const name = document.createElement("span");
    name.className = "term-name";
    name.textContent = entry.term;
    const count = document.createElement("span");
    count.className = "term-count";
    count.textContent = String(entry.count);
    item.append(name, count);
    list.append(item);
  }
}

/** Paint both term lists; "no terms" is its own region, not an empty list. */
function renderTerms(terms) {
  renderTermList(termsPositive, terms.positive);
  renderTermList(termsNegative, terms.negative);
  const empty = terms.positive.length === 0 && terms.negative.length === 0;
  termsEmpty.hidden = !empty;
  return empty ? "empty" : "ok";
}

/** Fetch the summary for `query`; returns "ok", "empty", "error" or "superseded". */
async function refreshSummary(token, signal, query) {
  let response;
  try {
    response = await fetch(`${ANALYTICS_SUMMARY_PATH}${query}`, { signal });
  } catch (error) {
    if (token !== analyticsRequestToken) {
      return "superseded";
    }
    analyticsError.textContent = `Could not reach the server: ${error.message}`;
    analyticsError.hidden = false;
    return "error";
  }
  if (token !== analyticsRequestToken) {
    return "superseded";
  }
  if (!response.ok) {
    // A failure renders as a failure, never as a plausible-looking empty result.
    analyticsError.textContent = await readAnalyticsError(response);
    analyticsError.hidden = false;
    return "error";
  }
  const summary = await response.json();
  if (token !== analyticsRequestToken) {
    return "superseded";
  }
  renderSummary(summary);
  return summary.total === 0 ? "empty" : "ok";
}

/** Fetch the term lists for `query`; returns "ok", "empty", "error" or "superseded". */
async function refreshTerms(token, signal, query) {
  let response;
  try {
    response = await fetch(`${ANALYTICS_TERMS_PATH}${query}`, { signal });
  } catch (error) {
    if (token !== analyticsRequestToken) {
      return "superseded";
    }
    termsError.textContent = `Could not reach the server: ${error.message}`;
    termsError.hidden = false;
    return "error";
  }
  if (token !== analyticsRequestToken) {
    return "superseded";
  }
  if (!response.ok) {
    termsError.textContent = await readAnalyticsError(response);
    termsError.hidden = false;
    return "error";
  }
  const terms = await response.json();
  if (token !== analyticsRequestToken) {
    return "superseded";
  }
  return renderTerms(terms);
}

/** Mark the failed section while the successful one keeps its data (NFR4.6). */
function showPartialFailures(summaryOutcome, termsOutcome) {
  if (summaryOutcome === "error" && termsOutcome !== "error") {
    summaryPartial.textContent =
      "The summary could not be loaded; the term lists below are still current.";
    summaryPartial.hidden = false;
  }
  if (termsOutcome === "error" && summaryOutcome !== "error") {
    termsPartial.textContent =
      "The term lists could not be loaded; the summary above is still current.";
    termsPartial.hidden = false;
  }
}

/** Refetch both sections on the current range, superseding any in-flight request. */
async function refreshAnalytics() {
  analyticsRequestToken += 1;
  const token = analyticsRequestToken;
  if (analyticsAbortController) {
    analyticsAbortController.abort();
  }
  analyticsAbortController = new AbortController();
  const signal = analyticsAbortController.signal;
  const query = rangeQuery();

  resetAnalyticsRegions();
  resetTermsRegions();

  const [summaryOutcome, termsOutcome] = await Promise.all([
    refreshSummary(token, signal, query),
    refreshTerms(token, signal, query),
  ]);

  if (token !== analyticsRequestToken) {
    // A newer refresh is in flight; this response is stale and is discarded.
    return;
  }
  announceRange();
  showPartialFailures(summaryOutcome, termsOutcome);
}

analyticsRange.addEventListener("submit", (event) => {
  event.preventDefault();
  refreshAnalytics();
});
analyticsRange.addEventListener("change", refreshAnalytics);

// -- OpenRouter connection indicator ----------------------------------------
// Red means the app is running the offline engine; green means it is talking to
// OpenRouter. The credential lives in the server process only, so the indicator
// is re-read rather than cached here, and its state is written in words so
// colour is never the only signal (AC5.3.2).

/** Paint the indicator from the connection payload. */
function renderConnection(connection) {
  const connected = Boolean(connection.connected);
  connectionIndicator.dataset.connected = connected ? "true" : "false";
  connectionIndicator.title = connected
    ? "OpenRouter is connected. Click to disconnect."
    : `${connection.reason || "Not connected to OpenRouter."} Click to connect.`;
  connectionText.textContent = connected
    ? "OpenRouter: connected"
    : "Offline engine (OpenRouter not connected)";
}

async function refreshConnection() {
  try {
    const response = await fetch(`${API}/health`);
    if (!response.ok) {
      return null;
    }
    const connection = await response.json();
    renderConnection(connection);
    return connection;
  } catch (error) {
    // The page keeps working offline; the indicator simply stays as it was.
    return null;
  }
}

/** Report the sign-in flow's own outcome, whose reason the server recorded. */
function reportAuthOutcome(connection) {
  const outcome = new URLSearchParams(window.location.search).get("auth");
  if (outcome === "failed") {
    showError(connection.reason || FALLBACK_AUTH_FAILURE);
  } else if (outcome === "connected") {
    clearError();
  }
}

async function toggleConnection() {
  if (connectionIndicator.dataset.connected !== "true") {
    window.location.href = "/auth/openrouter/start";
    return;
  }
  const response = await fetch("/auth/disconnect", { method: "POST" });
  if (response.ok) {
    renderConnection(await response.json());
  }
}

connectionIndicator.addEventListener("click", toggleConnection);

refreshHistory();
refreshAnalytics();
refreshConnection().then((connection) => {
  if (connection) {
    reportAuthOutcome(connection);
  }
});
// A credential that expires while the page is open must turn the indicator red
// on its own, so the status is re-read on a slow timer.
setInterval(refreshConnection, 20000);
