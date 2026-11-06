"""Connect Vercel's HTTP requests to the readable Python backend.

This file handles communication and input errors. It does not contain frontend
HTML, CSS or JavaScript. See analyzer.py for the main word-counting algorithm.
"""
import json
from flask import Flask, jsonify, request
from analyzer import analyze_text, make_report, read_text_file
from backend.extractors import extract_text, check_text_length, MAX_FILE_SIZE
from backend.dashboard import prepare_dashboard
from backend.sample import SAMPLE_TEXT

app = Flask(__name__)
# Allow some room for upload metadata while staying below serverless limits.
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024


def read_document():
    """Read either an uploaded file or JSON text, along with display options."""
    if 'file' in request.files:
        uploaded_file = request.files['file']
        file_name = uploaded_file.filename or ''
        file_bytes = uploaded_file.read(MAX_FILE_SIZE + 1)
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValueError('Choose a file of 3 MB or less.')
        # All extension checking and UTF-8 decoding happen in Python.
        text = extract_text(file_name, file_bytes)
        try:
            options = json.loads(request.form.get('options', '{}'))
        except ValueError:
            raise ValueError('The dashboard options are not valid JSON.')
    else:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('Send a JSON object containing text and a filename.')
        if data.get('sample') is True:
            file_name = 'SSECOUNT-sample.txt'
            text = SAMPLE_TEXT
        else:
            file_name = data.get('file_name', 'sample.txt')
            text = data.get('text')
            if not isinstance(text, str) or not isinstance(file_name, str):
                raise ValueError('The text and filename must be strings.')
            if len(text.encode('utf-8')) > MAX_FILE_SIZE:
                raise ValueError('Choose a file of 3 MB or less.')
            text = check_text_length(read_text_file(file_name, text.encode('utf-8')))
        options = data.get('options', {})
    if not isinstance(options, dict):
        raise ValueError('Dashboard options must be a JSON object.')
    return file_name, text, options


def analyze_request():
    """Analyze the document and return Python-prepared data as JSON."""
    try:
        file_name, text, options = read_document()
        if not text:
            raise ValueError('This file is empty. Choose a file containing text.')
        analysis = analyze_text(text)
        if not analysis['words']:
            raise ValueError('No valid words found. Try text containing letters or numbers.')

        # Each request is independent. No document or account is stored on disk.
        dashboard = prepare_dashboard(analysis, options)
        analysis['report'] = make_report(file_name, analysis)
        analysis['dashboard'] = dashboard
        analysis['file_name'] = file_name
        analysis['original_text'] = text
        del analysis['words']  # The browser does not need a duplicate token list.
        return jsonify(analysis)
    except ValueError as error:
        status = 400
        if '3 MB' in str(error) or 'too much text' in str(error):
            status = 413
        return jsonify(error=str(error)), status


def oversized_request(error):
    """Return JSON even when Flask rejects a very large incoming request."""
    return jsonify(error='The request is too large. Choose a file of 3 MB or less.'), 413


# Named functions are registered explicitly; no decorators or classes are used.
app.add_url_rule('/api/analyze', view_func=analyze_request, methods=['POST'])
app.register_error_handler(413, oversized_request)
