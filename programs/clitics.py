"""Divides written words into hosts and clitics: as declared, else as the treebank does, else -que alone divides."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, NamedTuple

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from programs.proiel import Token

CLITICS = ("que", "ne", "ve")
DIVIDING = "que"


Place = tuple[str, int, int, str]


class Declared(NamedTuple):
    """The declared clitic of forms and of single occurrences, None where the word stays whole."""

    forms: dict[str, str | None]
    places: dict[Place, str | None]


def _place(text: str) -> Place:
    """Reads a place written as book chapter:verse form."""
    book, reference, form = text.split(" ")
    chapter, verse = reference.split(":")
    return book, int(chapter), int(verse), form


def read_declared(path: Path) -> Declared:
    """Reads the declared clitic of each form and of each single occurrence, None for a word that stays whole."""
    declared = yaml.safe_load(path.read_text(encoding="utf-8"))
    forms = {form: clitic for form, (clitic, _) in (declared["forms"] or {}).items()}
    places = {_place(text): clitic for text, (clitic, _) in (declared["places"] or {}).items()}
    return Declared(forms, places)


def _ending(form: str) -> str | None:
    """Gives the clitic a form ends in, or None."""
    return next((c for c in CLITICS if form.endswith(c) and len(form) > len(c)), None)


def treebank_divisions(tokens: Sequence[Token]) -> dict[str, str | None]:
    """Reads for each form ending in a clitic the clitic most of its treebank occurrences divide off, or None."""
    found: dict[str, Counter[str | None]] = {}
    for previous, token in zip(tokens, tokens[1:]):
        lower = token.form.lower()
        if lower in CLITICS and previous.space == "":
            found.setdefault(previous.form.lower() + lower, Counter())[lower] += 1
    for token in tokens:
        lower = token.form.lower()
        if _ending(lower):
            found.setdefault(lower, Counter())[None] += 1
    return {form: counts.most_common(1)[0][0] for form, counts in found.items()}


def divisions(forms: Iterable[str], treebank: Mapping[str, str | None], declared: Declared) -> dict[str, str]:
    """Gives each dividing form with its clitic; a declared form must be in the text and not in the treebank."""
    present = {form.lower() for form in forms}
    if missing := sorted(set(declared.forms) - present):
        raise ValueError(f"declared forms the text lacks: {', '.join(map(repr, missing))}")
    if decided := sorted((set(declared.forms) | {place[3] for place in declared.places}) & set(treebank)):
        raise ValueError(f"declared forms the treebank decides: {', '.join(map(repr, decided))}")
    rule = {form: DIVIDING if _ending(form) == DIVIDING else None for form in present}
    found = rule | {form: treebank[form] for form in present & set(treebank)} | declared.forms
    return {form: clitic for form, clitic in sorted(found.items()) if clitic is not None}


def divide(form: str, table: Mapping[str, str | None]) -> list[str]:
    """Divides a written form into its host and its clitics by the table, or leaves it whole."""
    clitic = table.get(form.lower())
    if clitic is None:
        return [form]
    return [*divide(form[: -len(clitic)], table), form[-len(clitic) :]]
