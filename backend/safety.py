"""Deterministic safety policy (Lane 4). Emits CT-03. Fails closed."""
from __future__ import annotations

import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from contracts.schemas import CT03SafetyDecision

_DIAG = re.compile(
    r"\b(do i have|diagnos(e|is)|am i diabetic|what (disease|condition) do i have|"
    r"should i take|what dose|how many (mg|units|pills)|prescri(be|ption)|insulin dose)\b",
    re.I,
)
_EMERG = re.compile(r"\b(unconscious|not breathing|severe bleeding|chest pain|stroke|overdose)\b", re.I)
_INJECT = re.compile(
    r"\b(ignore (all |your |previous |prior )?instructions|disregard (all |your )?instructions|"
    r"reveal (your )?system prompt|show (me )?(your )?system prompt|jailbreak|\bDAN\b|"
    r"pretend (you are|to be)|act as (a |an )?doctor|override (your|safety) )",
    re.I,
)


def decide(question: str) -> CT03SafetyDecision:
    try:
        q = (question or "").strip()
        if not q:
            return CT03SafetyDecision(decision="safety_redirect", reason_code="other",
                                      user_message="Please ask a question about the supplied guides.")
        if _EMERG.search(q):
            return CT03SafetyDecision(
                decision="emergency_redirect", reason_code="possible_emergency",
                user_message="This sounds like a possible emergency. Call your local emergency number now.")
        if _INJECT.search(q):
            return CT03SafetyDecision(
                decision="safety_redirect", reason_code="other",
                user_message=("I only answer questions about the supplied guides and can't "
                              "change how I work. Please ask about the guide content."))
        if _DIAG.search(q):
            return CT03SafetyDecision(
                decision="safety_redirect",
                reason_code="diagnosis_request" if "dose" not in q.lower() else "prescription_dose_request",
                user_message=("I can't diagnose or prescribe doses. Ask your doctor or diabetes teacher. "
                              "I can explain what the supplied guide says."))
        return CT03SafetyDecision(decision="allow_general_info", reason_code="allowed")
    except Exception:
        return CT03SafetyDecision(decision="safety_redirect", reason_code="other",
                                  user_message="Something went wrong. Please rephrase your question.")
