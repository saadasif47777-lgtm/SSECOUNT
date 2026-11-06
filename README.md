# SSECOUNT — Text Analysis Studio

Analyze words, numbers, and text statistics from documents using a readable Python backend and a responsive web dashboard. A Streamlit interface is also included for university presentations.

## Supported documents

| Files | What is analyzed |
| --- | --- |
| Word `.docx` | Paragraphs, table text, headers, footers, footnotes and endnotes |
| PowerPoint `.pptx` | Text on slides, in slide order, including text in tables |
| PDF `.pdf` | Selectable text from the PDF's text layer |
| Excel `.xlsx`, `.xls` | Cell text and stored/cached numbers across worksheets |
| OpenDocument `.odt`, `.odp`, `.ods` | Paragraphs and visible text in the document content |
| Rich Text `.rtf` | Text with formatting instructions removed |
| HTML `.html`, `.htm` | Page text without scripts, styles and templates |
| Plain text, CSV, TSV, Markdown, JSON, XML, logs, code | Unicode source text, including source syntax |
| Other extensions or no extension | Accepted when their contents decode as readable Unicode text |

The upload chooser accepts any extension. This does **not** mean every binary format is readable. Old Word `.doc` and PowerPoint `.ppt` files must be exported to `.docx`/`.pptx` or PDF first. Macro-enabled Office formats are not supported. Images, handwriting and scanned PDF pages need OCR before uploading; OCR is not included. Password-protected/encrypted files must be unlocked first. Embedded images and charts are not converted into text. Spreadsheet formulas are never evaluated; only cached values are read when available. Layout, formatting, annotations, presentation speaker notes, and visual reading order are not guaranteed to be preserved.

Files may be up to **3 MB**, with at most **100,000 extracted characters**. PDFs are limited to 200 pages. Office/OpenDocument archives are limited to 2,000 entries and 20 MB expanded content. These limits keep the educational app practical on serverless hosting. Plain text supports UTF-8 and BOM-marked UTF-16/32. Other encodings should be saved as UTF-8 first.

## Features

- Upload a document or analyze the built-in sample.
- Total tokens, unique tokens, extracted characters and average token length.
- Numeric tokens, unique numbers, digit characters, nonempty lines and paragraphs.
- All most/least frequent ties, a searchable frequency table, four sorting modes and minimum-frequency filtering.
- Top 5, 10, 15 or 20 words in a frequency chart.
- Complete downloadable text report, including numeric and document counts.
- Paginated results with 50 rows per page. Filters affect the table; reports contain all words.

## Counting rules

All calculations run in Python. Text is lowercased, and non-alphanumeric characters become word separators. `Hello, HELLO!` counts as two occurrences of `hello`. `don't` becomes `don` and `t`; `well-known` becomes `well` and `known`. Unicode letters and numbers are retained; no stopwords are removed. No linguistic segmentation, stemming or Unicode normalization is performed.

Numeric tokens are cleaned tokens containing only decimal digits. Thus `42 42 12.5` has four numeric tokens (`42`, `42`, `12`, `5`) and three unique numeric tokens. Digits count individual digit characters in the extracted text. Decimal points, signs and thousands separators follow the ordinary punctuation rule; the app does not interpret monetary values, dates or calculate a numeric sum.

Characters include spaces and punctuation in **extracted text**, not file bytes or visual grapheme clusters. Lines are nonempty extracted lines; paragraphs are blocks of nonempty lines separated by blank lines. Document extraction affects line/paragraph boundaries, so these are text counts rather than counts of visual PDF or Office layout objects. Average length includes repeated cleaned tokens. All frequency ties are listed alphabetically.

## Run the web application locally

Use Python 3.12 (the version selected for Vercel).

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python dev.py
```

The local development server prints its address and uses port 8502. Stop with Ctrl+C. No database, account or API keys are required.

## Deploy on Vercel

1. Import `saadasif47777-lgtm/SSECOUNT` from GitHub.
2. Set Framework Preset to **Other** and keep the root directory at the repository root.
3. Leave Build Command and Output Directory unset. Do not use `streamlit run` for Vercel.
4. Deploy `main`. `vercel.json` builds/routes the Python API and static frontend.

The web version sends uploaded files over HTTPS to the Python API, which extracts and analyzes text without writing documents to disk. Each control request is independent and resends the selected file; no session database is needed. Actual Vercel build and public deployment have not been verified here.

## Streamlit interface

```bash
python -m pip install -r requirements-streamlit.txt
python -m streamlit run app.py
```

This uses the same document readers and analyzer. Streamlit installs pandas/NumPy internally; our analysis code does not import or use them.

## Code organization

- `analyzer.py`: simple text cleaning, dictionary counting, statistics, sorting, search and reports.
- `backend/extractors.py`: Python readers for supported document formats.
- `backend/statistics.py`: number, digit, line and paragraph counts.
- `backend/dashboard.py`: Python-prepared table pages, search messages and chart values.
- `backend/sample.py`: sample document.
- `api/index.py`: Python HTTP adapter, upload limits, input validation and JSON responses.
- `dev.py`: local web server.
- `public/index.html`, `public/style.css`, `public/app.js`: frontend structure, appearance, requests and display.
- `app.py`, `.streamlit/config.toml`: Streamlit interface and theme.
- `requirements.txt`, `requirements-streamlit.txt`: pinned dependencies.
- `vercel.json`, `.python-version`: deployment configuration and Python runtime.
- `tests/`: backend/API/interface tests; `tests/fixtures/example.xls` is a generated, non-private workbook.
- `docs/`: backend teaching, line-by-line explanation, viva preparation and testing evidence.
- `Frequency`: preserved initial repository file; not used by the app.

The backend is Python throughout. Libraries parse document containers, while the word-counting algorithm remains visible in beginner-friendly dictionaries, loops, conditions and functions. JavaScript only sends input and renders Python results.

## Tests and learning

```bash
python -m pip install -r requirements-streamlit.txt
python -m unittest discover -s tests -v
```

Read [the backend guide](docs/BACKEND.md), [learning guide and viva questions](docs/LEARNING_GUIDE.md), [document reader guide](docs/DOCUMENTS.md), and [testing results](docs/TESTING.md).
