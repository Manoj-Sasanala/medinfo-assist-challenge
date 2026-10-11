"""Answer generation: Gemini (google) when a key is present, else extractive fallback."""
from __future__ import annotations

import os

import httpx

from .schemas import EvidenceItem

_MODEL = "gemini-2.5-flash"
_SYSTEM = (
    "You phrase ONLY what the supplied guide passages support. "
    "Every factual claim must be traceable to the passages. "
    "If passages are insufficient, say so. Never diagnose or dose. "
    "Keep it under 120 words."
)


def _key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def generate(question: str, evidence: list[EvidenceItem]) -> str | None:
    """Return model text or None when no key / call fails (caller falls back)."""
    key = _key()
    if not key:
        return None
    passages = "\n\n".join(
        f"[{e.document_title} p.{e.pdf_page}] {e.excerpt}" for e in evidence
    )
    prompt = f"{_SYSTEM}\n\nQuestion: {question}\n\nPassages:\n{passages}"
    try:
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def extractive(question: str, evidence: list[EvidenceItem]) -> str:
    top = evidence[0]
    return (
        f"From {top.document_title} (page {top.pdf_page}): {top.excerpt}"
    )
