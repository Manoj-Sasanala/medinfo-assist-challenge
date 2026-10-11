"""Frozen integration contracts CT-01 / CT-02 (schema level, per 9.6)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """CT-01 Source Page / Chunk. pdf_page is 1-based physical PDF page."""

    chunk_id: str
    source_id: str
    document_title: str
    filename: str
    pdf_page: int = Field(ge=1)
    text: str
    section_title: str | None = None


class EvidenceItem(BaseModel):
    chunk_id: str
    source_id: str
    document_title: str
    filename: str
    pdf_page: int
    excerpt: str
    score: float


class ChatRequest(BaseModel):
    question: str


class Citation(BaseModel):
    document_title: str
    filename: str
    pdf_page: int
    chunk_id: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    abstained: bool = False
    safety_redirect: bool = False
    disclaimer: str = "General health education only — not medical advice. Ask your doctor."
