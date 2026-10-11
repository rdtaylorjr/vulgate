from concurrent.futures import ThreadPoolExecutor

import pytest
from tf.fabric import Fabric

from programs import ota, proiel
from programs import tfFromOta as converter
from tests.fixtures import PROIEL, inputs, outputs


def build(tmp_path, **kwargs):
    assert converter.convert(inputs(tmp_path, **kwargs), outputs(tmp_path), ThreadPoolExecutor)
    return Fabric(locations=str(tmp_path / "tf"), silent="deep").loadAll(silent="deep")


def test_convert_builds_books_chapters_verses_stichoi_and_words(tmp_path):
    api = build(tmp_path)
    F, L, T = api.F, api.L, api.T
    assert [F.book.v(b) for b in F.otype.s("book")] == ["Gn", "PsG", "Apc", "SirP"]
    assert len(F.otype.s("stichos")) == 8
    verse = T.nodeFromSection(("Gn", 1, 2))
    assert T.text(verse) == "spiritus et tenebrae super faciem dixitque Deus fiat lux "
    words = L.d(verse, otype="word")
    assert F.apparatus.v(words[2]) == "+ erant A 𝔠"
    assert F.apparatus.v(words[3]) == "ferentem T M Φ; facientem 𝔠"
    assert (
        T.text(T.nodeFromSection(("PsG", 1, 4)))
        == "non sic impii ÷non sic: sed tamquam pulvis ※grando et carbones ignis: "
    )
    grando = [w for w in L.d(T.nodeFromSection(("PsG", 1, 4)), otype="word") if F.word.v(w) == "grando"][0]
    assert F.apparatus_before.v(grando) == "+ et 𝔠"
    assert T.text(T.nodeFromSection(("SirP", 1, 1))) == "primus "
    assert all(
        F.language.v(n) == "Latin" and F.languageISO.v(n) == "lat" for t in ("word", "lex") for n in F.otype.s(t)
    )


def test_convert_divides_clitics_by_the_table(tmp_path):
    api = build(tmp_path)
    F, L, T = api.F, api.L, api.T
    words = L.d(T.nodeFromSection(("Gn", 1, 2)), otype="word")
    dixit, que = words[5], words[6]
    assert (F.word.v(dixit), F.trailer.v(dixit), F.word.v(que), F.trailer.v(que)) == ("dixit", "", "que", " ")
    assert F.apparatus.v(words[3]) is not None and F.prefix.v(que) is None
    assert [F.word.v(w) for w in L.d(T.nodeFromSection(("Gn", 1, 3)), otype="word")] == ["eas", "namque", "ne", "que"]
    assert all(F.pdp.v(w) is None for w in L.d(T.nodeFromSection(("Gn", 1, 2)), otype="word"))


def test_convert_writes_the_proiel_analysis_and_its_lexemes(tmp_path):
    api = build(tmp_path)
    F, L, T = api.F, api.L, api.T
    words = L.d(T.nodeFromSection(("Apc", 1, 8)), otype="word")
    assert [F.word.v(w) for w in words] == ["ego", "sum", "A", "et", "ω", "dixit", "que", "non"]
    ego, sum_, a, et, omega, dixit, que, non = words
    assert (F.lex.v(ego), F.sp.v(ego), F.pdp.v(ego), F.ps.v(ego), F.nu.v(ego), F.gn.v(ego), F.case.v(ego)) == (
        "ego",
        "prps",
        "prps",
        "p1",
        "sg",
        "unknown",
        "nominative",
    )
    assert (F.lex.v(sum_), F.ps.v(sum_), F.tense.v(sum_), F.mood.v(sum_), F.voice.v(sum_)) == (
        "sum[",
        "p1",
        "present",
        "indicative",
        "active",
    )
    assert (F.lex.v(et), F.sp.v(et), F.pdp.v(et), F.ls.v(et)) == ("et", "conj", "conj", "ccrd")
    assert (F.lex.v(dixit), F.tense.v(dixit), F.lex.v(que), F.sp.v(que)) == ("dico[", "perfect", "que", "conj")
    assert (F.lex.v(non), F.sp.v(non), F.pdp.v(non)) == ("non", "nega", "nega")
    assert F.lex.v(a) is None and F.lex.v(omega) is None
    assert sorted(F.lex.v(n) for n in F.otype.s("lex")) == ["dico[", "ego", "et", "non", "que", "sum["]
    lex = [n for n in F.otype.s("lex") if F.lex.v(n) == "et"][0]
    assert (
        list(L.d(lex, otype="word")) == [et]
        and F.freq_lex.v(lex) == 1
        and F.freq_lex.v(et) == 1
        and F.rank_lex.v(et) == 0
    )


def test_convert_counts_frequencies_and_ranks_of_forms(tmp_path):
    api = build(tmp_path)
    F = api.F
    et = [w for w in F.otype.s("word") if F.word.v(w) == "et"]
    assert len(et) == 5 and F.freq_occ.v(et[0]) == 5 and F.rank_occ.v(et[0]) == 0


