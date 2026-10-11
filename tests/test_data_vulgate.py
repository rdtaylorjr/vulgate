import os
import re
import xml.etree.ElementTree as ET
from collections import Counter

import yaml
from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = "tf"
SOURCE_FOLDER = "source"
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]
SOURCE = os.path.join(ROOT_DIR, SOURCE_FOLDER, latest_data_folder, "ota", "biblelat-0319.txt")
FIXES = os.path.join(ROOT_DIR, "yaml", "fixes.yaml")
TABLES = [os.path.join(ROOT_DIR, "yaml", name) for name in ("lemmas.yaml", "lexicon_proiel.yaml")]
PROIEL_BOOKS = os.path.join(ROOT_DIR, "yaml", "proiel.yaml")
TREEBANK = os.path.join(ROOT_DIR, SOURCE_FOLDER, latest_data_folder, "proiel", "latin-nt.xml")

MORPHOLOGY = ("pdp", "ps", "nu", "gn", "case", "tense", "mood", "voice", "degree")
LEXICAL = ("lex", "sp", "ls", "freq_lex", "rank_lex")

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load(
    " ".join(
        [
            "otype book chapter verse word prefix trailer apparatus apparatus_before language languageISO freq_occ rank_occ",
            *MORPHOLOGY,
            *LEXICAL,
        ]
    )
)
api.loadLog()

F, L = api.F, api.L
WORDS = F.otype.s("word")
with open(PROIEL_BOOKS, encoding="utf-8") as f:
    CODES = yaml.safe_load(f)
NT = set(CODES)


def source_lines():
    with open(SOURCE, encoding="latin-1") as f:
        lines = f.read().split("\n")
    with open(FIXES, encoding="utf-8") as f:
        for number, (old, new, _) in yaml.safe_load(f)["lineFixes"].items():
            lines[number - 1] = lines[number - 1].replace(old, new, 1)
    return lines


def logical_lines():
    result, pending = [], ""
    for line in source_lines():
        if not line.strip() or line.startswith("PPPP"):
            continue
        if "|" in line:
            text, ref = line.split("|", 1)
            result.append((pending + text.rstrip(), ref.split("\\")[0]))
            pending = ""
        else:
            pending += re.sub(r"\\\s*\d*\s*$", "", line)
    return result


def outside_apparatus(text):
    depth, out = 0, []
    for char in text:
        depth += char == "("
        if not depth:
            out.append(char)
        depth -= char == ")"
    return "".join(out)


def entries(text):
    depth, count = 0, 0
    for char in text:
        if char == "(":
            depth += 1
            count += depth == 1
        elif char == ")":
            depth -= 1
    return count


LINES = logical_lines()
MAIN = [outside_apparatus(text) for text, _ in LINES]


def source_words():
    result = []
    for (_, ref), text in zip(LINES, MAIN):
        code, number = ref.split(" ")
        chapter, verse = number.split(",") if "," in number else ("1", number)
        book = re.sub(r"<([^>]*)>|([A-Z]+)", lambda m: m[1] or m[2].lower(), code)
        verse = int(verse)
        text = re.sub(r"<; ?>", " ", text).replace("<>", "")
        for token in re.findall(r"<\d+>|(?<!\S)\d+(?!\S)|\S+", text):
            if token.strip("<>").isdigit():
                verse = int(token.strip("<>"))
                continue
            word = re.sub(r"[^A-Za-zω]", "", token.replace("!O", "ω")).lower()
            if word:
                result.append((book, int(chapter), verse, word))
    return result


def place(w):
    b, c, v = (L.u(w, otype=t)[0] for t in ("book", "chapter", "verse"))
    return F.book.v(b), F.chapter.v(c), F.verse.v(v)


def tf_written_words():
    result, pending = [], ""
    for w in WORDS:
        pending += F.word.v(w).lower()
        if F.trailer.v(w):
            result.append((*place(w), pending))
            pending = ""
    assert pending == ""
    return result


def test_every_word_of_the_source_is_a_written_word_of_the_data_in_the_same_verse_and_order():
    assert source_words() == tf_written_words()


def test_every_apparatus_entry_of_the_source_is_kept():
    expected = sum(entries(text) for text, _ in LINES)
    found = sum(
        len((F.apparatus.v(w) or "").split(" | ")) * bool(F.apparatus.v(w))
        + len((F.apparatus_before.v(w) or "").split(" | ")) * bool(F.apparatus_before.v(w))
        for w in WORDS
    )
    assert found == expected


