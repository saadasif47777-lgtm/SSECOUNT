"""Prepare dashboard data in Python; the frontend only displays these values.

All functions use ordinary variables, lists, dictionaries, loops and conditions.
The text-cleaning and word-counting functions are in analyzer.py.
"""
from analyzer import search_word, sort_frequencies

# These names match the values sent by the sort dropdown in the frontend.
SORT_OPTIONS = {
    'high': 'Highest frequency first',
    'low': 'Lowest frequency first',
    'az': 'Alphabetical (A–Z)',
    'za': 'Reverse alphabetical (Z–A)',
}
PAGE_SIZE = 50


def read_integer(options, name, default, smallest, largest):
    """Read one whole-number option and explain invalid input clearly."""
    value = options.get(name, default)
    # Reject decimals and booleans instead of silently changing their meaning.
    if isinstance(value, bool):
        raise ValueError(name + ' must be a whole number.')
    try:
        number = int(str(value))
    except (ValueError, TypeError):
        raise ValueError(name + ' must be a whole number.')
    if number < smallest or number > largest:
        raise ValueError(name + ' is outside the allowed range.')
    return number


def make_table(analysis, order, minimum, page):
    """Filter, sort and paginate words, including Python-calculated shares."""
    all_rows = sort_frequencies(analysis['frequencies'], order, minimum)
    matching_words = len(all_rows)

    # Adding PAGE_SIZE - 1 rounds the division up to a whole page.
    page_count = max(1, (matching_words + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page, page_count)
    first_row = (page - 1) * PAGE_SIZE
    last_row = first_row + PAGE_SIZE
    visible_rows = []

    for word, count in all_rows[first_row:last_row]:
        share = count / analysis['total_words'] * 100
        visible_rows.append({
            'word': word,
            'count': count,
            'share': format(share, '.2f') + '%',
        })

    return {
        'rows': visible_rows,
        'matching_words': matching_words,
        'page': page,
        'page_count': page_count,
    }


def make_chart(analysis, top_count):
    """Choose the most frequent words and calculate their relative bar widths."""
    top_rows = sort_frequencies(analysis['frequencies'])[:top_count]
    chart_rows = []
    for word, count in top_rows:
        width = count / analysis['highest'] * 100
        chart_rows.append({'word': word, 'count': count, 'width': width})
    return chart_rows


def make_search_message(query, analysis):
    """Use the same Python cleaning rules for both documents and searches."""
    if not query.strip():
        return ''
    try:
        word, count, share = search_word(query, analysis)
    except ValueError as error:
        return str(error)
    if count == 0:
        return '“' + word + '” does not appear in this document.'
    return word + ' appears ' + str(count) + ' time(s) · ' + format(share, '.2f') + '% of all words.'


def prepare_dashboard(analysis, options):
    """Validate controls and return table, chart and search display data."""
    order_name = options.get('order', 'high')
    if not isinstance(order_name, str) or order_name not in SORT_OPTIONS:
        raise ValueError('Choose a supported sorting option.')
    order = SORT_OPTIONS[order_name]
    minimum = read_integer(options, 'minimum', 1, 1, 1000000)
    page = read_integer(options, 'page', 1, 1, 1000000)
    top_count = read_integer(options, 'top', 10, 1, 20)
    query = options.get('query', '')
    if not isinstance(query, str) or len(query) > 1000:
        raise ValueError('Search must be text with at most 1000 characters.')

    return {
        'table': make_table(analysis, order, minimum, page),
        'chart': make_chart(analysis, top_count),
        'search_message': make_search_message(query, analysis),
        'average_display': format(analysis['average_length'], '.2f'),
    }