def test_convert_writes_the_licenses_language_and_attribution(tmp_path):
    build(tmp_path)
    otext = (tmp_path / "tf" / "otext.tf").read_text(encoding="utf-8")
    assert "@licenseUrl=https://creativecommons.org/licenses/by-nc-sa/4.0/" in otext
    assert "@language=lat" in otext
    assert "Oxford Text Archive" in otext
    assert "@fmt:lex-orig-full={lex} " in otext
    cs = (tmp_path / "tf" / "case.tf").read_text(encoding="utf-8")
    assert "PROIEL treebank" in cs and "Creative Commons Attribution-NonCommercial-ShareAlike 4.0" in cs


def test_convert_removes_features_of_an_earlier_conversion(tmp_path):
    target = tmp_path / "tf"
    target.mkdir()
    (target / "old.tf").write_text("@node\n", encoding="utf-8")
    assert converter.convert(inputs(tmp_path), outputs(tmp_path), ThreadPoolExecutor)
    assert not (target / "old.tf").exists()


def test_convert_rejects_a_lexeme_tie_no_table_settles_and_accepts_a_declared_one(tmp_path):
    tied = PROIEL.replace('lemma="sum" part-of-speech="V-"', 'lemma="ego" part-of-speech="V-"')
    with pytest.raises(ValueError, match="lexemes tie and need a lexicon entry: ego# sp"):
        build(tmp_path / "a", treebank=tied)
    api = build(tmp_path / "b", treebank=tied, lexicon_proiel="ego: [prps, null, tie]\n")
    assert {api.F.sp.v(w) for w in api.F.otype.s("word") if api.F.lex.v(w) == "ego"} == {"prps"}


def test_convert_rejects_a_loanword_without_a_class(tmp_path):
    foreign = PROIEL.replace('lemma="et" part-of-speech="C-"', 'lemma="racha" part-of-speech="F-"')
    with pytest.raises(ValueError, match="REV 1.8: no part of speech for \\('racha', ''\\)"):
        build(tmp_path, treebank=foreign)


def test_main_reports_success_and_failure(tmp_path):
    found, made = inputs(tmp_path), outputs(tmp_path)
    args = [f"--{name}={value}" for name, value in {**found._asdict(), **made._asdict()}.items()]
    assert converter.main(args, ThreadPoolExecutor) == 0
    (found.source / "ota" / "biblelat-0319.txt").write_text("", encoding="latin-1")
    none = tmp_path / "none.yaml"
    none.write_text("lineFixes: {}\n", encoding="utf-8")
    undeclared = tmp_path / "undeclared.yaml"
    undeclared.write_text("forms: {}\nplaces: {}\n", encoding="utf-8")
    args = [a for a in args if not a.startswith(("--fixes", "--clitics"))] + [
        "--fixes",
        str(none),
        "--clitics",
        str(undeclared),
    ]
    assert converter.main(args, ThreadPoolExecutor) == 1


def treebank_token(chapter, verse, form, lemma, pos="Df", morphology="---------n"):
    return proiel.Token("REV", chapter, verse, form, lemma, "", pos, morphology, " ")


def test_matched_pairs_written_words_with_treebank_words_only_in_the_same_chapter_and_near_verse():
    text = [
        ota.Word("<A>PC", chapter, verse, 0, form, "", " ", (), ())
        for chapter, verse, form in ((1, 1, "non"), (1, 2, "ne"), (2, 1, "non"), (2, 9, "ne"))
    ]
    tokens = [
        treebank_token(1, 1, "non", "non"),
        treebank_token(2, 1, "ne", "ne"),
        treebank_token(2, 1, "non", "non"),
        treebank_token(2, 2, "ne", "ne"),
    ]
    with ThreadPoolExecutor() as pool:
        found = converter.matched(text, [(t,) for t in tokens], {"Apc": "REV"}, pool)
    assert {i: [t.form for t in unit] for i, unit in found.items()} == {0: ["non"], 2: ["non"]}


def test_divided_follows_the_treebank_then_a_declared_place_then_the_form():
    text = [
        ota.Word("<A>PC", 1, verse, 0, form, "", " ", (), ())
        for verse, form in ((1, "quique"), (2, "quique"), (3, "neque"))
    ]
    ne = treebank_token(1, 3, "ne", "ne")
    que = treebank_token(1, 3, "que", "que", "C-")
    entries = converter.divided(text, {"quique": "que"}, {("Apc", 1, 2, "quique"): None}, {2: (ne, que)}, {})
    assert [[p.form for p in e.parts] for e in entries] == [["qui", "que"], ["quique"], ["ne", "que"]]
    assert [p.proiel.key for p in entries[2].parts] == [("ne", ""), ("que", "")]
    assert entries[0].parts[0].proiel.key is None


def test_divided_rejects_a_declared_place_the_text_lacks():
    text = [ota.Word("<A>PC", 1, 1, 0, "quique", "", " ", (), ())]
    with pytest.raises(ValueError, match="declared places the text lacks: Apc 1:3 quique"):
        converter.divided(text, {}, {("Apc", 1, 3, "quique"): "que"}, {}, {})
