"""Claim-level grounding check (Lane 4): answer words must trace to evidence.

Coverage = fraction of answer content-words appearing in retrieved passages.
Below threshold the caller must fall back to the extractive answer (which
quotes evidence verbatim) rather than serving possibly-ungrounded prose.
"""
from __future__ import annotations

import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from contracts.schemas import CT02Hit

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the of is are was were be been to in on for with what when where which who how why "
    "it its this that these those as at by from or and do does did i you we they he she him her our your "
    "can could should would may might will shall must not no yes if then than so such very more most other into".split()
)
MIN_COVERAGE = 0.30


def _toks(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if w not in _STOP and len(w) > 2}


def coverage(answer: str, hits: list[CT02Hit]) -> float:
    words = _toks(answer)
    if not words:
        return 0.0
    ev = set()
    for h in hits:
        ev |= _toks(h.chunk.text)
    return round(len(words & ev) / len(words), 4)


def grounded(answer: str, hits: list[CT02Hit]) -> bool:
    return coverage(answer, hits) >= MIN_COVERAGE
