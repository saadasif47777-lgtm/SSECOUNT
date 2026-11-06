"""SSECOUNT's Streamlit interface. Analysis lives in analyzer.py."""
import streamlit as st
from analyzer import analyze_text, read_text_file, sort_frequencies, search_word, make_report

from backend.sample import SAMPLE_TEXT
from backend.extractors import extract_text


st.set_page_config(page_title='SSECOUNT · Text Analysis Studio', page_icon='◈', layout='wide')
st.markdown('''<style>
.stApp {background:#F7F9FC;}
.block-container {max-width:1400px;padding-top:2.5rem;padding-bottom:2rem;}
[data-testid="stSidebar"] {background:#101C32;}
[data-testid="stSidebar"] * {color:#F7F9FC;}
[data-testid="stSidebar"] .stCaption {color:#b8cad9;}
h1,h2,h3 {color:#101C32;letter-spacing:-.035em;}
h1 {font-size:2.6rem!important;}
[data-testid="stMetric"] {background:white;border:1px solid #e1e8ef;border-radius:14px;padding:20px;box-shadow:0 4px 18px #101c3205;}
[data-testid="stMetricValue"] {color:#101C32;font-size:1.9rem;}
[data-testid="stFileUploader"] {background:white;border:1px solid #dce6ed;border-radius:14px;padding:12px;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
.brand {font-size:26px;font-weight:800;letter-spacing:2px;}
.brand span {color:#20B8A9!important;}
.eyebrow {color:#168679;font-size:12px;font-weight:700;letter-spacing:2px;}
.hero {background:#101C32;padding:24px 28px;border-radius:16px;color:#cad7e3;margin:12px 0 26px;}
.hero strong {color:white;font-size:19px;display:block;margin-bottom:6px;}
.footer {border-top:1px solid #dce6ed;margin-top:32px;padding-top:18px;color:#65758b;font-size:12px;}
</style>''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">SSE<span>COUNT</span></div>', unsafe_allow_html=True)
    st.caption('TEXT ANALYSIS STUDIO')
    st.divider()
    st.markdown('### Your workspace')
    source = st.radio('Text source', ['Upload a file', 'Explore sample'], label_visibility='collapsed')
    st.divider()
    st.markdown('### A little clarity,\none word at a time.')
    st.caption('Upload → Explore → Export\n\nAnalyze a document containing text or start with our sample. Your file is processed in this session and is not written to disk by the app.')
    st.caption('01 / DOCUMENT INTELLIGENCE')

st.markdown('<div class="eyebrow">YOUR WORDS. A CLEARER PICTURE.</div>', unsafe_allow_html=True)
st.title('Text analysis, made simple.')
st.write('Discover the patterns in your writing with instant word counts, frequency insights, and a report you can take with you.')
st.markdown('<div class="hero"><strong>Every word has a story.</strong>Bring your document. We’ll help you see what stands out.</div>', unsafe_allow_html=True)

text = None
file_name = ''
if source == 'Upload a file':
    st.subheader('01  Add your document')
    uploaded = st.file_uploader('Choose a text file', type=None, help='Word, PowerPoint, PDF, Excel, OpenDocument, RTF and Unicode text. Up to 3 MB.')
    if uploaded is None:
        st.info('Your workspace is ready. Upload a document or choose “Explore sample” in the sidebar.')
    else:
        try:
            file_name = uploaded.name
            text = extract_text(file_name, uploaded.getvalue())
            st.success('Uploaded successfully: ' + file_name)
        except (ValueError, OSError) as error:
            st.error(str(error))
else:
    text = SAMPLE_TEXT
    file_name = 'SSECOUNT-sample.txt'
    st.success('Sample document loaded. Explore the dashboard below.')

if text is not None:
    analysis = analyze_text(text)
    if not text:
        st.warning('This file is empty. Upload a file containing some text.')
    elif not analysis['words']:
        st.warning('No valid words found. The document contains only whitespace or punctuation.')
    else:
        st.subheader('02  Document overview')
        st.caption(file_name + ' · All statistics describe the complete document.')
        columns = st.columns(4)
        columns[0].metric('Total words', format(analysis['total_words'], ','))
        columns[1].metric('Unique words', format(analysis['unique_words'], ','))
        columns[2].metric('Characters', format(analysis['characters'], ','))
        columns[3].metric('Average word length', format(analysis['average_length'], '.2f'))
        extra = analysis['extra_statistics']
        more_columns = st.columns(4)
        more_columns[0].metric('Numeric tokens', extra['numeric_tokens'])
        more_columns[1].metric('Unique numbers', extra['unique_numbers'])
        more_columns[2].metric('Digit characters', extra['digits'])
        more_columns[3].metric('Nonempty lines', extra['nonempty_lines'])
        left, right = st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown('**Most frequent · ' + str(analysis['highest']) + ' occurrences each**')
                st.write(', '.join(analysis['most_words']))
        with right:
            with st.container(border=True):
                st.markdown('**Least frequent · ' + str(analysis['lowest']) + ' occurrences each**')
                st.write(', '.join(analysis['least_words']))
        with st.expander('Read the extracted text & counting rules'):
            st.text(text)
            st.caption('Text is lowercased. Punctuation, apostrophes, hyphens, symbols, and whitespace separate words. Unicode letters and numbers remain. Characters include original spaces and punctuation. All frequency ties appear alphabetically. No stopwords are removed.')

        st.subheader('03  Explore your words')
        query = st.text_input('Find a word', placeholder='Search a word in the complete document…')
        if query:
            try:
                word, count, percent = search_word(query, analysis)
                if count:
                    st.success(word + ' appears ' + str(count) + ' time(s) · ' + format(percent, '.2f') + '% of all words.')
                else:
                    st.info('“' + word + '” does not appear in this document.')
            except ValueError as error:
                st.warning(str(error))
        controls = st.columns(2)
        order = controls[0].selectbox('Sort results', ['Highest frequency first', 'Lowest frequency first', 'Alphabetical (A–Z)', 'Reverse alphabetical (Z–A)'])
        minimum = controls[1].number_input('Minimum occurrences', min_value=1, value=1, step=1)
        rows = sort_frequencies(analysis['frequencies'], order, minimum)
        table, chart = st.columns([1, 1], gap='large')
        with table:
            st.markdown('#### Word frequency')
            st.caption(str(len(rows)) + ' of ' + str(analysis['unique_words']) + ' unique words · filters apply to this table')
            if rows:
                words = []
                counts = []
                shares = []
                for word, count in rows:
                    words.append(word)
                    counts.append(count)
                    shares.append(round(count / analysis['total_words'] * 100, 2))
                st.dataframe({'Word': words, 'Occurrences': counts, 'Share (%)': shares}, hide_index=True, width='stretch', height=390)
            else:
                st.info('No words meet this minimum. Lower the filter to see results.')
        with chart:
            st.markdown('#### Words that stand out')
            top_count = st.selectbox('Show top words', [5, 10, 15, 20], index=1)
            top_rows = sort_frequencies(analysis['frequencies'])[:top_count]
            # Inline Vega-Lite data avoids importing pandas or NumPy.
            chart_rows = []
            chart_order = []
            for word, count in top_rows:
                chart_rows.append({'Word': word, 'Occurrences': count})
                chart_order.append(word)
            st.vega_lite_chart({'data': {'values': chart_rows}, 'height': 310,
                'layer': [
                    {'mark': {'type': 'bar', 'color': '#20B8A9', 'cornerRadiusEnd': 4}},
                    {'mark': {'type': 'text', 'align': 'left', 'dx': 5, 'color': '#263449'}, 'encoding': {'text': {'field': 'Occurrences', 'type': 'quantitative'}}}
                ],
                'encoding': {
                    'y': {'field': 'Word', 'type': 'nominal', 'sort': chart_order, 'axis': {'title': None}},
                    'x': {'field': 'Occurrences', 'type': 'quantitative', 'scale': {'domain': [0, analysis['highest'] * 1.2]}, 'axis': {'tickMinStep': 1}},
                    'tooltip': [{'field': 'Word'}, {'field': 'Occurrences'}]
                }}, width='stretch')
            st.caption('Top words across the complete document, independent of table filters. Choose 5 for a quick top-five view.')
        st.subheader('04  Take your insights with you')
        st.write('A complete text report with document statistics, all tied words, and every word frequency.')
        st.download_button('↓ Download analysis report', make_report(file_name, analysis), file_name='SSECOUNT-report.txt', mime='text/plain', type='primary')

st.markdown('<div class="footer">SSECOUNT · Text Analysis Studio &nbsp; / &nbsp; Made for curious minds.</div>', unsafe_allow_html=True)
