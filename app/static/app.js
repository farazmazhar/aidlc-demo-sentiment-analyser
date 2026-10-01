// Page behaviour for very-cool-sentiment-analysis.
//
// This script only *displays* what the API returns: it never decides a label,
// a probability or a confidence of its own, so the sentiment engine stays
// swappable behind the HTTP contract (FR2.1, NFR5). Every data call goes to the
// versioned `/v1` surface (BR4.2, D3); only the page's own support routes stay
// unversioned.

const LABEL_ORDER = ["positive", "negative", "neutral"];
const API = "/v1";
const FALLBACK_AUTH_FAILURE =
  "Connecting the live model did not complete. You can keep using the offline engine.";

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
refreshConnection().then((connection) => {
  if (connection) {
    reportAuthOutcome(connection);
  }
});
// A credential that expires while the page is open must turn the indicator red
// on its own, so the status is re-read on a slow timer.
setInterval(refreshConnection, 20000);
