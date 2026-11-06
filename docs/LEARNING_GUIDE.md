# Learning SSECOUNT, step by step

## Part 1 — Project structure

Start with `analyzer.py`: it handles information and does not draw the screen. `app.py` imports its functions and displays their results using Streamlit. `requirements.txt` tells pip which interface library to install. `.streamlit/config.toml` chooses the theme and upload limit. `.gitignore` prevents temporary Python files and private local Streamlit configuration from entering Git. The two test files check the calculations and the interface. `README.md` explains running and using the project; this guide teaches its implementation; `TESTING.md` records verification. The `Frequency` file contains only a newline and is not used. Document readers live in `backend/extractors.py`; additional number and text-structure counts live in `backend/statistics.py`. See `docs/DOCUMENTS.md` for their explanations.

Keeping analysis separate means we can test counting without a browser. It also lets you explain the counting algorithm before discussing interface details.

## Part 2 — Python concepts used

- **Variable:** a name attached to a value. `letter_count = 0` stores a starting total.
- **String:** text between quotes. `text.lower()` returns a lowercase string; it does not change the original string.
- **List:** an ordered collection. `['hello', 'hello', 'world']` preserves repeated words. Index zero is the first item.
- **Dictionary:** key/value pairs. `{'hello': 2}` associates a word with its count. Keys are unique.
- **For loop:** repeats instructions for each item. `for word in words:` visits every token, including duplicates.
- **Condition:** chooses a path. `if word in frequencies:` asks whether a dictionary key exists. `else` handles a new word; `elif` adds another alternative.
- **Function:** a named group of instructions defined with `def`. Parameters are the inputs; a call supplies argument values.
- **String methods:** `.lower()` changes case, `.isalnum()` recognizes letters/numbers, `.split()` creates tokens, `.endswith()` checks the filename suffix, and `.join()` combines strings.
- **File handling:** the upload widget reads a browser-selected file; `.getvalue()` retrieves its bytes. `.decode('utf-8-sig')` turns bytes into Python text. A report is a string that Streamlit sends as a downloadable file. For a local file, the equivalent is `with open('example.txt', encoding='utf-8-sig') as file: text = file.read()`; the `with` block closes it automatically.
- **Exception handling:** `try` runs an operation that may fail; `except` handles a particular failure. `raise ValueError(...)` gives the caller a helpful explanation. The interface catches it and displays a message.
- **Return:** sends a result back to the caller and ends that function call.
- **Imports:** `from analyzer import analyze_text` makes that function available. Streamlit supplies UI tools, not our counting logic.
- **Indentation:** tells Python which lines belong to a function, loop, or condition.
- **Named sorting keys:** `key=frequency_key` passes a function for Python to call on each row; it does not call the function immediately. No lambda is needed.

## Part 3 — Backend walkthrough

Read each explanation beside the function in `analyzer.py`. Blank lines separate ideas; triple-quoted text is documentation, not counting logic. The annotated source listing after this walkthrough explains each nonblank source line.

### read_text_file(file_name, file_data)

Purpose: validate the name and decode file bytes so later functions receive strings. Inputs: a filename string and byte content. Output: decoded text, or a helpful exception. Concepts: strings, conditions, methods, try/except, return.

The suffix check lowercases only the filename for comparison, allowing `.TXT`. It is a first check, not proof that bytes are text. Decoding uses UTF-8 with an optional BOM; invalid encoding raises `UnicodeDecodeError`. We convert that error into an understandable `ValueError`. NUL is a common sign of binary or UTF-16 content and is rejected. Other valid UTF-8 control characters become separators later. Empty strings are returned successfully so the interface can distinguish an empty file from a decoding failure.

### clean_words(text)

Purpose: define a predictable token rule. Input: original text. Output: a list of lowercase tokens. Concepts: strings, iteration, conditions, concatenation, methods, return.

Start with an empty string. Visit each lowercase character. Keep it if it is a Unicode letter or number; otherwise add a space. We replace punctuation rather than deleting it, so `one,two` does not become `onetwo`. Finally `split()` separates on whitespace and discards empty pieces. Apostrophes, hyphens, and emoji follow this same rule. The original text remains available for the character statistic and preview.

### count_words(words)

Purpose: implement frequency counting visibly. Input: token list. Output: dictionary of counts. Concepts: dictionary, loop, membership condition, assignment, addition, return.

