"""The sources and tables of a small text, for the tests of the converters."""

import yaml

from programs import tfFromOta as converter


def line(text, ref, number):
    return f"{text:<67}|{ref}\\".ljust(86) + f"{number:>6}"


def continued(text, number):
    return f"{text}\\".ljust(86) + f"{number:>6}"


STRAY = line("^00^STRAY LINE", "<A>PC 1,8", 70)

SOURCE = "\n".join(
    [
        line("IN PRINCIPIO CREAVIT <D>EUS CAELUM ET TERRAM", "<G>N 1,1", 10),
        line("TERRA AUTEM ERAT INANIS (-E @<A>') ET VACUA <2> SPIRITUS", "<G>N 1,1", 20),
        continued("ET TENEBRAE (+ ERANT @<A>'!C) SUPER (FERENTEM @<TM'!F>@;' FACIENTEM", 30),
        line(" !C) FACIEM", "<G>N 1,2", 30),
        line("DIXITQUE <D>EUS FIAT LUX  3  EAS NAMQUE NEQUE", "<G>N 1,2", 35),
        "PPPP" + "0" * 80 + "      0",
        line("NON SIC IMPII =NON SIC<;> SED TAMQUAM PULVIS", "<P>S<G> 1,4", 40),
        line("(+ ET !C) *GRANDO ET CARBONES IGNIS<;>  5  QUIA", "<P>S<G> 1,4", 50),
        line("EGO SUM <A> ET <!O> DIXITQUE NON", "<A>PC 1,8", 60),
        STRAY,
        line("PRIMUS", "<S>IR<P> 1", 80),
        "",
    ]
)

FIXES = {10: [STRAY, "", "stray duplicate line"]}


def proiel_token(id, form, citation, lemma, pos, morphology, space=" "):
    return f'<token id="{id}" form="{form}" citation-part="{citation}" lemma="{lemma}" part-of-speech="{pos}" morphology="{morphology}" relation="pred" presentation-after="{space}"/>'


PROIEL = "\n".join(
    [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<proiel export-time="2018-04-07T21:30:35+02:00" schema-version="2.1"><source id="latin-nt" language="lat"><div><sentence id="1" status="reviewed">',
        proiel_token(1, "ego", "REV 1.8", "ego", "Pp", "1s---qn--i"),
        proiel_token(2, "sum", "REV 1.8", "sum", "V-", "1spia----i"),
        proiel_token(3, "alpha", "REV 1.8", "alpha", "Nb", "-s---nn--i"),
        proiel_token(4, "et", "REV 1.8", "et", "C-", "---------n"),
        proiel_token(5, "omega", "REV 1.8", "omega", "Nb", "-s---nn--i"),
        proiel_token(6, "dixit", "REV 1.8", "dico", "V-", "3sria----i", ""),
        proiel_token(7, "que", "REV 1.8", "que", "C-", "---------n"),
        proiel_token(8, "non", "REV 1.8", "non", "Df", "---------n"),
        proiel_token(9, "et", "REV 1.9", "et", "Df", "---------n"),
        "</sentence></div></source></proiel>",
        "",
    ]
)

CLITICS = "forms:\n  namque: [null, conjunction]\nplaces: {}\n"
PROIEL_BOOKS = {"Apc": "REV"}
LEMMAS = "non: [nega, negation]\n"
LEXICON = "{}\n"


def inputs(tmp_path, source=SOURCE, fixes=FIXES, treebank=PROIEL, lexicon_proiel=LEXICON, lemmas=LEMMAS):
    folder = tmp_path / "source"
    for name in ("ota", "proiel"):
        (folder / name).mkdir(parents=True)
    (folder / "ota" / "biblelat-0319.txt").write_text(source, encoding="latin-1")
    (folder / "proiel" / "latin-nt.xml").write_text(treebank, encoding="utf-8")
    texts = {
        "fixes": yaml.safe_dump({"lineFixes": fixes}, allow_unicode=True),
        "proiel_books": yaml.safe_dump(PROIEL_BOOKS),
        "clitics": CLITICS,
        "lemmas": lemmas,
        "lexicon_proiel": lexicon_proiel,
    }
    for name, text in texts.items():
        (tmp_path / f"{name}.yaml").write_text(text, encoding="utf-8")
    return converter.Inputs(folder, *(tmp_path / f"{name}.yaml" for name in texts))


def outputs(tmp_path):
    return converter.Outputs(tmp_path / "tf")
