from concurrent.futures import ThreadPoolExecutor

import pytest

from programs import ota


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
        "PPPP" + "0" * 80 + "      0",
        line("NON SIC IMPII =NON SIC<;> SED TAMQUAM PULVIS", "<P>S<G> 1,4", 40),
        line("EGO SUM <A> ET <!O>", "<A>PC 1,8", 60),
        STRAY,
        line("PRIMUS", "<S>IR<P> 1", 80),
        "",
    ]
)

FIXES = {8: [STRAY, "", "stray duplicate line"]}


def test_fixed_lines_apply_each_declared_fix_to_its_line():
    assert ota.fixed_lines("A B\nC D\nE F", {2: ["C", "X", "reason"]}) == ["A B", "X D", "E F"]


def test_fixed_lines_reject_a_fix_whose_text_is_absent():
    with pytest.raises(ValueError, match="line 2"):
        ota.fixed_lines("A B\nC D", {2: ["Q", "X", "reason"]})


def test_records_join_continued_lines_and_skip_book_separators():
    found = ota.records(ota.fixed_lines(SOURCE, FIXES))
    assert [(r.code, r.chapter, r.verse) for r in found] == [
        ("<G>N", 1, 1),
        ("<G>N", 1, 1),
        ("<G>N", 1, 2),
        ("<P>S<G>", 1, 4),
        ("<A>PC", 1, 8),
        ("<S>IR<P>", 1, 1),
    ]
    assert found[2].text == "ET TENEBRAE (+ ERANT @<A>'!C) SUPER (FERENTEM @<TM'!F>@;' FACIENTEM !C) FACIEM"


def test_reference_reads_chapter_and_verse_or_a_verse_of_a_book_without_chapters():
    assert ota.reference("<G>N 1,12\\") == ("<G>N", 1, 12)
    assert ota.reference("<A>BD 21\\") == ("<A>BD", 1, 21)
    assert ota.reference("<S>IR<P> 3\\") == ("<S>IR<P>", 1, 3)


def test_decode_entry_gives_the_printed_notation():
    assert ota.decode_entry("FERENTEM @<TM'!F>@;' FACIENTEM !C") == "ferentem T M Φ; facientem 𝔠"
    assert ota.decode_entry("MOBILEM @<O>'.@;' MUTABILEM @<AC'!L>!R") == "mobilem O.; mutabilem A C Λ 𝔯"
    assert ota.decode_entry("+ ERANT @<A>'!C") == "+ erant A 𝔠"
    assert ota.decode_entry("% % @<AM>'") == "om. om. A M"
    assert ota.decode_entry("? L. M. @<C>'!C") == "~ l. m. C 𝔠"
    assert ota.decode_entry("-IS @<T'!F>!C") == "-is T Φ 𝔠"


def test_decode_entry_gives_lemma_witnesses_editorial_words_and_hands():
    assert ota.decode_entry("@<GAO>'!R!B@;' <A>DAE @CET'.") == "G A O 𝔯 𝔟; Adae cet."
    assert (
        ota.decode_entry("COTIDIANUM @<S>-MG'.@<GC>;' + COTIDIANUM @<F>'.")
        == "cotidianum S (marg.) G C; + cotidianum F."
    )
    assert ota.decode_entry("<I>ONA @<S>-TXT'.@<ZC'!F>!C") == "Iona S (text.) Z C Φ 𝔠"
    assert ota.decode_entry("-O @<C> ET '!R @LAPSU'") == "-o C et 𝔯 lapsu"
    assert ota.decode_entry("CENTUM @<A\"Q'!O>!C") == "centum A2 Q Ω 𝔠"
    assert ota.decode_entry("PARTE @<A*>;' EX PARTE <!O>!C") == "parte A*; ex parte Ω 𝔠"


def test_decode_entry_gives_nested_variants_and_signs():
    assert ota.decode_entry("+ CUM [EIUS @<A>'] @<A'!L>!C") == "+ cum (eius A) A Λ 𝔠"
    assert ota.decode_entry("=ET<;> @<R>'") == "÷et: R"
    assert ota.decode_entry("* @<R>'") == "※ R"
    assert ota.decode_entry("-ITE @<S>'!S@;' -IT @CET'.") == "-ite S 𝔰; -it cet."


def test_decode_entry_keeps_parentheses_of_a_reading():
    assert ota.decode_entry("? O. M. (RE)CID. @<T>'!C") == "~ o. m. (re)cid. T 𝔠"


def test_decode_entry_rejects_an_unknown_character():
    with pytest.raises(ValueError, match="unexpected"):
        ota.decode_entry("+ ET # @<A>'")


def test_decode_entry_shifts_the_whole_run_between_angle_brackets():
    assert ota.decode_entry("-US @<A'!S@M>'!C") == "-us A Σ M 𝔠"
    assert ota.decode_entry("% @<C'!S!L@M'!F>!C") == "om. C Σ Λ M Φ 𝔠"


def test_stichos_reads_words_signs_verse_marks_and_entries():
    found = ota.stichos("NON SIC IMPII =NON SIC<;> SED (% @<C>') <D>EUS <7> IGNIS<; >(+ ET !C) MEUS", 1)
    assert found == [
        ota.Item("non", "", " ", (), (), 1),
        ota.Item("sic", "", " ", (), (), 1),
        ota.Item("impii", "", " ", (), (), 1),
        ota.Item("non", "÷", " ", (), (), 1),
        ota.Item("sic", "", ": ", (), (), 1),
        ota.Item("sed", "", " ", ("om. C",), (), 1),
        ota.Item("Deus", "", " ", (), (), 1),
        ota.Item("ignis", "", ": ", ("+ et 𝔠",), (), 7),
        ota.Item("meus", "", " ", (), (), 7),
    ]


