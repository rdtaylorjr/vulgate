import os
import sys
import importlib.util
from concurrent.futures import ThreadPoolExecutor

import pytest
from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = os.path.join(ROOT_DIR, 'programs', 'tfFromLatinISE.py')

spec = importlib.util.spec_from_file_location('tfFromLatinISE', PROGRAM)
converter = importlib.util.module_from_spec(spec)
sys.modules['tfFromLatinISE'] = converter
spec.loader.exec_module(converter)

LATINISE = '''<doc id="LC" n="10" author="uncertain" title="Eclogues">
<p>
Te	PRO	tu
</p>
</doc>
<doc id="IT" n="LAT0001" author="Hieronymus" title="Vulgata">
<book title="Genesis">
<section title="1">
<p>
in	PRE	in
principio	N	principium
</p>
<p>
terra	N	terra
autem	C	autem
<g/>
,	PUN	,
erat	V	sum
</p>
</section>
</book>
</doc>
<doc id="IT" n="LAT0001" author="Hieronymus" title="Vulgata">
<book title="Psalmorum liber">
<section title="22">
<p>
canticum	N	canticum
David	N	David
</p>
</section>
</book>
</doc>
'''

INDEX = '''<ul class=Indice><li><font size=2>Genesis</font><ul><li><font size=1>
<a href=_P1.HTM>1</a>. </font></li></ul></li>
<li><font size=2>Numeri</font><ul><li><font size=1><a href=_P2.HTM>1</a>. <a href=_P3.HTM>2</a>.
</font></li></ul></li>
<li><font size=2>Psalmorum liber</font><ul><li><font size=1><a href=_P4.HTM>22</a>.
</font></li></ul></li></ul>
'''


def page(book, chapter, verses):
    head = f'<h1><A NAME=1>{book}</A></h1>' if book else ''
    body = ''.join(
        (f'<p><A NAME=X HREF=1.HTM>{n}</A> {text} </p>\n' if n == 1 else f'<p><i><A NAME=X HREF=1.HTM>{n}</A></i> {text} </p>\n')
        for n, text in verses
    )
    return (
        '<html><head><TITLE>Vulgata: text - IntraText CT</TITLE></head><body>'
        f'{head}<h2><A NAME=2 HREF=15.HTM>{chapter}</A>.</h2>\n{body}'
        '<p class=MsoNormal>&nbsp;</p></body></html>'
    )


def source(tmp_path):
    folder = tmp_path / 'source'
    (folder / 'latinise').mkdir(parents=True)
    (folder / 'latinise' / 'latin14_vulgata.txt').write_text(LATINISE, encoding='utf-8')
    intratext = folder / 'intratext'
    intratext.mkdir()
    (intratext / 'index.htm').write_text(INDEX, encoding='latin-1')
    pages = {
        '_P1.HTM': page('Genesis', 1, [(1, 'in principio'), (2, 'terra autem erat')]),
        '_P2.HTM': page('Numeri', 1, [(1, '<A NAME=3 HREF=2.HTM>locutusque</A> est'), (2, 'tollite')]),
        '_P3.HTM': page('', 2, [(1, 'locutus est &amp; ait')]),
        '_P4.HTM': page('Psalmorum liber', 22, [(1, 'canticum David')]),
    }
    for name, text in pages.items():
        (intratext / name).write_text(text, encoding='latin-1')
    return folder


def build(tmp_path):
    target = tmp_path / 'tf'
    assert converter.convert(source(tmp_path), target, ThreadPoolExecutor)
    return Fabric(locations=str(target), silent='deep').loadAll(silent='deep')


def test_latinise_verses_read_the_vulgate_documents_only(tmp_path):
    found = converter.latinise_verses(source(tmp_path) / 'latinise' / 'latin14_vulgata.txt')
    assert found == {
        ('Genesis', 1): [
            [('in', ' '), ('principio', ' ')],
            [('terra', ' '), ('autem', ''), (',', ' '), ('erat', ' ')],
        ],
        ('Psalmorum liber', 22): [[('canticum', ' '), ('David', ' ')]],
    }


def test_contents_list_each_chapter_page_with_its_book_in_order(tmp_path):
    found = converter.contents(source(tmp_path) / 'intratext' / 'index.htm')
    assert found == [
        ('Genesis', 1, '_P1.HTM'),
        ('Numeri', 1, '_P2.HTM'),
        ('Numeri', 2, '_P3.HTM'),
        ('Psalmorum liber', 22, '_P4.HTM'),
    ]


def test_intratext_verses_give_each_verse_number_and_words(tmp_path):
    folder = source(tmp_path) / 'intratext'
    assert converter.intratext_verses(folder / '_P2.HTM') == [
        (1, (('locutusque', 'est'),)),
        (2, (('tollite',),)),
    ]
    assert converter.intratext_verses(folder / '_P3.HTM') == [(1, (('locutus', 'est', '&', 'ait'),))]


