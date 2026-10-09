import os
import re
import html
from concurrent.futures import ProcessPoolExecutor

from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = 'tf'
SOURCE_FOLDER = 'source'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]
SOURCE_DIR = os.path.join(ROOT_DIR, SOURCE_FOLDER, latest_data_folder)
LATINISE = os.path.join(SOURCE_DIR, 'latinise', 'latin14_vulgata.txt')
INTRATEXT = os.path.join(SOURCE_DIR, 'intratext')

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype book book@en chapter verse source word trailer
''')
api.loadLog()

F, Fs, L = api.F, api.Fs, api.L

CONTENTS_ITEM = re.compile(r"<font size=2>([^<]+)</font>|<a href=(_P\w+\.HTM)>(\d+)</a>")
PARAGRAPH = re.compile(r"(?s)<p\b[^>]*>(.*?)</p>")
TAG = re.compile(r"<[^>]+>")


def plain(fragment):
    return html.unescape(TAG.sub('', fragment)).strip()


def contents():
    with open(os.path.join(INTRATEXT, 'index.htm'), encoding='latin-1') as f:
        text = f.read()
    result = []
    book = ''
    for match in CONTENTS_ITEM.finditer(text):
        if match.group(1):
            book = match.group(1).strip()
        else:
            result.append((book, int(match.group(3)), match.group(2)))
    return result


def page_verses(page):
    with open(os.path.join(INTRATEXT, page), encoding='latin-1') as f:
        text = f.read()
    verses = []
    for paragraph in filter(None, (plain(p) for p in PARAGRAPH.findall(text))):
        if re.fullmatch(r'\d+\s*\.', paragraph):
            continue
        numbered = re.fullmatch(r'(?s)(\d+)\s*(.*)', paragraph)
        if numbered:
            verses.append((int(numbered.group(1)), [numbered.group(2).split()]))
        else:
            verses[-1][1].append(paragraph.split())
    return verses


def latinise_chapters():
    result = {}
    inside = False
    key = None
    with open(LATINISE, encoding='utf-8') as f:
        for line in f:
            if line.startswith('<doc'):
                inside = 'n="LAT0001"' in line
            elif not inside:
                continue
            elif line.startswith('<book title="'):
                book = line.split('"')[1]
            elif line.startswith('<section title="'):
                key = (book, int(line.split('"')[1]))
                result[key] = []
            elif line.startswith('<p'):
                result[key].append([])
            elif line.startswith('<g/>'):
                if result[key][-1]:
                    result[key][-1][-1] = (result[key][-1][-1][0], '')
            elif not line.startswith('<'):
                result[key][-1].append((line.split('\t')[0], ' '))
    return result


OUTSIDE_HEBREW_BIBLE = ('Tobia', 'Iudith', 'Machabaeorum', 'Sapientia', 'Ecclesiasticus', 'Evangelium', 'Actus', 'Epistula', 'Apocalypsis')
CHAPTERS = [item for item in contents() if not item[0].startswith(OUTSIDE_HEBREW_BIBLE)]
TITLES = list(dict.fromkeys(title for title, _, _ in CHAPTERS))
BOOK_OF_TITLE = dict(zip(TITLES, F.otype.s('book')))


def tf_chapter(title, number):
    book = BOOK_OF_TITLE[title]
    found = [c for c in L.d(book, otype='chapter') if F.chapter.v(c) == number]
    return found[0] if found else None


SPLIT_VERSES = {('Iosue', 19): (4, 21)}


def corrected(verses, split):
    if split:
        kept = []
        for position, (_, parts) in enumerate(verses, 1):
            if position in split:
                kept[-1] = kept[-1] + parts
            else:
                kept.append(parts)
        return [(verses[0][0] + i, parts) for i, parts in enumerate(kept)]
    result = []
    for n, parts in verses:
        if result and n < result[-1][0] + 1 and n % 10 == (result[-1][0] + 1) % 10:
            n = result[-1][0] + 1
        result.append((n, parts))
    return result


def expected_verses(verses, paragraphs):
    if len(paragraphs) == sum(len(parts) for _, parts in verses):
        flat = iter(paragraphs)
        return [(n, 'latinise', tuple(w for _ in parts for w in next(flat))) for n, parts in verses]
    return [(n, 'intratext', tuple((w, ' ') for part in parts for w in part)) for n, parts in verses]


def test_every_book_of_the_contents_is_a_book_in_the_same_order():
    assert len(TITLES) == len(F.otype.s('book'))
    assert all(F.book.v(b) and Fs('book@en').v(b) for b in F.otype.s('book'))


def test_every_chapter_page_of_the_contents_is_downloaded():
    assert [page for _, _, page in CHAPTERS if not os.path.isfile(os.path.join(INTRATEXT, page))] == []


def test_every_chapter_of_the_contents_is_a_chapter_of_its_book():
    assert [(t, n) for t, n, _ in CHAPTERS if tf_chapter(t, n) is None] == []


def test_every_latinise_chapter_of_the_hebrew_bible_is_in_the_contents():
    listed = {(t, n) for t, n, _ in CHAPTERS}
    found = [key for key in latinise_chapters() if not key[0].startswith(OUTSIDE_HEBREW_BIBLE)]
    assert [key for key in found if key not in listed] == []


def test_no_book_outside_the_hebrew_bible_is_in_the_data():
    names = {'Tb', 'Jdt', 'Mc1', 'Mc2', 'Sap', 'Sir', 'Matt', 'Rev'}
    assert [F.book.v(b) for b in F.otype.s('book') if F.book.v(b) in names] == []


def test_every_chapter_has_the_verses_and_words_of_its_source():
    latinise = latinise_chapters()
    with ProcessPoolExecutor() as pool:
        pages = list(pool.map(page_verses, [p for _, _, p in CHAPTERS], chunksize=16))
    for (title, number, _), verses in zip(CHAPTERS, pages):
        chapter = tf_chapter(title, number)
        found = [
            (F.verse.v(v), F.source.v(v), tuple((F.word.v(w), F.trailer.v(w)) for w in L.d(v, otype='word')))
            for v in L.d(chapter, otype='verse')
        ]
        verses = corrected(verses, SPLIT_VERSES.get((title, number)))
        assert found == expected_verses(verses, latinise.get((title, number), [])), (title, number)


def test_verse_numbers_run_on_apart_from_the_gaps_of_the_edition():
    gaps = []
    for c in F.otype.s('chapter'):
        numbers = [F.verse.v(v) for v in L.d(c, otype='verse')]
        if any(b <= a for a, b in zip(numbers, numbers[1:])):
            gaps.append((Fs('book@en').v(L.u(c, otype='book')[0]), F.chapter.v(c)))
    assert gaps == []


def test_every_verse_has_a_word():
    assert all(L.d(v, otype='word') for v in F.otype.s('verse'))
