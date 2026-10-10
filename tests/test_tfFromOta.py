import os
import sys
import importlib.util
from concurrent.futures import ThreadPoolExecutor

import pytest
import yaml
from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = os.path.join(ROOT_DIR, 'programs', 'tfFromOta.py')

spec = importlib.util.spec_from_file_location('tfFromOta', PROGRAM)
converter = importlib.util.module_from_spec(spec)
sys.modules['tfFromOta'] = converter
spec.loader.exec_module(converter)


def line(text, ref, number):
    return f'{text:<67}|{ref}\\'.ljust(86) + f'{number:>6}'


def continued(text, number):
    return f'{text}\\'.ljust(86) + f'{number:>6}'


STRAY = line('^00^STRAY LINE', '<A>PC 1,8', 70)

SOURCE = '\n'.join([
    line('IN PRINCIPIO CREAVIT <D>EUS CAELUM ET TERRAM', '<G>N 1,1', 10),
    line("TERRA AUTEM ERAT INANIS (-E @<A>') ET VACUA <2> SPIRITUS", '<G>N 1,1', 20),
    continued("ET TENEBRAE (+ ERANT @<A>'!C) SUPER (FERENTEM @<TM'!F>@;' FACIENTEM", 30),
    line(' !C) FACIEM', '<G>N 1,2', 30),
    'PPPP' + '0' * 80 + '      0',
    line('NON SIC IMPII =NON SIC<;> SED TAMQUAM PULVIS', '<P>S<G> 1,4', 40),
    line('(+ ET !C) *GRANDO ET CARBONES IGNIS<;>  5  QUIA', '<P>S<G> 1,4', 50),
    line('EGO SUM <A> ET <!O>', '<A>PC 1,8', 60),
    STRAY,
    line('PRIMUS', '<S>IR<P> 1', 80),
    '',
])

FIXES = {9: [STRAY, '', 'stray duplicate line']}


def source(tmp_path):
    folder = tmp_path / 'source'
    (folder / 'ota').mkdir(parents=True)
    (folder / 'ota' / 'biblelat-0319.txt').write_text(SOURCE, encoding='latin-1')
    fixes = tmp_path / 'fixes.yaml'
    fixes.write_text(yaml.safe_dump({'lineFixes': FIXES}, allow_unicode=True), encoding='utf-8')
    return folder, fixes


def build(tmp_path):
    folder, fixes = source(tmp_path)
    target = tmp_path / 'tf'
    assert converter.convert(folder, target, fixes, ThreadPoolExecutor)
    return Fabric(locations=str(target), silent='deep').loadAll(silent='deep')


def test_fixed_lines_apply_each_declared_fix_to_its_line():
    lines = converter.fixed_lines('A B\nC D\nE F', {2: ['C', 'X', 'reason']})
    assert lines == ['A B', 'X D', 'E F']


def test_fixed_lines_reject_a_fix_whose_text_is_absent():
    with pytest.raises(ValueError, match='line 2'):
        converter.fixed_lines('A B\nC D', {2: ['Q', 'X', 'reason']})


def test_records_join_continued_lines_and_skip_book_separators():
    found = converter.records(converter.fixed_lines(SOURCE, FIXES))
    assert [(r.code, r.chapter, r.verse) for r in found] == [
        ('<G>N', 1, 1), ('<G>N', 1, 1), ('<G>N', 1, 2), ('<P>S<G>', 1, 4), ('<P>S<G>', 1, 4),
        ('<A>PC', 1, 8), ('<S>IR<P>', 1, 1),
    ]
    assert found[2].text == "ET TENEBRAE (+ ERANT @<A>'!C) SUPER (FERENTEM @<TM'!F>@;' FACIENTEM !C) FACIEM"


def test_reference_reads_chapter_and_verse_or_a_verse_of_a_book_without_chapters():
    assert converter.reference('<G>N 1,12\\') == ('<G>N', 1, 12)
    assert converter.reference('<A>BD 21\\') == ('<A>BD', 1, 21)
    assert converter.reference('<S>IR<P> 3\\') == ('<S>IR<P>', 1, 3)