def test_intratext_verses_read_every_verse_layout_and_skip_headings_and_empty_paragraphs(tmp_path):
    path = tmp_path / 'x.HTM'
    path.write_text(
        '<TITLE>Vulgata: text - IntraText CT</TITLE>'
        '<p class=MsoNormal><a href="x"></a>&nbsp;</p>\n'
        '<p><A NAME=9 HREF=1.HTM>115</A> .</p>\n'
        '<p><A NAME=0 HREF=1.HTM>11</A> igitur </p>\n'
        '<p><i><A NAME=1 HREF=1.HTM>12</A></i> et murmur </p>\n'
        '<p><i></i><A NAME=2 HREF=1.HTM>13</A> nemo tamen </p>\n'
        '<p><i></i><i><A NAME=3 HREF=1.HTM>14</A></i> proximum </p>\n'
        '<p><i><A NAME=4 HREF=1.HTM>15</A> [&hellip;]</i></p>\n'
        '<p><i></i></p>\n'
        "<p class=MsoNormal style='margin:0'><b><i></i></b><i\nstyle='x'><A NAME=5>16</A></i>&nbsp;&nbsp; deinde post </p>\n",
        encoding='latin-1',
    )
    assert converter.intratext_verses(path) == [
        (11, (('igitur',),)),
        (12, (('et', 'murmur'),)),
        (13, (('nemo', 'tamen'),)),
        (14, (('proximum',),)),
        (15, (('[…]',),)),
        (16, (('deinde', 'post'),)),
    ]


def test_intratext_verses_join_an_unnumbered_paragraph_to_the_verse_before(tmp_path):
    path = tmp_path / 'x.HTM'
    path.write_text(
        '<TITLE>Vulgata: text</TITLE>'
        '<p><A NAME=0 HREF=1.HTM>1</A> qui fuit </p>\n'
        '<p>&nbsp;<A NAME=1 HREF=1.HTM>superioribus</A> Galileae </p>\n'
        '<p><i><A NAME=2 HREF=1.HTM>2</A></i> captivitate </p>\n',
        encoding='latin-1',
    )
    assert converter.intratext_verses(path) == [
        (1, (('qui', 'fuit'), ('superioribus', 'Galileae'))),
        (2, (('captivitate',),)),
    ]


def test_intratext_verses_reject_text_before_the_first_verse(tmp_path):
    path = tmp_path / 'x.HTM'
    path.write_text('<TITLE>Vulgata: text</TITLE><p><i>incipit</i> liber </p>', encoding='latin-1')
    with pytest.raises(ValueError, match='incipit'):
        converter.intratext_verses(path)


def test_intratext_verses_reject_a_page_that_is_not_a_chapter(tmp_path):
    path = tmp_path / 'x.HTM'
    path.write_text('<html><title>IntraText Digital Library</title></html>', encoding='latin-1')
    with pytest.raises(ValueError, match='x.HTM'):
        converter.intratext_verses(path)


def test_verses_take_latinise_text_with_intratext_numbers_and_intratext_for_missing_books(tmp_path):
    with ThreadPoolExecutor() as pool:
        found = converter.verses(source(tmp_path), pool)
    assert [(v.book, v.chapter, v.verse, v.source, v.words) for v in found] == [
        ('Genesis', 1, 1, 'latinise', (('in', ' '), ('principio', ' '))),
        ('Genesis', 1, 2, 'latinise', (('terra', ' '), ('autem', ''), (',', ' '), ('erat', ' '))),
        ('Numeri', 1, 1, 'intratext', (('locutusque', ' '), ('est', ' '))),
        ('Numeri', 1, 2, 'intratext', (('tollite', ' '),)),
        ('Numeri', 2, 1, 'intratext', (('locutus', ' '), ('est', ' '), ('&', ' '), ('ait', ' '))),
        ('Psalmi', 22, 1, 'latinise', (('canticum', ' '), ('David', ' '))),
    ]
    assert found[-1].book_en == 'Psalms'


def test_verses_group_latinise_paragraphs_into_the_verses_of_intratext(tmp_path):
    folder = source(tmp_path)
    (folder / 'intratext' / '_P1.HTM').write_text(
        page('Genesis', 1, [(7, 'in principio</p>\n<p>&nbsp;terra autem erat')]), encoding='latin-1'
    )
    with ThreadPoolExecutor() as pool:
        found = converter.verses(folder, pool)
    assert [(v.verse, v.source, v.words) for v in found if v.book == 'Genesis'] == [
        (7, 'latinise', (('in', ' '), ('principio', ' '), ('terra', ' '), ('autem', ''), (',', ' '), ('erat', ' '))),
    ]


def test_verses_take_intratext_where_the_paragraph_counts_differ(tmp_path):
    folder = source(tmp_path)
    (folder / 'intratext' / '_P1.HTM').write_text(page('Genesis', 1, [(1, 'in principio terra')]), encoding='latin-1')
    with ThreadPoolExecutor() as pool:
        found = converter.verses(folder, pool)
    assert [(v.verse, v.source, v.words) for v in found if v.book == 'Genesis'] == [
        (1, 'intratext', (('in', ' '), ('principio', ' '), ('terra', ' '))),
    ]


