import pytest

from programs import morphology
from programs.proiel import decode


def test_read_classes_map_each_lemma_and_homograph_to_its_part_of_speech(tmp_path):
    path = tmp_path / "lemmas.yaml"
    path.write_text("non: [nega, negation]\nmane#2: [subs, a thing]\n", encoding="utf-8")
    assert morphology.read_classes(path) == {("non", ""): "nega", ("mane", "2"): "subs"}


def test_lemma_key_separates_a_lemma_from_its_homograph_number():
    assert morphology.lemma_key("ut#2") == ("ut", "2")
    assert morphology.lemma_key("sum") == ("sum", "")


def test_classed_gives_the_declared_class_and_rejects_a_foreign_word_without_one():
    classes = {("non", ""): "nega", ("racha", ""): "subs"}
    assert morphology.classed(("non", ""), decode("Df", "---------n"), classes, "MATT 5.17").pdp == "nega"
    assert morphology.classed(("racha", ""), decode("F-", "---------n"), classes, "MATT 5.22").pdp == "subs"
    assert morphology.classed(("et", ""), decode("C-", "---------n"), classes, "MATT 1.2").pdp == "conj"
    with pytest.raises(ValueError, match="MATT 5.22: no part of speech for \\('raca', ''\\)"):
        morphology.classed(("raca", ""), decode("F-", "---------n"), classes, "MATT 5.22")
