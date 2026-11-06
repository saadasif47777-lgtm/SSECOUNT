import unittest
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_dashboard_interactions(self):
        app = AppTest.from_file('app.py').run()
        self.assertFalse(app.exception)
        self.assertIn('Your workspace is ready', app.info[0].value)
        app.radio[0].set_value('Explore sample').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 8)
        self.assertGreater(int(app.metric[0].value), 0)
        self.assertEqual(len(app.dataframe), 1)
        self.assertEqual(len(app.get('download_button')), 1)
        app.text_input[0].set_value('curiosity').run()
        self.assertIn('appears 2 time(s)', app.success[-1].value)
        app.text_input[0].set_value('zzmissing').run()
        self.assertIn('does not appear', app.info[-1].value)
        app.text_input[0].set_value('two words').run()
        self.assertIn('exactly one word', app.warning[-1].value)
        for order in ['Lowest frequency first', 'Alphabetical (A–Z)', 'Reverse alphabetical (Z–A)', 'Highest frequency first']:
            app.selectbox[0].set_value(order).run()
            self.assertFalse(app.exception)
        app.number_input[0].set_value(100).run()
        self.assertIn('No words meet', app.info[-1].value)
        app.number_input[0].set_value(2).run()
        self.assertEqual(len(app.dataframe), 1)
        for top in [5, 15, 20, 10]:
            app.selectbox[1].set_value(top).run()
            self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()
