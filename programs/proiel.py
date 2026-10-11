"""Reads the PROIEL treebank of the Vulgate New Testament and writes its analyses in ETCBC feature values."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, NamedTuple

from programs.morphology import CATEGORIES, NA, NONE, UNKNOWN, Morphology, lemma_key

if TYPE_CHECKING:
    from pathlib import Path

PARTS_OF_SPEECH = {
    "Nb": ("subs", NONE),
    "Ne": ("nmpr", NONE),
    "V-": ("verb", NONE),
    "A-": ("adjv", NONE),
    "Ma": ("adjv", "card"),
    "Mo": ("adjv", "ordn"),
    "Ps": ("adjv", "poss"),
    "Pt": ("adjv", "poss"),
    "Py": ("adjv", "indf"),
    "Df": ("advb", NONE),
    "Du": ("inrg", NONE),
    "Dq": ("advb", "rela"),
    "C-": ("conj", "ccrd"),
    "G-": ("conj", "csub"),
    "R-": ("prep", NONE),
    "I-": ("intj", NONE),
    "Pp": ("prps", NONE),
    "Pk": ("prps", "refl"),
    "Pd": ("prde", NONE),
    "Pi": ("prin", NONE),
    "Pr": ("pron", "rela"),
    "Px": ("pron", "indf"),
    "Pc": ("pron", "recp"),
    "F-": (None, NONE),
}
PERSON = {"1": "p1", "2": "p2", "3": "p3"}
NUMBER = {"s": "sg", "p": "pl"}
TENSE = {"p": "present", "i": "imperfect", "r": "perfect", "l": "pluperfect", "f": "future", "t": "futureperfect"}
MOOD = {
    "i": "indicative",
    "s": "subjunctive",
    "m": "imperative",
    "n": "infinitive",
    "p": "participle",
    "d": "gerund",
    "g": "gerundive",
    "u": "supine",
}
VOICE = {"a": "active", "p": "passive"}
GENDER = {"m": "m", "f": "f", "n": "n", "p": UNKNOWN, "o": UNKNOWN, "r": UNKNOWN, "q": UNKNOWN}
CASE = {
    "n": "nominative",
    "a": "accusative",
    "g": "genitive",
    "d": "dative",
    "b": "ablative",
    "l": "locative",
    "v": "vocative",
}
DEGREE = {"c": "comparative", "s": "superlative", "p": NA}
ABSENT = "-"
STRENGTH = {ABSENT: NA}
INFLECTION = {"i": NA, "n": NA}
POSITIONS = (
    ("ps", PERSON),
    ("nu", NUMBER),
    ("tense", TENSE),
    ("mood", MOOD),
    ("voice", VOICE),
    ("gn", GENDER),
    ("case", CASE),
    ("degree", DEGREE),
    ("strength", STRENGTH),
    ("inflection", INFLECTION),
)


class Token(NamedTuple):
    """One word of the treebank with its place, its analysis, and what follows it."""

    book: str
    chapter: int
    verse: int
    form: str
    lemma: str
    homograph: str
    pos: str
    morphology: str
    space: str


def citation(text: str) -> tuple[str, int, int]:
    """Reads a citation such as MATT 1.1 into book code, chapter, and verse."""
    book, place = text.rsplit(" ", 1)
    chapter, verse = place.split(".")
    return book, int(chapter), int(verse)


def read_tokens(path: Path) -> list[Token]:
    """Reads the tokens that carry a form, leaving out the empty tokens of elided words."""
    result: list[Token] = []
    for _, element in ET.iterparse(str(path)):
        if element.tag == "token" and element.get("form"):
            book, chapter, verse = citation(element.get("citation-part"))
            lemma, homograph = lemma_key(element.get("lemma") or "")
            result.append(
                Token(
                    book,
                    chapter,
                    verse,
                    element.get("form"),
                    lemma,
                    homograph,
                    element.get("part-of-speech") or "",
                    element.get("morphology") or "",
                    element.get("presentation-after") or "",
                )
            )
        if element.tag == "sentence":
            element.clear()
    return result


def _value(table: dict[str, str], char: str, morphology: str) -> str:
    """Reads one position of the morphology: absent, or a code of the scheme."""
    if char == ABSENT:
        return NA
    if char not in table:
        raise ValueError(f"morphology {morphology!r} has {char!r} outside the scheme")
    return table[char]


def decode(pos: str, morphology: str) -> Morphology:
    """Writes a part of speech and morphology string of the treebank in ETCBC values."""
    if pos not in PARTS_OF_SPEECH:
        raise ValueError(f"part of speech {pos!r} has no ETCBC class")
    if len(morphology) != len(POSITIONS):
        raise ValueError(f"morphology {morphology!r} does not have {len(POSITIONS)} positions")
    pdp, ls = PARTS_OF_SPEECH[pos]
    values = {name: _value(table, char, morphology) for (name, table), char in zip(POSITIONS, morphology, strict=True)}
    return Morphology(pdp, ls, **{name: values[name] for name in CATEGORIES})
