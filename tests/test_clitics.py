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


def test_divide_cuts_the_clitics_of_a_listed_form_and_leaves_other_forms_whole():
    table = {"dixitque": "que", "mecum": "cum", "huiusmodi": "modi", "tecumque": "que", "tecum": "cum"}
    assert clitics.divide("Dixitque", table) == ["Dixit", "que"]
    assert clitics.divide("MECUM", table) == ["ME", "CUM"]
    assert clitics.divide("huiusmodi", table) == ["huius", "modi"]
    assert clitics.divide("tecumque", table) == ["te", "cum", "que"]
    assert clitics.divide("itaque", table) == ["itaque"]


def test_divisions_follow_the_declaration_then_divide_que_only():
    forms = [
        "Dixitque",
        "abiitque",
        "aeque",
        "neque",
        "putasne",
        "tune",
        "grandine",
        "triduumve",
        "grave",
        "mecum",
        "que",
    ]
    declared = clitics.Declared({"aeque": None, "neque": None, "tune": "ne", "triduumve": "ve", "mecum": "cum"}, {})
    assert clitics.divisions(forms, declared) == {
        "dixitque": "que",
        "abiitque": "que",
        "tune": "ne",
        "triduumve": "ve",
        "mecum": "cum",
    }


def test_divisions_reject_a_declared_form_the_text_lacks():
    with pytest.raises(ValueError, match="declared forms the text lacks: 'sicine'"):
        clitics.divisions(["et"], clitics.Declared({"sicine": "ne"}, {}))


def test_units_join_a_clitic_to_its_host_where_the_joined_form_is_a_written_word():
    tokens = [
        token("dixit", ""),
        token("que"),
        token("me", ""),
        token("cum"),
        token("est", ""),
        token("cum"),
        token("ne", ""),
        token("que"),
    ]
    found = clitics.units(tokens, {"dixitque", "mecum", "neque", "cum"})
    assert [[t.form for t in unit] for unit in found] == [
        ["dixit", "que"],
        ["me", "cum"],
        ["est"],
        ["cum"],
        ["ne", "que"],
    ]


def test_cut_divides_a_form_into_its_host_and_the_given_clitics():
    assert clitics.cut("Dixitque", ["que"]) == ["Dixit", "que"]
    assert clitics.cut("tecumque", ["cum", "que"]) == ["te", "cum", "que"]
    assert clitics.cut("neque", []) == ["neque"]
