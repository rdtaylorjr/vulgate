import os
import re
from collections import Counter

import yaml
from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = 'tf'
SOURCE_FOLDER = 'source'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]
SOURCE = os.path.join(ROOT_DIR, SOURCE_FOLDER, latest_data_folder, 'ota', 'biblelat-0319.txt')
FIXES = os.path.join(ROOT_DIR, 'yaml', 'fixes.yaml')

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype book chapter verse word prefix trailer apparatus apparatus_before
''')
api.loadLog()

F, L = api.F, api.L


def source_lines():
    with open(SOURCE, encoding='latin-1') as f:
        lines = f.read().split('\n')
    with open(FIXES, encoding='utf-8') as f:
        for number, (old, new, _) in yaml.safe_load(f)['lineFixes'].items():
            lines[number - 1] = lines[number - 1].replace(old, new, 1)
    return lines


def logical_lines():
    result, pending = [], ''
    for line in source_lines():
        if not line.strip() or line.startswith('PPPP'):
            continue
        if '|' in line:
            text, ref = line.split('|', 1)
            result.append((pending + text.rstrip(), ref.split('\\')[0]))
            pending = ''
        else:
            pending += re.sub(r'\\\s*\d*\s*$', '', line)
    return result


def outside_apparatus(text):
    depth, out = 0, []
    for char in text:
        depth += char == '('
        if not depth:
            out.append(char)
        depth -= char == ')'
    return ''.join(out)


def entries(text):
    depth, count = 0, 0
    for char in text:
        if char == '(':
            depth += 1
            count += depth == 1
        elif char == ')':
            depth -= 1
    return count


LINES = logical_lines()
MAIN = [outside_apparatus(text) for text, _ in LINES]


def source_words():
    result = []
    for (_, ref), text in zip(LINES, MAIN):
        code, number = ref.split(' ')
        chapter, verse = number.split(',') if ',' in number else ('1', number)
        book = re.sub(r'<([^>]*)>|([A-Z]+)', lambda m: m[1] or m[2].lower(), code)
        verse = int(verse)
        text = re.sub(r'<; ?>', ' ', text).replace('<>', '')
        for token in re.findall(r'<\d+>|(?<!\S)\d+(?!\S)|\S+', text):
            if token.strip('<>').isdigit():
                verse = int(token.strip('<>'))
                continue
            word = re.sub(r'[^A-Za-zω]', '', token.replace('!O', 'ω')).lower()
            if word:
                result.append((book, int(chapter), verse, word))
    return result


def tf_words():
    result = []
    for w in F.otype.s('word'):
        b, c, v = (L.u(w, otype=t)[0] for t in ('book', 'chapter', 'verse'))
        result.append((F.book.v(b), F.chapter.v(c), F.verse.v(v), F.word.v(w).lower()))
    return result


def test_every_word_of_the_source_is_a_word_of_the_data_in_the_same_verse_and_order():
    assert source_words() == tf_words()


def test_every_apparatus_entry_of_the_source_is_kept():
    expected = sum(entries(text) for text, _ in LINES)
    found = sum(
        len((F.apparatus.v(w) or '').split(' | ')) * bool(F.apparatus.v(w))
        + len((F.apparatus_before.v(w) or '').split(' | ')) * bool(F.apparatus_before.v(w))
        for w in F.otype.s('word')
    )
    assert found == expected


def test_every_sign_of_the_text_is_kept():
    text = '\n'.join(MAIN)
    signs = Counter(F.prefix.v(w) for w in F.otype.s('word'))
    signs.update(
        entry[2]
        for w in F.otype.s('word')
        for entry in (F.apparatus.v(w) or '').split(' | ')
        if entry[:3] in ('+ ÷', '+ ※')
    )
    assert signs['÷'] == len(re.findall(r'(?<![^\s>])=', text))
    assert signs['※'] == len(re.findall(r'(?<![^\s>])\*', text))
    assert Counter(F.trailer.v(w) for w in F.otype.s('word'))[': '] == len(re.findall(r'<; ?>', text))


def test_every_verse_and_stichos_has_a_word():
    assert all(L.d(n, otype='word') for t in ('verse', 'stichos') for n in F.otype.s(t))
    assert all(F.word.v(w) for w in F.otype.s('word'))
