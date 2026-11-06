# Readable Python backend

## Separation of responsibilities

| File | Purpose |
| --- | --- |
| `analyzer.py` | Core text-cleaning, dictionary counting, statistics, sorting, search and reports |
| `backend/dashboard.py` | Validate controls and prepare table pages, chart values and search messages |
| `backend/sample.py` | Sample document |
| `backend/extractors.py` | Convert supported document formats to text |
| `backend/statistics.py` | Count numeric tokens, digits, lines and paragraphs |
| `api/index.py` | Receive HTTP requests and return results from Python |
| `dev.py` | Run the web interface locally |
| `public/index.html` | Frontend structure |
| `public/style.css` | Frontend appearance |
| `public/app.js` | Send requests and display returned values |
| `vercel.json` | Hosting builds and routes |
| `app.py` | Optional Streamlit interface using the same analyzer |

The backend is entirely Python. Application functions use dictionaries, lists, loops, conditions, string methods, basic exception handling and named functions. No application classes, decorators, lambdas, comprehensions, machine learning, pandas or NumPy imports are used. Framework dependencies may internally use these techniques.

## Follow one request

1. The frontend sends original uploaded bytes and control values to `/api/analyze`. For sample mode it sends `sample: true`; the sample paragraph lives in Python.
2. `read_document()` reads the file in Python, enforces the 3 MB limit and calls `extract_text()` to read the supported document format. It also reads dashboard options. Requests with JSON text are supported for testing and API use.
3. `analyze_request()` checks for empty or wordless text and calls `analyze_text()`.
4. `analyze_text()` calls `clean_words()` and `count_words()`, then calculates the statistics. Start your viva explanation here.
5. `prepare_dashboard()` reads and validates controls. `read_integer()` rejects decimals, invalid text, booleans and out-of-range values instead of silently accepting them.
6. `make_table()` calls `sort_frequencies()`, takes the requested 50-row page, and calculates each percentage. `//` is whole-number division; `(matching_words + PAGE_SIZE - 1) // PAGE_SIZE` calculates how many pages are needed.
7. `make_chart()` chooses the top words and calculates each bar width relative to the maximum count.
8. `make_search_message()` reuses `search_word()`. Unicode and punctuation rules are therefore identical for searching and document analysis.
9. `make_report()` generates the complete report. The API packages this with original text, statistics and dashboard values using `jsonify()`.
10. JavaScript uses `textContent` to display values safely. It does not clean words, count, sort or calculate percentages. Clicking download saves the report string produced by Python.

Every control change sends the file again and recomputes the result in Python. This simple, stateless approach needs no database or server-side file storage, and works across independent serverless invocations. A 250 ms delay while typing reduces unnecessary requests. It is suitable for the bounded educational workflow; it is not designed for large-document processing.

## Read the code in this order

Start with `count_words()`: a repeated word increments its dictionary value; a new word starts at one. Continue to `clean_words()`, `analyze_text()`, `sort_frequencies()`, `search_word()` and `make_report()`. Then read `backend/dashboard.py`. Finally study `api/index.py`, which connects those calculations to HTTP.

`docs/LEARNING_GUIDE.md` explains the Python fundamentals, every nonblank analyzer line, examples and 35 viva questions. Source comments explain important decisions beside the code. `tests/test_dashboard.py` checks the Python calculations used by the web frontend.

See `docs/DOCUMENTS.md` for extraction functions, number-counting examples and format limitations. The analyzer passes cleaned tokens and extracted text to `count_extra_statistics()` and includes the resulting dictionary in the API response and report.
