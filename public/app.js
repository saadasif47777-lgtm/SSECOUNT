"use strict";

// Frontend controller only: Python owns extraction, counting, sorting, shares,
// pagination and report contents. Uploaded text is always rendered as plain text.
const byId = (id) => document.getElementById(id);
let selectedDocument = null;
let analysis = null;
let currentPage = 1;
let requestNumber = 0;
let activeRequest = null;
let controlTimer = null;
let busy = false;

function showFeedback(text, kind = "loading", retry = false) {
  byId("feedback").hidden = !text;
  byId("feedback").className = "feedback " + kind;
  byId("message").textContent = text;
  byId("feedback-icon").textContent =
    kind === "loading" ? "" : kind === "error" ? "!" : "✓";
  byId("retry").hidden = !retry;
}

function setBusy(value) {
  busy = value;
  byId("results").setAttribute("aria-busy", String(value));
  byId("sample").disabled = value;
  byId("download").disabled = value || !analysis;
  const table = analysis && analysis.dashboard.table;
  byId("previous").disabled = value || !table || table.page <= 1;
  byId("next").disabled = value || !table || table.page >= table.page_count;
  if (analysis)
    byId("document-state").textContent = value
      ? "Updating analysis…"
      : "Analysis complete";
}

function readControls() {
  return {
    order: byId("sort").value,
    minimum: byId("minimum").value,
    query: byId("search").value,
    top: byId("top").value,
    page: currentPage,
  };
}

function resetControls(newDocument = false) {
  currentPage = 1;
  byId("sort").value = "high";
  byId("minimum").value = "1";
  byId("search").value = "";
  byId("search-result").hidden = true;
  if (newDocument) byId("top").value = "10";
}

function setView(view, focus = false) {
  for (const name of ["frequency", "text"]) {
    const selected = name === view;
    const tab = byId(name + "-tab");
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    byId(name + "-view").hidden = !selected;
    if (focus && selected) tab.focus();
  }
}

// Cancelling immediately (including during the debounce window) prevents an old
// response from flashing results for a document or controls the user has replaced.
function cancelPreviousRequest() {
  requestNumber += 1;
  if (activeRequest) activeRequest.abort();
  clearTimeout(controlTimer);
}

async function requestAnalysis(newDocument = false) {
  if (!selectedDocument) return;
  cancelPreviousRequest();
  const thisRequest = requestNumber;
  const documentSnapshot = selectedDocument;
  const controller = new AbortController();
  activeRequest = controller;
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, 30000);

  if (newDocument) {
    analysis = null;
    resetControls(true);
    setView("frequency");
    byId("results").hidden = true;
    byId("document-header").hidden = true;
    byId("start").hidden = false;
    byId("empty-state").hidden = false;
    byId("empty-title").textContent = "Reading your document…";
    byId("empty-description").textContent =
      "Extracting text and preparing your word frequencies.";
  }
  setBusy(true);
  showFeedback(newDocument ? "Analyzing your document…" : "Updating analysis…");

  try {
    const options = readControls();
    const settings = { method: "POST", signal: controller.signal };
    if (documentSnapshot.sample) {
      settings.headers = { "Content-Type": "application/json" };
      settings.body = JSON.stringify({ sample: true, options });
    } else {
      const form = new FormData();
      form.append("file", documentSnapshot.file);
      form.append("options", JSON.stringify(options));
      settings.body = form;
    }
    const response = await fetch("/api/analyze", settings);
    const data = await response.json();
    if (thisRequest !== requestNumber) return;
    if (!response.ok) {
      const failure = new Error(
        data.error || "Analysis failed. Choose another document or try again.",
      );
      failure.retry = response.status >= 500;
      throw failure;
    }
    analysis = data;
    currentPage = data.dashboard.table.page;
    renderDashboard();
    byId("start").hidden = true;
    byId("empty-state").hidden = true;
    byId("document-header").hidden = false;
    byId("results").hidden = false;
    // A document-level success has meaning; routine control updates need no badge.
    showFeedback(
      newDocument
        ? "Analysis complete. Your document is ready to explore."
        : "",
      "success",
    );
  } catch (error) {
    if (thisRequest !== requestNumber) return;
    if (error.name === "AbortError" && !timedOut) return;
    const connectionError =
      timedOut || error instanceof TypeError || error instanceof SyntaxError;
    const message = timedOut
      ? "The analysis took too long. Try again or choose a smaller document."
      : connectionError
        ? "Could not reach the analysis service. Check your connection and try again."
        : error.message;
    showFeedback(message, "error", connectionError || error.retry === true);
    if (!analysis) {
      byId("empty-title").textContent = "This document couldn’t be analyzed.";
      byId("empty-description").textContent =
        "Choose another file above, or try the sample to explore the workspace.";
    }
  } finally {
    clearTimeout(timeout);
    if (thisRequest === requestNumber) {
      activeRequest = null;
      setBusy(false);
    }
  }
}

function renderDashboard() {
  byId("filename").textContent = analysis.file_name;
  for (const [id, value] of Object.entries({
    total: analysis.total_words,
    unique: analysis.unique_words,
    characters: analysis.characters,
    average: analysis.dashboard.average_display,
    numbers: analysis.extra_statistics.numeric_tokens,
    "unique-numbers": analysis.extra_statistics.unique_numbers,
    digits: analysis.extra_statistics.digits,
    lines: analysis.extra_statistics.nonempty_lines,
    paragraphs: analysis.extra_statistics.paragraphs,
  })) {
    byId(id).textContent =
      typeof value === "number" ? value.toLocaleString() : value;
  }
  byId("original").textContent = analysis.original_text;
  byId("most-label").textContent =
    "Most frequent · " + analysis.highest + " occurrences each";
  byId("least-label").textContent =
    "Least frequent · " + analysis.lowest + " occurrences each";
  byId("most").textContent = analysis.most_words.join(", ");
  byId("least").textContent = analysis.least_words.join(", ");
  const searchMessage = analysis.dashboard.search_message;
  byId("search-result").textContent = searchMessage;
  byId("search-result").hidden = !searchMessage;
  byId("search-result").className =
    "search-result" +
    (searchMessage.includes("does not appear") ? " no-match" : "");
  renderTable();
  renderChart();
}

