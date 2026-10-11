"""Decodes the Oxford Text Archive Vulgate (item 0319) into words with their places, signs, and apparatus."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterable
    from concurrent.futures import Executor

VERSION = "0.2"

REPO_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_DIR / "source" / VERSION
FIXES = REPO_DIR / "yaml" / "fixes.yaml"
SOURCE_FILE = Path("ota") / "biblelat-0319.txt"
ENCODING = "latin-1"
CHUNK = 256

SEPARATOR = "PPPP"
CONTINUATION = "\\"
WITHOUT_CHAPTERS = 1

GREEK_CAPITAL = {"F": "Φ", "L": "Λ", "O": "Ω", "S": "Σ", "T": "Θ"}
GREEK_SMALL = {"O": "ω"}
GOTHIC = {"B": "𝔟", "C": "𝔠", "D": "𝔡", "H": "𝔥", "O": "𝔬", "R": "𝔯", "S": "𝔰", "V": "𝔳", "W": "𝔴"}
OPERATORS = {"%": "om.", "?": "~", "=": "÷", "*": "※", "[": "(", "]": ")"}
HAND = {"*": "*", '"': "2"}
PUNCTUATION = " .,;+-()"
EDITORIAL_SUFFIX = {"MG": "(marg.)", "TXT": "(text.)"}
EDITORIAL_WORDS = {
    "an",
    "cet",
    "codd",
    "et",
    "in",
    "lapsu",
    "om",
    "omnes",
    "partim",
    "pro",
    "rege",
    "semper",
    "seqq",
    "sic",
    "supplenda",
    "vel",
}
NAMES = {"Iuda", "Light", "Ver"}
FRAGMENTS = set("bhiklmrs")
OBELUS = "="
ASTERISK = "*"
SIGNS = {OBELUS: "÷", ASTERISK: "※"}
METOBELUS = ":"
ADDITION = "+ "
SPACE = " "

REFERENCE = re.compile(r"(\S+) (\d+)(?:,(\d+))?")
BOOK_CODE = re.compile(r"(\d*)(.+)")
SHIFTED_SEMICOLON = re.compile(r"<; ?>")
EMPTY_SHIFT = re.compile(r"<>")
VERSE_MARK = re.compile(r"<(\d+)>|(?<!\S)(\d+)(?!\S)")
ENTRY_TOKEN = re.compile(r"-(MG|TXT)'\.?|!(.)|(.)", re.S)
WORD_TOKEN = re.compile(r"!(.)|(.)", re.S)
SWITCHES = {"<": ("shifted", True), ">": ("shifted", False), "@": ("italic", True), "'": ("italic", False)}


class Record(NamedTuple):
    """One logical line of the source: a stichos of the edition with its apparatus and its reference."""

    text: str
    code: str
    chapter: int
    verse: int


class Item(NamedTuple):
    """One word of a stichos with its sign, trailer, apparatus entries, and verse; an empty one has entries only."""

    word: str
    prefix: str
    trailer: str
    apparatus: tuple[str, ...]
    before: tuple[str, ...]
    verse: int


class Word(NamedTuple):
    """One word of the text with its place in the book, chapter, verse, and stichos."""

    code: str
    chapter: int
    verse: int
    stichos: int
    word: str
    prefix: str
    trailer: str
    apparatus: tuple[str, ...]
    before: tuple[str, ...]


def fixed_lines(text: str, fixes: dict[int, list[str]]) -> list[str]:
    """Splits the source into lines and applies each declared fix to its line number, counted from 1."""
    lines = text.split("\n")
    for number, (old, new, _) in fixes.items():
        if old not in lines[number - 1]:
            raise ValueError(f"fix for line {number} does not match: {old!r}")
        lines[number - 1] = lines[number - 1].replace(old, new, 1)
    return lines


def reference(field: str) -> tuple[str, int, int]:
    """Gives the book code, chapter, and verse of a reference field, chapter 1 for books without chapters."""
    match = REFERENCE.match(field)
    if match is None:
        raise ValueError(f"no reference in {field!r}")
    code, first, second = match.groups()
    if second is not None:
        return code, int(first), int(second)
    return code, WITHOUT_CHAPTERS, int(first)


def records(lines: Iterable[str]) -> list[Record]:
    """Joins continued lines into the logical lines of the source and reads their references."""
    result: list[Record] = []
    pending = ""
    for line in lines:
        if not line.strip() or line.startswith(SEPARATOR):
            continue
        if "|" in line:
            text, field = line.split("|", 1)
            result.append(Record(pending + text.rstrip(), *reference(field)))
            pending = ""
        else:
            body = line.rstrip().rstrip("0123456789").rstrip()
            if not body.endswith(CONTINUATION):
                raise ValueError(f"line without reference or continuation: {line!r}")
            pending += body[: -len(CONTINUATION)]
    if pending:
        raise ValueError(f"continued line without end: {pending!r}")
    return result


class _Entry:
    """Builds the printed form of one apparatus entry from its codes, read in order."""

    def __init__(self) -> None:
        """Starts an entry in roman, unshifted."""
        self.out: list[str] = []
        self.shifted = False
        self.italic = False
        self.run = ""
        self.capital = False

    def add(self, suffix: str, code: str, char: str) -> None:
        """Reads one code: an editorial suffix, a Greek or Gothic siglum, a switch, or a character."""
        if char in SWITCHES:
            if char in "@'":
                self.flush()
            key, value = SWITCHES[char]
            setattr(self, key, value)
        elif self.italic and not self.shifted and char.isalpha():
            self.run += char.lower()
        else:
            self.flush()
            if suffix:
                self.out.extend((SPACE, EDITORIAL_SUFFIX[suffix]))
                self.italic = False
            elif code:
                self.siglum(GREEK_CAPITAL[code] if self.shifted else GOTHIC[code])
            else:
                self.character(char)

    def siglum(self, symbol: str) -> None:
        """Appends a siglum, separated from what precedes it."""
        if self.out and self.out[-1] not in (SPACE, "("):
            self.out.append(SPACE)
        self.out.append(symbol)
        self.capital = False

    def character(self, char: str) -> None:
        """Appends a character that is no siglum of an edition."""
        if self.italic and char in HAND:
            self.out.append(HAND[char])
        elif self.italic and char.isalpha():
            self.siglum(char)
            self.capital = True
        elif char.isalpha():
            self.out.append(char if self.shifted else char.lower())
        elif self.shifted and char == ";":
            self.out.append(METOBELUS)
        elif char in OPERATORS:
            self.out.append(OPERATORS[char])
        elif char in PUNCTUATION:
            self.out.append(char)
        else:
            raise ValueError(f"unexpected {char!r} in apparatus entry")

    def flush(self) -> None:
        """Ends a run of lower case italic letters: a name, an editorial word, or fragment sigla."""
        run, self.run = self.run, ""
        if not run:
            return
        if self.capital and self.out[-1] + run in NAMES:
            self.out[-1] += run
        elif run in EDITORIAL_WORDS:
            self.siglum(run)
        else:
            for letter in run:
                if letter not in FRAGMENTS:
                    raise ValueError(f"italic {letter!r} is no siglum of a fragment")
                self.siglum(letter)
        self.capital = False

    def text(self) -> str:
        """Gives the printed form of the entry."""
        self.flush()
        return re.sub(r" +", SPACE, "".join(self.out)).strip()


def decode_entry(entry: str) -> str:
    """Gives an apparatus entry in the notation of the printed edition."""
    builder = _Entry()
    for suffix, code, char in ENTRY_TOKEN.findall(entry):
        builder.add(suffix, code, char)
    return builder.text()


def segments(text: str) -> list[tuple[bool, str]]:
    """Splits a logical line into its text and its apparatus entries, each marked whether it is an entry."""
    result: list[tuple[bool, str]] = []
    depth, start = 0, 0
    for i, char in enumerate(text):
        if char == "(":
            if depth == 0:
                result.append((False, text[start:i]))
                start = i + 1
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                result.append((True, text[start:i]))
                start = i + 1
    if depth:
        raise ValueError(f"unbalanced apparatus in {text!r}")
    result.append((False, text[start:]))
    return [(entry, part) for entry, part in result if entry or part]


def decode_word(token: str) -> str:
    """Gives the text of a word with its capitals, Greek letters of the text in lower case."""
    out: list[str] = []
    shifted = False
    for code, char in WORD_TOKEN.findall(token):
        if code:
            out.append(GREEK_SMALL[code])
        elif char in "<>":
            shifted = char == "<"
        elif char.isalpha():
            out.append(char if shifted else char.lower())
        else:
            raise ValueError(f"unexpected {char!r} in word {token!r}")
    return "".join(out)


def book_name(code: str) -> str:
    """Gives the name of a book as its source code spells it, with its number and capitals."""
    number, letters = BOOK_CODE.fullmatch(code).groups()
    return number + decode_word(letters)


def signed(sign: str, entry: str) -> str:
    """Puts the sign of a line without words before the text that its entry adds."""
    if not sign:
        return entry
    if not entry.startswith(ADDITION):
        raise ValueError(f"sign before an entry that adds nothing: {entry!r}")
    return ADDITION + sign + entry[len(ADDITION) :]


class _Line:
    """Collects the items of one logical line while its text and entries are read in order."""

    def __init__(self, verse: int) -> None:
        """Starts a line in the verse of its reference."""
        self.verse = verse
        self.items: list[Item] = []
        self.sign = ""
        self.pending: list[str] = []

    def entry(self, part: str) -> None:
        """Gives an entry to the word before it, or keeps it for the first word."""
        decoded_entry = decode_entry(part)
        if self.items:
            self.items[-1] = self.items[-1]._replace(apparatus=(*self.items[-1].apparatus, decoded_entry))
        else:
            self.pending.append(decoded_entry)

    def text(self, part: str) -> None:
        """Reads the words and verse marks of a piece of text."""
        for mark in re.split(VERSE_MARK, EMPTY_SHIFT.sub("", SHIFTED_SEMICOLON.sub(METOBELUS, part))):
            if mark and mark.isdigit():
                self.verse = int(mark)
            elif mark:
                for raw in mark.split():
                    self.word(raw)

    def word(self, raw: str) -> None:
        """Reads one word with the sign before it and the metobelus after it."""
        while raw[:1] in SIGNS:
            self.sign, raw = SIGNS[raw[0]], raw[1:]
        if raw:
            trailer = METOBELUS + SPACE if raw.endswith(METOBELUS) else SPACE
            word = decode_word(raw.rstrip(METOBELUS))
            self.items.append(Item(word, self.sign, trailer, (), tuple(self.pending), self.verse))
            self.sign, self.pending = "", []

    def finish(self) -> list[Item]:
        """Gives the items, entries of a line without words in an item without a word."""
        if self.pending:
            entries = (signed(self.sign, self.pending[0]), *self.pending[1:])
            self.items.append(Item("", "", "", entries, (), self.verse))
        elif self.sign:
            raise ValueError("sign before nothing")
        return self.items


def stichos(text: str, verse: int) -> list[Item]:
    """Reads the words of a logical line with their signs, verse numbers, and apparatus entries."""
    line = _Line(verse)
    for entry, part in segments(text):
        (line.entry if entry else line.text)(part)
    return line.finish()


def decoded(record: Record) -> list[Item]:
    """Reads the items of a record, for parallel decoding."""
    return stichos(record.text, record.verse)


def words(found: list[Record], executor: Executor) -> list[Word]:
    """Gives every word of the text; entries of a line without words go to the word before in the book, else after."""
    result: list[Word] = []
    leading: tuple[str, ...] = ()
    for index, (record, items) in enumerate(zip(found, executor.map(decoded, found, chunksize=CHUNK), strict=True)):
        for item in items:
            if item.word:
                before = (*leading, *item.before)
                result.append(
                    Word(
                        record.code,
                        record.chapter,
                        item.verse,
                        index,
                        item.word,
                        item.prefix,
                        item.trailer,
                        item.apparatus,
                        before,
                    )
                )
                leading = ()
            elif result and result[-1].code == record.code:
                result[-1] = result[-1]._replace(apparatus=(*result[-1].apparatus, *item.apparatus))
            else:
                leading = (*leading, *item.apparatus)
    if leading:
        raise ValueError(f"apparatus without a word: {leading}")
    return result
