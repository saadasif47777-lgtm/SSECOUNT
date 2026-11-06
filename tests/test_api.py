import io
import unittest
from api.index import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_counts_and_report(self):
        response = self.client.post('/api/analyze', json={'text': 'Hello HELLO café', 'file_name': 'test.txt'})
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['frequencies'], {'hello': 2, 'café': 1})
        self.assertIn('hello\t2\t66.67%', result['report'])
        self.assertNotIn('words', result)

    def test_bad_requests(self):
        for data in [None, [], {}, {'text': 10}, {'text': 'ok', 'file_name': 4}, {'text': 'ok', 'file_name': 'a.csv'}, {'text': ''}, {'text': '   '}, {'text': '!!!'}, {'text': '\x00'}]:
            with self.subTest(data=data):
                response = self.client.post('/api/analyze', json=data)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())

    def test_limits(self):
        response = self.client.post('/api/analyze', json={'text': 'a' * (3 * 1024 * 1024 + 1)})
        self.assertEqual(response.status_code, 413)
        self.assertIn('3 MB', response.get_json()['error'])
        response = self.client.post('/api/analyze', data=b'x' * (4 * 1024 * 1024 + 1), content_type='application/json')
        self.assertEqual(response.status_code, 413)

    def test_uploaded_bytes(self):
        response = self.client.post('/api/analyze', data={
            'file': (io.BytesIO('CAFÉ café'.encode('utf-8')), 'words.txt'),
            'options': '{"query": "café", "minimum": 2}',
        })
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['frequencies'], {'café': 2})
        self.assertIn('100.00%', result['dashboard']['search_message'])
        response = self.client.post('/api/analyze', data={
            'file': (io.BytesIO(b'\xff'), 'bad.txt'),
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('UTF-8', response.get_json()['error'])

    def test_sample_and_bad_options(self):
        response = self.client.post('/api/analyze', json={'sample': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['total_words'], 45)
        for options in [[], {'minimum': 'no'}, {'order': 'wrong'}]:
            response = self.client.post('/api/analyze', json={'sample': True, 'options': options})
            self.assertEqual(response.status_code, 400)

    def test_office_upload_and_numeric_counts(self):
        from test_extractors import container
        data = container({'word/document.xml': '<document><p><t>Hello 42 42</t></p></document>'})
        response = self.client.post('/api/analyze', data={
            'file': (io.BytesIO(data), 'report.docx'),
        })
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result['extra_statistics']['numeric_tokens'], 2)
        self.assertEqual(result['frequencies']['42'], 2)
