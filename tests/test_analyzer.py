import unittest
from analyzer import analyze_text, clean_words, read_text_file, search_word, sort_frequencies, make_report


class AnalysisTests(unittest.TestCase):
    def test_normal_file(self):
        text = read_text_file('normal.txt', b'Hello world!')
        result = analyze_text(text)
        self.assertEqual(result['frequencies'], {'hello': 1, 'world': 1})
        self.assertEqual(result['characters'], 12)
        self.assertEqual(result['average_length'], 5)

    def test_repetition_and_case(self):
        result = analyze_text('Python PYTHON python code')
        self.assertEqual(result['total_words'], 4)
        self.assertEqual(result['unique_words'], 2)
        self.assertEqual(result['most_words'], ['python'])
        self.assertEqual(result['least_words'], ['code'])

    def test_empty_space_and_punctuation(self):
        for text in ['', '   \n\t', '!!! — ,.?']:
            with self.subTest(text=text):
                result = analyze_text(text)
                self.assertEqual(result['total_words'], 0)
                self.assertEqual(result['average_length'], 0)
                self.assertEqual(result['most_words'], [])
                self.assertIn('None', make_report('empty.txt', result))

    def test_cleaning_and_unicode(self):
        self.assertEqual(clean_words("Don't well-known CAFÉ 123😊hello"), ['don', 't', 'well', 'known', 'café', '123', 'hello'])
        self.assertEqual(read_text_file('UNICODE.TXT', b'\xef\xbb\xbfhello'), 'hello')
        self.assertEqual(read_text_file('urdu.txt', 'سلام'.encode()), 'سلام')

    def test_invalid_uploads(self):
        for name, data in [('a.csv', b'text'), ('a.txt', b'\xff'), ('a.txt', b'a\x00b')]:
            with self.subTest(name=name, data=data):
                with self.assertRaises(ValueError):
                    read_text_file(name, data)

    def test_ties_and_sorting(self):
        result = analyze_text('b a c b a')
        self.assertEqual(result['most_words'], ['a', 'b'])
        self.assertEqual(sort_frequencies(result['frequencies']), [['a', 2], ['b', 2], ['c', 1]])
        self.assertEqual(sort_frequencies(result['frequencies'], 'Lowest frequency first'), [['c', 1], ['a', 2], ['b', 2]])
        self.assertEqual(sort_frequencies(result['frequencies'], 'Alphabetical (A–Z)'), [['a', 2], ['b', 2], ['c', 1]])
        self.assertEqual(sort_frequencies(result['frequencies'], 'Reverse alphabetical (Z–A)'), [['c', 1], ['b', 2], ['a', 2]])
        self.assertEqual(sort_frequencies(result['frequencies'], minimum=2), [['a', 2], ['b', 2]])
        self.assertEqual(sort_frequencies(result['frequencies'], minimum=5), [])

    def test_search(self):
        result = analyze_text('Hello hello world')
        word, count, percent = search_word('HELLO!', result)
        self.assertEqual((word, count), ('hello', 2))
        self.assertAlmostEqual(percent, 200 / 3)
        self.assertEqual(search_word('missing', result), ('missing', 0, 0))
        for query in ['!!!', 'two words', 'well-known']:
            with self.assertRaises(ValueError):
                search_word(query, result)

    def test_complete_report(self):
        result = analyze_text('one two two')
        report = make_report('example.txt', result)
        for expected in ['example.txt', 'Total words: 3', 'Unique words: 2', 'Total characters: 11', 'Average word length: 3.00', 'Most frequent words: two (2 each)', 'Least frequent words: one (1 each)', 'two\t2\t66.67%', 'one\t1\t33.33%']:
            self.assertIn(expected, report)
        self.assertEqual(report.encode('utf-8').decode('utf-8'), report)


if __name__ == '__main__':
    unittest.main()