`frequencies = {}` creates an empty dictionary. For each word, ask whether it is already a key. If yes, `+= 1` increments the stored number. If no, start at 1. Return the completed dictionary after the loop finishes. Returning inside the loop would count only the first token!

### frequency_key(row)

Purpose: tell sorting which part of a `[word, count]` pair matters. Input: one row. Output: the count at index 1. Concepts: function, list indexing, return. Index 0 holds the word. This named helper replaces an advanced-looking anonymous lambda.

### sort_frequencies(frequencies, order, minimum)

Purpose: produce filtered table rows in the requested order. Inputs: dictionary, sort label, minimum count (defaults are provided). Output: list of `[word, count]` pairs. Concepts: defaults, loop, list append, conditions, named key function, sort.

First iterate over `sorted(frequencies)`, which supplies alphabetically ordered keys. Include a row only if its count is at least the minimum. Highest-first sorts by count with `reverse=True`; lowest-first uses ordinary ascending count order. Python's stable sort keeps the earlier alphabetical order for equal counts. Z–A reverses the alphabetic rows. A–Z needs no extra operation because rows already start in alphabetic order. `sort()` and `reverse()` change a list in place; they do not return the sorted list. The final `return rows` supplies it.

### analyze_text(text)

Purpose: combine cleaning, counting, and statistics. Input: original text string. Output: one dictionary containing tokens, counts, and statistics. Concepts: function calls, loops, accumulators, lists, dictionaries, min/max, conditions, arithmetic.

Call `clean_words`, then `count_words`. Add the length of every token to `letter_count`; repeated tokens contribute each time. Set safe empty defaults before calculations. If there are words, divide their combined length by their count. Convert dictionary values into a list and obtain maximum/minimum counts. Loop through alphabetic keys and append every word tied at either extreme. The two `if` statements are independent: when all words have the same count, each belongs to both lists. Return a dictionary so the interface can access results with meaningful keys. `len(text)` counts the original characters, `len(words)` counts all tokens, and `len(frequencies)` counts unique tokens.

### search_word(query, analysis)

Purpose: look up one normalized word. Inputs: user query and analysis dictionary. Output: a tuple `(word, count, percent)` or an exception for an invalid multiword/empty query. Concepts: function reuse, list indexing, dictionary lookup, arithmetic, conditions, tuple return.

Clean the query with exactly the document's rule. Require exactly one resulting token to avoid silently searching part of a phrase. Read its count using `.get(word, 0)`, which returns zero if absent. Default the percentage to zero; divide only when total words is positive. A count of 2 among 8 tokens is 25%, not 2 divided by unique words.

### make_report(file_name, analysis)

Purpose: create a readable, complete export. Inputs: source filename and results. Output: a newline-separated string. Concepts: lists, string joining, numeric conversion, formatting, loops, unpacking, return.

Join all tied words with commas; use `None` if the list is empty. Build header lines and statistics using `str` because strings cannot be directly concatenated with integers. `format(value, '.2f')` displays two decimal places without changing the underlying calculation. Loop over the full dictionary in highest-frequency order, calculate each share, and append tab-separated lines. Unpacking `for word, count` assigns the two parts of a row to separate names. Finally join lines using newline characters and add a final newline. Empty results have no rows, so no division happens inside that loop. This function never reads the dashboard filter: exports are complete by design.

## Part 4 — Feature-to-code map

| Feature | Responsible code |
|---|---|
| Upload, filename, success, no-file state | `app.py`: `st.file_uploader`, `uploaded.name`, success/info messages |
| Extension, decoding, binary rejection | `read_text_file`; UI try/except |
| Empty/space/punctuation warning | `app.py` checks `text` then `analysis['words']` |
| Lowercase and punctuation rule | `clean_words` |
| Frequency dictionary | `count_words` |
| Six required statistics and all ties | `analyze_text`; four metrics and two extreme-word cards |
| Four sorts, minimum count | `sort_frequencies`; selectbox and number input |
| Search, missing result, percentage | `search_word`; text input and result messages |
| Top five and adjustable chart | `app.py`: `top_count`, slicing sorted rows, Vega-Lite chart |
| Complete report and download | `make_report`; `st.download_button` |
| Sample paragraph | `backend/sample.py`: `SAMPLE_TEXT`; `app.py`: source radio |
| Theme and responsive layout | `.streamlit/config.toml`, CSS, Streamlit columns/sidebar |

