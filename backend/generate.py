"""Answer generation: Gemini 2.5-flash when keyed, else extractive fallback."""
from __future__ import annotations

import os

import httpx

from contracts.schemas import CT02Hit

_MODEL = "gemini-2.5-flash"
_SYSTEM = (
    "Phrase ONLY what the supplied guide passages support. "
    "Every claim must trace to a passage. If insufficient, say so. "
    "Never diagnose or dose. Under 120 words."
)


def generate(question: str, hits: list[CT02Hit]) -> str | None:
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    passages = "\n\n".join(f"[{h.chunk.document_title} p.{h.chunk.pdf_page}] {h.chunk.text[:500]}" for h in hits)
    try:
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": f"{_SYSTEM}\n\nQ: {question}\n\nPassages:\n{passages}"}]}]},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def extractive(hits: list[CT02Hit]) -> str:
    top = hits[0]
    return f"From {top.chunk.document_title} (page {top.chunk.pdf_page}): {top.chunk.text[:400]}"
