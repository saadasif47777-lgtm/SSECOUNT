"""Simple text analysis using strings, lists, dictionaries, and loops."""
from backend.statistics import count_extra_statistics


def read_text_file(file_name, file_data):
    """Validate an uploaded filename and decode its bytes as UTF-8."""
    if not file_name.lower().endswith('.txt'):
        raise ValueError('Please choose a .txt file.')
    try:
        # utf-8-sig also removes an optional UTF-8 byte order mark.
        text = file_data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('This file is not valid UTF-8. Save it as UTF-8 text and try again.')
    if '\x00' in text:
        raise ValueError('This file contains binary data. Please upload a plain UTF-8 text file.')
    return text


def clean_words(text):
    """Lowercase text; replace every non-letter/non-number with a space."""
    cleaned_text = ''
    for character in text.lower():
        if character.isalnum():
            cleaned_text += character
        else:
            cleaned_text += ' '
    # split() automatically ignores repeated spaces, tabs, and newlines.
    return cleaned_text.split()


def count_words(words):
    """Build a dictionary mapping each word to its occurrence count."""
    # Each dictionary key is a word; its value is the occurrence count.
    frequencies = {}
    for word in words:
        # An existing word gains one occurrence; a new word starts at one.
        if word in frequencies:
            frequencies[word] += 1
        else:
            frequencies[word] = 1
    return frequencies


def frequency_key(row):
    """Named sorting key: rows are [word, count] pairs."""
    return row[1]


def sort_frequencies(frequencies, order='Highest frequency first', minimum=1):
    """Filter counts, then sort with alphabetical ordering for frequency ties."""
    rows = []
    # Starting alphabetically also gives predictable ordering for ties.
    for word in sorted(frequencies):
        if frequencies[word] >= minimum:
            rows.append([word, frequencies[word]])
    if order == 'Highest frequency first':
        rows.sort(key=frequency_key, reverse=True)
    elif order == 'Lowest frequency first':
        rows.sort(key=frequency_key)
    elif order == 'Reverse alphabetical (Z–A)':
        rows.reverse()
    return rows


def analyze_text(text):
    """Return words, frequencies, and document statistics, including all ties."""
    words = clean_words(text)
    frequencies = count_words(words)
    # Count the letters/numbers in every occurrence, including repeated words.
    letter_count = 0
    for word in words:
        letter_count += len(word)
    average_length = 0
    most_words = []
    least_words = []
    highest = 0
    lowest = 0
    # Empty text keeps the zero defaults and never divides by zero.
    if words:
        average_length = letter_count / len(words)
        counts = list(frequencies.values())
        highest = max(counts)
        lowest = min(counts)
        for word in sorted(frequencies):
            if frequencies[word] == highest:
                most_words.append(word)
            if frequencies[word] == lowest:
                least_words.append(word)
    # Meaningful dictionary keys make results easy for the interface to read.
    return {
        'extra_statistics': count_extra_statistics(text, words),
        'words': words,
        'frequencies': frequencies,
        'total_words': len(words),
        'unique_words': len(frequencies),
        'characters': len(text),
        'average_length': average_length,
        'most_words': most_words,
        'least_words': least_words,
        'highest': highest,
        'lowest': lowest,
    }


def search_word(query, analysis):
    """Require one cleaned word; return its count and share of all tokens."""
    # Apply exactly the same punctuation and lowercase rules to searches.
    words = clean_words(query)
    if len(words) != 1:
        raise ValueError('Enter exactly one word after punctuation is removed.')
    word = words[0]
    # get() returns zero instead of failing when the word is absent.
    count = analysis['frequencies'].get(word, 0)
    percent = 0
    if analysis['total_words'] > 0:
        percent = count / analysis['total_words'] * 100
    return word, count, percent


def make_report(file_name, analysis):
    """Create a complete plain-text report, independent of dashboard filters."""
    most = ', '.join(analysis['most_words']) or 'None'
    least = ', '.join(analysis['least_words']) or 'None'
    lines = [
        'SSECOUNT | Text Analysis Studio',
        '=' * 54,
        'File: ' + file_name,
        'Total words: ' + str(analysis['total_words']),
        'Unique words: ' + str(analysis['unique_words']),
        'Total characters: ' + str(analysis['characters']),
        'Numeric tokens: ' + str(analysis['extra_statistics']['numeric_tokens']),
        'Unique numbers: ' + str(analysis['extra_statistics']['unique_numbers']),
        'Digit characters: ' + str(analysis['extra_statistics']['digits']),
        'Nonempty lines: ' + str(analysis['extra_statistics']['nonempty_lines']),
        'Paragraphs: ' + str(analysis['extra_statistics']['paragraphs']),
        'Average word length: ' + format(analysis['average_length'], '.2f'),
        'Most frequent words: ' + most + ' (' + str(analysis['highest']) + ' each)',
        'Least frequent words: ' + least + ' (' + str(analysis['lowest']) + ' each)',
        '',
        'Rules: lowercase; non-alphanumeric characters separate words.',
        'Numbers are tokens; character count includes original whitespace.',
        '',
        'COMPLETE WORD FREQUENCY LIST',
        'Word\tCount\tShare of total words',
    ]
    # Use the full dictionary so a table filter never removes report entries.
    for word, count in sort_frequencies(analysis['frequencies']):
        percent = count / analysis['total_words'] * 100
        lines.append(word + '\t' + str(count) + '\t' + format(percent, '.2f') + '%')
    return '\n'.join(lines) + '\n'