def test_every_sign_of_the_text_is_kept():
    text = "\n".join(MAIN)
    signs = Counter(F.prefix.v(w) for w in WORDS)
    signs.update(
        entry[2] for w in WORDS for entry in (F.apparatus.v(w) or "").split(" | ") if entry[:3] in ("+ ÷", "+ ※")
    )
    assert signs["÷"] == len(re.findall(r"(?<![^\s>])=", text))
    assert signs["※"] == len(re.findall(r"(?<![^\s>])\*", text))
    assert Counter(F.trailer.v(w) for w in WORDS)[": "] == len(re.findall(r"<; ?>", text))


def test_every_verse_and_stichos_has_a_word():
    assert all(L.d(n, otype="word") for t in ("verse", "stichos") for n in F.otype.s(t))
    assert all(F.word.v(w) and F.language.v(w) == "Latin" and F.languageISO.v(w) == "lat" for w in WORDS)


def test_a_clitic_is_a_whole_word_with_an_empty_trailer_before_it():
    clitics = {"que", "ne", "ve", "cum", "modi"}
    for w in WORDS:
        if F.trailer.v(w) == "":
            assert F.word.v(w + 1).lower() in clitics
            assert F.prefix.v(w + 1) is None and F.apparatus.v(w + 1) is None and F.apparatus_before.v(w + 1) is None


def test_the_treebank_analyses_only_new_testament_words():
    assert all(F.pdp.v(w) is None for w in WORDS if place(w)[0] not in NT)
    assert sum(1 for w in WORDS if F.pdp.v(w) is not None) > 100000


def test_analysed_words_carry_every_morphological_feature_with_a_declared_value():
    declared = {name: set(TF.features[name].metaData["values"].split()) for name in MORPHOLOGY}
    for w in WORDS:
        if F.pdp.v(w) is not None:
            for name in MORPHOLOGY:
                assert getattr(F, name).v(w) in declared[name], (w, name, getattr(F, name).v(w))


def test_every_lexeme_has_one_part_of_speech_and_set_shared_by_its_words():
    for lex in F.otype.s("lex"):
        words = L.d(lex, otype="word")
        assert words and len(words) == F.freq_lex.v(lex)
        assert {F.lex.v(w) for w in words} == {F.lex.v(lex)}
        assert {F.sp.v(w) for w in words} == {F.sp.v(lex)}
        assert {F.ls.v(w) for w in words} == {F.ls.v(lex)}
    assert len({F.lex.v(n) for n in F.otype.s("lex")}) == len(F.otype.s("lex"))


def test_frequencies_and_ranks_count_the_data():
    forms = Counter(F.word.v(w) for w in WORDS)
    assert all(F.freq_occ.v(w) == forms[F.word.v(w)] for w in WORDS)
    top = max(forms.values())
    assert all((F.rank_occ.v(w) == 0) == (forms[F.word.v(w)] == top) for w in WORDS)
    lexes = Counter(F.lex.v(w) for w in WORDS if F.lex.v(w))
    assert all(F.freq_lex.v(w) == lexes[F.lex.v(w)] for w in WORDS if F.lex.v(w))


def treebank_chapters():
    found = Counter()
    for _, element in ET.iterparse(TREEBANK):
        if element.tag == "token" and element.get("form"):
            book, place = element.get("citation-part").rsplit(" ", 1)
            found[(book, int(place.split(".")[0]))] += 1
    return found


def analysed_chapters():
    found = Counter()
    for chapter in F.otype.s("chapter"):
        book = F.book.v(L.u(chapter, otype="book")[0])
        if book in CODES:
            found[(CODES[book], F.chapter.v(chapter))] = sum(1 for w in L.d(chapter, otype="word") if F.pdp.v(w))
    return found


TREEBANK_CHAPTERS = treebank_chapters()
ANALYSED_CHAPTERS = analysed_chapters()


def test_every_chapter_of_the_treebank_is_a_chapter_of_the_text():
    assert set(TREEBANK_CHAPTERS) <= set(ANALYSED_CHAPTERS)


def test_nearly_every_word_of_the_treebank_finds_its_word_in_the_text():
    assert sum(ANALYSED_CHAPTERS.values()) >= 0.996 * sum(TREEBANK_CHAPTERS.values())
    low = {c: ANALYSED_CHAPTERS[c] / n for c, n in TREEBANK_CHAPTERS.items() if ANALYSED_CHAPTERS[c] < 0.9 * n}
    assert low == {}


def test_every_lemma_the_tables_declare_is_a_lemma_of_the_treebank():
    lemmas = {element.get("lemma") for _, element in ET.iterparse(TREEBANK) if element.tag == "token"}
    for table in TABLES:
        with open(table, encoding="utf-8") as f:
            assert set(yaml.safe_load(f)) - lemmas == set(), table
