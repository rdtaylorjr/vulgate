"""The ETCBC morphological values of one occurrence and their features, shared by the readers of the sources."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import yaml

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

NA = "NA"
UNKNOWN = "unknown"
NONE = "none"
CATEGORIES = ("ps", "nu", "gn", "case", "tense", "mood", "voice", "degree")
FEATURES = ("pdp", *CATEGORIES)
Key = tuple[str, str]

PARTS_OF_SPEECH = "subs nmpr verb adjv advb prep conj prps prde prin pron intj nega inrg"
LEXICAL_SETS = "card ordn poss indf rela refl recp ccrd csub none"
MORPHOLOGY = {
    "lex": {"description": "lemma, [ after a verb, / after a noun or adjective, = per homograph after the first"},
    "sp": {"description": "part of speech of the lexeme", "values": PARTS_OF_SPEECH},
    "pdp": {"description": "part of speech of the occurrence", "values": PARTS_OF_SPEECH},
    "ls": {"description": "lexical set of the lexeme", "values": LEXICAL_SETS},
    "ps": {"description": "person", "values": "p1 p2 p3 NA unknown"},
    "nu": {"description": "number", "values": "sg pl NA unknown"},
    "gn": {"description": "gender", "values": "m f n NA unknown"},
    "case": {
        "description": "case",
        "values": "nominative genitive dative accusative ablative vocative locative NA unknown",
    },
    "tense": {"description": "tense", "values": "present imperfect future perfect pluperfect futureperfect NA unknown"},
    "mood": {
        "description": "mood",
        "values": "indicative subjunctive imperative infinitive participle gerund gerundive supine NA unknown",
    },
    "voice": {"description": "voice of the form", "values": "active passive NA unknown"},
    "degree": {"description": "degree", "values": "comparative superlative NA unknown"},
    "freq_lex": {"description": "number of occurrences of the lexeme"},
    "rank_lex": {"description": "number of lexemes with a higher frequency"},
}


class Morphology(NamedTuple):
    """ETCBC feature values of one occurrence."""

    pdp: str | None
    ls: str
    ps: str
    nu: str
    gn: str
    case: str
    tense: str
    mood: str
    voice: str
    degree: str


class Layer(NamedTuple):
    """The analysis of one word: its lexeme key and morphology, both None where the source has none."""

    key: Key | None
    morphology: Morphology | None


NO_ANALYSIS = Layer(None, None)


def lemma_key(text: str) -> Key:
    """Separates a lemma from its homograph number, written after #."""
    lemma, _, homograph = text.partition("#")
    return lemma, homograph


def read_classes(path: Path) -> dict[Key, str]:
    """Reads the part of speech that replaces the source's class for every occurrence of a lemma."""
    declared = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {lemma_key(name): sp for name, (sp, _) in declared.items()}


def classed(key: Key | None, found: Morphology, classes: Mapping[Key, str], place: str) -> Morphology:
    """Gives an occurrence the class the lemma table declares; a word its source does not class must have one."""
    if key in classes:
        return found._replace(pdp=classes[key])
    if found.pdp is None:
        raise ValueError(f"{place}: no part of speech for {key!r}")
    return found
