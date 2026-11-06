"""Small in-memory documents test format readers without uploading private files."""
import io
import zipfile
import unittest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from backend.extractors import extract_text, MAX_FILE_SIZE
from analyzer import analyze_text, make_report


def container(parts):
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, text in parts.items():
            archive.writestr(name, text)
    return result.getvalue()


def pdf_document(text=None, encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    if text:
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(('BT /F1 12 Tf 20 250 Td (' + text + ') Tj ET').encode())
        page[NameObject('/Contents')] = writer._add_object(stream)
    if encrypted:
        writer.encrypt('password')
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class ExtractionTests(unittest.TestCase):
    def test_unicode_and_other_text_extensions(self):
        for name in ['data.csv', 'data.tsv', 'notes.md', 'log.log', 'source.py', 'unknown.xyz', 'noextension']:
            with self.subTest(name=name):
                self.assertEqual(extract_text(name, b'Hello 42'), 'Hello 42')
        self.assertEqual(extract_text('data.json', b'{"count": 42}'), '{"count": 42}')
        self.assertEqual(extract_text('utf16.txt', 'سلام 42'.encode('utf-16')), 'سلام 42')
        self.assertEqual(extract_text('utf32.txt', 'Hello'.encode('utf-32')), 'Hello')
        self.assertEqual(extract_text('empty.txt', b''), '')

    def test_word_paragraphs_tables_and_headers(self):
        data = container({
            'word/document.xml': '<document><p><r><t>Hel</t></r><r><t>lo 42</t></r></p><table><p><t>Table</t></p></table></document>',
            'word/header1.xml': '<header><p><t>Heading</t></p></header>',
        })
        self.assertEqual(extract_text('sample.DOCX', data), 'Hello 42\nTable\nHeading')

    def test_powerpoint_slide_order(self):
        data = container({
            'ppt/slides/slide10.xml': '<slide><p><t>Last</t></p></slide>',
            'ppt/slides/slide2.xml': '<slide><p><t>First 42</t></p></slide>',
        })
        self.assertEqual(extract_text('slides.pptx', data), 'First 42\nLast')

    def test_excel_shared_inline_and_numeric_cells(self):
        data = container({
            'xl/workbook.xml': '<workbook/>',
            'xl/sharedStrings.xml': '<sst><si><t>Hello</t></si></sst>',
            'xl/worksheets/sheet1.xml': '<worksheet><row><c t="s"><v>0</v></c><c t="inlineStr"><is><t>World</t></is></c><c><v>42</v></c></row></worksheet>',
        })
        self.assertEqual(extract_text('data.xlsx', data), 'Hello\nWorld\n42')

    def test_opendocument_formats(self):
        data = container({'content.xml': '<document><h>Heading</h><p>Hello <span>world</span> 42</p></document>'})
        for extension in ['odt', 'odp', 'ods']:
            self.assertEqual(extract_text('file.' + extension, data), 'Heading\nHello world 42')

    def test_pdf_text_scans_and_encryption(self):
        self.assertIn('Hello 42', extract_text('file.pdf', pdf_document('Hello 42')))
        with self.assertRaisesRegex(ValueError, 'OCR'):
            extract_text('scan.pdf', pdf_document())
        with self.assertRaisesRegex(ValueError, 'Password'):
            extract_text('locked.pdf', pdf_document('secret', encrypted=True))

    def test_rtf_and_html(self):
        self.assertIn('Hello 42', extract_text('file.rtf', br'{\rtf1\ansi Hello 42\par World}'))
        text = extract_text('page.html', b'<h1>Hello 42</h1><script>hidden</script><style>hidden</style><p>World</p>')
        self.assertIn('Hello 42', text)
        self.assertNotIn('hidden', text)

    def test_invalid_binary_legacy_and_limits(self):
        for name, data in [('bad.docx', b'invalid'), ('bad.pdf', b'invalid'), ('bad.png', b'\x89PNG\x00'), ('bad.txt', b'\xff'), ('old.doc', b'legacy'), ('old.ppt', b'legacy'), ('macro.docm', b'legacy')]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    extract_text(name, data)
        with self.assertRaisesRegex(ValueError, '3 MB'):
            extract_text('large.txt', b'a' * (MAX_FILE_SIZE + 1))
        with self.assertRaisesRegex(ValueError, 'too much text'):
            extract_text('large.txt', b'a' * 100001)
        bomb = container({'word/document.xml': ' ' * (20 * 1024 * 1024 + 1)})
        with self.assertRaisesRegex(ValueError, 'expands'):
            extract_text('bomb.docx', bomb)
        entity = container({'word/document.xml': '<!DOCTYPE x [<!ENTITY a "secret">]><p>&a;</p>'})
        with self.assertRaises(ValueError):
            extract_text('entity.docx', entity)

    def test_additional_statistics_and_report(self):
        result = analyze_text('Hello 42 42 12.5\n\nNext 7')
        self.assertEqual(result['extra_statistics'], {'numeric_tokens': 5, 'unique_numbers': 4, 'digits': 8, 'nonempty_lines': 2, 'paragraphs': 2})
        report = make_report('file.docx', result)
        self.assertIn('Numeric tokens: 5', report)
        self.assertIn('Paragraphs: 2', report)

    def test_legacy_excel_fixture(self):
        from pathlib import Path
        data = Path(__file__).with_name('fixtures').joinpath('example.xls').read_bytes()
        self.assertEqual(extract_text('example.xls', data), 'Hello\n42')
