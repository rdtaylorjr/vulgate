"""Converts the Hebrew Bible of the Vulgate of LatinISE, completed from the IntraText Digital Library, to Text-Fabric."""

from __future__ import annotations

import argparse
import html
import re
from concurrent.futures import Executor, ProcessPoolExecutor
from itertools import groupby
from operator import attrgetter
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any, NamedTuple

from tf.convert.walker import CV
from tf.fabric import Fabric

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

ORG = "rdtaylorjr"
REPO = "vulgate"
VERSION = "0.1"

BASE = Path("~/github").expanduser()
REPO_DIR = BASE / ORG / REPO
SOURCE_DIR = REPO_DIR / "source" / VERSION
TF_DIR = REPO_DIR / "tf" / VERSION
LATINISE = Path("latinise") / "latin14_vulgata.txt"
INTRATEXT = Path("intratext")
CONTENTS = "index.htm"
CHUNK = 16

VULGATE_DOC = 'n="LAT0001"'
GLUE = "<g/>"
CHAPTER_PAGE = "Vulgata: text"
SPACE = " "
NO_SPACE = ""

BOOKS = {
    "Genesis": ("Genesis", "Genesis"),
    "Exodus": ("Exodus", "Exodus"),
    "Leviticus": ("Leviticus", "Leviticus"),
    "Numeri": ("Numeri", "Numbers"),
    "Deuteronomium": ("Deuteronomium", "Deuteronomy"),
    "Iosue": ("Josua", "Joshua"),
    "Iudices": ("Judices", "Judges"),
    "Ruth": ("Ruth", "Ruth"),
    "Samuelis liber I": ("Samuel_I", "1_Samuel"),
    "Samuelis liber II": ("Samuel_II", "2_Samuel"),
    "Regum liber I": ("Reges_I", "1_Kings"),
    "Regum liber II": ("Reges_II", "2_Kings"),
    "Paralipomenon liber I": ("Chronica_I", "1_Chronicles"),
    "Paralipomenon liber II": ("Chronica_II", "2_Chronicles"),
    "Esdrae": ("Esra", "Ezra"),
    "Nehemias": ("Nehemia", "Nehemiah"),
    "Esther": ("Esther", "Esther"),
    "Iob": ("Iob", "Job"),
    "Psalmorum liber": ("Psalmi", "Psalms"),
    "Proverbia": ("Proverbia", "Proverbs"),
    "Ecclesiastes": ("Ecclesiastes", "Ecclesiastes"),
    "Canticum canticorum": ("Canticum", "Song_of_songs"),
    "Isaias": ("Jesaia", "Isaiah"),
    "Ieremias": ("Jeremia", "Jeremiah"),
    "Lamentationes": ("Threni", "Lamentations"),
    "Ezechiel": ("Ezechiel", "Ezekiel"),
    "Daniel": ("Daniel", "Daniel"),
    "Osee": ("Hosea", "Hosea"),
    "Ioel": ("Joel", "Joel"),
    "Amos": ("Amos", "Amos"),
    "Abdias": ("Obadia", "Obadiah"),
    "Ionas": ("Jona", "Jonah"),
    "Michaea": ("Micha", "Micah"),
    "Nahum": ("Nahum", "Nahum"),
    "Habacuc": ("Habakuk", "Habakkuk"),
    "Sophonias": ("Zephania", "Zephaniah"),
    "Aggaeus": ("Haggai", "Haggai"),
    "Zacharias": ("Sacharia", "Zechariah"),
    "Malachias": ("Maleachi", "Malachi"),
}

LEFT_OUT = frozenset(
    {
        "Tobia",
        "Iudith",
        "Machabaeorum liber I",
        "Machabaeorum liber II",
        "Sapientia",
        "Ecclesiasticus",
        "Evangelium secundum Matthaeum",
        "Evangelium secundum Marcum",
        "Evangelium secundum Lucam",
        "Evangelium secundum Ioannem",
        "Actus apostolorum",
        "Epistula beati Pauli apostoli ad Romanos",
        "Epistula beati Pauli apostoli ad Corinthios I",
        "Epistula beati Pauli apostoli ad Corinthios II",
        "Epistula beati Pauli apostoli ad Galatas",
        "Epistula beati Pauli apostoli ad Ephesios",
        "Epistula beati Pauli apostoli ad Philippenses",
        "Epistula beati Pauli apostoli ad Colossenses",
        "Epistula beati Pauli apostoli ad Thessalonicenses I",
        "Epistula beati Pauli apostoli ad Thessalonicenses II",
        "Epistula beati Pauli apostoli ad Timotheum I",
        "Epistula beati Pauli apostoli ad Timotheum II",
        "Epistula beati Pauli apostoli ad Titum",
        "Epistula beati Pauli apostoli ad Philemonem",
        "Epistula beati Pauli apostoli ad Hebraeos",
        "Epistula catholica beati Iacobi apostoli",
        "Epistula beati Petri apostoli I",
        "Epistula beati Petri apostoli II",
        "Epistula beati Ioannis I",
        "Epistula beati Ioannis II",
        "Epistula beati Ioannis III",
        "Epistula catholica beati Iudae apostoli",
        "Apocalypsis beati Ioannis apostoli",
    }
)