Streamlit reruns the script from top to bottom when a widget changes. The selected file and widget values are managed by Streamlit. The chart receives ordinary lists/dictionaries. Vega-Lite describes how to draw bars and labels; it does not compute word counts. Custom HTML is static; uploaded text is rendered with Streamlit's safe text widgets rather than inserted into HTML.

## Part 5 — Trace small examples yourself

For `Cat, cat! Dog`, lowercase gives `cat, cat! dog`; replacements give `cat  cat  dog`; splitting gives `['cat', 'cat', 'dog']`.

| Loop step | Word | Already present? | Dictionary after step |
|---|---|---|---|
| 1 | cat | No | `{'cat': 1}` |
| 2 | cat | Yes | `{'cat': 2}` |
| 3 | dog | No | `{'cat': 2, 'dog': 1}` |

Total words = 3; unique = 2; original characters = 13; average length = (3+3+3)/3 = 3.00. Search for `CAT!` gives `cat`, count 2, share 66.67%. A minimum of 2 shows only cat, but downloading still includes dog. For `red blue`, both words appear in both extreme lists. For `!!!`, the list is empty and the interface asks for meaningful text.

Try changing `+= 1` to `= 1` on paper: repeats would never accumulate. Try removing `else`: accessing an absent dictionary key would fail. These examples explain why each branch matters.

## Part 6 — Viva preparation

1. **What is SSECOUNT?** A UTF-8 text analyzer that counts words and presents statistics, charts, search, and a report.
2. **What is a variable?** A name referring to a value, such as `text`.
3. **What is a string?** A sequence of text characters.
4. **Why lowercase?** So `Hello` and `hello` count together.
5. **What is a list?** An ordered collection that can contain duplicates.
6. **What is a dictionary?** A collection mapping unique keys to values.
7. **Why use a dictionary here?** Each word is a key and its count is the value.
8. **What does `in` check on a dictionary?** Whether a key exists.
9. **What does `+= 1` do?** Adds one to the existing count.
10. **Why start a new word at 1?** We have just encountered it once.
11. **What does the for loop visit?** Every token, including repeated tokens.
12. **What is a function?** Reusable named instructions with inputs and a result.
13. **What does return do?** Sends the result to the caller and ends the call.
14. **What if return is inside the counting loop?** It stops after the first token, producing incomplete results.
15. **What does split do?** Divides text on whitespace into nonempty tokens.
16. **Why replace punctuation with spaces?** To avoid merging adjacent words.
17. **How is don't counted?** As `don` and `t`, following the documented separator rule.
18. **Are digits counted?** Yes, `isalnum()` includes numbers.
19. **Are common words removed?** No; every valid token contributes.
20. **What is UTF-8?** A standard encoding that represents Unicode text as bytes.
21. **Why decode bytes?** Uploaded file bytes must become Python strings for text methods.
22. **What is exception handling?** Catching a known failure and displaying a helpful response.
23. **How are empty files handled?** The UI warns; statistics functions safely return zero values.
24. **What are total and unique counts?** Total includes repeats; unique counts distinct dictionary keys.
25. **How is average length calculated?** Sum cleaned token lengths including repeats, divided by total token count.
26. **Why guard division?** An empty token list would otherwise divide by zero.
27. **How are ties handled?** Every maximum/minimum word is included, alphabetically.
28. **What does the sorting key return?** The count in each row, so Python sorts numerically.
29. **Why alphabetic ties survive frequency sorting?** Python sorting is stable and the rows begin alphabetically.
30. **What does dictionary get do?** Returns the value or a supplied default when the key is absent.
31. **What is Streamlit?** A library that builds interactive web interfaces from Python scripts.
32. **Does changing a filter change the document?** No; it only changes the rows shown in the table.
33. **Why is search percentage divided by total tokens?** It measures the share of all occurrences, not distinct vocabulary.
34. **What are limitations?** In-memory processing, no linguistic segmentation/stemming, apostrophe splitting, no normalization of combining accents, and a 3 MB upload cap and a 100,000-character extraction limit.
35. **How would you prove you understand the code?** Trace a three-word example, explain each dictionary update, predict tie behavior, and show why empty input needs a division guard.

