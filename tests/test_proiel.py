import pytest

from programs import proiel

XML = """<?xml version="1.0" encoding="UTF-8"?>
<proiel export-time="2018-04-07T21:30:35+02:00" schema-version="2.1">
  <source id="latin-nt" language="lat">
    <div><title>Matthew 1</title>
      <sentence id="1" status="reviewed">
        <token id="1" form="liber" citation-part="MATT 1.1" lemma="liber" part-of-speech="Nb" morphology="-s---mn--i" head-id="9" relation="xobj" presentation-after=" "/>
        <token id="2" form="generationis" citation-part="MATT 1.1" lemma="generatio" part-of-speech="Nb" morphology="-s---fg--i" head-id="1" relation="atr"/>
        <token id="9" empty-token-sort="V" citation-part="MATT 1.1" relation="pred"/>
        <token id="3" form="volens" citation-part="MATT 1.19" lemma="volo#1" part-of-speech="V-" morphology="-sppamn--i" head-id="4" relation="xadv"/>
        <token id="4" form="dimittere" citation-part="MATT 1.19" lemma="dimitto" part-of-speech="V-" morphology="--pna----i" relation="pred"/>
      </sentence>
    </div>
  </source>
</proiel>
"""


def test_read_tokens_reads_place_analysis_and_spacing_and_leaves_out_empty_tokens(tmp_path):
    path = tmp_path / "latin-nt.xml"
    path.write_text(XML, encoding="utf-8")
    found = proiel.read_tokens(path)
    assert [t.form for t in found] == ["liber", "generationis", "volens", "dimittere"]
    assert found[0] == proiel.Token("MATT", 1, 1, "liber", "liber", "", "Nb", "-s---mn--i", " ")
    assert (found[2].lemma, found[2].homograph, found[2].chapter, found[2].verse) == ("volo", "1", 1, 19)
    assert found[3].space == ""


def test_citation_reads_book_chapter_and_verse():
    assert proiel.citation("1COR 12.15") == ("1COR", 12, 15)


def values(pos, morphology):
    m = proiel.decode(pos, morphology)
    return {k: v for k, v in m._asdict().items() if v not in ("NA", "none")}


def test_decode_writes_nouns_adjectives_and_numerals():
    assert values("Nb", "-s---fg--i") == {"pdp": "subs", "nu": "sg", "gn": "f", "case": "genitive"}
    assert values("Ne", "-s---mn--i") == {"pdp": "nmpr", "nu": "sg", "gn": "m", "case": "nominative"}
    assert values("A-", "-p---mac-i") == {
        "pdp": "adjv",
        "nu": "pl",
        "gn": "m",
        "case": "accusative",
        "degree": "comparative",
    }
    assert values("A-", "-s---fnp-i") == {"pdp": "adjv", "nu": "sg", "gn": "f", "case": "nominative"}
    assert values("Ma", "-p---mg--i") == {"pdp": "adjv", "ls": "card", "nu": "pl", "gn": "m", "case": "genitive"}
    assert values("Mo", "-s---nn--i") == {"pdp": "adjv", "ls": "ordn", "nu": "sg", "gn": "n", "case": "nominative"}
    assert values("Ps", "-s---fa--i") == {"pdp": "adjv", "ls": "poss", "nu": "sg", "gn": "f", "case": "accusative"}


def test_decode_writes_verbs_with_the_voice_of_the_form():
    assert values("V-", "3spia----i") == {
        "pdp": "verb",
        "ps": "p3",
        "nu": "sg",
        "tense": "present",
        "mood": "indicative",
        "voice": "active",
    }
    assert values("V-", "3spip----i") == {
        "pdp": "verb",
        "ps": "p3",
        "nu": "sg",
        "tense": "present",
        "mood": "indicative",
        "voice": "passive",
    }
    assert values("V-", "2ptia----i") == {
        "pdp": "verb",
        "ps": "p2",
        "nu": "pl",
        "tense": "futureperfect",
        "mood": "indicative",
        "voice": "active",
    }
    assert values("V-", "3srsa----i") == {
        "pdp": "verb",
        "ps": "p3",
        "nu": "sg",
        "tense": "perfect",
        "mood": "subjunctive",
        "voice": "active",
    }
    assert values("V-", "-srppmn--i") == {
        "pdp": "verb",
        "nu": "sg",
        "tense": "perfect",
        "mood": "participle",
        "voice": "passive",
        "gn": "m",
        "case": "nominative",
    }
    assert values("V-", "--pna----i") == {"pdp": "verb", "tense": "present", "mood": "infinitive", "voice": "active"}
    assert values("V-", "---dpnb--i") == {
        "pdp": "verb",
        "mood": "gerund",
        "voice": "passive",
        "gn": "n",
        "case": "ablative",
    }


def test_decode_writes_pronouns_adverbs_conjunctions_and_particles():
    assert values("Pp", "1s---qn--i") == {"pdp": "prps", "ps": "p1", "nu": "sg", "gn": "unknown", "case": "nominative"}
    assert values("Pk", "3s---mb--i") == {
        "pdp": "prps",
        "ls": "refl",
        "ps": "p3",
        "nu": "sg",
        "gn": "m",
        "case": "ablative",
    }
    assert values("Pd", "-p---nn--i") == {"pdp": "prde", "nu": "pl", "gn": "n", "case": "nominative"}
    assert values("Pr", "-s---pn--i") == {
        "pdp": "pron",
        "ls": "rela",
        "nu": "sg",
        "gn": "unknown",
        "case": "nominative",
    }
    assert values("Pi", "-s---nn--i") == {"pdp": "prin", "nu": "sg", "gn": "n", "case": "nominative"}
    assert values("Px", "-s---ma--i") == {"pdp": "pron", "ls": "indf", "nu": "sg", "gn": "m", "case": "accusative"}
    assert values("Df", "---------n") == {"pdp": "advb"}
    assert values("Du", "---------n") == {"pdp": "inrg"}
    assert values("Dq", "---------n") == {"pdp": "advb", "ls": "rela"}
    assert values("C-", "---------n") == {"pdp": "conj", "ls": "ccrd"}
    assert values("G-", "---------n") == {"pdp": "conj", "ls": "csub"}
    assert values("R-", "---------n") == {"pdp": "prep"}
    assert values("I-", "---------n") == {"pdp": "intj"}
    assert proiel.decode("F-", "---------n").pdp is None


def test_decode_marks_a_double_gender_unknown():
    assert [proiel.decode("A-", f"-s---{g}n--i").gn for g in "poqr"] == ["unknown"] * 4


@pytest.mark.parametrize(
    "morphology", ["-s---mn--", "-s---mn--i-", "-x---mn--i", "-s---mz--i", "3spea----i", "-s---mn-xi", "-s---mn--y"]
)
def test_decode_rejects_a_morphology_outside_the_scheme(morphology):
    with pytest.raises(ValueError, match="morphology"):
        proiel.decode("Nb", morphology)


def test_decode_rejects_an_unknown_part_of_speech():
    with pytest.raises(ValueError, match="no ETCBC class"):
        proiel.decode("S-", "-s---mn--i")
