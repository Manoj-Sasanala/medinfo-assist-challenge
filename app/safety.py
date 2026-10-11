"""Deterministic safety controls. Work without any LLM."""
from __future__ import annotations

import re

DISCLAIMER = "General health education only — not medical advice. Ask your doctor."

_DIAGNOSIS = re.compile(
    r"\b(do i have|diagnos(e|is)|am i diabetic|what (disease|condition) do i have|"
    r"should i take|what dose|how many (mg|units|pills)|prescri(be|ption)|insulin dose)\b",
    re.I,
)

_REDIRECT = (
    "I can't diagnose or prescribe doses. Ask your doctor or diabetes teacher. "
    "I can explain what the supplied guide says about food, blood-glucose targets, "
    "or when to seek care."
)


def is_diagnosis_or_dose(question: str) -> bool:
    return bool(_DIAGNOSIS.search(question))


def redirect_answer() -> str:
    return _REDIRECT