def test_decode_entry_gives_the_printed_notation():
    assert converter.decode_entry("FERENTEM @<TM'!F>@;' FACIENTEM !C") == 'ferentem T M Φ; facientem 𝔠'
    assert converter.decode_entry("MOBILEM @<O>'.@;' MUTABILEM @<AC'!L>!R") == 'mobilem O.; mutabilem A C Λ 𝔯'
    assert converter.decode_entry("+ ERANT @<A>'!C") == '+ erant A 𝔠'
    assert converter.decode_entry("% % @<AM>'") == 'om. om. A M'
    assert converter.decode_entry("? L. M. @<C>'!C") == '~ l. m. C 𝔠'
    assert converter.decode_entry("-IS @<T'!F>!C") == '-is T Φ 𝔠'


def test_decode_entry_gives_lemma_witnesses_editorial_words_and_hands():
    assert converter.decode_entry("@<GAO>'!R!B@;' <A>DAE @CET'.") == 'G A O 𝔯 𝔟; Adae cet.'
    assert converter.decode_entry("COTIDIANUM @<S>-MG'.@<GC>;' + COTIDIANUM @<F>'.") == (
        'cotidianum S (marg.) G C; + cotidianum F.'
    )
    assert converter.decode_entry("<I>ONA @<S>-TXT'.@<ZC'!F>!C") == 'Iona S (text.) Z C Φ 𝔠'
    assert converter.decode_entry("-O @<C> ET '!R @LAPSU'") == '-o C et 𝔯 lapsu'
    assert converter.decode_entry("CENTUM @<A\"Q'!O>!C") == 'centum A2 Q Ω 𝔠'
    assert converter.decode_entry("PARTE @<A*>;' EX PARTE <!O>!C") == 'parte A*; ex parte Ω 𝔠'


def test_decode_entry_gives_nested_variants_and_signs():
    assert converter.decode_entry("+ CUM [EIUS @<A>'] @<A'!L>!C") == '+ cum (eius A) A Λ 𝔠'
    assert converter.decode_entry("=ET<;> @<R>'") == '÷et: R'
    assert converter.decode_entry("* @<R>'") == '※ R'
    assert converter.decode_entry("-ITE @<S>'!S@;' -IT @CET'.") == '-ite S 𝔰; -it cet.'


def test_decode_entry_keeps_parentheses_of_a_reading():
    assert converter.decode_entry("? O. M. (RE)CID. @<T>'!C") == '~ o. m. (re)cid. T 𝔠'


def test_decode_entry_rejects_an_unknown_character():
    with pytest.raises(ValueError, match='unexpected'):
        converter.decode_entry("+ ET # @<A>'")


def test_decode_entry_shifts_the_whole_run_between_angle_brackets():
    assert converter.decode_entry("-US @<A'!S@M>'!C") == '-us A Σ M 𝔠'
    assert converter.decode_entry("% @<C'!S!L@M'!F>!C") == 'om. C Σ Λ M Φ 𝔠'


def test_stichos_reads_words_signs_verse_marks_and_entries():
    found = converter.stichos("NON SIC IMPII =NON SIC<;> SED (% @<C>') <D>EUS <7> IGNIS<; >(+ ET !C) MEUS", 1)
    assert found == [
        converter.Token('non', '', ' ', (), (), 1),
        converter.Token('sic', '', ' ', (), (), 1),
        converter.Token('impii', '', ' ', (), (), 1),
        converter.Token('non', '÷', ' ', (), (), 1),
        converter.Token('sic', '', ': ', (), (), 1),
        converter.Token('sed', '', ' ', ('om. C',), (), 1),
        converter.Token('Deus', '', ' ', (), (), 1),
        converter.Token('ignis', '', ': ', ('+ et 𝔠',), (), 7),
        converter.Token('meus', '', ' ', (), (), 7),
    ]


def test_stichos_decodes_the_metobelus_inside_an_entry():
    assert converter.stichos("=ET<;> (=ET<;> @<R>') RETRIBUET", 21) == [
        converter.Token('et', '÷', ': ', ('÷et: R',), (), 21),
        converter.Token('retribuet', '', ' ', (), (), 21),
    ]