## Suggested learning order

First trace `count_words` on paper. Next understand `clean_words`. Then study `analyze_text`, sorting, search, and report generation. Finally read the UI: it mainly calls these functions and displays results. Run the tests and change your own input examples to compare your predictions with actual outputs.

## Appendix — Every nonblank backend line

Line numbers refer to `analyzer.py`. Blank lines separate ideas.

**Line 1**

```python
"""Simple text analysis using strings, lists, dictionaries, and loops."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 2**

```python
from backend.statistics import count_extra_statistics
```

Import the simple helper that counts numeric tokens, digits, lines and paragraphs.

**Line 5**

```python
def read_text_file(file_name, file_data):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 6**

```python
    """Validate an uploaded filename and decode its bytes as UTF-8."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 7**

```python
    if not file_name.lower().endswith('.txt'):
```

Check that the lowercased filename ends in .txt.

**Line 8**

```python
        raise ValueError('Please choose a .txt file.')
```

Stop with a readable error when the extension is unsupported.

**Line 9**

```python
    try:
```

Begin the decoding operation that may fail.

**Line 10**

```python
        # utf-8-sig also removes an optional UTF-8 byte order mark.
```

A comment for the reader; Python does not execute it.

**Line 11**

```python
        text = file_data.decode('utf-8-sig')
```

Decode bytes as UTF-8, removing an optional BOM.

**Line 12**

```python
    except UnicodeDecodeError:
```

Handle invalid UTF-8 bytes specifically.

**Line 13**

```python
        raise ValueError('This file is not valid UTF-8. Save it as UTF-8 text and try again.')
```

Replace the technical decoding error with a user-facing explanation.

**Line 14**

```python
    if '\x00' in text:
```

Look for a NUL character in the decoded string.

**Line 15**

```python
        raise ValueError('This file contains binary data. Please upload a plain UTF-8 text file.')
```

Reject likely binary data.

**Line 16**

```python
    return text
```

Send the decoded original string back.

**Line 19**

```python
def clean_words(text):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 20**

```python
    """Lowercase text; replace every non-letter/non-number with a space."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 21**

```python
    cleaned_text = ''
```

Create the empty string that will hold cleaned text.

**Line 22**

```python
    for character in text.lower():
```

Loop through each character of the lowercased text.

**Line 23**

```python
        if character.isalnum():
```

Ask whether this character is a letter or number.

**Line 24**

```python
            cleaned_text += character
```

Keep that character by adding it to the cleaned string.

**Line 25**

```python
        else:
```

Handle every other character.

**Line 26**

```python
            cleaned_text += ' '
```

Replace that separator with a space.

**Line 27**

```python
    # split() automatically ignores repeated spaces, tabs, and newlines.
```

A comment for the reader; Python does not execute it.

**Line 28**

```python
    return cleaned_text.split()
```

Split on whitespace and return a list without empty tokens.

**Line 31**

```python
def count_words(words):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 32**

```python
    """Build a dictionary mapping each word to its occurrence count."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 33**

```python
    # Each dictionary key is a word; its value is the occurrence count.
```

Comment: Each dictionary key is a word; its value is the occurrence count. Python does not execute comments.

**Line 34**

```python
    frequencies = {}
```

Create an empty word-to-count dictionary.

**Line 35**

```python
    for word in words:
```

Visit every token in order.

**Line 36**

```python
        # An existing word gains one occurrence; a new word starts at one.
```

Comment: An existing word gains one occurrence; a new word starts at one. Python does not execute comments.

**Line 37**

```python
        if word in frequencies:
```

Check whether this token already has a dictionary entry.

**Line 38**

```python
            frequencies[word] += 1
```

Increase the existing count by one.

**Line 39**

```python
        else:
```

Handle a word seen for the first time.

**Line 40**

```python
            frequencies[word] = 1
```

Store its first occurrence as one.

**Line 41**

```python
    return frequencies
```

Return the completed frequency dictionary.

**Line 44**

```python
def frequency_key(row):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 45**

```python
    """Named sorting key: rows are [word, count] pairs."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 46**

```python
    return row[1]
```

Return the second item of the row: its numeric count.

**Line 49**

```python
def sort_frequencies(frequencies, order='Highest frequency first', minimum=1):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 50**

