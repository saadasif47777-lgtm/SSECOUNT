"""Check that Python owns all dashboard calculations."""
import unittest
from analyzer import analyze_text
from backend.dashboard import prepare_dashboard


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        self.analysis = analyze_text('b a c b a')

    def test_sorted_filtered_rows(self):
        expected = {
            'high': ['a', 'b', 'c'],
            'low': ['c', 'a', 'b'],
            'az': ['a', 'b', 'c'],
            'za': ['c', 'b', 'a'],
        }
        for order in expected:
            result = prepare_dashboard(self.analysis, {'order': order})
            words = []
            for row in result['table']['rows']:
                words.append(row['word'])
            self.assertEqual(words, expected[order])
        result = prepare_dashboard(self.analysis, {'minimum': '2'})
        self.assertEqual(result['table']['matching_words'], 2)
        self.assertEqual(result['table']['rows'][0]['share'], '40.00%')
        result = prepare_dashboard(self.analysis, {'minimum': 10})
        self.assertEqual(result['table']['rows'], [])
        self.assertEqual(result['table']['page_count'], 1)

    def test_chart_and_search(self):
        result = prepare_dashboard(self.analysis, {'query': 'B!', 'top': 1})
        self.assertEqual(result['chart'], [{'word': 'a', 'count': 2, 'width': 100.0}])
        self.assertIn('2 time(s) · 40.00%', result['search_message'])
        result = prepare_dashboard(self.analysis, {'query': 'missing'})
        self.assertIn('does not appear', result['search_message'])
        result = prepare_dashboard(self.analysis, {'query': 'two words'})
        self.assertIn('exactly one', result['search_message'])

    def test_pagination(self):
        text = ''
        for number in range(70):
            text += 'word' + str(number) + ' '
        analysis = analyze_text(text)
        result = prepare_dashboard(analysis, {'page': 2})
        self.assertEqual(len(result['table']['rows']), 20)
        self.assertEqual(result['table']['page'], 2)
        result = prepare_dashboard(analysis, {'page': 999})
        self.assertEqual(result['table']['page'], 2)

    def test_invalid_controls(self):
        for options in [{'minimum': 1.5}, {'minimum': True}, {'minimum': 0}, {'page': 'bad'}, {'top': 21}, {'order': []}, {'order': 'wrong'}, {'query': 2}]:
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    prepare_dashboard(self.analysis, options)
