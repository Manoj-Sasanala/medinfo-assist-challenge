# Handoff: build -> integration (Step 10 Plan A, two-PDF test stage)

Scope decision (review round 3): `Eating_Diabetes_508.pdf` indexed;
`DIA_Ch01.pdf` stays **reference-only** (user decision, recorded here).
Five-organizer-PDF acceptance remains a later step (R-14 OPEN).

## What was built
- 9.4 layout: `backend/` (api, retrieve, safety, generate, validate), `contracts/`
  (CT-01..CT-06 + fixtures/ reserved), `frontend/` (textContent-only UI), `docs/`,
  `scripts/` (no-clobber ingestion, guarded embeddings), `data/`, `tests/`, CI.
- Ingestion: PyMuPDF per-PHYSICAL-page extraction (52pp, 3 image-only empties
  [2,4,6]) -> 54 CT-01 chunks; refuses to overwrite corpus on empty extraction.
- Retrieval Plan A: all-MiniLM-L6-v2 + FAISS, threshold 0.30 (proof in PIVOT_LOG).
  Defensive load (corrupt/mismatched index, model failure) degrades to lexical
  with recorded reason; runtime fallbacks counted and shown in /api/health.
- Chat: CT-03 -> CT-02 -> generation (default `gemini-3.8-flash`, `GEMINI_MODEL`
  override; 2.5-flash retired 404 — see PIVOT_LOG) or extractive -> per-sentence
  lexical + NLI-entailment grounding gate -> CT-05 with mandatory disclaimer.
- Safety: deterministic policy incl. question-side injection patterns; emergency,
  dose, and diagnosis variants redirect with zero citations.

## Contracts
CT-01 chunk, CT-02 evidence pack (method + reason recorded), CT-03 safety,
CT-04 request, CT-05 response, CT-06 manifest with readiness + degraded block.

## Verify
`python -m pytest -q` (39 tests incl. R-01..R-15 traceability gate), CI green on
every push; live probes in docs/INTEGRATION_EVIDENCE.md.

## Known limits
- One guide indexed; organizer five-PDF set pending (R-14 OPEN).
- Printed page labels unmapped (printed_page_label null); physical pdf_page canonical.
- Grounding: NLI (MNLI, P>=0.5) + lexical; hostile-passage evidence is one live
  pattern (scoped, see evidence doc).