```python
    """Filter counts, then sort with alphabetical ordering for frequency ties."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 51**

```python
    rows = []
```

Create an empty list for filtered rows.

**Line 52**

```python
    # Starting alphabetically also gives predictable ordering for ties.
```

Comment: Starting alphabetically also gives predictable ordering for ties. Python does not execute comments.

**Line 53**

```python
    for word in sorted(frequencies):
```

Visit dictionary keys alphabetically.

**Line 54**

```python
        if frequencies[word] >= minimum:
```

Keep only words reaching the minimum occurrence count.

**Line 55**

```python
            rows.append([word, frequencies[word]])
```

Append a two-item list holding the word and its count.

**Line 56**

```python
    if order == 'Highest frequency first':
```

Select descending frequency sorting.

**Line 57**

```python
        rows.sort(key=frequency_key, reverse=True)
```

Sort in place by count from largest to smallest.

**Line 58**

```python
    elif order == 'Lowest frequency first':
```

Select ascending frequency sorting.

**Line 59**

```python
        rows.sort(key=frequency_key)
```

Sort in place by count from smallest to largest.

**Line 60**

```python
    elif order == 'Reverse alphabetical (Z–A)':
```

Select reverse alphabetical order.

**Line 61**

```python
        rows.reverse()
```

Reverse the alphabetic list in place.

**Line 62**

```python
    return rows
```

Return the filtered and ordered rows.

**Line 65**

```python
def analyze_text(text):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 66**

```python
    """Return words, frequencies, and document statistics, including all ties."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 67**

```python
    words = clean_words(text)
```

Call the cleaning function to obtain tokens.

**Line 68**

```python
    frequencies = count_words(words)
```

Call the dictionary counter on those tokens.

**Line 69**

```python
    # Count the letters/numbers in every occurrence, including repeated words.
```

Comment: Count the letters/numbers in every occurrence, including repeated words. Python does not execute comments.

**Line 70**

```python
    letter_count = 0
```

Start the combined token-length accumulator at zero.

**Line 71**

```python
    for word in words:
```

Visit every occurrence, including duplicates.

**Line 72**

```python
        letter_count += len(word)
```

Add this token length to the accumulator.

**Line 73**

```python
    average_length = 0
```

Use zero as the average for empty input.

**Line 74**

```python
    most_words = []
```

Prepare a list for all most-frequent ties.

**Line 75**

```python
    least_words = []
```

Prepare a list for all least-frequent ties.

**Line 76**

```python
    highest = 0
```

Use zero as the maximum for empty input.

**Line 77**

```python
    lowest = 0
```

Use zero as the minimum for empty input.

**Line 78**

```python
    # Empty text keeps the zero defaults and never divides by zero.
```

Comment: Empty text keeps the zero defaults and never divides by zero. Python does not execute comments.

**Line 79**

```python
    if words:
```

Calculate nonempty statistics only if the token list has items.

**Line 80**

```python
        average_length = letter_count / len(words)
```

Divide combined token length by the number of occurrences.

**Line 81**

```python
        counts = list(frequencies.values())
```

Collect dictionary counts into a list.

**Line 82**

```python
        highest = max(counts)
```

Find the largest occurrence count.

**Line 83**

```python
        lowest = min(counts)
```

Find the smallest occurrence count.

**Line 84**

```python
        for word in sorted(frequencies):
```

Visit words alphabetically to produce deterministic tie lists.

**Line 85**

```python
            if frequencies[word] == highest:
```

Check whether this word ties for the highest count.

**Line 86**

```python
                most_words.append(word)
```

Add this highest-frequency word to the list.

**Line 87**

```python
            if frequencies[word] == lowest:
```

Independently check whether it ties for the lowest count.

**Line 88**

```python
                least_words.append(word)
```

Add this lowest-frequency word to the list.

**Line 89**

```python
    # Meaningful dictionary keys make results easy for the interface to read.