def test_stichos_puts_an_entry_before_the_first_word_on_that_word():
    found = converter.stichos("(+ ET !C) *GRANDO ET  5  QUIA", 4)
    assert found == [
        converter.Token('grando', '※', ' ', (), ('+ et 𝔠',), 4),
        converter.Token('et', '', ' ', (), (), 4),
        converter.Token('quia', '', ' ', (), (), 5),
    ]


def test_stichos_without_words_keeps_its_entries_for_the_word_before():
    assert converter.stichos("(+ EQUI EORUM !C.)", 67) == [converter.Token('', '', '', ('+ equi eorum 𝔠.',), (), 67)]


def test_stichos_without_words_gives_its_sign_to_the_added_text():
    assert converter.stichos("= (+ ET PERFICE @<C'!S!L>)", 40) == [
        converter.Token('', '', '', ('+ ÷et perfice C Σ Λ',), (), 40)
    ]


def test_stichos_rejects_a_sign_before_an_entry_that_adds_nothing():
    with pytest.raises(ValueError, match='sign'):
        converter.stichos("= (% @<C>')", 40)


def test_stichos_rejects_a_sign_that_stands_before_nothing():
    with pytest.raises(ValueError, match='sign'):
        converter.stichos('VERBUM =', 1)


def test_stichos_gives_greek_letters_of_the_text_in_lower_case():
    assert [t.word for t in converter.stichos('EGO SUM <A> ET <!O>', 8)] == ['ego', 'sum', 'A', 'et', 'ω']


def test_stichos_reads_an_empty_shift_as_nothing():
    assert [t.word for t in converter.stichos("ILLOS ACTI (-AE @<A>')<>", 2)] == ['illos', 'acti']


def test_words_give_entries_of_a_line_without_words_to_the_word_before_in_the_book():
    found = [
        converter.Record("IN PRINCIPIO (% @<C>')", '<G>N', 1, 1),
        converter.Record("(+ EQUI !C.)", '<G>N', 1, 1),
        converter.Record("(+ ET FACTUM !C)", '<L>AM', 1, 1),
        converter.Record("(+ SEDIT !C)", '<L>AM', 1, 1),
        converter.Record("ALEPH QUOMODO", '<L>AM', 1, 1),
    ]
    with ThreadPoolExecutor() as pool:
        result = converter.words(found, pool)
    assert [(w.code, w.word, w.apparatus, w.before) for w in result] == [
        ('<G>N', 'in', (), ()),
        ('<G>N', 'principio', ('om. C', '+ equi 𝔠.'), ()),
        ('<L>AM', 'aleph', (), ('+ et factum 𝔠', '+ sedit 𝔠')),
        ('<L>AM', 'quomodo', (), ()),
    ]


def test_book_name_spells_the_code_of_the_source_with_its_capitals():
    assert converter.book_name('<G>N') == 'Gn'
    assert converter.book_name('1<S>M') == '1Sm'
    assert converter.book_name('<P>S<G>') == 'PsG'
    assert converter.book_name('<S>IR<P>') == 'SirP'
    assert converter.book_name('<O>R<M>AN') == 'OrMan'


def test_convert_builds_books_chapters_verses_stichoi_and_words(tmp_path):
    api = build(tmp_path)
    F, L, T = api.F, api.L, api.T
    assert [F.book.v(b) for b in F.otype.s('book')] == ['Gn', 'PsG', 'Apc', 'SirP']
    assert len(F.otype.s('stichos')) == 7
    verse = T.nodeFromSection(('Gn', 1, 2))
    assert T.text(verse) == 'spiritus et tenebrae super faciem '
    words = L.d(verse, otype='word')
    assert F.apparatus.v(words[2]) == '+ erant A 𝔠'
    assert F.apparatus.v(words[3]) == 'ferentem T M Φ; facientem 𝔠'
    assert T.text(T.nodeFromSection(('PsG', 1, 4))) == 'non sic impii ÷non sic: sed tamquam pulvis ※grando et carbones ignis: '
    grando = [w for w in L.d(T.nodeFromSection(('PsG', 1, 4)), otype='word') if F.word.v(w) == 'grando'][0]
    assert F.apparatus_before.v(grando) == '+ et 𝔠'
    assert T.text(T.nodeFromSection(('SirP', 1, 1))) == 'primus '