def test_stichos_decodes_the_metobelus_inside_an_entry():
    assert ota.stichos("=ET<;> (=ET<;> @<R>') RETRIBUET", 21) == [
        ota.Item("et", "÷", ": ", ("÷et: R",), (), 21),
        ota.Item("retribuet", "", " ", (), (), 21),
    ]


def test_stichos_puts_an_entry_before_the_first_word_on_that_word():
    assert ota.stichos("(+ ET !C) *GRANDO ET  5  QUIA", 4) == [
        ota.Item("grando", "※", " ", (), ("+ et 𝔠",), 4),
        ota.Item("et", "", " ", (), (), 4),
        ota.Item("quia", "", " ", (), (), 5),
    ]


def test_stichos_without_words_keeps_its_entries_for_the_word_before():
    assert ota.stichos("(+ EQUI EORUM !C.)", 67) == [ota.Item("", "", "", ("+ equi eorum 𝔠.",), (), 67)]


def test_stichos_without_words_gives_its_sign_to_the_added_text():
    assert ota.stichos("= (+ ET PERFICE @<C'!S!L>)", 40) == [ota.Item("", "", "", ("+ ÷et perfice C Σ Λ",), (), 40)]


def test_stichos_rejects_a_sign_before_an_entry_that_adds_nothing():
    with pytest.raises(ValueError, match="sign"):
        ota.stichos("= (% @<C>')", 40)


def test_stichos_rejects_a_sign_that_stands_before_nothing():
    with pytest.raises(ValueError, match="sign"):
        ota.stichos("VERBUM =", 1)


def test_stichos_gives_greek_letters_of_the_text_in_lower_case():
    assert [t.word for t in ota.stichos("EGO SUM <A> ET <!O>", 8)] == ["ego", "sum", "A", "et", "ω"]


def test_stichos_reads_an_empty_shift_as_nothing():
    assert [t.word for t in ota.stichos("ILLOS ACTI (-AE @<A>')<>", 2)] == ["illos", "acti"]


def test_words_give_entries_of_a_line_without_words_to_the_word_before_in_the_book():
    found = [
        ota.Record("IN PRINCIPIO (% @<C>')", "<G>N", 1, 1),
        ota.Record("(+ EQUI !C.)", "<G>N", 1, 1),
        ota.Record("(+ ET FACTUM !C)", "<L>AM", 1, 1),
        ota.Record("(+ SEDIT !C)", "<L>AM", 1, 1),
        ota.Record("ALEPH QUOMODO", "<L>AM", 1, 1),
    ]
    with ThreadPoolExecutor() as pool:
        result = ota.words(found, pool)
    assert [(w.code, w.word, w.apparatus, w.before) for w in result] == [
        ("<G>N", "in", (), ()),
        ("<G>N", "principio", ("om. C", "+ equi 𝔠."), ()),
        ("<L>AM", "aleph", (), ("+ et factum 𝔠", "+ sedit 𝔠")),
        ("<L>AM", "quomodo", (), ()),
    ]


def test_words_reject_entries_that_no_word_follows():
    with ThreadPoolExecutor() as pool, pytest.raises(ValueError, match="without a word"):
        ota.words([ota.Record("(+ ET !C)", "<G>N", 1, 1)], pool)


def test_book_name_spells_the_code_of_the_source_with_its_capitals():
    assert ota.book_name("<G>N") == "Gn"
    assert ota.book_name("1<S>M") == "1Sm"
    assert ota.book_name("<P>S<G>") == "PsG"
    assert ota.book_name("<S>IR<P>") == "SirP"
    assert ota.book_name("<O>R<M>AN") == "OrMan"


def test_decode_entry_separates_an_editorial_word_from_the_siglum_before_it():
    assert ota.decode_entry("-O @<C>LAPSU'") == "-o C lapsu"


def test_reference_rejects_a_field_without_a_reference():
    with pytest.raises(ValueError, match="no reference"):
        ota.reference("???")


def test_records_reject_a_line_without_reference_or_continuation():
    with pytest.raises(ValueError, match="without reference"):
        ota.records(["IN PRINCIPIO"])


def test_records_reject_a_continued_line_without_end():
    with pytest.raises(ValueError, match="without end"):
        ota.records(["IN PRINCIPIO\\     10"])


def test_segments_reject_an_unbalanced_entry():
    with pytest.raises(ValueError, match="unbalanced"):
        ota.segments("IN (+ ET")


def test_decode_word_rejects_an_unknown_character():
    with pytest.raises(ValueError, match="unexpected"):
        ota.decode_word("IN#")


def test_decode_entry_gives_fragment_sigla_one_by_one():
    assert ota.decode_entry("<D>EI @<A>HM'") == "Dei A h m"
    assert ota.decode_entry("-DET @<O'!S>@L'") == "-det O Σ l"
    assert ota.decode_entry("@<GC>L'.") == "G C l."


def test_decode_entry_keeps_editorial_words_and_names_whole():
    assert ota.decode_entry("% @OM'.") == "om. om."
    assert ota.decode_entry("<O>CHOZIAS !C @ET SIC SEMPER PRO REGE <I>UDA'") == "Ochozias 𝔠 et sic semper pro rege Iuda"
    assert ota.decode_entry("? O. <D>. !C @<V>ER'") == "~ o. D. 𝔠 Ver"
    assert ota.decode_entry("AVERTANT @<L>IGHT'") == "avertant Light"


def test_decode_entry_rejects_an_italic_letter_that_is_no_siglum():
    with pytest.raises(ValueError, match="siglum"):
        ota.decode_entry("+ ET @Q'")
