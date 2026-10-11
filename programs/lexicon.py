"""Builds the ETCBC lexemes: one part of speech and lexical set per lemma and homograph."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import yaml

from programs.morphology import lemma_key

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from programs.morphology import Key, Morphology

SUFFIXES = {"verb": "[", "subs": "/", "nmpr": "/", "adjv": "/"}


class Lexeme(NamedTuple):
    """The lexical values of one lemma and homograph."""

    lex: str
    sp: str
    ls: str


def lexeme(lemma: str, homograph: str, sp: str) -> str:
    """Writes a lemma as a BHSA lexeme: one = per homograph number, the unnumbered lemma first."""
    return lemma + "=" * int(homograph or 0) + SUFFIXES.get(sp, "")


def read_lexicon(path: Path) -> dict[Key, tuple[str, str]]:
    """Reads the part of speech and lexical set declared for lexemes, each with its reason."""
    declared = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {lemma_key(name): (sp or "", ls or "") for name, (sp, ls, _) in declared.items()}


def _settle(found: Counter[str], declared: str) -> str | None:
    """Gives the declared value, else the value of most occurrences, else nothing where they tie."""
    if declared:
        return declared
    ranked = found.most_common(2)
    if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
        return ranked[0][0]
    return None


def lexemes(
    occurrences: Iterable[tuple[Key, Morphology]], declared: Mapping[Key, tuple[str, str]]
) -> dict[Key, Lexeme]:
    """Builds one lexeme per lemma and homograph, rejecting a tie no declaration settles."""
    counts: dict[Key, dict[str, Counter[str]]] = defaultdict(lambda: {"sp": Counter(), "ls": Counter()})
    for key, morphology in occurrences:
        counts[key]["sp"][morphology.pdp] += 1
        counts[key]["ls"][morphology.ls] += 1
    result: dict[Key, Lexeme] = {}
    ties: list[str] = []
    for key, found in counts.items():
        sp_declared, ls_declared = declared.get(key, ("", ""))
        sp, ls = _settle(found["sp"], sp_declared), _settle(found["ls"], ls_declared)
        for name, value in (("sp", sp), ("ls", ls)):
            if value is None:
                ties.append(f"{'#'.join(key)} {name} " + " ".join(f"{v} {n}" for v, n in found[name].most_common()))
        if sp is not None and ls is not None:
            result[key] = Lexeme(lexeme(*key, sp), sp, ls)
    if ties:
        raise ValueError(f"{len(ties)} lexemes tie and need a lexicon entry: " + "; ".join(ties))
    return result


def ranks(counts: Mapping[str, int]) -> dict[str, int]:
    """Ranks each item by the number of items with a higher frequency."""
    frequencies = np.fromiter(counts.values(), dtype=np.int64, count=len(counts))
    ordered = np.sort(frequencies)
    higher = len(ordered) - np.searchsorted(ordered, frequencies, side="right")
    return dict(zip(counts, higher.tolist(), strict=True))
