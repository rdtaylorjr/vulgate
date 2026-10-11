"""Converts the Oxford Text Archive Vulgate to Text-Fabric, with the PROIEL treebank's New Testament morphology."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import Executor, ProcessPoolExecutor
from itertools import groupby
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any, NamedTuple

import yaml
from tf.convert.walker import CV
from tf.fabric import Fabric

from programs import proiel
from programs.align import align, nearby
from programs.clitics import Place, divide, divisions, read_declared, treebank_divisions
from programs.lexicon import Lexeme, lexemes, ranks, read_lexicon
from programs.morphology import FEATURES, MORPHOLOGY, NO_ANALYSIS, Key, Layer, Morphology, classed, read_classes
from programs.ota import (
    ENCODING,
    FIXES,
    REPO_DIR,
    SOURCE_DIR,
    SOURCE_FILE,
    VERSION,
    Word,
    book_name,
    fixed_lines,
    records,
    words,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

TF_DIR = REPO_DIR / "tf" / VERSION
PROIEL_BOOKS = REPO_DIR / "yaml" / "proiel.yaml"
CLITICS = REPO_DIR / "yaml" / "clitics.yaml"
LEMMAS = REPO_DIR / "yaml" / "lemmas.yaml"
LEXICON_PROIEL = REPO_DIR / "yaml" / "lexicon_proiel.yaml"
PROIEL_FILE = Path("proiel") / "latin-nt.xml"
LANGUAGE = "Latin"
LANGUAGE_ISO = "lat"

slotType = "word"

PROIEL_LICENSE = (
    "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International, the license of the PROIEL treebank"
)

generic = {
    "name": "Vulgate",
    "source": "Biblia Sacra iuxta Vulgatam Versionem, ed. R. Weber, Stuttgart, encoded at Tübingen under W. Ott",
    "sourceUrl": "http://hdl.handle.net/20.500.14106/0319",
    "sourceFormat": "Tübingen encoding, Oxford Text Archive item 0319",
    "morphology": "New Testament: the PROIEL treebank (Haug and Jøhndal), latin-nt.xml, aligned word by word",
    "encoders": "Wilhelm Ott (Tübingen)",
    "converters": "Rusty Taylor",
    "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International",
    "licenseUrl": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "copynote1": (
        "Oxford Text Archive 0319, Vulgate: Distributed by the University of Oxford under a"
        " Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License."
    ),
    "copynote2": (
        "Modified: converted to Text-Fabric, see docs/transcription.md."
        " Provided as is, without warranties, see the disclaimer in the license."
    ),
    "language": LANGUAGE_ISO,
    "version": VERSION,
}

otext = {
    "sectionTypes": "book,chapter,verse",
    "sectionFeatures": "book,chapter,verse",
    "fmt:text-orig-full": "{prefix}{word}{trailer}",
    "fmt:lex-orig-full": "{lex} ",
}

intFeatures = {"chapter", "verse", "freq_lex", "rank_lex", "freq_occ", "rank_occ"}

featureMeta = {
    "book": {"description": "book name as the source gives it"},
    "chapter": {"description": "chapter number, 1 for books without chapters"},
    "verse": {"description": "verse number"},
    "word": {"description": "the text of a word, a clitic divided from its host"},
    "prefix": {"description": "sign printed before the word: ÷ obelus, ※ asteriscus"},
    "trailer": {
        "description": "material after the word: a space, or the metobelus and a space, nothing before a clitic"
    },
    "apparatus": {"description": "entries of the critical apparatus that follow the written word, separated by |"},
    "apparatus_before": {
        "description": "entries of the critical apparatus that stand before the first word of a stichos"
    },
    "language": {"description": "language of the word or lexeme", "values": LANGUAGE},
    "languageISO": {"description": "language of the word or lexeme in ISO 639 code", "values": LANGUAGE_ISO},
    "freq_occ": {"description": "number of occurrences of the form of the word"},
    "rank_occ": {"description": "number of word forms with a higher frequency"},
    **{
        name: {**meta, "source": "PROIEL treebank, New Testament", "license": PROIEL_LICENSE}
        for name, meta in MORPHOLOGY.items()
    },
}

APPARATUS_JOIN = " | "


class Part(NamedTuple):
    """A host or a clitic of a written word, with its analysis in the PROIEL layer."""

    form: str
    proiel: Layer


class Entry(NamedTuple):
    """A word of the text with its parts."""

    word: Word
    parts: tuple[Part, ...]


def divided(found: Iterable[Word], table: Mapping[str, str], places: Mapping[Place, str | None]) -> list[Entry]:
    """Divides every word at its clitic by the table, or as declared for its place, with no analysis yet."""
    names: dict[str, str] = {}
    unused = set(places)
    result = []
    for word in found:
        name = names.setdefault(word.code, book_name(word.code))
        place = (name, word.chapter, word.verse, word.word.lower())
        local = {**table, place[3]: places[place]} if place in places else table
        unused.discard(place)
        result.append(Entry(word, tuple(Part(form, NO_ANALYSIS) for form in divide(word.word, local))))
    if unused:
        raise ValueError(
            "declared places the text lacks: " + ", ".join(f"{b} {c}:{v} {f}" for b, c, v, f in sorted(unused))
        )
    return result


def morphology_proiel(token: proiel.Token, classes: Mapping[Key, str]) -> Layer:
    """Writes the analysis of a treebank token in ETCBC values, classed by the lemma table."""
    key = (token.lemma, token.homograph)
    return Layer(
        key,
        classed(
            key, proiel.decode(token.pos, token.morphology), classes, f"{token.book} {token.chapter}.{token.verse}"
        ),
    )


def alignment(chapter: tuple[list[str], list[str], list[int], list[int]]) -> list[int | None]:
    """Aligns the words and tokens of one chapter at most one verse apart, for parallel alignment."""
    words, forms, word_verses, token_verses = chapter
    return align(words, forms, nearby(word_verses, token_verses))


def _places(entries: Sequence[Entry], codes: Mapping[str, str]) -> dict[tuple[str, int], list[tuple[int, int]]]:
    """Gives the entry and part index of each word the treebank may cover, by its book code and chapter."""
    names = {code: book_name(code) for code in {e.word.code for e in entries}}
    places: dict[tuple[str, int], list[tuple[int, int]]] = defaultdict(list)
    for e, entry in enumerate(entries):
        code = codes.get(names[entry.word.code])
        if code is not None:
            places[(code, entry.word.chapter)].extend((e, i) for i in range(len(entry.parts)))
    return places


def annotate_proiel(
    entries: Sequence[Entry],
    treebank: Sequence[proiel.Token],
    codes: Mapping[str, str],
    classes: Mapping[Key, str],
    executor: Executor,
) -> list[Entry]:
    """Gives the words the analyses of their treebank tokens, aligned chapter by chapter."""
    tokens: dict[tuple[str, int], list[proiel.Token]] = defaultdict(list)
    for token in treebank:
        tokens[(token.book, token.chapter)].append(token)
    places = _places(entries, codes)
    chapters = [chapter for chapter in places if chapter in tokens]
    jobs = []
    for chapter in chapters:
        words = [entries[e] for e, _ in places[chapter]]
        forms = [entries[e].parts[i].form for e, i in places[chapter]]
        jobs.append(
            (
                forms,
                [t.form for t in tokens[chapter]],
                [w.word.verse for w in words],
                [t.verse for t in tokens[chapter]],
            )
        )
    analyses: dict[tuple[int, int], Layer] = {}
    for chapter, indices in zip(chapters, executor.map(alignment, jobs), strict=True):
        for place, index in zip(places[chapter], indices, strict=True):
            if index is not None:
                analyses[place] = morphology_proiel(tokens[chapter][index], classes)
    result = []
    for e, entry in enumerate(entries):
        parts = tuple(part._replace(proiel=analyses.get((e, i), NO_ANALYSIS)) for i, part in enumerate(entry.parts))
        result.append(entry._replace(parts=parts))
    return result


def occurrences(entries: Iterable[Entry]) -> list[tuple[Key, Morphology]]:
    """Lists the analysed parts with their lexeme keys."""
    return [
        (p.proiel.key, p.proiel.morphology)
        for e in entries
        for p in e.parts
        if p.proiel.key is not None and p.proiel.morphology is not None
    ]


class _Writer:
    """Emits the slots and nodes of the dataset while the entries are walked in order."""

    def __init__(self, cv: Any, entries: Sequence[Entry], proiel_lexemes: Mapping[Key, Lexeme]) -> None:
        """Counts the forms and the lexemes so that every slot carries its frequencies and ranks."""
        self.cv = cv
        self.lexemes = proiel_lexemes
        self.forms = Counter(p.form for e in entries for p in e.parts)
        self.form_ranks = ranks(self.forms)
        self.lexes = Counter(
            proiel_lexemes[p.proiel.key].lex for e in entries for p in e.parts if p.proiel.key is not None
        )
        self.lex_ranks = ranks(self.lexes)
        self.slots: dict[str, list[int]] = defaultdict(list)

    def features(self, analysis: Layer) -> dict[str, Any]:
        """Collects the features of one analysis."""
        m = analysis.morphology
        if m is None:
            return {}
        values: dict[str, Any] = {name: getattr(m, name) for name in FEATURES}
        if analysis.key is not None:
            entry = self.lexemes[analysis.key]
            values |= {
                "lex": entry.lex,
                "sp": entry.sp,
                "ls": entry.ls,
                "freq_lex": self.lexes[entry.lex],
                "rank_lex": self.lex_ranks[entry.lex],
            }
        return values

    def entry(self, item: Entry) -> None:
        """Emits the parts of a word, the sign and apparatus on the host, the trailer on the last part."""
        word = item.word
        last = len(item.parts) - 1
        for index, part in enumerate(item.parts):
            slot = self.cv.slot()
            self.cv.feature(slot, word=part.form, trailer=word.trailer if index == last else "")
            self.cv.feature(slot, language=LANGUAGE, languageISO=LANGUAGE_ISO)
            self.cv.feature(slot, freq_occ=self.forms[part.form], rank_occ=self.form_ranks[part.form])
            if index == 0:
                if word.prefix:
                    self.cv.feature(slot, prefix=word.prefix)
                if word.apparatus:
                    self.cv.feature(slot, apparatus=APPARATUS_JOIN.join(word.apparatus))
                if word.before:
                    self.cv.feature(slot, apparatus_before=APPARATUS_JOIN.join(word.before))
            self.cv.feature(slot, **self.features(part.proiel))
            if part.proiel.key is not None:
                self.slots[self.lexemes[part.proiel.key].lex].append(slot[1])

    def chapter(self, chapter: int, items: Iterable[Entry]) -> None:
        """Emits a chapter with its verses, stichoi, and words, verses and stichoi not nested."""
        chapter_node = self.cv.node("chapter")
        self.cv.feature(chapter_node, chapter=chapter)
        open_nodes: dict[str, tuple[Any, int]] = {}
        for item in items:
            for kind, value in (("verse", item.word.verse), ("stichos", item.word.stichos)):
                node, current = open_nodes.get(kind, (None, None))
                if value != current:
                    if node is not None:
                        self.cv.terminate(node)
                    node = self.cv.node(kind)
                    if kind == "verse":
                        self.cv.feature(node, verse=value)
                    open_nodes[kind] = (node, value)
            self.entry(item)
        for node, _ in open_nodes.values():
            self.cv.terminate(node)
        self.cv.terminate(chapter_node)

    def lexeme_nodes(self) -> None:
        """Emits one lex node per lexeme over all its words."""
        for entry in self.lexemes.values():
            node = self.cv.node("lex", slots=self.slots[entry.lex])
            self.cv.feature(node, lex=entry.lex, sp=entry.sp, ls=entry.ls, language=LANGUAGE, languageISO=LANGUAGE_ISO)
            self.cv.feature(node, freq_lex=self.lexes[entry.lex], rank_lex=self.lex_ranks[entry.lex])


def director(cv: Any, entries: Sequence[Entry], proiel_lexemes: Mapping[Key, Lexeme]) -> None:
    """Emits the book, chapter, verse, stichos, word, and lex nodes of the entries."""
    writer = _Writer(cv, entries, proiel_lexemes)
    for code, in_book in groupby(entries, key=lambda e: e.word.code):
        book_node = cv.node("book")
        cv.feature(book_node, book=book_name(code))
        for chapter, in_chapter in groupby(in_book, key=lambda e: e.word.chapter):
            writer.chapter(chapter, in_chapter)
        cv.terminate(book_node)
    writer.lexeme_nodes()
    for name in featureMeta:
        if not cv.occurs(name):
            cv.meta(name)


class Inputs(NamedTuple):
    """The folders and tables the conversion reads."""

    source: Path = SOURCE_DIR
    fixes: Path = FIXES
    proiel_books: Path = PROIEL_BOOKS
    clitics: Path = CLITICS
    lemmas: Path = LEMMAS
    lexicon_proiel: Path = LEXICON_PROIEL


class Outputs(NamedTuple):
    """The dataset folder the conversion writes."""

    target: Path = TF_DIR


def convert(
    inputs: Inputs = Inputs(), outputs: Outputs = Outputs(), executor: Callable[[], Executor] = ProcessPoolExecutor
) -> bool:
    """Writes the Text-Fabric dataset."""
    declared = yaml.safe_load(inputs.fixes.read_text(encoding="utf-8"))["lineFixes"]
    lines = fixed_lines((inputs.source / SOURCE_FILE).read_text(encoding=ENCODING), declared)
    treebank = proiel.read_tokens(inputs.source / PROIEL_FILE)
    codes = yaml.safe_load(inputs.proiel_books.read_text(encoding="utf-8"))
    with executor() as pool:
        found = words(records(lines), pool)
        declared = read_declared(inputs.clitics)
        table = divisions((w.word for w in found), treebank_divisions(treebank), declared)
        entries = annotate_proiel(
            divided(found, table, declared.places), treebank, codes, read_classes(inputs.lemmas), pool
        )
    proiel_lexemes = lexemes(occurrences(entries), read_lexicon(inputs.lexicon_proiel))
    if outputs.target.exists():
        rmtree(outputs.target)
    cv = CV(Fabric(locations=str(outputs.target), silent="deep"), silent="deep")
    return bool(
        cv.walk(
            lambda walker: director(walker, entries, proiel_lexemes),
            slotType,
            otext=otext,
            generic=generic,
            intFeatures=intFeatures,
            featureMeta=featureMeta,
        )
    )


def main(argv: list[str] | None = None, executor: Callable[[], Executor] = ProcessPoolExecutor) -> int:
    """Converts the sources given on the command line, or the sources of this version."""
    parser = argparse.ArgumentParser(description=__doc__)
    for fields in (Inputs._field_defaults, Outputs._field_defaults):
        for name, default in fields.items():
            parser.add_argument(f"--{name}", type=Path, default=default)
    args = vars(parser.parse_args(argv))
    outputs = Outputs(**{name: args.pop(name) for name in Outputs._fields})
    return 0 if convert(Inputs(**args), outputs, executor) else 1


if __name__ == "__main__":
    raise SystemExit(main())