```

Comment: Meaningful dictionary keys make results easy for the interface to read. Python does not execute comments.

**Line 90**

```python
    return {
```

Begin returning a dictionary of named results.

**Line 91**

```python
        'extra_statistics': count_extra_statistics(text, words),
```

Calculate additional numeric and text-structure counts and include their dictionary in the result.

**Line 92**

```python
        'words': words,
```

Store the cleaned token list.

**Line 93**

```python
        'frequencies': frequencies,
```

Store the frequency dictionary.

**Line 94**

```python
        'total_words': len(words),
```

Store the count of every token occurrence.

**Line 95**

```python
        'unique_words': len(frequencies),
```

Store the number of distinct dictionary keys.

**Line 96**

```python
        'characters': len(text),
```

Store the original decoded character count.

**Line 97**

```python
        'average_length': average_length,
```

Store the unrounded average token length.

**Line 98**

```python
        'most_words': most_words,
```

Store every most-frequent word.

**Line 99**

```python
        'least_words': least_words,
```

Store every least-frequent word.

**Line 100**

```python
        'highest': highest,
```

Store the maximum occurrence count.

**Line 101**

```python
        'lowest': lowest,
```

Store the minimum occurrence count.

**Line 102**

```python
    }
```

Close the result dictionary.

**Line 105**

```python
def search_word(query, analysis):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 106**

```python
    """Require one cleaned word; return its count and share of all tokens."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 107**

```python
    # Apply exactly the same punctuation and lowercase rules to searches.
```

Comment: Apply exactly the same punctuation and lowercase rules to searches. Python does not execute comments.

**Line 108**

```python
    words = clean_words(query)
```

Normalize the search query with the document cleaning rule.

**Line 109**

```python
    if len(words) != 1:
```

Reject queries that produce zero or more than one token.

**Line 110**

```python
        raise ValueError('Enter exactly one word after punctuation is removed.')
```

Explain how to correct an invalid query.

**Line 111**

```python
    word = words[0]
```

Take the single valid token at list index zero.

**Line 112**

```python
    # get() returns zero instead of failing when the word is absent.
```

Comment: get() returns zero instead of failing when the word is absent. Python does not execute comments.

**Line 113**

```python
    count = analysis['frequencies'].get(word, 0)
```

Read its frequency, or zero if it is absent.

**Line 114**

```python
    percent = 0
```

Default the share to zero.

**Line 115**

```python
    if analysis['total_words'] > 0:
```

Check the denominator before dividing.

**Line 116**

```python
        percent = count / analysis['total_words'] * 100
```

Calculate its percentage of all token occurrences.

**Line 117**

```python
    return word, count, percent
```

Return three results as a tuple.

**Line 120**

```python
def make_report(file_name, analysis):
```

Define this named function with the listed input parameters; its indented body runs when called.

**Line 121**

```python
    """Create a complete plain-text report, independent of dashboard filters."""
```

Documentation string explaining the module or function; it does not perform analysis.

**Line 122**

```python
    most = ', '.join(analysis['most_words']) or 'None'
```

Join maximum-frequency ties; choose None if empty.

**Line 123**

```python
    least = ', '.join(analysis['least_words']) or 'None'
```

Join minimum-frequency ties; choose None if empty.

**Line 124**

```python
    lines = [
```

Start a list of report lines.

**Line 125**

```python
        'SSECOUNT | Text Analysis Studio',
```

Add the report title.

**Line 126**

```python
        '=' * 54,
```

Repeat an equals sign 54 times to make a separator.

**Line 127**

```python
        'File: ' + file_name,
```

Include the source filename.

**Line 128**

```python
        'Total words: ' + str(analysis['total_words']),
```

Convert the total count to text for concatenation.

**Line 129**

```python
        'Unique words: ' + str(analysis['unique_words']),
```

Include the distinct word count.

**Line 130**

```python
        'Total characters: ' + str(analysis['characters']),
```

Include the original character count.

**Line 131**

```python
        'Numeric tokens: ' + str(analysis['extra_statistics']['numeric_tokens']),
```

Convert this additional statistic to text and include it in the downloadable report.

**Line 132**

```python
        'Unique numbers: ' + str(analysis['extra_statistics']['unique_numbers']),
```

Convert this additional statistic to text and include it in the downloadable report.

**Line 133**

```python
        'Digit characters: ' + str(analysis['extra_statistics']['digits']),
```

Convert this additional statistic to text and include it in the downloadable report.

**Line 134**

```python
        'Nonempty lines: ' + str(analysis['extra_statistics']['nonempty_lines']),
```

Convert this additional statistic to text and include it in the downloadable report.

**Line 135**

```python
        'Paragraphs: ' + str(analysis['extra_statistics']['paragraphs']),
```

Convert this additional statistic to text and include it in the downloadable report.

**Line 136**

```python
        'Average word length: ' + format(analysis['average_length'], '.2f'),
```

Display the average with two decimal places.

**Line 137**

```python
        'Most frequent words: ' + most + ' (' + str(analysis['highest']) + ' each)',
```

Include every most-frequent tie and its count.

**Line 138**

```python
        'Least frequent words: ' + least + ' (' + str(analysis['lowest']) + ' each)',
```

Include every least-frequent tie and its count.

**Line 139**

```python
        '',
```

Add a blank separator line.

**Line 140**

```python
        'Rules: lowercase; non-alphanumeric characters separate words.',
```

Record the cleaning rule in the export.

**Line 141**

```python
        'Numbers are tokens; character count includes original whitespace.',
```

Explain numbers and original character counting.

**Line 142**

```python
        '',
```

Add a blank separator line.

**Line 143**

```python
        'COMPLETE WORD FREQUENCY LIST',
```

Add the frequency-list heading.

**Line 144**

```python
        'Word\tCount\tShare of total words',
```

Add tab-separated column headings.

**Line 145**

```python
    ]
