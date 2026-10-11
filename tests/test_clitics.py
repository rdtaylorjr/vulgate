import pytest

from programs import clitics
from programs.proiel import Token


def token(form, space=" "):
    return Token("MATT", 1, 1, form, form, "", "Nb", "-s---mn--i", space)


def test_read_declared_reads_the_clitic_of_each_form_and_place_none_for_whole(tmp_path):
    path = tmp_path / "clitics.yaml"
    path.write_text(
        "forms:\n  mecum: [cum, me + cum]\n  quique: [null, quisque]\nplaces:\n  2Mcc 7:23 quique: [que, qui + -que]\n",
        encoding="utf-8",
    )
    assert clitics.read_declared(path) == clitics.Declared(
        {"mecum": "cum", "quique": None}, {("2Mcc", 7, 23, "quique"): "que"}
    )


def test_treebank_divisions_read_divided_and_whole_forms_by_most_occurrences():
    tokens = [
        token("dixit", ""),
        token("que"),
        token("itaque"),
        token("Deus"),
        token("ne", ""),
        token("que"),
        token("neque"),
        token("ne", ""),
        token("que"),
    ]
    assert clitics.treebank_divisions(tokens) == {"dixitque": "que", "itaque": None, "neque": "que"}


def test_divisions_follow_the_declaration_then_the_treebank_then_divide_que_only():
    forms = [
        "Dixitque",
        "abiitque",
        "aeque",
        "itaque",
        "neque",
        "putasne",
        "tune",
        "grandine",
        "triduumve",
        "grave",
        "mecum",
        "que",
        "et",
    ]
    treebank = {"itaque": None, "neque": "que", "putasne": "ne"}
    declared = {"aeque": None, "tune": "ne", "triduumve": "ve", "mecum": "cum"}
    assert clitics.divisions(forms, treebank, clitics.Declared(declared, {})) == {
        "dixitque": "que",
        "abiitque": "que",
        "neque": "que",
        "putasne": "ne",
        "tune": "ne",
        "triduumve": "ve",
        "mecum": "cum",
    }


def test_divisions_reject_a_declared_form_the_text_lacks_or_the_treebank_decides():
    with pytest.raises(ValueError, match="declared forms the text lacks: 'sicine'"):
        clitics.divisions(["et"], {}, clitics.Declared({"sicine": "ne"}, {}))
    with pytest.raises(ValueError, match="declared forms the treebank decides: 'neque'"):
        clitics.divisions(["neque"], {"neque": "que"}, clitics.Declared({"neque": None}, {}))


def test_divide_cuts_the_clitics_of_a_listed_form_and_leaves_other_forms_whole():
    table = {"dixitque": "que", "mecum": "cum", "huiusmodi": "modi", "tecumque": "que", "tecum": "cum"}
    assert clitics.divide("Dixitque", table) == ["Dixit", "que"]
    assert clitics.divide("MECUM", table) == ["ME", "CUM"]
    assert clitics.divide("huiusmodi", table) == ["huius", "modi"]
    assert clitics.divide("tecumque", table) == ["te", "cum", "que"]
    assert clitics.divide("itaque", table) == ["itaque"]


def test_divisions_reject_a_declared_place_whose_form_the_treebank_decides():
    with pytest.raises(ValueError, match="declared forms the treebank decides: 'neque'"):
        clitics.divisions(["neque"], {"neque": "que"}, clitics.Declared({}, {("Mt", 5, 17, "neque"): None}))
