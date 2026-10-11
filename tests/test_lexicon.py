import pytest

from programs import lexicon
from programs import proiel


def analysis(pos, morphology="---------n"):
    return proiel.decode(pos, morphology)


def test_lexeme_writes_the_bhsa_convention_with_one_equals_sign_per_homograph_number():
    assert lexicon.lexeme("dico", "", "verb") == "dico["
    assert lexicon.lexeme("terra", "", "subs") == "terra/"
    assert lexicon.lexeme("Deus", "", "nmpr") == "Deus/"
    assert lexicon.lexeme("bonus", "", "adjv") == "bonus/"
    assert lexicon.lexeme("et", "", "conj") == "et"
    assert lexicon.lexeme("ut", "1", "advb") == "ut="
    assert lexicon.lexeme("sum", "2", "verb") == "sum==["


def test_read_lexicon_reads_declared_classes_and_sets(tmp_path):
    path = tmp_path / "lexicon.yaml"
    path.write_text("par: [adjv, none, tie]\nut#1: [null, rela, tie]\n", encoding="utf-8")
    assert lexicon.read_lexicon(path) == {("par", ""): ("adjv", "none"), ("ut", "1"): ("", "rela")}


def occurrences():
    return [
        (("terra", ""), analysis("Nb", "-s---fn--i")),
        (("terra", ""), analysis("Nb", "-s---fa--i")),
        (("et", ""), analysis("C-")),
        (("et", ""), analysis("C-")),
        (("et", ""), analysis("Df")),
        (("ut", "1"), analysis("Df")),
        (("exsul", ""), analysis("Nb", "-s---mn--i")),
        (("exsul", ""), analysis("A-", "-s---mnp-i")),
    ]


def test_lexemes_give_one_part_of_speech_and_set_per_lemma_by_declaration_or_majority():
    found = lexicon.lexemes(occurrences(), {("exsul", ""): ("subs", "none"), ("et", ""): ("", "none")})
    assert found == {
        ("terra", ""): lexicon.Lexeme("terra/", "subs", "none"),
        ("et", ""): lexicon.Lexeme("et", "conj", "none"),
        ("ut", "1"): lexicon.Lexeme("ut=", "advb", "none"),
        ("exsul", ""): lexicon.Lexeme("exsul/", "subs", "none"),
    }


def test_lexemes_reject_a_tie_no_declaration_settles():
    with pytest.raises(ValueError, match="1 lexemes tie and need a lexicon entry: exsul# sp subs 1 adjv 1"):
        lexicon.lexemes(occurrences(), {})


def test_ranks_count_the_items_with_a_higher_frequency():
    assert lexicon.ranks({"a": 5, "b": 2, "c": 5, "d": 1}) == {"a": 0, "b": 2, "c": 0, "d": 3}
    assert lexicon.ranks({}) == {}
