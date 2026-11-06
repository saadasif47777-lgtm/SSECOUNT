"""Additional document counts, using simple loops and dictionaries."""


def count_extra_statistics(text, words):
    """Count numeric tokens, digits, nonempty lines and paragraphs.

Numeric tokens follow the same cleaning rule as words: 12.5 becomes 12 and 5.
We do not guess currencies, dates, decimal values, or add numbers together.
"""
    number_count = 0
    unique_numbers = {}
    for word in words:
        if word.isdecimal():
            number_count += 1
            unique_numbers[word] = True

    digit_count = 0
    for character in text:
        if character.isdigit():
            digit_count += 1

    nonempty_lines = 0
    paragraph_count = 0
    inside_paragraph = False
    for line in text.splitlines():
        if line.strip():
            nonempty_lines += 1
            if not inside_paragraph:
                paragraph_count += 1
            inside_paragraph = True
        else:
            inside_paragraph = False

    return {
        'numeric_tokens': number_count,
        'unique_numbers': len(unique_numbers),
        'digits': digit_count,
        'nonempty_lines': nonempty_lines,
        'paragraphs': paragraph_count,
    }