# IntraText gives a verse of these chapters as two numbered paragraphs, at these verse positions of the page.
SPLIT_VERSES = {("Iosue", 19): (4, 21)}

BOOK_TITLE = re.compile(r'<book title="([^"]*)"')
SECTION_TITLE = re.compile(r'<section title="([^"]*)"')
CONTENTS_ITEM = re.compile(r"<font size=2>([^<]+)</font>|<a href=(_P\w+\.HTM)>(\d+)</a>")
PARAGRAPH = re.compile(r"(?s)<p\b[^>]*>(.*?)</p>")
NUMBERED = re.compile(r"(?s)(\d+)\s*(.*)")
HEADING = re.compile(r"\d+\s*\.")
TAG = re.compile(r"<[^>]+>")

slotType = "word"

generic = {
    "name": "Vulgate",
    "language": "lat",
    "source": "LatinISE corpus (version 6), completed from the IntraText Digital Library",
    "sourceUrl": "http://hdl.handle.net/11372/LRT-6140",
    "sourceFormat": "LatinISE vertical text and IntraText HTML",
    "compiler": "Barbara McGillivray (LatinISE); EuloTech SRL (IntraText)",
    "converters": "Rusty Taylor",
    "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International",
    "licenseUrl": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "copynote1": "The IntraText Digital Library - www.intratext.com",
    "copynote2": "LatinISE corpus (version 6), Barbara McGillivray, http://hdl.handle.net/11372/LRT-6140",
    "copynote3": (
        "Modified: converted to Text-Fabric, see docs/transcription.md."
        " Provided as is, without warranties, see the disclaimer in the license."
    ),
    "version": VERSION,
}

otext = {
    "sectionTypes": "book,chapter,verse",
    "sectionFeatures": "book,chapter,verse",
    "fmt:text-orig-full": "{word}{trailer}",
}

intFeatures = {"chapter", "verse"}

featureMeta = {
    "book": {"description": "book name in Latin, as in the BHSA"},
    "book@en": {
        "description": "book name in english, as in the BHSA",
        "language": "English",
        "languageCode": "en",
        "languageEnglish": "english",
    },
    "chapter": {"description": "chapter number"},
    "verse": {"description": "verse number"},
    "source": {"description": "source of the words of the verse", "values": "latinise intratext"},
    "word": {"description": "the text of a word"},
    "trailer": {"description": "after-word material until the next word"},
}

Word = tuple[str, str]
Key = tuple[str, int]
Paragraphs = tuple[tuple[str, ...], ...]


class Verse(NamedTuple):
    """One verse with its book names, chapter, verse number, source, and words."""

    book: str
    book_en: str
    chapter: int
    verse: int
    source: str
    words: tuple[Word, ...]


def latinise_verses(path: Path) -> dict[Key, list[list[Word]]]:
    """Reads the words of every verse of the Vulgate documents of LatinISE, by book title and chapter."""
    result: dict[Key, list[list[Word]]] = {}
    inside = False
    key: Key | None = None
    words: list[Word] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("<doc"):
                inside = VULGATE_DOC in line
            elif not inside:
                continue
            elif match := BOOK_TITLE.match(line):
                book = match.group(1)
            elif match := SECTION_TITLE.match(line):
                key = (book, int(match.group(1)))
                result[key] = []
            elif line.startswith("<p"):
                words = []
            elif line.startswith("</p") and key is not None:
                result[key].append(words)
            elif line.startswith(GLUE) and words:
                words[-1] = (words[-1][0], NO_SPACE)
            elif not line.startswith("<"):
                words.append((line.split("\t")[0], SPACE))
    return result


def contents(path: Path) -> list[tuple[str, int, str]]:
    """Lists the book title, chapter, and page of every chapter in the IntraText contents."""
    result: list[tuple[str, int, str]] = []
    book = ""
    for match in CONTENTS_ITEM.finditer(path.read_text(encoding="latin-1")):
        if match.group(1):
            book = match.group(1).strip()
        else:
            result.append((book, int(match.group(3)), match.group(2)))
    return result


def intratext_verses(path: Path) -> list[tuple[int, Paragraphs]]:
    """Reads the number and the words of each paragraph of every verse of an IntraText chapter page."""
    text = path.read_text(encoding="latin-1")
    if CHAPTER_PAGE not in text:
        raise ValueError(f"{path} is not an IntraText chapter page")
    result: list[tuple[int, Paragraphs]] = []
    for paragraph in PARAGRAPH.findall(text):
        content = _plain(paragraph)
        if not content or HEADING.fullmatch(content):
            continue
        match = NUMBERED.fullmatch(content)
        if match is not None:
            result.append((int(match.group(1)), (tuple(match.group(2).split()),)))
        elif result:
            number, paragraphs = result[-1]
            result[-1] = (number, (*paragraphs, tuple(content.split())))
        else:
            raise ValueError(f"{path} has text before its first verse: {content[:60]}")
    return result


