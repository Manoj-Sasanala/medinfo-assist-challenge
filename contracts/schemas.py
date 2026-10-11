"""Frozen integration contracts CT-01..CT-06 (schemas only; see 9.6).

Plan A and Plan B both satisfy these. Change only with failing
fixture/test/integration evidence + integration-lead approval.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class CT01Chunk(BaseModel):
    """CT-01 Source Page / Chunk. pdf_page is 1-based PHYSICAL page."""

    chunk_id: str
    source_id: str
    document_title: str
    filename: str
    pdf_page: int = Field(ge=1)
    printed_page_label: str | None = None
    section_title: str | None = None
    text: str


class CT02Hit(BaseModel):
    chunk: CT01Chunk
    score: float
    rank: int = Field(ge=1)


class CT02EvidencePack(BaseModel):
    """CT-02 Retrieved Evidence Pack."""

    query_id: str
    evidence_status: Literal["sufficient", "insufficient"]
    results: list[CT02Hit] = []
    retrieval_method: Literal["semantic", "lexical", "fixture"]
    reason_code: str | None = None


class CT03SafetyDecision(BaseModel):
    """CT-03 Safety Decision (deterministic, pre-generation)."""

    decision: Literal["allow_general_info", "safety_redirect", "emergency_redirect"]
    reason_code: Literal[
        "allowed", "diagnosis_request", "prescription_dose_request",
        "possible_emergency", "other",
    ]
    user_message: str | None = None


class CT04HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class CT04ChatRequest(BaseModel):
    """CT-04 Chat Request (history is context only, never evidence)."""

    question: str
    history: list[CT04HistoryItem] = []


class CT05Citation(BaseModel):
    document_title: str
    pdf_page: int
    printed_page_label: str | None = None
    chunk_id: str
    excerpt: str


class CT05ChatResponse(BaseModel):
    """CT-05 Chat Response."""

    status: Literal["answered", "insufficient_evidence", "safety_redirect", "system_error"]
    answer: str
    citations: list[CT05Citation] = []
    disclaimer: str = (
        "MedInfo Assist provides general information from supplied guides, "
        "not medical advice. It cannot diagnose or prescribe medicines or doses."
    )


class CT06SourceManifest(BaseModel):
    """CT-06 Source Manifest / Readiness entry."""

    source_id: str
    document_title: str
    filename: str
    sha256: str
    page_count: int
    extraction_status: Literal["ok", "partial", "failed", "not_supplied"]
    empty_pages: list[int] = []
    notes: str = ""