function renderTable() {
  const table = analysis.dashboard.table;
  const body = byId("rows");
  body.replaceChildren();
  // These rows are already sorted, filtered, paginated and assigned shares by Python.
  for (const item of table.rows) {
    const row = document.createElement("tr");
    for (const [index, value] of [
      item.word,
      item.count.toLocaleString(),
      item.share,
    ].entries()) {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (index > 0) cell.className = "numeric";
      row.append(cell);
    }
    body.append(row);
  }
  byId("table-caption").textContent =
    table.matching_words.toLocaleString() +
    " of " +
    analysis.unique_words.toLocaleString() +
    " unique words";
  byId("empty-table").hidden = table.rows.length > 0;
  byId("page-info").textContent =
    "Page " + table.page + " of " + table.page_count;
}

function renderChart() {
  const chart = byId("chart");
  chart.replaceChildren();
  const descriptions = [];
  for (const item of analysis.dashboard.chart) {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.title = item.word + ": " + item.count + " occurrences";
    const label = document.createElement("span");
    label.className = "bar-label";
    label.textContent = item.word;
    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.width = item.width + "%";
    track.append(bar);
    const value = document.createElement("span");
    value.className = "bar-value";
    value.textContent = item.count.toLocaleString();
    row.append(label, track, value);
    chart.append(row);
    descriptions.push(item.word + ": " + item.count);
  }
  chart.setAttribute(
    "aria-label",
    "Word counts; widths relative to the highest count. " +
      descriptions.join("; "),
  );
}

function chooseFile(file) {
  // Size feedback can be immediate. Python still validates the original bytes.
  if (file.size > 3 * 1024 * 1024) {
    cancelPreviousRequest();
    setBusy(false);
    showFeedback(
      "Choose a file of 3 MB or less. Replace this file with a smaller document.",
      "error",
    );
    if (!analysis) {
      byId("empty-title").textContent = "Choose a smaller document.";
      byId("empty-description").textContent =
        "Files can be up to 3 MB. You can also try the sample above.";
    }
    return;
  }
  selectedDocument = { file };
  requestAnalysis(true);
}

function controlsChanged() {
  if (!selectedDocument) return;
  currentPage = 1;
  cancelPreviousRequest();
  setBusy(true);
  controlTimer = setTimeout(() => requestAnalysis(), 250);
}

function downloadReport() {
  if (!analysis || busy) return;
  // The complete Python report is independent of table filters and pagination.
  const blob = new Blob([analysis.report], {
    type: "text/plain;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "SSECOUNT-report.txt";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// One native file input serves the hero, keyboard drop zone and replacement action.
byId("file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) chooseFile(file);
  event.target.value = ""; // Choosing the same document again must still fire change.
});
for (const id of ["upload-document", "replace"])
  byId(id).addEventListener("click", () => byId("file").click());
byId("sample").addEventListener("click", () => {
  selectedDocument = { sample: true };
  requestAnalysis(true);
});
byId("retry").addEventListener("click", () => requestAnalysis(!analysis));
byId("download").addEventListener("click", downloadReport);
for (const id of ["search", "minimum"])
  byId(id).addEventListener("input", controlsChanged);
for (const id of ["sort", "top"])
  byId(id).addEventListener("change", controlsChanged);
for (const id of ["reset-filters", "clear-filter"])
  byId(id).addEventListener("click", () => {
    resetControls();
    requestAnalysis();
  });
byId("previous").addEventListener("click", () => {
  if (!busy && currentPage > 1) {
    currentPage -= 1;
    requestAnalysis();
  }
});
byId("next").addEventListener("click", () => {
  if (!busy) {
    currentPage += 1;
    requestAnalysis();
  }
});

const dropzone = byId("dropzone");
dropzone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    byId("file").click();
  }
});
let dragDepth = 0;
for (const type of ["dragenter", "dragover"])
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    if (type === "dragenter") dragDepth += 1;
    dropzone.classList.add("drag");
  });
dropzone.addEventListener("dragleave", () => {
  dragDepth = Math.max(0, dragDepth - 1);
  if (!dragDepth) dropzone.classList.remove("drag");
});
dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dragDepth = 0;
  dropzone.classList.remove("drag");
  if (event.dataTransfer.files[0]) chooseFile(event.dataTransfer.files[0]);
});
// Prevent an accidental document navigation when a file lands outside the drop zone.
for (const type of ["dragover", "drop"])
  window.addEventListener(type, (event) => event.preventDefault());

// Tabs support pointer, Tab, arrow, Home and End navigation without a UI library.
for (const name of ["frequency", "text"]) {
  const tab = byId(name + "-tab");
  tab.addEventListener("click", () => setView(name));
  tab.addEventListener("keydown", (event) => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const next =
        event.key === "Home"
          ? "frequency"
          : event.key === "End"
            ? "text"
            : name === "frequency"
              ? "text"
              : "frequency";
      setView(next, true);
    }
  });
}
byId("guide-link").addEventListener("click", () => {
  byId("guide").open = true;
});
setBusy(false);
