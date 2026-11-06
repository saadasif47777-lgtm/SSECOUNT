# Validation

Tested with Python 3.12 and Streamlit 1.51.0. The web API uses Flask 3.1.2.

## Automated tests

Run from the repository root after installing both requirements files:

```bash
python -m pip install -r requirements.txt -r requirements-streamlit.txt
python -m unittest discover -s tests -v
```

**29 tests passed.** They cover normal/repeated/case-insensitive/Unicode text, UTF-8 decoding and BOM removal, unsupported/invalid/empty/binary files, punctuation and whitespace, all sorting modes, frequency ties, minimum filters, found/missing/invalid searches, report contents, request validation, file/request limits, raw multipart uploads, sample analysis, Python-prepared chart/table/search values, pagination, and the Streamlit interface. Document-reader tests also cover DOCX text runs/tables/headers, numerical PPTX slide order, XLSX shared/inline/numeric cells, a generated XLS workbook fixture, OpenDocument formats, PDF text/scans/encryption, RTF, HTML, UTF-16/32, unknown text extensions, archive expansion/entity rejection, legacy-format errors, and numeric/digit/line/paragraph counts.

## Browser verification

A live Chromium session against the web dashboard and Python API verified:

- Sample statistics and chart rendering.
- Found, missing, multiword and Unicode searches through Python.
- All four sorting modes, frequency filtering, and every top-word chart option.
- Normal, empty, whitespace, punctuation, invalid Unicode, oversized and Unicode uploads.
- Successful DOCX, PPTX, PDF, XLSX, XLS, ODT, ODS, ODP, RTF, HTML and CSV uploads, with numeric counts checked for each format.
- OCR guidance for a scanned PDF; the removed frontend credit/status labels remain absent.
- Exact numeric token, unique-number, digit and line/paragraph counts for a controlled text example.
- An actual report download containing `hello`, count 2, share 66.67%.
- Pagination of 70 unique words into pages of 50 and 20.
- A 390-pixel mobile layout without horizontal document overflow.
- No browser JavaScript errors.

Validation scripts and screenshots are retained outside the repository at `/workspace/ssecount-validation/`. The current script is `document-browser.cjs`; current screenshots are `final-desktop.png` and `final-mobile.png`.

Actual Vercel cloud build and public deployment have not been verified. Import the repository with Framework Preset “Other” and no build/output overrides. Other browsers, assistive technologies and real mobile devices have not been tested.

Files are limited to 3 MB and 100,000 extracted characters; malformed/encrypted/unsupported binary content receives readable errors. These checks do not establish OCR or legacy Word/PowerPoint support. The XLS fixture was generated with xlwt as a test-only tool; xlwt is not required to run the app or tests. Office XML fixtures are small synthetic documents, not an exhaustive compatibility suite for every Office version.
