"""Extract readable text before passing it to the simple word counter.

PDF and RTF libraries understand their file formats. Modern Office and
OpenDocument files are ZIP containers of XML; we read their text elements.
No uploaded macros, scripts, formulas or embedded programs are executed.
"""
import io
import os
import zipfile
from defusedxml import ElementTree
from pypdf import PdfReader
from striprtf.striprtf import rtf_to_text
from bs4 import BeautifulSoup
import xlrd

MAX_FILE_SIZE = 3 * 1024 * 1024
MAX_TEXT_CHARACTERS = 100000
MAX_ARCHIVE_SIZE = 20 * 1024 * 1024
MAX_ARCHIVE_FILES = 2000


def check_text_length(text):
    """Bound extracted text so reports and API responses fit serverless limits."""
    if len(text) > MAX_TEXT_CHARACTERS:
        raise ValueError('This document contains too much text. Choose a document with at most 100,000 extracted characters.')
    return text


def decode_text(file_bytes):
    """Accept UTF-8 and BOM-marked UTF-16/32 without guessing a legacy encoding."""
    encoding = 'utf-8-sig'
    if file_bytes.startswith((b'\xff\xfe\x00\x00', b'\x00\x00\xfe\xff')):
        encoding = 'utf-32'
    elif file_bytes.startswith((b'\xff\xfe', b'\xfe\xff')):
        encoding = 'utf-16'
    try:
        text = file_bytes.decode(encoding)
    except UnicodeError:
        raise ValueError('This file is not readable Unicode text. Save text as UTF-8 or upload a supported document format.')
    for character in text:
        if ord(character) < 32 and character not in '\t\n\r\f':
            raise ValueError('This file contains binary data rather than readable text.')
    return text


def read_archive(file_bytes):
    """Check a document container before reading any expanded XML."""
    archive = zipfile.ZipFile(io.BytesIO(file_bytes))
    total_size = 0
    entries = archive.infolist()
    if len(entries) > MAX_ARCHIVE_FILES:
        archive.close()
        raise ValueError('This document contains too many internal files.')
    for entry in entries:
        total_size += entry.file_size
        if entry.flag_bits & 1:
            archive.close()
            raise ValueError('Password-protected documents are not supported. Upload an unlocked copy.')
    if total_size > MAX_ARCHIVE_SIZE:
        archive.close()
        raise ValueError('This document expands beyond the supported size. Choose a smaller document.')
    return archive


def local_name(element):
    """Remove an XML namespace, leaving a simple name such as p, t or v."""
    return element.tag.split('}')[-1]


def paragraph_text(xml_bytes):
    """Read paragraph text from Word, PowerPoint or OpenDocument XML."""
    root = ElementTree.fromstring(xml_bytes)
    paragraphs = []
    for element in root.iter():
        name = local_name(element)
        if name in ['p', 'h']:
            pieces = []
            # Joining runs without extra spaces preserves words split by styling.
            for child in element.iter():
                child_name = local_name(child)
                if child_name in ['t', 'tab', 'br']:
                    if child_name == 't':
                        pieces.append(child.text or '')
                    else:
                        pieces.append(' ')
            if pieces:
                paragraphs.append(''.join(pieces))
            else:
                # OpenDocument paragraphs store text directly, including spans.
                paragraphs.append(''.join(element.itertext()))
    return '\n'.join(paragraphs)


def slide_number(name):
    """Keep slide2 before slide10 instead of sorting slide names as words."""
    number = os.path.basename(name).replace('slide', '').replace('.xml', '')
    return int(number)


def extract_office(file_bytes, extension):
    """Read modern Word, PowerPoint, Excel and OpenDocument containers."""
    with read_archive(file_bytes) as archive:
        names = archive.namelist()
        parts = []
        if extension == '.docx':
            if 'word/document.xml' not in names:
                raise ValueError('This is not a valid Word document.')
            parts.append(paragraph_text(archive.read('word/document.xml')))
            for name in sorted(names):
                if name.startswith(('word/header', 'word/footer', 'word/footnotes', 'word/endnotes')) and name.endswith('.xml'):
                    parts.append(paragraph_text(archive.read(name)))
        elif extension == '.pptx':
            slides = []
            for name in names:
                if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                    number = os.path.basename(name)[5:-4]
                    if number.isdigit():
                        slides.append(name)
            if not slides:
                raise ValueError('This presentation contains no readable slides.')
            for name in sorted(slides, key=slide_number):
                parts.append(paragraph_text(archive.read(name)))
        elif extension == '.xlsx':
            parts.append(extract_spreadsheet(archive))
        else:
            if 'content.xml' not in names:
                raise ValueError('This is not a valid OpenDocument file.')
            parts.append(paragraph_text(archive.read('content.xml')))
        return '\n'.join(parts)


