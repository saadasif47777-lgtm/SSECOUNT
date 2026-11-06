"use strict";

// This file handles browser events and displays results prepared by Python.
// Word cleaning, counting, sorting, filtering, search and percentages live
// in analyzer.py and backend/dashboard.py.
function byId(id) {
  return document.getElementById(id);
}

let selectedFile = null;
let useSample = false;
let analysis = null;
let currentPage = 1;
let requestNumber = 0;
let controlTimer = null;

function showMessage(text, kind = "") {
  byId("message").textContent = text;
  byId("message").className = kind;
}

function readControls() {
  // Send raw control values. Python validates and interprets them.
  return {
    order: byId("sort").value,
    minimum: byId("minimum").value,
    query: byId("search").value,
    top: byId("top").value,
    page: currentPage,
  };
}

function resetControls() {
  currentPage = 1;
  byId("sort").value = "high";
  byId("minimum").value = "1";
  byId("search").value = "";
  byId("search-result").textContent = "";
}

async function requestAnalysis(newDocument = false) {
  if (!selectedFile && !useSample) return;
  clearTimeout(controlTimer);
  requestNumber += 1;
  const thisRequest = requestNumber;

  if (newDocument) {
    analysis = null;
    byId("results").hidden = true;
    resetControls();
  }
  showMessage("Analyzing your document…");

  const controls = readControls();
  const settings = { method: "POST" };
  if (useSample) {
    settings.headers = { "Content-Type": "application/json" };
    settings.body = JSON.stringify({ sample: true, options: controls });
  } else {
    // Send original bytes so Python checks the filename, size and encoding.
    const form = new FormData();
    form.append("file", selectedFile);
    form.append("options", JSON.stringify(controls));
    settings.body = form;
  }

  try {
    const response = await fetch("/api/analyze", settings);
    const data = await response.json();
    // Ignore older responses if the user has already changed the document.
    if (thisRequest !== requestNumber) return;
    if (!response.ok)
      throw new Error(data.error || "Analysis failed. Please try again.");
    analysis = data;
    currentPage = data.dashboard.table.page;
    renderDashboard();
    byId("results").hidden = false;
    showMessage("Analyzed successfully: " + data.file_name, "success");
  } catch (error) {
    if (thisRequest !== requestNumber) return;
    const connectionError =
      error instanceof SyntaxError || error instanceof TypeError;
    const explanation = connectionError
      ? "Could not reach the analysis service. Please try again."
      : error.message;
    showMessage(explanation, "error");
    // Keep an existing document visible when a control value is invalid.
    // New-document requests already cleared the previous results above.
  }
}

function renderDashboard() {
  byId("filename").textContent = analysis.file_name;
  byId("total").textContent = analysis.total_words;
  byId("unique").textContent = analysis.unique_words;
  byId("characters").textContent = analysis.characters;
  byId("average").textContent = analysis.dashboard.average_display;
  byId("most-label").textContent =
    "Most frequent · " + analysis.highest + " occurrences each";
  byId("least-label").textContent =
    "Least frequent · " + analysis.lowest + " occurrences each";
  byId("most").textContent = analysis.most_words.join(", ");
  byId("least").textContent = analysis.least_words.join(", ");
  byId("original").textContent = analysis.original_text;
  byId("search-result").textContent = analysis.dashboard.search_message;
  const extra = analysis.extra_statistics;
  byId("numbers").textContent = extra.numeric_tokens;
  byId("unique-numbers").textContent = extra.unique_numbers;
  byId("digits").textContent = extra.digits;
  byId("lines").textContent = extra.nonempty_lines + " / " + extra.paragraphs;
  renderTable();
  renderChart();
}

function renderTable() {
  const table = analysis.dashboard.table;
  const body = byId("rows");
  body.replaceChildren();
  // Python has already sorted, filtered and paginated these rows.
  for (const item of table.rows) {
    const row = document.createElement("tr");
    for (const value of [item.word, item.count, item.share]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    body.append(row);
  }
  byId("table-caption").textContent =
    table.matching_words +
    " of " +
    analysis.unique_words +
    " unique words · table filters only";
  byId("empty-table").hidden = table.rows.length !== 0;
  byId("page-info").textContent =
    "Page " + table.page + " of " + table.page_count;
  byId("previous").disabled = table.page === 1;
  byId("next").disabled = table.page === table.page_count;
}

function renderChart() {
  const chart = byId("chart");
  chart.replaceChildren();
  let description = "Top word frequencies: ";
  // Bar lengths and top-word selection were calculated by Python.
  for (const item of analysis.dashboard.chart) {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.title = item.word + ": " + item.count;
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
    value.textContent = item.count;
    row.append(label, track, value);
    chart.append(row);
    description += item.word + ": " + item.count + ", ";
  }
  chart.setAttribute("aria-label", description);
}

function chooseFile(file) {
  selectedFile = file;
  useSample = false;
  requestAnalysis(true);
}

function chooseSample() {
  selectedFile = null;
  useSample = true;
  requestAnalysis(true);
}

function controlsChanged() {
  currentPage = 1;
  // Wait briefly while typing to avoid a request for every keystroke.
  clearTimeout(controlTimer);
  requestNumber += 1;
  controlTimer = setTimeout(requestAnalysis, 250);
}

function downloadReport() {
  if (!analysis) return;
  // Python wrote this complete report. The browser only saves the received text.
  const report = new Blob([analysis.report], {
    type: "text/plain;charset=utf-8",
  });
  const url = URL.createObjectURL(report);
  const link = document.createElement("a");
  link.href = url;
  link.download = "SSECOUNT-report.txt";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(function releaseDownload() {
    URL.revokeObjectURL(url);
  }, 1000);
}

// Connect each visible control to its browser action.
byId("file").addEventListener("change", function fileChosen(event) {
  if (event.target.files[0]) chooseFile(event.target.files[0]);
});
byId("sample").addEventListener("click", chooseSample);
byId("sort").addEventListener("change", controlsChanged);
byId("minimum").addEventListener("input", controlsChanged);
byId("top").addEventListener("change", controlsChanged);
byId("search").addEventListener("input", controlsChanged);
byId("download").addEventListener("click", downloadReport);
byId("previous").addEventListener("click", function previousPage() {
  currentPage -= 1;
  requestAnalysis();
});
byId("next").addEventListener("click", function nextPage() {
  currentPage += 1;
  requestAnalysis();
});

const dropzone = byId("dropzone");
for (const type of ["dragenter", "dragover"]) {
  dropzone.addEventListener(type, function highlightDropzone(event) {
    event.preventDefault();
    dropzone.classList.add("drag");
  });
}
for (const type of ["dragleave", "drop"]) {
  dropzone.addEventListener(type, function clearDropzone(event) {
    event.preventDefault();
    dropzone.classList.remove("drag");
  });
}
dropzone.addEventListener("drop", function fileDropped(event) {
  if (event.dataTransfer.files[0]) chooseFile(event.dataTransfer.files[0]);
});
