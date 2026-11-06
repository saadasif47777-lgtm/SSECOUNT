"""Run the same web dashboard/API locally: python dev.py."""
import os
from flask import send_from_directory
from api.index import app


def home():
    return send_from_directory('public', 'index.html')


def asset(name):
    return send_from_directory('public', name)


app.static_folder = None
app.root_path = os.path.dirname(__file__)
app.add_url_rule('/', view_func=home)
app.add_url_rule('/<path:name>', view_func=asset)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8502, debug=False)