def extract_spreadsheet(archive):
    """Read text cells and cached numeric values; never evaluate formulas."""
    shared_strings = []
    names = archive.namelist()
    if 'xl/workbook.xml' not in names:
        raise ValueError('This is not a valid Excel workbook.')
    if 'xl/sharedStrings.xml' in names:
        root = ElementTree.fromstring(archive.read('xl/sharedStrings.xml'))
        for item in root:
            shared_strings.append(''.join(item.itertext()))
    values = []
    for name in sorted(names):
        if not name.startswith('xl/worksheets/sheet') or not name.endswith('.xml'):
            continue
        root = ElementTree.fromstring(archive.read(name))
        for cell in root.iter():
            if local_name(cell) != 'c':
                continue
            cell_type = cell.get('t', '')
            for child in cell:
                if local_name(child) == 'v' and child.text:
                    if cell_type == 's':
                        values.append(shared_strings[int(child.text)])
                    else:
                        values.append(child.text)
                elif local_name(child) == 'is':
                    values.append(''.join(child.itertext()))
    return '\n'.join(values)


def extract_pdf(file_bytes):
    """Extract a PDF text layer. Image-only pages require OCR elsewhere."""
    reader = PdfReader(io.BytesIO(file_bytes))
    if reader.is_encrypted:
        raise ValueError('Password-protected PDFs are not supported. Upload an unlocked copy.')
    if len(reader.pages) > 200:
        raise ValueError('Please choose a PDF with no more than 200 pages.')
    pages = []
    total_characters = 0
    for page in reader.pages:
        text = page.extract_text() or ''
        total_characters += len(text)
        if total_characters > MAX_TEXT_CHARACTERS:
            raise ValueError('This PDF contains too much text. Choose a smaller document.')
        pages.append(text)
    text = '\n'.join(pages)
    if not text.strip():
        raise ValueError('No selectable text found in this PDF. Scanned pages and images need OCR first.')
    return text


def extract_legacy_excel(file_bytes):
    """Read visible cell values from the older .xls workbook format."""
    workbook = xlrd.open_workbook(file_contents=file_bytes, on_demand=True)
    values = []
    try:
        for sheet in workbook.sheets():
            for row in range(sheet.nrows):
                for value in sheet.row_values(row):
                    if value != '':
                        # Excel stores whole-number cells as floats internally.
                        if isinstance(value, float) and value == int(value):
                            value = int(value)
                        values.append(str(value))
    finally:
        workbook.release_resources()
    return '\n'.join(values)


def extract_text(file_name, file_bytes):
    """Select a reader by format, and use Unicode decoding for other text files."""
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError('Choose a file of 3 MB or less.')
    if not file_bytes:
        return ''
    extension = os.path.splitext(file_name)[1].lower()
    if extension in ['.doc', '.ppt', '.docm', '.pptm', '.xlsm']:
        raise ValueError('Please save this document as .docx, .pptx, .xlsx or PDF before uploading. Legacy Word/PowerPoint and macro-enabled files are not supported.')
    try:
        if extension == '.pdf':
            text = extract_pdf(file_bytes)
        elif extension in ['.docx', '.pptx', '.xlsx', '.odt', '.odp', '.ods']:
            text = extract_office(file_bytes, extension)
        elif extension == '.xls':
            text = extract_legacy_excel(file_bytes)
        elif extension == '.rtf':
            text = rtf_to_text(file_bytes.decode('latin-1'), errors='strict')
        elif extension in ['.html', '.htm']:
            soup = BeautifulSoup(decode_text(file_bytes), 'html.parser')
            for element in soup(['script', 'style', 'template']):
                element.decompose()
            text = soup.get_text(separator=' ')
        else:
            # CSV, Markdown, JSON, XML, logs, code and unknown text extensions
            # use their readable source text. Arbitrary binary files are rejected.
            text = decode_text(file_bytes)
    except ValueError:
        raise
    except Exception:
        # Document parsers have different exception types; keep traces out of UI.
        raise ValueError('This document could not be read. It may be damaged, encrypted, or saved in a different format. Try exporting it as PDF or plain text.')
    return check_text_length(text)