def test_numbers_correct_a_misprinted_tens_digit_only():
    assert converter.numbers([28, 29, *range(10, 20), 40]) == list(range(28, 41))
    assert converter.numbers([29, *range(10, 16), 36, 17, 38]) == list(range(29, 39))
    assert converter.numbers([31, 12]) == [31, 32]
    assert converter.numbers([67, 69, 70]) == [67, 69, 70]
    assert converter.numbers([22, 23, 22, 23]) == [22, 23, 22, 23]
    assert converter.numbers([10, 11]) == [10, 11]


def test_verses_number_a_misprinted_verse_by_the_corrected_count(tmp_path):
    folder = source(tmp_path)
    (folder / 'intratext' / '_P2.HTM').write_text(
        page('Numeri', 1, [(29, 'locutusque est'), (10, 'tollite')]), encoding='latin-1'
    )
    with ThreadPoolExecutor() as pool:
        found = converter.verses(folder, pool)
    assert [(v.chapter, v.verse) for v in found if v.book == 'Numeri'] == [(1, 29), (1, 30), (2, 1)]


def test_verses_join_the_split_verses_of_the_corrections_and_number_the_chapter_in_order(tmp_path):
    folder = source(tmp_path)
    (folder / 'intratext' / '_P2.HTM').write_text(
        page('Numeri', 1, [(1, 'locutusque'), (2, 'est'), (3, 'tollite')]), encoding='latin-1'
    )
    with ThreadPoolExecutor() as pool:
        found = converter.verses(folder, pool, {('Numeri', 1): (2,)})
    assert [(v.chapter, v.verse, v.words) for v in found if v.book == 'Numeri'][:2] == [
        (1, 1, (('locutusque', ' '), ('est', ' '))),
        (1, 2, (('tollite', ' '),)),
    ]


def test_verses_leave_out_the_books_outside_the_hebrew_bible(tmp_path):
    folder = source(tmp_path)
    index = folder / 'intratext' / 'index.htm'
    index.write_text(index.read_text(encoding='latin-1').replace('Numeri', 'Tobia'), encoding='latin-1')
    with ThreadPoolExecutor() as pool:
        found = converter.verses(folder, pool)
    assert [v.book for v in found] == ['Genesis', 'Genesis', 'Psalmi']


def test_verses_reject_a_book_without_a_name(tmp_path):
    folder = source(tmp_path)
    index = folder / 'intratext' / 'index.htm'
    index.write_text(index.read_text(encoding='latin-1').replace('Numeri', 'Liber ignotus'), encoding='latin-1')
    with ThreadPoolExecutor() as pool, pytest.raises(KeyError, match='Liber ignotus'):
        converter.verses(folder, pool)


def test_convert_builds_book_chapter_verse_and_word_nodes(tmp_path):
    api = build(tmp_path)
    F, L, T, Fs = api.F, api.L, api.T, api.Fs
    assert [F.book.v(n) for n in F.otype.s('book')] == ['Genesis', 'Numeri', 'Psalmi']
    assert [Fs('book@en').v(n) for n in F.otype.s('book')] == ['Genesis', 'Numbers', 'Psalms']
    verse = T.nodeFromSection(('Genesis', 1, 2))
    assert T.text(verse) == 'terra autem, erat '
    assert F.source.v(verse) == 'latinise'
    assert F.source.v(T.nodeFromSection(('Numbers', 2, 1))) == 'intratext'
    psalm = T.nodeFromSection(('Psalms', 22, 1))
    assert [F.word.v(w) for w in L.d(psalm, 'word')] == ['canticum', 'David']
    assert T.sectionFromNode(psalm) == ('Psalms', 22, 1)


def test_convert_writes_the_attribution_and_license_into_the_metadata(tmp_path):
    build(tmp_path)
    otext = (tmp_path / 'tf' / 'otext.tf').read_text(encoding='utf-8')
    assert '@licenseUrl=https://creativecommons.org/licenses/by-nc-sa/4.0/' in otext
    assert 'The IntraText Digital Library - www.intratext.com' in otext
    assert '@language=lat' in otext


def test_convert_removes_features_of_an_earlier_conversion(tmp_path):
    target = tmp_path / 'tf'
    target.mkdir()
    (target / 'old.tf').write_text('@node\n', encoding='utf-8')
    assert converter.convert(source(tmp_path), target, ThreadPoolExecutor)
    assert not (target / 'old.tf').exists()


def test_main_reports_success_and_failure(tmp_path):
    folder = source(tmp_path)
    assert converter.main(['--source', str(folder), '--target', str(tmp_path / 'a')], ThreadPoolExecutor) == 0
    empty = tmp_path / 'empty'
    (empty / 'latinise').mkdir(parents=True)
    (empty / 'latinise' / 'latin14_vulgata.txt').write_text('', encoding='utf-8')
    (empty / 'intratext').mkdir()
    (empty / 'intratext' / 'index.htm').write_text('', encoding='latin-1')
    assert converter.main(['--source', str(empty), '--target', str(tmp_path / 'b')], ThreadPoolExecutor) == 1
