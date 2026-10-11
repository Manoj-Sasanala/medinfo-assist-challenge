"""Claim-level grounding check (Lane 4): every substantive sentence must trace
to the CITED passages (the top hits actually shown to the user), not just the
wider evidence set.

Two layers, both must pass:
  1. Lexical heuristic (fast): per-sentence word-overlap with cited passages.
  2. NLI entailment (typeform/distilbert-base-uncased-mnli, lazy): each
     substantive sentence must be ENTAILED by the cited passages
     (P(entailment) >= 0.5). Neutral/contradiction-dominant sentences fail.

If the NLI model cannot load, layer 1 alone decides and the caller is told via
nli_available(). Anything failing either layer falls back to the extractive
quote (which cannot add claims by construction).
"""
from __future__ import annotations

import re
from functools import lru_cache
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
NLI_MODEL = "typeform/distilbert-base-uncased-mnli"
NLI_ENTAIL_MIN = 0.5


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
    if coverage(answer, hits) < MIN_COVERAGE or ungrounded_sentences(answer, hits):
        return False
    nli_bad = nli_ungrounded_sentences(answer, hits)
    return not nli_bad


@lru_cache(maxsize=1)
def _nli():
    """(tokenizer, model) or (None, None) if unavailable. Lazy: ~250MB download once."""
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(NLI_MODEL)
        mdl = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL)
        mdl.eval()
        return tok, mdl
    except Exception:
        return None, None


def nli_available() -> bool:
    tok, mdl = _nli()
    return tok is not None


def validator_mode() -> str:
    """Which grounding layers are active. Served via /api/health so a missing
    NLI model (heuristic-only mode) is visible instead of silent."""
    return "heuristic+nli" if nli_available() else "heuristic-only"


def nli_entailment(premise: str, hypothesis: str) -> float:
    """P(entailment) of hypothesis given premise. Raises if NLI unavailable."""
    import torch
    tok, mdl = _nli()
    if tok is None:
        raise RuntimeError("NLI model unavailable")
    with torch.no_grad():
        logits = mdl(**tok(premise, hypothesis, return_tensors="pt", truncation=True)).logits
        probs = torch.softmax(logits, dim=-1)[0]
    entail_idx = next(i for i, l in mdl.config.id2label.items() if l.upper() == "ENTAILMENT")
    return round(float(probs[int(entail_idx)]), 4)


def nli_ungrounded_sentences(answer: str, hits: list[CT02Hit]) -> list[str]:
    if not nli_available():
        return []
    premise = "\n".join(h.chunk.text for h in hits)[:3000]
    bad = []
    for s in sentences(answer):
        if len(_toks(s)) < 3:
            continue
        try:
            if nli_entailment(premise, s) < NLI_ENTAIL_MIN:
                bad.append(s)
        except Exception:
            bad.append(s)  # NLI error fails closed
    return bad
