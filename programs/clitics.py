"""Divides written words into hosts and clitics, as declared or else by the rule that -que alone divides."""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import yaml

from programs.align import normal

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence, Set
    from pathlib import Path

    from programs.proiel import Token

CLITICS = ("que", "ne", "ve")
ATTACHED = ("que", "ne", "ve", "cum", "modi")
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


def ending(form: str) -> str | None:
    """Gives the clitic a form ends in, or None."""
    return next((c for c in CLITICS if form.endswith(c) and len(form) > len(c)), None)


def divisions(forms: Iterable[str], declared: Declared) -> dict[str, str]:
    """Gives each dividing form with its clitic, as declared or else by the rule; a declared form must be in the text."""
    present = {form.lower() for form in forms}
    if missing := sorted(set(declared.forms) - present):
        raise ValueError(f"declared forms the text lacks: {', '.join(map(repr, missing))}")
    rule = {form: DIVIDING if ending(form) == DIVIDING else None for form in present}
    found = rule | declared.forms
    return {form: clitic for form, clitic in sorted(found.items()) if clitic is not None}


def divide(form: str, table: Mapping[str, str | None]) -> list[str]:
    """Divides a written form into its host and its clitics by the table, or leaves it whole."""
    clitic = table.get(form.lower())
    if clitic is None:
        return [form]
    return [*divide(form[: -len(clitic)], table), form[-len(clitic) :]]


def units(tokens: Sequence[Token], written: Set[str]) -> list[tuple[Token, ...]]:
    """Joins each treebank token with the clitics written onto it, where the joined form is a written word of the text."""
    result: list[tuple[Token, ...]] = []
    for token in tokens:
        if result and result[-1][-1].space == "" and token.form.lower() in ATTACHED:
            joined = normal("".join(t.form for t in (*result[-1], token)))
            if joined in written:
                result[-1] = (*result[-1], token)
                continue
        result.append((token,))
    return result


def cut(form: str, clitics: Sequence[str]) -> list[str]:
    """Divides a written form into its host and the given clitics, the last clitic last."""
    parts: list[str] = []
    for clitic in reversed(clitics):
        parts.insert(0, form[-len(clitic) :])
        form = form[: -len(clitic)]
    return [form, *parts]
