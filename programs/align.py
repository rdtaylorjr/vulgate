"""Aligns the words of the Oxford Text Archive text with the tokens of an analysed edition."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

LETTERS = re.compile(r"[^a-z]")
NEAR = 1


def normal(form: str) -> str:
    """Spells a form in lower case letters, u for v and i for j."""
    return LETTERS.sub("", form.lower().replace("v", "u").replace("j", "i"))


def nearby(word_verses: Sequence[int], token_verses: Sequence[int]) -> Callable[[int, int], bool]:
    """Lets a word match a token of the same form at most one verse away."""
    return lambda word, token: abs(word_verses[word] - token_verses[token]) <= NEAR


def align(words: Sequence[str], forms: Sequence[str], near: Callable[[int, int], bool]) -> list[int | None]:
    """Gives each word the index of a token of the same form the rule allows, or None, matching leftovers again."""
    normal_words = [normal(w) for w in words]
    normal_forms = [normal(f) for f in forms]
    result: list[int | None] = [None] * len(words)
    far: set[int] = set()
    while True:
        rows = [i for i, found in enumerate(result) if found is None and i not in far]
        taken = {found for found in result if found is not None}
        columns = [j for j in range(len(forms)) if j not in taken]
        matcher = SequenceMatcher(
            None, [normal_words[i] for i in rows], [normal_forms[j] for j in columns], autojunk=False
        )
        pairs = [
            (rows[i1 + k], columns[j1 + k])
            for tag, i1, i2, j1, _ in matcher.get_opcodes()
            if tag == "equal"
            for k in range(i2 - i1)
        ]
        if not pairs:
            return result
        for i, j in pairs:
            if near(i, j):
                result[i] = j
            else:
                far.add(i)