```

Close the initial report-lines list.

**Line 146**

```python
    # Use the full dictionary so a table filter never removes report entries.
```

Comment: Use the full dictionary so a table filter never removes report entries. Python does not execute comments.

**Line 147**

```python
    for word, count in sort_frequencies(analysis['frequencies']):
```

Visit all sorted frequency rows and unpack each into two names.

**Line 148**

```python
        percent = count / analysis['total_words'] * 100
```

Calculate each word’s document share.

**Line 149**

```python
        lines.append(word + '\t' + str(count) + '\t' + format(percent, '.2f') + '%')
```

Append a tab-separated row with a two-decimal percentage.

**Line 150**

```python
    return '\n'.join(lines) + '\n'
```

Join all lines using newline characters and add a final newline.

## Vercel web version

`app.py` provides the optional Streamlit interface. Vercel instead serves `public/index.html`, styles it with `public/style.css`, and runs browser interactions in `public/app.js`. The browser sends text to `/api/analyze`; `api/index.py` validates the JSON request and calls the same `analyze_text` and `make_report` functions explained above. The response is JSON: a text format for dictionaries, lists, numbers, and strings.

`Flask(__name__)` creates the small HTTP adapter. `request.get_json(silent=True)` reads the incoming data without exposing a parsing traceback. `isinstance` validates types before using string methods. The adapter checks the filename, UTF-8 byte size, NUL characters, empty input and absence of tokens. `jsonify` turns result dictionaries into JSON responses. A return value paired with `400` means invalid input; `413` means too large. `app.add_url_rule` registers the analysis function for POST requests without decorators. `app.register_error_handler` converts oversized requests to helpful JSON errors. There are no classes or decorators in the application code.

The `words` list is removed from the response after counting to avoid sending duplicate data. The complete report is still produced by Python. Python also prepares search messages, sorted and filtered table pages, percentages and chart values in `backend/dashboard.py`. JavaScript only sends files/control values and displays the returned data. Text is inserted using `textContent`, so uploaded markup is displayed as text rather than executed. Stale responses are ignored using a request counter when the user selects another file before analysis finishes.

`dev.py` serves these same assets/API for local testing. `vercel.json` tells Vercel to build static assets and the Python serverless entrypoint, routing API requests separately. `.python-version` selects Python 3.12. `requirements.txt` installs Flask for this version; `requirements-streamlit.txt` installs Streamlit for the Streamlit interface. The web table paginates 50 rows at a time; reports contain all rows. The 3 MB upload cap applies to both interfaces and keeps request sizes bounded. Extracted text is also limited to 100,000 characters.

## Reading other document formats

`backend/extractors.py` now prepares text from supported documents before this analyzer runs. `backend/statistics.py` counts numeric tokens, unique numbers, digits, nonempty lines and paragraphs with loops and dictionaries. Read `docs/DOCUMENTS.md` for the complete extraction walkthrough, examples and supported formats. The strict `read_text_file()` helper remains for direct JSON text requests and its tests; actual document uploads use `extract_text()`.
