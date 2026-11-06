# How document extraction works

The counting algorithm should not know whether a word came from a PDF, slide, spreadsheet or text file. `backend/extractors.py` converts each supported document into one ordinary Python string. `analyzer.py` then processes that string exactly as it processes the sample paragraph.

## Follow the functions

1. `extract_text(file_name, file_bytes)` checks the byte limit and selects a reader using the filename extension. Modern document formats have dedicated readers. Other files use Unicode decoding, so a text file does not need a `.txt` extension. Unreadable binary content receives a helpful error.
2. `decode_text()` starts with UTF-8 and recognizes byte-order markers for UTF-16/32. It catches encoding problems and rejects binary control characters. It does not guess legacy encodings.
3. `read_archive()` opens a modern Office/OpenDocument ZIP container in memory. A loop adds up expanded entry sizes and checks the entry count before any XML is read. Password-protected entries are rejected. No archive is unpacked onto disk.
4. `local_name()` removes an XML namespace so the code can compare a simple element name such as `p` (paragraph) or `t` (text).
5. `paragraph_text()` loops over paragraphs and their text runs. Joining styled runs without extra spaces preserves a word split across formatting changes. OpenDocument paragraphs store text directly, so `itertext()` retrieves their text spans. Tabs and breaks become separators.
6. `extract_office()` selects the appropriate XML parts. Word uses document paragraphs and related headers/footers/notes. PowerPoint uses numbered slides; `slide_number()` makes slide 2 precede slide 10. OpenDocument reads `content.xml`.
7. `extract_spreadsheet()` reads shared strings, inline strings and cached values from worksheet cells. A shared-string cell contains an index into a list of strings. No spreadsheet formula is run.
8. `extract_legacy_excel()` uses `xlrd` for old `.xls` files, visits sheets/rows/cells, and releases workbook resources in a `finally` block. Whole-number floats are displayed as integers.
9. `extract_pdf()` uses `pypdf` to extract each page's text layer. Encrypted or overly long documents are rejected. A PDF without readable text gets an OCR message. Mixed PDFs may contain text alongside unprocessed image content; extraction does not turn those images into text.
10. RTF uses `striprtf` to remove formatting commands. HTML uses BeautifulSoup to remove script/style/template elements and extract page text.
11. `check_text_length()` enforces the extracted-character cap after reading. A 3 MB file can expand into much more text, so this is separate from the file-byte check.

These format readers need parsing libraries because document bytes are not plain text. The core counting logic remains a small loop and dictionary. XML uses `defusedxml` to reject unsafe entity processing. Uploaded code, macros, scripts, formulas and programs are never executed.

## Numeric and structural counts

`backend/statistics.py` is deliberately simple:

- Start `number_count` at zero and `unique_numbers` as an empty dictionary.
- Visit each cleaned token. If `word.isdecimal()` is true, increment the total and store the token as a dictionary key. Dictionary length gives the unique number count.
- Visit each extracted character. If `character.isdigit()` is true, increment the digit count.
- Visit `text.splitlines()`. Count nonempty lines. An `inside_paragraph` flag detects the first nonempty line after a blank line, so each block is counted once.
- Return the counts in a dictionary. `analyze_text()` includes this under `extra_statistics`; the dashboard and report display it.

For `Hello 42 42 12.5`, tokens include `42`, `42`, `12`, `5`: four numeric tokens, three unique numeric tokens, seven digit characters. These are token counts, not an arithmetic interpretation of decimal numbers.

## Practical limitations

No program can extract readable text from every possible file format automatically. Legacy `.doc`/`.ppt` and macro-enabled formats need export to a supported format. OCR is not bundled. PDF reading order, visual layout, automatic numbering, embedded charts, speaker notes and all document metadata are not reconstructed. Spreadsheet values may differ from formatted cell display, and formulas without cached values contribute no calculated result. Unknown text extensions work when their bytes are readable Unicode; unknown binary formats do not.