def test_convert_writes_the_license_language_and_attribution(tmp_path):
    build(tmp_path)
    otext = (tmp_path / 'tf' / 'otext.tf').read_text(encoding='utf-8')
    assert '@licenseUrl=https://creativecommons.org/licenses/by-nc-sa/4.0/' in otext
    assert '@language=lat' in otext
    assert 'Oxford Text Archive' in otext


def test_convert_removes_features_of_an_earlier_conversion(tmp_path):
    folder, fixes = source(tmp_path)
    target = tmp_path / 'tf'
    target.mkdir()
    (target / 'old.tf').write_text('@node\n', encoding='utf-8')
    assert converter.convert(folder, target, fixes, ThreadPoolExecutor)
    assert not (target / 'old.tf').exists()


def test_main_reports_success_and_failure(tmp_path):
    folder, fixes = source(tmp_path)
    args = ['--source', str(folder), '--fixes', str(fixes)]
    assert converter.main([*args, '--target', str(tmp_path / 'a')], ThreadPoolExecutor) == 0
    empty = tmp_path / 'empty'
    (empty / 'ota').mkdir(parents=True)
    (empty / 'ota' / 'biblelat-0319.txt').write_text('', encoding='latin-1')
    none = tmp_path / 'none.yaml'
    none.write_text('lineFixes: {}\n', encoding='utf-8')
    assert converter.main(['--source', str(empty), '--fixes', str(none), '--target', str(tmp_path / 'b')], ThreadPoolExecutor) == 1


def test_decode_entry_separates_an_editorial_word_from_the_siglum_before_it():
    assert converter.decode_entry("-O @<C>LAPSU'") == '-o C lapsu'


def test_reference_rejects_a_field_without_a_reference():
    with pytest.raises(ValueError, match='no reference'):
        converter.reference('???')


def test_records_reject_a_line_without_reference_or_continuation():
    with pytest.raises(ValueError, match='without reference'):
        converter.records(['IN PRINCIPIO'])


def test_records_reject_a_continued_line_without_end():
    with pytest.raises(ValueError, match='without end'):
        converter.records(['IN PRINCIPIO\\     10'])


def test_segments_reject_an_unbalanced_entry():
    with pytest.raises(ValueError, match='unbalanced'):
        converter.segments('IN (+ ET')


def test_decode_word_rejects_an_unknown_character():
    with pytest.raises(ValueError, match='unexpected'):
        converter.decode_word('IN#')


def test_words_reject_entries_that_no_word_follows():
    with ThreadPoolExecutor() as pool, pytest.raises(ValueError, match='without a word'):
        converter.words([converter.Record("(+ ET !C)", '<G>N', 1, 1)], pool)


def test_decode_entry_gives_fragment_sigla_one_by_one():
    assert converter.decode_entry("<D>EI @<A>HM'") == 'Dei A h m'
    assert converter.decode_entry("-DET @<O'!S>@L'") == '-det O Σ l'
    assert converter.decode_entry("@<GC>L'.") == 'G C l.'


def test_decode_entry_keeps_editorial_words_and_names_whole():
    assert converter.decode_entry("% @OM'.") == 'om. om.'
    assert converter.decode_entry("<O>CHOZIAS !C @ET SIC SEMPER PRO REGE <I>UDA'") == 'Ochozias 𝔠 et sic semper pro rege Iuda'
    assert converter.decode_entry("? O. <D>. !C @<V>ER'") == '~ o. D. 𝔠 Ver'
    assert converter.decode_entry("AVERTANT @<L>IGHT'") == 'avertant Light'


def test_decode_entry_rejects_an_italic_letter_that_is_no_siglum():
    with pytest.raises(ValueError, match='siglum'):
        converter.decode_entry("+ ET @Q'")
