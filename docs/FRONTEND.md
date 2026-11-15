# SSECOUNT frontend

The web interface is deliberately separated from the Python analysis code. No frontend framework or build step is required.

| File                 | Responsibility                                                                                                   |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `public/index.html`  | Semantic layout, sidebar, upload area, result containers, format/counting guide                                  |
| `public/style.css`   | Design tokens, typography, responsive layouts, interaction states and reduced-motion rules                       |
| `public/app.js`      | File and sample requests, loading/error feedback, rendering, filtering controls, navigation and report downloads |
| `public/favicon.svg` | Local browser icon                                                                                               |

Section comments in these files explain the purpose of each group. Keep HTML out of Python handlers and CSS out of JavaScript; chart widths are the exception because they are returned by Python for each result.

## Design direction

The requested `design` skill and Motion Sites' **Data Signal** reference informed the visual direction: a charcoal hero, editorial display typography, warm orange details and restrained interface chrome. The reference is adapted to a working document dashboard, preserving SSECOUNT's name, upload controls and analysis features rather than copying the unrelated Vantage landing page. The hero illustration uses local HTML/CSS; it does not download videos, fonts or third-party scripts.

CSS tokens begin with palette primitives, map them to roles such as `--text`, `--surface`, `--accent` and `--border`, then define component values such as `--button-bg`. Change shared values in `:root` before adding component-specific overrides. A 4px/8px spacing scale, consistent corner radii and tabular numerals keep the workspace coherent.

The sidebar becomes a usable horizontal navigation on phones. Results use two metric columns on smaller screens and stack the chart/table as needed. Controls have visible labels and focus indicators, upload has a keyboard-operable native file input, and announcements use a live status region. Decorative illustrations are hidden from assistive technology. Optional entrance motion respects `prefers-reduced-motion`.

## Data and request behavior

1. Uploading a file or clicking **Try a sample** sends `POST /api/analyze`.
2. Python reads, cleans and counts the document and prepares the table, chart, search message and report.
3. JavaScript renders text using `textContent`, keeping uploaded content out of HTML interpretation.
4. New-document requests hide old results and restore the explanatory empty state. Result navigation links point to the empty state until analysis succeeds.
5. The latest request owns loading feedback; older responses cannot overwrite newer results. Controls debounce typing by 250ms.
6. Report download is disabled while requests are active and saves the complete Python-generated report as UTF-8 text.

Run `python dev.py` from the repository root and open the printed address. Do not open `public/index.html` directly: document analysis needs the Python API. The existing `vercel.json` serves the same public files and API when deployed.

## Redesign validation

- All 29 existing Python/backend/API/Streamlit tests pass.
- `node --check public/app.js` and `git diff --check` pass.
- Chrome checks confirmed the desktop design, successful sample analysis, word search, sorting, minimum-frequency empty results, and responsive layouts at 375px and 768px, plus landscape review in a viewport-sized preview frame.
- A separate DOM integration check using the actual frontend script against the running Python API verified the file input change handler, multipart upload, numeric metrics, report Blob/download action, invalid-file error and empty-state recovery. Its known text fixture produced 10 words, 3 numeric tokens, 2 unique numbers and 3 lines / 2 paragraphs.
- Native browser upload and saved-download completion could not be confirmed reliably through this environment's file-dialog controls. The DOM/API check validates these code paths, but does not prove a file was saved by Chrome.
- Production deployment is outside this verification; the checked-in Vercel routing remains compatible with the same static frontend and Python API.
