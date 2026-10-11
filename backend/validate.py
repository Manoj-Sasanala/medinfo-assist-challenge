"""Claim-level grounding check (Lane 4): every substantive sentence must trace
to the CITED passages (the top hits actually shown to the user), not just the
wider evidence set. Heuristic (word-overlap), documented as such: it catches
unsupported additions, not paraphrase-level entailment.
"""
from __future__ import annotations

import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from contracts.schemas import CT02Hit

_WORD = re.compile(r"[a-z0-9]+")
_SENT = re.compile(r"(?<=[.!?])\s+")
_STOP = frozenset(
    "a an the of is are was were be been to in on for with what when where which who how why "
    "it its this that these those as at by from or and do does did i you we they he she him her our your "
    "can could should would may might will shall must not no yes if then than so such very more most other into".split()
)
SENT_COVERAGE = 0.25
MIN_COVERAGE = 0.30  # whole-answer floor, kept for diagnostics


def _toks(s: str) -> set[str]:
    return {w for w in _WORD.findall(s.lower()) if w not in _STOP and len(w) > 2}


def sentences(answer: str) -> list[str]:
    return [s.strip() for s in _SENT.split(answer.strip()) if s.strip()]


def coverage(answer: str, hits: list[CT02Hit]) -> float:
    words = _toks(answer)
    if not words:
        return 0.0
    ev = set()
    for h in hits:
        ev |= _toks(h.chunk.text)
    return round(len(words & ev) / len(words), 4)


def ungrounded_sentences(answer: str, hits: list[CT02Hit]) -> list[str]:
    ev = set()
    for h in hits:
        ev |= _toks(h.chunk.text)
    bad = []
    for s in sentences(answer):
        words = _toks(s)
        if len(words) < 3:
            continue  # framing fragments carry no checkable claim
        if len(words & ev) / len(words) < SENT_COVERAGE:
            bad.append(s)
    return bad


def grounded(answer: str, hits: list[CT02Hit]) -> bool:
    return coverage(answer, hits) >= MIN_COVERAGE and not ungrounded_sentences(answer, hits)