def numbers(found: list[int]) -> list[int]:
    """Corrects a verse number that falls back but ends in the digit of the next number, a misprinted tens digit."""
    result: list[int] = []
    for number in found:
        expected = result[-1] + 1 if result else None
        if expected is not None and number < expected and number % 10 == expected % 10:
            number = expected
        result.append(number)
    return result


def joined(found: list[tuple[int, Paragraphs]], positions: Iterable[int]) -> list[tuple[int, Paragraphs]]:
    """Joins the verses at the given positions to the verse before, and numbers the verses in order."""
    result: list[Paragraphs] = []
    for position, (_, paragraphs) in enumerate(found, 1):
        if position in positions:
            result[-1] = (*result[-1], *paragraphs)
        else:
            result.append(paragraphs)
    return list(enumerate(result, found[0][0]))


def verses(
    source: Path, executor: Executor, split: dict[Key, tuple[int, ...]] = SPLIT_VERSES
) -> list[Verse]:
    """Groups the LatinISE paragraphs into the IntraText verses, and takes IntraText words where they do not match."""
    latinise = latinise_verses(source / LATINISE)
    chapters = [item for item in contents(source / INTRATEXT / CONTENTS) if item[0] not in LEFT_OUT]
    paths = [source / INTRATEXT / page for _, _, page in chapters]
    pages = executor.map(intratext_verses, paths, chunksize=CHUNK)
    result: list[Verse] = []
    for (title, chapter, _), found in zip(chapters, pages, strict=True):
        book, book_en = BOOKS[title]
        numbered = (
            joined(found, split[(title, chapter)])
            if (title, chapter) in split
            else list(zip(numbers([n for n, _ in found]), [p for _, p in found], strict=True))
        )
        texts = latinise.get((title, chapter), [])
        if len(texts) == sum(len(paragraphs) for _, paragraphs in numbered):
            parts = iter(texts)
            result.extend(
                Verse(book, book_en, chapter, number, "latinise", tuple(w for _ in paragraphs for w in next(parts)))
                for number, paragraphs in numbered
            )
        else:
            result.extend(
                Verse(book, book_en, chapter, number, "intratext", tuple((w, SPACE) for p in paragraphs for w in p))
                for number, paragraphs in numbered
            )
    return result


def director(cv: Any, source: Iterable[Verse]) -> None:
    """Emits the book, chapter, verse, and word nodes of the verses."""
    for (book, book_en), in_book in groupby(source, key=attrgetter("book", "book_en")):
        book_node = cv.node("book")
        cv.feature(book_node, **{"book": book, "book@en": book_en})
        for chapter, in_chapter in groupby(in_book, key=attrgetter("chapter")):
            chapter_node = cv.node("chapter")
            cv.feature(chapter_node, chapter=chapter)
            for item in in_chapter:
                verse = cv.node("verse")
                cv.feature(verse, verse=item.verse, source=item.source)
                for text, trailer in item.words:
                    word = cv.slot()
                    cv.feature(word, word=text, trailer=trailer)
                cv.terminate(verse)
            cv.terminate(chapter_node)
        cv.terminate(book_node)
    for name in featureMeta:
        if not cv.occurs(name):
            cv.meta(name)


def _plain(fragment: str) -> str:
    """Removes the markup of an HTML fragment and resolves its character references."""
    return html.unescape(TAG.sub("", fragment)).strip()


def convert(
    source: Path = SOURCE_DIR,
    target: Path = TF_DIR,
    executor: Callable[[], Executor] = ProcessPoolExecutor,
) -> bool:
    """Writes the Text-Fabric dataset of the source folder to the target folder."""
    with executor() as pool:
        found = verses(source, pool)
    if target.exists():
        rmtree(target)
    cv = CV(Fabric(locations=str(target), silent="deep"), silent="deep")
    return bool(
        cv.walk(
            lambda walker: director(walker, found),
            slotType,
            otext=otext,
            generic=generic,
            intFeatures=intFeatures,
            featureMeta=featureMeta,
        )
    )


def main(
    argv: list[str] | None = None, executor: Callable[[], Executor] = ProcessPoolExecutor
) -> int:
    """Converts the source given on the command line, or the source of this version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DIR)
    parser.add_argument("--target", type=Path, default=TF_DIR)
    args = parser.parse_args(argv)
    return 0 if convert(args.source, args.target, executor) else 1


if __name__ == "__main__":
    raise SystemExit(main())
